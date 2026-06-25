"""
EvolvS AI - FastAPI Backend
Production-ready QA Analytics & Audio Transcription
"""

import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routes import ai, analytics, audio, health, knowledge, settings as settings_routes, upload

# ──── LOGGING SETUP ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ──── DIRECTORY SETUP ──────────────────────────────────────────────────
DATA_DIR = Path("data")
UPLOAD_DIR = DATA_DIR / "uploads"
AUDIO_DIR = DATA_DIR / "audio"

for directory in [UPLOAD_DIR, AUDIO_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ──── LIFESPAN CONTEXT ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 EvolvS AI Backend Starting")
    recovered = audio.recover_interrupted_transcriptions()
    if recovered:
        logger.info("Requeued %s interrupted transcription job(s)", recovered)
    yield
    logger.info("🛑 EvolvS AI Backend Shutting Down")

# ──── FASTAPI APP INITIALIZATION ───────────────────────────────────────
app = FastAPI(
    title="EvolvS AI",
    description="Zero-Budget QA Automation SaaS - Analytics & Audio Transcription",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ──── CORS MIDDLEWARE ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──── ROUTE REGISTRATION ───────────────────────────────────────────────
app.include_router(health.router)
app.include_router(health.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(audio.router, prefix="/api")
app.include_router(settings_routes.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(ai.router, prefix="/api")

# ──── ROOT ENDPOINT ────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def root():
    """Root endpoint - API info"""
    return {
        "name": "EvolvS AI",
        "version": "1.0.0",
        "description": "QA Automation SaaS",
        "docs": "/docs",
        "health": "/health",
    }

# ──── EXCEPTION HANDLERS ───────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
