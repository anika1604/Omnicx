"""Pydantic request/response schemas."""
from pydantic import BaseModel
from typing import Optional, Literal


class FeedbackSchema(BaseModel):
    session_id: str
    csat_score: float   # 1.0 – 5.0
    comment:    Optional[str] = None
