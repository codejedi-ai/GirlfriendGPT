"""Message queue and bus implementation."""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional
from .events import Event, InboundMessage, OutboundMessage, EventType


class MessageQueue:
    """Async message queue for event processing."""

    def __init__(self, maxsize: int = 0) -> None:
        """Initialize the message queue.

        Args:
            maxsize: Maximum queue size (0 for unlimited)
        """
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)

    async def put(self, event: Event) -> None:
        """Put an event on the queue."""
        await self._queue.put(event)

    async def get(self) -> Event:
        """Get an event from the queue."""
        return await self._queue.get()

    def put_nowait(self, event: Event) -> None:
        """Put an event on the queue without waiting."""
        self._queue.put_nowait(event)

    def get_nowait(self) -> Event:
        """Get an event from the queue without waiting."""
        return self._queue.get_nowait()

    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()

    def qsize(self) -> int:
        """Get queue size."""
        return self._queue.qsize()


class MessageBus:
    """Central message bus for pub/sub messaging."""

    def __init__(self) -> None:
        """Initialize the message bus."""
        self._subscribers: Dict[EventType, List[Callable[[Event], Any]]] = {}
        self._queue = MessageQueue()
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the message bus processor."""
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_messages())

    async def stop(self) -> None:
        """Stop the message bus processor."""
        if not self._running:
            return

        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
            self._processor_task = None

    async def publish(self, message: InboundMessage | OutboundMessage | Event) -> None:
        """Publish a message to the bus.

        Args:
            message: The message or event to publish
        """
        if isinstance(message, InboundMessage):
            event = message.to_event()
        elif isinstance(message, OutboundMessage):
            event = message.to_event()
        else:
            event = message

        await self._queue.put(event)

        # Notify subscribers immediately (non-blocking)
        if event.type in self._subscribers:
            for callback in self._subscribers[event.type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(event))
                    else:
                        callback(event)
                except Exception as e:
                    # Log but don't propagate subscriber errors
                    import logging

                    logging.getLogger(__name__).error(
                        f"Error in subscriber callback for {event.type}: {e}"
                    )

    async def _process_messages(self) -> None:
        """Process messages from the queue."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                # Additional processing can be done here if needed
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                import logging

                logging.getLogger(__name__).error(f"Error processing message: {e}")

    def subscribe(
        self, event_type: EventType, callback: Callable[[Event], Any]
    ) -> None:
        """Subscribe to an event type.

        Args:
            event_type: The type of event to subscribe to
            callback: Function to call when event is published
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(
        self, event_type: EventType, callback: Callable[[Event], Any]
    ) -> None:
        """Unsubscribe from an event type.

        Args:
            event_type: The type of event to unsubscribe from
            callback: The callback to remove
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass

    async def wait_until_complete(self) -> None:
        """Wait for all queued messages to be processed."""
        await self._queue._queue.join()
