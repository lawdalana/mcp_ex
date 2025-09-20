"""Pydantic schemas shared by the FastAPI application."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RequestConversation(BaseModel):
    question: str = Field(..., min_length=1)
    interaction_id: str = Field(..., min_length=1)


class ToolCallSummary(BaseModel):
    name: str
    result: Any
    events: list[dict[str, Any]]


class ConversationResponse(BaseModel):
    interaction_id: str
    question: str
    reply: str
    tool: ToolCallSummary | None = None

