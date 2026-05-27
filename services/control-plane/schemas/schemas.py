from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AgentSpawnRequest(BaseModel):
    model: str = Field("openbmb/minicpm5:fp16", description="Model identifier")
    task_summary: str = Field(..., description="Goal summary for the agent")
    hardware: Optional[str] = Field(None, description="Hardware constraints")

class AgentSpawnResponse(BaseModel):
    agent_id: str
    status: str
    created_at: datetime
