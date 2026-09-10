"""
Unit and Integration Tests for Rime Neural TTS Client.
"""

import pytest
from app.rime_client import rime_client, RIME_MODELS, RIME_SPEAKERS
from app.prompting import normalize_text_for_ear, chunk_text_into_speech_clauses

@pytest.mark.asyncio
async def test_rime_catalog():
    catalog = rime_client.get_catalog()
    assert "active_configuration" in catalog
    assert "models" in catalog
    assert "speakers" in catalog
    assert "mist" in catalog["models"]
    assert "cora" in catalog["speakers"]

@pytest.mark.asyncio
async def test_speech_stream_chunks():
    test_text = "Administer zero point three milligrams of epinephrine."
    chunks = []
    metas = []
    
    async for chunk, meta in rime_client.stream_speech(test_text):
        chunks.append(chunk)
        metas.append(meta)
        
    assert len(chunks) > 0
    assert len(metas) > 0
    assert metas[0]["chunk_index"] == 1
    assert "ttfb_ms" in metas[0]
    assert "provider" in metas[0]

def test_writing_for_ear_normalization():
    raw = "Give 5 mg/kg IV push, SpO2 is 88% and GCS is 8."
    normalized = normalize_text_for_ear(raw)
    assert "milligrams per kilogram" in normalized
    assert "I-V" in normalized
    assert "S-P-O-2" in normalized
    assert "G-C-S" in normalized

def test_speech_clause_chunking():
    long_text = "Checking hospital capacity now. St. Jude has three beds open, and Mercy Center is on divert."
    clauses = chunk_text_into_speech_clauses(long_text)
    assert len(clauses) >= 2
