"""
Person 3 — Python Code Execution Tool (Tier 2)
Runs LLM-generated Python code in a sandboxed exec() environment.
KEY FEATURE: Retries up to 3 times if the code fails, feeding the error
back to the Agent so it can self-correct.

=== TEAM (Person 3): Implement the retry logic and add safety restrictions ===

Security note: exec() is dangerous in production. For this lab, we use
a restricted globals dict. For production, use RestrictedPython or Docker.
"""

import io
import sys
import traceback
import math
from typing import Dict, Any

from src.telemetry.logger import logger


# ─── Safe globals for exec() ─────────────────────────────────────────────────
# Only allow math-related modules — no os, subprocess, etc.

ALLOWED_MODULES = {"math", "sympy", "fractions", "decimal", "cmath", "statistics"}


def _safe_import(name, *args, **kwargs):
    """Restricted import — only allows whitelisted math modules."""
    if name in ALLOWED_MODULES:
        return __builtins__["__import__"](name, *args, **kwargs) if isinstance(__builtins__, dict) else __import__(name, *args, **kwargs)
    raise ImportError(f"Module '{name}' is not allowed. Allowed: {', '.join(sorted(ALLOWED_MODULES))}")


def _build_safe_globals() -> Dict[str, Any]:
    """
    Build a restricted globals dictionary for exec().
    === TEAM (Person 3): Add/remove allowed functions as needed ===
    """
    import sympy

    safe = {
        "__builtins__": {
            "__import__": _safe_import,
            "print": print,
            "range": range,
            "len": len,
            "int": int,
            "float": float,
            "str": str,
            "abs": abs,
            "round": round,
            "sum": sum,
            "min": min,
            "max": max,
            "list": list,
            "tuple": tuple,
            "dict": dict,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "isinstance": isinstance,
            "True": True,
            "False": False,
            "None": None,
        },
        "math": math,
        "sympy": sympy,
        "sp": sympy,
        "sqrt": math.sqrt,
        "pi": math.pi,
        "e": math.e,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
    }
    return safe


# ─── Core execution with retry ───────────────────────────────────────────────

MAX_RETRIES = 3  # === TEAM (Person 3): Adjust this ===


def run_python_code(code: str) -> str:
    """
    Execute a Python code snippet and capture its output.
    If execution fails, returns the error message so the Agent can retry.

    Input: a Python code string that prints its result.
    Returns: captured stdout output, or error message.

    The Agent is responsible for calling this up to 3 times — each time
    the error is fed back as an Observation so the LLM can fix its code.
    """
    logger.log_event("PYTHON_EXEC", {"code_preview": code[:200], "code_len": len(code)})

    # Validate: block dangerous operations
    # === TEAM (Person 3): Add more safety checks ===
    blocked_keywords = ["import os", "import subprocess", "import sys",
                        "exec(", "eval(", "__import__", "open(", "file(",
                        "import shutil", "import socket", "import requests"]
    for keyword in blocked_keywords:
        if keyword in code:
            msg = f"BLOCKED: Code contains forbidden operation '{keyword}'. Only math operations are allowed."
            logger.log_event("PYTHON_BLOCKED", {"keyword": keyword})
            return msg

    # Capture stdout
    old_stdout = sys.stdout
    captured = io.StringIO()
    sys.stdout = captured

    try:
        safe_globals = _build_safe_globals()
        exec(code, safe_globals)
        output = captured.getvalue().strip()

        if not output:
            output = "(Code executed successfully but produced no output. Add print() to see results.)"

        logger.log_event("PYTHON_SUCCESS", {"output_preview": output[:200]})
        return output

    except Exception as e:
        error_msg = traceback.format_exc()
        # Return a concise error for the LLM to understand
        short_error = f"Python Error: {type(e).__name__}: {e}"
        logger.log_event("PYTHON_ERROR", {"error": short_error})
        return short_error

    finally:
        sys.stdout = old_stdout


# ─── Tool Registration ───────────────────────────────────────────────────────

PYTHON_TOOL = {
    "name": "run_python",
    "description": (
        "Execute Python code to solve a math problem. "
        "The code runs in a sandbox with access to math, sympy, and basic builtins. "
        "IMPORTANT: Your code MUST use print() to output the result. "
        "If the code fails, you will receive the error message — fix the code and try again (up to 3 attempts). "
        "Input: a Python code string. "
        "Example: run_python(import sympy as sp; x = sp.Symbol('x'); print(sp.diff(x**3, x)))"
    ),
    "function": run_python_code,
}
