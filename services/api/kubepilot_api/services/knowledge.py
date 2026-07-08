"""Knowledge retrieval application service."""

from agent.kubepilot_agent import Retriever, create_configured_retriever
from kubepilot_api.schemas import (
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
)


class KnowledgeService:
    """Boundary between the API and retrieval implementations."""

    def __init__(self, retriever: Retriever | None = None) -> None:
        self._retriever = retriever or create_configured_retriever()

    async def search(self, request: KnowledgeSearchRequest) -> KnowledgeSearchResponse:
        """Return ranked knowledge chunks for a query."""

        matches = self._retriever.search(request.query, limit=request.limit)
        return KnowledgeSearchResponse(
            results=[
                KnowledgeSearchResult(
                    title=match.document.title,
                    source=match.document.source,
                    snippet=_snippet(match.document.content),
                    score=match.score,
                )
                for match in matches
            ]
        )


async def get_knowledge_service() -> KnowledgeService:
    """Provide the knowledge service to API routes."""

    return KnowledgeService()


def _snippet(content: str, *, max_length: int = 220) -> str:
    compact = " ".join(content.split())
    if len(compact) <= max_length:
        return compact
    return f"{compact[: max_length - 3].rstrip()}..."
