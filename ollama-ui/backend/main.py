"""
FastAPI Backend — Proxies all Ollama API calls
Covers: /api/chat, /api/generate, /api/embed,
        /api/tags, /api/show, /api/pull, /api/delete
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import httpx
import json

app = FastAPI(title="Ollama UI API", version="1.0.0")

# ── CORS for local Vite dev server ──────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_BASE_URL = "http://localhost:11434"


# ── Pydantic Models ────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    num_ctx: Optional[int] = 2048

class GenerateRequest(BaseModel):
    model: str
    prompt: str
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    num_ctx: Optional[int] = 2048

class EmbedRequest(BaseModel):
    model: str
    input: str

class ModelRequest(BaseModel):
    name: str

class PullRequest(BaseModel):
    name: str


# ── Health Check ───────────────────────────────────────────
@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return {"status": "ok", "ollama": r.status_code == 200}
    except Exception:
        return {"status": "ok", "ollama": False}


# ── 1. List Models ─────────────────────────────────────────
@app.get("/api/models")
async def list_models():
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return r.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Ollama unreachable: {e}")


# ── 2. Show Model Info ─────────────────────────────────────
@app.post("/api/model/info")
async def model_info(req: ModelRequest):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{OLLAMA_BASE_URL}/api/show",
            json={"name": req.name}
        )
        return r.json()


# ── 3. Pull Model ──────────────────────────────────────────
@app.post("/api/model/pull")
async def pull_model(req: PullRequest):
    async def stream_pull():
        async with httpx.AsyncClient(timeout=600) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/pull",
                json={"name": req.name, "stream": True},
            ) as r:
                async for line in r.aiter_lines():
                    if line:
                        yield f"data: {line}\n\n"
    return StreamingResponse(stream_pull(), media_type="text/event-stream")


# ── 4. Delete Model ────────────────────────────────────────
@app.delete("/api/model/delete")
async def delete_model(req: ModelRequest):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.request(
            "DELETE",
            f"{OLLAMA_BASE_URL}/api/delete",
            json={"name": req.name}
        )
        if r.status_code == 200:
            return {"status": "deleted", "name": req.name}
        raise HTTPException(status_code=r.status_code, detail=r.text)


# ── 5. Chat ────────────────────────────────────────────────
@app.post("/api/chat")
async def chat(req: ChatRequest):
    payload = {
        "model"   : req.model,
        "messages": [m.dict() for m in req.messages],
        "stream"  : req.stream,
        "options" : {
            "temperature": req.temperature,
            "top_p"      : req.top_p,
            "num_ctx"    : req.num_ctx,
        },
    }

    if req.stream:
        async def stream_chat():
            async with httpx.AsyncClient(timeout=300) as client:
                async with client.stream(
                    "POST", f"{OLLAMA_BASE_URL}/api/chat", json=payload
                ) as r:
                    async for line in r.aiter_lines():
                        if line:
                            yield f"data: {line}\n\n"
        return StreamingResponse(stream_chat(), media_type="text/event-stream")

    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
        return r.json()


# ── 6. Generate ────────────────────────────────────────────
@app.post("/api/generate")
async def generate(req: GenerateRequest):
    payload = {
        "model"  : req.model,
        "prompt" : req.prompt,
        "stream" : req.stream,
        "options": {
            "temperature": req.temperature,
            "top_p"      : req.top_p,
            "num_ctx"    : req.num_ctx,
        },
    }

    if req.stream:
        async def stream_gen():
            async with httpx.AsyncClient(timeout=300) as client:
                async with client.stream(
                    "POST", f"{OLLAMA_BASE_URL}/api/generate", json=payload
                ) as r:
                    async for line in r.aiter_lines():
                        if line:
                            yield f"data: {line}\n\n"
        return StreamingResponse(stream_gen(), media_type="text/event-stream")

    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
        return r.json()


# ── 7. Embeddings ──────────────────────────────────────────
@app.post("/api/embed")
async def embed(req: EmbedRequest):
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json={"model": req.model, "input": req.input}
        )
        data = r.json()
        embedding = data.get("embeddings", [[]])[0]
        return {
            "model"          : req.model,
            "embedding"      : embedding,
            "dimensions"     : len(embedding),
            "preview"        : embedding[:10],
        }

# ── List Running (Loaded) Models ───────────────────────
@app.get("/api/running")
async def list_running_models():
    """
    Calls Ollama GET /api/ps
    Returns models currently loaded in memory (VRAM/RAM).
    """
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/ps")
            return r.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Ollama unreachable: {e}")