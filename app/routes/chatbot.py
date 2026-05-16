from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import os
from app.db import supabase

router = APIRouter(prefix="/chat", tags=["Chatbot"])

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

class ChatRequest(BaseModel):
    question: str

@router.post("/ask")
async def ask_question(request: ChatRequest):
    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=500, detail="DeepSeek API key not configured.")

    # Gather context from Supabase
    try:
        csat_res = supabase.table("survey_responses").select("csat_score").limit(5).execute()
        nps_res = supabase.table("survey_responses").select("nps_score").limit(5).execute()
        verbatim_res = supabase.table("survey_responses").select("verbatim").order("received_at", desc=True).limit(3).execute()
        context = f"CSAT samples: {csat_res.data}\nNPS samples: {nps_res.data}\nLatest feedback: {verbatim_res.data}"
    except Exception:
        context = "No data available."

    prompt = f"""You are a CX analytics assistant for a call centre. Answer using the data below.
Data:
{context}
User question: {request.question}
Answer:"""

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            answer = data["choices"][0]["message"]["content"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DeepSeek API error: {str(e)}")

    return JSONResponse(content={"answer": answer})
