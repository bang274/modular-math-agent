"""
Extract Endpoints — Input Processing Module (Person 1).

POST /api/v1/extract/text   — Nhận text → LLM extract → JSON
POST /api/v1/extract/image  — Nhận ảnh → LLM Vision extract → JSON

Response format:
    {
        "problems": [
            {"id": "bai_1", "content": "Giải PT: $2x^2 - 3x + 1 = 0$"},
            ...
        ],
        "total": 1,
        "source": "text" | "image",
        "ocr_text": null
    }
"""

from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.agent.nodes.extractor import extract_problems_from_text, extract_problems_from_image
from app.utils.image import get_image_mime_type, preprocess_image, validate_image_type
from app.utils.validators import validate_text_input, validate_upload_size
from app.telemetry.logger import logger

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────

class TextExtractRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10_000)


class ExtractedProblem(BaseModel):
    id: str
    content: str


class ExtractResponse(BaseModel):
    problems: List[ExtractedProblem]
    total: int
    source: str
    ocr_text: Optional[str] = None
    error: Optional[str] = None


# ── Endpoint 1: Text → JSON ───────────────────────────────────────────

@router.post("/extract/text", response_model=ExtractResponse)
async def extract_from_text(request: TextExtractRequest):
    """Nhận text từ frontend, gọi LLM để extract bài toán, trả về JSON."""
    valid, err = validate_text_input(request.text)
    if not valid:
        raise HTTPException(status_code=400, detail=err)

    logger.info(f"[API /extract/text] {len(request.text)} chars")

    result = await extract_problems_from_text(request.text)

    if result["error"] and not result["problems"]:
        raise HTTPException(status_code=422, detail=result["error"])

    return ExtractResponse(
        problems=[ExtractedProblem(**p) for p in result["problems"]],
        total=len(result["problems"]),
        source="text",
        error=result.get("error"),
    )


# ── Endpoint 2: Image → LLM Vision → JSON ────────────────────────────

@router.post("/extract/image", response_model=ExtractResponse)
async def extract_from_image(image: UploadFile = File(...)):
    """Nhận ảnh từ frontend, gọi trực tiếp LLM Vision để extract bài toán."""
    # 1. Validate MIME type
    mime = get_image_mime_type(image.content_type)
    if not validate_image_type(mime):
        raise HTTPException(
            status_code=415,
            detail=f"Không hỗ trợ định dạng ảnh: {image.content_type}. Chấp nhận: JPEG, PNG, WebP, GIF.",
        )

    # 2. Validate kích thước file
    image_bytes = await image.read()
    valid, err = validate_upload_size(len(image_bytes))
    if not valid:
        raise HTTPException(status_code=413, detail=err)

    logger.info(f"[API /extract/image] {image.filename} ({len(image_bytes):,} bytes)")

    # 3. Tiền xử lý ảnh (resize nếu cần, encode base64)
    image_b64, err = await preprocess_image(image_bytes)
    if err:
        raise HTTPException(status_code=400, detail=f"Lỗi xử lý ảnh: {err}")

    # 4. LLM extract trực tiếp từ ảnh (Vision)
    result = await extract_problems_from_image(image_b64)

    if result["error"] and not result["problems"]:
        raise HTTPException(status_code=422, detail=result["error"])

    return ExtractResponse(
        problems=[ExtractedProblem(**p) for p in result["problems"]],
        total=len(result["problems"]),
        source="image",
        ocr_text=None,
        error=result.get("error"),
    )
