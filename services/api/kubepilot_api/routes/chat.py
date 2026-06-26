"""Chat API routes."""

from fastapi import APIRouter, Depends

from kubepilot_api.schemas import ChatRequest, ChatResponse
from kubepilot_api.services.chat import ChatService, get_chat_service

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Accept a user message and return the current agent response."""

    return await service.respond(request)

