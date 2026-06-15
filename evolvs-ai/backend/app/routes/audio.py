"""Audio transcription endpoints"""

import logging
from datetime import datetime
from pathlib import Path
import json

from fastapi import APIRouter, UploadFile, File, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()

AUDIO_DIR = Path("data/audio")

@router.post("/audio/upload")
async def upload_audio(file: UploadFile = File(...)):
    """Upload audio file for transcription"""
    
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename")
        
        ext = Path(file.filename).suffix.lower()
        valid = [".wav", ".mp3", ".flac", ".ogg", ".m4a"]
        if ext not in valid:
            raise HTTPException(status_code=400, detail=f"Support: {', '.join(valid)}")
        
        # Save file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_id = f"{timestamp}_{file.filename}"
        audio_path = AUDIO_DIR / audio_id
        
        content = await file.read()
        with open(audio_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Audio saved: {audio_id}")
        
        # Real transcription using WhisperService
        whisper_service = WhisperService(settings)
        result = await whisper_service.transcribe_file(audio_path)
        transcript = result.text
        # Optionally generate VTT from segments (simple placeholder)
        vtt = "WEBVTT\n\n"
        for seg in result.segments:
            start = int(seg.start * 1000)
            end = int(seg.end * 1000)
            vtt += f"{start // 3600000:02}:{(start // 60000) % 60:02}:{(start // 1000) % 60:02}.{start % 1000:03} --> {end // 3600000:02}:{(end // 60000) % 60:02}:{(end // 1000) % 60:02}.{end % 1000:03}\n{seg.text}\n\n"
        duration = result.duration_seconds or 0
        
        # Save metadata
        metadata = {
            "id": audio_id,
            "file_name": file.filename,
            "duration": duration,
            "transcript": transcript,
            "vtt_content": vtt,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        with open(audio_path.with_suffix(".json"), "w") as f:
            json.dump(metadata, f)
        
        return metadata
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audio/{audio_id}")
async def get_audio(audio_id: str):
    """Get audio transcript"""
    
    audio_path = AUDIO_DIR / audio_id
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    
    metadata_path = audio_path.with_suffix(".json")
    if metadata_path.exists():
        with open(metadata_path) as f:
            return json.load(f)
    
    raise HTTPException(status_code=404, detail="Metadata not found")
