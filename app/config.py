import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "small")
    AUDIO_TEMP_DIR: str = os.getenv("AUDIO_TEMP_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "audio_temp"))

    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1500"))
    LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "90"))
    OLLAMA_KEEP_ALIVE: str = os.getenv("OLLAMA_KEEP_ALIVE", "15m")
    WARMUP_RAG: bool = os.getenv("WARMUP_RAG", "true").lower() == "true"
    WARMUP_SPEECH: bool = os.getenv("WARMUP_SPEECH", "false").lower() == "true"

    # "anthropic", "gemini", or "ollama"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "anthropic")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

settings = Settings()
os.makedirs(settings.AUDIO_TEMP_DIR, exist_ok=True)