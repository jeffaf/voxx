# VOXX Setup Guide

Complete setup guide for VOXX - Voice eXecution eXpress.

## Table of Contents

- [Prerequisites](#prerequisites)
- [OpenAI API Setup](#openai-api-setup)
- [Tailscale Setup](#tailscale-setup)
- [Claude Code CLI Setup](#claude-code-cli-setup)
- [Server Setup](#server-setup)
- [Mobile App Setup](#mobile-app-setup)
- [First Run](#first-run)
- [Multi-Agent Configuration](#multi-agent-configuration)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have:

- ✅ **Python 3.10+** with pip ([Download](https://www.python.org/downloads/))
- ✅ **Node.js 18+** with npm ([Download](https://nodejs.org/))
- ✅ **Tailscale** installed and authenticated
- ✅ **OpenAI API key** with credits
- ✅ **Claude Code CLI** installed
- ✅ **Android phone** with Expo Go app
- ✅ **Git** (for cloning repository)

### Verify Prerequisites

```bash
# Check Python version
python --version  # Should be 3.10 or higher

# Check Node version
node --version    # Should be 18 or higher

# Check Tailscale
tailscale status  # Should show "logged in"

# Check Claude Code
claude code --version
```

## OpenAI API Setup

### 1. Create OpenAI Account

1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up or log in
3. Verify your email address

### 2. Add Credits to Account

1. Navigate to [Settings → Billing](https://platform.openai.com/account/billing)
2. Click "Add payment method"
3. Add a credit/debit card
4. Purchase credits:
   - **Minimum**: $5 (covers ~1,000 commands)
   - **Recommended**: $10 (covers ~2,000 commands)
   - **Heavy use**: $20+ (covers 4,000+ commands)

### 3. Generate API Key

1. Go to [API Keys](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Name it: `VOXX-Server`
4. Copy the key (starts with `sk-...`)
5. **Save it securely** - you won't see it again!

### 4. Test API Key

```bash
# Test your API key works
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-YOUR_API_KEY_HERE"

# Should return a JSON list of available models
```

### OpenAI Pricing

- **Whisper API**: $0.006 per minute of audio
- **Typical command**: 5-10 seconds = $0.0005-0.001
- **$5 credit**: ~1,000 voice commands
- **$10 credit**: ~2,000 voice commands

See [OpenAI Pricing](https://openai.com/pricing) for details.

## Tailscale Setup

### 1. Install Tailscale

**macOS:**
```bash
brew install tailscale
```

**Linux:**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

**Windows:**
Download from [tailscale.com/download](https://tailscale.com/download)

### 2. Authenticate Tailscale

```bash
sudo tailscale up
```

Follow the link to authenticate in your browser.

### 3. Get Your Tailscale IP

```bash
tailscale ip -4
```

Example output: `100.76.158.67`

**Save this IP** - you'll need it for configuration.

### 4. Install Tailscale on Android

1. Install [Tailscale from Google Play](https://play.google.com/store/apps/details?id=com.tailscale.ipn)
2. Open app and log in with same account
3. Enable VPN connection
4. Verify: Your phone should now see your dev machine's IP

## Claude Code CLI Setup

### 1. Install Claude Code

Follow instructions at [claude.ai/code](https://claude.ai/code) to install the Claude Code CLI.

### 2. Verify Installation

```bash
claude code --version
```

### 3. Test Claude Code

```bash
# Test basic command
claude code "echo hello world"

# Test with agents
claude code "echo hello" --agent-count 2
```

If commands fail, ensure Claude Code is in your PATH.

## Server Setup

### 1. Clone Repository

```bash
git clone https://github.com/jeffaf/voxx.git
cd voxx
```

### 2. Navigate to Server Directory

```bash
cd server
```

### 3. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: If `python-magic` fails on macOS, install libmagic:
```bash
brew install libmagic
pip install python-magic
```

### 5. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```bash
OPENAI_API_KEY=sk-YOUR_KEY_HERE
TAILSCALE_IP=100.76.158.67  # Your Tailscale IP
SERVER_PORT=8000
MAX_AUDIO_SIZE_MB=25
DEFAULT_AGENT_COUNT=3
```

### 6. Test Server

```bash
python main.py
```

You should see:
```
============================================================
  VOXX Server - Voice eXecution eXpress
============================================================
  Listening on: 0.0.0.0:8000
  Tailscale IP: 100.76.158.67
  Default Agent Count: 3
  Max Audio Size: 25MB
  Rate Limit: 10 requests/minute
============================================================
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 7. Verify Server

In another terminal:
```bash
# Test from dev machine
curl http://localhost:8000

# Test from Tailscale IP (should work from anywhere on Tailscale network)
curl http://100.76.158.67:8000
```

Expected response:
```json
{
  "status": "online",
  "service": "VOXX API",
  "version": "1.0.0",
  "timestamp": "2025-10-27T12:00:00"
}
```

## Mobile App Setup

### 1. Install Expo Go on Android

Install from [Google Play Store](https://play.google.com/store/apps/details?id=host.exp.exponent).

### 2. Navigate to Mobile Directory

```bash
cd ../mobile
```

### 3. Install Dependencies

```bash
npm install
```

### 4. Configure Server URL

Edit `App.js` (line ~15):
```javascript
const SERVER_URL = 'http://100.76.158.67:8000';  // Update with your Tailscale IP
```

### 5. Start Expo Dev Server

```bash
npm start
```

You should see:
- QR code in terminal
- Metro bundler opens in browser

### 6. Connect Android Device

1. Ensure phone is on Tailscale VPN
2. Open Expo Go app on Android
3. Scan QR code from terminal
4. App builds and launches

### 7. Grant Permissions

On first launch:
1. Tap "Allow" for microphone permission
2. Connection status dot should turn green

## First Run

### Test the Complete Flow

1. **Start Server** (on dev machine):
   ```bash
   cd voxx/server
   source venv/bin/activate
   python main.py
   ```

2. **Start Mobile App**:
   ```bash
   cd voxx/mobile
   npm start
   # Scan QR code with Expo Go
   ```

3. **Record First Command**:
   - Press and hold red button
   - Say: "Check git status"
   - Release button
   - Watch transcription appear
   - See agent count (should be 3)
   - Hear response via TTS

4. **Verify Logs**:
   - Check server terminal for audit log
   - Should show: `AUDIT: IP=... | Command='check git status' | Agents=3 | Success=True | Time=2.5s`

## Multi-Agent Configuration

### Default Agent Counts

Edit `server/.env`:
```bash
DEFAULT_AGENT_COUNT=3  # Standard tasks
```

### Agent Selection Logic

The server automatically adjusts agent count based on command keywords:

| Keyword | Agent Count | Example Commands |
|---------|-------------|------------------|
| fix, add, change | 2 | "Fix the linting error" |
| (default) | 3 | "Create a new component" |
| refactor, analyze, optimize | 5 | "Refactor auth module" |

### Manual Override

To force a specific agent count, modify `determine_agent_count()` in `server/main.py`.

### Performance Tips

- **Simple tasks**: Reduce to 2 agents for faster execution
- **Complex tasks**: Increase to 5+ agents for parallel work
- **Debugging**: Use 1 agent for easier debugging

## Troubleshooting

### Server Won't Start

**Error: `OPENAI_API_KEY not found`**
```bash
# Verify .env file exists
ls server/.env

# Check contents
cat server/.env | grep OPENAI_API_KEY

# Ensure no trailing spaces or quotes
```

**Error: `ModuleNotFoundError: No module named 'fastapi'`**
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Error: `Address already in use`**
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>
```

### Mobile App Won't Connect

**Connection status is red**
```bash
# 1. Verify Tailscale on phone
#    Settings → VPN → Tailscale should be ON

# 2. Test server from phone browser
#    Open: http://100.76.158.67:8000
#    Should see JSON response

# 3. Verify server is running
ps aux | grep "python main.py"

# 4. Check firewall (macOS)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

**Microphone permission denied**
```
Android Settings → Apps → Expo Go → Permissions → Microphone → Allow
```

### Audio Issues

**No transcription returned**
- Speak clearly and louder
- Reduce background noise
- Try shorter commands (<30 seconds)
- Check OpenAI API credits

**Audio upload fails**
- Check file size (max 25MB)
- Verify internet connection
- Check server logs for errors

### Claude Code Issues

**Error: `claude: command not found`**
```bash
# Check if Claude Code is installed
which claude

# If not in PATH, add it
export PATH="$PATH:/path/to/claude"

# Make permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export PATH="$PATH:/path/to/claude"' >> ~/.bashrc
source ~/.bashrc
```

**Commands timeout**
```bash
# Increase timeout in server/main.py
timeout = 120  # Line ~200

# Or reduce agent count for faster execution
DEFAULT_AGENT_COUNT=2
```

### OpenAI API Errors

**Error: `Invalid API key`**
```bash
# Test API key manually
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# If fails, regenerate key at platform.openai.com/api-keys
```

**Error: `Insufficient credits`**
- Add more credits at [platform.openai.com/account/billing](https://platform.openai.com/account/billing)
- Check usage at [platform.openai.com/usage](https://platform.openai.com/usage)

**Rate limit exceeded**
- OpenAI Whisper has rate limits
- Wait 60 seconds and retry
- Consider upgrading OpenAI account tier

### Expo/React Native Issues

**Metro bundler won't start**
```bash
# Clear cache
npm start -- --clear

# Or manually
rm -rf node_modules .expo
npm install
npm start
```

**App crashes on launch**
```bash
# Check Expo Go app version (should be latest)
# Update via Google Play Store

# Check Node version
node --version  # Should be 18+
```

## Support

If you're still stuck:

1. Check [GitHub Issues](https://github.com/jeffaf/voxx/issues)
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
3. Enable debug logging in `server/main.py`:
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

## Next Steps

Once setup is complete:

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for technical deep dive
- Explore multi-agent configurations
- Customize agent count logic
- Build custom command shortcuts
- Contribute improvements!

---

**Happy Coding! 🎤💻**
