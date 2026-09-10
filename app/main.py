"""
PulseDispatch: Voice-Native Emergency Incident Copilot
FastAPI Server with Full-Duplex WebSockets, Rime Neural TTS streaming,
Interruption Fencing, and Live Mission Control Telemetry HUD.
"""

import json
import base64
import asyncio
from pathlib import Path
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.config import settings
from app.rime_client import rime_client
from app.orchestrator import orchestrator
from app.tools import (
    state, 
    switch_scenario, 
    calculate_emergency_dosage, 
    lookup_hospital_beds, 
    dispatch_backup_units, 
    log_patient_vitals
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Full-Duplex Voice-Native Emergency Incident Copilot powered by Rime Neural TTS"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SynthesizeRequest(BaseModel):
    text: str
    speaker: str = "cora"
    model_id: str = "mist"
    speed_alpha: float = 1.0

class DosageRequest(BaseModel):
    drug_name: str
    weight_kg: Optional[float] = None
    indication: str = "general"

class VitalsRequest(BaseModel):
    heart_rate: Optional[int] = None
    blood_pressure: Optional[str] = None
    spo2: Optional[int] = None
    gcs: Optional[int] = None
    respiratory_rate: Optional[int] = None

class DispatchRequest(BaseModel):
    unit_type: str
    priority: str = "CODE 3 HIGH PRIORITY"
    staging_area: Optional[str] = None

class HospitalQueryRequest(BaseModel):
    trauma_level: int = 1
    require_burn: bool = False
    max_distance_miles: float = 30.0

class ModeRequest(BaseModel):
    mode: str = "RESONANCE"  # "RESONANCE" or "NAIVE"

class DelayRequest(BaseModel):
    delay_sec: float = 1.0

@app.get("/api/catalog")
async def get_catalog():
    """Returns live Rime voice catalog, model configurations, and connection state."""
    return rime_client.get_catalog()

@app.get("/api/state")
async def get_system_state():
    """Returns current clinical and operational incident state."""
    return {
        "incident": state.active_incident,
        "vitals": state.patient_vitals,
        "dispatched_units": state.dispatched_units,
        "hospitals": state.hospitals,
        "active_turn_id": orchestrator.active_turn_id,
        "mode": orchestrator.mode,
        "current_state": orchestrator.current_state,
        "interruption_history": orchestrator.interruption_events[-10:],
        "stale_firewall_history": orchestrator.stale_firewall_events[-10:]
    }

@app.post("/api/mode/set")
async def set_agent_mode(req: ModeRequest):
    """Switches agent between RESONANCE (fenced) and NAIVE (unfenced) mode."""
    orchestrator.mode = req.mode.upper()
    return {"status": "ok", "mode": orchestrator.mode}

@app.post("/api/stress/delay")
async def set_tool_delay(req: DelayRequest):
    """Sets synthetic tool delay for stress testing."""
    orchestrator.tool_delay_override = req.delay_sec
    return {"status": "ok", "delay_sec": req.delay_sec}
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")
@app.get("/api/replay/timeline")
async def get_replay_timeline():
    """Returns chronologically ordered events for incident replay."""
    timeline = []
    for evt in orchestrator.interruption_events:
        timeline.append({"category": "INTERRUPTION", "time": evt.get("timestamp"), "detail": f"Interruption Flush ({evt.get('flush_latency_ms')}ms): Turn #{evt.get('cancelled_turn_id')} -> Turn #{evt.get('new_turn_id')}"})
    for evt in orchestrator.stale_firewall_events:
        status_label = "STALE FIREWALL BLOCKED" if evt.get("status") == "BLOCKED" else "NAIVE UNGUARDED SPOKEN"
        timeline.append({"category": "FIREWALL", "time": evt.get("timestamp"), "detail": f"{status_label}: {evt.get('source')} (Turn #{evt.get('old_turn_id')} vs Active #{evt.get('current_turn_id')})"})
    timeline.sort(key=lambda x: x["time"] or 0)
    return {"timeline": timeline}

@app.post("/api/scenario/randomize")
async def randomize_scenario():
    """Switches active emergency scenario."""
    return switch_scenario()

@app.post("/api/scenario/select/{index}")
async def select_scenario_by_index(index: int):
    """Selects specific emergency scenario by index."""
    return switch_scenario(index)

@app.post("/api/dosage/calculate")
async def api_calculate_dosage(req: DosageRequest):
    """Calculates weight-based emergency medication dosage."""
    return await calculate_emergency_dosage(req.drug_name, req.weight_kg, req.indication)

@app.post("/api/vitals/update")
async def api_update_vitals(req: VitalsRequest):
    """Updates patient vitals."""
    return await log_patient_vitals(req.heart_rate, req.blood_pressure, req.spo2, req.gcs, req.respiratory_rate)

@app.post("/api/dispatch/unit")
async def api_dispatch_unit(req: DispatchRequest):
    """Dispatches a backup unit."""
    return await dispatch_backup_units(req.unit_type, req.priority, req.staging_area)

@app.post("/api/hospitals/query")
async def api_query_hospitals(req: HospitalQueryRequest):
    """Queries regional trauma facilities."""
    return await lookup_hospital_beds(req.trauma_level, req.require_burn, req.max_distance_miles)

@app.post("/api/interrupt")
async def trigger_manual_interrupt():
    """Immediately triggers audio buffer flush and turn cancellation."""
    event = await orchestrator.interrupt_current_turn(reason="manual_operator_interrupt")
    return {"status": "flushed", "event": event}

@app.post("/api/tts/synthesize")
async def direct_synthesize(req: SynthesizeRequest):
    """Direct single-phrase TTS synthesis testing endpoint."""
    chunks = []
    meta_records = []
    async for chunk, meta in rime_client.stream_speech(
        text=req.text,
        speaker=req.speaker,
        model_id=req.model_id,
        speed_alpha=req.speed_alpha
    ):
        chunks.append(chunk)
        meta_records.append(meta)
        
    full_audio = b"".join(chunks)
    return {
        "audio_base64": base64.b64encode(full_audio).decode("utf-8"),
        "telemetry": meta_records[-1] if meta_records else {},
        "audio_bytes": len(full_audio),
        "text": req.text
    }

@app.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    """
    Full-duplex WebSocket channel:
    - Receives user transcripts, microphone events, and barge-in notifications.
    - Streams Rime audio chunks, turn status, and telemetry in real time.
    """
    await websocket.accept()
    
    # Send initial connection greeting
    await websocket.send_json({
        "type": "CONNECTION_ESTABLISHED",
        "message": "PulseDispatch tactical voice channel online",
        "state": {
            "incident": state.active_incident,
            "vitals": state.patient_vitals,
            "dispatched_units": state.dispatched_units,
            "hospitals": state.hospitals,
            "mode": orchestrator.mode,
            "current_state": orchestrator.current_state
        },
        "catalog": rime_client.get_catalog()
    })
    
    active_turn_task = None
    
    async def send_audio_chunk(chunk_bytes: bytes, meta: Dict[str, Any]):
        b64_audio = base64.b64encode(chunk_bytes).decode("utf-8")
        await websocket.send_json({
            "type": "AUDIO_CHUNK",
            "audio": b64_audio,
            "telemetry": meta
        })
        
    async def send_telemetry(meta: Dict[str, Any]):
        await websocket.send_json({
            "type": "TELEMETRY",
            "data": meta
        })

    try:
        while True:
            raw_msg = await websocket.receive_text()
            data = json.loads(raw_msg)
            msg_type = data.get("type")
            
            # 1. User Barge-in / Interruption
            if msg_type == "INTERRUPT":
                if active_turn_task and not active_turn_task.done():
                    active_turn_task.cancel()
                flush_event = await orchestrator.interrupt_current_turn(reason=data.get("reason", "user_speech_detected"), on_telemetry=send_telemetry)
                await websocket.send_json({
                    "type": "AUDIO_FLUSH",
                    "event": flush_event
                })
                
            # 2. Mode Switch
            elif msg_type == "SET_MODE":
                m = data.get("mode", "RESONANCE").upper()
                orchestrator.mode = m
                await websocket.send_json({
                    "type": "MODE_CHANGED",
                    "mode": orchestrator.mode
                })

            # 3. Delay Switch
            elif msg_type == "SET_DELAY":
                d = float(data.get("delay_sec", 1.0))
                orchestrator.tool_delay_override = d
                await websocket.send_json({
                    "type": "DELAY_CHANGED",
                    "delay_sec": d
                })

            # 4. Switch Incident Scenario
            elif msg_type == "SWITCH_SCENARIO":
                res = switch_scenario(data.get("index"))
                await websocket.send_json({
                    "type": "SCENARIO_UPDATED",
                    "state": res
                })

            # 5. Incoming User Utterance (Voice turn trigger)
            elif msg_type == "USER_UTTERANCE":
                transcript = data.get("transcript", "").strip()
                if not transcript:
                    continue
                    
                # If assistant is currently speaking or running tools, barge in immediately
                if active_turn_task and not active_turn_task.done():
                    if orchestrator.mode == "RESONANCE":
                        active_turn_task.cancel()
                    flush_event = await orchestrator.interrupt_current_turn(reason="new_utterance_preemption", on_telemetry=send_telemetry)
                    await websocket.send_json({
                        "type": "AUDIO_FLUSH",
                        "event": flush_event
                    })
                    
                # Launch new turn asynchronously
                active_turn_task = asyncio.create_task(
                    orchestrator.execute_voice_turn(
                        transcript=transcript,
                        on_audio_chunk=send_audio_chunk,
                        on_telemetry=send_telemetry
                    )
                )
                
            # 6. Ping / Keepalive
            elif msg_type == "PING":
                await websocket.send_json({"type": "PONG", "timestamp": data.get("timestamp")})
                
    except WebSocketDisconnect:
        if active_turn_task and not active_turn_task.done():
            active_turn_task.cancel()
    except Exception as e:
        if active_turn_task and not active_turn_task.done():
            active_turn_task.cancel()
        print(f"[WS ERROR] {e}")

# Mount static frontend
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
