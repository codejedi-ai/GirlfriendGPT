#!/usr/bin/env python3
"""
Example websocket client for Intimate Companion Agent (websocket.py).

This demonstrates how to programmatically connect to the websocket server
and interact with the companion agent.
"""

import asyncio
import json
import websockets
import uuid
from pathlib import Path
from typing import Optional


class IntimateCompanionClient:
    """Websocket client for the Intimate Companion Agent."""
    
    def __init__(self, server_url: str = "ws://localhost:8000", session_id: Optional[str] = None):
        """Initialize the client.
        
        Args:
            server_url: URL of the websocket server
            session_id: Optional session ID (generates new one if not provided)
        """
        self.server_url = server_url
        self.session_id = session_id or str(uuid.uuid4())
        self.messages = []
    
    async def send_message(self, content: str, message_type: str = "text") -> str:
        """Send a message to the companion and get response.
        
        Args:
            content: The message content
            message_type: Type of message (text, code_request, etc.)
            
        Returns:
            The companion's response text
        """
        uri = f"{self.server_url}/ws/{self.session_id}"
        response_text = ""
        
        async with websockets.connect(uri) as websocket:
            # Receive greeting
            greeting_data = await websocket.recv()
            greeting = json.loads(greeting_data)
            print(f"[{greeting['role']}] {greeting['content']}\n")
            self.messages.append(greeting)
            
            # Send user message
            user_msg = {
                "role": "user",
                "content": content,
                "type": message_type,
                "metadata": None
            }
            await websocket.send(json.dumps(user_msg))
            self.messages.append(user_msg)
            print(f"[user] {content}\n")
            
            # Receive responses
            try:
                while True:
                    response_data = await asyncio.wait_for(
                        websocket.recv(), 
                        timeout=60.0  # 60 second timeout
                    )
                    response = json.loads(response_data)
                    print(f"[{response['role']}] {response['content']}\n")
                    self.messages.append(response)
                    response_text += response['content']
            except asyncio.TimeoutError:
                print("[connection] Server response timeout")
            except websockets.exceptions.ConnectionClosed:
                print("[connection] Connection closed")
        
        return response_text
    
    async def code_generation(self, request: str) -> str:
        """Ask the companion to generate code.
        
        Args:
            request: Description of the code to generate
            
        Returns:
            Generated code
        """
        prompt = f"Write code for: {request}"
        return await self.send_message(prompt, message_type="code_request")
    
    async def code_refactoring(self, code: str, request: str) -> str:
        """Ask the companion to refactor code.
        
        Args:
            code: The code to refactor
            request: Refactoring request/description
            
        Returns:
            Refactored code
        """
        prompt = f"Please refactor this code with request: {request}\n\n```\n{code}\n```"
        return await self.send_message(prompt, message_type="code_refactor")
    
    def save_session(self):
        """Save session to file."""
        session_file = Path.home() / ".companion" / f"session_{self.session_id}.json"
        session_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(session_file, 'w') as f:
            json.dump({
                "session_id": self.session_id,
                "messages": self.messages
            }, f, indent=2)
        
        print(f"Session saved to {session_file}")
    
    def get_conversation(self) -> str:
        """Get the full conversation history.
        
        Returns:
            Formatted conversation string
        """
        conv = []
        for msg in self.messages:
            conv.append(f"{msg['role'].upper()}: {msg['content']}")
        return "\n\n".join(conv)


async def main():
    """Example usage of the client."""
    
    print("=" * 60)
    print("Intimate Companion - Websocket Client Example")
    print("=" * 60)
    print()
    
    # Create client
    client = IntimateCompanionClient()
    print(f"Connected with session ID: {client.session_id}\n")
    
    # Example 1: Simple chat
    print("--- Example 1: Chat ---")
    await client.send_message("Hello! Can you help me learn Python?")
    print()
    
    # Example 2: Code generation
    print("--- Example 2: Code Generation ---")
    await client.code_generation("Python function to calculate factorial")
    print()
    
    # Example 3: Code refactoring
    print("--- Example 3: Code Refactoring ---")
    sample_code = """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

def divide(a, b):
    return a / b
"""
    await client.code_refactoring(sample_code, "add type hints and docstrings")
    print()
    
    # Save conversation
    client.save_session()
    print("\n" + "=" * 60)
    print("Conversation Transcript")
    print("=" * 60)
    print(client.get_conversation())


if __name__ == "__main__":
    # Run the example
    # Make sure the websocket server is running first!
    # python run_websocket.py
    
    try:
        asyncio.run(main())
    except ConnectionRefusedError:
        print("Error: Could not connect to websocket server")
        print("Make sure the server is running: python run_websocket.py")
    except KeyboardInterrupt:
        print("\nCancelled")
