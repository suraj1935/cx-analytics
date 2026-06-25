"""Audio upload and local Whisper transcription endpoints."""

import logging
import mimetypes
import os
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.auth import CurrentUser, get_current_user
from app.config import settings
from app.services.settings_store import get_user_settings
from app.supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)
router = APIRouter()

AUDIO_BUCKET = "audio"
VALID_AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
TRANSCRIPTION_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="evolvs-transcription")


@lru_cache
def get_whisper_model():
    """Load faster-whisper once per backend process."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("Install faster-whisper to enable local transcription") from exc

    return WhisperModel(
        settings.WHISPER_MODEL,
        device="cpu",
        compute_type="int8",
        cpu_threads=settings.WHISPER_CPU_THREADS,
        num_workers=1,
    )


def _format_vtt_timestamp(seconds: float) -> str:
    millis = int(seconds * 1000)
    hours = millis // 3_600_000
    minutes = (millis // 60_000) % 60
    secs = (millis // 1000) % 60
    ms = millis % 1000
    return f"{hours:02}:{minutes:02}:{secs:02}.{ms:03}"


def _transcribe_and_save(recording_id: str, storage_path: str, retain_original: bool) -> None:
    sb = get_supabase_admin()
    tmp_path = None

    try:
        sb.table("call_recordings").update(
            {"status": "processing", "error_msg": None}
        ).eq("id", recording_id).execute()

        audio_bytes = sb.storage.from_(AUDIO_BUCKET).download(storage_path)
        suffix = Path(storage_path).suffix or ".audio"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        model = get_whisper_model()
        segments_iter, info = model.transcribe(
            tmp_path,
            beam_size=1,
            task=settings.WHISPER_TASK,
            word_timestamps=False,
            vad_filter=True,
        )

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

        sb.table("transcript_segments").delete().eq("recording_id", recording_id).execute()
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
        if not retain_original:
            try:
                sb.storage.from_(AUDIO_BUCKET).remove([storage_path])
                sb.table("call_recordings").update(
                    {"storage_path": None, "original_file_retained": False}
                ).eq("id", recording_id).execute()
            except Exception:
                logger.exception("Could not remove non-retained original for %s", recording_id)
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


def queue_transcription(recording_id: str, storage_path: str, retain_original: bool) -> None:
    TRANSCRIPTION_EXECUTOR.submit(_transcribe_and_save, recording_id, storage_path, retain_original)


def recover_interrupted_transcriptions() -> int:
    try:
        response = (
            get_supabase_admin()
            .table("call_recordings")
            .select("id,storage_path,original_file_retained")
            .in_("status", ["pending", "processing"])
            .order("created_at")
            .limit(20)
            .execute()
        )
    except Exception:
        logger.exception("Could not recover interrupted transcription jobs")
        return 0

    recovered = 0
    for row in response.data or []:
        storage_path = row.get("storage_path")
        if not storage_path:
            continue
        get_supabase_admin().table("call_recordings").update(
            {"status": "pending", "error_msg": None}
        ).eq("id", row["id"]).execute()
        queue_transcription(row["id"], storage_path, bool(row["original_file_retained"]))
        recovered += 1
    return recovered


@router.post("/audio/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_audio(
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
    retain_original = get_user_settings(current_user.id)["retain_original_audio"]

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
            "original_file_retained": retain_original,
        }
    ).execute()

    queue_transcription(recording_id, storage_path, retain_original)
    return {"id": recording_id, "status": "pending", "original_file_retained": retain_original}


@router.get("/audio/{recording_id}")
async def get_audio(
    recording_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get transcription status or completed transcript."""
    result = (
        get_supabase_admin()
        .table("call_recordings")
        .select("id,filename,duration_s,status,error_msg,transcript,vtt_content,created_at,original_file_retained")
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
        "original_file_retained": row["original_file_retained"],
    }


@router.get("/audio/{recording_id}/file")
async def download_audio_file(
    recording_id: str,
    download: bool = False,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Return an owned original without exposing the private Storage bucket."""
    sb = get_supabase_admin()
    result = (sb.table("call_recordings").select("filename,storage_path,original_file_retained")
              .eq("id", recording_id).eq("uploaded_by", current_user.id).limit(1).execute())
    if not result.data:
        raise HTTPException(status_code=404, detail="Recording not found")
    row = result.data[0]
    if not row["original_file_retained"] or not row["storage_path"]:
        raise HTTPException(status_code=410, detail="Original recording was not retained")
    try:
        content = sb.storage.from_(AUDIO_BUCKET).download(row["storage_path"])
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Original recording file not found") from exc
    disposition = "attachment" if download else "inline"
    name = quote(Path(row["filename"]).name)
    media_type = mimetypes.guess_type(row["filename"])[0] or "application/octet-stream"
    return Response(content=content, media_type=media_type,
                    headers={"Content-Disposition": f"{disposition}; filename*=UTF-8''{name}"})
