"""
RCA routes:
  GET /api/rca/keyword   ← keyword-based root cause analysis
"""
import logging

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.db import supabase
from app.services.rca_engine import NEGATIVE_KEYWORDS, run_keyword_rca

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rca", tags=["RCA"])


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
    # Fetch all survey responses from Supabase
    try:
        res = supabase.table("survey_responses").select("csat_score", "verbatim").execute()
        data = res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data from Supabase: {e}")

    if not data:
        raise HTTPException(
            status_code=404,
            detail="No data found. Please upload a CSV file first via POST /api/upload/.",
        )

    df = pd.DataFrame(data)
    # Rename columns to match what the engine expects
    df = df.rename(columns={"csat_score": "score", "verbatim": "feedback"})

    result = run_keyword_rca(df)
    result["matching_records"] = result["matching_records"][:limit]
    result["keywords_used"] = NEGATIVE_KEYWORDS
    return JSONResponse(content=result)
