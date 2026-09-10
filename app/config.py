import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "PulseDispatch - Voice-Native Emergency Incident Copilot"
    VERSION: str = "1.0.0"
    
    # Rime Configuration
    RIME_API_KEY: str = os.getenv("RIME_API_KEY", "")
    RIME_API_URL: str = os.getenv("RIME_API_URL", "https://users.rime.ai/v1/rime-tts")
    RIME_MODEL_ID: str = os.getenv("RIME_MODEL_ID", "mist")  # 'mist' (fastest/streaming), 'arcana', 'aura'
    RIME_SPEAKER: str = os.getenv("RIME_SPEAKER", "cora")      # 'cora', 'marsh', 'allison', 'amber', 'creed'
    RIME_LANGUAGE: str = os.getenv("RIME_LANGUAGE", "en")
    RIME_AUDIO_FORMAT: str = os.getenv("RIME_AUDIO_FORMAT", "mp3") # 'mp3', 'pcm', 'wav'
    RIME_SAMPLING_RATE: int = int(os.getenv("RIME_SAMPLING_RATE", "22050"))
    RIME_SPEED_ALPHA: float = float(os.getenv("RIME_SPEED_ALPHA", "1.0"))
    RIME_TIMEOUT_SEC: float = float(os.getenv("RIME_TIMEOUT_SEC", "10.0"))
    
    # LLM Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Telemetry and Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT") or "8080")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

settings = Settings()
