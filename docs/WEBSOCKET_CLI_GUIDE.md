# Intimate Companion - Websocket & CLI Guide

This document describes how to use the Intimate Companion Agent with websocket connections and the CLI tool.

## Overview

Intimate Companion is an advanced AI agent framework designed for engineers. It combines:

- **Websocket Server**: Real-time bidirectional communication for direct chat
- **CLI Tool**: Command-line interface for code generation and refactoring
- **Code Generation**: Write code using natural language descriptions
- **Personality Framework**: Customize your AI companion's behavior and voice

Unlike the original Telegram-only version, this version allows direct interaction through websockets, similar to OpenClaw's architecture.

## Architecture

```
┌─────────────────────────────────────────────────┐
│   Intimate Companion Agent (FunctionsBasedAgent)│
│   - GPT-4 or GPT-3.5-turbo LLM                  │
│   - Tools: Search, Code Gen, Selfies, Video    │
└─────────────────────────────────────────────────┘
         ▲                     ▲
         │                     │
    ┌────┴────┐          ┌─────┴─────┐
    │WebSocket│          │  Telegram  │
    │ Server  │          │ Transport  │
    └────┬────┘          └─────┬─────┘
         │                     │
    ┌────┴────┐          ┌─────┴─────┐
    │CLI Tool │          │Telegram   │
    │& Chat   │          │Bot        │
    └─────────┘          └───────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Make sure you have:
- `STEAMSHIP_API_KEY` environment variable set
- `OPENAI_API_KEY` environment variable set for GPT models
- (Optional) `ELEVENLABS_API_KEY` for voice synthesis

### 2. Start the Websocket Server

```bash
python run_websocket.py --name "Your Companion Name" --port 8000
```

Options:
- `--host` (default: 0.0.0.0) - Server host
- `--port` (default: 8000) - Server port
- `--name` - Companion's name
- `--byline` - Short description
- `--identity` - Personality definition
- `--behavior` - How it should behave
- `--use-gpt4` (default: true) - Use GPT-4 instead of GPT-3.5

### 3. Use the CLI Tool

## CLI Commands

### Chat Interactively

```bash
companion chat
```

Starts an interactive conversation with your companion.

```
🤖 Intimate Companion - Interactive Chat
Type 'exit' or 'quit' to end the session

You: Hello, how are you?
Companion: I'm doing great! How can I help you today?

You: Can you help me write a Python function?
Companion: Of course! I'd be happy to help with Python code. What would you like the function to do?
```

### Generate Code

```bash
companion code "Write a Python function to calculate fibonacci numbers"
```

The companion will generate complete, production-ready code with:
- Proper documentation and docstrings
- Error handling
- Type hints
- Clear formatting

Example output:
```
You: Write a Python function to calculate fibonacci numbers

Companion: Here's a well-documented fibonacci function:

```python
def fibonacci(n: int) -> List[int]:
    """
    Generate fibonacci sequence up to n numbers.
    
    Args:
        n: Number of fibonacci numbers to generate
        
    Returns:
        List of fibonacci numbers
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    
    if n == 0:
        return []
    if n == 1:
        return [0]
    
    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[i-1] + sequence[i-2])
    
    return sequence
```
```

### Refactor Code

```bash
companion refactor myfile.py "optimize for performance and add type hints"
```

Reads the file and asks the companion to refactor it with your requirements.

Input: `myfile.py`
```python
def slow_func(data):
    result = []
    for item in data:
        if item > 5:
            result.append(item * 2)
    return result
```

Output from companion:
```
Here's the optimized refactored version:

```python
from typing import List

def process_data(data: List[int]) -> List[int]:
    """
    Filter and transform data efficiently using list comprehension.
    
    Args:
        data: Input list of integers
        
    Returns:
        Filtered and doubled integers (values > 5 only)
    """
    return [item * 2 for item in data if item > 5]
```

Key improvements:
1. Used list comprehension for better performance
2. Added type hints for clarity
3. Added docstring for documentation
4. Renamed function to be more descriptive
```

### Ask Questions

```bash
companion ask --message "What's the best way to structure a Python project?"
```

Ask the companion any technical question.

### Check Server Health

```bash
companion health --server ws://localhost:8000
```

Verify the server is running.

### Other Options

```bash
# Set custom server URL
companion --server ws://api.example.com:8000 chat

# Show version
companion version

# Get help
companion --help
companion code --help
```

## Session Management

The CLI automatically manages sessions:

- Session ID is stored in `~/.companion/session.json`
- Allows resuming conversations across CLI invocations
- Each session maintains context with the companion

## API Integration

### Direct API Usage

You can also interact programmatically:

```python
from src.api import GirlfriendGPT, GirlFriendGPTConfig
from steamship import Steamship

# Configure
config = GirlFriendGPTConfig(
    name="Luna",
    byline="Your AI companion",
    identity="A helpful and supportive AI",
    behavior="Be warm and engaging",
)

# Initialize
client = Steamship()
service = GirlfriendGPT(client=client, config=config)

# Start websocket server
service.start_websocket_server(host="0.0.0.0", port=8000)
```

### Websocket Message Format

Messages are JSON formatted:

```json
{
    "role": "user",
    "content": "Write a Python function for sorting",
    "type": "text",
    "metadata": null
}
```

Response:
```json
{
    "role": "assistant",
    "content": "Here's a sorting function...",
    "type": "text",
    "metadata": null
}
```

## Tools Available

1. **SearchTool** - Search the web for information
2. **CodeGenerationTool** - Write and generate code
3. **CodeRefactoringTool** - Optimize and refactor code
4. **SelfieTool** - Generate selfies (requires Stable Diffusion)
5. **VideoMessageTool** - Create video messages (requires D-ID)
6. **GenerateSpeechTool** - Generate audio (requires ElevenLabs)

## Environment Variables

```bash
# Required
export STEAMSHIP_API_KEY="your-steamship-key"
export OPENAI_API_KEY="your-openai-key"

# Optional
export ELEVENLABS_API_KEY="your-elevenlabs-key"
export ELEVENLABS_VOICE_ID="your-voice-id"
```

## Examples

### Developer Flow

```bash
# 1. Start the server
python run_websocket.py --name "DevCompanion"

# 2. In another terminal, interact
companion chat

# User: I need a REST API in FastAPI
# Companion: [generates complete FastAPI code]

# 3. Refactor if needed
companion refactor api.py "add better error handling"

# 4. Get help
companion ask --message "How should I structure this project?"
```

### Code Generation Workflow

```bash
companion code "FastAPI server with database models and CRUD operations"
companion code "Unit tests for the API endpoints"
companion refactor main.py "use async/await patterns"
```

## Troubleshooting

### Server won't start

```bash
# Check if port is in use
lsof -i :8000

# Try different port
python run_websocket.py --port 8001
```

### Can't connect CLI to server

```bash
# Check server is running
companion health

# Check with custom URL
companion --server ws://your-server:8000 health
```

### Session management issues

```bash
# Clear session
rm ~/.companion/session.json

# Will create new session on next run
companion chat
```

## Performance Notes

- GPT-4 provides better code quality but is slower and more expensive
- GPT-3.5-turbo is faster and cheaper, good for testing
- Use `--use-gpt4=False` for faster responses during development

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please submit pull requests to enhance:
- New tools
- UI improvements
- Code generation capabilities
- Documentation
