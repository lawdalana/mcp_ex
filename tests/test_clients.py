import httpx
import pytest

from host.mcp_client.client_a import MathMCPClient
from host.mcp_client.client_b import WeatherMCPClient
from mcp_server.server_a import server as math_server
from mcp_server.server_b import server as weather_server


@pytest.mark.asyncio
async def test_math_client_add() -> None:
    transport = httpx.ASGITransport(app=math_server.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://math") as http_client:
        client = MathMCPClient("http://math", http_client=http_client)
        response = await client.add(7, 5)

    assert response.result["total"] == 12
    assert response.events[-1]["status"] == "completed"


@pytest.mark.asyncio
async def test_weather_client_current_weather() -> None:
    transport = httpx.ASGITransport(app=weather_server.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://weather") as http_client:
        client = WeatherMCPClient("http://weather", http_client=http_client)
        response = await client.current_weather("London")

    assert response.result["condition"] == "cloudy"
    assert response.result["temperature"] == pytest.approx(16.0)

