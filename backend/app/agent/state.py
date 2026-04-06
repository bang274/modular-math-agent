"""
Agent State — LangGraph TypedDict defining all state fields.

Person 3 owns this file.
This is the shared state passed between all LangGraph nodes.
"""

from typing import Any, Dict, List, Optional, TypedDict

from app.models.common import Difficulty, SessionStatus


class ProblemState(TypedDict, total=False):
    """State for a single problem within the pipeline."""
    id: int
    content: str
    original_text: str
    source: str
    difficulty: str                   # "easy" | "hard" | "unknown"
    difficulty_score: float
    # Solving state
    solve_route: str                  # which route was taken
    wolfram_result: Optional[Dict[str, Any]]
    python_result: Optional[Dict[str, Any]]
    python_code: Optional[str]
    python_retry_count: int
    python_errors: List[str]
    search_result: Optional[Dict[str, Any]]
    llm_result: Optional[Dict[str, Any]]
    # Final
    solution: Optional[Dict[str, Any]]
    final_answer: str
    confidence: float
    tools_used: List[str]
    error: Optional[str]
    latency_ms: int
    cache_hit: bool


class AgentState(TypedDict, total=False):
    """Global state for the entire LangGraph pipeline.

    Every node reads from and writes to this state.
    """
    # ── Session ──────────────────────────────────────────────
    session_id: str
    status: str                       # SessionStatus value

    # ── Input ────────────────────────────────────────────────
    raw_text: Optional[str]
    raw_image_b64: Optional[str]
    upload_type: str                  # "text" | "image" | "mixed"

    # ── Extraction (Person 1) ────────────────────────────────
    problems: List[ProblemState]      # Extracted & parsed problems
    extraction_error: Optional[str]

    # ── Classification (Person 3) ────────────────────────────
    easy_problems: List[int]          # Problem IDs routed to easy
    hard_problems: List[int]          # Problem IDs routed to hard

    # ── Solving ──────────────────────────────────────────────
    current_problem_id: Optional[int] # Which problem is being solved
    results: Dict[int, Dict[str, Any]]  # problem_id → solution result

    # ── Aggregation ──────────────────────────────────────────
    final_results: List[Dict[str, Any]]
    total_latency_ms: int

    # ── Cache (Person 4) ─────────────────────────────────────
    cache_hits: Dict[int, Dict[str, Any]]  # problem_id → cached result
    cached_count: int

    # ── WebSocket streaming ──────────────────────────────────
    ws_messages: List[Dict[str, Any]]   # Messages to send to client

    # ── Errors ───────────────────────────────────────────────
    errors: List[str]
