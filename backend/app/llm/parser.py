"""
Output Parsers — parse LLM responses into structured data.

Used by extractor, classifier, solvers, and aggregator nodes.
"""

import json
import re
from typing import Any, Dict, Optional

from app.telemetry.logger import logger


def parse_json_response(text: str) -> Optional[Dict[str, Any]]:
    """Extract and parse JSON from LLM response.

    Handles cases where LLM wraps JSON in markdown code blocks
    or includes extra text before/after.
    """
    if not text:
        return None

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract from markdown code block
    patterns = [
        r"```json\s*\n?(.*?)\n?\s*```",
        r"```\s*\n?(.*?)\n?\s*```",
        r"\{.*\}",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1) if "```" in pattern else match.group(0))
            except (json.JSONDecodeError, IndexError):
                continue

    logger.warning(f"Failed to parse JSON from LLM response: {text[:200]}...")
    return None


def extract_python_code(text: str) -> Optional[str]:
    """Extract Python code from LLM response.

    Handles markdown code blocks and raw code.
    """
    if not text:
        return None

    # Try to extract from markdown code block
    match = re.search(r"```python\s*\n(.*?)\n\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    match = re.search(r"```\s*\n(.*?)\n\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # If no code block, assume the entire text is code
    # (only if it looks like Python)
    if any(kw in text for kw in ["import ", "print(", "def ", "from "]):
        return text.strip()

    return None


def safe_latex_escape(text: str) -> str:
    """Ensure LaTeX strings are properly escaped for JSON transport."""
    if not text:
        return ""
    # Double-escape backslashes for JSON
    return text.replace("\\", "\\\\") if "\\\\" not in text else text
