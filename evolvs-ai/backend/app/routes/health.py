"""Health check endpoints"""

from datetime import datetime
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "EvolvS AI",
        "timestamp": datetime.utcnow().isoformat(),
    }
