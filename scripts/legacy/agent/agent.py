#!/usr/bin/env python3
"""
Example: Direct Agent Usage (agent.py)

This demonstrates how to use the Intimate Companion Agent directly in Python
without going through the websocket server.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from api import GirlfriendGPT, GirlFriendGPTConfig
from steamship import Steamship, Block
from steamship.agents.schema import AgentContext


def example_direct_usage():
    """Example of using the agent directly."""
    
    print("=" * 60)
    print("Intimate Companion - Direct Agent Usage Example")
    print("=" * 60)
    print()
    
    # Create configuration
    config = GirlFriendGPTConfig(
        name="Luna",
        byline="Your AI companion for coding",
        identity="A knowledgeable and supportive AI assistant",
        behavior="Be helpful, supportive, and provide thorough explanations",
        use_gpt4=True,
        bot_token="",  # Not needed for direct usage
    )
    
    # Initialize Steamship client
    client = Steamship()
    
    # Create agent service
    service = GirlfriendGPT(client=client, config=config)
    agent = service.get_agent()
    
    print(f"Agent: {config.name}")
    print(f"Model: {'GPT-4' if config.use_gpt4 else 'GPT-3.5-turbo'}")
    print("-" * 60)
    print()
    
    # Example requests
    requests = [
        "What's a good way to structure a Python project?",
        "Write a simple REST API using FastAPI",
        "How should I handle errors in async code?",
    ]
    
    # Process each request
    for i, user_input in enumerate(requests, 1):
        print(f"Request {i}: {user_input}")
        print("-" * 40)
        
        # Create agent context
        context = AgentContext(
            messages=[Block(text=user_input)],
            emit_funcs=[
                lambda blocks, metadata: print_response(blocks, metadata)
            ]
        )
        
        # Run agent
        try:
            service.run_agent(agent, context)
        except Exception as e:
            print(f"Error: {e}")
        
        print()
    
    print("=" * 60)


def print_response(blocks, metadata):
    """Print agent response blocks."""
    for block in blocks:
        if block.is_text():
            print(f"Assistant: {block.text}")
        elif block.is_image():
            print(f"[Image: {block.id}]")
        elif block.is_audio():
            print(f"[Audio: {block.id}]")
        else:
            print(f"[{block.mime_type}: {block.id}]")


def example_code_generation():
    """Example of code generation."""
    
    print("\n" + "=" * 60)
    print("Code Generation Example")
    print("=" * 60)
    print()
    
    config = GirlFriendGPTConfig(
        name="CodeMaster",
        byline="Pro code generator",
        identity="Expert programmer",
        behavior="Generate clean, well-documented code",
        use_gpt4=True,
        bot_token="",
    )
    
    client = Steamship()
    service = GirlfriendGPT(client=client, config=config)
    agent = service.get_agent()
    
    code_requests = [
        "Python function to merge two sorted arrays",
        "JavaScript async function to fetch and parse JSON",
    ]
    
    for request in code_requests:
        print(f"Generate: {request}")
        print("-" * 40)
        
        context = AgentContext(
            messages=[Block(text=f"Write code for: {request}")],
            emit_funcs=[
                lambda blocks, metadata: print_response(blocks, metadata)
            ]
        )
        
        try:
            service.run_agent(agent, context)
        except Exception as e:
            print(f"Error: {e}")
        
        print()


if __name__ == "__main__":
    try:
        example_direct_usage()
        # Uncomment to run code generation example
        # example_code_generation()
    except KeyboardInterrupt:
        print("\n\nCancelled")
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have set STEAMSHIP_API_KEY and OPENAI_API_KEY")
