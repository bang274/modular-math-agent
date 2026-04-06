"""
Extractor — Input Processing & LLM Extraction (Person 1).

Chức năng:
  - extract_problems_from_text(text)    → extract từ plain text
  - extract_problems_from_ocr(ocr_text) → extract từ kết quả OCR

Output mỗi hàm:
  {"problems": [{"id": "bai_1", "content": "..."}], "error": None | str}
"""

from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.llm.provider import get_extractor_llm
from app.llm.prompts import EXTRACTOR_SYSTEM_PROMPT, EXTRACTOR_IMAGE_PROMPT
from app.llm.parser import parse_json_response
from app.telemetry.logger import logger


def _parse_problems(parsed: Optional[Dict]) -> List[Dict[str, Any]]:
    """Chuyển JSON từ LLM thành list problem chuẩn hoá."""
    if not parsed or "problems" not in parsed:
        return []
    result = []
    for idx, p in enumerate(parsed["problems"], start=1):
        content = p.get("content", "").strip()
        if content:
            result.append({"id": f"bai_{idx}", "content": content})
    return result


async def extract_problems_from_text(text: str) -> Dict[str, Any]:
    """Gọi LLM để extract bài toán từ text thuần.

    Returns:
        {"problems": [{"id": "bai_1", "content": "..."}], "error": None | str}
    """
    try:
        llm = get_extractor_llm()
        messages = [
            SystemMessage(content=EXTRACTOR_SYSTEM_PROMPT),
            HumanMessage(content=f"Extract math problems from:\n\n{text}"),
        ]
        
        response = await llm.ainvoke(messages)
        problems = _parse_problems(parse_json_response(response.content))
        if not problems:
            return {"problems": [], "error": "No valid math problems found in text"}
        logger.info(f"[Extractor] text → {len(problems)} problem(s)")
        return {"problems": problems, "error": None}
    except Exception as e:
        logger.error(f"[Extractor] extract_from_text error: {e}")
        return {"problems": [], "error": f"Lỗi cấu hình LLM hoặc gọi API: {str(e)}"}


async def extract_problems_from_image(image_b64: str) -> Dict[str, Any]:
    """Gọi LLM (Vision) để extract bài toán trực tiếp từ ảnh.

    Returns:
        {"problems": [{"id": "bai_1", "content": "..."}], "error": None | str}
    """
    try:
        llm = get_extractor_llm()
        messages = [
            SystemMessage(content=EXTRACTOR_SYSTEM_PROMPT),
            HumanMessage(content=[
                {"type": "text", "text": EXTRACTOR_IMAGE_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
            ])
        ]
        
        response = await llm.ainvoke(messages)
        problems = _parse_problems(parse_json_response(response.content))
        if not problems:
            return {"problems": [], "error": "No valid math problems found in image"}
        logger.info(f"[Extractor] image vision → {len(problems)} problem(s)")
        return {"problems": problems, "error": None}
    except Exception as e:
        logger.error(f"[Extractor] extract_from_image error: {e}")
        return {"problems": [], "error": f"Lỗi cấu hình LLM hoặc gọi API: {str(e)}"}


# ── LangGraph node — GIỮ NGUYÊN, dùng bởi graph.py (Person 3) ─────────

async def extractor_node(state: AgentState) -> Dict[str, Any]:
    """LangGraph entry node — đọc state, trả về problems list đầy đủ schema."""
    logger.info(f"[Extractor] session={state.get('session_id', 'unknown')}")

    raw_text = state.get("raw_text")
    raw_image = state.get("raw_image_b64")
    upload_type = state.get("upload_type", "text")
    llm = get_extractor_llm()

    try:
        messages = [SystemMessage(content=EXTRACTOR_SYSTEM_PROMPT)]

        if upload_type == "image" and raw_image:
            messages.append(HumanMessage(content=[
                {"type": "text", "text": EXTRACTOR_IMAGE_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{raw_image}"}},
            ]))
        elif upload_type == "both" and raw_text and raw_image:
            messages.append(HumanMessage(content=[
                {"type": "text", "text": (
                    f"Text input: {raw_text}\n\n"
                    "Also extract problems from the image below:"
                )},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{raw_image}"}},
            ]))
        else:
            messages.append(HumanMessage(content=f"Extract math problems from:\n\n{raw_text}"))

        response = await llm.ainvoke(messages)
        parsed = parse_json_response(response.content)

        if not parsed or "problems" not in parsed:
            logger.warning(f"[Extractor] Parse failed: {response.content[:200]}")
            return {
                "problems": [],
                "extraction_error": "Failed to extract problems from input",
                "ws_messages": state.get("ws_messages", []) + [
                    {"type": "error", "data": {"message": "Extraction failed"}}
                ],
            }

        problems = []
        for idx, p in enumerate(parsed["problems"], start=1):
            content = p.get("content", "").strip()
            if not content:
                continue
            problems.append({
                "id": p.get("id", idx),
                "content": content,
                "original_text": content,
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

        if not problems:
            return {"problems": [], "extraction_error": "No valid math problems found in input"}

        logger.info(f"[Extractor] Extracted {len(problems)} problems")
        return {
            "problems": problems,
            "extraction_error": None,
            "ws_messages": state.get("ws_messages", []) + [{
                "type": "extraction_complete",
                "data": {
                    "total_problems": len(problems),
                    "problems": [{"id": p["id"], "content": p["content"]} for p in problems],
                },
            }],
        }

    except Exception as e:
        logger.error(f"[Extractor] Error: {e}")
        return {
            "problems": [],
            "extraction_error": str(e),
            "errors": state.get("errors", []) + [f"Extraction error: {e}"],
        }
