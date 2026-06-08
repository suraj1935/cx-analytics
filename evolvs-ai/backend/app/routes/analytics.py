"""Analytics and dashboard data endpoints"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Query, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = Path("data/uploads")

def _load_latest_file() -> Optional[dict]:
    """Load most recently uploaded file"""
    try:
        files = sorted(UPLOAD_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            return None
        
        latest = files[0]
        logger.info(f"Loading: {latest.name}")
        
        if latest.suffix.lower() == ".csv":
            return {"data": pd.read_csv(latest)}
        else:
            xls = pd.ExcelFile(latest)
            return {sheet: pd.read_excel(latest, sheet_name=sheet) for sheet in xls.sheet_names}
    
    except Exception as e:
        logger.error(f"Load error: {str(e)}")
        return None

@router.get("/analytics")
async def get_analytics():
    """Get complete analytics data"""
    
    data = _load_latest_file()
    if not data:
        raise HTTPException(status_code=404, detail="No data available")
    
    try:
        # Extract sheets
        summary_df = data.get("Summary") or data.get("data")
        drilldown_df = data.get("Drilldown", pd.DataFrame())
        agents_df = data.get("Agent Analytics", pd.DataFrame())
        params_df = data.get("Parameter Analytics", pd.DataFrame())
        reasons_df = data.get("Reason Analytics", pd.DataFrame())
        
        # Build summary dict
        summary = {}
        if isinstance(summary_df, pd.DataFrame) and "Metric" in summary_df.columns:
            summary = dict(zip(summary_df["Metric"], summary_df["Value"]))
        
        return {
            "summary": {
                "total_audits": float(summary.get("total_audits", 0)),
                "completion_rate": float(summary.get("completion_rate", 0)),
                "average_final_score": float(summary.get("average_final_score", 0)),
            },
            "audits": drilldown_df.fillna(0).to_dict("records") if len(drilldown_df) > 0 else [],
            "agents": agents_df.fillna(0).to_dict("records") if len(agents_df) > 0 else [],
            "parameters": params_df.fillna(0).to_dict("records") if len(params_df) > 0 else [],
            "reasons": reasons_df.fillna(0).to_dict("records") if len(reasons_df) > 0 else [],
        }
    
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/summary")
async def get_summary():
    """Get summary metrics only"""
    data = _load_latest_file()
    if not data:
        raise HTTPException(status_code=404, detail="No data available")
    
    summary_df = data.get("Summary") or data.get("data")
    summary = {}
    if isinstance(summary_df, pd.DataFrame) and "Metric" in summary_df.columns:
        summary = dict(zip(summary_df["Metric"], summary_df["Value"]))
    
    return {
        "total_audits": float(summary.get("total_audits", 0)),
        "completion_rate": float(summary.get("completion_rate", 0)),
        "average_final_score": float(summary.get("average_final_score", 0)),
    }

@router.get("/analytics/audits")
async def get_audits(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    """Get paginated audits"""
    data = _load_latest_file()
    if not data:
        raise HTTPException(status_code=404, detail="No data available")
    
    df = data.get("Drilldown", pd.DataFrame())
    if len(df) == 0:
        return []
    
    return df.iloc[skip:skip+limit].fillna(0).to_dict("records")
