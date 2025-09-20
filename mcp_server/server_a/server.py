"""Math oriented MCP server implemented with the FastMCP helper."""
from __future__ import annotations

from fastmcp import FastMCP

mcp = FastMCP(
    "Math Toolkit",
    metadata={"description": "Basic arithmetic operations exposed over MCP."},
)


@mcp.tool(name="add")
def add(a: float, b: float) -> dict[str, float | list[float] | str]:
    total = a + b
    return {"operation": "add", "operands": [a, b], "total": total}


@mcp.tool(name="subtract")
def subtract(a: float, b: float) -> dict[str, float | list[float] | str]:
    total = a - b
    return {"operation": "subtract", "operands": [a, b], "total": total}


@mcp.tool(name="multiply")
def multiply(a: float, b: float) -> dict[str, float | list[float] | str]:
    total = a * b
    return {"operation": "multiply", "operands": [a, b], "total": total}


app = mcp.app


if __name__ == "__main__":  # pragma: no cover - manual run helper
    mcp.run(host="0.0.0.0", port=8001)

