from mcp.server.fastmcp import FastMCP
import pandas as pd
import io
from pathlib import Path
from app.db import supabase
from app.services.scoring import compute_csat, compute_nps
from app.services.rca_engine import run_keyword_rca
import httpx
import git
import tempfile
import os

mcp = FastMCP("CX Analytics MCP Server")

DATA_PATH = Path("data/raw_data.csv")

def _load_data():
    res = supabase.table("survey_responses").select("csat_score", "verbatim").execute()
    data = res.data
    if not data:
        raise FileNotFoundError("No data uploaded yet.")
    df = pd.DataFrame(data)
    df = df.rename(columns={"csat_score": "score", "verbatim": "feedback"})
    return df

# ---------- existing CSV upload tools ----------
@mcp.tool()
def upload_csv_tool(file_path: str) -> str:
    """Upload a local CSV file. Must contain 'score' and 'feedback' columns."""
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip().str.lower()
        for col in ['score', 'feedback']:
            if col not in df.columns:
                return f"Error: CSV must contain '{col}' column."
        records = df.rename(columns={"score": "nps_score", "feedback": "verbatim"}).to_dict(orient="records")
        supabase.table("survey_responses").insert(records).execute()
        return f"Uploaded {len(df)} rows from {file_path}"
    except Exception as e:
        return f"Upload failed: {str(e)}"

@mcp.tool()
async def upload_csv_from_github(url: str) -> str:
    """Upload a CSV file from a public raw URL (e.g. GitHub raw)."""
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

        records = df.rename(columns={"score": "nps_score", "feedback": "verbatim"}).to_dict(orient="records")
        supabase.table("survey_responses").insert(records).execute()
        return f"Uploaded {len(df)} rows from {url}"
    except Exception as e:
        return f"Upload failed: {str(e)}"

# ---------- analytics tools ----------
@mcp.tool()
def get_csat() -> str:
    df = _load_data()
    return str(compute_csat(df))

@mcp.tool()
def get_nps() -> str:
    df = _load_data()
    return str(compute_nps(df))

@mcp.tool()
def get_summary() -> str:
    df = _load_data()
    csat = compute_csat(df)
    nps = compute_nps(df)
    dist = {int(k): int(v) for k, v in df['score'].value_counts().sort_index().items()}
    return str({"csat": csat, "nps": nps, "score_distribution": dist, "total_records": len(df)})

@mcp.tool()
def run_rca() -> str:
    df = _load_data()
    return str(run_keyword_rca(df))

# ---------- NEW Git tools ----------
@mcp.tool()
def git_list_files(repo_url: str, branch: str = "main") -> str:
    """
    Clone a public Git repository and list all files in the given branch.
    repo_url: e.g. https://github.com/suraj1935/cx-analytics.git
    branch:   branch name (default 'main')
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = git.Repo.clone_from(repo_url, tmpdir, branch=branch, depth=1)
            files = [item.path for item in repo.tree().traverse() if item.type == "blob"]
            return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"

@mcp.tool()
def git_read_file(repo_url: str, file_path: str, branch: str = "main") -> str:
    """
    Read the content of a single file from a public Git repository.
    repo_url:  e.g. https://github.com/suraj1935/cx-analytics.git
    file_path: path relative to repo root, e.g. 'sample.csv'
    branch:    branch name (default 'main')
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = git.Repo.clone_from(repo_url, tmpdir, branch=branch, depth=1)
            full_path = os.path.join(tmpdir, file_path)
            if not os.path.exists(full_path):
                return f"File '{file_path}' not found in branch '{branch}'."
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content[:5000]  # limit output to 5000 chars
    except Exception as e:
        return f"Error reading file: {str(e)}"
