"""
Guard Node — Safety & Relevance Filtering (Gate).

Person 0 owns this file.
Checks if the query is math-related, a greeting, or should be rejected.
"""

import json
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.llm.provider import get_extractor_llm
from app.llm.prompts import GUARDRAIL_SYSTEM_PROMPT
from app.telemetry.logger import logger


async def guard_node(state: AgentState) -> Dict[str, Any]:
    """Safety gate to filter non-math queries and handle greetings."""
    raw_text = state.get("raw_text", "")
    
    # If it's only an image, we might still want to check the image's context or just proceed
    # For now, we primarily guard the text.
    if not raw_text and state.get("raw_image_b64"):
        return {
            "is_guarded": False,
            "intent": "math",
            "ws_messages": [
                {"type": "guard_check", "data": {"status": "passed", "reason": "image_only"}}
            ]
        }

    logger.info(f"[Guard] Checking query: {raw_text[:50]}...")
    
    llm = get_extractor_llm()  # Use the fast extractor model for guarding
    
    try:
        response = await llm.ainvoke([
            SystemMessage(content=GUARDRAIL_SYSTEM_PROMPT),
            HumanMessage(content=f"User Query: {raw_text}")
        ])
        
        # Parse JSON output
        result = json.loads(response.content)
        intent = result.get("intent", "unknown")
        guard_response = result.get("response", "")
        
        is_guarded = intent in ["greeting", "rejected", "out_of_scope"]
        
        logger.info(f"[Guard] Intent: {intent} | Guarded: {is_guarded}")
        
        return {
            "is_guarded": is_guarded,
            "intent": intent,
            "guard_response": guard_response,
            "ws_messages": [
                {
                    "type": "guard_check", 
                    "data": {
                        "intent": intent, 
                        "guarded": is_guarded,
                        "response": guard_response
                    }
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"[Guard] Error: {e}")
        # On error, we default to passing the query to be safe, or we could reject it.
        # Let's pass it to the extractor.
        return {"is_guarded": False, "intent": "math"}
