"""
Emergency Triage and Tactical Incident Dispatch Tool Suite.
Provides real-time clinical calculations, hospital resource discovery,
vitals tracking, scenario randomization, and intentional latency injection.
"""

import asyncio
import time
import random
from typing import Dict, Any, List

INCIDENT_PRESETS = [
    {
        "id": "MED-7829",
        "title": "Pediatric Anaphylaxis & Severe Stridor",
        "category": "RED",
        "triage_label": "PRIORITY 1 - IMMEDIATE",
        "patient": {
            "name": "Tommy R.",
            "age": 5,
            "weight_kg": 18.0,
            "gender": "Male",
            "allergy": "Peanut / Ingestion",
            "chief_complaint": "Acute respiratory distress, facial angioedema, inspiratory stridor"
        },
        "vitals": {"heart_rate": 142, "blood_pressure": "78/48", "spo2": 89, "gcs": 13, "respiratory_rate": 34},
        "location": "Lincoln Elementary School Cafeteria, Zone 2"
    },
    {
        "id": "MED-9102",
        "title": "Highway Rollover Collision with Entrapment",
        "category": "RED",
        "triage_label": "PRIORITY 1 - IMMEDIATE",
        "patient": {
            "name": "Sarah K.",
            "age": 34,
            "weight_kg": 75.0,
            "gender": "Female",
            "allergy": "NKDA",
            "chief_complaint": "Severe blunt chest trauma, asymmetric breath sounds, steering wheel deformity"
        },
        "vitals": {"heart_rate": 128, "blood_pressure": "84/52", "spo2": 91, "gcs": 8, "respiratory_rate": 26},
        "location": "Interstate 95 Southbound at Mile Marker 42.5"
    },
    {
        "id": "MED-4421",
        "title": "Acute STEMI with Refractory Ventricular Tachycardia",
        "category": "RED",
        "triage_label": "PRIORITY 1 - CRITICAL",
        "patient": {
            "name": "Robert M.",
            "age": 58,
            "weight_kg": 85.0,
            "gender": "Male",
            "allergy": "Penicillin",
            "chief_complaint": "Crushing substernal chest pressure radiating to jaw, diaphoresis, runs of V-Tach"
        },
        "vitals": {"heart_rate": 165, "blood_pressure": "92/60", "spo2": 94, "gcs": 14, "respiratory_rate": 22},
        "location": "Metro Transit Station Platform 3B"
    },
    {
        "id": "MED-6380",
        "title": "Industrial Boiler Flash Burn & Inhalation Injury",
        "category": "RED",
        "triage_label": "PRIORITY 1 - IMMEDIATE",
        "patient": {
            "name": "Marcus L.",
            "age": 42,
            "weight_kg": 80.0,
            "gender": "Male",
            "allergy": "Sulfa",
            "chief_complaint": "35% Total Body Surface Area 2nd/3rd degree burns to chest/face, singed facial hair"
        },
        "vitals": {"heart_rate": 118, "blood_pressure": "108/68", "spo2": 95, "gcs": 15, "respiratory_rate": 24},
        "location": "Apex Chemical Processing Plant, Bay 4"
    },
    {
        "id": "MED-3199",
        "title": "Unresponsive Suspected Opioid Overdose with Hypoventilation",
        "category": "RED",
        "triage_label": "PRIORITY 1 - IMMEDIATE",
        "patient": {
            "name": "Unknown Female",
            "age": 26,
            "weight_kg": 65.0,
            "gender": "Female",
            "allergy": "Unknown",
            "chief_complaint": "Comatose, pinpoint pupils, agonal breathing 4 breaths/min, peripheral cyanosis"
        },
        "vitals": {"heart_rate": 48, "blood_pressure": "88/54", "spo2": 79, "gcs": 4, "respiratory_rate": 4},
        "location": "Civic Center Plaza Restroom Facility"
    }
]

HOSPITALS_DB = [
    {
        "id": "HOSP-01",
        "name": "Mercy University Trauma Center",
        "trauma_level": 1,
        "burn_unit": True,
        "pediatric_trauma": True,
        "distance_miles": 6.8,
        "eta_minutes": 11,
        "open_trauma_bays": 3,
        "icu_beds": 5,
        "status": "ACCEPTING_ALL",
        "divert": False
    },
    {
        "id": "HOSP-02",
        "name": "St. Jude Regional Medical Center",
        "trauma_level": 2,
        "burn_unit": False,
        "pediatric_trauma": False,
        "distance_miles": 3.9,
        "eta_minutes": 6,
        "open_trauma_bays": 2,
        "icu_beds": 2,
        "status": "ACCEPTING_ALL",
        "divert": False
    },
    {
        "id": "HOSP-03",
        "name": "Valley Burn & Specialized Critical Care",
        "trauma_level": 1,
        "burn_unit": True,
        "pediatric_trauma": True,
        "distance_miles": 14.5,
        "eta_minutes": 18,
        "open_trauma_bays": 4,
        "icu_beds": 8,
        "status": "ACCEPTING_ALL",
        "divert": False
    },
    {
        "id": "HOSP-04",
        "name": "Memorial Community Hospital",
        "trauma_level": 3,
        "burn_unit": False,
        "pediatric_trauma": False,
        "distance_miles": 2.1,
        "eta_minutes": 4,
        "open_trauma_bays": 1,
        "icu_beds": 1,
        "status": "DIVERT_TRAUMA",
        "divert": True
    }
]

class EmergencyState:
    def __init__(self):
        preset = INCIDENT_PRESETS[0]
        self.active_incident: Dict[str, Any] = {
            "id": preset["id"],
            "type": preset["title"],
            "triage_category": preset["category"],
            "triage_label": preset["triage_label"],
            "location": preset["location"],
            "patient": preset["patient"]
        }
        self.patient_vitals: Dict[str, Any] = {
            **preset["vitals"],
            "last_updated": time.strftime("%H:%M:%S")
        }
        self.dispatched_units: List[Dict[str, Any]] = [
            {
                "unit_id": "MEDIC-12",
                "type": "ALS Advanced Life Support Ambulance",
                "priority": "CODE 3 HIGH PRIORITY",
                "staging_area": preset["location"],
                "status": "ON SCENE",
                "eta_minutes": 0,
                "timestamp": time.strftime("%H:%M:%S")
            }
        ]
        self.administered_medications: List[Dict[str, Any]] = []
        self.hospitals = list(HOSPITALS_DB)
        self.cpr_active: bool = False
        self.cpr_start_time: float = 0.0

state = EmergencyState()

def switch_scenario(scenario_index: int = None) -> Dict[str, Any]:
    """Switches active incident scenario."""
    if scenario_index is None or scenario_index >= len(INCIDENT_PRESETS):
        preset = random.choice(INCIDENT_PRESETS)
    else:
        preset = INCIDENT_PRESETS[scenario_index]
        
    state.active_incident = {
        "id": preset["id"],
        "type": preset["title"],
        "triage_category": preset["category"],
        "triage_label": preset["triage_label"],
        "location": preset["location"],
        "patient": preset["patient"]
    }
    state.patient_vitals = {
        **preset["vitals"],
        "last_updated": time.strftime("%H:%M:%S")
    }
    state.dispatched_units = [
        {
            "unit_id": f"MEDIC-{random.randint(10, 30)}",
            "type": "ALS Advanced Life Support Ambulance",
            "priority": "CODE 3 HIGH PRIORITY",
            "staging_area": preset["location"],
            "status": "ON SCENE",
            "eta_minutes": 0,
            "timestamp": time.strftime("%H:%M:%S")
        }
    ]
    return {
        "incident": state.active_incident,
        "vitals": state.patient_vitals,
        "units": state.dispatched_units,
        "spoken_summary": f"Incident switched to {preset['id']}: {preset['title']}. Patient weight is {preset['patient']['weight_kg']} kilograms."
    }

async def calculate_emergency_dosage(drug_name: str, weight_kg: float = None, indication: str = "general") -> Dict[str, Any]:
    """Calculates weight-based emergency medication dosages."""
    if weight_kg is None:
        weight_kg = state.active_incident.get("patient", {}).get("weight_kg", 70.0)
        
    drug = drug_name.lower().strip()
    
    if "epi" in drug or "epinephrine" in drug:
        if "anaphylaxis" in indication.lower() or "arrest" not in indication.lower():
            dose_mg = round(min(0.5, 0.01 * weight_kg), 2)
            if weight_kg >= 50:
                dose_mg = 0.3
            return {
                "drug": "Epinephrine (1:1,000 concentration)",
                "route": "Intramuscular (anterolateral thigh)",
                "dose": f"{dose_mg} milligrams",
                "volume": f"{dose_mg} milliliters",
                "weight_kg": weight_kg,
                "dilution": "1 mg in 1 mL (1:1,000)",
                "spoken_summary": f"Administer {dose_mg} milligrams of one to one-thousand Epinephrine intramuscularly in the anterolateral thigh for {weight_kg} kilogram patient."
            }
        else:
            return {
                "drug": "Epinephrine (1:10,000 concentration)",
                "route": "Intravenous / Intraosseous push",
                "dose": "1 milligram every 3 to 5 minutes",
                "volume": "10 milliliters",
                "weight_kg": weight_kg,
                "dilution": "1 mg in 10 mL (1:10,000)",
                "spoken_summary": "Administer 1 milligram of one to ten-thousand Epinephrine I-V push every 3 to 5 minutes followed by a 20 milliliter saline flush."
            }
            
    elif "amiodarone" in drug:
        if weight_kg < 40:
            dose_mg = round(5.0 * weight_kg, 1)
            return {
                "drug": "Amiodarone Pediatric",
                "route": "IV / IO push",
                "dose": f"{dose_mg} milligrams (5 mg/kg)",
                "volume": f"{round(dose_mg / 50.0, 1)} mL",
                "weight_kg": weight_kg,
                "dilution": "50 mg/mL",
                "spoken_summary": f"Pediatric dose is {dose_mg} milligrams I-V push based on 5 milligrams per kilogram."
            }
        return {
            "drug": "Amiodarone Adult",
            "route": "IV / IO push",
            "dose": "300 milligrams first dose, 150 milligrams second dose",
            "volume": "6 mL (first dose)",
            "weight_kg": weight_kg,
            "dilution": "50 mg/mL",
            "spoken_summary": "First dose is 300 milligrams I-V push. Second dose is 150 milligrams if ventricular fibrillation persists."
        }
        
    elif "fentanyl" in drug:
        dose_mcg = int(min(100, weight_kg * 1.0))
        return {
            "drug": "Fentanyl Citrate",
            "route": "Slow IV push or Intranasal",
            "dose": f"{dose_mcg} micrograms",
            "volume": f"{round(dose_mcg / 50.0, 1)} mL",
            "weight_kg": weight_kg,
            "dilution": "50 mcg/mL",
            "spoken_summary": f"Administer {dose_mcg} micrograms slow I-V push over 2 minutes. Continuously monitor respiratory rate."
        }
        
    elif "naloxone" in drug or "narcan" in drug:
        return {
            "drug": "Naloxone (Narcan)",
            "route": "Intranasal or IV",
            "dose": "2 milligrams IN or 0.4 milligrams IV titrate",
            "volume": "2 mL (IN spray)",
            "weight_kg": weight_kg,
            "dilution": "2 mg/2 mL",
            "spoken_summary": "Administer 2 milligrams intranasally or 0.4 milligrams I-V, titrating to restore adequate spontaneous breathing."
        }
        
    elif "atropine" in drug:
        if weight_kg < 40:
            dose_mg = max(0.1, round(0.02 * weight_kg, 2))
            return {
                "drug": "Atropine Sulfate Pediatric",
                "route": "IV / IO push",
                "dose": f"{dose_mg} milligrams",
                "volume": f"{round(dose_mg / 0.1, 1)} mL",
                "weight_kg": weight_kg,
                "dilution": "0.1 mg/mL",
                "spoken_summary": f"Administer {dose_mg} milligrams I-V push for symptomatic bradycardia."
            }
        return {
            "drug": "Atropine Sulfate Adult",
            "route": "IV push",
            "dose": "1 milligram rapid IV push",
            "volume": "10 mL",
            "weight_kg": weight_kg,
            "dilution": "0.1 mg/mL",
            "spoken_summary": "Administer 1 milligram rapid I-V push. May repeat every 3 to 5 minutes up to a maximum of 3 milligrams."
        }
        
    elif "midazolam" in drug or "versed" in drug:
        dose_mg = round(min(5.0, weight_kg * 0.1), 1)
        return {
            "drug": "Midazolam (Versed)",
            "route": "IV or Intranasal / IM",
            "dose": f"{dose_mg} milligrams",
            "volume": f"{round(dose_mg / 5.0, 1)} mL",
            "weight_kg": weight_kg,
            "dilution": "5 mg/mL",
            "spoken_summary": f"Administer {dose_mg} milligrams for active seizure sedation."
        }
        
    elif "ketamine" in drug:
        dose_mg = round(weight_kg * 1.5, 0)
        return {
            "drug": "Ketamine HCl",
            "route": "IV push over 60 seconds",
            "dose": f"{dose_mg} milligrams (1.5 mg/kg)",
            "volume": f"{round(dose_mg / 50.0, 1)} mL",
            "weight_kg": weight_kg,
            "dilution": "50 mg/mL",
            "spoken_summary": f"Administer {dose_mg} milligrams Ketamine slow I-V push for rapid sequence induction or severe pain."
        }

    else:
        return {
            "drug": drug_name,
            "dose": "Standard protocol applies",
            "weight_kg": weight_kg,
            "spoken_summary": f"Standard protocol verified for {drug_name}. Verify patient weight of {weight_kg} kilograms before administration."
        }

async def lookup_hospital_beds(trauma_level: int = 1, require_burn: bool = False, max_distance_miles: float = 30.0, delay_sec: float = 0.0) -> Dict[str, Any]:
    """
    Looks up regional trauma and specialized critical care capacity.
    Supports synthetic delay injection for interruption stress testing.
    """
    if delay_sec > 0:
        await asyncio.sleep(delay_sec)
        
    matched = [
        h for h in state.hospitals 
        if h["trauma_level"] <= trauma_level 
        and (not require_burn or h["burn_unit"])
        and h["distance_miles"] <= max_distance_miles
        and not h.get("divert", False)
    ]
    
    top = matched[0] if matched else state.hospitals[0]
    spoken = f"{top['name']} is {top['distance_miles']} miles away with an estimated ETA of {top['eta_minutes']} minutes. They have {top['open_trauma_bays']} open trauma bays and are actively accepting priority patients."
        
    return {
        "results": matched or state.hospitals,
        "primary_destination": top,
        "spoken_summary": spoken
    }

async def dispatch_backup_units(unit_type: str, priority: str = "CODE 3 HIGH PRIORITY", staging_area: str = None) -> Dict[str, Any]:
    """Dispatches emergency resources."""
    staging = staging_area or state.active_incident.get("location", "Scene Command")
    unit_id = f"UNIT-{len(state.dispatched_units) + 201}"
    record = {
        "unit_id": unit_id,
        "type": unit_type,
        "priority": priority,
        "staging_area": staging,
        "status": "EN_ROUTE",
        "eta_minutes": 5 if "Air" in unit_type or "Medevac" in unit_type else 9,
        "timestamp": time.strftime("%H:%M:%S")
    }
    state.dispatched_units.append(record)
    
    return {
        "dispatched": record,
        "spoken_summary": f"Dispatched {unit_type} {unit_id} running {priority} to {staging}. ETA is {record['eta_minutes']} minutes."
    }

async def log_patient_vitals(heart_rate: int = None, blood_pressure: str = None, spo2: int = None, gcs: int = None, respiratory_rate: int = None) -> Dict[str, Any]:
    """Updates patient vital signs and assesses clinical stability."""
    if heart_rate is not None: state.patient_vitals["heart_rate"] = heart_rate
    if blood_pressure is not None: state.patient_vitals["blood_pressure"] = blood_pressure
    if spo2 is not None: state.patient_vitals["spo2"] = spo2
    if gcs is not None: state.patient_vitals["gcs"] = gcs
    if respiratory_rate is not None: state.patient_vitals["respiratory_rate"] = respiratory_rate
    state.patient_vitals["last_updated"] = time.strftime("%H:%M:%S")
    
    alerts = []
    if state.patient_vitals["gcs"] <= 8:
        alerts.append("Severe airway compromise protocol indicated")
    if state.patient_vitals["spo2"] < 90:
        alerts.append("Critical hypoxia alert - initiate high-flow oxygen")
    if state.patient_vitals["heart_rate"] > 140:
        alerts.append("Severe tachycardia detected")
        
    spoken = f"Vitals logged. Blood pressure {state.patient_vitals['blood_pressure']}, heart rate {state.patient_vitals['heart_rate']}, oxygen saturation {state.patient_vitals['spo2']} percent, and G-C-S is {state.patient_vitals['gcs']}."
    if alerts:
        spoken += f" Critical alert: {alerts[0]}."
        
    return {
        "vitals": state.patient_vitals,
        "alerts": alerts,
        "spoken_summary": spoken
    }
