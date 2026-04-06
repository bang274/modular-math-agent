"""
API Request schemas.

Person 5 (API) owns these schemas.
"""

from typing import Optional
from pydantic import BaseModel, Field


class SolveRequest(BaseModel):
    """Request body for text-only solve (JSON body)."""
    text: str = Field(
        ...,
        description="Math problem text to solve",
        min_length=1,
        max_length=10000,
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID for persistent memory",
    )



class SolveTextRequest(BaseModel):
    """Used internally when processing multipart form."""
    text: Optional[str] = Field(None, description="Math problem text")
    # Image is handled via UploadFile, not in request body
