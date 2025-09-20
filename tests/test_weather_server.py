import json

import httpx
import pytest

from mcp_server.server_b import server as weather_server


@pytest.mark.asyncio
async def test_weather_stream_contains_progress_event() -> None:
    transport = httpx.ASGITransport(app=weather_server.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://weather") as client:
        async with client.stream(
            "POST", "/tools/current_weather", json={"location": "London", "unit": "celsius"}
        ) as response:
            events = []
            async for line in response.aiter_lines():
                if line:
                    events.append(json.loads(line))

    assert events[0]["status"] == "started"
    assert any(event["status"] == "progress" for event in events)
    final = events[-1]
    assert final["status"] == "completed"
    assert final["result"]["location"] == "London"


@pytest.mark.asyncio
async def test_weather_fahrenheit_conversion() -> None:
    transport = httpx.ASGITransport(app=weather_server.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://weather") as client:
        async with client.stream(
            "POST", "/tools/current_weather", json={"location": "London", "unit": "fahrenheit"}
        ) as response:
            events = []
            async for line in response.aiter_lines():
                if line:
                    events.append(json.loads(line))

    assert round(events[-1]["result"]["temperature"], 1) == 60.8
    assert events[-1]["result"]["unit"] == "fahrenheit"

