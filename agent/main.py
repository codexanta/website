"""FastAPI server: web UI + chat API. Runs on Hugging Face Spaces (port 7860)."""
import os
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import agent as core

AGENT_TOKEN = os.getenv("AGENT_TOKEN", "")  # required to protect your agent
STATIC = Path(__file__).parent / "static"

app = FastAPI(title="Personal Agent")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def auth(authorization: str = Header(default="")):
    if AGENT_TOKEN and authorization != f"Bearer {AGENT_TOKEN}":
        raise HTTPException(401, "invalid token")


class ChatIn(BaseModel):
    message: str
    history: list[dict] | None = None


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health():
    return {"ok": True, "llm_configured": bool(core.LLM_API_KEY)}


@app.post("/api/chat", dependencies=[Depends(auth)])
def chat(body: ChatIn):
    return core.run_agent(body.message, body.history)


@app.post("/api/upload", dependencies=[Depends(auth)])
async def upload(file: UploadFile = File(...)):
    dest = core._safe_path(file.filename)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(await file.read())
    return {"saved": str(dest.relative_to(core.WORKSPACE))}
