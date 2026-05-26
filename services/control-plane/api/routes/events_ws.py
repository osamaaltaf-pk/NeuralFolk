from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import structlog
from core.valkey import get_valkey

router = APIRouter()
logger = structlog.get_logger()

@router.websocket("/events/ws")
async def websocket_events_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    await logger.ainfo("websocket_client_connected")
    
    client = get_valkey()
    last_id = "$"  # Start reading from current time onwards
    
    try:
        while True:
            # Read from the all-events stream
            streams = {"neuralfolk:events:all": last_id}
            results = await client.xread(streams, count=10, block=1000)
            
            for stream, events in results:
                for event_id, fields in events:
                    event_type = fields.get("event_type")
                    data_str = fields.get("data", "{}")
                    
                    # Parse data safely
                    try:
                        data = json.loads(data_str)
                    except Exception:
                        data = {}
                        
                    await websocket.send_json({
                        "event_type": event_type,
                        "id": event_id,
                        "data": data
                    })
                    last_id = event_id
                    
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        await logger.ainfo("websocket_client_disconnected")
    except Exception as e:
        await logger.aerror("websocket_stream_failed", error=str(e))
        try:
            await websocket.close()
        except Exception:
            pass
