"""Run locally with: python -m app.mcp_server"""

from mcp.server.fastmcp import FastMCP

from app.config import settings
from app.services.knowledge import search_knowledge as rag_search
from app.services.settings_store import get_user_settings
from app.supabase_client import get_supabase_admin

mcp = FastMCP("EvolvS AI")


def _user_id() -> str:
    if not settings.MCP_USER_ID:
        raise RuntimeError("MCP_USER_ID must be configured")
    return settings.MCP_USER_ID


@mcp.tool()
def search_knowledge(query: str, limit: int = 5) -> list[dict]:
    """Search policies and SOPs owned by the configured user."""
    return rag_search(_user_id(), query, limit)


@mcp.tool()
def get_transcript(recording_id: str) -> dict:
    """Return one owned recording transcript."""
    response = (get_supabase_admin().table("call_recordings")
                .select("id,filename,status,transcript,vtt_content,created_at")
                .eq("id", recording_id).eq("uploaded_by", _user_id()).limit(1).execute())
    if not response.data:
        raise ValueError("Recording not found")
    return response.data[0]


@mcp.tool()
def get_upload_settings() -> dict:
    """Return retention and model settings for the configured user."""
    return get_user_settings(_user_id())


if __name__ == "__main__":
    mcp.run(transport="stdio")
