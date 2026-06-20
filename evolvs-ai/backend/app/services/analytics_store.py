"""Persistence layer for uploaded analytics datasets."""

from typing import Any

from app.supabase_client import get_supabase_admin

TABLE_NAME = "upload_datasets"


def save_dataset(
    *,
    user_id: str,
    file_name: str,
    file_type: str,
    rows_processed: int,
    sheets: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    payload = {
        "user_id": user_id,
        "file_name": file_name,
        "file_type": file_type,
        "rows_processed": rows_processed,
        "sheets": sheets,
    }
    result = get_supabase_admin().table(TABLE_NAME).insert(payload).execute()
    if not result.data:
        raise RuntimeError("Supabase did not return the inserted dataset")
    return result.data[0]


def load_latest_dataset(user_id: str) -> dict[str, list[dict[str, Any]]] | None:
    result = (
        get_supabase_admin()
        .table(TABLE_NAME)
        .select("sheets")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        return None
    return result.data[0]["sheets"]
