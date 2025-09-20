# MCP Example Platform

This repository contains a small platform that demonstrates how a FastAPI host
application can orchestrate multiple Model Context Protocol (MCP) compatible
servers. Two tool servers are provided:

* **Math Toolkit** – exposes basic arithmetic operations over a streamable HTTP
  interface implemented with a lightweight `fastmcp` helper.
* **Weather Toolkit** – serves a simple weather lookup service over streaming
  HTTP using an equally small `mcp` helper.

The host application exposes a `/conversation` endpoint that routes incoming
questions to the appropriate MCP tool, produces a human friendly reply and
includes a record of the streaming events that were emitted during the tool
invocation.

## Features

* Stream-aware HTTP client base class that converts tool responses into
  structured `ToolResponse` objects.
* Math client with add, subtract and multiply helpers that communicate with the
  FastMCP-based math server.
* Weather client capable of retrieving temperatures in Celsius or Fahrenheit
  from the MCP server.
* FastAPI host service with request routing, response formatting and graceful
  fallbacks when a question is not understood.
* Comprehensive test suite that exercises the servers, clients and host
  end-to-end via ASGI transports.

## Change History

* **v0.1.0** – Initial end-to-end implementation of the host service, math and
  weather MCP servers, typed client SDK, automated tests and developer tooling.

## Running the services locally

The project uses standard ASGI applications, so the services can be launched
with Uvicorn. A typical development workflow looks like this:

```bash
# Optionally create a virtual environment first
python -m venv .venv
source .venv/bin/activate

# Install dependencies for the host and tests
pip install fastapi httpx pydantic uvicorn pytest pytest-asyncio ruff

# Run the math MCP server
uvicorn mcp_server.server_a.server:app --reload --port 8001

# Run the weather MCP server in a separate terminal
uvicorn mcp_server.server_b.server:app --reload --port 8002

# Launch the host FastAPI app
uvicorn host.app.app:app --reload --port 8000
```

Once all three services are running you can interact with the host endpoint:

```bash
curl -X POST http://localhost:8000/conversation \
     -H "Content-Type: application/json" \
     -d '{"question": "What is 12 + 7?", "interaction_id": "demo-1"}'
```

The response will include the generated reply plus all streamed events from the
invoked tool.

### Running the automated checks

```bash
ruff check .
pytest
```

## Future improvements

* Expand the math server with division, power operations and better numeric
  parsing in the host router.
* Swap the in-repository `fastmcp`/`mcp` shims with the official packages once
  they are available in the execution environment.
* Persist conversation history and expose past tool invocations from the host
  API.
* Provide Docker Compose definitions for running all services together with a
  single command.

