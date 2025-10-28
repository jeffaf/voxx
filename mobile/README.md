# VOXX Mobile App

Expo/React Native mobile application for voice-controlled coding.

## Features

- Voice recording with expo-av (HIGH_QUALITY preset)
- Real-time visual feedback during recording
- OpenAI Whisper transcription display
- Claude Code response display
- Multi-agent execution metrics (agent count, execution time)
- Text-to-speech response playback
- Command history (last 10 commands)
- Connection status indicator
- Retry mechanism (up to 3 attempts)
- Permission handling

## Prerequisites

- Node.js 18+
- Expo CLI
- Android phone with Expo Go app installed
- Tailscale running on both phone and dev machine

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Server URL

Edit `App.js` and update the server URL if needed:

```javascript
const SERVER_URL = 'http://100.76.158.67:8000';
```

Replace `100.76.158.67` with your dev machine's Tailscale IP.

### 3. Start Development Server

```bash
npm start
```

This will:
- Start Expo dev server
- Display QR code in terminal
- Open Metro bundler in browser

### 4. Run on Android

1. Install [Expo Go](https://play.google.com/store/apps/details?id=host.exp.exponent) on your Android phone
2. Ensure phone is connected to Tailscale
3. Scan QR code from terminal using Expo Go app
4. App will build and launch

## Usage

1. **Grant Permissions**: On first launch, grant microphone permission
2. **Check Connection**: Look for green status dot (top-right)
3. **Record Command**:
   - Press and hold the big red button
   - Speak your command
   - Release button when done
4. **View Results**:
   - See transcription
   - View agent count and execution time
   - Read Claude's response
   - Response plays via text-to-speech automatically
5. **Review History**: Scroll down to see recent commands

## Configuration

### Server URL

Change in `App.js`:
```javascript
const SERVER_URL = 'http://YOUR_TAILSCALE_IP:8000';
```

### History Limit

Adjust max history items:
```javascript
const MAX_HISTORY_ITEMS = 10;  // Change to desired limit
```

## Connection Status

- 🟢 **Green**: Connected to server
- 🟡 **Yellow**: Server responded but with issues
- 🔴 **Red**: Cannot connect to server

## Troubleshooting

### Microphone Permission Denied

```
Settings → Apps → Expo Go → Permissions → Microphone → Allow
```

### Cannot Connect to Server

1. Check Tailscale is running on phone: `Settings → VPN`
2. Verify server is running: Open browser on phone, navigate to `http://100.76.158.67:8000`
3. Check Tailscale IP: Run `tailscale ip -4` on dev machine
4. Ensure phone and dev machine are on same Tailscale network

### Audio Not Recording

- Ensure microphone permission granted
- Try restarting Expo Go app
- Check phone is not in silent mode

### App Crashes on Launch

```bash
# Clear cache and restart
npm start -- --clear
```

### Response Not Playing

- Check phone volume
- Ensure phone not in Do Not Disturb mode
- Try manually unmuting phone

## Development

### Running in Development Mode

```bash
npm start
```

### Building for Production

```bash
# Build APK
expo build:android
```

Note: Production builds require Expo account and additional configuration.

## Dependencies

- **expo**: Core Expo SDK
- **expo-av**: Audio recording
- **expo-speech**: Text-to-speech
- **expo-status-bar**: Status bar styling
- **react**: React library
- **react-native**: React Native framework

## UI Components

- **Header**: Logo, subtitle, connection status
- **Transcription Card**: Displays voice command
- **Metrics Row**: Agent count and execution time
- **Response Card**: Claude's response
- **History Section**: Recent commands
- **Record Button**: Press-and-hold to record
- **Processing Indicator**: Shows loading state

## Permissions

The app requires:
- **RECORD_AUDIO**: For voice recording
- **INTERNET**: For server communication

These are declared in `app.json` and requested at runtime.

## License

MIT License - see [LICENSE](../LICENSE) for details.
