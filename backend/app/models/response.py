"""
API Response schemas.

Person 5 (API) owns these schemas.
Shared across: API layer, aggregator node, frontend types.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.common import Difficulty, SolveRoute, SessionStatus


class SolutionStep(BaseModel):
    """A single step in the solution."""
    step: int = Field(..., description="Step number")
    description: str = Field(..., description="What this step does")
    latex: str = Field("", description="LaTeX content for this step")


class ToolTrace(BaseModel):
    """Trace of which tools were used to solve a problem."""
    route: str = Field(..., description="Solving route taken")
    tools_used: List[str] = Field(default_factory=list)
    attempts: int = Field(1, description="Number of attempts")
    cache_hit: bool = Field(False, description="Whether result was cached")
    latency_ms: int = Field(0, description="Time to solve in ms")
    errors: List[str] = Field(
        default_factory=list,
        description="Any errors encountered during solving",
    )


class ProblemResult(BaseModel):
    """Result for a single problem."""
    problem_id: int
    original: str = Field(..., description="Original problem text")
    difficulty: Difficulty = Difficulty.UNKNOWN
    solution: Optional[Dict[str, Any]] = Field(
        None,
        description="Solution with steps and final answer",
    )
    steps: List[SolutionStep] = Field(default_factory=list)
    final_answer: str = Field("", description="Final answer in LaTeX")
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    images: List[str] = Field(
        default_factory=list, 
        description="Base64 encoded images (e.g., mathematical plots)"
    )
    tool_trace: ToolTrace = Field(default_factory=lambda: ToolTrace(route="unknown"))
    error: Optional[str] = Field(None, description="Error message if failed")



class SolveResponse(BaseModel):
    """Full response for a solve session."""
    session_id: str
    status: SessionStatus = SessionStatus.PROCESSING
    ws_url: Optional[str] = Field(None, description="WebSocket URL for live updates")
    results: List[ProblemResult] = Field(default_factory=list)
    total_problems: int = Field(0)
    solved_count: int = Field(0)
    failed_count: int = Field(0)
    cached_count: int = Field(0)
    total_latency_ms: int = Field(0)


class HistoryItem(BaseModel):
    """Summary of a past solve session."""
    session_id: str
    created_at: str
    problem_count: int
    solved_count: int
    preview: str = Field("", description="First problem text preview")


class HistoryListResponse(BaseModel):
    """Paginated history list."""
    sessions: List[HistoryItem] = Field(default_factory=list)
    total: int = Field(0)
    page: int = Field(1)
    page_size: int = Field(20)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = "1.0.0"
    redis_connected: bool = False
    db_connected: bool = False


class WSMessage(BaseModel):
    """WebSocket message format."""
    type: str
    data: Dict[str, Any] = Field(default_factory=dict)
