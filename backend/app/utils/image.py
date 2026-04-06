"""
Image preprocessing utilities.

Person 1 owns this file.
Handles: validation, resizing, base64 encoding for LLM vision, OCR API calls.
"""

import base64
import io
from typing import Optional, Tuple

from app.telemetry.logger import logger

# Supported image types
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_DIMENSION = 2048  # Max pixel dimension for LLM vision


def validate_image_type(content_type: str) -> bool:
    """Check if the image MIME type is supported."""
    return content_type.lower() in SUPPORTED_IMAGE_TYPES


def encode_image_to_base64(image_bytes: bytes) -> str:
    """Encode raw image bytes to base64 string."""
    return base64.b64encode(image_bytes).decode("utf-8")


def decode_base64_image(b64_string: str) -> bytes:
    """Decode a base64 string to raw image bytes."""
    return base64.b64decode(b64_string)


async def preprocess_image(
    image_bytes: bytes,
    max_size_bytes: int = 10 * 1024 * 1024,
) -> Tuple[str, Optional[str]]:
    """Preprocess an image for LLM vision input.

    Args:
        image_bytes: Raw image file bytes.
        max_size_bytes: Maximum allowed file size.

    Returns:
        Tuple of (base64_string, error_message).
        error_message is None if successful.
    """
    if len(image_bytes) > max_size_bytes:
        return "", f"Image too large: {len(image_bytes)} bytes (max: {max_size_bytes})"

    if len(image_bytes) < 100:
        return "", "Image file too small, possibly corrupted"

    try:
        # Try to resize with PIL if available
        try:
            from PIL import Image

            img = Image.open(io.BytesIO(image_bytes))

            # Resize if too large
            if max(img.size) > MAX_IMAGE_DIMENSION:
                ratio = MAX_IMAGE_DIMENSION / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"[Image] Resized to {new_size}")

                # Convert back to bytes
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=85)
                image_bytes = buffer.getvalue()

        except ImportError:
            # PIL not available, use raw bytes
            logger.debug("[Image] PIL not available, skipping resize")

        b64 = encode_image_to_base64(image_bytes)
        return b64, None

    except Exception as e:
        return "", f"Image processing error: {str(e)}"


def get_image_mime_type(content_type: Optional[str]) -> str:
    """Normalize MIME type string. Defaults to image/jpeg."""
    if not content_type:
        return "image/jpeg"
    return content_type.lower()


async def call_ocr_api(image_b64: str, mime_type: str = "image/jpeg") -> Tuple[str, Optional[str]]:
    """Call an external OCR API to extract text from a math image.

    Args:
        image_b64: Base64-encoded image string (output of preprocess_image).
        mime_type:  MIME type of the image (e.g. 'image/jpeg').

    Returns:
        Tuple of (extracted_text, error_message).
        error_message is None on success.

    TODO: Replace the stub body below with the real OCR API call.
          Recommended options:
            - Mathpix  (best for math/LaTeX): https://mathpix.com/docs/api
            - Google Cloud Vision: https://cloud.google.com/vision/docs
            - Azure Computer Vision: https://learn.microsoft.com/azure/ai-services/computer-vision
    """
    # ── Stub: replace with real API call ──────────────────────
    # Example skeleton for Mathpix (uncomment + fill in when ready):
    #
    # import httpx
    # from app.config import get_settings
    # settings = get_settings()
    #
    # headers = {
    #     "app_id":  settings.ocr_app_id,
    #     "app_key": settings.ocr_api_key,
    #     "Content-Type": "application/json",
    # }
    # payload = {
    #     "src": f"data:{mime_type};base64,{image_b64}",
    #     "formats": ["text", "latex_simplified"],
    # }
    # async with httpx.AsyncClient(timeout=settings.ocr_timeout_seconds) as client:
    #     resp = await client.post(settings.ocr_api_url, json=payload, headers=headers)
    #     resp.raise_for_status()
    #     data = resp.json()
    #     text = data.get("latex_simplified") or data.get("text", "")
    #     return text, None
    # ─────────────────────────────────────────────────────────

    logger.warning("[OCR] call_ocr_api() is not yet implemented — returning placeholder.")
    return "", "OCR API not configured yet. Please implement call_ocr_api() in app/utils/image.py."
