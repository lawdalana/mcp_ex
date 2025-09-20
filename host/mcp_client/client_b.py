"""Client for interacting with the weather MCP server."""
from __future__ import annotations

from .client import BaseClient, ToolResponse


class WeatherMCPClient(BaseClient):
    async def current_weather(self, location: str, unit: str = "celsius") -> ToolResponse:
        return await self.invoke_tool(
            "current_weather", {"location": location, "unit": unit}
        )

