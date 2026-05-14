from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.db import supabase
from app.services.scoring import compute_csat, compute_nps, score_distribution
import pandas as pd

router = APIRouter(prefix="/analytics", tags=["Analytics"])

def _load_df():
    res = supabase.table("survey_responses").select("nps_score", "csat_score").execute()
    data = res.data
    if not data:
        raise HTTPException(status_code=404, detail="No data found. Please upload a CSV first.")
    df = pd.DataFrame(data)
    # Merge the two score columns into one 'score' column for scoring functions.
    # Use nps_score as the primary score; if csat_score is present, fallback.
    if "nps_score" in df.columns:
        df["score"] = df["nps_score"].fillna(df.get("csat_score", 3))
    elif "csat_score" in df.columns:
        df["score"] = df["csat_score"]
    else:
        df["score"] = 0
    return df

@router.get("/csat")
def get_csat():
    df = _load_df()
    result = compute_csat(df)
    return JSONResponse(content=result)

@router.get("/nps")
def get_nps():
    df = _load_df()
    result = compute_nps(df)
    return JSONResponse(content=result)

@router.get("/summary")
def get_summary():
    df = _load_df()
    csat = compute_csat(df)
    nps = compute_nps(df)
    dist = score_distribution(df)
    return JSONResponse(content={
        "csat": csat,
        "nps": nps,
        "score_distribution": dist,
        "total_records": len(df)
    })
