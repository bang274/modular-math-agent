"""
Image preprocessing utilities.

Person 1 owns this file.
Handles: validation, resizing, base64 encoding for LLM vision.
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
