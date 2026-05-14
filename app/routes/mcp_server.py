from mcp.server.fastmcp import FastMCP
import pandas as pd
import io
from app.db import supabase
from app.services.scoring import compute_csat, compute_nps
from app.services.rca_engine import run_keyword_rca
import httpx

mcp = FastMCP("CX Analytics MCP Server")

def _load_data():
    """Fetch all survey responses from Supabase and return as a DataFrame."""
    res = supabase.table("survey_responses").select("csat_score", "verbatim").execute()
    data = res.data
    if not data:
        raise FileNotFoundError("No data uploaded yet. Use the upload_csv tool first.")
    df = pd.DataFrame(data)
    df = df.rename(columns={"csat_score": "score", "verbatim": "feedback"})
    return df

@mcp.tool()
def upload_csv_tool(file_path: str) -> str:
    """
    Upload a local CSV file (provide absolute path) to the CX analytics platform.
    The file must contain 'score' (0-10) and 'feedback' columns.
    """
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip().str.lower()
        for col in ['score', 'feedback']:
            if col not in df.columns:
                return f"Error: CSV must contain '{col}' column."

        # Insert rows into Supabase
        records = df.rename(columns={"score": "csat_score", "feedback": "verbatim"}).to_dict(orient="records")
        supabase.table("survey_responses").insert(records).execute()
        return f"Uploaded {len(df)} rows from {file_path}"
    except Exception as e:
        return f"Upload failed: {str(e)}"

@mcp.tool()
async def upload_csv_from_github(url: str) -> str:
    """
    Upload a CSV file from a public URL (GitHub raw, etc.).
    Example: https://raw.githubusercontent.com/suraj1935/cx-analytics/main/sample.csv
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(url, timeout=15)
            resp.raise_for_status()
            csv_bytes = resp.content

        df = pd.read_csv(io.BytesIO(csv_bytes))
        df.columns = df.columns.str.strip().str.lower()
        for col in ['score', 'feedback']:
            if col not in df.columns:
                return f"Error: CSV must contain '{col}' column."

        records = df.rename(columns={"score": "csat_score", "feedback": "verbatim"}).to_dict(orient="records")
        supabase.table("survey_responses").insert(records).execute()
        return f"Uploaded {len(df)} rows from {url}"
    except Exception as e:
        return f"Upload failed: {str(e)}"

@mcp.tool()
def get_csat() -> str:
    """Get Customer Satisfaction Score (CSAT) metrics."""
    df = _load_data()
    result = compute_csat(df)
    return str(result)

@mcp.tool()
def get_nps() -> str:
    """Get Net Promoter Score (NPS) metrics."""
    df = _load_data()
    result = compute_nps(df)
    return str(result)

@mcp.tool()
def get_summary() -> str:
    """Get a combined CSAT, NPS, and score distribution summary."""
    df = _load_data()
    csat = compute_csat(df)
    nps = compute_nps(df)
    dist = {int(k): int(v) for k, v in df['score'].value_counts().sort_index().items()}
    return str({"csat": csat, "nps": nps, "score_distribution": dist, "total_records": len(df)})

@mcp.tool()
def run_rca() -> str:
    """Run keyword-based Root Cause Analysis on feedback."""
    df = _load_data()
    result = run_keyword_rca(df)
    return str(result)
