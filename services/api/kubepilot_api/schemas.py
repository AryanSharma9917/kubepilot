"""API response models."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ServiceInfo(BaseModel):
    """Public information about the running service."""

    name: str
    version: str
    environment: str


class HealthResponse(BaseModel):
    """Health probe response."""

    status: Literal["ok", "ready"]


class ChatRequest(BaseModel):
    """A user message submitted to KubePilot."""

    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message", mode="before")
    @classmethod
    def normalize_message(cls, value: object) -> object:
        """Trim surrounding whitespace before validating message length."""

        return value.strip() if isinstance(value, str) else value


class ChatResponse(BaseModel):
    """KubePilot's response to a chat request."""

    request_id: UUID
    answer: str

