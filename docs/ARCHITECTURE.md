# Architecture Guide - Intimate Companion

This document explains the architecture of the Intimate Companion Agent system and how it enables websocket-based code generation and assistance.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  Intimate Companion System                   │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
                ▼           ▼           ▼
          ┌─────────┐ ┌──────────┐ ┌─────────┐
          │Websocket│ │ Telegram │ │ Web UI  │
          │ Server  │ │Transport │ │(Optional)│
          └────┬────┘ └─────┬────┘ └────┬────┘
               │            │           │
               └────────────┼───────────┘
                            │
                      ┌─────▼──────┐
                      │Agent Service│
                      │ (Steamship) │
                      └─────┬──────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
                ▼           ▼           ▼
           ┌─────────┐ ┌──────────┐ ┌────────┐
           │FunctionsBase         │ │SearchTool
           │Agent    │ │CodeGen   │ │        │
           │         │ │Tools     │ │        │
           └─────────┘ └──────────┘ └────────┘
                │
                ▼
           ┌──────────┐
           │ OpenAI   │
           │ GPT-4 or │
           │GPT-3.5   │
           └──────────┘
```

## Key Components

### 1. Websocket Server (`src/websocket_server.py`)

The websocket server provides real-time bidirectional communication without requiring a third-party service like Telegram.

**Advantages over Telegram:**
- No external dependency on Telegram infrastructure
- Real-time message streaming
- Lower latency (direct connection)
- Supports structured message types
- Can handle code blocks efficiently
- Persistent session management

**Key Classes:**

```python
class Message:
    """Message format for websocket exchange"""
    role: str          # "user" or "assistant"
    content: str       # Message text or code
    type: str          # "text", "code", "image", "audio"
    metadata: dict     # Optional metadata

class WebsocketConnectionManager:
    """Manages multiple concurrent connections"""
    async def connect(session_id, websocket)
    async def disconnect(session_id, websocket)
    async def broadcast(session_id, message)
    async def send_personal(websocket, message)
```

**Flow:**

```
Client connects to ws://host:port/ws/{session_id}
         │
         ▼
Server sends greeting message
         │
         ▼
Client sends user message (JSON)
         │
         ▼
Server creates AgentContext
         │
         ▼
Agent processes request (LLM)
         │
         ▼
Agent emits response blocks
         │
         ▼
Server broadcasts to client
         │
         ▼
Connection remains open for next message
```

### 2. CLI Tool (`cli.py`)

Command-line interface for interacting with the websocket server.

**Commands:**
- `companion chat` - Interactive conversation
- `companion code <request>` - Generate code
- `companion refactor <file> <request>` - Refactor code
- `companion ask --message <q>` - Ask questions
- `companion health` - Check server status

**Implementation:**

```python
class CompanionCLI:
    async def send_message(content, type) -> str
    async def code_generation(request) -> str
    async def code_refactoring(code, request) -> str
```

Session management using `~/.companion/session.json` allows persistent conversations.

### 3. Code Generation Tools (`src/tools/code_generation.py`)

Custom tools for generating and refactoring code.

**Tools:**

```python
class CodeGenerationTool(Tool):
    """Generates code from natural language descriptions"""
    
class CodeRefactoringTool(Tool):
    """Refactors and optimizes existing code"""
```

These tools work by:
1. Taking user input
2. Creating a specialized prompt for the LLM
3. Returning the prompt for the agent to process
4. The agent's LLM generates the code response

### 4. Agent Service (`src/api.py`)

Core service based on Steamship's `AgentService` and `FunctionsBasedAgent`.

**Key Features:**
- Integrates all tools (Search, Code Gen, Selfies, Video, Speech)
- Formats system prompts with personality config
- Manages audio generation for responses
- Supports multiple transports (Websocket, Telegram, Web)

**Tool List:**
```python
tools=[
    SearchTool(),                    # Web search
    SelfieTool(),                    # Generate images
    VideoMessageTool(client),        # Generate videos
    CodeGenerationTool(),            # Write code
    CodeRefactoringTool(),           # Improve code
]
```

## Data Flow - Code Generation

```
1. User Input
   └─► "Write a Python function to sort"
   
2. CLI Sends to Websocket
   └─► JSON: {"role": "user", "content": "...", "type": "code_request"}
   
3. Server Creates AgentContext
   └─► messages=[Block(text="...")]
       emit_funcs=[lambda blocks, metadata: ...]
   
4. service.run_agent(agent, context)
   └─► agent._llm.run(FunctionCall)
       └─► Request to OpenAI
           {"messages": [{"role": "system", "content": "You are... use CodeGenerationTool"},
                         {"role": "user", "content": "Write..."}]}
   
5. LLM Response
   └─► Calls CodeGenerationTool with user request
       └─► Tool returns formatted prompt
           └─► LLM generates code
   
6. Agent Emits Response
   └─► context.emit_funcs([Block(text="```python\n..."), Metadata()])
   
7. Emit Wrapper
   └─► If voice enabled: Generate audio
       └─► Broadcast to client
   
8. Client Receives
   └─► JSON: {"role": "assistant", "content": "```python\n...", "type": "text"}
```

## Session Management

Sessions maintain context across requests:

```
~/.companion/session.json
{
    "session_id": "uuid",
    "messages": [
        {"role": "assistant", "content": "..."},
        {"role": "user", "content": "..."},
        ...
    ]
}
```

This allows:
- Resuming conversations
- Maintaining context
- Persisting history
- Multi-turn interactions

## Comparison with OpenClaw

### Similarities:
- ✅ Websocket-based real-time communication
- ✅ Code generation and refactoring
- ✅ CLI interface
- ✅ Direct agent interaction (no middleware)
- ✅ Session persistence

### Key Differences:

| Feature | OpenClaw | Intimate Companion |
|---------|----------|-------------------|
| Framework | Custom | Steamship (LLM framework) |
| Transport | WebSocket only | WebSocket + Telegram + Web |
| Agent Type | RAG-based | FunctionsBasedAgent |
| Code Tools | Cursor-style | CodeGen + CodeRefactor |
| Voice | Optional | Full ElevenLabs support |
| Personality | N/A | Fully customizable |
| Deployment | Self-hosted | Steamship + Self-hosted |

## Extensibility

### Adding New Tools

```python
class MyCustomTool(Tool):
    name: str = "MyCustomTool"
    human_description: str = "..."
    agent_description: str = "..."
    
    def run(self, tool_input: List[Block], context: AgentContext):
        # Process input
        return [Block(text="response")]

# Add to agent
agent._agent.tools.append(MyCustomTool())
```

### Custom Personalities

```python
config = GirlFriendGPTConfig(
    name="DevAssistant",
    byline="Your code writing companion",
    identity="Expert software engineer",
    behavior="Write scalable, efficient code",
)
```

### Custom Transports

Steamship supports adding custom transports:

```python
service.add_mixin(CustomTransport(
    client=client,
    agent_service=service,
    agent=agent
))
```

## Performance Characteristics

### Latency
- WebSocket connection: <100ms
- LLM request (GPT-4): 2-10s
- Code generation: 5-30s
- Total per request: 5-40s (depending on code length)

### Scalability
- Concurrent connections: Limited by server resources
- Sessions: Each session is independent
- Websocket manager: Supports 1000+ connections per instance

### Resource Usage
- Memory per session: ~10KB
- Memory per concurrent connection: ~5MB
- Total: Roughly O(n*5MB) for n connections

## Security Considerations

### Current Implementation
- No authentication (internal use)
- All server URLs default to localhost
- Session IDs are UUIDs (not guessable)

### For Production:
- Add OAuth/token-based authentication
- Use WSS (WebSocket Secure) with SSL/TLS
- Implement rate limiting
- Add request validation
- Use environment variables for secrets

## Deployment Options

### Local Development
```bash
python run_websocket.py --port 8000
```

### Docker
```dockerfile
FROM python:3.14
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "run_websocket.py", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes
Deploy as a service with:
- StatefulSet for persistent sessions
- Service for load balancing
- Ingress for TLS/SSL
- HPA for auto-scaling

### Steamship Cloud
Deploy directly via Steamship:
```bash
ship serve remote
```

## Future Enhancements

1. **Long-term Memory** - Persistent conversation history with RAG
2. **Multi-user Sessions** - Shared companion for teams
3. **Code Execution** - Safe code execution and testing
4. **IDE Integration** - VS Code extension
5. **Advanced Refactoring** - AST-based code analysis
6. **Voice Streaming** - Real-time voice interaction
7. **Context Awareness** - Project structure understanding
8. **Custom Models** - Fine-tuning on user code patterns

## References

- [Steamship Documentation](https://docs.steamship.com)
- [OpenAI API](https://platform.openai.com/docs)
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
- [Python WebSockets](https://websockets.readthedocs.io/)
