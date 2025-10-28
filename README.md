```
██╗   ██╗ ██████╗ ██╗  ██╗██╗  ██╗
██║   ██║██╔═══██╗╚██╗██╔╝╚██╗██╔╝
██║   ██║██║   ██║ ╚███╔╝  ╚███╔╝
╚██╗ ██╔╝██║   ██║ ██╔██╗  ██╔██╗
 ╚████╔╝ ╚██████╔╝██╔╝ ██╗██╔╝ ██╗
  ╚═══╝   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝

    Voice eXecution eXpress
```

# VOXX - Voice eXecution eXpress

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![Expo](https://img.shields.io/badge/Expo-SDK%2053-000020.svg?style=flat&logo=expo)](https://expo.dev/)
[![Tailscale](https://img.shields.io/badge/Tailscale-Secured-blue.svg)](https://tailscale.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-Whisper-412991.svg)](https://openai.com/research/whisper)

> **Voice-controlled coding assistant for remote development over Tailscale**

Code at the speed of thought. Control your development environment with your voice, from anywhere.

## 🚀 Features

- **🎯 Multi-Agent Execution**: Intelligently parallelizes work with Claude Code's multi-agent system (2-5+ agents)
- **🎤 Voice-First Coding**: Speak commands naturally, get results instantly via OpenAI Whisper
- **🔒 Secure by Design**: All traffic over Tailscale VPN - zero public internet exposure
- **⚡ Claude Code Integration**: Full integration with Claude Code CLI for AI-powered development
- **📱 Mobile-Native**: Beautiful Expo app for Android with intuitive UI
- **🔊 Real-Time Feedback**: Hear responses with text-to-speech, see execution metrics
- **📊 Performance Metrics**: Real-time agent count, execution time, and command history
- **🛡️ Zero-Trust Architecture**: Input validation, rate limiting, audit logging

## 💡 Why Multi-Agent?

Traditional voice assistants execute commands sequentially. VOXX leverages Claude Code's multi-agent system to parallelize work:

- **Simple tasks** (fix, add, change): 2 agents → ~40% faster
- **Standard tasks** (default): 3 agents → ~60% faster
- **Complex tasks** (refactor, analyze, test suite): 5+ agents → ~80% faster

Example: "Refactor the auth module and update tests" runs multiple agents in parallel - one refactoring code, another updating tests, others analyzing dependencies.

## 💰 Cost Breakdown

**OpenAI Whisper API Pricing**: $0.006 per minute of audio

| Usage Pattern | Monthly Cost |
|--------------|--------------|
| Light (30 min/day) | ~$5.40 |
| Moderate (2 hrs/day) | ~$21.60 |
| Heavy (5 hrs/day) | ~$54.00 |

**Typical voice command**: 5-10 seconds = $0.0005-0.001 per command

Add $5-10 to your OpenAI account for ~1,000+ commands. Way cheaper than typing on a phone keyboard.

## 🏗️ Architecture

```
┌─────────────────────┐                         ┌──────────────────────┐
│   Android Device    │◄────── Tailscale ──────►│   Dev Machine        │
│   (Expo/React)      │    100.76.158.67:8000   │   (FastAPI Server)   │
└──────────┬──────────┘                         └──────────┬───────────┘
           │                                               │
           │ 1. Voice Recording (expo-av)                  │
           │ 2. Upload Audio (m4a/wav/mp3)                 │
           │                                               ▼
           │                                    ┌─────────────────────┐
           │                                    │  OpenAI Whisper API │
           │                                    │  (Speech-to-Text)   │
           │                                    └──────────┬──────────┘
           │                                               │
           │                                               ▼
           │                                    ┌─────────────────────┐
           │                                    │   Command Parser    │
           │                                    │ (Determine Agents)  │
           │                                    └──────────┬──────────┘
           │                                               │
           │                                               ▼
           │                                    ┌─────────────────────┐
           │                                    │  Claude Code CLI    │
           │                                    │  --agent-count N    │
           │                                    └──────────┬──────────┘
           │                                               │
           │                                          ┌────┴────┐
           │                                          ▼    ▼    ▼
           │                                       Agent1 Agent2 Agent3
           │                                          │    │    │
           │ 6. Display Results                  └────┴────┴────┘
           │ 7. TTS Playback                               │
           │◄──────────────────────────────────────────────┘
           │ 5. Return JSON (text, success, agent_count, time)
           │
```

## ⚡ Quick Start

### Prerequisites

- ✅ Python 3.10+ with pip
- ✅ Node.js 18+ with npm
- ✅ Tailscale installed and authenticated
- ✅ OpenAI API key with credits ([get one here](https://platform.openai.com/api-keys))
- ✅ Claude Code CLI installed
- ✅ Android phone with Expo Go app

### Installation

```bash
# Clone the repository
git clone https://github.com/jeffaf/voxx.git
cd voxx

# Set up the server
cd server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key: OPENAI_API_KEY=sk-...

# Start the server (on your dev machine)
python main.py
# Server will listen on 0.0.0.0:8000

# In a new terminal, set up mobile app
cd ../mobile
npm install

# Start the Expo dev server
npm start
# Scan QR code with Expo Go app on Android
```

See [docs/SETUP.md](docs/SETUP.md) for detailed setup instructions and troubleshooting.

## 📱 Usage

1. **Open VOXX** on your Android device
2. **Tap and hold** the big red record button
3. **Speak your command**:
   - "Check the git status"
   - "Create a new React component called UserProfile"
   - "Refactor the authentication module and add tests"
4. **Release** the button
5. **Watch the magic**: See transcription → agent count → execution time
6. **Hear and read** Claude's response with TTS

### Example Commands

```bash
# Simple tasks (2 agents)
"Fix the linting errors in auth.py"
"Add a debug log statement here"

# Standard tasks (3 agents - default)
"Check git status and show me unstaged changes"
"Create a new Express endpoint for user login"

# Complex tasks (5+ agents)
"Refactor the entire auth module for better security"
"Run the full test suite and analyze failures"
"Optimize database queries and update documentation"
```

The system automatically determines the optimal agent count based on command complexity!

## 🔒 Security Features

VOXX was built with security as a first-class citizen:

| Feature | Implementation |
|---------|---------------|
| **Network Isolation** | Tailscale VPN only - no public internet exposure |
| **Input Sanitization** | Whitelist approach for claude code commands |
| **Audio Validation** | Magic bytes check, file type validation, 25MB size limit |
| **Rate Limiting** | 10 requests/min per client IP |
| **Command Injection** | Subprocess with strict argument passing, no shell=True |
| **Audit Logging** | All commands logged with timestamps, agent count, source IP |
| **Timeout Protection** | 60s default, 120s for complex tasks, prevents hangs |
| **Zero Secrets** | All credentials in .env, never committed |
| **IP Validation** | Optional Tailscale IP range validation (100.x.x.x) |

**⚠️ SECURITY WARNING**: This tool gives voice commands direct access to your terminal via Claude Code CLI.

- ✅ **DO**: Use only over Tailscale VPN
- ✅ **DO**: Keep your OpenAI API key secret
- ✅ **DO**: Review command logs regularly
- ❌ **DON'T**: Expose FastAPI server to public internet
- ❌ **DON'T**: Share your Tailscale network with untrusted devices
- ❌ **DON'T**: Use in production environments

This is a development tool for personal use over secure networks.

## 📂 Project Structure

```
voxx/
├── README.md                 # You are here
├── LICENSE                   # MIT License
├── .gitignore               # Comprehensive ignore rules
│
├── server/                   # FastAPI backend
│   ├── main.py              # Core server with multi-agent logic
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment template
│   ├── .env                 # Your secrets (gitignored!)
│   └── README.md            # Server documentation
│
├── mobile/                   # Expo mobile app
│   ├── App.js               # Main application UI
│   ├── package.json         # Node dependencies
│   ├── app.json             # Expo configuration
│   ├── .gitignore           # Mobile-specific ignores
│   └── README.md            # Mobile documentation
│
├── docs/                     # Documentation
│   ├── SETUP.md             # Detailed setup guide
│   └── ARCHITECTURE.md      # Technical deep dive
│
└── .github/
    └── workflows/
        └── lint.yml          # CI/CD linting
```

## 🎯 Roadmap

Current features marked ✅, planned features marked 🔜:

- ✅ Voice input via OpenAI Whisper
- ✅ Multi-agent Claude Code execution
- ✅ Intelligent agent count selection
- ✅ TTS responses
- ✅ Command history
- ✅ Execution metrics
- ✅ Tailscale security
- 🔜 Wake word detection ("Hey VOXX")
- 🔜 Continuous listening mode
- 🔜 Command macros/shortcuts
- 🔜 Streaming responses for long outputs
- 🔜 iOS support
- 🔜 Local Whisper fallback (no API cost)
- 🔜 Voice biometric authentication
- 🔜 Multi-language support

## 🤝 Contributing

Contributions welcome! This is an open-source project built for the community.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/awesome-feature`)
3. Commit your changes (`git commit -m 'Add awesome feature'`)
4. Push to the branch (`git push origin feature/awesome-feature`)
5. Open a Pull Request

**Please ensure:**
- Code follows existing style
- Security best practices maintained
- Tests pass (when we add them!)
- Documentation updated
- No secrets or API keys committed

## 🐛 Troubleshooting

### Can't connect to server
- Verify Tailscale is running on both Android and dev machine
- Check server is running: `curl http://100.76.158.67:8000/`
- Confirm Tailscale IP with: `tailscale ip -4`

### Audio recording fails
- Grant microphone permissions in Android Settings → Apps → Expo Go
- Check audio format compatibility (m4a, wav, mp3)

### Commands timeout
- Check Claude Code CLI: `claude code --version`
- Verify OpenAI API key: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`
- Check server logs for detailed error messages
- Try reducing agent count for simpler tasks

### Agent execution fails
- Ensure Claude Code CLI is in PATH
- Try running manually: `claude code "check git status" --agent-count 3`
- Check logs in server console for agent orchestration errors

More troubleshooting in [docs/SETUP.md](docs/SETUP.md).

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Built with** [Claude Code](https://claude.ai/code) - AI-powered coding assistant
- **Powered by** [OpenAI Whisper](https://openai.com/research/whisper) - Speech recognition
- **Secured by** [Tailscale](https://tailscale.com/) - Zero-trust VPN
- **Mobile framework** [Expo](https://expo.dev/) - React Native made easy
- **Backend** [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework

**Found this useful? Star the repo!** ⭐

---

<p align="center">
<strong>⚠️ Security Notice</strong><br>
This tool executes commands on your development machine via voice.<br>
Use responsibly and only over secure networks. Not intended for production environments.
</p>
