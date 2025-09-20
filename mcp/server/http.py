"""A tiny HTTP server for MCP style tools.

The implementation mirrors the FastMCP helper but includes richer progress
updates suitable for long running tasks.
"""
from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse


@dataclass
class MCPEvent:
    status: str
    payload: dict[str, Any]


class MCPServer:
    """Expose decorated callables as streaming HTTP endpoints."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._tools: dict[str, Callable[..., Awaitable[Any]]] = {}
        self._app: FastAPI | None = None

    def tool(self, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            tool_name = name or func.__name__

            async def wrapper(**kwargs: Any) -> Any:
                result = func(**kwargs)
                if asyncio.iscoroutine(result):
                    return await result
                return result

            self._tools[tool_name] = wrapper
            return func

        return decorator

    @property
    def app(self) -> FastAPI:
        if self._app is None:
            self._app = self._create_app()
        return self._app

    def _create_app(self) -> FastAPI:
        app = FastAPI(title=self.name)

        @app.get("/.well-known/mcp.json")
        async def metadata() -> dict[str, Any]:
            return {"name": self.name, "tools": list(self._tools)}

        @app.post("/tools/{tool_name}")
        async def invoke(tool_name: str, request: Request) -> StreamingResponse:
            if tool_name not in self._tools:
                raise HTTPException(status_code=404, detail=f"Unknown tool '{tool_name}'")

            payload = await request.json()
            tool = self._tools[tool_name]

            async def event_stream() -> AsyncIterator[bytes]:
                yield json.dumps({"status": "started", "tool": tool_name}).encode() + b"\n"
                await asyncio.sleep(0)
                yield json.dumps({"status": "progress", "message": "processing"}).encode() + b"\n"
                result = await tool(**payload)
                yield (
                    json.dumps({"status": "completed", "result": result}).encode() + b"\n"
                )

            return StreamingResponse(event_stream(), media_type="application/json")

        return app

    def run(self, **uvicorn_options: Any) -> None:  # pragma: no cover - manual helper
        import uvicorn

        uvicorn.run(self.app, **uvicorn_options)

