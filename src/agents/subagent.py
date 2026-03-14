"""Subagent support for GirlfriendGPT."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor


@dataclass
class SubagentRequest:
    """Request to a subagent."""

    task: str
    context: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 60.0


@dataclass
class SubagentResponse:
    """Response from a subagent."""

    success: bool
    result: Any = None
    error: Optional[str] = None


class Subagent:
    """Spawns and manages subagents for specialized tasks.

    This class provides:
    - Subagent spawning
    - Task delegation
    - Result aggregation
    """

    def __init__(
        self,
        parent_agent: Any,
        max_concurrent: int = 3,
    ) -> None:
        """Initialize the subagent manager.

        Args:
            parent_agent: The parent agent instance
            max_concurrent: Maximum concurrent subagents
        """
        self._parent_agent = parent_agent
        self._max_concurrent = max_concurrent
        self._executor: Optional[ThreadPoolExecutor] = None
        self._active_subagents: Dict[str, asyncio.Task] = {}

    async def spawn(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: float = 60.0,
    ) -> SubagentResponse:
        """Spawn a subagent to handle a task.

        Args:
            task: Task description
            context: Task context
            timeout: Timeout in seconds

        Returns:
            Subagent response
        """
        # For now, subagents are just the same agent with different context
        # In the future, this could spawn different specialized agents

        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_running_loop()
            if not self._executor:
                self._executor = ThreadPoolExecutor(
                    max_workers=self._max_concurrent
                )

            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self._executor,
                    self._run_subagent,
                    task,
                    context or {},
                ),
                timeout=timeout,
            )

            return SubagentResponse(success=True, result=result)
        except asyncio.TimeoutError:
            return SubagentResponse(
                success=False, error=f"Subagent timed out after {timeout}s"
            )
        except Exception as e:
            return SubagentResponse(success=False, error=str(e))

    def _run_subagent(
        self, task: str, context: Dict[str, Any]
    ) -> str:
        """Run a subagent task (blocking).

        Args:
            task: Task description
            context: Task context

        Returns:
            Subagent result
        """
        # Build enhanced prompt with context
        context_str = "\n".join(
            f"{k}: {v}" for k, v in context.items()
        )
        enhanced_task = f"""
Context:
{context_str}

Task: {task}

Please handle this specialized task."""

        # Call parent agent
        if hasattr(self._parent_agent, "respond"):
            return self._parent_agent.respond(enhanced_task)
        else:
            return "Error: Parent agent has no respond method"

    async def spawn_multiple(
        self,
        tasks: List[SubagentRequest],
    ) -> List[SubagentResponse]:
        """Spawn multiple subagents concurrently.

        Args:
            tasks: List of subagent requests

        Returns:
            List of subagent responses
        """
        coroutines = [
            self.spawn(task.task, task.context, task.timeout)
            for task in tasks
        ]
        return await asyncio.gather(*coroutines)

    async def shutdown(self) -> None:
        """Shutdown all subagents and release resources."""
        # Cancel active tasks
        for task_id, task in self._active_subagents.items():
            if not task.done():
                task.cancel()

        # Shutdown executor
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

        self._active_subagents.clear()

    def __del__(self) -> None:
        """Cleanup on deletion."""
        if self._executor:
            self._executor.shutdown(wait=False)
