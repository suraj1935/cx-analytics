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

# ---------- Git tools ----------
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
            return content[:5000]
    except Exception as e:
        return f"Error reading file: {str(e)}"

# ---------- NEW Audio & Chat tools ----------
@mcp.tool()
async def transcribe_audio_url(audio_url: str) -> str:
    """Download an audio file from a URL and transcribe it using Groq Whisper."""
    try:
        async with httpx.AsyncClient() as client:
            # Download the audio file
            audio_resp = await client.get(audio_url, timeout=30)
            audio_resp.raise_for_status()
            audio_bytes = audio_resp.content

            # Determine MIME type from URL or default to mp3
            mime_type = "audio/mpeg"
            if audio_url.lower().endswith(".wav"):
                mime_type = "audio/wav"
            elif audio_url.lower().endswith(".m4a"):
                mime_type = "audio/mp4"

            # Send to Groq Whisper for transcription
            groq_resp = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
                files={"file": ("audio.mp3", audio_bytes, mime_type)},
                data={"model": "whisper-large-v3-turbo", "response_format": "verbose_json"},
                timeout=60
            )
            if groq_resp.status_code != 200:
                return f"Transcription failed: {groq_resp.text}"

            result = groq_resp.json()
            transcript = result.get("text", "")

            # Store transcript as feedback
            supabase.table("survey_responses").insert({"verbatim": transcript}).execute()
            return transcript
    except Exception as e:
        return f"Transcription error: {str(e)}"

@mcp.tool()
def get_recent_feedback(limit: int = 5) -> str:
    """Return the most recent feedback entries."""
    try:
        res = supabase.table("survey_responses").select("verbatim", "received_at").order("received_at", desc=True).limit(limit).execute()
        return str(res.data)
    except Exception as e:
        return f"Error fetching feedback: {str(e)}"

@mcp.tool()
def ask_deepseek(question: str) -> str:
    """Ask a question to the DeepSeek chatbot and get an answer."""
    try:
        # Gather context from Supabase
        csat_res = supabase.table("survey_responses").select("csat_score").limit(5).execute()
        nps_res  = supabase.table("survey_responses").select("nps_score").limit(5).execute()
        verbatim_res = supabase.table("survey_responses").select("verbatim").order("received_at", desc=True).limit(3).execute()
        context = f"CSAT samples: {csat_res.data}\nNPS samples: {nps_res.data}\nLatest feedback: {verbatim_res.data}"
    except Exception:
        context = "No data available."

    prompt = f"""You are a CX analytics assistant for a call centre. Answer using the data below.
Data:
{context}
User question: {question}
Answer:"""

    async def _call():
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}"},
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "max_tokens": 500},
                timeout=30
            )
            if resp.status_code != 200:
                return f"DeepSeek error: {resp.text}"
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    # Run async call synchronously (MCP tool is sync)
    import asyncio
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_call())
