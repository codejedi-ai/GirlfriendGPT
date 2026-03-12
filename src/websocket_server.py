"""Websocket server for companion agent using SmolAgent.

This module provides a websocket server for real-time bidirectional communication
with the SmolAgent, replacing the old Steamship-based websocket implementation.
"""

import json
import logging
from typing import Dict, Set
from dataclasses import dataclass, asdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Message format for websocket communication."""
    role: str  # "user" or "assistant"
    content: str
    type: str = "text"  # text, code, image, audio
    metadata: dict = None

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls(**data)


class WebsocketConnectionManager:
    """Manages websocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        """Connect a new websocket."""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
        logger.info(f"Websocket connected for session {session_id}")
    
    async def disconnect(self, session_id: str, websocket: WebSocket):
        """Disconnect a websocket."""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"Websocket disconnected for session {session_id}")
    
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
    
    async def send_personal(self, websocket: WebSocket, message: Message):
        """Send message to a specific connection."""
        try:
            await websocket.send_text(message.to_json())
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")


def create_websocket_app(agent, config: dict = None) -> FastAPI:
    """Create FastAPI app with websocket support.
    
    Args:
        agent: SmolAgent instance with a `respond` method
        config: Optional configuration dict
    
    Returns:
        FastAPI application with websocket endpoints
    """
    app = FastAPI(title="GirlfriendGPT WebSocket Server")
    
    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    manager = WebsocketConnectionManager()
    
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "ok", "type": "websocket"}
    
    @app.websocket("/ws/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str):
        """Main websocket endpoint for agent communication.
        
        Args:
            websocket: WebSocket connection
            session_id: Unique session identifier
        """
        await manager.connect(session_id, websocket)
        
        try:
            # Send initial greeting
            greeting = Message(
                role="assistant",
                content=f"Hello! I'm your companion. How can I help you today?"
            )
            await manager.send_personal(websocket, greeting)
            
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                user_message = Message.from_json(data)
                
                logger.info(f"Message from {session_id}: {user_message.content[:50]}...")
                
                # Ask SmolAgent for response
                try:
                    response_text = agent.respond(user_message.content)
                    response = Message(
                        role="assistant",
                        content=response_text,
                        type="text"
                    )
                    await manager.send_personal(websocket, response)
                except Exception as e:
                    logger.error(f"Agent error: {e}")
                    error_msg = Message(
                        role="assistant",
                        content=f"Error: {str(e)}"
                    )
                    await manager.send_personal(websocket, error_msg)
        
        except WebSocketDisconnect:
            await manager.disconnect(session_id, websocket)
        except Exception as e:
            logger.error(f"Websocket error: {e}")
            await manager.disconnect(session_id, websocket)
    
    return app
