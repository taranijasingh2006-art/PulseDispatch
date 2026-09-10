"""
Full-Duplex Voice Turn Orchestrator with Interruption Recovery and Tool Continuity.
Manages turn IDs, token cancellation fences, and non-blocking tool execution.
"""

import asyncio
import time
import re
from typing import Dict, Any, Optional, Callable, Tuple
from app.prompting import normalize_text_for_ear, chunk_text_into_speech_clauses, SYSTEM_PROMPT
from app.tools import (
    calculate_emergency_dosage, 
    lookup_hospital_beds, 
    dispatch_backup_units, 
    log_patient_vitals, 
    state
)
from app.rime_client import rime_client

class TurnOrchestrator:
    def __init__(self):
        self.active_turn_id: int = 0
        self.active_task: Optional[asyncio.Task] = None
        self.conversation_history: list[Dict[str, str]] = []
        self.interruption_events: list[Dict[str, Any]] = []
        self.stale_firewall_events: list[Dict[str, Any]] = []
        self.turn_lock = asyncio.Lock()
        self.mode: str = "RESONANCE"  # "RESONANCE" (fenced) or "NAIVE" (unfenced)
        self.current_state: str = "IDLE"
        self.last_heard_phrase: str = ""
        self.tool_delay_override: Optional[float] = None
        
    async def set_state(self, new_state: str, turn_id: int, on_telemetry: Optional[Callable] = None, detail: Optional[str] = None):
        # Guard against obsolete turns modifying live state machine in RESONANCE mode
        if self.mode == "RESONANCE" and self.active_turn_id > 0 and turn_id < self.active_turn_id:
            return

        old_state = self.current_state
        self.current_state = new_state
        evt = {
            "type": "STATE_CHANGE",
            "state": new_state,
            "previous_state": old_state,
            "turn_id": turn_id,
            "mode": self.mode,
            "detail": detail or "",
            "timestamp": time.time()
        }
        if on_telemetry:
            await on_telemetry(evt)

    async def interrupt_current_turn(self, reason: str = "user_barge_in", on_telemetry: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Executes immediate audio flush and cancellation fencing.
        Stops queued TTS streaming, aborts running generation tasks,
        and fences state against stale async completions.
        """
        t0 = time.perf_counter()
        cancelled_turn = self.active_turn_id
        
        if self.mode == "RESONANCE":
            if self.active_task and not self.active_task.done():
                self.active_task.cancel()
            async with self.turn_lock:
                self.active_turn_id += 1
                new_turn = self.active_turn_id
        else:
            new_turn = self.active_turn_id
            
        flush_time_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        event = {
            "type": "INTERRUPTION_FENCE",
            "cancelled_turn_id": cancelled_turn,
            "new_turn_id": new_turn,
            "reason": reason,
            "flush_latency_ms": flush_time_ms,
            "last_heard_phrase": self.last_heard_phrase or "Checking regional hospitals...",
            "mode": self.mode,
            "timestamp": time.time()
        }
        self.interruption_events.append(event)
        
        if on_telemetry:
            await self.set_state("INTERRUPTED", cancelled_turn, on_telemetry, detail=reason)
            
        return event

    async def parse_and_route_intent(self, transcript: str) -> Tuple[str, Optional[Dict[str, Any]], Optional[str]]:
        """
        Interprets user clinical instructions.
        Returns (filler_spoken_text, tool_call_spec, direct_spoken_text).
        """
        t = transcript.lower().strip()
        
        # 1. Stress Test Intent (Deliberate delay to test interruption & continuity)
        if "stress test" in t or "delay test" in t or "delay tool" in t:
            d = self.tool_delay_override if self.tool_delay_override is not None else 3.5
            self.tool_delay_override = None  # Auto-reset after stress test trigger
            return (
                "Initiating regional resource query across multiple jurisdictions with synthetic delay...",
                {"name": "lookup_hospital_beds", "args": {"trauma_level": 1, "require_burn": True, "delay_sec": d}},
                None
            )
            
        # 2. Medication / Dosage Calculation
        if any(w in t for w in ["dose", "dosage", "calculate", "give", "administer", "mg", "epi", "epinephrine", "amiodarone", "fentanyl", "naloxone", "narcan", "atropine", "versed", "midazolam", "ketamine"]):
            weight = state.active_incident.get("patient", {}).get("weight_kg", 70.0)
            m = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg|kilos?|kilograms?)", t)
            if m:
                weight = float(m.group(1))
            elif "pediatric" in t or "child" in t:
                weight = 18.0
                
            drug = "epinephrine"
            if "amiodarone" in t: drug = "amiodarone"
            elif "fentanyl" in t: drug = "fentanyl"
            elif "naloxone" in t or "narcan" in t: drug = "naloxone"
            elif "atropine" in t: drug = "atropine"
            elif "midazolam" in t or "versed" in t: drug = "midazolam"
            elif "ketamine" in t: drug = "ketamine"
            
            indication = "anaphylaxis" if "anaphylaxis" in t or "allergic" in t else "arrest"
            return (
                f"Calculating weight-based {drug} dosage for {weight} kilogram patient...",
                {"name": "calculate_emergency_dosage", "args": {"drug_name": drug, "weight_kg": weight, "indication": indication}},
                None
            )
            
        # 3. Hospital / Trauma Bed Search (Instant response delay: 0.05s)
        if any(w in t for w in ["hospital", "bed", "trauma center", "burn unit", "nearest", "divert", "route", "destination"]):
            require_burn = "burn" in t
            return (
                "Checking regional hospital bed telemetry and divert status...",
                {"name": "lookup_hospital_beds", "args": {"trauma_level": 1, "require_burn": require_burn, "delay_sec": 0.05}},
                None
            )
            
        # 4. Dispatch Backup Units
        if any(w in t for w in ["dispatch", "backup", "send air", "medevac", "als", "ambulance", "rescue", "hazmat"]):
            unit_type = "ALS Advanced Life Support Ambulance"
            if "air" in t or "medevac" in t or "helicopter" in t:
                unit_type = "Air Evac Medevac Helicopter"
            elif "rescue" in t or "extricat" in t:
                unit_type = "Heavy Extrication Rescue Squad"
            elif "hazmat" in t:
                unit_type = "Hazmat Decon Unit"
                
            return (
                f"Transmitting priority dispatch alert for {unit_type}...",
                {"name": "dispatch_backup_units", "args": {"unit_type": unit_type, "priority": "CODE 3 HIGH PRIORITY"}},
                None
            )
            
        # 5. Log Vitals
        if any(w in t for w in ["vital", "bp", "blood pressure", "spo2", "gcs", "heart rate", "pulse", "rr", "respiration"]):
            bp_match = re.search(r"(\d+/\d+)", t)
            spo2_match = re.search(r"(?:spo2|o2|sat|saturation)\s*(?:is|=|:)?\s*(\d+)", t) or re.search(r"(\d+)\s*%", t)
            gcs_match = re.search(r"gcs\s*(?:is|=|:)?\s*(\d+)", t)
            hr_match = re.search(r"(?:hr|heart rate|pulse)\s*(?:is|=|:)?\s*(\d+)", t)
            rr_match = re.search(r"(?:rr|respiration|respiratory rate)\s*(?:is|=|:)?\s*(\d+)", t)
            
            return (
                "Logging vital signs to incident manifest...",
                {"name": "log_patient_vitals", "args": {
                    "blood_pressure": bp_match.group(1) if bp_match else None,
                    "spo2": int(spo2_match.group(1)) if spo2_match else None,
                    "gcs": int(gcs_match.group(1)) if gcs_match else None,
                    "heart_rate": int(hr_match.group(1)) if hr_match else None,
                    "respiratory_rate": int(rr_match.group(1)) if rr_match else None
                }},
                None
            )
            
        # 6. CPR / ACLS Protocol
        if "cpr" in t or "arrest" in t or "resuscitation" in t:
            return (
                "ACLS cardiac arrest protocol initiated. Metronome set to 110 beats per minute. Deliver 30 high-quality chest compressions followed by 2 ventilations.",
                None,
                None
            )
            
        # Direct conversational response
        return ("", None, f"PulseDispatch standing by on incident {state.active_incident['id']}. Request dosage calculation, trauma hospital routing, vitals update, or unit dispatch.")

    async def execute_voice_turn(
        self, 
        transcript: str, 
        on_audio_chunk: Callable[[bytes, Dict[str, Any]], Any],
        on_telemetry: Callable[[Dict[str, Any]], Any]
    ):
        """
        Orchestrates an end-to-end full duplex voice turn:
        1. Increments turn ID & fences previous state.
        2. Routes intent -> streams auditory status filler immediately.
        3. Runs tool asynchronously.
        4. Synthesizes final spoken response.
        5. Respects mid-turn cancellation at every step.
        """
        async with self.turn_lock:
            self.active_turn_id += 1
            turn_id = self.active_turn_id
            
        turn_start_time = time.perf_counter()
        await self.set_state("LISTENING", turn_id, on_telemetry)
        await self.set_state("PROCESSING", turn_id, on_telemetry)
        
        await on_telemetry({
            "type": "TURN_START",
            "turn_id": turn_id,
            "transcript": transcript,
            "mode": self.mode,
            "timestamp": time.time()
        })
        
        filler_text, tool_spec, direct_text = await self.parse_and_route_intent(transcript)
        
        # Step A: Auditory Status Filler (Conversation Continuity)
        if filler_text:
            if self.mode == "RESONANCE" and turn_id != self.active_turn_id:
                print(f"[FENCED] Turn {turn_id} aborted before filler.")
                return
                
            await self.set_state("SPEAKING", turn_id, on_telemetry, detail="Status Filler")
            await on_telemetry({
                "type": "FILLER_START",
                "turn_id": turn_id,
                "text": filler_text
            })
            
            self.last_heard_phrase = filler_text
            
            async for chunk, meta in rime_client.stream_speech(filler_text):
                if self.mode == "RESONANCE" and turn_id != self.active_turn_id:
                    print(f"[FENCED] Mid-filler interruption on turn {turn_id}.")
                    return
                meta["turn_id"] = turn_id
                meta["phase"] = "FILLER_STATUS"
                await on_audio_chunk(chunk, meta)

        # Step B: Tool Execution (Async Non-blocking)
        final_spoken_text = direct_text or ""
        if tool_spec:
            if self.mode == "RESONANCE" and turn_id != self.active_turn_id:
                print(f"[FENCED] Turn {turn_id} aborted before tool execution.")
                return
                
            tool_name = tool_spec["name"]
            tool_args = tool_spec["args"]
            
            tool_t0 = time.perf_counter()
            await self.set_state("TOOL_RUNNING", turn_id, on_telemetry, detail=tool_name)
            await on_telemetry({
                "type": "TOOL_START",
                "turn_id": turn_id,
                "tool_name": tool_name,
                "args": tool_args
            })
            
            if tool_name == "calculate_emergency_dosage":
                res = await calculate_emergency_dosage(**tool_args)
            elif tool_name == "lookup_hospital_beds":
                res = await lookup_hospital_beds(**tool_args)
            elif tool_name == "dispatch_backup_units":
                res = await dispatch_backup_units(**tool_args)
            elif tool_name == "log_patient_vitals":
                res = await log_patient_vitals(**tool_args)
            else:
                res = {"spoken_summary": "Action completed."}
                
            tool_duration_ms = round((time.perf_counter() - tool_t0) * 1000.0, 1)
            
            # CHECK TURN FENCE AGAINST STALE RESULTS
            if turn_id != self.active_turn_id:
                if self.mode == "RESONANCE":
                    stale_evt = {
                        "type": "STALE_RESULT_BLOCKED",
                        "source": tool_name,
                        "old_turn_id": turn_id,
                        "current_turn_id": self.active_turn_id,
                        "status": "BLOCKED",
                        "reason": f"Result from turn #{turn_id} discarded because active turn is #{self.active_turn_id}",
                        "timestamp": time.time()
                    }
                    self.stale_firewall_events.append(stale_evt)
                    await self.set_state("STALE_RESULT_BLOCKED", turn_id, on_telemetry, detail=f"Firewall blocked turn #{turn_id}")
                    await on_telemetry(stale_evt)
                    print(f"[FIREWALL BLOCKED] Discarded stale tool output from turn {turn_id} (active: {self.active_turn_id})")
                    return
                else:
                    unguarded_evt = {
                        "type": "STALE_RESULT_UNGUARDED",
                        "source": tool_name,
                        "old_turn_id": turn_id,
                        "current_turn_id": self.active_turn_id,
                        "status": "UNGUARDED_SPOKEN",
                        "reason": f"CRITICAL: Naive mode allowed stale tool result from turn #{turn_id} to override active turn #{self.active_turn_id}!",
                        "timestamp": time.time()
                    }
                    self.stale_firewall_events.append(unguarded_evt)
                    await on_telemetry(unguarded_evt)
                    print(f"[NAIVE UNGUARDED] Allowed stale tool output from turn {turn_id}")
                
            await on_telemetry({
                "type": "TOOL_COMPLETE",
                "turn_id": turn_id,
                "tool_name": tool_name,
                "duration_ms": tool_duration_ms,
                "result": res
            })
            
            final_spoken_text = res.get("spoken_summary", "")

        # Step C: Final Spoken Answer via Rime TTS
        if final_spoken_text:
            if self.mode == "RESONANCE" and turn_id != self.active_turn_id:
                return
            await self.set_state("SPEAKING", turn_id, on_telemetry, detail="Final Answer")
            speech_clauses = chunk_text_into_speech_clauses(final_spoken_text)
            for clause in speech_clauses:
                if self.mode == "RESONANCE" and turn_id != self.active_turn_id:
                    print(f"[FENCED] Mid-synthesis interruption on turn {turn_id}.")
                    return
                self.last_heard_phrase = clause
                async for chunk, meta in rime_client.stream_speech(clause):
                    if self.mode == "RESONANCE" and turn_id != self.active_turn_id:
                        print(f"[FENCED] Mid-stream audio playback interrupted on turn {turn_id}.")
                        return
                    meta["turn_id"] = turn_id
                    meta["phase"] = "FINAL_ANSWER"
                    meta["total_turn_elapsed_ms"] = round((time.perf_counter() - turn_start_time) * 1000.0, 1)
                    await on_audio_chunk(chunk, meta)
                    
        if turn_id == self.active_turn_id:
            await self.set_state("COMPLETED", turn_id, on_telemetry)
            await self.set_state("IDLE", turn_id, on_telemetry)
            
        await on_telemetry({
            "type": "TURN_COMPLETE",
            "turn_id": turn_id,
            "total_latency_ms": round((time.perf_counter() - turn_start_time) * 1000.0, 1)
        })

orchestrator = TurnOrchestrator()

