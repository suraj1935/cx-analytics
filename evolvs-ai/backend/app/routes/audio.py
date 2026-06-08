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
        
        # Mock transcription (replace with Whisper in production)
        transcript = "Demo transcription: [0:00] This is a sample transcription..."
        vtt = "WEBVTT\n\n00:00:00.000 --> 00:00:05.000\nDemo transcription"
        duration = 5.0
        
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
