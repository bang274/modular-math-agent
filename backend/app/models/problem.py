"""
Problem & ProblemSet schemas — the core data structures.

Person 1 (Input/OCR) owns these schemas.
Used by: extractor node, classifier, solvers, aggregator, API layer.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Problem(BaseModel):
    """A single extracted math problem."""
    id: int = Field(..., description="Problem number (1-indexed)")
    content: str = Field(
        ...,
        description="LaTeX-ready math problem content",
        min_length=1,
    )
    original_text: Optional[str] = Field(
        None,
        description="Original raw text before LaTeX conversion",
    )
    source: str = Field(
        "text",
        description="Input source: text, image, or both",
    )
    image_ref: Optional[str] = Field(
        None,
        description="Base64 image data if from image, null otherwise",
    )


class ProblemSet(BaseModel):
    """Collection of problems extracted from user input."""
    session_id: str = Field(..., description="Unique session identifier")
    problems: List[Problem] = Field(
        default_factory=list,
        description="List of extracted problems",
    )
    total_problems: int = Field(0, description="Total number of problems")
    upload_type: str = Field("text", description="Type of upload: text, image, mixed")
    raw_text: Optional[str] = Field(None, description="Original raw text input")
    raw_image_b64: Optional[str] = Field(None, description="Original image as base64")

    def model_post_init(self, __context) -> None:
        """Auto-set total_problems from problems list."""
        if self.problems and self.total_problems == 0:
            self.total_problems = len(self.problems)
