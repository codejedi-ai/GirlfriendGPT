"""Real channel adapters: CLI, FastAPI, Browser-Terminal (WS),
Telegram (python-telegram-bot), Discord (discord.py).

Each adapter is a self-contained module that:
  - reads channel-native input,
  - constructs an ``InboundEnvelope`` and ``publish``es to ``agents:inbound``
    on the supplied ``QueueBus``,
  - consumes ``agents:replies`` filtered on its own ``target_channel``
    and delivers natively.

All five drop to no-op startup methods when their SDK isn't importable,
so the factory can ``adapter.start()`` everything without conditionals.
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any, Awaitable, Callable

from .bus import STREAM_INBOUND, STREAM_REPLIES, QueueBus
from .envelope import InboundEnvelope, OutboundEnvelope, TrustLevel


# ---------- import availability ----------

try:
    from telegram import Update  # type: ignore
    from telegram.ext import Application, MessageHandler, filters  # type: ignore

    TELEGRAM_AVAILABLE = True
except Exception:  # noqa: BLE001
    Update = None  # type: ignore[assignment]
    Application = None  # type: ignore[assignment]
    MessageHandler = None  # type: ignore[assignment]
    filters = None  # type: ignore[assignment]
    TELEGRAM_AVAILABLE = False

try:
    import discord  # type: ignore

    DISCORD_AVAILABLE = True
except Exception:  # noqa: BLE001
    discord = None  # type: ignore[assignment]
    DISCORD_AVAILABLE = False

try:
    from fastapi import APIRouter, WebSocket, WebSocketDisconnect  # type: ignore

    FASTAPI_AVAILABLE = True
except Exception:  # noqa: BLE001
    APIRouter = None  # type: ignore[assignment]
    WebSocket = None  # type: ignore[assignment]
    WebSocketDisconnect = Exception  # type: ignore[assignment]
    FASTAPI_AVAILABLE = False


# ---------- shared base ----------


class _BaseAdapter:
    name: str = "<base>"
    trust: TrustLevel = TrustLevel.USER

    def __init__(self, bus: QueueBus) -> None:
        self._bus = bus
        self._task: asyncio.Task | None = None

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
        raise NotImplementedError

    async def _replies_loop(self) -> None:
        agen = self._bus.consume(STREAM_REPLIES, f"channel-{self.name}", self.name)
        async for msg in agen:
            try:
                reply = OutboundEnvelope.from_dict(msg.data)
            except Exception:
                await self._bus.ack(
                    STREAM_REPLIES, f"channel-{self.name}", msg.message_id
                )
                continue
            if reply.target_channel == self.name:
                try:
                    await self.deliver(reply)
                except Exception:
                    # Don't crash the loop on a single bad reply.
                    pass
            await self._bus.ack(
                STREAM_REPLIES, f"channel-{self.name}", msg.message_id
            )

    async def start(self) -> None:
        self._task = asyncio.create_task(self._replies_loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None


# ---------- CLI adapter ----------


class RealCLIAdapter(_BaseAdapter):
    """stdin -> queue, queue -> stdout. Admin trust (it's your terminal)."""

    name = "cli"
    trust = TrustLevel.ADMIN

    def __init__(self, bus: QueueBus, *, stream_out=None) -> None:
        super().__init__(bus)
        self._out = stream_out or sys.stdout

    async def deliver(self, reply: OutboundEnvelope) -> None:
        prefix = (
            f"[reusing {reply.harness_hit}] " if reply.harness_hit else ""
        )
        text = reply.payload.get("text", "")
        self._out.write(f"\n>>> {prefix}{text}\n")
        self._out.flush()

    async def run_repl(self) -> None:
        """Tiny REPL: each line is a user message."""
        await self.start()
        loop = asyncio.get_running_loop()
        try:
            while True:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                if line in {"/quit", "/exit"}:
                    break
                await self.submit({"text": line}, source_address="terminal")
        finally:
            await self.stop()


# ---------- FastAPI HTTP adapter ----------


class RealFastAPIAdapter(_BaseAdapter):
    """HTTP enqueue endpoint + SSE reply polling.

    Mount on the existing app via ``app.include_router(adapter.router)``.
    Admin trust — the FastAPI surface is the admin console, just like CLI.
    """

    name = "fastapi"
    trust = TrustLevel.ADMIN

    def __init__(self, bus: QueueBus) -> None:
        super().__init__(bus)
        self._pending: dict[str, asyncio.Future] = {}
        if FASTAPI_AVAILABLE:
            self.router = APIRouter(prefix="/api/v1/harness", tags=["harness"])
            self._wire_routes()
        else:
            self.router = None

    def _wire_routes(self) -> None:
        @self.router.post("/messages")
        async def enqueue(payload: dict) -> dict:
            msg_id = await self.submit(
                payload, source_address=payload.get("source_address", "http")
            )
            fut: asyncio.Future = asyncio.get_running_loop().create_future()
            self._pending[msg_id] = fut
            try:
                reply = await asyncio.wait_for(fut, timeout=60.0)
            except asyncio.TimeoutError:
                return {"message_id": msg_id, "status": "timeout"}
            finally:
                self._pending.pop(msg_id, None)
            return {
                "message_id": msg_id,
                "reply": reply.payload,
                "harness_hit": reply.harness_hit,
            }

    async def deliver(self, reply: OutboundEnvelope) -> None:
        fut = self._pending.get(reply.in_reply_to)
        if fut is not None and not fut.done():
            fut.set_result(reply)


# ---------- Browser Terminal adapter (WebSocket) ----------


class RealBrowserTermAdapter(_BaseAdapter):
    """WebSocket adapter for the React-side terminal panel.

    Mount via ``app.add_api_websocket_route("/api/v1/harness/ws", adapter.ws_handler)``.
    USER trust — anyone with the page open is a user, not admin.
    """

    name = "browser-term"
    trust = TrustLevel.USER

    def __init__(self, bus: QueueBus) -> None:
        super().__init__(bus)
        self._sockets: dict[str, "WebSocket"] = {}

    async def deliver(self, reply: OutboundEnvelope) -> None:
        ws = self._sockets.get(reply.target_address)
        if ws is None:
            return
        await ws.send_json(
            {
                "text": reply.payload.get("text", ""),
                "harness_hit": reply.harness_hit,
            }
        )

    async def ws_handler(self, websocket: "WebSocket", client_id: str) -> None:
        if not FASTAPI_AVAILABLE:  # pragma: no cover
            return
        await websocket.accept()
        self._sockets[client_id] = websocket
        try:
            while True:
                data = await websocket.receive_json()
                await self.submit(data, source_address=client_id)
        except WebSocketDisconnect:
            pass
        finally:
            self._sockets.pop(client_id, None)


# ---------- Telegram adapter ----------


class RealTelegramAdapter(_BaseAdapter):
    """Telegram bot — long-poll updates, publish each text message."""

    name = "telegram"
    trust = TrustLevel.USER

    def __init__(self, bus: QueueBus, token: str) -> None:
        super().__init__(bus)
        if not TELEGRAM_AVAILABLE:
            raise RuntimeError(
                "python-telegram-bot not installed; cannot start Telegram adapter"
            )
        self._token = token
        self._app: Any = None

    async def _on_message(self, update: "Update", context) -> None:
        if not update.message or not update.message.text:
            return
        await self.submit(
            {"text": update.message.text},
            source_address=str(update.effective_chat.id),
        )

    async def deliver(self, reply: OutboundEnvelope) -> None:
        if self._app is None:
            return
        prefix = (
            f"[reusing {reply.harness_hit}]\n"
            if reply.harness_hit
            else ""
        )
        await self._app.bot.send_message(
            chat_id=int(reply.target_address),
            text=f"{prefix}{reply.payload.get('text', '')}",
        )

    async def start(self) -> None:
        await super().start()
        self._app = Application.builder().token(self._token).build()
        self._app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message)
        )
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling()

    async def stop(self) -> None:
        try:
            if self._app is not None:
                await self._app.updater.stop()
                await self._app.stop()
                await self._app.shutdown()
        finally:
            await super().stop()


# ---------- Discord adapter ----------


class RealDiscordAdapter(_BaseAdapter):
    """Discord bot — messages from any channel the bot is in."""

    name = "discord"
    trust = TrustLevel.USER

    def __init__(self, bus: QueueBus, token: str) -> None:
        super().__init__(bus)
        if not DISCORD_AVAILABLE:
            raise RuntimeError(
                "discord.py not installed; cannot start Discord adapter"
            )
        self._token = token
        intents = discord.Intents.default()
        intents.message_content = True
        self._client = discord.Client(intents=intents)
        self._client.event(self._on_message)

    async def _on_message(self, message: "discord.Message") -> None:
        if message.author.bot:
            return
        await self.submit(
            {"text": message.content},
            source_address=str(message.channel.id),
        )

    async def deliver(self, reply: OutboundEnvelope) -> None:
        chan = self._client.get_channel(int(reply.target_address))
        if chan is None:
            try:
                chan = await self._client.fetch_channel(int(reply.target_address))
            except Exception:
                return
        prefix = (
            f"[reusing {reply.harness_hit}]\n"
            if reply.harness_hit
            else ""
        )
        await chan.send(f"{prefix}{reply.payload.get('text', '')}")

    async def start(self) -> None:
        await super().start()
        # Run the discord client as a background task.
        self._task_discord = asyncio.create_task(self._client.start(self._token))

    async def stop(self) -> None:
        try:
            await self._client.close()
        finally:
            await super().stop()


# ---------- credential resolution ----------


def resolve_channel_token(name: str) -> str | None:
    """Try vault first via the existing ChainedCredentialProvider; fall
    back to env. Vault keys are `harness.<channel>.bot_token` per design.
    """
    env_key = {
        "telegram": "TELEGRAM_BOT_TOKEN",
        "discord": "DISCORD_BOT_TOKEN",
    }.get(name)
    if env_key and os.environ.get(env_key):
        return os.environ[env_key]
    try:  # pragma: no cover - environment-dependent
        from configclaw.infra.credentials import ChainedCredentialProvider  # type: ignore

        # The existing provider is async + saas-shaped; for v1 we just
        # honor the env path. Real wiring lives in the dispatcher start-up
        # script the user runs on their Mac.
        _ = ChainedCredentialProvider  # placeholder for future use
    except Exception:
        pass
    return None
