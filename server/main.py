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

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
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
    'audio/mpeg',
    'audio/wav',
    'audio/x-wav',
    'audio/mp3'
}

# Complex task keywords that require more agents
COMPLEX_KEYWORDS = ['refactor', 'analyze', 'optimize', 'test suite', 'full test', 'entire']
SIMPLE_KEYWORDS = ['fix', 'add', 'change', 'update', 'create']


def determine_agent_count(command: str) -> int:
    """
    Intelligently determine the optimal number of agents based on command complexity.

    Args:
        command: The transcribed voice command

    Returns:
        Number of agents to use (2-5+)
    """
    command_lower = command.lower()

    # Check for complex task keywords
    if any(keyword in command_lower for keyword in COMPLEX_KEYWORDS):
        logger.info(f"Complex task detected, using 5 agents")
        return 5

    # Check for simple task keywords
    if any(keyword in command_lower for keyword in SIMPLE_KEYWORDS):
        logger.info(f"Simple task detected, using 2 agents")
        return 2

    # Default to configured default (usually 3)
    logger.info(f"Standard task detected, using {DEFAULT_AGENT_COUNT} agents")
    return DEFAULT_AGENT_COUNT


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


def execute_claude_code(command: str, agent_count: int) -> Dict[str, Any]:
    """
    Execute command via Claude Code CLI with multi-agent support.

    Args:
        command: The command to execute
        agent_count: Number of agents to use

    Returns:
        Dict with execution results
    """
    # Sanitize command - prevent command injection
    if not command or len(command) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Invalid command length"
        )

    # Determine timeout based on agent count and complexity
    timeout = 60  # Default 60s
    if agent_count >= 5:
        timeout = 120  # Complex tasks get 120s

    try:
        start_time = time.time()
        logger.info(f"Executing Claude Code with {agent_count} agents: '{command}'")

        # Build command with agent count
        # Note: Using list form prevents shell injection
        cmd = ["claude", "code", command, "--agent-count", str(agent_count)]

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
            "agent_count": agent_count,
            "execution_time": round(execution_time, 2),
            "exit_code": result.returncode
        }

    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout}s")
        return {
            "text": f"Command execution timed out after {timeout} seconds",
            "success": False,
            "agent_count": agent_count,
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
            "agent_count": agent_count,
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

        # Determine optimal agent count
        agent_count = determine_agent_count(transcription)

        # Execute command via Claude Code
        execution_result = execute_claude_code(transcription, agent_count)

        # Log command for audit trail
        logger.info(
            f"AUDIT: IP={client_ip} | Command='{transcription}' | "
            f"Agents={agent_count} | Success={execution_result['success']} | "
            f"Time={execution_result['execution_time']}s"
        )

        # Return response
        return JSONResponse(content={
            "command": transcription,
            "text": execution_result["text"],
            "success": execution_result["success"],
            "agent_count": agent_count,
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
