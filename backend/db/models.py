"""Pydantic models for DB entities."""
from pydantic import BaseModel, Field
from typing import Optional
import time


class SessionTurn(BaseModel):
    ts:        float = Field(default_factory=time.time)
    channel:   str
    role:      str   # user | assistant
    content:   str
    intent:    Optional[str] = None
    sentiment: Optional[str] = None


class CustomerContext(BaseModel):
    customer_id:        str
    total_interactions: int = 0
    channels_used:      list[str] = []
    churn_risk:         float = 0.0
    recent_sessions:    list[str] = []
