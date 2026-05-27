from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from inference.router import InferenceRouter

router = APIRouter(prefix="/inference")

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="Content text")

class InferenceRequest(BaseModel):
    model: str = Field(..., description="Model identifier (e.g., 'openbmb/minicpm5:fp16')")
    messages: List[ChatMessage]
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)
    task_type: Optional[str] = Field(None, description="e.g. 'tool_call' or 'reasoning'")
    context_length: Optional[int] = Field(None, description="Explicit context length")
    batch_size: Optional[int] = Field(1, description="Explicit request batch size")
    hardware: Optional[str] = Field(None, description="Host environment constraints")

class InferenceResponse(BaseModel):
    model: str
    message: ChatMessage
    usage: Dict[str, int]

_router_instance = InferenceRouter()

def get_inference_router() -> InferenceRouter:
    return _router_instance

@router.post("/chat", response_model=InferenceResponse, summary="Intelligent multi-backend chat completion router")
async def chat_completion(
    request: InferenceRequest,
    inference_router: InferenceRouter = Depends(get_inference_router)
) -> dict:
    try:
        messages_raw = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        result = await inference_router.chat(
            model=request.model,
            messages=messages_raw,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            task_type=request.task_type,
            context_length=request.context_length,
            batch_size=request.batch_size,
            hardware=request.hardware
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Inference pipeline execution failure: {str(e)}"
        )
