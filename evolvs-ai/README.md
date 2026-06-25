# EvolvS AI - QA Automation SaaS

**Zero-Budget, Production-Ready Platform**

## Quick Start

### Docker (Recommended)
```bash
docker-compose up --build
```

Access at:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000/docs

### Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Features

✅ QA Analytics Dashboard  
✅ Audio Transcription  
✅ REST API  
✅ Zero-Cost Deployment  

## Local AI Setup

```powershell
ollama pull qwen3:4b
ollama pull nomic-embed-text
```

Set `MCP_USER_ID` to the Supabase user that the local MCP process may access, then run:

```powershell
cd backend
..\venv\Scripts\python.exe -m app.mcp_server
```

Whisper, embeddings, and LLM analysis run sequentially. Ollama requests use
`keep_alive: 0` so models are unloaded after each operation.

## File Structure

Reference: Deepak971726 GitHub repo style

- `/backend` - FastAPI application
- `/frontend` - React + TypeScript
- `/docs` - Documentation
- `/config` - Docker configs

## Deployment

Deploy to Render.com (free tier):
1. Connect GitHub repository
2. Set build commands
3. Add environment variables
4. Deploy!

---

**Made with ❤️ for QA Teams**
