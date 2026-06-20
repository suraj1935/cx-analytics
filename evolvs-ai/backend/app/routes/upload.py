"""File upload endpoints"""

import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from app.auth import CurrentUser, get_current_user
from app.services.analytics_store import save_dataset

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def _safe_filename(filename: str) -> str:
    name = Path(filename).name
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


def _records_from_frame(df: pd.DataFrame) -> list[dict[str, Any]]:
    safe_df = df.where(pd.notnull(df), None)
    return safe_df.to_dict("records")

@router.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Upload CSV or XLSX file for analysis"""
    
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename")
        
        safe_name = _safe_filename(file.filename)
        ext = Path(safe_name).suffix.lower()
        if ext not in [".csv", ".xlsx", ".xls"]:
            raise HTTPException(
                status_code=400,
                detail="Only CSV and XLSX files supported"
            )
        
        # Read file
        content = await file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)}MB upload limit",
            )
        
        # Parse
        sheets_payload = {}
        if ext == ".csv":
            df = pd.read_csv(__import__("io").BytesIO(content))
            sheets = ["data"]
            sheets_payload["data"] = _records_from_frame(df)
        else:
            xls = pd.ExcelFile(__import__("io").BytesIO(content))
            sheets = xls.sheet_names
            df = pd.read_excel(__import__("io").BytesIO(content), sheet_name=0)
            for sheet_name in sheets:
                sheet_df = pd.read_excel(__import__("io").BytesIO(content), sheet_name=sheet_name)
                sheets_payload[sheet_name] = _records_from_frame(sheet_df)

        dataset = save_dataset(
            user_id=current_user.id,
            file_name=safe_name,
            file_type=ext.lstrip("."),
            rows_processed=len(df),
            sheets=sheets_payload,
        )
        
        logger.info("File uploaded: %s by user %s", safe_name, current_user.id)
        
        return {
            "success": True,
            "message": "File uploaded successfully",
            "dataset_id": dataset["id"],
            "file_name": safe_name,
            "rows_processed": len(df),
            "sheets_found": sheets,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
