"""
Person 1 — OCR Engine
Extracts math questions from images (text or photo of handwriting)
and structures them into a JSON format for the Agent.

=== TEAM (Person 1): Choose your OCR backend and tune the parsing ===

Dependencies:
  pip install pytesseract Pillow
  + install Tesseract binary: https://github.com/tesseract-ocr/tesseract

Alternative (no binary install needed):
  pip install easyocr
"""

import json
import re
from typing import Dict, Any, Optional
from pathlib import Path

try:
    import pytesseract
    from PIL import Image
    OCR_BACKEND = "tesseract"
except ImportError:
    pytesseract = None
    OCR_BACKEND = "none"

from src.telemetry.logger import logger


# ─── Core OCR Function ───────────────────────────────────────────────────────

def extract_text_from_image(image_path: str) -> str:
    """
    Extract raw text from an image file.
    === TEAM (Person 1): Add support for easyocr or OpenAI Vision as alternatives ===
    """
    if OCR_BACKEND == "tesseract" and pytesseract:
        try:
            img = Image.open(image_path)
            raw_text = pytesseract.image_to_string(img, config="--psm 6")
            logger.log_event("OCR_EXTRACT", {
                "backend": "tesseract",
                "image": image_path,
                "chars": len(raw_text),
            })
            return raw_text.strip()
        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {e}")
            return ""
    else:
        logger.error("No OCR backend available. Install pytesseract or easyocr.")
        return ""


def extract_text_from_bytes(image_bytes: bytes, filename: str = "upload.png") -> str:
    """
    Extract text from raw image bytes (for FastAPI UploadFile).
    """
    import io
    if OCR_BACKEND == "tesseract" and pytesseract:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            raw_text = pytesseract.image_to_string(img, config="--psm 6")
            logger.log_event("OCR_EXTRACT", {
                "backend": "tesseract",
                "filename": filename,
                "chars": len(raw_text),
            })
            return raw_text.strip()
        except Exception as e:
            logger.error(f"OCR from bytes failed: {e}")
            return ""
    return ""


# ─── Question Parser ─────────────────────────────────────────────────────────

def parse_question(raw_text: str) -> Dict[str, Any]:
    """
    Parse raw OCR text into structured JSON for the Agent.

    Returns:
        {
            "question": "the main math question",
            "details": "any additional context or constraints",
            "raw": "original OCR output",
            "source": "ocr" | "text"
        }

    === TEAM (Person 1): Improve this parser for your specific question formats ===
    """
    lines = [line.strip() for line in raw_text.strip().split("\n") if line.strip()]

    if not lines:
        return {
            "question": "",
            "details": "",
            "raw": raw_text,
            "source": "ocr",
            "error": "No text extracted from image",
        }

    # Simple heuristic: first meaningful line is the question, rest is details
    question = lines[0]
    details = " ".join(lines[1:]) if len(lines) > 1 else ""

    # Clean up common OCR artifacts in math
    question = _clean_math_text(question)
    details = _clean_math_text(details)

    parsed = {
        "question": question,
        "details": details,
        "raw": raw_text,
        "source": "ocr",
    }

    logger.log_event("OCR_PARSED", {
        "question_preview": question[:100],
        "has_details": bool(details),
    })

    return parsed


def _clean_math_text(text: str) -> str:
    """
    Clean up common OCR mistakes in mathematical text.
    === TEAM (Person 1): Add more cleanup rules as you test with real images ===
    """
    # Common OCR substitutions
    replacements = {
        "×": "*",
        "÷": "/",
        "−": "-",
        "²": "**2",
        "³": "**3",
        "√": "sqrt",
        "∫": "integral of ",
        "π": "pi",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove stray non-math characters
    text = re.sub(r"[^\w\s+\-*/^()=.,<>|!?]", "", text)

    return text.strip()


# ─── Convenience: Process an image end-to-end ────────────────────────────────

def process_image(image_path: str) -> Dict[str, Any]:
    """Full pipeline: image file → OCR → structured JSON."""
    raw = extract_text_from_image(image_path)
    return parse_question(raw)


def process_image_bytes(image_bytes: bytes, filename: str = "upload.png") -> Dict[str, Any]:
    """Full pipeline: image bytes (from upload) → OCR → structured JSON."""
    raw = extract_text_from_bytes(image_bytes, filename)
    return parse_question(raw)


def process_text(raw_text: str) -> Dict[str, Any]:
    """For plain text input (no OCR needed)."""
    parsed = parse_question(raw_text)
    parsed["source"] = "text"
    return parsed
