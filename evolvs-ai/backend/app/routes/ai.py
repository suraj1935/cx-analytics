from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user
from app.services.knowledge import search_knowledge
from app.services.ollama import OllamaUnavailableError, structured_chat
from app.services.settings_store import get_user_settings
from app.supabase_client import get_supabase_admin

router = APIRouter(prefix="/ai", tags=["Local AI"])


class Finding(BaseModel):
    finding: str
    evidence: str
    policy_reference: str | None = None
    confidence: float = Field(ge=0, le=1)
    recommended_action: str


class Analysis(BaseModel):
    summary: str
    sentiment: str
    root_cause: str
    findings: list[Finding]


@router.post("/recordings/{recording_id}/analyze")
def analyze(recording_id: str, current_user: CurrentUser = Depends(get_current_user)):
    sb = get_supabase_admin()
    response = (sb.table("call_recordings").select("id,transcript,status")
                .eq("id", recording_id).eq("uploaded_by", current_user.id).limit(1).execute())
    if not response.data:
        raise HTTPException(status_code=404, detail="Recording not found")
    recording = response.data[0]
    if recording["status"] != "done" or not recording["transcript"]:
        raise HTTPException(status_code=409, detail="Recording transcription is not complete")
    try:
        evidence = search_knowledge(current_user.id, recording["transcript"][:4000], 5)
        context = "\n\n".join(f"Policy: {row['document_title']}\n{row['content']}" for row in evidence)
        if not context:
            context = "No policy evidence retrieved. Do not invent violations."
        model = get_user_settings(current_user.id)["llm_model"]
        raw = structured_chat(
            "You are an evidence-based contact-center QA auditor. Never claim a violation without evidence.",
            f"Transcript:\n{recording['transcript']}\n\nPolicies:\n{context}",
            Analysis.model_json_schema(), model,
        )
        result = Analysis.model_validate(raw)
    except OllamaUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    sb.table("ai_analyses").insert({"user_id": current_user.id, "recording_id": recording_id,
                                     "model": model, "result": result.model_dump()}).execute()
    return result
