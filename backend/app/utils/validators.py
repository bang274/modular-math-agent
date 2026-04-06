"""
Input Validators.

Person 1 owns this file.
"""

from typing import Optional, Tuple

from app.config import get_settings


def validate_text_input(text: Optional[str]) -> Tuple[bool, str]:
    """Validate text input."""
    if not text:
        return True, ""  # Text is optional if image is provided
    if len(text.strip()) == 0:
        return False, "Text input is empty"
    if len(text) > 10000:
        return False, f"Text too long: {len(text)} chars (max: 10000)"
    return True, ""


def validate_upload_size(size_bytes: int) -> Tuple[bool, str]:
    """Validate upload file size."""
    settings = get_settings()
    max_bytes = settings.max_upload_size_bytes
    if size_bytes > max_bytes:
        return False, f"File too large: {size_bytes} bytes (max: {max_bytes})"
    return True, ""
