"""Shared retrieval models."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Document:
    """A loaded or chunked knowledge document."""

    source: str
    title: str
    content: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievedDocument:
    """A document selected as relevant for a query."""

    document: Document
    score: float
