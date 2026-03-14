"""Tool registry for GirlfriendGPT."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ToolDef:
    """Definition of a registered tool."""

    name: str
    fn: Callable
    description: str
    schema: dict
    module: Optional[str] = None

    def to_openai_format(self) -> dict:
        """Convert to OpenAI-compatible tool definition."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.schema,
            },
        }


# Global tool registry
_TOOLS: Dict[str, ToolDef] = {}


def register_tool(
    name: str, description: str, schema: dict
) -> Callable[[Callable], Callable]:
    """Decorator to register a tool.

    Args:
        name: Tool name
        description: Human-readable description
        schema: JSON schema for tool parameters

    Returns:
        Decorator function

    Example:
        @register_tool(
            name="read_file",
            description="Read the contents of a file",
            schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read"}
                },
                "required": ["path"]
            }
        )
        async def read_file(path: str) -> str:
            ...
    """

    def decorator(fn: Callable) -> Callable:
        _TOOLS[name] = ToolDef(
            name=name,
            fn=fn,
            description=description,
            schema=schema,
            module=fn.__module__,
        )
        return fn

    return decorator


def get_all_tools() -> List[dict]:
    """Return all registered tools in OpenAI-compatible format.

    Returns:
        List of tool definitions
    """
    return [tool.to_openai_format() for tool in _TOOLS.values()]


def get_tool(name: str) -> Optional[ToolDef]:
    """Get a tool definition by name.

    Args:
        name: Tool name

    Returns:
        Tool definition or None if not found
    """
    return _TOOLS.get(name)


def get_tool_names() -> List[str]:
    """Get list of all registered tool names.

    Returns:
        List of tool names
    """
    return list(_TOOLS.keys())


async def execute_tool(name: str, arguments: dict) -> Any:
    """Execute a registered tool.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        Tool execution result

    Raises:
        ToolNotFoundError: If tool is not registered
        ToolExecutionError: If tool execution fails
    """
    from ..utils.errors import ToolExecutionError, ToolNotFoundError

    tool = _TOOLS.get(name)
    if not tool:
        raise ToolNotFoundError(name, f"Available tools: {', '.join(get_tool_names())}")

    try:
        if inspect.iscoroutinefunction(tool.fn):
            return await tool.fn(**arguments)
        else:
            return tool.fn(**arguments)
    except Exception as e:
        raise ToolExecutionError(name, str(e)) from e


def clear_tools() -> None:
    """Clear all registered tools.

    Useful for testing or reloading tools.
    """
    _TOOLS.clear()


def register_tools_from_module(module: Any) -> int:
    """Auto-register tools from a module.

    Looks for functions with a '_tool_def' attribute (set by @register_tool).

    Args:
        module: Module to scan for tools

    Returns:
        Number of tools registered
    """
    count = 0
    for name in dir(module):
        obj = getattr(module, name)
        if callable(obj) and hasattr(obj, "_tool_def"):
            tool_def = obj._tool_def
            _TOOLS[tool_def.name] = tool_def
            count += 1
    return count
