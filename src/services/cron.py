"""Cron service for GirlfriendGPT - scheduled task execution."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Dict, List, Optional
import time

logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """A scheduled task."""

    name: str
    interval: float  # seconds
    callback: Callable[[], Coroutine[Any, Any, Any]]
    enabled: bool = True
    last_run: float = 0.0
    next_run: float = field(default_factory=lambda: time.time())
    run_count: int = 0


class CronService:
    """Scheduled task service.

    This class provides:
    - Interval-based task scheduling
    - Task registration and management
    - Graceful shutdown
    """

    def __init__(self) -> None:
        """Initialize the cron service."""
        self._tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None

    def register(
        self,
        name: str,
        interval: float,
        callback: Callable[[], Coroutine[Any, Any, Any]],
        enabled: bool = True,
    ) -> None:
        """Register a scheduled task.

        Args:
            name: Task name
            interval: Interval in seconds
            callback: Async callback function
            enabled: Whether task is enabled
        """
        now = time.time()
        self._tasks[name] = ScheduledTask(
            name=name,
            interval=interval,
            callback=callback,
            enabled=enabled,
            last_run=0.0,
            next_run=now + interval,
        )
        logger.info(f"Registered cron task '{name}' with interval {interval}s")

    def unregister(self, name: str) -> None:
        """Unregister a scheduled task.

        Args:
            name: Task name
        """
        self._tasks.pop(name, None)
        logger.info(f"Unregistered cron task '{name}'")

    def enable(self, name: str) -> None:
        """Enable a scheduled task.

        Args:
            name: Task name
        """
        if name in self._tasks:
            self._tasks[name].enabled = True

    def disable(self, name: str) -> None:
        """Disable a scheduled task.

        Args:
            name: Task name
        """
        if name in self._tasks:
            self._tasks[name].enabled = False

    async def start(self) -> None:
        """Start the cron service."""
        if self._running:
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info(f"Cron service started with {len(self._tasks)} tasks")

    async def stop(self) -> None:
        """Stop the cron service."""
        if not self._running:
            return

        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

        logger.info("Cron service stopped")

    async def _worker(self) -> None:
        """Worker loop that executes scheduled tasks."""
        while self._running:
            try:
                now = time.time()

                # Find tasks due for execution
                due_tasks = [
                    task
                    for task in self._tasks.values()
                    if task.enabled and task.next_run <= now
                ]

                # Execute due tasks
                for task in due_tasks:
                    await self._execute_task(task)

                # Sleep until next task
                await asyncio.sleep(0.5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cron service error: {e}")
                await asyncio.sleep(1.0)

    async def _execute_task(self, task: ScheduledTask) -> None:
        """Execute a scheduled task.

        Args:
            task: Task to execute
        """
        try:
            logger.debug(f"Executing cron task '{task.name}'")
            await task.callback()
            task.last_run = time.time()
            task.next_run = task.last_run + task.interval
            task.run_count += 1
        except Exception as e:
            logger.error(f"Cron task '{task.name}' failed: {e}")
            # Still update next_run to prevent rapid retries
            task.last_run = time.time()
            task.next_run = task.last_run + task.interval

    def get_task_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a task.

        Args:
            name: Task name

        Returns:
            Task information or None
        """
        task = self._tasks.get(name)
        if not task:
            return None

        return {
            "name": task.name,
            "interval": task.interval,
            "enabled": task.enabled,
            "last_run": task.last_run,
            "next_run": task.next_run,
            "run_count": task.run_count,
        }

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get information about all tasks.

        Returns:
            List of task information dictionaries
        """
        return [self.get_task_info(name) for name in self._tasks]

    def __len__(self) -> int:
        """Get number of registered tasks."""
        return len(self._tasks)

    def __repr__(self) -> str:
        return f"CronService(tasks={len(self._tasks)})"
