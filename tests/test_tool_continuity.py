"""
Test Suite for Clinical Tools & Conversation Continuity.
"""

import pytest
from app.tools import calculate_emergency_dosage, lookup_hospital_beds, dispatch_backup_units, log_patient_vitals

@pytest.mark.asyncio
async def test_dosage_calculation():
    # Adult anaphylaxis
    res = await calculate_emergency_dosage("epinephrine", 70.0, "anaphylaxis")
    assert "0.3 milligrams" in res["dose"]
    assert "Intramuscular" in res["route"]
    assert "one to one-thousand" in res["spoken_summary"]
    
    # Pediatric anaphylaxis
    res_ped = await calculate_emergency_dosage("epinephrine", 15.0, "anaphylaxis")
    assert "0.15 milligrams" in res_ped["dose"]

@pytest.mark.asyncio
async def test_hospital_lookup():
    res = await lookup_hospital_beds(trauma_level=1, require_burn=True, delay_sec=0.01)
    assert len(res["results"]) > 0
    top = res["primary_destination"]
    assert top["burn_unit"] is True
    assert "miles away" in res["spoken_summary"]

@pytest.mark.asyncio
async def test_dispatch_and_vitals():
    disp = await dispatch_backup_units("Air Evac Medevac Helicopter", "CODE 3 EMERGENCY", "MM14")
    assert "UNIT-" in disp["dispatched"]["unit_id"]
    assert "Air Evac" in disp["spoken_summary"]
    
    v = await log_patient_vitals(heart_rate=120, blood_pressure="80/50", spo2=88, gcs=8)
    assert v["vitals"]["spo2"] == 88
    assert len(v["alerts"]) >= 2
