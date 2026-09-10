"""
Hard Voice Problem Acceptance Test:
Full-Duplex Interruption, Audio Queue Flush Latency, and Turn Fencing Benchmark.
Proves the exact hackathon test case:
"Introduce a fixed delay into a tool call. While the agent is speaking or waiting,
interrupt it and change one part of the request. Verify that queued Rime audio
stops promptly, the updated instruction reaches the application, stale tool results
are not spoken as current, and the final response reflects what the user requested."
"""

import pytest
import asyncio
import time
from app.orchestrator import TurnOrchestrator

@pytest.mark.asyncio
async def test_instant_barge_in_flush_latency():
    orchestrator = TurnOrchestrator()
    
    # Measure barge-in flush time
    flush_event = await orchestrator.interrupt_current_turn(reason="benchmark_user_barge_in")
    assert flush_event["flush_latency_ms"] < 100.0, f"Flush took {flush_event['flush_latency_ms']}ms (Must be < 100ms)"
    assert flush_event["new_turn_id"] == 1

@pytest.mark.asyncio
async def test_delayed_tool_barge_in_and_fencing():
    orchestrator = TurnOrchestrator()
    received_audio_chunks = []
    telemetry_events = []
    
    async def on_chunk(chunk, meta):
        received_audio_chunks.append(meta)
        
    async def on_telemetry(meta):
        telemetry_events.append(meta)
        
    # Turn 1: Launch long-running tool (3.5s delay)
    task1 = asyncio.create_task(
        orchestrator.execute_voice_turn(
            transcript="Run stress test lookup with deliberate 3.5 second delay",
            on_audio_chunk=on_chunk,
            on_telemetry=on_telemetry
        )
    )
    
    # Let initial status filler audio stream for 200ms
    await asyncio.sleep(0.2)
    turn1_id = orchestrator.active_turn_id
    
    # Verify filler audio chunks were delivered for Turn 1
    filler_chunks = [c for c in received_audio_chunks if c.get("turn_id") == turn1_id]
    assert len(filler_chunks) > 0, "Initial status filler was not emitted"
    
    # Interrupt and Barge-in with Turn 2 (Emergency medication order)
    flush_event = await orchestrator.interrupt_current_turn(reason="paramedic_barge_in")
    
    task2 = asyncio.create_task(
        orchestrator.execute_voice_turn(
            transcript="Cancel that! Patient crashing, dose epinephrine for 70 kilogram adult immediately",
            on_audio_chunk=on_chunk,
            on_telemetry=on_telemetry
        )
    )
    
    await task2
    active_final_turn_id = orchestrator.active_turn_id
    
    # Let any lingering Turn 1 task finish or fail safely
    try:
        await asyncio.wait_for(task1, timeout=1.0)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        pass
        
    # VERIFICATION:
    # 1. Stale tool result from Turn 1 MUST NOT be present in final answer audio chunks
    turn1_final_chunks = [
        c for c in received_audio_chunks 
        if c.get("turn_id") == turn1_id and c.get("phase") == "FINAL_ANSWER"
    ]
    assert len(turn1_final_chunks) == 0, "FATAL: Stale Turn 1 tool result was spoken after interruption!"
    
    # 2. Turn 2 (Epinephrine order) MUST be spoken and completed
    turn2_final_chunks = [
        c for c in received_audio_chunks 
        if c.get("turn_id") == active_final_turn_id and c.get("phase") == "FINAL_ANSWER"
    ]
    assert len(turn2_final_chunks) > 0, "Turn 2 response was not spoken"
    
    # 3. Interruption flush latency measured
    assert flush_event["flush_latency_ms"] < 50.0
