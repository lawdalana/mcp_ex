"""Shared client utilities for invoking MCP tools over HTTP."""
from __future__ import annotations

import json
from collections.abc import Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import httpx


class ToolInvocationError(RuntimeError):
    """Raised when a tool invocation fails or returns malformed data."""


@dataclass(slots=True)
class ToolResponse:
    """Represents the outcome of a tool invocation."""

    tool_name: str
    result: Any
    events: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {"tool": self.tool_name, "result": self.result, "events": self.events}


class BaseClient:
    """Base class handling HTTP streaming and error translation."""

    def __init__(
        self,
        base_url: str,
        *,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/") or "/"
        self._provided_client = http_client
        self.timeout = timeout

    @asynccontextmanager
    async def _client(self) -> httpx.AsyncClient:
        if self._provided_client is not None:
            yield self._provided_client
            return

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            yield client

    async def invoke_tool(self, tool_name: str, payload: Mapping[str, Any]) -> ToolResponse:
        async with self._client() as client:
            try:
                async with client.stream(
                    "POST",
                    f"/tools/{tool_name}",
                    json=dict(payload),
                    timeout=self.timeout,
                ) as response:
                    response.raise_for_status()
                    events: list[dict[str, Any]] = []
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                            raise ToolInvocationError(
                                f"Failed to decode event from tool '{tool_name}': {line}"
                            ) from exc
                        events.append(event)
            except httpx.HTTPStatusError as exc:  # pragma: no cover - defensive
                detail = exc.response.text
                raise ToolInvocationError(
                    f"Tool '{tool_name}' returned status {exc.response.status_code}: {detail}"
                ) from exc
            except httpx.HTTPError as exc:  # pragma: no cover - defensive
                message = f"HTTP error talking to tool '{tool_name}': {exc}"
                raise ToolInvocationError(message) from exc

        if not events:
            raise ToolInvocationError(f"Tool '{tool_name}' produced no events")

        final = events[-1]
        if "result" not in final:
            raise ToolInvocationError(f"Tool '{tool_name}' did not provide a result event")

        return ToolResponse(tool_name=tool_name, result=final["result"], events=events)

