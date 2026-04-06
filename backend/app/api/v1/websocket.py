"""
WebSocket Endpoint — Real-time solve progress streaming.

Person 5 owns this file.
"""

import asyncio
import json
import uuid
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agent.graph import run_agent_pipeline
from app.telemetry.logger import logger

router = APIRouter()

# Active WebSocket connections per session
active_connections: Dict[str, Set[WebSocket]] = {}


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket for real-time solve progress.

    Client connects with a session_id, then sends a solve request.
    Server streams progress messages as the pipeline runs.

    Client → Server messages:
        {"action": "solve", "text": "...", "image_b64": "..."}

    Server → Client messages:
        {"type": "extraction_complete", "data": {...}}
        {"type": "solving_problem", "data": {...}}
        {"type": "tool_called", "data": {...}}
        {"type": "problem_solved", "data": {...}}
        {"type": "all_complete", "data": {...}}
        {"type": "error", "data": {...}}
    """
    await websocket.accept()

    # Register connection
    if session_id not in active_connections:
        active_connections[session_id] = set()
    active_connections[session_id].add(websocket)

    logger.info(f"[WS] Client connected: session={session_id}")

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "data": {"session_id": session_id},
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

                # Run pipeline in background and stream messages
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
        # Cleanup connection
        if session_id in active_connections:
            active_connections[session_id].discard(websocket)
            if not active_connections[session_id]:
                del active_connections[session_id]


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

        # Send all accumulated WS messages
        ws_messages = final_state.get("ws_messages", [])
        for msg in ws_messages:
            try:
                await websocket.send_json(msg)
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
