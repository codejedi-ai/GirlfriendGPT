"""Agent run loop that dispatches gateway messages to worker threads."""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class _LoopItem:
    """Represents one inbound message to be processed by the agent."""

    session_id: str
    content: str
    future: asyncio.Future


class AgentRunLoop:
    """Non-blocking run loop for dispatching agent calls to worker threads."""

    def __init__(self, get_agent: Callable[[], Optional[Any]], workers: int = 1):
        self._get_agent = get_agent
        self._workers_count = max(1, workers)
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_tasks: list[asyncio.Task] = []
        self._executor: Optional[ThreadPoolExecutor] = None
        self._running = False

    async def start(self):
        """Start background workers."""
        if self._running:
            return

        self._running = True
        self._executor = ThreadPoolExecutor(
            max_workers=self._workers_count,
            thread_name_prefix="agent-loop",
        )
        self._worker_tasks = [
            asyncio.create_task(self._worker(worker_id))
            for worker_id in range(self._workers_count)
        ]
        logger.info("Agent run loop started with %s workers", self._workers_count)

    async def stop(self):
        """Stop workers and thread pool."""
        if not self._running:
            return

        self._running = False

        for _ in self._worker_tasks:
            await self._queue.put(None)

        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks = []

        if self._executor:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None

        logger.info("Agent run loop stopped")

    async def submit(self, session_id: str, content: str, timeout: float = 180.0) -> str:
        """Submit a message for threaded execution and await its result."""
        if not self._running:
            await self.start()

        loop = asyncio.get_running_loop()
        result_future = loop.create_future()
        await self._queue.put(_LoopItem(session_id=session_id, content=content, future=result_future))

        try:
            return await asyncio.wait_for(result_future, timeout=timeout)
        except asyncio.TimeoutError:
            if not result_future.done():
                result_future.cancel()
            return "Error: Agent response timed out"

    def _invoke_agent(self, content: str) -> str:
        """Run the agent invocation inside a worker thread."""
        agent = self._get_agent()
        if not agent:
            return "Error: Agent not initialized"
        return agent.respond(content)

    async def _worker(self, worker_id: int):
        """Queue consumer that fans out work to thread pool workers."""
        loop = asyncio.get_running_loop()

        while True:
            item = await self._queue.get()
            try:
                if item is None:
                    break

                if item.future.cancelled():
                    continue

                try:
                    response = await loop.run_in_executor(self._executor, self._invoke_agent, item.content)
                except Exception as exc:
                    logger.exception("Worker %s failed to process message", worker_id)
                    response = f"Error: {exc}"

                if not item.future.done():
                    item.future.set_result(response)
            finally:
                self._queue.task_done()
