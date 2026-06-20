"""Audio upload and local Whisper transcription endpoints."""

import logging
import os
import tempfile
import uuid
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status

from app.auth import CurrentUser, get_current_user
from app.config import settings
from app.supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)
router = APIRouter()

AUDIO_BUCKET = "audio"
VALID_AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}


@lru_cache
def get_whisper_model():
    """Load faster-whisper once per backend process."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("Install faster-whisper to enable local transcription") from exc

    return WhisperModel(settings.WHISPER_MODEL, device="cpu", compute_type="int8")


def _format_vtt_timestamp(seconds: float) -> str:
    millis = int(seconds * 1000)
    hours = millis // 3_600_000
    minutes = (millis // 60_000) % 60
    secs = (millis // 1000) % 60
    ms = millis % 1000
    return f"{hours:02}:{minutes:02}:{secs:02}.{ms:03}"


def _transcribe_and_save(recording_id: str, storage_path: str) -> None:
    sb = get_supabase_admin()
    tmp_path = None

    try:
        sb.table("call_recordings").update({"status": "processing"}).eq("id", recording_id).execute()

        audio_bytes = sb.storage.from_(AUDIO_BUCKET).download(storage_path)
        suffix = Path(storage_path).suffix or ".audio"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        model = get_whisper_model()
        segments_iter, info = model.transcribe(tmp_path, beam_size=5, word_timestamps=False)

        transcript_parts: list[str] = []
        vtt_lines = ["WEBVTT", ""]
        segment_rows = []

        recording = (
            sb.table("call_recordings")
            .select("org_id")
            .eq("id", recording_id)
            .single()
            .execute()
            .data
        )
        org_id = recording["org_id"]

        for segment in segments_iter:
            text = segment.text.strip()
            if not text:
                continue

            transcript_parts.append(text)
            vtt_lines.extend(
                [
                    f"{_format_vtt_timestamp(segment.start)} --> {_format_vtt_timestamp(segment.end)}",
                    text,
                    "",
                ]
            )
            segment_rows.append(
                {
                    "org_id": org_id,
                    "recording_id": recording_id,
                    "speaker": "unknown",
                    "start_ms": int(segment.start * 1000),
                    "end_ms": int(segment.end * 1000),
                    "text": text,
                    "confidence": float(segment.avg_logprob),
                }
            )

        if segment_rows:
            sb.table("transcript_segments").insert(segment_rows).execute()

        transcript = " ".join(transcript_parts)
        sb.table("call_recordings").update(
            {
                "status": "done",
                "duration_s": float(info.duration or 0),
                "transcript": transcript,
                "vtt_content": "\n".join(vtt_lines),
            }
        ).eq("id", recording_id).execute()
    except Exception as exc:
        logger.exception("Audio transcription failed for %s", recording_id)
        sb.table("call_recordings").update(
            {"status": "failed", "error_msg": str(exc)}
        ).eq("id", recording_id).execute()
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                logger.warning("Could not remove temp audio file %s", tmp_path)


@router.post("/audio/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Upload audio to Supabase Storage and queue local transcription."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename")

    ext = Path(file.filename).suffix.lower()
    if ext not in VALID_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Supported formats: {', '.join(sorted(VALID_AUDIO_EXTENSIONS))}",
        )

    content = await file.read()
    max_bytes = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.MAX_AUDIO_SIZE_MB}MB upload limit",
        )

    recording_id = str(uuid.uuid4())
    storage_path = f"users/{current_user.id}/{recording_id}{ext}"
    sb = get_supabase_admin()

    try:
        sb.storage.from_(AUDIO_BUCKET).upload(
            storage_path,
            content,
            {"content-type": file.content_type or "application/octet-stream"},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not upload audio to Supabase Storage. Confirm the private 'audio' bucket exists.",
        ) from exc

    sb.table("call_recordings").insert(
        {
            "id": recording_id,
            "org_id": current_user.id,
            "uploaded_by": current_user.id,
            "filename": Path(file.filename).name,
            "storage_path": storage_path,
            "file_size": len(content),
            "status": "pending",
        }
    ).execute()

    background_tasks.add_task(_transcribe_and_save, recording_id, storage_path)
    return {"id": recording_id, "status": "pending"}


@router.get("/audio/{recording_id}")
async def get_audio(
    recording_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get transcription status or completed transcript."""
    result = (
        get_supabase_admin()
        .table("call_recordings")
        .select("id,filename,duration_s,status,error_msg,transcript,vtt_content,created_at")
        .eq("id", recording_id)
        .eq("uploaded_by", current_user.id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Recording not found")

    row = result.data
    return {
        "id": row["id"],
        "file_name": row["filename"],
        "duration": float(row["duration_s"] or 0),
        "status": row["status"],
        "error_msg": row["error_msg"],
        "transcript": row["transcript"] or "",
        "vtt_content": row["vtt_content"] or "WEBVTT\n\n",
        "created_at": row["created_at"],
    }
