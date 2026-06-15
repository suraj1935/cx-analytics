"""Analytics and dashboard data endpoints"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Query, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = Path("data/uploads")


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to snake_case for consistent API output"""
    df = df.copy()
    df.columns = [
        col.lower().replace(" ", "_").replace("(", "").replace(")", "")
        for col in df.columns
    ]
    return df


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
        # Return empty structure instead of 404 so dashboard doesn't error
        return {
            "summary": {
                "total_audits": 0,
                "completion_rate": 0,
                "average_final_score": 0,
            },
            "audits": [],
            "agents": [],
            "parameters": [],
            "reasons": [],
        }
    
    try:
        # Extract sheets (try exact names, then fallback to "data" for CSV)
        summary_df = data.get("Summary") if data.get("Summary") is not None else data.get("data")
        drilldown_df = data.get("Drilldown") if data.get("Drilldown") is not None else pd.DataFrame()
        agents_df = data.get("Agent Analytics") if data.get("Agent Analytics") is not None else pd.DataFrame()
        params_df = data.get("Parameter Analytics") if data.get("Parameter Analytics") is not None else pd.DataFrame()
        reasons_df = data.get("Reason Analytics") if data.get("Reason Analytics") is not None else pd.DataFrame()
        
        # Build summary from Summary sheet
        summary = {}
        if isinstance(summary_df, pd.DataFrame) and "Metric" in summary_df.columns:
            summary = dict(zip(summary_df["Metric"], summary_df["Value"]))
        
        # If no Summary sheet, compute from Drilldown
        if not summary and isinstance(drilldown_df, pd.DataFrame) and len(drilldown_df) > 0:
            norm_drill = _normalize_columns(drilldown_df)
            total = len(norm_drill)
            completed = len(norm_drill[norm_drill.get("status", pd.Series()) == "Closed"]) if "status" in norm_drill.columns else total
            avg_score = norm_drill["final_score"].mean() if "final_score" in norm_drill.columns else 0
            summary = {
                "total_audits": total,
                "completion_rate": round((completed / total * 100) if total > 0 else 0, 2),
                "average_final_score": round(avg_score, 2),
            }

        # Normalize column names for API response
        drilldown_records = []
        if isinstance(drilldown_df, pd.DataFrame) and len(drilldown_df) > 0:
            norm_drill = _normalize_columns(drilldown_df)
            # Ensure required columns exist for frontend types
            col_map = {
                "audit_id": "audit_id",
                "project": "project",
                "status": "status",
                "final_score": "final_score",
                "system_score": "system_score",
                "created_at": "created_at",
            }
            for target, source in col_map.items():
                if source not in norm_drill.columns:
                    norm_drill[target] = 0 if target in ("final_score", "system_score") else ""
            drilldown_records = norm_drill.fillna(0).to_dict("records")

        agents_records = []
        if isinstance(agents_df, pd.DataFrame) and len(agents_df) > 0:
            norm_agents = _normalize_columns(agents_df)
            agents_records = norm_agents.fillna(0).to_dict("records")

        params_records = []
        if isinstance(params_df, pd.DataFrame) and len(params_df) > 0:
            norm_params = _normalize_columns(params_df)
            params_records = norm_params.fillna(0).to_dict("records")

        reasons_records = []
        if isinstance(reasons_df, pd.DataFrame) and len(reasons_df) > 0:
            norm_reasons = _normalize_columns(reasons_df)
            reasons_records = norm_reasons.fillna(0).to_dict("records")

        return {
            "summary": {
                "total_audits": float(summary.get("total_audits", 0)),
                "completion_rate": float(summary.get("completion_rate", 0)),
                "average_final_score": float(summary.get("average_final_score", 0)),
            },
            "audits": drilldown_records,
            "agents": agents_records,
            "parameters": params_records,
            "reasons": reasons_records,
        }
    
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/summary")
async def get_summary():
    """Get summary metrics only"""
    data = _load_latest_file()
    if not data:
        return {
            "total_audits": 0,
            "completion_rate": 0,
            "average_final_score": 0,
        }
    
    summary_df = data.get("Summary") if data.get("Summary") is not None else data.get("data")
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
        return []
    
    df = data.get("Drilldown", pd.DataFrame())
    if len(df) == 0:
        return []
    
    norm_df = _normalize_columns(df)
    return norm_df.iloc[skip:skip+limit].fillna(0).to_dict("records")


@router.get("/analytics/audit/{audit_id}")
async def get_audit_details(audit_id: str):
    """Get parameters and criteria breakdown for a specific audit ID"""
    data = _load_latest_file()
    if not data:
        raise HTTPException(status_code=404, detail="No dataset uploaded")
    
    df = data.get("Audit Parameters")
    if df is None or len(df) == 0:
        raise HTTPException(status_code=404, detail="Audit parameters sheet not found")
    
    norm_df = _normalize_columns(df)
    
    # Filter by specific audit ID
    audit_data = norm_df[norm_df["audit_id"] == audit_id]
    if len(audit_data) == 0:
        raise HTTPException(status_code=404, detail=f"No parameter details found for audit {audit_id}")
        
    return audit_data.fillna("").to_dict("records")
