"""FastAPI entry point for the Enterprise AI Agent POC."""
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

try:
    from .agent import EnterpriseAgent
except ImportError:  # supports `uvicorn app:app --app-dir server`
    from agent import EnterpriseAgent

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title="Enterprise AI Agent", version="1.0.0")
app.mount("/ui", StaticFiles(directory=ROOT / "ui"), name="ui")
agent = EnterpriseAgent(ROOT)


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def home():
    return FileResponse(ROOT / "ui" / "index.html")


@app.get("/api/dashboard")
def dashboard():
    return agent.dashboard()


@app.post("/api/chat")
def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Please enter a business question.")
    return agent.answer(request.message)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "enterprise-ai-agent"}
