from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import httpx, os
from app.db import supabase

router = APIRouter(prefix="/chat", tags=["Chatbot"])

@router.post("/ask")
async def ask_question(question: str):
    # Gather context (CSAT, NPS, recent feedbacks)
    try:
        csat_res = supabase.table("survey_responses").select("csat_score").limit(5).execute()
        nps_res  = supabase.table("survey_responses").select("nps_score").limit(5).execute()
        verbatim_res = supabase.table("survey_responses").select("verbatim").order("received_at", desc=True).limit(3).execute()
        context = f"CSAT samples: {csat_res.data}\nNPS samples: {nps_res.data}\nLatest feedback: {verbatim_res.data}"
    except Exception as e:
        context = "No data available."

    prompt = f"""You are a CX analytics assistant for a call centre. Answer using the data below.
Data:
{context}
User question: {question}
Answer:"""

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}"},
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "max_tokens": 500},
            timeout=30
        )
        if resp.status_code != 200:
            raise HTTPException(500, f"DeepSeek error: {resp.text}")
        data = resp.json()
        answer = data["choices"][0]["message"]["content"]
    return JSONResponse({"answer": answer})
