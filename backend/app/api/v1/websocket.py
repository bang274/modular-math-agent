"""
WebSocket Endpoint — Real-time solve progress streaming.

Person 5 owns this file.
Features: heartbeat keepalive, per-session connection limits, broadcast utility.
"""

import asyncio
import json
import uuid
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agent.graph import run_agent_pipeline
from app.telemetry.logger import logger

router = APIRouter()

# ── Connection management ────────────────────────────────────
MAX_CONNECTIONS_PER_SESSION = 5
HEARTBEAT_INTERVAL_SECONDS = 30

# Active WebSocket connections per session
active_connections: Dict[str, Set[WebSocket]] = {}


async def broadcast(session_id: str, message: dict) -> None:
    """Send a message to all WebSocket clients connected to a session.

    Silently removes dead connections.
    """
    if session_id not in active_connections:
        return

    dead: Set[WebSocket] = set()
    for ws in active_connections[session_id]:
        try:
            await ws.send_json(message)
        except Exception:
            dead.add(ws)

    # Cleanup dead connections
    active_connections[session_id] -= dead
    if not active_connections[session_id]:
        del active_connections[session_id]


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket for real-time solve progress.

    Client connects with a session_id, then sends a solve request.
    Server streams progress messages as the pipeline runs.

    Client → Server messages:
        {"action": "solve", "text": "...", "image_b64": "..."}
        {"action": "ping"}

    Server → Client messages:
        {"type": "connected", "data": {...}}
        {"type": "extraction_complete", "data": {...}}
        {"type": "solving_problem", "data": {...}}
        {"type": "tool_called", "data": {...}}
        {"type": "problem_solved", "data": {...}}
        {"type": "all_complete", "data": {...}}
        {"type": "error", "data": {...}}
        {"type": "pong", "data": {}}
        {"type": "heartbeat", "data": {}}
    """
    # ── Connection limit check ───────────────────────────────
    current_count = len(active_connections.get(session_id, set()))
    if current_count >= MAX_CONNECTIONS_PER_SESSION:
        await websocket.close(
            code=1008,
            reason=f"Max {MAX_CONNECTIONS_PER_SESSION} connections per session",
        )
        return

    await websocket.accept()

    # Register connection
    if session_id not in active_connections:
        active_connections[session_id] = set()
    active_connections[session_id].add(websocket)

    logger.info(
        f"[WS] Client connected: session={session_id} "
        f"(total={len(active_connections[session_id])})"
    )

    # ── Start heartbeat task ─────────────────────────────────
    heartbeat_task = asyncio.create_task(
        _heartbeat_loop(websocket, session_id)
    )

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "data": {
                "session_id": session_id,
                "heartbeat_interval": HEARTBEAT_INTERVAL_SECONDS,
            },
        })

        while True:
            # Wait for client message
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)

            action = data.get("action")

            if action == "solve":
                text = data.get("text")
                image_b64 = data.get("image_b64")

                if not text and not image_b64:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": "text or image_b64 required"},
                    })
                    continue

                # Run pipeline and stream messages
                await _run_and_stream(
                    websocket, session_id, text, image_b64
                )

            elif action == "ping":
                await websocket.send_json({"type": "pong", "data": {}})

    except WebSocketDisconnect:
        logger.info(f"[WS] Client disconnected: session={session_id}")
    except Exception as e:
        logger.error(f"[WS] Error: {e}")
    finally:
        # Cancel heartbeat
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass

        # Cleanup connection
        if session_id in active_connections:
            active_connections[session_id].discard(websocket)
            if not active_connections[session_id]:
                del active_connections[session_id]


async def _heartbeat_loop(websocket: WebSocket, session_id: str) -> None:
    """Send periodic heartbeat messages to keep the connection alive."""
    try:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
            try:
                await websocket.send_json({"type": "heartbeat", "data": {}})
            except Exception:
                break  # Connection is dead, exit loop
    except asyncio.CancelledError:
        pass


async def _run_and_stream(
    websocket: WebSocket,
    session_id: str,
    text: str = None,
    image_b64: str = None,
):
    """Run the agent pipeline and stream intermediate results."""
    try:
        await websocket.send_json({
            "type": "processing",
            "data": {"message": "Starting pipeline..."},
        })

        # Run pipeline
        final_state = await run_agent_pipeline(
            text=text,
            image_b64=image_b64,
            session_id=session_id,
        )

        # Send all accumulated WS messages (also broadcast to other clients)
        ws_messages = final_state.get("ws_messages", [])
        for msg in ws_messages:
            try:
                await broadcast(session_id, msg)
                await asyncio.sleep(0.05)  # Small delay for smooth streaming
            except Exception:
                break

    except Exception as e:
        logger.error(f"[WS] Pipeline error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"message": str(e)},
            })
        except Exception:
            pass
