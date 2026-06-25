"""Small Ollama client that unloads models after each operation."""

import json
from typing import Any

import httpx

from app.config import settings


class OllamaUnavailableError(RuntimeError):
    pass


def embed(texts: list[str], model: str | None = None) -> list[list[float]]:
    if not texts:
        return []
    try:
        response = httpx.post(
            f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/embed",
            json={"model": model or settings.OLLAMA_EMBEDDING_MODEL, "input": texts,
                  "truncate": True, "keep_alive": 0},
            timeout=settings.OLLAMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()["embeddings"]
    except httpx.HTTPError as exc:
        raise OllamaUnavailableError(
            "Ollama is unavailable. Start Ollama and pull the configured embedding model."
        ) from exc


def structured_chat(system: str, prompt: str, schema: dict[str, Any], model: str) -> dict:
    try:
        response = httpx.post(
            f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat",
            json={
                "model": model,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                "format": schema,
                "stream": False,
                "keep_alive": 0,
                "options": {"num_ctx": settings.OLLAMA_CONTEXT_LENGTH, "temperature": 0.1},
            },
            timeout=settings.OLLAMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return json.loads(response.json()["message"]["content"])
    except httpx.HTTPError as exc:
        raise OllamaUnavailableError(
            "Ollama is unavailable. Start Ollama and pull the configured LLM."
        ) from exc
