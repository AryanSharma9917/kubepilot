"""Chat API routes."""

from fastapi import APIRouter, Depends, HTTPException
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

    try:
        return await service.respond(request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/chat/stream")
async def stream_chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    """Accept a user message and stream the agent response as SSE."""

    try:
        service.ensure_allowed(request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return StreamingResponse(
        service.stream(request),
        media_type="text/event-stream",
    )
