import httpx
import pytest

from host.app.app import create_app
from host.mcp_client.client_a import MathMCPClient
from host.mcp_client.client_b import WeatherMCPClient
from mcp_server.server_a import server as math_server
from mcp_server.server_b import server as weather_server


@pytest.mark.asyncio
async def test_conversation_routes_to_math_tool() -> None:
    math_transport = httpx.ASGITransport(app=math_server.app)
    weather_transport = httpx.ASGITransport(app=weather_server.app)

    async with httpx.AsyncClient(
        transport=math_transport,
        base_url="http://math",
    ) as math_http:
        async with httpx.AsyncClient(
            transport=weather_transport,
            base_url="http://weather",
        ) as weather_http:
            app = create_app(
                math_client=MathMCPClient("http://math", http_client=math_http),
                weather_client=WeatherMCPClient("http://weather", http_client=weather_http),
            )
            host_transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=host_transport,
                base_url="http://host",
            ) as host_client:
                response = await host_client.post(
                    "/conversation",
                    json={"question": "What is 2 + 3?", "interaction_id": "math-1"},
                )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tool"]["name"] == "math.add"
    assert payload["reply"].startswith("The result of 2.0 + 3.0 is 5.0")


@pytest.mark.asyncio
async def test_conversation_routes_to_weather_tool_and_handles_fallback() -> None:
    math_transport = httpx.ASGITransport(app=math_server.app)
    weather_transport = httpx.ASGITransport(app=weather_server.app)

    async with httpx.AsyncClient(
        transport=math_transport,
        base_url="http://math",
    ) as math_http:
        async with httpx.AsyncClient(
            transport=weather_transport,
            base_url="http://weather",
        ) as weather_http:
            app = create_app(
                math_client=MathMCPClient("http://math", http_client=math_http),
                weather_client=WeatherMCPClient("http://weather", http_client=weather_http),
            )
            host_transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=host_transport,
                base_url="http://host",
            ) as host_client:
                weather_response = await host_client.post(
                    "/conversation",
                    json={
                        "question": "Please share the weather in London in Fahrenheit.",
                        "interaction_id": "weather-1",
                    },
                )
                fallback_response = await host_client.post(
                    "/conversation",
                    json={"question": "Tell me a joke", "interaction_id": "none-1"},
                )

    assert weather_response.status_code == 200
    weather_payload = weather_response.json()
    assert weather_payload["tool"]["name"] == "weather.current_weather"
    assert "London" in weather_payload["reply"]
    assert "°F" in weather_payload["reply"]

    assert fallback_response.status_code == 200
    fallback_payload = fallback_response.json()
    assert fallback_payload["tool"] is None
    assert "math or the weather" in fallback_payload["reply"]

