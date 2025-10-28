"""
VOXX Server - Voice eXecution eXpress
FastAPI server for processing voice commands via Claude Code CLI with multi-agent support
"""

import os
import time
import logging
import subprocess
import tempfile
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
import openai
import magic

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voxx_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="VOXX API",
    description="Voice-controlled coding assistant with multi-agent Claude Code integration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to Tailscale IPs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configuration from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAILSCALE_IP = os.getenv("TAILSCALE_IP", "100.76.158.67")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", "25"))
DEFAULT_AGENT_COUNT = int(os.getenv("DEFAULT_AGENT_COUNT", "3"))

# Validate OpenAI API key
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not found in environment variables!")
    raise ValueError("OPENAI_API_KEY must be set in .env file")

openai.api_key = OPENAI_API_KEY

# Allowed audio MIME types
ALLOWED_AUDIO_TYPES = {
    'audio/mp4',
    'audio/x-m4a',
    'audio/m4a',
    'audio/mpeg',
    'audio/wav',
    'audio/x-wav',
    'audio/mp3',
    'audio/aac',
    'audio/x-aac',
    'audio/3gpp',
    'audio/3gpp2',
    'video/mp4',  # Sometimes m4a files are detected as video/mp4
    'video/3gpp',
    'application/octet-stream'  # Fallback for some Android recordings
}

# Complex task keywords that require more agents
COMPLEX_KEYWORDS = ['refactor', 'analyze', 'optimize', 'test suite', 'full test', 'entire']
SIMPLE_KEYWORDS = ['fix', 'add', 'change', 'update', 'create']


def determine_complexity(command: str) -> str:
    """
    Determine task complexity based on command keywords.

    Args:
        command: The transcribed voice command

    Returns:
        Complexity level: 'simple', 'standard', or 'complex'
    """
    command_lower = command.lower()

    # Check for complex task keywords
    if any(keyword in command_lower for keyword in COMPLEX_KEYWORDS):
        logger.info(f"Complex task detected")
        return 'complex'

    # Check for simple task keywords
    if any(keyword in command_lower for keyword in SIMPLE_KEYWORDS):
        logger.info(f"Simple task detected")
        return 'simple'

    # Default to standard
    logger.info(f"Standard task detected")
    return 'standard'


def validate_audio_file(file: UploadFile) -> bool:
    """
    Validate audio file type and size with magic bytes check.

    Args:
        file: The uploaded file

    Returns:
        True if valid, raises HTTPException otherwise
    """
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Seek back to beginning

    max_size_bytes = MAX_AUDIO_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_AUDIO_SIZE_MB}MB"
        )

    # Read file header for magic bytes check
    file_header = file.file.read(2048)
    file.file.seek(0)

    # Use python-magic for MIME type detection
    mime = magic.from_buffer(file_header, mime=True)

    if mime not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Invalid audio format. Allowed: m4a, mp3, wav. Detected: {mime}"
        )

    logger.info(f"Audio file validated: {mime}, {file_size} bytes")
    return True


def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribe audio file using OpenAI Whisper API.

    Args:
        audio_file_path: Path to the audio file

    Returns:
        Transcribed text
    """
    try:
        logger.info("Sending audio to OpenAI Whisper API...")

        with open(audio_file_path, 'rb') as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )

        logger.info(f"Transcription successful: '{transcript}'")
        return transcript.strip()

    except Exception as e:
        logger.error(f"Whisper API error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Speech-to-text failed: {str(e)}"
        )


def execute_claude_code(command: str, complexity: str) -> Dict[str, Any]:
    """
    Execute command via Claude Code CLI.

    Args:
        command: The command to execute
        complexity: Task complexity level (simple, standard, complex)

    Returns:
        Dict with execution results
    """
    # Sanitize command - prevent command injection
    if not command or len(command) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Invalid command length"
        )

    # Determine timeout based on complexity
    timeout_map = {
        'simple': 60,
        'standard': 90,
        'complex': 120
    }
    timeout = timeout_map.get(complexity, 90)

    try:
        start_time = time.time()
        logger.info(f"Executing Claude Code ({complexity} task): '{command}'")

        # Build command - using -p for print mode (non-interactive)
        # Note: Using list form prevents shell injection
        # Format: claude [prompt] -p
        cmd = ["claude", command, "-p"]

        # Execute subprocess with timeout and no shell
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False  # Don't raise exception on non-zero exit
        )

        execution_time = time.time() - start_time

        # Check if execution was successful
        success = result.returncode == 0

        # Combine stdout and stderr for complete output
        output = result.stdout if result.stdout else result.stderr

        if not output:
            output = "Command executed successfully" if success else "Command failed with no output"

        logger.info(f"Claude Code execution completed in {execution_time:.2f}s (exit code: {result.returncode})")

        return {
            "text": output,
            "success": success,
            "complexity": complexity,
            "execution_time": round(execution_time, 2),
            "exit_code": result.returncode
        }

    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout}s")
        return {
            "text": f"Command execution timed out after {timeout} seconds",
            "success": False,
            "complexity": complexity,
            "execution_time": timeout,
            "exit_code": -1
        }

    except FileNotFoundError:
        logger.error("Claude Code CLI not found in PATH")
        raise HTTPException(
            status_code=500,
            detail="Claude Code CLI not installed or not in PATH"
        )

    except Exception as e:
        logger.error(f"Claude Code execution error: {str(e)}")
        return {
            "text": f"Execution error: {str(e)}",
            "success": False,
            "complexity": complexity,
            "execution_time": 0,
            "exit_code": -1
        }


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "VOXX API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for streaming voice command processing.
    Provides real-time status updates and streaming responses.
    """
    await websocket.accept()
    client_ip = websocket.client.host
    logger.info(f"WebSocket connected from {client_ip}")

    temp_file_path = None

    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "Ready to receive audio"
        })

        # Receive audio data
        await websocket.send_json({
            "type": "status",
            "message": "Receiving audio..."
        })

        audio_data = await websocket.receive_bytes()
        logger.info(f"Received {len(audio_data)} bytes of audio")

        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(audio_data)

        # Transcribe audio
        await websocket.send_json({
            "type": "status",
            "message": "Transcribing audio with Whisper..."
        })

        try:
            transcription = transcribe_audio(temp_file_path)
            logger.info(f"Transcription: '{transcription}'")

            await websocket.send_json({
                "type": "transcription",
                "text": transcription
            })

        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            await websocket.send_json({
                "type": "error",
                "message": f"Transcription failed: {str(e)}"
            })
            return

        # Determine complexity
        complexity = determine_complexity(transcription)
        await websocket.send_json({
            "type": "complexity",
            "level": complexity
        })

        await websocket.send_json({
            "type": "status",
            "message": f"Executing ({complexity} task)..."
        })

        # Execute Claude with streaming
        start_time = time.time()
        cmd = ["claude", transcription, "-p", "--output-format=stream-json"]

        timeout_map = {'simple': 60, 'standard': 90, 'complex': 120}
        timeout = timeout_map.get(complexity, 90)

        logger.info(f"Executing: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        full_response = ""

        try:
            # Stream output line by line with timeout
            import select
            poll = select.poll()
            poll.register(process.stdout, select.POLLIN)

            timeout_ms = timeout * 1000
            start_poll = time.time()

            while True:
                # Check for timeout
                if time.time() - start_poll > timeout:
                    process.kill()
                    raise subprocess.TimeoutExpired(cmd, timeout)

                # Poll for data with 1 second timeout
                if poll.poll(1000):
                    line = process.stdout.readline()
                    if not line:
                        break

                    # Stream the chunk
                    full_response += line
                    await websocket.send_json({
                        "type": "response_chunk",
                        "text": line.rstrip('\n')
                    })

            # Wait for process to complete
            process.wait(timeout=5)

            execution_time = time.time() - start_time
            success = process.returncode == 0

            logger.info(f"Claude execution completed in {execution_time:.2f}s (exit code: {process.returncode})")

            # Log command for audit trail
            logger.info(
                f"AUDIT: IP={client_ip} | Command='{transcription}' | "
                f"Complexity={complexity} | Success={success} | "
                f"Time={execution_time:.2f}s"
            )

            # Send completion
            await websocket.send_json({
                "type": "complete",
                "success": success,
                "complexity": complexity,
                "execution_time": round(execution_time, 2),
                "timestamp": datetime.utcnow().isoformat()
            })

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s")
            await websocket.send_json({
                "type": "error",
                "message": f"Command timed out after {timeout} seconds"
            })
            process.kill()

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected from {client_ip}")

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Server error: {str(e)}"
            })
        except:
            pass

    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Temporary file deleted: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")

        try:
            await websocket.close()
        except:
            pass


@app.post("/voice")
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute
async def process_voice_command(request: Request, audio: UploadFile = File(...)):
    """
    Process voice command: transcribe audio and execute via Claude Code CLI.

    Args:
        request: FastAPI request object (for rate limiting)
        audio: Uploaded audio file (m4a, mp3, or wav)

    Returns:
        JSON response with transcription, execution result, and metrics
    """
    client_ip = request.client.host
    logger.info(f"Received voice command from {client_ip}")

    # Validate Tailscale IP (optional - uncomment to enforce)
    # if not client_ip.startswith("100."):
    #     logger.warning(f"Rejected non-Tailscale IP: {client_ip}")
    #     raise HTTPException(status_code=403, detail="Only Tailscale connections allowed")

    temp_file_path = None

    try:
        # Validate audio file
        validate_audio_file(audio)

        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as temp_file:
            temp_file_path = temp_file.name
            content = await audio.read()
            temp_file.write(content)

        logger.info(f"Audio saved to temporary file: {temp_file_path}")

        # Transcribe audio using Whisper
        transcription = transcribe_audio(temp_file_path)

        if not transcription:
            raise HTTPException(
                status_code=400,
                detail="No speech detected in audio"
            )

        # Determine task complexity
        complexity = determine_complexity(transcription)

        # Execute command via Claude Code
        execution_result = execute_claude_code(transcription, complexity)

        # Log command for audit trail
        logger.info(
            f"AUDIT: IP={client_ip} | Command='{transcription}' | "
            f"Complexity={complexity} | Success={execution_result['success']} | "
            f"Time={execution_result['execution_time']}s"
        )

        # Return response
        return JSONResponse(content={
            "command": transcription,
            "text": execution_result["text"],
            "success": execution_result["success"],
            "complexity": complexity,
            "execution_time": execution_result["execution_time"],
            "timestamp": datetime.utcnow().isoformat()
        })

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Unexpected error processing voice command: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Temporary file deleted: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")


if __name__ == "__main__":
    import uvicorn

    logger.info("=" * 60)
    logger.info("  VOXX Server - Voice eXecution eXpress")
    logger.info("=" * 60)
    logger.info(f"  Listening on: 0.0.0.0:{SERVER_PORT}")
    logger.info(f"  Tailscale IP: {TAILSCALE_IP}")
    logger.info(f"  Default Agent Count: {DEFAULT_AGENT_COUNT}")
    logger.info(f"  Max Audio Size: {MAX_AUDIO_SIZE_MB}MB")
    logger.info(f"  Rate Limit: 10 requests/minute")
    logger.info("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=SERVER_PORT,
        log_level="info"
    )
