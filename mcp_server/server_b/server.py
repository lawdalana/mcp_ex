"""Weather MCP server built on the lightweight MCP utilities."""
from __future__ import annotations

from typing import Any

from mcp import MCPServer

WEATHER_DATA: dict[str, dict[str, Any]] = {
    "london": {"condition": "cloudy", "temperature_c": 16.0},
    "new york": {"condition": "sunny", "temperature_c": 22.0},
    "los angeles": {"condition": "clear", "temperature_c": 24.0},
}

server = MCPServer("Weather Toolkit")


def _convert_temperature(value_c: float, unit: str) -> float:
    if unit == "fahrenheit":
        return round((value_c * 9 / 5) + 32, 1)
    return value_c


@server.tool(name="current_weather")
async def current_weather(location: str, unit: str = "celsius") -> dict[str, Any]:
    normalized = location.strip().lower()
    if normalized not in WEATHER_DATA:
        raise ValueError(f"Weather data for '{location}' is not available")

    entry = WEATHER_DATA[normalized]
    temperature = _convert_temperature(entry["temperature_c"], unit)
    return {
        "location": location.title(),
        "condition": entry["condition"],
        "temperature": temperature,
        "unit": unit,
    }


app = server.app


if __name__ == "__main__":  # pragma: no cover - manual run helper
    server.run(host="0.0.0.0", port=8002)

