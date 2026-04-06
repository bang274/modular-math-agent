"""
LangGraph Agent Pipeline — Main Graph Definition.

Person 3 owns this file.
This is the core orchestrator that wires all nodes and edges together.
"""

import uuid
from typing import Any, Dict, Optional

from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes.guard import guard_node
from app.agent.nodes.extractor import extractor_node
from app.agent.nodes.classifier import classifier_node
from app.agent.nodes.easy_solver import easy_solver_node
from app.agent.nodes.hard_solver import hard_solver_node
from app.agent.nodes.aggregator import aggregator_node
from app.agent.nodes.critic import critic_node
from app.agent.nodes.cache_node import cache_check_node, cache_store_node
from app.agent.edges.routing import (
    route_after_guard,
    route_after_extraction,
    route_after_cache,
    route_after_classifier,
    route_after_critic,
)



from app.telemetry.logger import logger


def build_agent_graph() -> StateGraph:
    """Build and compile the LangGraph agent pipeline.

    Graph topology:
        extractor → cache_check → classifier → [easy_solver | hard_solver | both]
            → aggregator → cache_store → END

    Returns:
        Compiled LangGraph StateGraph ready to invoke.
    """
    graph = StateGraph(AgentState)

    # ── Add nodes ────────────────────────────────────────────
    graph.add_node("guard", guard_node)
    graph.add_node("extractor", extractor_node)
    graph.add_node("cache_check", cache_check_node)
    graph.add_node("classifier", classifier_node)
    graph.add_node("easy_solver", easy_solver_node)
    graph.add_node("hard_solver", hard_solver_node)
    graph.add_node("critic", critic_node)
    graph.add_node("aggregator", aggregator_node)
    graph.add_node("cache_store", cache_store_node)


    # Special terminal nodes
    async def guarded_end_node(state: AgentState) -> Dict[str, Any]:
        """Custom terminal node for greetings and rejections."""
        guard_response = state.get("guard_response", "")
        return {
            "status": "completed",
            "final_results": [
                {
                    "problem_id": 0,
                    "original": state.get("raw_text", ""),
                    "difficulty": "unknown",
                    "final_answer": guard_response,
                    "steps": [{"step": 1, "description": guard_response, "latex": ""}],
                    "confidence": 1.0,
                    "tool_trace": {"route": "guardrail"},
                }
            ],
        }

    async def error_end_node(state: AgentState) -> Dict[str, Any]:
        return {
            "status": "failed",
            "final_results": [],
            "ws_messages": state.get("ws_messages", []) + [
                {
                    "type": "error",
                    "data": {
                        "message": state.get("extraction_error", "Unknown error"),
                    },
                }
            ],
        }

    graph.add_node("guarded_end", guarded_end_node)
    graph.add_node("error_end", error_end_node)


    # ── Set entry point ──────────────────────────────────────
    graph.set_entry_point("guard")


    # ── Add edges ────────────────────────────────────────────

    # After guard → proceed to extraction or end
    graph.add_conditional_edges(
        "guard",
        route_after_guard,
        {
            "extractor": "extractor",
            "guarded_end": "guarded_end",
        },
    )

    # After extraction → cache check or error
    graph.add_conditional_edges(
        "extractor",
        route_after_extraction,
        {
            "cache_check": "cache_check",
            "aggregator": "aggregator",
            "error_end": "error_end",
        },
    )



    # After cache check → classifier or aggregator (if all cached)
    graph.add_conditional_edges(
        "cache_check",
        route_after_cache,
        {
            "classifier": "classifier",
            "aggregator": "aggregator",
        },
    )

    # After classifier → route to appropriate solver(s)
    # If route_after_classifier returns a list, LangGraph runs them in parallel.
    graph.add_conditional_edges(
        "classifier",
        route_after_classifier,
        {
            "easy_solver": "easy_solver",
            "hard_solver": "hard_solver",
            "aggregator": "aggregator",
        },
    )

    # Parallel solvers → critic (Fan-in)
    graph.add_edge("easy_solver", "critic")
    graph.add_edge("hard_solver", "critic")

    # After critic → loop back or aggregator
    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "hard_solver": "hard_solver",
            "aggregator": "aggregator",
        },
    )



    # Aggregator → cache store
    graph.add_edge("aggregator", "cache_store")

    # Cache store → END
    graph.add_edge("cache_store", END)

    # End nodes → END
    graph.add_edge("guarded_end", END)
    graph.add_edge("error_end", END)


    return graph.compile()


# ── Compile once at module level ─────────────────────────────
agent_graph = build_agent_graph()


async def run_agent_pipeline(
    text: Optional[str] = None,
    image_b64: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the full agent pipeline.

    Args:
        text: Optional text input with math problems.
        image_b64: Optional base64-encoded image of math problems.
        session_id: Optional session ID (auto-generated if not provided).

    Returns:
        Final state with all results.
    """
    if not text and not image_b64:
        raise ValueError("At least one of text or image must be provided")

    # Determine upload type
    if text and image_b64:
        upload_type = "both"
    elif image_b64:
        upload_type = "image"
    else:
        upload_type = "text"

    # Load previous history from DB if session exists
    from app.db.repository import session_repo
    chat_history = []
    
    if session_id:
        session = await session_repo.get_session(session_id)
        if session and session.get("solutions"):
            # Reconstruct history from previous solutions
            # We take the last 5 problems/solutions for memory
            for sol in session["solutions"][-5:]:
                chat_history.append({"role": "user", "content": sol.get("content", "")})
                chat_history.append({"role": "assistant", "content": sol.get("final_answer", "")})

    # Context Compression for long history
    if len(chat_history) > 10:
        logger.info(f"[Pipeline] Compressing history (currently {len(chat_history)} turns)")
        # We keep the first 2 (intro) and last 4 (recent) turns, 
        # and replace the middle with a summary (simplification)
        compressed = chat_history[:2] + [{"role": "system", "content": "...[previous context summarized]..."}] + chat_history[-6:]
        chat_history = compressed

    # Build initial state
    initial_state: AgentState = {
        "session_id": session_id or str(uuid.uuid4()),
        "status": "processing",
        "chat_history": chat_history,
        "needs_revision": [],

        "raw_text": text,
        "raw_image_b64": image_b64,
        "upload_type": upload_type,
        "problems": [],
        "extraction_error": None,
        "easy_problems": [],
        "hard_problems": [],
        "current_problem_id": None,
        "results": {},
        "final_results": [],
        "total_latency_ms": 0,
        "cache_hits": {},
        "cached_count": 0,
        "ws_messages": [],
        "errors": [],
    }

    logger.info(
        f"[Pipeline] Starting session {initial_state['session_id']} "
        f"with {len(chat_history)//2} turns of history"
    )

    # Run the graph
    final_state = await agent_graph.ainvoke(initial_state)


    logger.info(
        f"[Pipeline] Session {initial_state['session_id']} completed: "
        f"status={final_state.get('status')}"
    )

    return final_state
