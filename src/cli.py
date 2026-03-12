"""CLI interface for GirlfriendGPT."""

import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Optional

import click
import websockets

from src.config import ConfigManager


class CLIClient:
    """Lightweight CLI client for the gateway."""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.config = ConfigManager.load_config()
    
    async def send_message(self, message: str, message_type: str = "text") -> str:
        """Send a message and get response."""
        host = self.config.get("gateway_host", "127.0.0.1")
        port = self.config.get("gateway_port", 18789)
        uri = f"ws://{host}:{port}/ws/{self.session_id}"
        
        try:
            async with websockets.connect(uri) as websocket:
                # Receive greeting
                greeting_json = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                greeting = json.loads(greeting_json)
                print(f"\n[{greeting['role']}]: {greeting['content']}\n")
                
                # Send message
                msg_data = {
                    "role": "user",
                    "content": message,
                    "type": message_type,
                    "metadata": None
                }
                await websocket.send(json.dumps(msg_data))
                
                # Receive responses
                response_text = ""
                try:
                    while True:
                        response_json = await asyncio.wait_for(
                            websocket.recv(), 
                            timeout=60.0
                        )
                        response = json.loads(response_json)
                        print(f"[{response['role']}]: {response['content']}\n")
                        response_text += response['content']
                except asyncio.TimeoutError:
                    pass
                
                return response_text
        
        except Exception as e:
            click.echo(f"Error: Could not connect to gateway", err=True)
            click.echo(f"Details: {str(e)}", err=True)
            click.echo(f"\nMake sure the gateway is running:", err=True)
            click.echo(f"  gfgpt gateway start", err=True)
            sys.exit(1)
    
    async def interactive_chat(self):
        """Start interactive chat session."""
        host = self.config.get("gateway_host", "127.0.0.1")
        port = self.config.get("gateway_port", 18789)
        uri = f"ws://{host}:{port}/ws/{self.session_id}"
        
        try:
            async with websockets.connect(uri) as websocket:
                # Receive greeting
                greeting_json = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                greeting = json.loads(greeting_json)
                print(f"\n[{greeting['role']}]: {greeting['content']}\n")
                
                # Start chat loop
                while True:
                    try:
                        user_input = input("You: ").strip()
                        
                        if not user_input:
                            continue
                        
                        if user_input.lower() in ['exit', 'quit', 'bye']:
                            print("Goodbye!")
                            break
                        
                        # Send message
                        msg_data = {
                            "role": "user",
                            "content": user_input,
                            "type": "text",
                            "metadata": None
                        }
                        await websocket.send(json.dumps(msg_data))
                        
                        # Receive response
                        try:
                            response_json = await asyncio.wait_for(
                                websocket.recv(),
                                timeout=60.0
                            )
                            response = json.loads(response_json)
                            print(f"[{response['role']}]: {response['content']}\n")
                        except asyncio.TimeoutError:
                            print("[system]: Response timeout\n")
                    
                    except KeyboardInterrupt:
                        print("\n\nGoodbye!")
                        break
        
        except Exception as e:
            click.echo(f"Error: Could not connect to gateway", err=True)
            click.echo(f"Details: {str(e)}", err=True)
            click.echo(f"\nMake sure the gateway is running:", err=True)
            click.echo(f"  gfgpt gateway start", err=True)
            sys.exit(1)


@click.group()
@click.version_option(version="1.0.0", prog_name="GirlfriendGPT")
def cli():
    """GirlfriendGPT - AI Companion Agent."""
    pass


@cli.group()
def gateway():
    """Manage the websocket gateway."""
    pass


@gateway.command()
@click.option('--port', default=None, type=int, help='Gateway port (reads from config if not specified)')
@click.option('--host', default=None, help='Gateway host (reads from config if not specified)')
def start(port: int, host: str):
    """Start the websocket gateway."""
    from src.gateway import run_gateway
    
    config = ConfigManager.load_config()
    
    # Read from config, with fallback to 18789 for port
    if port is None:
        port = config.get("gateway_port", 18789)
    if host is None:
        host = config.get("gateway_host", "127.0.0.1")
    
    click.echo("🚀 Starting GirlfriendGPT Gateway")
    click.echo(f"   Companion: {config.get('name')}")
    click.echo(f"   Server: {host}:{port}")
    click.echo(f"   Model: {config.get('model')}")
    click.echo()
    
    try:
        run_gateway(port=port, host=host)
    except KeyboardInterrupt:
        click.echo("\n👋 Gateway stopped")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@gateway.command()
def stop():
    """Stop the websocket gateway."""
    state = ConfigManager.load_state()
    gateway_pid = state.get("gateway_pid")
    
    if not gateway_pid:
        click.echo("Gateway is not running")
        return
    
    import os
    import signal
    
    try:
        os.kill(gateway_pid, signal.SIGTERM)
        click.echo("✓ Gateway stopped")
        
        # Clear PID
        state.pop("gateway_pid", None)
        ConfigManager.save_state(state)
    except ProcessLookupError:
        click.echo("Gateway process not found")


@gateway.command()
def restart():
    """Restart the websocket gateway."""
    cli.invoke(Context(stop))
    asyncio.sleep(1)
    cli.invoke(Context(start))


@cli.command()
def tui():
    """Launch the terminal UI."""
    session_id = str(uuid.uuid4())
    
    try:
        import asyncio
        from src.tui import run_tui
        
        asyncio.run(run_tui(session_id))
    except ImportError:
        click.echo("Error: textual library not installed", err=True)
        click.echo("Install with: pip install textual", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('message', required=False)
@click.option('--type', 'msg_type', default='text', help='Message type')
def chat(message: Optional[str], msg_type: str):
    """Chat with the companion."""
    client = CLIClient()
    
    if message:
        # Single message mode
        asyncio.run(client.send_message(message, msg_type))
    else:
        # Interactive mode
        click.echo("\n🤖 GirlfriendGPT")
        click.echo("Type 'exit' or 'quit' to end\n")
        
        asyncio.run(client.interactive_chat())


@cli.command()
@click.argument('request')
def code(request: str):
    """Generate code."""
    client = CLIClient()
    
    prompt = f"Write code for: {request}"
    click.echo(f"\nRequest: {request}\n")
    
    asyncio.run(client.send_message(prompt, 'code_request'))


@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.argument('request')
def refactor(filepath: str, request: str):
    """Refactor code."""
    client = CLIClient()
    
    with open(filepath, 'r') as f:
        code_content = f.read()
    
    prompt = f"Refactor this code with request: {request}\n\n```\n{code_content}\n```"
    
    click.echo(f"\nRefactoring: {filepath}")
    click.echo(f"Request: {request}\n")
    
    asyncio.run(client.send_message(prompt, 'code_refactor'))


@cli.command()
@click.option('--host', default=None, help='Gateway host (reads from config if not specified)')
@click.option('--port', default=None, type=int, help='Gateway port (reads from config if not specified)')
def health(host: str, port: int):
    """Check gateway health."""
    import httpx
    
    config = ConfigManager.load_config()
    
    # Read from config, with fallback to 18789 for port
    if host is None:
        host = config.get("gateway_host", "127.0.0.1")
    if port is None:
        port = config.get("gateway_port", 18789)
    
    url = f"http://{host}:{port}/health"
    
    try:
        response = httpx.get(url, timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            click.echo(f"✓ Gateway is running")
            click.echo(f"  Companion: {data.get('name')}")
            click.echo(f"  Active sessions: {data.get('active_sessions')}")
        else:
            click.echo(f"✗ Gateway error: {response.status_code}", err=True)
    except Exception as e:
        click.echo(f"✗ Gateway is not running", err=True)
        click.echo(f"Start it with: gfgpt gateway start", err=True)


@cli.command()
def setup():
    """Run initial setup (onboarding)."""
    click.echo("\n🤖 GirlfriendGPT Setup\n")
    
    config = ConfigManager.load_config()
    
    # Companion name
    name = click.prompt(
        "Companion name",
        default=config.get("name", "Luna")
    )
    
    # Model provider
    click.echo("Model providers: 1=OpenAI")
    provider = click.prompt(
        "Model provider",
        default=config.get("model_provider", "openai")
    )
    
    # Model selection
    model = click.prompt(
        "Model (gpt-4, gpt-3.5-turbo)",
        default=config.get("model", "gpt-4")
    )
    
    # Identity
    identity = click.prompt(
        "Personality identity",
        default=config.get("identity", "A helpful AI assistant")
    )
    
    # Behavior
    behavior = click.prompt(
        "Behavior description",
        default=config.get("behavior", "Be helpful and supportive")
    )
    
    # Save
    config.update({
        "name": name,
        "model_provider": provider,
        "model": model,
        "identity": identity,
        "behavior": behavior,
    })
    
    ConfigManager.save_config(config)
    
    click.echo("\n✓ Configuration saved to ~/.gfgpt/config.json")
    click.echo("\nNext steps:")
    click.echo("  gfgpt gateway start    # Start the gateway")
    click.echo("  gfgpt tui              # Open the TUI")
    click.echo("  gfgpt chat             # Chat in CLI mode")


@cli.command(name="onboard")
def onboard():
    """Alias for ``setup`` (provides a more descriptive command)."""
    ctx = click.get_current_context()
    ctx.invoke(setup)


@cli.command()
def config():
    """Show current configuration."""
    current_config = ConfigManager.load_config()
    
    click.echo("\n🔧 Current Configuration\n")
    for key, value in current_config.items():
        if 'key' not in key.lower() or not value:
            click.echo(f"  {key}: {value}")
    
    click.echo(f"\nConfiguration file: {ConfigManager.CONFIG_FILE}")


if __name__ == '__main__':
    cli()
