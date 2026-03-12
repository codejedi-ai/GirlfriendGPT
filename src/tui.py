"""Terminal User Interface for GirlfriendGPT."""

import asyncio
import json
import websockets
from textual.app import App
from textual.widgets import Header, Footer, Static, Input, RichLog
from textual.containers import Vertical
from textual.binding import Binding

from src.config import ConfigManager


class ChatApp(App):
    """Simple chat application."""

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    CSS = """
    Screen {
        background: $surface;
    }
    #chatlog {
        height: 1fr;
        border: solid $primary;
        padding: 1;
        background: $background;
    }
    #status {
        height: 1;
        color: $text-muted;
    }
    #input {
        dock: bottom;
        height: 3;
    }
    #title {
        height: 2;
        text-align: center;
        text-style: bold;
    }
    """

    def __init__(self, config: dict, session_id: str):
        super().__init__()
        self.config = config
        self.session_id = session_id
        self.ws = None
        self.connected = False

    def compose(self):
        yield Header(show_clock=True)
        with Vertical():
            yield Static(f"🤖 {self.config.get('name', 'Companion')}", id="title")
            yield RichLog(markup=True, id="chatlog", wrap=True, highlight=True)
            yield Static("Connecting...", id="status")
            yield Input(placeholder="Type message... (Enter to send)", id="input")
        yield Footer()

    def on_mount(self):
        self.title = "GirlfriendGPT"
        asyncio.create_task(self.connect())

    async def connect(self):
        host = self.config.get("gateway_host", "127.0.0.1")
        port = self.config.get("gateway_port", 18789)
        uri = f"ws://{host}:{port}/ws/{self.session_id}"

        try:
            async with websockets.connect(uri) as websocket:
                self.ws = websocket
                self.connected = True
                self.set_status("Connected", "green")

                # Get greeting
                try:
                    greeting = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(greeting)
                    self.add_msg(data.get("role", "system"), data.get("content", ""))
                except:
                    pass

                # Listen loop
                while True:
                    try:
                        msg_json = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        msg = json.loads(msg_json)
                        if msg.get("type") != "ping":
                            self.add_msg(msg.get("role", ""), msg.get("content", ""))
                    except asyncio.TimeoutError:
                        continue
                    except websockets.ConnectionClosed:
                        break

        except Exception as e:
            self.connected = False
            self.set_status(f"Disconnected: {e}", "red")

    def add_msg(self, role: str, content: str):
        try:
            log = self.query_one("#chatlog", RichLog)
            name = self.config.get("name", "Companion")
            if role == "assistant":
                log.write(f"[bold cyan]{name}:[/] {content}")
            elif role == "user":
                log.write(f"[bold green]You:[/] {content}")
            elif content:
                log.write(f"[yellow]{content}[/]")
        except:
            pass

    def set_status(self, text: str, color: str = "white"):
        try:
            status = self.query_one("#status", Static)
            status.update(f"[{color}]{text}[/{color}]")
        except:
            pass

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id != "input":
            return
        text = event.value.strip()
        if not text:
            return

        self.add_msg("user", text)
        event.input.value = ""

        if self.connected and self.ws:
            asyncio.create_task(self.send_msg(text))

    async def send_msg(self, text: str):
        try:
            await self.ws.send(json.dumps({
                "role": "user",
                "content": text,
                "type": "text",
                "metadata": None
            }))
        except Exception as e:
            self.set_status(f"Error: {e}", "red")

    def action_quit(self):
        if self.ws:
            asyncio.create_task(self.ws.close())
        self.exit()


def run_tui(session_id: str = None, **kwargs):
    """Run the TUI."""
    import uuid
    config = ConfigManager.load_config()
    app = ChatApp(config, session_id or str(uuid.uuid4()))
    app.run()


def run_tui_main():
    """Entry point."""
    import uuid
    try:
        run_tui(str(uuid.uuid4()))
    except KeyboardInterrupt:
        print("\nGoodbye!")
