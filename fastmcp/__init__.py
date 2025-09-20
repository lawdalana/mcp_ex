"""A tiny FastMCP-inspired framework used for tests.

This implementation is intentionally lightweight; it mimics the API surface
used by the example servers so the code remains self-contained for unit tests.
"""
from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse


@dataclass
class StreamingEvent:
    """Represents a structured event emitted during a tool invocation."""

    status: str
    payload: dict[str, Any]


class FastMCP:
    """Minimal server for exposing tools over HTTP with streaming responses."""

    def __init__(self, name: str, *, metadata: dict[str, Any] | None = None) -> None:
        self.name = name
        self.metadata = metadata or {}
        self._tools: dict[str, Callable[..., Awaitable[Any]]] = {}
        self._app: FastAPI | None = None

    def tool(self, func: Callable[..., Any] | None = None, *, name: str | None = None) -> Callable:
        """Register a tool function that can be invoked via HTTP."""

        def decorator(inner: Callable[..., Any]) -> Callable[..., Any]:
            tool_name = name or inner.__name__

            async def async_wrapper(**kwargs: Any) -> Any:
                result = inner(**kwargs)
                if asyncio.iscoroutine(result):
                    return await result
                return result

            self._tools[tool_name] = async_wrapper
            return inner

        if func is not None:
            return decorator(func)
        return decorator

    @property
    def app(self) -> FastAPI:
        """Return the ASGI application for the server."""

        if self._app is None:
            self._app = self._create_app()
        return self._app

    def _create_app(self) -> FastAPI:
        app = FastAPI(title=self.name)

        @app.get("/.well-known/mcp.json")
        async def metadata() -> dict[str, Any]:
            return {"name": self.name, "metadata": self.metadata, "tools": list(self._tools)}

        @app.post("/tools/{tool_name}")
        async def invoke(tool_name: str, request: Request) -> StreamingResponse:
            if tool_name not in self._tools:
                raise HTTPException(status_code=404, detail=f"Unknown tool '{tool_name}'")

            payload = await request.json()
            tool = self._tools[tool_name]

            async def event_stream() -> AsyncIterator[bytes]:
                started = {"status": "started", "tool": tool_name}
                yield json.dumps(started).encode("utf-8") + b"\n"
                try:
                    result = await tool(**payload)
                except Exception as exc:  # pragma: no cover - surfaced to caller
                    error = {"status": "error", "error": str(exc)}
                    yield json.dumps(error).encode("utf-8") + b"\n"
                    raise

                completed = {"status": "completed", "result": result}
                yield json.dumps(completed).encode("utf-8") + b"\n"

            return StreamingResponse(event_stream(), media_type="application/json")

        return app

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[FastAPI]:
        yield self.app

    def run(self, **uvicorn_options: Any) -> None:  # pragma: no cover - helper for manual runs
        import uvicorn

        uvicorn.run(self.app, **uvicorn_options)

