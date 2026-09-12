#!/usr/bin/env python3
# Copyright (C) 2026, Advanced Micro Devices, Inc. All rights reserved.
# Portions of this file consist of AI-generated content.
# SPDX-License-Identifier: Apache 2.0

"""
Custom Tools MCP Server

Provides AI assistant access to custom optimization tools via the Model
Context Protocol. Tools are auto-discovered from the sibling `tools/`
directory; see `tools/_template.py` for the per-tool contract.
"""
import argparse
import asyncio
import importlib
import json
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio


# Required attribute names every tool module must expose.
_REQUIRED_TOOL_ATTRS = ("NAME", "DESCRIPTION", "INPUT_SCHEMA", "run")

# Logger configured in main() based on CLI args.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Server instance.
app = Server("custom-tools-mcp")

# Populated by _discover_tools() before the server starts serving.
_REGISTRY: Dict[str, ModuleType] = {}


def _discover_tools(tools_dir: Path) -> Dict[str, ModuleType]:
    """Import every `tools/*.py` (skipping `__init__.py` and `_*.py`)
    and build a registry keyed by each module's `NAME` attribute.

    Skips (with a warning) any module missing required attributes or that
    fails to import. Raises on duplicate `NAME` to fail-fast at startup.
    """
    registry: Dict[str, ModuleType] = {}

    if not tools_dir.is_dir():
        logger.warning(f"Tools directory not found: {tools_dir}")
        return registry

    for path in sorted(tools_dir.glob("*.py")):
        stem = path.stem
        if stem == "__init__" or stem.startswith("_"):
            continue

        try:
            module = importlib.import_module(f"tools.{stem}")
        except Exception as e:
            logger.warning(f"Failed to import tools.{stem}: {e}")
            continue

        missing = [a for a in _REQUIRED_TOOL_ATTRS if not hasattr(module, a)]
        if missing:
            logger.warning(
                f"Skipping tools.{stem}: missing required attribute(s) {missing}"
            )
            continue

        name = getattr(module, "NAME")
        if name in registry:
            raise RuntimeError(
                f"Duplicate tool NAME '{name}' (in tools.{stem} and "
                f"tools.{registry[name].__name__.split('.')[-1]})"
            )
        registry[name] = module
        logger.info(f"Registered tool: {name} (from tools/{stem}.py)")

    return registry


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Return the full set of discovered custom tools."""
    return [
        Tool(
            name=module.NAME,
            description=module.DESCRIPTION,
            inputSchema=module.INPUT_SCHEMA,
        )
        for module in _REGISTRY.values()
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Dispatch a tool call to its module's `run()` function."""
    try:
        logger.info(f"Tool called: {name} with arguments: {arguments}")
        module = _REGISTRY.get(name)
        if module is None:
            result: Dict[str, Any] = {"error": f"Unknown tool: {name}"}
        else:
            result = module.run(arguments or {})
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e), "tool": name}, indent=2),
        )]


async def main():
    """Main entry point for the server."""
    global _REGISTRY

    parser = argparse.ArgumentParser(description="Custom Tools MCP Server")
    parser.add_argument(
        "--mcp-log",
        type=str,
        help="Path to log file for MCP server logs",
    )
    args = parser.parse_args()

    if args.mcp_log:
        mcp_log_file = open(args.mcp_log, "w", buffering=1)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(mcp_log_file)],
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stderr)],
        )

    server_dir = Path(__file__).parent.resolve()
    if str(server_dir) not in sys.path:
        sys.path.insert(0, str(server_dir))

    _REGISTRY = _discover_tools(server_dir / "tools")
    logger.info(f"Starting Custom Tools MCP Server with {len(_REGISTRY)} tool(s)...")

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("Server running on stdio transport")
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
