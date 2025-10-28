# VOXX Server

FastAPI backend for VOXX voice-controlled coding assistant.

## Features

- OpenAI Whisper API integration for speech-to-text
- Multi-agent Claude Code CLI execution
- Intelligent agent count selection based on task complexity
- Rate limiting (10 requests/minute per client)
- Audio file validation with magic bytes checking
- Comprehensive audit logging
- Timeout protection
- Security-first design

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-...
TAILSCALE_IP=100.76.158.67
SERVER_PORT=8000
MAX_AUDIO_SIZE_MB=25
DEFAULT_AGENT_COUNT=3
```

### 4. Verify Claude Code CLI

Ensure Claude Code is installed and in your PATH:

```bash
claude code --version
```

### 5. Start Server

```bash
python main.py
```

Server will listen on `0.0.0.0:8000` (accessible via Tailscale).

## API Endpoints

### `GET /`

Health check endpoint.

**Response:**
```json
{
  "status": "online",
  "service": "VOXX API",
  "version": "1.0.0",
  "timestamp": "2025-10-27T12:00:00"
}
```

### `POST /voice`

Process voice command.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Audio file (m4a, mp3, or wav)
- Max size: 25MB
- Rate limit: 10 requests/minute

**Response:**
```json
{
  "command": "check git status",
  "text": "On branch main...",
  "success": true,
  "agent_count": 3,
  "execution_time": 2.45,
  "timestamp": "2025-10-27T12:00:00"
}
```

## Multi-Agent Logic

The server intelligently determines the number of Claude Code agents based on command complexity:

| Task Type | Agent Count | Detection Keywords |
|-----------|-------------|-------------------|
| Simple | 2 | fix, add, change, update, create |
| Standard | 3 | (default) |
| Complex | 5 | refactor, analyze, optimize, test suite, entire |

## Security Features

- **Input Validation**: Audio files validated with magic bytes
- **Rate Limiting**: 10 requests/minute per client IP
- **Command Injection Prevention**: No `shell=True`, strict argument passing
- **Timeout Protection**: 60s default, 120s for complex tasks
- **Audit Logging**: All commands logged with timestamps, agent count, source IP
- **File Size Limits**: 25MB maximum audio upload
- **Tailscale-Only** (optional): Uncomment IP validation in code

## Logging

Logs are written to:
- **Console**: Real-time output
- **File**: `voxx_server.log`

Log format:
```
2025-10-27 12:00:00 - AUDIT: IP=100.76.158.67 | Command='check git status' | Agents=3 | Success=True | Time=2.45s
```

## Troubleshooting

### OpenAI API Errors

```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Claude Code Not Found

```bash
# Check if in PATH
which claude

# Add to PATH if needed
export PATH="$PATH:/path/to/claude"
```

### Rate Limit Exceeded

Wait 60 seconds between bursts of requests. Rate limit: 10 requests/minute.

### Timeout Errors

Increase timeout in `main.py`:
```python
timeout = 120  # Increase for very complex tasks
```

## Development

### Running in Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py
```

### Testing Endpoints

```bash
# Health check
curl http://localhost:8000/

# Test voice endpoint (requires audio file)
curl -X POST http://localhost:8000/voice \
  -F "audio=@test.m4a"
```

## Dependencies

- **FastAPI**: Modern Python web framework
- **Uvicorn**: ASGI server
- **OpenAI**: Python client for Whisper API
- **slowapi**: Rate limiting middleware
- **python-magic**: File type detection
- **python-dotenv**: Environment variable management

## License

MIT License - see [LICENSE](../LICENSE) file for details.
