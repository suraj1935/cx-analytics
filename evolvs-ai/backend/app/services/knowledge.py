"""Lightweight RAG ingestion and retrieval."""

from app.services.ollama import embed
from app.supabase_client import get_supabase_admin

MAX_CHUNK_CHARS = 2800


def chunk_text(content: str) -> list[str]:
    paragraphs = [part.strip() for part in content.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > MAX_CHUNK_CHARS:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(paragraph[i:i + MAX_CHUNK_CHARS] for i in range(0, len(paragraph), MAX_CHUNK_CHARS))
            continue
        candidate = f"{current}\n\n{paragraph}".strip()
        if current and len(candidate) > MAX_CHUNK_CHARS:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def ingest_document(user_id: str, title: str, document_type: str, content: str) -> dict:
    sb = get_supabase_admin()
    document = sb.table("knowledge_documents").insert(
        {"user_id": user_id, "title": title, "document_type": document_type}
    ).execute().data[0]
    chunks = chunk_text(content)
    vectors = embed(chunks)
    rows = [{"user_id": user_id, "document_id": document["id"], "chunk_index": index,
             "content": chunk, "embedding": vector}
            for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))]
    if rows:
        sb.table("knowledge_chunks").insert(rows).execute()
    return {**document, "chunks_created": len(rows)}


def search_knowledge(user_id: str, query: str, limit: int = 5) -> list[dict]:
    vector = embed([query])[0]
    response = get_supabase_admin().rpc("match_knowledge", {
        "query_embedding": vector, "match_user_id": user_id, "match_count": max(1, min(limit, 10))
    }).execute()
    return response.data or []
