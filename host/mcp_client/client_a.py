"""Client for interacting with the math MCP server."""
from __future__ import annotations

from typing import Any

from .client import BaseClient, ToolResponse


class MathMCPClient(BaseClient):
    async def add(self, a: float, b: float) -> ToolResponse:
        return await self.invoke_tool("add", {"a": a, "b": b})

    async def subtract(self, a: float, b: float) -> ToolResponse:
        return await self.invoke_tool("subtract", {"a": a, "b": b})

    async def multiply(self, a: float, b: float) -> ToolResponse:
        return await self.invoke_tool("multiply", {"a": a, "b": b})

    async def calculate(self, operation: str, a: float, b: float) -> ToolResponse:
        operations: dict[str, Any] = {
            "add": self.add,
            "subtract": self.subtract,
            "multiply": self.multiply,
        }
        if operation not in operations:
            raise ValueError(f"Unsupported math operation '{operation}'")
        return await operations[operation](a, b)

