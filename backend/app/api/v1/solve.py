"""
Solve Endpoint — Main problem-solving API.

Person 5 owns this file.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import check_rate_limit
from app.models.request import SolveRequest
from app.models.response import SolveResponse, ProblemResult, ToolTrace, SolutionStep
from app.models.common import SessionStatus, Difficulty
from app.agent.graph import run_agent_pipeline
from app.db.repository import session_repo
from app.telemetry.logger import logger
from app.telemetry.metrics import metrics

router = APIRouter()


@router.post("/solve", response_model=SolveResponse)
async def solve_text(
    request: SolveRequest,
    _: None = Depends(check_rate_limit),
):
    """Solve math problems from text input.

    Runs the full agent pipeline:
    extract → cache check → classify → solve → aggregate → cache store
    """
    session_id = str(uuid.uuid4())
    logger.info(f"[API] POST /solve session={session_id}")

    try:
        # Run agent pipeline
        final_state = await run_agent_pipeline(
            text=request.text,
            session_id=session_id,
        )

        # Build response
        response = _build_response(session_id, final_state)

        # Save to database (async, non-blocking for response)
        await _save_to_db(session_id, final_state, response)

        # Record metrics
        metrics.record_request(response.total_problems)
        metrics.record_latency(response.total_latency_ms)

        return response

    except Exception as e:
        logger.error(f"[API] Solve error: {e}")
        metrics.record_error()
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@router.get("/solve/{session_id}", response_model=SolveResponse)
async def get_solve_result(session_id: str):
    """Get results of a previous solve session."""
    session = await session_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Reconstruct response from DB
    results = []
    for sol in session.get("solutions", []):
        import json
        steps_raw = sol.get("steps_json", "[]")
        steps = json.loads(steps_raw) if isinstance(steps_raw, str) else steps_raw

        results.append(ProblemResult(
            problem_id=sol["problem_id"],
            original=sol.get("content", ""),
            difficulty=sol.get("difficulty", "unknown"),
            steps=[SolutionStep(**s) if isinstance(s, dict) else s for s in steps],
            final_answer=sol.get("final_answer", ""),
            confidence=sol.get("confidence", 0.0),
            tool_trace=ToolTrace(
                route=sol.get("solve_route", ""),
                tools_used=json.loads(sol.get("tools_used", "[]")),
                cache_hit=bool(sol.get("cache_hit")),
                latency_ms=sol.get("latency_ms", 0),
            ),
            error=sol.get("error"),
        ))

    return SolveResponse(
        session_id=session_id,
        status=session.get("status", "completed"),
        results=results,
        total_problems=session.get("total_problems", 0),
        solved_count=session.get("solved_count", 0),
        failed_count=session.get("failed_count", 0),
        cached_count=session.get("cached_count", 0),
        total_latency_ms=session.get("total_latency_ms", 0),
    )


def _build_response(session_id: str, state: dict) -> SolveResponse:
    """Build SolveResponse from final agent state."""
    final_results = state.get("final_results", [])

    results = []
    for r in final_results:
        steps = []
        for s in r.get("steps", []):
            if isinstance(s, dict):
                steps.append(SolutionStep(
                    step=s.get("step", 0),
                    description=s.get("description", ""),
                    latex=s.get("latex", ""),
                ))

        trace_data = r.get("tool_trace", {})
        results.append(ProblemResult(
            problem_id=r.get("problem_id", 0),
            original=r.get("original", ""),
            difficulty=r.get("difficulty", "unknown"),
            steps=steps,
            final_answer=r.get("final_answer", ""),
            confidence=r.get("confidence", 0.0),
            tool_trace=ToolTrace(
                route=trace_data.get("route", "unknown"),
                tools_used=trace_data.get("tools_used", []),
                attempts=trace_data.get("attempts", 1),
                cache_hit=trace_data.get("cache_hit", False),
                latency_ms=trace_data.get("latency_ms", 0),
                errors=trace_data.get("errors", []),
            ),
            error=r.get("error"),
        ))

    solved = sum(1 for r in results if not r.error)
    failed = sum(1 for r in results if r.error)
    cached = sum(1 for r in results if r.tool_trace.cache_hit)

    status = SessionStatus.COMPLETED
    if failed == len(results):
        status = SessionStatus.FAILED
    elif failed > 0:
        status = SessionStatus.PARTIAL

    return SolveResponse(
        session_id=session_id,
        status=status,
        ws_url=f"/api/v1/ws/{session_id}",
        results=results,
        total_problems=len(results),
        solved_count=solved,
        failed_count=failed,
        cached_count=cached,
        total_latency_ms=state.get("total_latency_ms", 0),
    )


async def _save_to_db(session_id: str, state: dict, response: SolveResponse):
    """Save session and results to database."""
    try:
        await session_repo.save_session(
            session_id=session_id,
            status=response.status,
            upload_type=state.get("upload_type", "text"),
            total_problems=response.total_problems,
            solved_count=response.solved_count,
            failed_count=response.failed_count,
            cached_count=response.cached_count,
            total_latency_ms=response.total_latency_ms,
            raw_text=state.get("raw_text"),
        )

        problems = state.get("problems", [])
        for result in state.get("final_results", []):
            pid = result.get("problem_id")
            problem = next((p for p in problems if p["id"] == pid), None)
            if problem:
                await session_repo.save_solution(
                    session_id=session_id,
                    problem_id=pid,
                    content=problem["content"],
                    result=result,
                )
    except Exception as e:
        logger.warning(f"[API] Error saving to DB (non-fatal): {e}")
