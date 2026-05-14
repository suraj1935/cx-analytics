import io
import logging
import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from app.db import supabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["Upload"])
REQUIRED_COLUMNS = {"score", "feedback"}

def _clean(df):
    df.columns = df.columns.str.strip().str.lower()
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")
    df = df.dropna(subset=list(REQUIRED_COLUMNS))
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df = df.dropna(subset=["score"])
    df["score"] = df["score"].clip(0, 10)
    df["feedback"] = df["feedback"].astype(str).str.strip()
    df = df[df["feedback"].str.len() > 0]
    df = df.drop_duplicates().reset_index(drop=True)
    return df

@router.post("/", summary="Upload CSV (database only, no storage)")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")
    raw_bytes = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(raw_bytes))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Cannot parse CSV: {e}")
    try:
        cleaned = _clean(df)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if cleaned.empty:
        raise HTTPException(status_code=422, detail="No valid rows after cleaning.")

    # Insert rows into survey_responses
    records = cleaned.rename(columns={"score": "csat_score", "feedback": "verbatim"}).to_dict(orient="records")
    supabase.table("survey_responses").insert(records).execute()

    # (Optional) log metadata – skip for now
    logger.info("Inserted %d rows into Supabase", len(records))
    return JSONResponse(content={"message": "File uploaded and stored successfully.", "rows_accepted": len(records), "columns": list(cleaned.columns)})
