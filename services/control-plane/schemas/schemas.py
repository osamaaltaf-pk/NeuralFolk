from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AgentSpawnRequest(BaseModel):
    model: str = Field("qwen2.5:3b", description="Model identifier")
    task_summary: str = Field(..., description="Goal summary for the agent")
    hardware: Optional[str] = Field(None, description="Hardware constraints")

class AgentSpawnResponse(BaseModel):
    agent_id: str
    status: str
    created_at: datetime
