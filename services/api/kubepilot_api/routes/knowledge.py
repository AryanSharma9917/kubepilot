"""Knowledge search API routes."""

from fastapi import APIRouter, Depends

from kubepilot_api.schemas import KnowledgeSearchRequest, KnowledgeSearchResponse
from kubepilot_api.services.knowledge import KnowledgeService, get_knowledge_service

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    request: KnowledgeSearchRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeSearchResponse:
    """Return retrieved runbook chunks for a query."""

    return await service.search(request)
