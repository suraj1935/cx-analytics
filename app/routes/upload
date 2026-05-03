"""
POST /api/upload/
Accepts a CSV file, validates required columns, cleans data,
and persists it to data/raw_data.csv.
"""
import io
import logging
import shutil
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["Upload"])

DATA_DIR = Path("data")
RAW_CSV = DATA_DIR / "raw_data.csv"
REQUIRED_COLUMNS = {"score", "feedback"}


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Minimal cleaning: lowercase columns, drop nulls, coerce score."""
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


@router.post(
    "/",
    summary="Upload a CSV file (requires 'score' and 'feedback' columns)",
)
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

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(RAW_CSV, index=False)
    logger.info("Saved %d rows to %s", len(cleaned), RAW_CSV)

    return JSONResponse(
        status_code=200,
        content={
            "message": "File uploaded and stored successfully.",
            "rows_accepted": len(cleaned),
            "columns": list(cleaned.columns),
        },
    )