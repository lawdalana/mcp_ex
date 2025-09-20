import json

import httpx
import pytest

from mcp_server.server_a import server as math_server


@pytest.mark.asyncio
async def test_math_add_tool_streams_events() -> None:
    transport = httpx.ASGITransport(app=math_server.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://math") as client:
        async with client.stream("POST", "/tools/add", json={"a": 2, "b": 3}) as response:
            assert response.status_code == 200
            events = []
            async for line in response.aiter_lines():
                if line:
                    events.append(json.loads(line))

    assert events[0]["status"] == "started"
    assert events[-1]["status"] == "completed"
    assert events[-1]["result"]["total"] == 5


@pytest.mark.asyncio
async def test_math_multiply_tool() -> None:
    transport = httpx.ASGITransport(app=math_server.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://math") as client:
        async with client.stream("POST", "/tools/multiply", json={"a": 4, "b": 6}) as response:
            lines = []
            async for line in response.aiter_lines():
                if line:
                    lines.append(json.loads(line))

    assert lines[-1]["result"]["total"] == 24

