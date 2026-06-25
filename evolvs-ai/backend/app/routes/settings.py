from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.auth import CurrentUser, get_current_user
from app.services.settings_store import get_user_settings, save_user_settings

router = APIRouter(prefix="/settings", tags=["Settings"])


class SettingsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    retain_original_audio: bool = True
    llm_model: str = "qwen3:4b"
    embedding_model: str = "nomic-embed-text"


@router.get("")
def read_settings(current_user: CurrentUser = Depends(get_current_user)):
    return get_user_settings(current_user.id)


@router.put("")
def update_settings(payload: SettingsPayload, current_user: CurrentUser = Depends(get_current_user)):
    return save_user_settings(current_user.id, payload.model_dump())
