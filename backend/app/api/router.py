"""
API Router — Central router that includes all v1 routes.

Person 5 owns this file.
"""

from fastapi import APIRouter

from app.api.v1 import solve, upload, history, health, websocket
from app.api.v1 import extract  # Person 1 — Input extraction endpoints

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(extract.router, tags=["Extract"])   # Person 1
api_router.include_router(solve.router, tags=["Solve"])
api_router.include_router(upload.router, tags=["Upload"])
api_router.include_router(history.router, tags=["History"])
api_router.include_router(websocket.router, tags=["WebSocket"])
