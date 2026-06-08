"""File upload endpoints"""

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = Path("data/uploads")

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """Upload CSV or XLSX file for analysis"""
    
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename")
        
        ext = Path(file.filename).suffix.lower()
        if ext not in [".csv", ".xlsx", ".xls"]:
            raise HTTPException(
                status_code=400,
                detail="Only CSV and XLSX files supported"
            )
        
        # Read file
        content = await file.read()
        
        # Parse
        if ext == ".csv":
            df = pd.read_csv(__import__("io").BytesIO(content))
            sheets = ["data"]
        else:
            xls = pd.ExcelFile(__import__("io").BytesIO(content))
            sheets = xls.sheet_names
            df = pd.read_excel(__import__("io").BytesIO(content), sheet_name=0)
        
        # Save file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = UPLOAD_DIR / f"{timestamp}_{file.filename}"
        
        with open(save_path, "wb") as f:
            f.write(content)
        
        logger.info(f"File uploaded: {file.filename}")
        
        return {
            "success": True,
            "message": "File uploaded successfully",
            "file_name": file.filename,
            "rows_processed": len(df),
            "sheets_found": sheets,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
