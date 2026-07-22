"""Heartbeat service for GirlfriendGPT - periodic health checks."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Dict, List, Optional
import time

logger = logging.getLogger(__name__)


@dataclass
class HealthCheck:
    """A health check definition."""

    name: str
    interval: float  # seconds
    callback: Callable[[], Coroutine[Any, Any, bool]]
    healthy: bool = True
    last_check: float = 0.0
    last_error: Optional[str] = None
    check_count: int = 0


class HeartbeatService:
    """Periodic health check service.

    This class provides:
    - Periodic health checks
    - Health status tracking
    - Alert callbacks on failure
    """

    def __init__(self) -> None:
        """Initialize the heartbeat service."""
        self._checks: Dict[str, HealthCheck] = {}
        self._alert_callbacks: List[Callable[[str, str], Coroutine[Any, Any, None]]] = []
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._overall_healthy = True

    def register_check(
        self,
        name: str,
        interval: float,
        callback: Callable[[], Coroutine[Any, Any, bool]],
    ) -> None:
        """Register a health check.

        Args:
            name: Check name
            interval: Interval in seconds
            callback: Async callback that returns True if healthy
        """
        self._checks[name] = HealthCheck(
            name=name,
            interval=interval,
            callback=callback,
            healthy=True,
            last_check=0.0,
        )
        logger.info(f"Registered health check '{name}' with interval {interval}s")

    def unregister_check(self, name: str) -> None:
        """Unregister a health check.

        Args:
            name: Check name
        """
        self._checks.pop(name, None)
        logger.info(f"Unregistered health check '{name}'")

    def add_alert_callback(
        self, callback: Callable[[str, str], Coroutine[Any, Any, None]]
    ) -> None:
        """Add an alert callback for health failures.

        Args:
            callback: Async callback that receives (check_name, error_message)
        """
        self._alert_callbacks.append(callback)

    def remove_alert_callback(
        self, callback: Callable[[str, str], Coroutine[Any, Any, None]]
    ) -> None:
        """Remove an alert callback.

        Args:
            callback: Callback to remove
        """
        try:
            self._alert_callbacks.remove(callback)
        except ValueError:
            pass

    async def start(self) -> None:
        """Start the heartbeat service."""
        if self._running:
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info(
            f"Heartbeat service started with {len(self._checks)} checks"
        )

    async def stop(self) -> None:
        """Stop the heartbeat service."""
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

        logger.info("Heartbeat service stopped")

    async def _worker(self) -> None:
        """Worker loop that executes health checks."""
        while self._running:
            try:
                now = time.time()

                # Find checks due for execution
                due_checks = [
                    check
                    for check in self._checks.values()
                    if check.last_check + check.interval <= now
                ]

                # Execute due checks
                for check in due_checks:
                    await self._execute_check(check)

                # Update overall health
                self._overall_healthy = all(
                    check.healthy for check in self._checks.values()
                )

                # Sleep
                await asyncio.sleep(1.0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat service error: {e}")
                await asyncio.sleep(1.0)

    async def _execute_check(self, check: HealthCheck) -> None:
        """Execute a health check.

        Args:
            check: Check to execute
        """
        try:
            logger.debug(f"Executing health check '{check.name}'")
            result = await check.callback()
            check.healthy = result
            check.last_check = time.time()
            check.check_count += 1
            check.last_error = None

            if not result:
                logger.warning(f"Health check '{check.name}' failed")
                await self._alert(check.name, "Health check returned False")

        except Exception as e:
            check.healthy = False
            check.last_check = time.time()
            check.check_count += 1
            check.last_error = str(e)
            logger.error(f"Health check '{check.name}' failed: {e}")
            await self._alert(check.name, str(e))

    async def _alert(self, check_name: str, error_message: str) -> None:
        """Send alerts for a health check failure.

        Args:
            check_name: Name of failed check
            error_message: Error message
        """
        for callback in self._alert_callbacks:
            try:
                await callback(check_name, error_message)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

    def is_healthy(self) -> bool:
        """Check if all health checks are passing.

        Returns:
            True if all checks are healthy
        """
        return self._overall_healthy

    def get_check_status(self, name: str) -> Optional[Dict[str, Any]]:
        """Get status of a health check.

        Args:
            name: Check name

        Returns:
            Check status or None
        """
        check = self._checks.get(name)
        if not check:
            return None

        return {
            "name": check.name,
            "healthy": check.healthy,
            "last_check": check.last_check,
            "last_error": check.last_error,
            "check_count": check.check_count,
            "interval": check.interval,
        }

    def get_all_statuses(self) -> List[Dict[str, Any]]:
        """Get status of all health checks.

        Returns:
            List of status dictionaries
        """
        return [self.get_check_status(name) for name in self._checks]

    async def run_all_checks_now(self) -> Dict[str, bool]:
        """Run all health checks immediately.

        Returns:
            Dictionary of check results
        """
        results = {}
        for check in self._checks.values():
            try:
                results[check.name] = await check.callback()
            except Exception:
                results[check.name] = False
        return results

    def __len__(self) -> int:
        """Get number of registered checks."""
        return len(self._checks)

    def __repr__(self) -> str:
        healthy_count = sum(1 for c in self._checks.values() if c.healthy)
        return f"HeartbeatService(healthy={healthy_count}/{len(self._checks)})"
