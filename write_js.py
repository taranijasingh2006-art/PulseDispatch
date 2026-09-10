# -*- coding: utf-8 -*-
import os

js_code = """
class SoundFX {
    constructor() { this.ctx = null; }
    init() {
        if (!this.ctx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.ctx = new AudioContext();
        }
        if (this.ctx.state === "suspended") this.ctx.resume();
    }
    playRogerBeep() {
        try {
            this.init();
            const now = this.ctx.currentTime;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = "sine";
            osc.frequency.setValueAtTime(880, now);
            osc.frequency.setValueAtTime(1200, now + 0.05);
            gain.gain.setValueAtTime(0.12, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(now);
            osc.stop(now + 0.12);
        } catch (e) {}
    }
    playFlushClick() {
        try {
            this.init();
            const now = this.ctx.currentTime;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = "triangle";
            osc.frequency.setValueAtTime(320, now);
            osc.frequency.exponentialRampToValueAtTime(150, now + 0.08);
            gain.gain.setValueAtTime(0.2, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(now);
            osc.stop(now + 0.08);
        } catch (e) {}
    }
}

class SpeechVoiceEngine {
    constructor() {
        this.soundFX = new SoundFX();
        this.currentTurnId = null;
        this.isPlaying = false;
        this.soundEnabled = true;
    }
    speak(text, turnId) {
        if (!this.soundEnabled || !text) return;
        this.currentTurnId = turnId;
        this.isPlaying = true;
        if ("speechSynthesis" in window) {
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance(text);
            u.rate = 1.05;
            const voices = window.speechSynthesis.getVoices();
            const v = voices.find(vox => vox.lang.includes("en") && (vox.name.includes("Female") || vox.name.includes("Natural") || vox.name.includes("Samantha")));
            if (v) u.voice = v;
            u.onend = () => { if (this.currentTurnId === turnId) this.isPlaying = false; };
            u.onerror = () => { this.isPlaying = false; };
            this.soundFX.playRogerBeep();
            window.speechSynthesis.speak(u);
        }
    }
    stopAll(newTurnId = null) {
        const t0 = performance.now();
        if ("speechSynthesis" in window) window.speechSynthesis.cancel();
        this.isPlaying = false;
        this.currentTurnId = newTurnId;
        this.soundFX.playFlushClick();
        return (performance.now() - t0).toFixed(2);
    }
}

class VoiceCopilotApp {
    constructor() {
        this.ws = null;
        this.voiceEngine = new SpeechVoiceEngine();
        this.isListening = false;
        this.recognition = null;
        this.turnCount = 0;
        this.mediaStream = null;
        this.audioContext = null;
        this.analyser = null;
        this.micDataArray = null;
        this.micLevel = 0;
        this.canvas = document.getElementById("waveformCanvas");
        this.canvasCtx = this.canvas ? this.canvas.getContext("2d") : null;
        this.animPhase = 0;

        this.initDOMElements();
        this.initWebSocket();
        this.initVisualizer();
        this.bindUserEvents();
        this.loadInitialState();
    }

    initDOMElements() {
        this.micToggleBtn = document.getElementById("micToggleBtn");
        this.micBtnText = document.getElementById("micBtnText");
        this.inputMicBtn = document.getElementById("inputMicBtn");
        this.interruptBtn = document.getElementById("interruptBtn");
        this.stressTestBtn = document.getElementById("stressTestBtn");
        this.soundToggleBtn = document.getElementById("soundToggleBtn");
        this.commandInput = document.getElementById("commandInput");
        this.sendCommandBtn = document.getElementById("sendCommandBtn");

        this.wsStatus = document.getElementById("wsStatus");
        this.activeProviderBadge = document.getElementById("activeProviderBadge");
        this.audioStatusOverlay = document.getElementById("audioStatusOverlay");
        this.transcriptFeed = document.getElementById("transcriptFeed");
        this.unitsFeed = document.getElementById("unitsFeed");
        this.turnCounter = document.getElementById("turnCounter");
        this.micVolumeBar = document.getElementById("micVolumeBar");
        this.micDbText = document.getElementById("micDbText");
        this.liveHearingPill = document.getElementById("liveHearingPill");
        this.liveHearingText = document.getElementById("liveHearingText");

        this.metricTTFB = document.getElementById("metricTTFB");
        this.metricFlush = document.getElementById("metricFlush");
        this.metricTurnId = document.getElementById("metricTurnId");
        this.metricToolTime = document.getElementById("metricToolTime");

        this.incidentBadge = document.getElementById("incidentBadge");
        this.incidentId = document.getElementById("incidentId");
        this.incidentTitle = document.getElementById("incidentTitle");
        this.incidentLocation = document.getElementById("incidentLocation");
        this.patientInfo = document.getElementById("patientInfo");
        this.randomScenarioBtn = document.getElementById("randomScenarioBtn");

        this.vitalHR = document.getElementById("vitalHR");
        this.vitalBP = document.getElementById("vitalBP");
        this.vitalSpO2 = document.getElementById("vitalSpO2");
        this.vitalGCS = document.getElementById("vitalGCS");

        this.voiceSelect = document.getElementById("voiceSelect");
        this.modelSelect = document.getElementById("modelSelect");

        this.dosageModal = document.getElementById("dosageModal");
        this.openDosageModalBtn = document.getElementById("openDosageModalBtn");
        this.closeDosageModalBtn = document.getElementById("closeDosageModalBtn");
        this.modalDrugSelect = document.getElementById("modalDrugSelect");
        this.modalWeightSlider = document.getElementById("modalWeightSlider");
        this.modalWeightDisplay = document.getElementById("modalWeightDisplay");
        this.modalDoseResult = document.getElementById("modalDoseResult");
        this.modalSpokenPreview = document.getElementById("modalSpokenPreview");
        this.modalSpeakOrderBtn = document.getElementById("modalSpeakOrderBtn");
    }

    async loadInitialState() {
        try {
            const res = await fetch("/api/state");
            const data = await res.json();
            if (data.incident) this.updateIncidentHUD(data.incident);
            if (data.vitals) this.updateVitalsHUD(data.vitals);
            if (data.dispatched_units) this.renderUnitsHUD(data.dispatched_units);
        } catch (e) {}
    }

    initWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws/voice`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            this.wsStatus.innerHTML = `<i class="fa-solid fa-circle text-[9px] text-emerald-400 animate-pulse"></i><span>WS Connected</span>`;
            this.wsStatus.className = "flex items-center space-x-1.5 text-xs text-emerald-400 bg-emerald-950/80 border border-emerald-800 px-3 py-1.5 rounded-full";
        };

        this.ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            this.handleMessage(msg);
        };

        this.ws.onclose = () => {
            this.wsStatus.innerHTML = `<i class="fa-solid fa-circle text-[9px] text-red-400"></i><span>Reconnecting...</span>`;
            this.wsStatus.className = "flex items-center space-x-1.5 text-xs text-red-400 bg-red-950/80 border border-red-800 px-3 py-1.5 rounded-full";
            setTimeout(() => this.initWebSocket(), 2500);
        };
    }

    handleMessage(msg) {
        if (msg.type === "CONNECTION_ESTABLISHED") {
            const config = msg.catalog.active_configuration;
            this.activeProviderBadge.textContent = `RIME_TTS (${config.model_id} / ${config.speaker})`;
            if (msg.state) {
                if (msg.state.incident) this.updateIncidentHUD(msg.state.incident);
                if (msg.state.vitals) this.updateVitalsHUD(msg.state.vitals);
                if (msg.state.dispatched_units) this.renderUnitsHUD(msg.state.dispatched_units);
            }
        } else if (msg.type === "SCENARIO_UPDATED") {
            const s = msg.state;
            if (s.incident) this.updateIncidentHUD(s.incident);
            if (s.vitals) this.updateVitalsHUD(s.vitals);
            if (s.units) this.renderUnitsHUD(s.units);
            this.appendLog("system", `Emergency Scenario Switched: [${s.incident.id}] ${s.incident.type}`);
        } else if (msg.type === "AUDIO_CHUNK") {
            const meta = msg.telemetry;
            if (meta) {
                if (meta.ttfb_ms) this.metricTTFB.textContent = `${meta.ttfb_ms} ms`;
                if (meta.turn_id) this.metricTurnId.textContent = `#${meta.turn_id}`;
                if (meta.text) this.voiceEngine.speak(meta.text, meta.turn_id);
            }
        } else if (msg.type === "AUDIO_FLUSH") {
            const flushLatency = this.voiceEngine.stopAll(msg.event.new_turn_id);
            this.metricFlush.textContent = `${flushLatency} ms`;
            this.appendLog("system", `Barge-in fence triggered (Turn #${msg.event.cancelled_turn_id} -> #${msg.event.new_turn_id}). Audio queue instantly cleared.`);
        } else if (msg.type === "TELEMETRY") {
            const d = msg.data;
            if (d.type === "TURN_START") {
                this.metricTurnId.textContent = `#${d.turn_id}`;
                this.turnCount++;
                this.turnCounter.textContent = `${this.turnCount} turns`;
                this.appendLog("user", d.transcript);
            } else if (d.type === "FILLER_START") {
                this.appendLog("copilot-filler", `[Status Filler] ${d.text}`);
                this.voiceEngine.speak(d.text, d.turn_id);
            } else if (d.type === "TOOL_START") {
                this.metricToolTime.textContent = `Running ${d.tool_name}...`;
                this.appendLog("tool", `Executing async tool: ${d.tool_name}`);
            } else if (d.type === "TOOL_COMPLETE") {
                this.metricToolTime.textContent = `${d.duration_ms} ms`;
                if (d.tool_name === "log_patient_vitals" && d.result.vitals) {
                    this.updateVitalsHUD(d.result.vitals);
                } else if (d.tool_name === "dispatch_backup_units" && d.result.dispatched) {
                    this.addDispatchedUnitHUD(d.result.dispatched);
                }
                const summary = d.result.spoken_summary || JSON.stringify(d.result);
                this.appendLog("tool", `Tool output (${d.duration_ms}ms): ${summary}`);
                this.appendLog("copilot", summary);
                this.voiceEngine.speak(summary, d.turn_id);
            }
        }
    }

    updateIncidentHUD(inc) {
        this.incidentId.textContent = inc.id || "MED-7829";
        this.incidentTitle.textContent = inc.type || "Active Emergency Incident";
        this.incidentLocation.innerHTML = `<i class="fa-solid fa-location-dot text-red-400 mr-1"></i>${inc.location || "Scene Command"}`;
        const pat = inc.patient || { age: 30, weight_kg: 70, allergy: "NKDA" };
        this.patientInfo.innerHTML = `<i class="fa-solid fa-user text-cyan-400 mr-1"></i>Age ${pat.age} • ${pat.weight_kg} kg • Allergy: ${pat.allergy}`;
        if (this.modalWeightSlider) {
            this.modalWeightSlider.value = pat.weight_kg;
            this.updateModalDosagePreview();
        }
    }

    updateVitalsHUD(v) {
        if (v.heart_rate !== undefined) this.vitalHR.innerHTML = `${v.heart_rate} <span class="text-[10px] font-normal text-slate-400">BPM</span>`;
        if (v.blood_pressure !== undefined) this.vitalBP.innerHTML = `${v.blood_pressure} <span class="text-[10px] font-normal text-slate-400">mmHg</span>`;
        if (v.spo2 !== undefined) this.vitalSpO2.innerHTML = `${v.spo2} <span class="text-[10px] font-normal text-slate-400">%</span>`;
        if (v.gcs !== undefined) this.vitalGCS.innerHTML = `${v.gcs} <span class="text-[10px] font-normal text-slate-400">/ 15</span>`;
    }

    renderUnitsHUD(units) {
        this.unitsFeed.innerHTML = "";
        units.forEach(u => this.addDispatchedUnitHUD(u));
    }

    addDispatchedUnitHUD(unit) {
        const item = document.createElement("div");
        item.className = "bg-slate-950 border border-slate-800/80 p-2.5 rounded-lg shadow-inner animate-fade-in";
        item.innerHTML = `
            <div class="flex items-center justify-between text-slate-200 font-bold">
                <span>${unit.unit_id} (${unit.type})</span>
                <span class="text-[9px] font-mono text-amber-400">${unit.status || "EN ROUTE"}</span>
            </div>
            <div class="text-[10px] text-slate-400 mt-0.5">${unit.priority || "CODE 3"} • ${unit.staging_area} (ETA ${unit.eta_minutes}m)</div>
        `;
        this.unitsFeed.prepend(item);
    }

    appendLog(role, text) {
        const div = document.createElement("div");
        div.className = "flex items-start space-x-2.5 p-3 rounded-xl border text-xs";

        if (role === "user") {
            div.className += " bg-blue-950/50 border-blue-800/60 text-blue-200";
            div.innerHTML = `<div class="w-6 h-6 rounded-full bg-blue-900 text-blue-300 border border-blue-700 flex items-center justify-center font-bold flex-shrink-0 text-[10px]">EM</div><div class="space-y-0.5"><div class="text-[10px] font-bold text-blue-400 uppercase">Paramedic Voice</div><p class="text-slate-200">${text}</p></div>`;
        } else if (role === "copilot-filler") {
            div.className += " bg-cyan-950/40 border-cyan-800/50 text-cyan-300 italic";
            div.innerHTML = `<div class="w-6 h-6 rounded-full bg-cyan-900/80 text-cyan-300 border border-cyan-700 flex items-center justify-center flex-shrink-0 text-[10px]"><i class="fa-solid fa-wave-square"></i></div><div class="space-y-0.5"><div class="text-[10px] font-bold text-cyan-400 uppercase">Acoustic Filler</div><p>${text}</p></div>`;
        } else if (role === "tool") {
            div.className += " bg-amber-950/40 border-amber-800/50 text-amber-200 font-mono";
            div.innerHTML = `<div class="w-6 h-6 rounded-full bg-amber-900/80 text-amber-400 border border-amber-700 flex items-center justify-center flex-shrink-0 text-[10px]"><i class="fa-solid fa-gear"></i></div><div class="space-y-0.5"><div class="text-[10px] font-bold text-amber-400 uppercase">Clinical Tool</div><p class="text-slate-300">${text}</p></div>`;
        } else if (role === "system") {
            div.className += " bg-red-950/50 border-red-800/60 text-red-300 font-mono";
            div.innerHTML = `<div class="w-6 h-6 rounded-full bg-red-900 text-red-300 border border-red-700 flex items-center justify-center flex-shrink-0 text-[10px]"><i class="fa-solid fa-shield"></i></div><div class="space-y-0.5"><div class="text-[10px] font-bold text-red-400 uppercase">Interruption Fence</div><p>${text}</p></div>`;
        } else {
            div.className += " bg-slate-950/80 border-slate-800/60 text-slate-200";
            div.innerHTML = `<div class="w-6 h-6 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center justify-center flex-shrink-0 text-[10px] font-bold">PD</div><div class="space-y-0.5"><div class="text-[10px] font-bold text-emerald-400 uppercase">PulseDispatch</div><p class="text-slate-100">${text}</p></div>`;
        }

        this.transcriptFeed.appendChild(div);
        this.transcriptFeed.scrollTop = this.transcriptFeed.scrollHeight;
    }

    sendUtterance(transcript) {
        if (!transcript) return;
        if (this.liveHearingPill) this.liveHearingPill.classList.add("hidden");
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: "USER_UTTERANCE",
                transcript: transcript,
                speaker: this.voiceSelect.value,
                model_id: this.modelSelect.value
            }));
        }
    }

    triggerInterruption() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: "INTERRUPT", reason: "manual_user_barge_in" }));
        }
        const latency = this.voiceEngine.stopAll();
        this.metricFlush.textContent = `${latency} ms`;
    }

    async startHardwareMicrophone() {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.audioContext = new AudioContext();
            this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            source.connect(this.analyser);
            this.micDataArray = new Uint8Array(this.analyser.frequencyBinCount);

            this.isListening = true;
            this.micBtnText.textContent = "Mic Active (Listening...)";
            this.micToggleBtn.className = "flex-1 sm:flex-initial flex items-center justify-center space-x-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-5 py-2 rounded-xl shadow-lg shadow-emerald-600/30 transition-all";
            this.audioStatusOverlay.textContent = "LIVE MICROPHONE ACTIVE -- SPEAK NOW";
            this.audioStatusOverlay.className = "absolute inset-0 flex items-center justify-center text-xs font-mono font-bold text-emerald-400 pointer-events-none animate-pulse";

            this.startSpeechRecognition();
        } catch (err) {
            alert("Microphone Access Required: Please allow microphone access in your browser.");
            this.isListening = false;
        }
    }

    stopHardwareMicrophone() {
        this.isListening = false;
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(t => t.stop());
            this.mediaStream = null;
        }
        if (this.recognition) {
            try { this.recognition.stop(); } catch (e) {}
        }
        this.micBtnText.textContent = "Activate Microphone";
        this.micToggleBtn.className = "flex-1 sm:flex-initial flex items-center justify-center space-x-2 bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 text-white font-bold px-5 py-2 rounded-xl shadow-md shadow-cyan-600/20 transition-all";
        this.audioStatusOverlay.textContent = "CLICK ACTIVATE MICROPHONE TO SPEAK";
        this.audioStatusOverlay.className = "absolute inset-0 flex items-center justify-center text-xs font-mono font-bold text-slate-500 pointer-events-none";
        if (this.liveHearingPill) this.liveHearingPill.classList.add("hidden");
        if (this.micVolumeBar) this.micVolumeBar.style.width = "0%";
        if (this.micDbText) this.micDbText.textContent = "0%";
    }

    startSpeechRecognition() {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRec) {
            this.recognition = new SpeechRec();
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            this.recognition.lang = "en-US";

            this.recognition.onresult = (event) => {
                let interimTranscript = "";
                let finalTranscript = "";
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript;
                    } else {
                        interimTranscript += event.results[i][0].transcript;
                    }
                }

                if ((interimTranscript || finalTranscript) && this.voiceEngine.isPlaying) {
                    this.triggerInterruption();
                }

                if (interimTranscript && this.liveHearingPill) {
                    this.liveHearingPill.classList.remove("hidden");
                    this.liveHearingText.textContent = `"${interimTranscript.trim()}"`;
                }

                if (finalTranscript.trim()) {
                    if (this.liveHearingPill) this.liveHearingPill.classList.add("hidden");
                    this.sendUtterance(finalTranscript.trim());
                }
            };

            this.recognition.onerror = (e) => console.warn("[SPEECH REC]", e.error);
            this.recognition.onend = () => { if (this.isListening) { try { this.recognition.start(); } catch (e) {} } };
            try { this.recognition.start(); } catch (e) {}
        }
    }

    initVisualizer() {
        const canvas = this.canvas;
        const ctx = this.canvasCtx;
        const render = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            canvas.width = canvas.parentElement.clientWidth;
            canvas.height = canvas.parentElement.clientHeight;

            const isSpeaking = this.voiceEngine.isPlaying;
            const isListening = this.isListening;

            if (this.analyser && this.isListening && this.micDataArray) {
                this.analyser.getByteFrequencyData(this.micDataArray);
                let sum = 0;
                for (let i = 0; i < this.micDataArray.length; i++) sum += this.micDataArray[i];
                const avg = sum / this.micDataArray.length;
                this.micLevel = Math.min(100, Math.round((avg / 128) * 100));
                if (this.micVolumeBar) this.micVolumeBar.style.width = `${this.micLevel}%`;
                if (this.micDbText) this.micDbText.textContent = `${this.micLevel}%`;
            }

            ctx.lineWidth = 2.5;
            ctx.beginPath();
            const slices = 80;
            const sliceWidth = canvas.width / slices;
            let x = 0;

            for (let i = 0; i < slices; i++) {
                let amp = 0;
                if (isSpeaking) {
                    amp = Math.sin(this.animPhase + i * 0.25) * 24 + Math.cos(this.animPhase * 1.8 + i * 0.1) * 12;
                    ctx.strokeStyle = "rgba(6, 182, 212, 0.9)";
                } else if (isListening) {
                    const freqVal = this.micDataArray ? (this.micDataArray[i % this.micDataArray.length] / 6) : 0;
                    amp = Math.sin(this.animPhase * 0.9 + i * 0.15) * (6 + freqVal);
                    ctx.strokeStyle = "rgba(16, 185, 129, 0.9)";
                } else {
                    amp = Math.sin(this.animPhase * 0.2 + i * 0.05) * 2;
                    ctx.strokeStyle = "rgba(71, 85, 105, 0.4)";
                }
                const y = canvas.height / 2 + amp;
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
                x += sliceWidth;
            }
            ctx.stroke();
            this.animPhase += 0.09;
            requestAnimationFrame(render);
        };
        render();
    }

    updateModalDosagePreview() {
        const weight = parseFloat(this.modalWeightSlider.value);
        this.modalWeightDisplay.textContent = `${weight.toFixed(1)} kg`;
        const drug = this.modalDrugSelect.value;
        if (drug === "epinephrine") {
            const dose = (weight >= 50 ? 0.3 : Math.min(0.5, 0.01 * weight)).toFixed(2);
            this.modalDoseResult.textContent = `${dose} mg IM (1:1,000)`;
            this.modalSpokenPreview.textContent = `"Administer ${dose} milligrams of one to one-thousand Epinephrine intramuscularly."`;
        } else if (drug === "amiodarone") {
            const dose = weight < 40 ? `${(5 * weight).toFixed(0)} mg (5 mg/kg)` : "300 mg IV push";
            this.modalDoseResult.textContent = dose;
            this.modalSpokenPreview.textContent = `"Administer ${dose} I-V push for ventricular tachycardia."`;
        } else if (drug === "fentanyl") {
            const dose = Math.min(100, Math.round(weight * 1.0));
            this.modalDoseResult.textContent = `${dose} mcg IV/IN`;
            this.modalSpokenPreview.textContent = `"Administer ${dose} micrograms slow I-V push over 2 minutes."`;
        } else if (drug === "naloxone") {
            this.modalDoseResult.textContent = "2 mg IN / 0.4 mg IV";
            this.modalSpokenPreview.textContent = '"Administer 2 milligrams intranasally or 0.4 milligrams I-V titrate."';
        } else if (drug === "atropine") {
            const dose = weight < 40 ? `${Math.max(0.1, (0.02 * weight)).toFixed(2)} mg` : "1.0 mg rapid IV";
            this.modalDoseResult.textContent = dose;
            this.modalSpokenPreview.textContent = `"Administer ${dose} rapid I-V push for bradycardia."`;
        } else if (drug === "midazolam") {
            const dose = Math.min(5.0, (weight * 0.1)).toFixed(1);
            this.modalDoseResult.textContent = `${dose} mg IV/IN`;
            this.modalSpokenPreview.textContent = `"Administer ${dose} milligrams for active seizure sedation."`;
        }
    }

    bindUserEvents() {
        this.micToggleBtn.addEventListener("click", async () => {
            if (!this.isListening) await this.startHardwareMicrophone();
            else this.stopHardwareMicrophone();
        });
        this.sendCommandBtn.addEventListener("click", () => {
            const val = this.commandInput.value.trim();
            if (val) { this.sendUtterance(val); this.commandInput.value = ""; }
        });
        this.commandInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                const val = this.commandInput.value.trim();
                if (val) { this.sendUtterance(val); this.commandInput.value = ""; }
            }
        });
        this.inputMicBtn.addEventListener("click", () => this.micToggleBtn.click());
        this.interruptBtn.addEventListener("click", () => this.triggerInterruption());
        this.soundToggleBtn.addEventListener("click", () => {
            this.voiceEngine.soundEnabled = !this.voiceEngine.soundEnabled;
            this.soundToggleBtn.innerHTML = this.voiceEngine.soundEnabled 
                ? '<i class="fa-solid fa-volume-high text-cyan-400"></i> Audio Enabled' 
                : '<i class="fa-solid fa-volume-xmark text-slate-500"></i> Audio Muted';
        });
        this.randomScenarioBtn.addEventListener("click", () => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) this.ws.send(JSON.stringify({ type: "SWITCH_SCENARIO" }));
        });
        this.stressTestBtn.addEventListener("click", () => {
            this.sendUtterance("Run stress test lookup with deliberate 3.5 second delay");
            setTimeout(() => {
                this.appendLog("user", "[MID-TOOL BARGE-IN INTERRUPTION]: Cancel query! Patient crashing, dose epinephrine immediately!");
                this.sendUtterance("Cancel query! Patient crashing, dose epinephrine immediately for 70kg adult!");
            }, 1200);
        });
        document.querySelectorAll(".quick-prompt").forEach(btn => {
            btn.addEventListener("click", () => this.sendUtterance(btn.getAttribute("data-text")));
        });
        this.openDosageModalBtn.addEventListener("click", () => {
            this.dosageModal.classList.remove("hidden");
            this.updateModalDosagePreview();
        });
        this.closeDosageModalBtn.addEventListener("click", () => this.dosageModal.classList.add("hidden"));
        this.modalWeightSlider.addEventListener("input", () => this.updateModalDosagePreview());
        this.modalDrugSelect.addEventListener("change", () => this.updateModalDosagePreview());
        this.modalSpeakOrderBtn.addEventListener("click", () => {
            const preview = this.modalSpokenPreview.textContent.replace(/"/g, "");
            this.dosageModal.classList.add("hidden");
            this.sendUtterance(preview);
        });
    }
}

window.addEventListener("DOMContentLoaded", () => {
    window.voiceCopilotApp = new VoiceCopilotApp();
});
"""

with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(js_code)
print("static/app.js successfully written!")
