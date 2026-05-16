"""
CX Analytics Platform – FastAPI entry point.
"""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.routes import analytics, rca, upload
from app.routes.mcp_server import mcp

from app.routes import audio_upload
app.include_router(audio_upload.router, prefix="/api")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── Bootstrap ─────────────────────────────────────────────────────────────────
Path("data").mkdir(parents=True, exist_ok=True)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CX Analytics Platform",
    description=(
        "Customer Experience Analytics API providing CSAT, NPS, "
        "and keyword-based Root Cause Analysis over uploaded feedback data."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS – allows all origins, even on error responses ────────────────────────
class CorsErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            response = await call_next(request)
        except Exception:
            # Catch any unhandled exception and return a 500 with CORS headers
            response = Response(status_code=500)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

app.add_middleware(CorsErrorMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers – all mounted under /api ──────────────────────────────────────────
PREFIX = "/api"

app.include_router(upload.router,    prefix=PREFIX)
app.include_router(analytics.router, prefix=PREFIX)
app.include_router(rca.router,       prefix=PREFIX)

# ── MCP Server (SSE transport) ────────────────────────────────────────────────
app.mount("/mcp", mcp.sse_app())

# ── Utility routes ────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "cx-analytics"}


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "CX Analytics Platform API",
        "docs": "/docs",
        "health": "/health",
    }
