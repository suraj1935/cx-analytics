from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
from app.db import supabase

router = APIRouter(prefix="/upload", tags=["Audio Upload"])

@router.post("/audio")
async def upload_audio(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.ogg')):
        raise HTTPException(400, "Only audio files (.wav, .mp3, .m4a, .ogg) are accepted.")
    
    audio_bytes = await file.read()
    
    # Call Groq Whisper for transcription
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
            files={"file": (file.filename, audio_bytes, file.content_type)},
            data={"model": "whisper-large-v3-turbo", "response_format": "verbose_json"},
            timeout=60
        )
        if resp.status_code != 200:
            raise HTTPException(500, f"Transcription failed: {resp.text}")
        
        result = resp.json()
        transcript = result.get("text", "")
    
    # Store transcription as feedback (similar to CSV upload)
    supabase.table("survey_responses").insert({
        "verbatim": transcript,
        # You could also add a dummy score or later use sentiment for score
    }).execute()
    
    return JSONResponse({"transcript": transcript, "message": "Audio transcribed and stored."})
