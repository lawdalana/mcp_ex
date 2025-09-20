"""FastAPI application that routes questions to MCP tool clients."""
from __future__ import annotations

import os
import re

from fastapi import Depends, FastAPI, HTTPException

from host.mcp_client.client import ToolInvocationError, ToolResponse
from host.mcp_client.client_a import MathMCPClient
from host.mcp_client.client_b import WeatherMCPClient
from host.schema.schema import (
    ConversationResponse,
    RequestConversation,
    ToolCallSummary,
)

_OPERATION_SYMBOLS = {"add": "+", "subtract": "-", "multiply": "×"}


class ClientRegistry:
    """Container holding the concrete MCP clients used by the API."""

    def __init__(self, math_client: MathMCPClient, weather_client: WeatherMCPClient) -> None:
        self.math = math_client
        self.weather = weather_client


def parse_math_question(question: str) -> tuple[str, float, float] | None:
    lowered = question.lower()
    numbers = re.findall(r"-?\d+(?:\.\d+)?", question)
    if len(numbers) < 2:
        return None

    if any(keyword in lowered for keyword in {"multiply", "times", "product", "*"}):
        operation = "multiply"
    elif any(keyword in lowered for keyword in {"subtract", "minus", "difference", "-"}):
        operation = "subtract"
    else:
        operation = "add"

    a, b = map(float, numbers[:2])
    return operation, a, b


def parse_weather_question(question: str) -> tuple[str, str] | None:
    lowered = question.lower()
    unit = "fahrenheit" if "fahrenheit" in lowered else "celsius"
    location_match = re.search(r"in ([a-z\s]+?)(?:\?|\.|!|$)", lowered)
    if not location_match:
        return None
    location = location_match.group(1).strip()
    if " in " in location:
        location = location.split(" in ", 1)[0].strip()
    location = location.rstrip(".?!")
    if not location:
        return None
    return location, unit


def format_math_reply(response: ToolResponse) -> str:
    result = response.result
    if isinstance(result, dict):
        total = result.get("total")
        operands = result.get("operands")
        operation = result.get("operation", response.tool_name)
        if total is not None and operands:
            symbol = _OPERATION_SYMBOLS.get(operation, operation)
            return (
                f"The result of {operands[0]} {symbol} {operands[1]} is {total}."
            )
    return f"The tool returned: {result}"


def format_weather_reply(response: ToolResponse) -> str:
    result = response.result
    if isinstance(result, dict):
        location = result.get("location", "the requested location")
        condition = result.get("condition")
        temperature = result.get("temperature")
        unit = result.get("unit", "celsius")
        if condition is not None and temperature is not None:
            unit_suffix = "°F" if unit == "fahrenheit" else "°C"
            return (
                f"The weather in {location} is {condition} "
                f"with a temperature of {temperature}{unit_suffix}."
            )
    return f"Weather tool response: {result}"


def create_app(
    *,
    math_client: MathMCPClient | None = None,
    weather_client: WeatherMCPClient | None = None,
) -> FastAPI:
    math_client = math_client or MathMCPClient(os.getenv("MATH_MCP_URL", "http://localhost:8001"))
    weather_client = weather_client or WeatherMCPClient(
        os.getenv("WEATHER_MCP_URL", "http://localhost:8002")
    )
    registry = ClientRegistry(math_client=math_client, weather_client=weather_client)

    app = FastAPI(title="Conversation Host")

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"service": "conversation-host", "status": "ok"}

    def get_registry() -> ClientRegistry:
        return registry

    @app.post("/conversation", response_model=ConversationResponse)
    async def conversation(
        request: RequestConversation,
        clients: ClientRegistry = Depends(get_registry),
    ) -> ConversationResponse:
        math_question = parse_math_question(request.question)
        if math_question:
            operation, a, b = math_question
            try:
                tool_response = await clients.math.calculate(operation, a, b)
            except (ToolInvocationError, ValueError) as exc:
                raise HTTPException(status_code=502, detail=str(exc)) from exc
            summary = ToolCallSummary(
                name=f"math.{operation}",
                result=tool_response.result,
                events=tool_response.events,
            )
            return ConversationResponse(
                interaction_id=request.interaction_id,
                question=request.question,
                reply=format_math_reply(tool_response),
                tool=summary,
            )

        weather_question = parse_weather_question(request.question)
        if weather_question:
            location, unit = weather_question
            try:
                tool_response = await clients.weather.current_weather(location, unit)
            except ToolInvocationError as exc:
                raise HTTPException(status_code=502, detail=str(exc)) from exc
            summary = ToolCallSummary(
                name="weather.current_weather",
                result=tool_response.result,
                events=tool_response.events,
            )
            return ConversationResponse(
                interaction_id=request.interaction_id,
                question=request.question,
                reply=format_weather_reply(tool_response),
                tool=summary,
            )

        return ConversationResponse(
            interaction_id=request.interaction_id,
            question=request.question,
            reply="I'm not sure how to help with that yet. Try asking about math or the weather.",
            tool=None,
        )

    return app


app = create_app()

