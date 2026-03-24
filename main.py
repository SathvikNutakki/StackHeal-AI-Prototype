"""
main.py — StackHeal AI FastAPI Backend
Exposes the 7-agent pipeline over HTTP.

Run:  uvicorn main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""

from __future__ import annotations

import asyncio
import json as _json
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel


# ── Lifespan: eagerly import all agents on startup ─────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from error_detection import run_error_agent          # noqa: F401
        from error_line import run_line_agent                # noqa: F401
        from error_classify import run_classification_agent  # noqa: F401
        from root_cause import run_root_cause_agent          # noqa: F401
        from fix import run_fix_agent                        # noqa: F401
        from explain import run_explanation_agent            # noqa: F401
        from confident import run_confidence_agent           # noqa: F401
        print("[StackHeal] ✅ All 7 agents loaded successfully")
    except ImportError as exc:
        print(f"[StackHeal] ⚠️  Agent import warning: {exc}")
    yield
    print("[StackHeal] 👋 Shutting down")


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(title="StackHeal AI", version="2.1.0", lifespan=lifespan)

# CORS — allow the Vite dev server (port 5173) and any localhost origin.
# Tighten allow_origins in production to your real domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ────────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    code: str
    language: Optional[str] = "auto"


class PipelineResponse(BaseModel):
    type: str
    message: str
    line: int
    snippet: str
    severity: str
    language: str
    root_cause: str
    description: str
    correctedCode: str
    simple: str
    detailed: str
    confidence: float


# ── In-memory history (resets on server restart) ───────────────────────────────

_history: list[dict] = []


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "StackHeal AI", "version": "2.1.0", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "StackHeal AI"}


@app.post("/analyze", response_model=PipelineResponse)
def analyze(body: AnalyzeRequest):
    """
    Run the full 7-agent pipeline on the submitted code / error log.
    Returns structured JSON with detection, classification, root cause,
    fix suggestion, explanation, and confidence score.
    """
    if not body.code.strip():
        raise HTTPException(status_code=400, detail="'code' field must not be empty")

    from orchestrator import run_stackheal_pipeline

    try:
        result = run_stackheal_pipeline(body.code)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}")

    response = PipelineResponse(
        type=result.get("type", "UnknownError"),
        message=result.get("message", ""),
        line=result.get("line", -1),
        snippet=result.get("snippet", ""),
        severity=result.get("severity", "Medium"),
        language=result.get("language", body.language or "Unknown"),
        root_cause=result.get("root_cause", ""),
        description=result.get("description", ""),
        correctedCode=result.get("correctedCode", ""),
        simple=result.get("simple", ""),
        detailed=result.get("detailed", ""),
        confidence=result.get("confidence", 0.5),
    )

    _history.append({
        "id": len(_history) + 1,
        "input_preview": body.code[:120] + ("…" if len(body.code) > 120 else ""),
        "language": body.language,
        "result": response.model_dump(),
    })

    return response


# ── Streaming endpoint (Server-Sent Events) ────────────────────────────────────

@app.post("/analyze/stream")
async def analyze_stream(body: AnalyzeRequest):
    """
    Same pipeline as /analyze but streams step-by-step progress via SSE.
    Each event: data: {"step": <name>, "status": "running"|"done"|"error", "payload": ...}
    Final event: {"step": "complete", "status": "complete", "payload": <full_result>}
    """
    if not body.code.strip():
        raise HTTPException(status_code=400, detail="'code' field must not be empty")

    def _step_functions():
        from error_detection import run_error_agent
        from error_line import run_line_agent
        from error_classify import run_classification_agent
        from root_cause import run_root_cause_agent
        from fix import run_fix_agent
        from explain import run_explanation_agent
        from confident import run_confidence_agent

        # (step_name, callable, arg_mode)
        # arg_mode "input"       → fn(body.code)
        # arg_mode "accumulated" → fn(accumulated_dict)  returns float
        return [
            ("error_detection", run_error_agent,          "input"),
            ("error_line",      run_line_agent,            "input"),
            ("error_classify",  run_classification_agent,  "input"),
            ("root_cause",      run_root_cause_agent,      "input"),
            ("fix",             run_fix_agent,             "input"),
            ("explain",         run_explanation_agent,     "input"),
            ("confidence",      run_confidence_agent,      "accumulated"),
        ]

    async def event_generator():
        step_fns = _step_functions()
        accumulated: dict = {}

        yield _sse({"step": "start", "status": "running", "total_steps": len(step_fns)})
        await asyncio.sleep(0)

        for step_name, fn, arg_mode in step_fns:
            yield _sse({"step": step_name, "status": "running"})
            await asyncio.sleep(0)

            try:
                loop = asyncio.get_event_loop()
                if arg_mode == "input":
                    partial = await loop.run_in_executor(None, fn, body.code)
                else:
                    raw = await loop.run_in_executor(None, fn, accumulated)
                    partial = {"confidence": raw}

                accumulated.update(partial)
                yield _sse({"step": step_name, "status": "done", "payload": partial})
            except Exception as exc:
                yield _sse({"step": step_name, "status": "error", "error": str(exc)})

            await asyncio.sleep(0)

        final = {
            "type":          accumulated.get("type", "UnknownError"),
            "message":       accumulated.get("message", ""),
            "line":          accumulated.get("line", -1),
            "snippet":       accumulated.get("snippet", ""),
            "severity":      accumulated.get("severity", "Medium"),
            "language":      accumulated.get("language", body.language or "Unknown"),
            "root_cause":    accumulated.get("root_cause", ""),
            "description":   accumulated.get("description", ""),
            "correctedCode": accumulated.get("correctedCode", ""),
            "simple":        accumulated.get("simple", ""),
            "detailed":      accumulated.get("detailed", ""),
            "confidence":    accumulated.get("confidence", 0.5),
        }

        _history.append({
            "id": len(_history) + 1,
            "input_preview": body.code[:120] + ("…" if len(body.code) > 120 else ""),
            "language": body.language,
            "result": final,
        })

        yield _sse({"step": "complete", "status": "complete", "payload": final})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse(data: dict) -> str:
    return f"data: {_json.dumps(data)}\n\n"


# ── History routes ─────────────────────────────────────────────────────────────

@app.get("/history")
def get_history(limit: int = 20):
    return {"total": len(_history), "items": list(reversed(_history[-limit:]))}


@app.delete("/history")
def clear_history():
    _history.clear()
    return {"status": "cleared"}


@app.get("/history/{item_id}")
def get_history_item(item_id: int):
    matches = [h for h in _history if h["id"] == item_id]
    if not matches:
        raise HTTPException(status_code=404, detail=f"No history item with id={item_id}")
    return matches[0]
