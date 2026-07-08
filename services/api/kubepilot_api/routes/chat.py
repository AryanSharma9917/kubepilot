"""Chat API routes."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

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


@router.post("/chat/stream")
async def stream_chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    """Accept a user message and stream the agent response as SSE."""

    return StreamingResponse(
        service.stream(request),
        media_type="text/event-stream",
    )
