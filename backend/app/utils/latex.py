"""
Utility functions for LaTeX validation and formatting.
"""

import re
from typing import Optional


def validate_latex(text: str) -> bool:
    """Basic validation that a string contains valid-ish LaTeX."""
    if not text:
        return False
    # Check balanced braces
    open_count = text.count("{")
    close_count = text.count("}")
    return open_count == close_count


def clean_latex_for_display(text: str) -> str:
    """Clean LaTeX for frontend display."""
    if not text:
        return ""
    # Ensure proper escaping for JSON transport
    cleaned = text.strip()
    return cleaned


def wrap_in_display_math(latex: str) -> str:
    """Wrap LaTeX in display math delimiters if not already wrapped."""
    if not latex:
        return ""
    if latex.startswith("$$") or latex.startswith("\\["):
        return latex
    return f"$${latex}$$"
