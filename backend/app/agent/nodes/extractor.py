"""
Extractor Node — Input Processing & OCR.

Person 1 owns this file.
Handles: text/image/both → LLM extraction → JSON ProblemSet.
"""

import base64
import json
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.llm.provider import get_extractor_llm

from app.llm.prompts import EXTRACTOR_SYSTEM_PROMPT, EXTRACTOR_IMAGE_PROMPT
from app.llm.parser import parse_json_response
from app.telemetry.logger import logger


async def extractor_node(state: AgentState) -> Dict[str, Any]:
    """Extract math problems from raw input (text, image, or both).

    This node:
    1. Detects input type (text / image / both)
    2. Calls LLM with appropriate prompt (vision for images)
    3. Parses response into structured Problem list
    4. Validates the extraction output

    Returns:
        Updated state with 'problems' list populated.
    """
    logger.info(f"[Extractor] Processing session {state.get('session_id', 'unknown')}")

    raw_text = state.get("raw_text")
    raw_image = state.get("raw_image_b64")
    upload_type = state.get("upload_type", "text")

    llm = get_extractor_llm()


    try:
        messages = [SystemMessage(content=EXTRACTOR_SYSTEM_PROMPT)]

        if upload_type == "image" and raw_image:
            # Image-only: use vision model
            messages.append(
                HumanMessage(content=[
                    {"type": "text", "text": EXTRACTOR_IMAGE_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{raw_image}",
                        },
                    },
                ])
            )
        elif upload_type == "both" and raw_text and raw_image:
            # Both text and image
            messages.append(
                HumanMessage(content=[
                    {
                        "type": "text",
                        "text": (
                            f"The user provided both text and an image.\n"
                            f"Text input: {raw_text}\n\n"
                            f"Also extract any additional problems from the image below:"
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{raw_image}",
                        },
                    },
                ])
            )
        else:
            # Text-only
            messages.append(
                HumanMessage(content=f"Extract math problems from:\n\n{raw_text}")
            )

        # Call LLM
        response = await llm.ainvoke(messages)
        response_text = response.content

        # Parse JSON response
        parsed = parse_json_response(response_text)

        if not parsed or "problems" not in parsed:
            logger.warning(f"[Extractor] Failed to parse, raw: {response_text[:300]}")
            return {
                "problems": [],
                "extraction_error": "Failed to extract problems from input",
                "ws_messages": state.get("ws_messages", []) + [
                    {"type": "error", "data": {"message": "Extraction failed"}}
                ],
            }

        # Build problem states
        problems = []
        for p in parsed["problems"]:
            problems.append({
                "id": p.get("id", len(problems) + 1),
                "content": p.get("content", ""),
                "original_text": p.get("content", ""),
                "source": upload_type,
                "difficulty": "unknown",
                "difficulty_score": 0.0,
                "solve_route": "",
                "wolfram_result": None,
                "python_result": None,
                "python_code": None,
                "python_retry_count": 0,
                "python_errors": [],
                "search_result": None,
                "llm_result": None,
                "solution": None,
                "final_answer": "",
                "confidence": 0.0,
                "tools_used": [],
                "error": None,
                "latency_ms": 0,
                "cache_hit": False,
            })

        # Filter out empty problems
        problems = [p for p in problems if p["content"].strip()]

        if not problems:
            return {
                "problems": [],
                "extraction_error": "No valid math problems found in input",
            }

        logger.info(f"[Extractor] Extracted {len(problems)} problems")

        return {
            "problems": problems,
            "extraction_error": None,
            "ws_messages": state.get("ws_messages", []) + [
                {
                    "type": "extraction_complete",
                    "data": {
                        "total_problems": len(problems),
                        "problems": [
                            {"id": p["id"], "content": p["content"]}
                            for p in problems
                        ],
                    },
                }
            ],
        }

    except Exception as e:
        logger.error(f"[Extractor] Error: {e}")
        return {
            "problems": [],
            "extraction_error": str(e),
            "errors": state.get("errors", []) + [f"Extraction error: {e}"],
        }
