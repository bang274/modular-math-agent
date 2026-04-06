"""
History Endpoint — Session history retrieval.

Person 5 owns this file.
"""

from fastapi import APIRouter, HTTPException, Query

from app.db.repository import session_repo
from app.models.response import HistoryListResponse, HistoryItem

router = APIRouter()


@router.get("/history", response_model=HistoryListResponse)
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Get paginated list of past solve sessions."""
    data = await session_repo.get_history(page=page, page_size=page_size)

    sessions = []
    for s in data.get("sessions", []):
        sessions.append(HistoryItem(
            session_id=s.get("id", ""),
            created_at=str(s.get("created_at", "")),
            problem_count=s.get("total_problems", 0),
            solved_count=s.get("solved_count", 0),
            preview=s.get("preview", "")[:200] if s.get("preview") else "",
        ))

    return HistoryListResponse(
        sessions=sessions,
        total=data.get("total", 0),
        page=page,
        page_size=page_size,
    )


@router.get("/history/{session_id}")
async def get_session_detail(session_id: str):
    """Get full details for a specific session."""
    session = await session_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
