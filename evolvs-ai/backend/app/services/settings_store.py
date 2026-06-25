"""Owner-scoped application settings stored in Supabase."""

from app.supabase_client import get_supabase_admin

DEFAULT_USER_SETTINGS = {
    "retain_original_audio": True,
    "llm_model": "qwen3:4b",
    "embedding_model": "nomic-embed-text",
}


def get_user_settings(user_id: str) -> dict:
    response = (
        get_supabase_admin().table("user_ai_settings")
        .select("retain_original_audio,llm_model,embedding_model")
        .eq("user_id", user_id).limit(1).execute()
    )
    return {**DEFAULT_USER_SETTINGS, **(response.data[0] if response.data else {})}


def save_user_settings(user_id: str, values: dict) -> dict:
    response = (
        get_supabase_admin().table("user_ai_settings")
        .upsert({"user_id": user_id, **values}, on_conflict="user_id").execute()
    )
    return {**DEFAULT_USER_SETTINGS, **response.data[0]}
