import json
from typing import Dict, Any
import structlog
from core.valkey import get_valkey

logger = structlog.get_logger()

async def publish_event(event_type: str, data: Dict[str, Any]) -> None:
    """
    Publishes a structured system/agent/workflow event to its prefix-based Valkey stream
    as well as to the 'neuralfolk:events:all' fan-out queue for dashboard streaming.
    """
    prefix = event_type.split(".")[0]
    stream_key = f"neuralfolk:events:{prefix}"
    fanout_key = "neuralfolk:events:all"
    
    payload = {
        "event_type": event_type,
        "data": json.dumps(data)
    }
    
    client = get_valkey()
    try:
        # Publish to individual stream
        await client.xadd(stream_key, payload)
        # Publish to dashboard fan-out stream
        await client.xadd(fanout_key, payload)
    except Exception as e:
        await logger.aerror("event_publish_failed", event_type=event_type, error=str(e))
