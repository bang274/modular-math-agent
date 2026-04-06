"""
Upload Endpoint — Multipart file upload (text + image).

Person 5 owns this file.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.deps import check_rate_limit
from app.models.response import SolveResponse
from app.agent.graph import run_agent_pipeline
from app.db.repository import session_repo
from app.utils.image import preprocess_image, validate_image_type
from app.utils.validators import validate_text_input, validate_upload_size
from app.telemetry.logger import logger
from app.telemetry.metrics import metrics
from app.api.v1.solve import _build_response, _save_to_db

router = APIRouter()


@router.post("/upload", response_model=SolveResponse)
async def upload_and_solve(
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    _: None = Depends(check_rate_limit),
):
    """Upload math problems as text, image, or both.

    Accepts multipart form data with optional text and image fields.
    Runs the full agent pipeline after input processing.
    """
    session_id = str(uuid.uuid4())
    logger.info(f"[API] POST /upload session={session_id}")

    # ── Validate inputs ──────────────────────────────────────
    if not text and not image:
        raise HTTPException(
            status_code=400,
            detail="At least one of 'text' or 'image' must be provided",
        )

    # Validate text
    if text:
        valid, err = validate_text_input(text)
        if not valid:
            raise HTTPException(status_code=400, detail=err)

    # Process image
    image_b64 = None
    if image:
        # Validate type
        if image.content_type and not validate_image_type(image.content_type):
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported image type: {image.content_type}. "
                       f"Supported: JPEG, PNG, WebP, GIF",
            )

        # Read and validate size
        image_bytes = await image.read()
        valid, err = validate_upload_size(len(image_bytes))
        if not valid:
            raise HTTPException(status_code=413, detail=err)

        # Preprocess
        image_b64, err = await preprocess_image(image_bytes)
        if err:
            raise HTTPException(status_code=400, detail=err)

    # ── Run pipeline ─────────────────────────────────────────
    try:
        final_state = await run_agent_pipeline(
            text=text,
            image_b64=image_b64,
            session_id=session_id,
        )

        response = _build_response(session_id, final_state)
        await _save_to_db(session_id, final_state, response)

        metrics.record_request(response.total_problems)
        metrics.record_latency(response.total_latency_ms)

        return response

    except Exception as e:
        logger.error(f"[API] Upload solve error: {e}")
        metrics.record_error()
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")
