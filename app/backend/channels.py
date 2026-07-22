"""Channel adapters — the surfaces that put messages on the queue.

A ``ChannelAdapter`` is responsible for two things:

  1. Translating channel-native input (HTTP request, Telegram update,
     terminal keystroke) into an ``InboundEnvelope`` and ``publish``ing it
     on ``agents:inbound``.
  2. Consuming ``agents:replies``, filtering by ``target_channel``, and
     translating each reply back into the channel-native output.

v0.1 ships:
- ``InMemoryAdapter`` for tests / the demo (no real transport)
- Stub interfaces for ``FastAPIAdapter``, ``CLIAdapter``, ``BrowserTermAdapter``,
  ``TelegramAdapter``, ``DiscordAdapter`` — same shape, marked NotImplemented
  in v0.1 so we don't ship dead transport code.

The trust level a channel declares determines whether the dispatcher will
accept privileged actions from it.
"""

from __future__ import annotations

from typing import Protocol

from .bus import STREAM_INBOUND, STREAM_REPLIES, QueueBus
from .envelope import InboundEnvelope, OutboundEnvelope, TrustLevel


class ChannelAdapter(Protocol):
    name: str
    trust: TrustLevel

    async def submit(self, payload: dict, source_address: str) -> str: ...
    async def deliver(self, reply: OutboundEnvelope) -> None: ...


class InMemoryAdapter:
    """Test / demo adapter. Replies accumulate in a list for inspection."""

    def __init__(self, name: str, trust: TrustLevel, bus: QueueBus) -> None:
        self.name = name
        self.trust = trust
        self._bus = bus
        self.delivered: list[OutboundEnvelope] = []

    async def submit(self, payload: dict, source_address: str) -> str:
        env = InboundEnvelope(
            source_channel=self.name,
            source_address=source_address,
            trust=self.trust,
            payload=payload,
        )
        await self._bus.publish(STREAM_INBOUND, env.to_dict())
        return env.message_id

    async def deliver(self, reply: OutboundEnvelope) -> None:
        self.delivered.append(reply)

    async def consume_replies_for(self, target_channel: str) -> None:
        """Run a single iteration of the replies-consumer loop.

        In production this is an asyncio.Task; here we expose it as a
        single-iteration helper so tests can step through deterministically.
        """
        agen = self._bus.consume(STREAM_REPLIES, f"channel-{self.name}", self.name)
        async for msg in agen:
            reply = OutboundEnvelope.from_dict(msg.data)
            if reply.target_channel == target_channel:
                await self.deliver(reply)
            await self._bus.ack(STREAM_REPLIES, f"channel-{self.name}", msg.message_id)
            return


# ---------- production adapter stubs (interfaces only in v0.1) ----------


class _NotWiredAdapter:
    """Marker for adapters whose transport isn't implemented in v0.1.

    The class exists so the dispatcher / registry can be configured with
    the full channel set today and the transport can be filled in later
    without changing any other call site.
    """

    name: str = "<unwired>"
    trust: TrustLevel = TrustLevel.USER

    async def submit(self, payload: dict, source_address: str) -> str:
        raise NotImplementedError(
            f"{type(self).__name__} transport not implemented in v0.1; "
            "use InMemoryAdapter for tests/demo"
        )

    async def deliver(self, reply: OutboundEnvelope) -> None:
        raise NotImplementedError(
            f"{type(self).__name__} transport not implemented in v0.1"
        )


class FastAPIAdapter(_NotWiredAdapter):
    """HTTP enqueue + reply-via-WS/SSE/polling.

    TODO: wire into existing app/configclaw/api/agent_chat.py — refactor
    the message-handling endpoint to enqueue + return job id, then add
    a reply endpoint or WS upgrade. ADMIN trust (admin-only console).
    """

    name = "fastapi"
    trust = TrustLevel.ADMIN


class CLIAdapter(_NotWiredAdapter):
    """Stdin/stdout terminal adapter wired into the existing typer CLI.

    TODO: add ``configclaw chat`` command that puts each line on the
    queue and prints replies as they arrive. ADMIN trust.
    """

    name = "cli"
    trust = TrustLevel.ADMIN


class BrowserTermAdapter(_NotWiredAdapter):
    """WebSocket connector for the React-side terminal panel.

    TODO: tiny endpoint in app/configclaw/api/, React panel under
    app/frontend/aegis. USER trust.
    """

    name = "browser-term"
    trust = TrustLevel.USER


class TelegramAdapter(_NotWiredAdapter):
    """Telegram bot adapter (long-polling).

    Credential source: ChainedCredentialProvider key
    ``harness.telegram.bot_token``. USER trust.
    """

    name = "telegram"
    trust = TrustLevel.USER


class DiscordAdapter(_NotWiredAdapter):
    """Discord gateway adapter.

    Credential source: ChainedCredentialProvider key
    ``harness.discord.bot_token``. USER trust.
    """

    name = "discord"
    trust = TrustLevel.USER
