import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from app.models.common import Difficulty, SessionStatus


def merge_dicts(a: Dict[Any, Any], b: Dict[Any, Any]) -> Dict[Any, Any]:
    """Reducer for merging dictionaries in parallel branches."""
    return {**a, **b}


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

    Equipped with reducers to support parallel node execution.
    """
    # ── Session ──────────────────────────────────────────────
    session_id: str
    status: str                       # SessionStatus value
    chat_history: Annotated[List[Dict[str, str]], operator.add]


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
    results: Annotated[Dict[int, Dict[str, Any]], merge_dicts]

    # ── Aggregation ──────────────────────────────────────────
    final_results: List[Dict[str, Any]]
    total_latency_ms: int
    needs_revision: List[int]


    # ── Cache (Person 4) ─────────────────────────────────────
    cache_hits: Dict[int, Dict[str, Any]]  # problem_id → cached result
    cached_count: int

    # ── WebSocket streaming ──────────────────────────────────
    ws_messages: Annotated[List[Dict[str, Any]], operator.add]

    # ── Guardrail (Gate) ─────────────────────────────────────
    is_guarded: bool                  # True if rejected or greeting
    guard_response: Optional[str]     # Direct response (greeting/refusal)
    intent: str                       # "math" | "greeting" | "rejected" | "unknown"

    # ── Errors ───────────────────────────────────────────────
    errors: Annotated[List[str], operator.add]


