"""API response models."""

from typing import Literal

from pydantic import BaseModel


class ServiceInfo(BaseModel):
    """Public information about the running service."""

    name: str
    version: str
    environment: str


class HealthResponse(BaseModel):
    """Health probe response."""

    status: Literal["ok", "ready"]

