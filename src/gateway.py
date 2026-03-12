"""
Gateway service for GirlfriendGPT - AI Companion Agent.

The gateway provides:
- Websocket server for client connections
- Service management (start/stop/restart)
- Configuration management
- Client routing
- Session persistence
"""

import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Dict, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from api import Agent, Config
from config import ConfigManager


logger = logging.getLogger(__name__)
CONFIG_DIR = Path.home() / ".gfgpt"


@dataclass
class Message:
    """Message format for websocket communication."""
    role: str  # "user" or "assistant"
    content: str
    type: str = "text"  # text, code, image, audio
    timestamp: str = None
    metadata: dict = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls(**data)


class GatewayConnectionManager:
    """Manages websocket connections and routes messages through the agent."""
    
    def __init__(self, agent_service):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.agent_service = agent_service
    
    async def connect(self, session_id: str, websocket: WebSocket):
        """Connect a new websocket."""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
        logger.info(f"Client connected: {session_id}")
    
    async def disconnect(self, session_id: str, websocket: WebSocket):
        """Disconnect a websocket."""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"Client disconnected: {session_id}")
    
    async def broadcast(self, session_id: str, message: Message):
        """Send message to all connections in a session."""
        if session_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_text(message.to_json())
                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.active_connections[session_id].discard(conn)


class GatewayService:
    """Wrapper for agent service with gateway functionality."""
    
    def __init__(self, agent_service, config: dict):
        self.agent_service = agent_service
        self.config = config
        self.manager = None
    
    def create_app(self) -> FastAPI:
        """Create FastAPI app with gateway endpoints."""
        app = FastAPI(title="GirlfriendGPT Gateway")
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.manager = GatewayConnectionManager(self.agent_service)
        
        @app.get("/health")
        async def health():
            """Health check."""
            return {
                "status": "ok",
                "name": self.config.get("name", "Unknown"),
                "active_sessions": len(self.manager.active_connections)
            }
        
        @app.get("/info")
        async def info():
            """Get gateway info."""
            return {
                "gateway": "GirlfriendGPT",
                "version": "1.0.0",
                "companion_name": self.config.get("name"),
                "model": "GPT-4" if self.config.get("use_gpt4") else "GPT-3.5-turbo",
                "active_sessions": len(self.manager.active_connections)
            }
        
        @app.websocket("/ws/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, session_id: str):
            """Main gateway websocket endpoint."""
            await self.manager.connect(session_id, websocket)

            try:
                # Send greeting
                greeting = Message(
                    role="assistant",
                    content=f"Hello! I'm {self.config.get('name', 'your companion')}. How can I help?"
                )
                await self.manager.broadcast(session_id, greeting)

                while True:
                    try:
                        data = await asyncio.wait_for(websocket.receive_text(), timeout=300.0)
                        user_message = Message.from_json(data)

                        logger.info(f"Message from {session_id}: {user_message.content[:100]}")

                        # Process through agent
                        await self._process_through_agent(session_id, user_message)

                    except asyncio.TimeoutError:
                        # Send keepalive ping
                        try:
                            await websocket.send_text(json.dumps({"role": "system", "content": "", "type": "ping"}))
                        except:
                            break
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON received: {e}")
                        error_msg = Message(role="system", content="Invalid message format")
                        await self.manager.broadcast(session_id, error_msg)

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {session_id}")
                await self.manager.disconnect(session_id, websocket)
            except Exception as e:
                logger.error(f"Websocket error: {e}")
                await self.manager.disconnect(session_id, websocket)
    
        return app
    
    async def _process_through_agent(self, session_id: str, message: Message):
        """Ask the SmolAgent for a response and broadcast it."""
        try:
            # the agent_service is now a SmolAgent instance with a `respond` method
            resp_text = self.agent_service.respond(message.content)
            response = Message(role="assistant", content=resp_text, type="text")
            await self.manager.broadcast(session_id, response)
        except Exception as e:
            logger.error(f"Agent error: {e}")
            error_msg = Message(
                role="assistant",
                content=f"Error processing request: {str(e)}"
            )
            await self.manager.broadcast(session_id, error_msg)


def run_gateway(port: int = 18789, host: str = "127.0.0.1"):
    """Run the gateway service."""
    
    # Load configuration (creates defaults if needed)
    config = ConfigManager.load_config()
    
    # Ensure config file is saved
    ConfigManager.save_config(config)
    
    # Extract OpenAI config
    openai_config = config.get("model_provider", {}).get("openai", {})
    api_key = openai_config.get("api_key") or os.environ.get("OPENAI_API_KEY")
    model = openai_config.get("model", "gpt-4")
    
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set. Model may not respond correctly.")
        logger.warning("OPENAI_API_KEY not configured")
    
    print(f"🚀 Starting GirlfriendGPT Gateway")
    print(f"   Companion: {config.get('name')}")
    print(f"   Server: {host}:{port}")
    print(f"   Model: {model}")
    print()
    
    logger.info(f"Starting GirlfriendGPT Gateway")
    logger.info(f"Companion: {config.get('name')}")
    logger.info(f"Server: {host}:{port}")
    
    # Build configuration object for the agent
    agent_config = Config(
        name=config.get("name", "Companion"),
        byline=config.get("byline", "AI Companion"),
        identity=config.get("identity", "A helpful AI assistant"),
        behavior=config.get("behavior", "Be helpful and supportive"),
        use_gpt4=(model == "gpt-4"),
        elevenlabs_api_key=config.get("elevenlabs_api_key", ""),
        elevenlabs_voice_id=config.get("elevenlabs_voice_id", ""),
    )
    
    # instantiate the lightweight SmolAgent with OpenAI API key
    agent_service = Agent(agent_config)
    print(f"✅ Model initialized: {agent_config.model}")
    
    # Create gateway
    gateway = GatewayService(agent_service, config)
    app = gateway.create_app()
    
    # Run server
    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    except KeyboardInterrupt:
        logger.info("Gateway shutting down...")


def run_gateway_main():
    """Entry point for gateway."""
    
    config = ConfigManager.load_config()
    
    try:
        run_gateway(
            port=config.get("gateway_port", 8000),
            host=config.get("gateway_host", "127.0.0.1")
        )
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
