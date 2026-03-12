# GirlfriendGPT → Intimate Companion 

**An OpenClaw-style AI companion framework for engineers.** Your personal code-writing, intimate AI assistant with websocket support and CLI integration.

This is an enhanced version of GirlfriendGPT that adds professional websocket support, CLI tools for code generation, and code refactoring capabilities.

## 🚀 New Features (v2.0)

* **Websocket Server**: Direct real-time communication with your AI companion (no Telegram required)
* **CLI Tool**: Command-line interface for code generation and refactoring
* **Code Generation**: Write production-ready code with natural language
* **Code Refactoring**: Ask the companion to optimize and improve your code
* **Personality System**: Fully customizable companion with unique voice and behavior
* **Multi-interface**: Use via websocket, CLI, Telegram, or web UI

## Features

* **Custom Voice**: Utilize ElevenLabs to create a unique voice for your AI companion
* **Websocket API**: Direct bidirectional communication (like OpenClaw)
* **CLI Tool**: Generate and refactor code from the command line
* **Telegram Integration**: Also supports direct Telegram bot interface
* **Personality**: Fully customizable AI personality, name, and behavior
* **Selfies**: AI can generate selfies when requested
* **Video Messages**: Create video responses from your companion

## Getting Started

### Quick Start with Websocket

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the websocket server
python run_websocket.py --name "Luna" --port 8000

# 3. In another terminal, use the CLI
companion chat          # Interactive chat
companion code "Python function for fibonacci"  # Generate code
companion ask "How do I structure a Python project?"  # Ask questions
```

### Setup CLI Tool

```bash
# Install CLI globally
python setup_cli.py

# Then use from anywhere
companion chat
companion code "Your code request here"
companion refactor myfile.py "optimize for performance"
```

### Traditional Steamship Deploy

To deploy your companion & connect it to Telegram:

```bash
pip install -r requirements.txt
pip install steamship
ship serve remote
```

You will need to fetch a Telegram key to connect your companion to Telegram. [This guide](/docs/register-telegram-bot.md) will show you how.

## CLI Commands

```bash
# Interactive chat
companion chat

# Generate code
companion code "FastAPI REST API with database models"
companion code "Python async web scraper"

# Refactor existing code  
companion refactor myfile.py "add error handling and type hints"

# Ask questions
companion ask --message "Best practices for Python projects?"

# Check server health
companion health --server ws://localhost:8000
```

## Architecture

**Framework**: Steamship (LLM agent framework)

**LLM**: GPT-4 or GPT-3.5-turbo (configurable)

**Transport**: Websocket (with Telegram optional)

**Tools**:
- CodeGenerationTool - Write code
- CodeRefactoringTool - Improve code
- SearchTool - Web search
- SelfieTool - Generate selfies
- VideoMessageTool - Create videos
- GenerateSpeechTool - Voice synthesis

## Advanced Usage

See [WEBSOCKET_CLI_GUIDE.md](WEBSOCKET_CLI_GUIDE.md) for detailed documentation on:
- Websocket API integration
- Custom personality configuration
- Voice synthesis setup
- Code generation best practices
- Deployment options

## Configuration

Set environment variables:

```bash
export STEAMSHIP_API_KEY="your-steamship-key"
export OPENAI_API_KEY="your-openai-key"
export ELEVENLABS_API_KEY="your-elevenlabs-key"  # optional
export ELEVENLABS_VOICE_ID="your-voice-id"       # optional
```

## Roadmap
* Long-term memory for context awareness
* Photorealistic selfies
* Voice cloning
* Custom training per user
* Multi-user sessions
* Persistent conversation history

## Technical Notes

This project is built on **Steamship**, an AI framework for building agents with tools, memory, and multiple interfaces.

Unlike the original Telegram-only version, this enhanced version adds:
- Websocket transport for real-time communication
- CLI-first interaction pattern  
- Professional code generation tooling
- Direct API access without Telegram middleware

## Contributing
Pull requests welcome! Areas for contribution:

<details>
  <summary>👀 Add a personality!</summary>
  <br>
Do you have a unique personality in mind for our AI model, GirlfriendGPT? Great! Here's a step-by-step guide on how to add it.

## Step 1: Define Your Personality
First, you'll need to define your personality. This is done by creating a new Python file in the src/personalities directory.

For example, if your personality is named "jane", you would create a file called `jane.json`. Inside this file, you would define the characteristics and behaviors that embody "jane". This could include her speaking style, responses to certain inputs, or any other defining features you envision.

## Step 2: Test and Submit

Before you submit your new personality, please test it to ensure everything works as expected. If all is well, submit a Pull Request with your changes, and be sure to include the title "{name} - {description}" where {name} is your personality's name, and {description} is a brief explanation of the personality.

Good luck, and we can't wait to meet your new GirlfriendGPT personality!
</details>





## License
This project is licensed under the MIT License. 
