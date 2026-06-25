from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user
from app.services.knowledge import ingest_document, search_knowledge
from app.services.ollama import OllamaUnavailableError

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


class DocumentPayload(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    document_type: str = Field(default="policy", min_length=1, max_length=50)
    content: str = Field(min_length=1, max_length=500_000)


class SearchPayload(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    limit: int = Field(default=5, ge=1, le=10)


@router.post("/documents", status_code=201)
def create_document(payload: DocumentPayload, current_user: CurrentUser = Depends(get_current_user)):
    try:
        return ingest_document(current_user.id, payload.title, payload.document_type, payload.content)
    except OllamaUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/search")
def search(payload: SearchPayload, current_user: CurrentUser = Depends(get_current_user)):
    try:
        return {"matches": search_knowledge(current_user.id, payload.query, payload.limit)}
    except OllamaUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
