"""
Shared enums and common types used across the entire application.

This file is a SHARED CONTRACT — changes here affect all team members.
Discuss before modifying.
"""

from enum import Enum


class Difficulty(str, Enum):
    """Problem difficulty classification."""
    EASY = "easy"
    HARD = "hard"
    UNKNOWN = "unknown"


class SolveRoute(str, Enum):
    """Which solving route was taken."""
    LLM_DIRECT = "llm_direct"
    WEB_SEARCH = "web_search"
    WOLFRAM = "wolfram"
    PYTHON_SANDBOX = "python_sandbox"
    FALLBACK_SEARCH = "fallback_search"
    CACHED = "cached"


class ProblemStatus(str, Enum):
    """Status of an individual problem in the pipeline."""
    PENDING = "pending"
    EXTRACTING = "extracting"
    CLASSIFYING = "classifying"
    SOLVING = "solving"
    SOLVED = "solved"
    FAILED = "failed"


class SessionStatus(str, Enum):
    """Status of the overall solve session."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL = "partial"        # Some problems solved, some failed
    FAILED = "failed"


class InputSource(str, Enum):
    """How the problem was provided."""
    TEXT = "text"
    IMAGE = "image"
    BOTH = "both"


class WSMessageType(str, Enum):
    """WebSocket message types for real-time updates."""
    EXTRACTION_COMPLETE = "extraction_complete"
    SOLVING_PROBLEM = "solving_problem"
    TOOL_CALLED = "tool_called"
    PROBLEM_SOLVED = "problem_solved"
    ALL_COMPLETE = "all_complete"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
