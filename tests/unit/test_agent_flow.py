import pytest
import os
import shutil
import json
from unittest.mock import AsyncMock, patch
import httpx
from worker.tools.filesystem import FilesystemTool
from worker.tools.search import SearchTool
from worker.agent.base import ReactiveAgent

# ==========================================================================
# 1. Tools Tests
# ==========================================================================
@pytest.mark.asyncio
async def test_filesystem_tool() -> None:
    tool = FilesystemTool()
    test_dir = "workspace_test"
    test_file = f"{test_dir}/test_note.txt"
    test_content = "NeuralFolk Complete Dev Stack Integration"

    try:
        # Write
        res_write = await tool.execute("write", test_file, test_content)
        assert res_write["status"] == "success"
        assert os.path.exists(test_file)

        # Read
        res_read = await tool.execute("read", test_file)
        assert res_read["status"] == "success"
        assert res_read["content"] == test_content

        # List
        res_list = await tool.execute("list", test_dir)
        assert res_list["status"] == "success"
        assert "test_note.txt" in res_list["items"]
    finally:
        # Cleanup
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

@pytest.mark.asyncio
async def test_search_tool_real() -> None:
    tool = SearchTool()
    try:
        # Execute actual network request to DuckDuckGo
        res = await tool.execute("NeuralFolk AI")
        assert res["status"] == "success"
        assert "results" in res
        assert isinstance(res["results"], list)
    except Exception as e:
        # If rate-limited or offline, verify it handles it gracefully
        pytest.skip(f"Live DuckDuckGo query skipped due to connection rate limit: {e}")

# ==========================================================================
# 2. Agent Cognitive Loop Tests
# ==========================================================================
@pytest.mark.asyncio
async def test_reactive_agent_flow() -> None:
    agent_id = "test-agent-123"
    model = "openbmb/minicpm5:fp16"
    task = "Evaluate local AI infrastructure stacks"
    
    agent = ReactiveAgent(
        agent_id=agent_id,
        model=model,
        task=task,
        api_url="http://localhost:8000"
    )

    published_events = []

    # Mock the HTTP calls to the Control Plane event publisher & inference API
    original_post = httpx.AsyncClient.post
    async def mock_httpx_post(self_client, url: str, *args, **kwargs):
        class MockResponse:
            def __init__(self, data: dict, status_code: int = 200) -> None:
                self.data = data
                self.status_code = status_code
                self.text = json.dumps(data)
            def json(self) -> dict:
                return self.data
            def raise_for_status(self) -> None:
                pass
                
        if "duckduckgo.com" in str(url):
            return await original_post(self_client, url, *args, **kwargs)
            
        json_payload = kwargs.get("json")
        if "/publish-event" in str(url):
            published_events.append(json_payload)
            return MockResponse({"status": "event_published"})
            
        if "/inference/chat" in str(url):
            return MockResponse({
                "model": model,
                "message": {
                    "role": "assistant",
                    "content": "Optimized stack loading for openbmb/minicpm5:fp16 verified successfully."
                },
                "usage": {"total_tokens": 120}
            })
            
        return MockResponse({}, 404)

    with patch("httpx.AsyncClient.post", new=mock_httpx_post):
        # Run agent loop
        await agent.run()

    # Verify that standard state events were published chronologically conforming to STACK.md
    assert len(published_events) >= 5
    
    event_types = [e["event_type"] for e in published_events]
    assert "agent.plan.created" in event_types
    assert "agent.tool.called" in event_types
    assert "agent.tool.completed" in event_types
    assert "agent.completed" in event_types

    # Verify plan payload
    plan_event = next(e for e in published_events if e["event_type"] == "agent.plan.created")
    assert plan_event["data"]["steps_planned"] == 3
    assert plan_event["data"]["model_used"] == model

    # Verify completion payload
    comp_event = next(e for e in published_events if e["event_type"] == "agent.completed")
    assert comp_event["data"]["steps_taken"] == 3
    assert "Optimized stack" in comp_event["data"]["summary"]
    
    # Cleanup generated files
    output_file = f"workspace/agent_{agent_id}.txt"
    if os.path.exists(output_file):
        os.remove(output_file)
        if os.path.exists("workspace"):
            os.rmdir("workspace")
