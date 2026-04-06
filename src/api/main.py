"""
Person 5 — FastAPI Server
Serves the ReAct Agent as a REST API with endpoints for:
  - POST /solve       → Text question → JSON answer
  - POST /solve/image → Image upload → OCR → JSON answer
  - POST /solve/stream → Text question → SSE streaming thoughts
  - GET  /health      → Health check

Run with: uvicorn src.api.main:app --reload --port 8000
Docs at:  http://localhost:8000/docs

=== TEAM (Person 5 + Person 6): Coordinate on response format ===
"""

import os
import json
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

from src.core.openai_provider import OpenAIProvider
from src.agent.react_engine import ReActEngine
from src.input.ocr_engine import process_image_bytes, process_text
from src.tools.wolfram_tool import WOLFRAM_TOOL
from src.tools.python_tool import PYTHON_TOOL
from src.tools.search_tool import SEARCH_TOOL
from src.tools.math_tools import TOOLS as SYMPY_TOOLS
from src.telemetry.metrics import tracker
from src.telemetry.logger import logger

# ─── Load environment and init ────────────────────────────────────────────────

load_dotenv()

app = FastAPI(
    title="Math ReAct Agent API",
    description="A multi-tier math-solving agent: Wolfram → Python → Search",
    version="1.0.0",
)

# CORS — allow the frontend (Person 6) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # === TEAM: Restrict in production ===
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Build the agent once (shared across requests) ────────────────────────────

def _build_agent() -> ReActEngine:
    llm = OpenAIProvider(
        model_name=os.getenv("DEFAULT_MODEL", "gpt-4o"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Combine all tools into a single registry
    # Order matters for the system prompt's tier instructions
    all_tools = [WOLFRAM_TOOL, PYTHON_TOOL, SEARCH_TOOL] + SYMPY_TOOLS

    return ReActEngine(llm=llm, tools=all_tools, max_steps=10)


agent = _build_agent()


# ─── Request/Response Models ─────────────────────────────────────────────────

class SolveRequest(BaseModel):
    question: str
    details: Optional[str] = None


class SolveResponse(BaseModel):
    answer: str
    steps: int
    tool_attempts: dict
    metrics: dict


class HealthResponse(BaseModel):
    status: str
    model: str
    tools: list


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check — shows model and available tools."""
    return HealthResponse(
        status="ok",
        model=agent.llm.model_name,
        tools=[t["name"] for t in agent.tools],
    )


@app.post("/solve", response_model=SolveResponse)
async def solve_text(request: SolveRequest):
    """
    Solve a math question from text input.
    The agent will try Wolfram → Python → Search in order.
    """
    logger.log_event("API_SOLVE_TEXT", {"question": request.question})

    full_query = request.question
    if request.details:
        full_query += f"\nAdditional context: {request.details}"

    answer = agent.run(full_query)

    # Get the last history entry for metadata
    last_entry = agent.history[-1] if agent.history else {}

    return SolveResponse(
        answer=answer,
        steps=last_entry.get("steps", 0),
        tool_attempts=last_entry.get("tool_attempts", {}),
        metrics=tracker.get_summary(),
    )


@app.post("/solve/image", response_model=SolveResponse)
async def solve_image(
    file: UploadFile = File(...),
    details: Optional[str] = Form(None),
):
    """
    Solve a math question from an image upload.
    Uses OCR to extract the question, then runs the agent.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image (png, jpg, etc.)")

    image_bytes = await file.read()
    logger.log_event("API_SOLVE_IMAGE", {"filename": file.filename, "size": len(image_bytes)})

    # OCR
    parsed = process_image_bytes(image_bytes, filename=file.filename or "upload.png")

    if not parsed.get("question"):
        raise HTTPException(
            status_code=422,
            detail=f"Could not extract text from image. OCR raw: {parsed.get('raw', '')[:200]}",
        )

    full_query = parsed["question"]
    if parsed.get("details"):
        full_query += f"\n{parsed['details']}"
    if details:
        full_query += f"\nUser note: {details}"

    answer = agent.run(full_query)
    last_entry = agent.history[-1] if agent.history else {}

    return SolveResponse(
        answer=answer,
        steps=last_entry.get("steps", 0),
        tool_attempts=last_entry.get("tool_attempts", {}),
        metrics=tracker.get_summary(),
    )


@app.post("/solve/stream")
async def solve_stream(request: SolveRequest):
    """
    Streaming endpoint — returns Server-Sent Events (SSE) so the frontend
    can show the agent's thoughts in real-time.

    === TEAM (Person 6): Connect to this with EventSource in JavaScript ===
    """
    logger.log_event("API_SOLVE_STREAM", {"question": request.question})

    full_query = request.question
    if request.details:
        full_query += f"\nAdditional context: {request.details}"

    def event_generator():
        for step_data in agent.run_stream(full_query):
            # SSE format: data: {json}\n\n
            yield f"data: {json.dumps(step_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/metrics")
async def get_metrics():
    """Return session-level performance metrics."""
    return tracker.get_summary()
