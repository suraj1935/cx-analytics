from mcp.server.fastmcp import FastMCP
import pandas as pd
from pathlib import Path
from app.services.scoring import compute_csat, compute_nps
from app.services.rca_engine import run_keyword_rca

# Create an MCP server instance (no 'version' argument)
mcp = FastMCP("CX Analytics MCP Server")

DATA_PATH = Path("data/raw_data.csv")

def _load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError("No data uploaded yet. Use the upload_csv tool first.")
    return pd.read_csv(DATA_PATH)

@mcp.tool()
def upload_csv_tool(file_path: str) -> str:
    """
    Upload a CSV file (provide local file path) to the CX analytics platform.
    The file must contain 'score' (0-10) and 'feedback' columns.
    """
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip().str.lower()
        for col in ['score', 'feedback']:
            if col not in df.columns:
                return f"Error: CSV must contain '{col}' column."
        df.to_csv(DATA_PATH, index=False)
        return f"Uploaded {len(df)} rows from {file_path}"
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
    result = run_keyword_rca(df, limit=50)
    return str(result)
