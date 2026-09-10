"""
Audio Processing Utilities, Tone Synthesizers, and Sound Effects Generator.
Provides standard RIFF WAV encoding, emergency telemetry beeps, and audio chunking.
"""

import math
import struct
import io
from typing import Generator, List

def create_wav_header(sample_rate: int = 22050, bits_per_sample: int = 16, channels: int = 1, data_size: int = 0) -> bytes:
    """Generates standard 44-byte RIFF WAV header for PCM stream encapsulation."""
    byte_rate = sample_rate * channels * (bits_per_sample // 8)
    block_align = channels * (bits_per_sample // 8)
    
    header = io.BytesIO()
    header.write(b'RIFF')
    header.write(struct.pack('<I', 36 + data_size))
    header.write(b'WAVE')
    header.write(b'fmt ')
    header.write(struct.pack('<I', 16)) # Subchunk1Size
    header.write(struct.pack('<H', 1))  # PCM format
    header.write(struct.pack('<H', channels))
    header.write(struct.pack('<I', sample_rate))
    header.write(struct.pack('<I', byte_rate))
    header.write(struct.pack('<H', block_align))
    header.write(struct.pack('<H', bits_per_sample))
    header.write(b'data')
    header.write(struct.pack('<I', data_size))
    return header.getvalue()

def generate_tone_pcm(duration_sec: float = 0.2, freq: float = 440.0, sample_rate: int = 22050, volume: float = 0.4) -> bytes:
    """Generates a smooth sine wave tone in raw 16-bit PCM."""
    num_samples = int(sample_rate * duration_sec)
    buffer = bytearray()
    
    for i in range(num_samples):
        t = i / sample_rate
        # Smooth attack and decay envelope
        attack = min(1.0, 30.0 * t)
        decay = min(1.0, 30.0 * (duration_sec - t))
        envelope = attack * decay
        val = int(envelope * 32767 * volume * math.sin(2.0 * math.pi * freq * t))
        buffer.extend(struct.pack('<h', max(-32768, min(32767, val))))
        
    return bytes(buffer)

def generate_tactical_roger_beep(sample_rate: int = 22050) -> bytes:
    """Generates tactical dispatch roger beep (two short ascending tones)."""
    tone1 = generate_tone_pcm(duration_sec=0.08, freq=880.0, sample_rate=sample_rate, volume=0.3)
    tone2 = generate_tone_pcm(duration_sec=0.10, freq=1200.0, sample_rate=sample_rate, volume=0.3)
    combined = tone1 + tone2
    header = create_wav_header(sample_rate=sample_rate, bits_per_sample=16, channels=1, data_size=len(combined))
    return header + combined

def generate_flush_alert_sound(sample_rate: int = 22050) -> bytes:
    """Generates rapid double click for barge-in audio queue flush."""
    tone = generate_tone_pcm(duration_sec=0.04, freq=300.0, sample_rate=sample_rate, volume=0.4)
    pause = b'\x00' * int(sample_rate * 0.02 * 2)
    tone2 = generate_tone_pcm(duration_sec=0.04, freq=250.0, sample_rate=sample_rate, volume=0.4)
    combined = tone + pause + tone2
    header = create_wav_header(sample_rate=sample_rate, bits_per_sample=16, channels=1, data_size=len(combined))
    return header + combined

def generate_fallback_speech_wav(text: str, sample_rate: int = 22050) -> bytes:
    """
    Creates a playable multi-tone cadence representing words in fallback mode.
    Guarantees a valid RIFF/WAV container that plays cleanly in WebAudio.
    """
    words = text.split()
    duration_per_word = max(0.10, min(0.25, 2.0 / max(1, len(words))))
    base_freqs = [440.0, 520.0, 580.0, 490.0, 392.0, 660.0]
    
    pcm_chunks = []
    for idx, word in enumerate(words):
        freq = base_freqs[idx % len(base_freqs)]
        pcm_chunks.append(generate_tone_pcm(duration_sec=duration_per_word, freq=freq, sample_rate=sample_rate, volume=0.25))
        pcm_chunks.append(b'\x00' * int(sample_rate * 0.02 * 2))
        
    all_pcm = b"".join(pcm_chunks)
    header = create_wav_header(sample_rate=sample_rate, bits_per_sample=16, channels=1, data_size=len(all_pcm))
    return header + all_pcm
