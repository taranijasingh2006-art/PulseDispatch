"""
Prompt Engineering & Acoustic Phrasing for Voice-Native Delivery.
Follows "Writing for the Ear" principles:
- Short conversational clauses (< 18 words per sentence).
- Phonetic expansions for medical identifiers, ratios, and acronyms.
- Natural audible pauses via commas and ellipses.
- Immediate auditory feedback before initiating asynchronous tools.
"""

import re

SYSTEM_PROMPT = """You are PulseDispatch, an expert hands-free voice triage and emergency operations copilot.
You assist paramedics, trauma nurses, and incident commanders in fast-paced, hands-busy, sterile environments.

CRITICAL VOICE DELIVERY RULES:
1. Speak concisely and clearly. Never speak in markdown bullet points, tables, or asterisks.
2. Expand numbers and medical acronyms so they are easy to hear and understand:
   - "GCS 8" -> "G-C-S is eight."
   - "0.3 mg" -> "zero point three milligrams."
   - "1:1000" -> "one to one-thousand concentration."
   - "SpO2 92%" -> "oxygen saturation is ninety-two percent."
   - "IV push" -> "I-V push."
3. Keep sentences short and direct. Prioritize immediate life-saving clarity over conversational pleasantries.
4. When invoking a tool that requires database lookups or calculation, immediately emit an auditory status filler first (e.g. "Calculating pediatric dosage now...", "Checking trauma bed availability...").
5. State units of measurement clearly (milligrams, milliliters, liters per minute).
"""

# Phonetic normalization dictionary for medical emergency terms
MEDICAL_PHONETIC_MAP = [
    (r"\bmg/kg\b", "milligrams per kilogram"),
    (r"\bmg\b", "milligrams"),
    (r"\bmcg\b", "micrograms"),
    (r"\bml\b", "milliliters"),
    (r"\bkg\b", "kilograms"),
    (r"\blbs?\b", "pounds"),
    (r"\bSpO2\b", "S-P-O-2"),
    (r"\bspo2\b", "S-P-O-2"),
    (r"\bGCS\b", "G-C-S"),
    (r"\bgcs\b", "G-C-S"),
    (r"\bBP\b", "blood pressure"),
    (r"\bbp\b", "blood pressure"),
    (r"\bHR\b", "heart rate"),
    (r"\bhr\b", "heart rate"),
    (r"\bIV\b", "I-V"),
    (r"\bIM\b", "I-M"),
    (r"\bIO\b", "I-O"),
    (r"\bCPR\b", "C-P-R"),
    (r"\bETT\b", "endotracheal tube"),
    (r"\bROSC\b", "return of spontaneous circulation"),
    (r"\bSTEMI\b", "ST-elevation myocardial infarction"),
    (r"\bVFib\b", "V-Fib"),
    (r"\bVTach\b", "V-Tach"),
    (r"\bPEA\b", "pulseless electrical activity"),
    (r"\b1:1000\b", "one to one-thousand"),
    (r"\b1:10,?000\b", "one to ten-thousand"),
]

def normalize_text_for_ear(text: str) -> str:
    """
    Cleans and prepares text for neural TTS playback.
    Removes markdown asterisks, hashes, backticks, and applies phonetic expansions.
    """
    if not text:
        return ""
    
    # Remove markdown formatting
    cleaned = re.sub(r"[\*#`_~\[\]\(\)\{\}>|]", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    
    # Apply medical phonetic replacements
    for pattern, replacement in MEDICAL_PHONETIC_MAP:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
    return cleaned

def chunk_text_into_speech_clauses(text: str) -> list[str]:
    """
    Splits a longer response into short, natural speech clauses at punctuation boundaries
    to enable low-latency pipelined streaming to Rime TTS.
    """
    cleaned = normalize_text_for_ear(text)
    if not cleaned:
        return []
    
    # Split by sentence terminators or major punctuation pauses
    raw_clauses = re.split(r"(?<=[.?!;:])\s+", cleaned)
    clauses = [c.strip() for c in raw_clauses if c.strip()]
    
    # If single clause is excessively long (> 25 words), split at commas or conjunctions
    refined_clauses = []
    for clause in clauses:
        words = clause.split()
        if len(words) > 25 and "," in clause:
            sub = [s.strip() for s in clause.split(",") if s.strip()]
            refined_clauses.extend(sub)
        else:
            refined_clauses.append(clause)
            
    return refined_clauses if refined_clauses else [cleaned]
