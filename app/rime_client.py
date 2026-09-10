"""
Rime Neural Text-to-Speech Streaming Client.
Integrates with Rime's low-latency streaming endpoints (mist, arcana, aura models).
Emits real-time telemetry metrics (TTFB, chunk duration, active provider badge).
"""

import time
import httpx
import asyncio
from typing import AsyncGenerator, Dict, Any, Tuple
from app.config import settings
from app.audio_utils import generate_fallback_speech_wav

# Supported Rime Live Catalog Specs
RIME_MODELS = {
    "mist": {"description": "Ultra low-latency streaming model optimized for interactive voice agents", "recommended": True},
    "arcana": {"description": "Hyper-expressive conversational model for dynamic range", "recommended": False},
    "aura": {"description": "Standard natural delivery model", "recommended": False}
}

RIME_SPEAKERS = {
    "cora": {"gender": "Female", "role": "Crisp, authoritative medical dispatch"},
    "marsh": {"gender": "Male", "role": "Calm tactical field supervisor"},
    "allison": {"gender": "Female", "role": "Empathetic triage care"},
    "amber": {"gender": "Female", "role": "Clear operational announcements"},
    "creed": {"gender": "Male", "role": "Resolute incident response"}
}

class RimeClient:
    def __init__(self):
        self.api_key = settings.RIME_API_KEY
        self.api_url = settings.RIME_API_URL
        self.model_id = settings.RIME_MODEL_ID
        self.speaker = settings.RIME_SPEAKER
        self.audio_format = settings.RIME_AUDIO_FORMAT
        self.sampling_rate = settings.RIME_SAMPLING_RATE
        self.speed_alpha = settings.RIME_SPEED_ALPHA
        self.timeout = settings.RIME_TIMEOUT_SEC
        
    def get_catalog(self) -> Dict[str, Any]:
        """Returns the active model, voice, and audio transport catalog."""
        return {
            "active_configuration": {
                "endpoint": self.api_url,
                "model_id": self.model_id,
                "speaker": self.speaker,
                "language": settings.RIME_LANGUAGE,
                "audio_format": self.audio_format,
                "sampling_rate": self.sampling_rate,
                "speed_alpha": self.speed_alpha,
                "has_valid_key": bool(self.api_key and self.api_key != "your_rime_api_key_here")
            },
            "models": RIME_MODELS,
            "speakers": RIME_SPEAKERS
        }

    async def stream_speech(
        self, 
        text: str, 
        speaker: str = None, 
        model_id: str = None, 
        speed_alpha: float = None
    ) -> AsyncGenerator[Tuple[bytes, Dict[str, Any]], None]:
        """
        Streams audio bytes from Rime API chunk by chunk.
        Yields (chunk_bytes, telemetry_metadata).
        Gracefully fails over to local audible synthesizer if unconfigured.
        """
        speaker = speaker or self.speaker
        model_id = model_id or self.model_id
        speed_alpha = speed_alpha or self.speed_alpha
        
        start_time = time.perf_counter()
        has_key = bool(self.api_key and self.api_key != "your_rime_api_key_here")
        
        if has_key:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": f"audio/{self.audio_format}",
                "Content-Type": "application/json"
            }
            payload = {
                "speaker": speaker,
                "text": text,
                "modelId": model_id,
                "audioFormat": self.audio_format,
                "samplingRate": self.sampling_rate,
                "speedAlpha": speed_alpha,
                "lang": settings.RIME_LANGUAGE
            }
            
            first_byte_received = False
            ttfb_ms = 0.0
            
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    async with client.stream("POST", self.api_url, json=payload, headers=headers) as response:
                        if response.status_code == 200:
                            chunk_index = 0
                            async for raw_chunk in response.aiter_bytes(chunk_size=4096):
                                if not raw_chunk:
                                    continue
                                if not first_byte_received:
                                    ttfb_ms = (time.perf_counter() - start_time) * 1000.0
                                    first_byte_received = True
                                    
                                chunk_index += 1
                                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                                
                                telemetry = {
                                    "provider": "RIME_TTS",
                                    "model_id": model_id,
                                    "speaker": speaker,
                                    "format": self.audio_format,
                                    "ttfb_ms": round(ttfb_ms, 1),
                                    "elapsed_ms": round(elapsed_ms, 1),
                                    "chunk_index": chunk_index,
                                    "is_fallback": False,
                                    "text": text
                                }
                                yield raw_chunk, telemetry
                            return
                        else:
                            print(f"[RIME WARNING] HTTP {response.status_code}: {response.reason_phrase}. Triggering observable fallback.")
            except Exception as e:
                print(f"[RIME ERROR] Connection failed: {e}. Triggering observable fallback.")

        # --- FALLBACK PATH (Resilience & Offline Reproducibility) ---
        # Produces a self-contained valid RIFF/WAV for 100% reliable browser playback
        await asyncio.sleep(0.03) # 30ms local synthesis time
        ttfb_ms = (time.perf_counter() - start_time) * 1000.0
        fallback_wav = generate_fallback_speech_wav(text, sample_rate=self.sampling_rate)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        telemetry = {
            "provider": "FALLBACK_SYNTHESIZER",
            "model_id": "local-resonant-pcm",
            "speaker": "synthetic-dispatch",
            "format": "wav",
            "ttfb_ms": round(ttfb_ms, 1),
            "elapsed_ms": round(elapsed_ms, 1),
            "chunk_index": 1,
            "is_fallback": True,
            "text": text
        }
        yield fallback_wav, telemetry

rime_client = RimeClient()
