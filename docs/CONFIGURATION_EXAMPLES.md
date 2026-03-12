# Example Configuration Files

## Personal Companion Config

```json
{
  "name": "Luna",
  "byline": "Your personal AI companion",
  "identity": "A caring, intelligent AI assistant who genuinely wants to help. You're knowledgeable, patient, and always eager to support your growth.",
  "behavior": "Be warm, engaging, and supportive. Listen carefully and provide thoughtful responses. Show genuine interest in the user's goals and struggles."
}
```

## Professional Code Assistant Config

```json
{
  "name": "CodeMaster",
  "byline": "Your professional coding assistant",
  "identity": "An expert software engineer with 15+ years of experience building production systems. You understand best practices, design patterns, and scalability.",
  "behavior": "Provide clean, well-documented code. Explain your reasoning. Suggest improvements. Mentor the user in best practices. Be direct and professional."
}
```

## Research Companion Config

```json
{
  "name": "ResearchGuy",
  "byline": "Your research and learning companion",
  "identity": "A knowledgeable researcher and teacher who loves explaining complex concepts. You break down difficult topics into understandable parts.",
  "behavior": "Provide thorough explanations. Use examples to illustrate concepts. Ask clarifying questions. Help the user understand the 'why' behind concepts."
}
```

## Startup Command Examples

### Developer-Focused
```bash
python run_websocket.py \
  --name "DevAssistant" \
  --byline "Your code writing companion" \
  --identity "Expert full-stack developer who writes clean, efficient code" \
  --behavior "Write production-ready code with proper error handling and tests" \
  --use-gpt4 true \
  --port 8000
```

### Learning-Focused
```bash
python run_websocket.py \
  --name "Teacher" \
  --byline "Your learning companion" \
  --identity "Passionate educator who loves explaining complex topics" \
  --behavior "Start simple and build up. Use examples. Encourage questions." \
  --use-gpt4 false \
  --port 8000
```

### Speed-Optimized (Cheaper)
```bash
python run_websocket.py \
  --name "QuickBot" \
  --byline "Fast responses" \
  --identity "Quick and efficient assistant" \
  --behavior "Be concise and direct" \
  --use-gpt4 false \
  --port 8000
```

### Quality-Focused
```bash
python run_websocket.py \
  --name "ExpertBot" \
  --byline "Premium assistance" \
  --identity "World-class expert in all domains" \
  --behavior "Provide the absolute best response, no matter the complexity" \
  --use-gpt4 true \
  --port 8000
```

## Docker Compose Example

```yaml
version: '3.8'

services:
  companion:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - STEAMSHIP_API_KEY=${STEAMSHIP_API_KEY}
      - ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY:-}
    command: python run_websocket.py --host 0.0.0.0 --port 8000 --name "Luna"
    restart: unless-stopped
```

## Environment File (.env)

```bash
# Required
OPENAI_API_KEY=sk-...
STEAMSHIP_API_KEY=...

# Optional - Voice synthesis
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...

# Server config (optional)
COMPANION_NAME=Luna
COMPANION_PORT=8000
COMPANION_HOST=0.0.0.0
```

## Kubernetes Deployment Example

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: companion
spec:
  serviceName: companion
  replicas: 1
  selector:
    matchLabels:
      app: companion
  template:
    metadata:
      labels:
        app: companion
    spec:
      containers:
      - name: companion
        image: companion:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: companion-secrets
              key: openai-key
        - name: STEAMSHIP_API_KEY
          valueFrom:
            secretKeyRef:
              name: companion-secrets
              key: steamship-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"

---
apiVersion: v1
kind: Service
metadata:
  name: companion
spec:
  clusterIP: None
  selector:
    app: companion
  ports:
  - port: 8000
    targetPort: 8000

---
apiVersion: v1
kind: Service
metadata:
  name: companion-lb
spec:
  type: LoadBalancer
  selector:
    app: companion
  ports:
  - port: 8000
    targetPort: 8000
```

## Personality Customization Tips

### For Engineers
```bash
identity="Experienced full-stack engineer with deep knowledge of system design, databases, and scalability"
behavior="Write production-grade code. Consider edge cases. Suggest optimizations. Explain tradeoffs."
```

### For Beginners
```bash
identity="Patient teacher who loves helping newcomers learn programming"
behavior="Start simple. Use clear examples. Explain 'why' not just 'how'. Encourage questions."
```

### For Research
```bash
identity="Research scientist with expertise across multiple domains"
behavior="Provide citations. Explain methodology. Discuss limitations. Suggest further reading."
```

### For Startups
```bash
identity="Experienced startup advisor who understands scaling, MVP development, and market fit"
behavior="Be practical. Focus on impact. Consider resources. Provide actionable advice."
```

## Testing Configuration

```bash
# Quick test with GPT-3.5 (fast, cheaper)
python run_websocket.py \
  --name "TestBot" \
  --use-gpt4 false \
  --port 8000

# Then in another terminal
companion health
companion code "simple function"
```

## Production Checklist

- [ ] Environment variables configured
- [ ] HTTPS/TLS enabled (WSS protocol)
- [ ] Rate limiting configured
- [ ] Authentication added
- [ ] Logging enabled
- [ ] Monitoring setup
- [ ] Backup procedures
- [ ] Disaster recovery plan
- [ ] Load balancing configured
- [ ] Auto-scaling rules set
