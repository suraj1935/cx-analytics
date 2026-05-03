"""
Analytics routes:
  GET /api/analytics/csat
  GET /api/analytics/nps
  GET /api/analytics/summary   ← combined endpoint used by the dashboard
"""
import logging
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.services.scoring import compute_csat, compute_nps, score_distribution

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

RAW_CSV = Path("data/raw_data.csv")


def _load() -> pd.DataFrame:
    if not RAW_CSV.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "No data found. Please upload a CSV file first via POST /api/upload/."
            ),
        )
    try:
        df = pd.read_csv(RAW_CSV)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read data: {exc}")

    if df.empty:
        raise HTTPException(
            status_code=422, detail="Stored dataset is empty. Please re-upload."
        )
    return df


# ── CSAT ──────────────────────────────────────────────────────────────────────

@router.get("/csat", summary="Customer Satisfaction Score metrics")
def get_csat() -> JSONResponse:
    df = _load()
    result = compute_csat(df)
    return JSONResponse(content=result)


# ── NPS ───────────────────────────────────────────────────────────────────────

@router.get("/nps", summary="Net Promoter Score metrics")
def get_nps() -> JSONResponse:
    df = _load()
    result = compute_nps(df)
    return JSONResponse(content=result)


# ── Summary (CSAT + NPS + distribution) ──────────────────────────────────────

@router.get("/summary", summary="Combined CSAT, NPS and score distribution")
def get_summary() -> JSONResponse:
    df = _load()
    return JSONResponse(
        content={
            "csat": compute_csat(df),
            "nps": compute_nps(df),
            "score_distribution": score_distribution(df),
            "total_records": len(df),
        }
    )