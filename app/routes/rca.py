"""
RCA routes:
  GET /api/rca/keyword   ← keyword-based root cause analysis
"""
import logging
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.services.rca_engine import NEGATIVE_KEYWORDS, run_keyword_rca

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rca", tags=["RCA"])

RAW_CSV = Path("data/raw_data.csv")


def _load() -> pd.DataFrame:
    if not RAW_CSV.exists():
        raise HTTPException(
            status_code=404,
            detail="No data found. Please upload a CSV file first via POST /api/upload/.",
        )
    try:
        df = pd.read_csv(RAW_CSV)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read data: {exc}")
    if df.empty:
        raise HTTPException(status_code=422, detail="Stored dataset is empty.")
    return df


@router.get("/keyword", summary="Keyword-based Root Cause Analysis")
def keyword_rca(
    limit: int = Query(
        default=200,
        ge=1,
        le=1000,
        description="Maximum number of matching feedback rows to return",
    ),
) -> JSONResponse:
    """
    Scans all feedback entries for negative keywords and returns:
    - keyword_counts   : frequency map of each matched keyword
    - matching_records : feedback rows that contained at least one negative keyword
    - total_matches    : number of affected rows
    - total_records    : total rows in the dataset
    - keywords_used    : the keyword list applied
    """
    df = _load()
    result = run_keyword_rca(df)
    # Truncate records to limit
    result["matching_records"] = result["matching_records"][:limit]
    result["keywords_used"] = NEGATIVE_KEYWORDS
    return JSONResponse(content=result)
