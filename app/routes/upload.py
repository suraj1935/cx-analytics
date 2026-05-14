"""
POST /api/upload/
Accepts a CSV file, validates required columns, cleans data,
and persists it to Supabase.
"""
import io
import logging

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.db import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["Upload"])

REQUIRED_COLUMNS = {"score", "feedback"}

def _clean(df: pd.DataFrame) -> pd.DataFrame:
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

@router.post("/", summary="Upload a CSV file (requires 'score' and 'feedback' columns)")
async def upload_csv(file: UploadFile = File(...)) -> JSONResponse:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    raw_bytes = await file.read()

    try:
        df = pd.read_csv(io.BytesIO(raw_bytes))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Cannot parse CSV: {exc}")

    try:
        cleaned = _clean(df)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if cleaned.empty:
        raise HTTPException(
            status_code=422,
            detail="No valid rows remain after cleaning. Check score ranges and feedback text.",
        )

    # Store the raw file in Supabase Storage
    try:
        storage_path = f"uploads/{file.filename}"
        supabase.storage.from_("cx-uploads").upload(
            storage_path,
            raw_bytes,
            {"content-type": "text/csv"}
        )
    except Exception as e:
        # File already exists? Try with a unique name
        storage_path = f"uploads/{pd.Timestamp.utcnow().isoformat()}_{file.filename}"
        supabase.storage.from_("cx-uploads").upload(
            storage_path,
            raw_bytes,
            {"content-type": "text/csv"}
        )

    # Insert rows into survey_responses
    rows_inserted = 0
    for _, row in cleaned.iterrows():
        supabase.table("survey_responses").insert({
            "csat_score": int(row["score"]),
            "verbatim": str(row["feedback"]),
        }).execute()
        rows_inserted += 1

    # Log the upload in the uploads table (if you have the table)
    try:
        supabase.table("uploads").insert({
            "filename": file.filename,
            "row_count": rows_inserted,
            "storage_path": storage_path,
        }).execute()
    except Exception as e:
        logger.warning(f"Could not log upload: {e}")

    logger.info("Stored %d rows to Supabase", rows_inserted)

    return JSONResponse(
        status_code=200,
        content={
            "message": "File uploaded and stored successfully.",
            "rows_accepted": rows_inserted,
            "columns": list(cleaned.columns),
        },
    )
