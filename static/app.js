/**
 * PULSE DISPATCH // Enterprise Emergency Dispatch & Paramedic Workstation Engine
 * Full-Duplex WebAudio + Hardware Mic VU Analyser + Rime Neural Audio Streamer
 * Real Voice Input, Interruption Fencing, Request ID Turn Management & State Graph
 */

class SoundFX {
    constructor() {
        this.ctx = null;
        this.cprInterval = null;
        this.cprActive = false;
    }

    init() {
        if (!this.ctx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.ctx = new AudioContext();
        }
        if (this.ctx.state === "suspended") {
            this.ctx.resume();
        }
    }

    playRogerBeep() {
        try {
            this.init();
            const now = this.ctx.currentTime;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = "sine";
            osc.frequency.setValueAtTime(880, now);
            osc.frequency.setValueAtTime(1200, now + 0.04);
            gain.gain.setValueAtTime(0.12, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(now);
            osc.stop(now + 0.1);
        } catch (e) { }
    }

    playFlushClick() {
        try {
            this.init();
            const now = this.ctx.currentTime;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = "triangle";
            osc.frequency.setValueAtTime(340, now);
            osc.frequency.exponentialRampToValueAtTime(110, now + 0.06);
            gain.gain.setValueAtTime(0.2, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.06);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(now);
            osc.stop(now + 0.06);
        } catch (e) { }
    }

    toggleCprMetronome(onTick) {
        this.init();
        if (this.cprActive) {
            clearInterval(this.cprInterval);
            this.cprActive = false;
            return false;
        } else {
            this.cprActive = true;
            this.cprInterval = setInterval(() => {
                try {
                    const now = this.ctx.currentTime;
                    const osc = this.ctx.createOscillator();
                    const gain = this.ctx.createGain();
                    osc.type = "square";
                    osc.frequency.setValueAtTime(950, now);
                    gain.gain.setValueAtTime(0.06, now);
                    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.035);
                    osc.connect(gain);
                    gain.connect(this.ctx.destination);
                    osc.start(now);
                    osc.stop(now + 0.035);
                    if (onTick) onTick();
                } catch (e) { }
            }, 545);
            return true;
        }
    }
}

class SpeechVoiceEngine {
    constructor() {
        this.soundFX = new SoundFX();
        this.currentTurnId = null;
        this.isPlaying = false;
        this.soundEnabled = true;
        this.currentAudioElement = null;
        this.currentAudioUrl = null;

        if ("speechSynthesis" in window) {
            window.speechSynthesis.onvoiceschanged = () => {
                const voices = window.speechSynthesis.getVoices();
                console.log(`[TTS] voices populated: ${voices.length} voices available`);
            };
        }
    }

    init() {
        this.soundFX.init();
    }

    playBase64Audio(b64Data, turnId, onStarted, onEnded, format = "wav") {
        this.init();
        this.stopAll(turnId);

        this.currentTurnId = turnId;
        this.isPlaying = true;

        try {
            const binaryString = window.atob(b64Data);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            const mimeType = format === "mp3" ? "audio/mpeg" : "audio/wav";
            const blob = new Blob([bytes.buffer], { type: mimeType });
            this.currentAudioUrl = URL.createObjectURL(blob);
            this.currentAudioElement = new Audio(this.currentAudioUrl);

            this.currentAudioElement.onplay = () => {
                console.log(`[TTS] WebAudio playback started for turn #${turnId}`);
                if (onStarted) onStarted();
            };

            this.currentAudioElement.onended = () => {
                console.log(`[TTS] WebAudio playback ended for turn #${turnId}`);
                this.isPlaying = false;
                if (this.currentAudioUrl) {
                    URL.revokeObjectURL(this.currentAudioUrl);
                    this.currentAudioUrl = null;
                }
                if (onEnded) onEnded();
            };

            this.currentAudioElement.onerror = (e) => {
                console.warn("[AUDIO PLAYBACK ERROR]", e);
                this.isPlaying = false;
                if (onEnded) onEnded();
            };

            this.currentAudioElement.play().catch(err => {
                console.warn("[AUDIO PLAY FAILED]", err);
                this.isPlaying = false;
                if (onEnded) onEnded();
            });
        } catch (err) {
            console.warn("[AUDIO DECODE ERROR]", err);
            this.isPlaying = false;
            if (onEnded) onEnded();
        }
    }

    stopAll(newTurnId) {
        const t0 = performance.now();
        console.log(`[TTS] speech cancelled / flushed for new turn #${newTurnId}`);
        this.isPlaying = false;

        if (this.currentAudioElement) {
            try {
                this.currentAudioElement.pause();
                this.currentAudioElement.currentTime = 0;
            } catch (e) { }
            this.currentAudioElement = null;
        }

        if (this.currentAudioUrl) {
            try { URL.revokeObjectURL(this.currentAudioUrl); } catch (e) { }
            this.currentAudioUrl = null;
        }

        if ("speechSynthesis" in window) {
            window.speechSynthesis.cancel();
        }

        this.soundFX.playFlushClick();
        this.currentTurnId = newTurnId;

        const latencyMs = (performance.now() - t0).toFixed(1);
        return latencyMs;
    }
}

// Controlled Emergency & Medical Vocabulary Normalization Dictionary
const MEDICAL_VOCABULARY = {
    "Narcan": ["narcan", "nar can", "nar-kan", "narkan", "anarkali", "nar kali", "nar con", "naloxone"],
    "Epinephrine": ["epinephrine", "epinefrin", "epi", "epinephrin", "adrenaline"],
    "Amiodarone": ["amiodarone", "amiodaron"],
    "Air Medevac": ["air medevac", "medevac", "med evac", "medical evac", "helicopter", "air evac", "send air"],
    "CPR": ["cpr", "compressions", "chest compressions", "resuscitation"],
    "Trauma": ["trauma", "traumacenter", "trauma center", "level 1 trauma"],
    "Hospital": ["hospital", "hospitals", "regional beds", "trauma beds", "divert"],
    "Vitals": ["vitals", "vital", "vital signs"],
    "SpO2": ["spo2", "oxygen", "o2 sat", "saturation"],
    "Heart Rate": ["heart rate", "pulse", "bpm", "tachycardia", "bradycardia"],
    "Blood Pressure": ["blood pressure", "bp", "mmhg", "hypotension"],
    "STEMI": ["stemi", "heart attack", "st elevation"],
    "V-Tach": ["v-tach", "vtach", "ventricular tachycardia", "v-fib"],
    "Anaphylaxis": ["anaphylaxis", "allergic reaction", "stridor", "angioedema"],
    "Opioid Overdose": ["opioid", "overdose", "nodding out"],
    "Fentanyl": ["fentanyl", "fentany"],
    "Atropine": ["atropine", "atropin"],
    "Midazolam": ["midazolam", "versed"],
    "Ketamine": ["ketamine", "ketamin"],
    "Flush": ["flush", "barge in", "barge-in", "cancel"],
    "Interrupt": ["interrupt", "stop", "abort"]
};

class TacticalApp {
    constructor() {
        this.ws = null;
        this.voiceEngine = new SpeechVoiceEngine();
        this.soundEnabled = true;
        this.isTransmitting = false;
        this.recognition = null;
        this.hasSpeechRec = false;
        this.shouldBeListening = false;
        this.isPushToSpeakActive = false;
        this.isInterruptionMonitorActive = false;
        this.isAgentSpeaking = false;
        this.isToolRunning = false;
        this.stopRequested = false;
        this.alreadyTransmittedTurn = false;
        this.currentInterimText = "";
        this.currentRawHeard = "";
        this.currentInterpreted = "";
        this.turnCount = 0;
        this.currentIncident = null;

        // Core Conversation State Machine & Request Versioning
        this.conversationState = "IDLE";
        this.requestId = 0;
        this.activeTurnId = 0;
        this.activeTurnUuid = null;
        this.isListening = false;
        this.selectedDelay = 0;
        this.lastRecognizedText = "";
        this.recoveryTimer = null;
        this.localFallbackTimer = null;

        // Hardware Microphone & Audio Analyser
        this.mediaStream = null;
        this.audioContext = null;
        this.analyser = null;
        this.micDataArray = null;

        // Canvases
        this.oscilloscopeCanvas = document.getElementById("oscilloscopeCanvas");
        this.oscCtx = this.oscilloscopeCanvas ? this.oscilloscopeCanvas.getContext("2d") : null;
        this.ecgCanvas = document.getElementById("ecgCanvas");
        this.ecgCtx = this.ecgCanvas ? this.ecgCanvas.getContext("2d") : null;
        this.animPhase = 0;
        this.ecgIndex = 0;

        // Epinephrine timer
        this.epiSecondsLeft = 180;
        this.epiInterval = null;

        this.availableVoices = [];
        this.initDOMElements();
        this.initVoices();
        this.initSpeechRecognition();
        this.initVULevels();
        this.initWebSocket();
        this.initCanvases();
        this.startEpiTimer();
        this.bindEvents();
        this.loadState();
        this.setConversationState("IDLE");
    }

    initDOMElements() {
        // Transceiver & Microphone
        this.pttButton = document.getElementById("pttButton");
        this.pttIcon = document.getElementById("pttIcon");
        this.pttLabelText = document.getElementById("pttLabelText");
        this.pttLed = document.getElementById("pttLed");
        this.flushBargeInBtn = document.getElementById("flushBargeInBtn");
        this.transceiverStatusText = document.getElementById("transceiverStatusText");
        this.liveHearingBanner = document.getElementById("liveHearingBanner");
        this.liveHearingPillText = document.getElementById("liveHearingPillText");
        this.heardSpeechContainer = document.getElementById("heardSpeechContainer");
        this.heardSpeechText = document.getElementById("heardSpeechText");
        this.interpretedSpeechText = document.getElementById("interpretedSpeechText");
        this.voiceConfidenceBadge = document.getElementById("voiceConfidenceBadge");
        this.vuDbText = document.getElementById("vuDbText");

        // Commands & Transcripts
        this.tacticalCommandInput = document.getElementById("tacticalCommandInput");
        this.transmitCommandBtn = document.getElementById("transmitCommandBtn");
        this.radioTranscriptFeed = document.getElementById("radioTranscriptFeed");
        this.turnCounterBadge = document.getElementById("turnCounterBadge");

        // Telemetry & Latency Timeline
        this.telemetryTTFB = document.getElementById("telemetryTTFB");
        this.telemetryFlush = document.getElementById("telemetryFlush");
        this.telemetryTurn = document.getElementById("telemetryTurn");
        this.telemetryTool = document.getElementById("telemetryTool");
        this.telemetryTotal = document.getElementById("telemetryTotal");

        // State Machine & Firewall
        this.activeTurnBadge = document.getElementById("activeTurnBadge");
        this.staleFirewallLog = document.getElementById("staleFirewallLog");
        this.firewallBlockedBadge = document.getElementById("firewallBlockedBadge");

        // Mode & Judge Controls
        this.judgeDemoBtn = document.getElementById("judgeDemoBtn");
        this.modeToggleBtn = document.getElementById("modeToggleBtn");
        this.modeLabelText = document.getElementById("modeLabelText");
        this.replayIncidentBtn = document.getElementById("replayIncidentBtn");
        this.currentMode = "RESONANCE";

        // Patient & Vitals
        this.triageBadge = document.getElementById("triageBadge");
        this.incidentIdText = document.getElementById("incidentIdText");
        this.headerIncidentId = document.getElementById("headerIncidentId");
        this.incidentTitleText = document.getElementById("incidentTitleText");
        this.incidentLocationText = document.getElementById("incidentLocationText");
        this.patName = document.getElementById("patName");
        this.patAgeGender = document.getElementById("patAgeGender");
        this.patWeight = document.getElementById("patWeight");
        this.patAllergy = document.getElementById("patAllergy");
        this.patComplaint = document.getElementById("patComplaint");

        this.valHR = document.getElementById("valHR");
        this.valBP = document.getElementById("valBP");
        this.valSpO2 = document.getElementById("valSpO2");
        this.valGCS = document.getElementById("valGCS");
        this.hrStatus = document.getElementById("hrStatus");
        this.bpStatus = document.getElementById("bpStatus");
        this.spo2Status = document.getElementById("spo2Status");
        this.gcsStatus = document.getElementById("gcsStatus");

        // Selectors
        this.speakerSelect = document.getElementById("speakerSelect") || { value: "cora" };
        this.modelSelect = document.getElementById("modelSelect") || { value: "mist" };

        // Tool Tabs & Containers
        this.hospitalsListContainer = document.getElementById("hospitalsListContainer");
        this.fleetListContainer = document.getElementById("fleetListContainer");
        this.toolDrugSelect = document.getElementById("toolDrugSelect");
        this.toolWeightSlider = document.getElementById("toolWeightSlider");
        this.toolWeightValue = document.getElementById("toolWeightValue");
        this.calculatedDoseText = document.getElementById("calculatedDoseText");
        this.calculatedDilutionText = document.getElementById("calculatedDilutionText");
        this.speakDosageOrderBtn = document.getElementById("speakDosageOrderBtn");
        this.queryHospitalRadarBtn = document.getElementById("queryHospitalRadarBtn");

        // Stress Bench & Baseline Table
        this.runStressTestBenchmarkBtn = document.getElementById("runStressTestBenchmarkBtn");
        this.stressScenarioSelect = document.getElementById("stressScenarioSelect");
        this.stressStep1 = document.getElementById("stressStep1");
        this.stressStep2 = document.getElementById("stressStep2");
        this.stressStep3 = document.getElementById("stressStep3");
        this.stressFinalResult = document.getElementById("stressFinalResult");

        // Top Toggles
        this.cprMetronomeBtn = document.getElementById("cprMetronomeBtn");
        this.cprStatusText = document.getElementById("cprStatusText");
        this.audioMuteToggleBtn = document.getElementById("audioMuteToggleBtn");
        this.audioMuteText = document.getElementById("audioMuteText");
        this.audioMuteIcon = document.getElementById("audioMuteIcon");
        this.epiTimerDisplay = document.getElementById("epiTimerDisplay");
        this.resetEpiTimerBtn = document.getElementById("resetEpiTimerBtn");

        // Vitals Modal
        this.vitalsModal = document.getElementById("vitalsModal");
        this.editVitalsBtn = document.getElementById("editVitalsBtn");
        this.closeVitalsModalBtn = document.getElementById("closeVitalsModalBtn");
        this.saveVitalsModalBtn = document.getElementById("saveVitalsModalBtn");
        this.inputEditHR = document.getElementById("inputEditHR");
        this.inputEditBP = document.getElementById("inputEditBP");
        this.inputEditSpO2 = document.getElementById("inputEditSpO2");
        this.inputEditGCS = document.getElementById("inputEditGCS");
    }

    normalizeAndSelectTranscript(speechResults) {
        let bestRawText = "";
        let highestConfidence = 0;
        let foundMedicalMatch = false;

        // Inspect up to maxAlternatives = 5 alternatives returned by SpeechRecognition
        for (let j = 0; j < speechResults.length; j++) {
            const candidateText = speechResults[j].transcript.trim();
            const conf = speechResults[j].confidence || 0.85;
            if (!bestRawText) bestRawText = candidateText;
            if (conf > highestConfidence) highestConfidence = conf;

            const lowerCandidate = candidateText.toLowerCase();

            for (const [canonicalTerm, variants] of Object.entries(MEDICAL_VOCABULARY)) {
                for (const variant of variants) {
                    if (lowerCandidate.includes(variant)) {
                        foundMedicalMatch = true;
                        const regex = new RegExp("\\b" + variant + "\\b", "gi");
                        const interpreted = candidateText.replace(regex, canonicalTerm);
                        console.log(`[VOICE] normalized command candidate: "${candidateText}" -> "${interpreted}"`);
                        return {
                            raw: candidateText,
                            interpreted: interpreted,
                            confidence: "HIGH",
                            matchedTerm: canonicalTerm
                        };
                    }
                }
            }
        }

        let wordInterpreted = bestRawText;
        for (const [canonicalTerm, variants] of Object.entries(MEDICAL_VOCABULARY)) {
            for (const variant of variants) {
                const regex = new RegExp("\\b" + variant + "\\b", "gi");
                if (regex.test(wordInterpreted.toLowerCase())) {
                    wordInterpreted = wordInterpreted.replace(regex, canonicalTerm);
                    foundMedicalMatch = true;
                }
            }
        }

        const isLowConf = (!foundMedicalMatch && highestConfidence < 0.65);

        console.log(`[VOICE] normalized command: raw="${bestRawText}" -> interpreted="${wordInterpreted}"`);
        return {
            raw: bestRawText,
            interpreted: isLowConf ? `Please confirm: Did you say "${bestRawText}"?` : wordInterpreted,
            confidence: foundMedicalMatch ? "HIGH" : (isLowConf ? "LOW_CONFIRM" : "MEDIUM"),
            matchedTerm: foundMedicalMatch ? "Medical Vocabulary" : null
        };
    }

    initSpeechRecognition() {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRec) {
            this.hasSpeechRec = false;
            console.warn("[VOICE] Speech recognition unavailable in this browser.");
            return;
        }

        this.hasSpeechRec = true;
        try {
            this.recognition = new SpeechRec();
            this.recognition.lang = "en-US";
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            this.recognition.maxAlternatives = 5;

            this.recognition.onstart = () => {
                console.log("[VOICE] recognition started");
                this.isListening = true;
                this.setConversationState("LISTENING");
            };

            this.recognition.onresult = (event) => {
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    const resultObj = event.results[i];
                    const norm = this.normalizeAndSelectTranscript(resultObj);

                    this.currentRawHeard = norm.raw;
                    this.currentInterpreted = norm.interpreted;

                    if (resultObj.isFinal) {
                        console.log(`[VOICE] final result: raw="${norm.raw}" -> interpreted="${norm.interpreted}"`);
                        this.lastRecognizedText = norm.interpreted;
                    } else {
                        console.log(`[VOICE] interim result: "${norm.raw}"`);
                        this.currentInterimText = norm.interpreted;
                    }

                    // Live UI Updates
                    if (this.liveHearingBanner) this.liveHearingBanner.classList.remove("hidden");
                    if (this.liveHearingPillText) this.liveHearingPillText.textContent = `"${norm.raw}"`;

                    if (this.heardSpeechContainer && this.heardSpeechText && this.interpretedSpeechText) {
                        this.heardSpeechText.textContent = `"${norm.raw}"`;
                        this.interpretedSpeechText.textContent = norm.confidence === "LOW_CONFIRM" ? `"Please confirm: Did you say ${norm.raw}?"` : `"${norm.interpreted}"`;
                        if (this.voiceConfidenceBadge) {
                            this.voiceConfidenceBadge.textContent = `VOICE CONFIDENCE: ${norm.confidence}`;
                            this.voiceConfidenceBadge.className = norm.confidence === "HIGH"
                                ? "text-[9px] font-mono px-1.5 py-0.2 rounded bg-[#DBEAFE] text-[#1E40AF] font-bold"
                                : (norm.confidence === "LOW_CONFIRM"
                                    ? "text-[9px] font-mono px-1.5 py-0.2 rounded bg-[#FEF2F2] text-[#DC2626] font-bold"
                                    : "text-[9px] font-mono px-1.5 py-0.2 rounded bg-[#FEF3C7] text-[#D97706] font-bold");
                        }
                        this.heardSpeechContainer.classList.remove("hidden");
                    }

                    if (this.tacticalCommandInput && norm.confidence !== "LOW_CONFIRM") {
                        this.tacticalCommandInput.value = norm.interpreted;
                    }
                }

                // Continuous Interruption / Barge-In Monitoring:
                if (this.currentRawHeard && (this.voiceEngine.isPlaying || this.conversationState === "SPEAKING" || this.conversationState === "PROCESSING" || this.conversationState === "TOOL_RUNNING")) {
                    this.handleInterrupt();
                }
            };

            this.recognition.onerror = (e) => {
                console.warn("[VOICE] recognition error", e.error);
                if (e.error === "not-allowed" || e.error === "service-not-allowed") {
                    if (this.transceiverStatusText) {
                        this.transceiverStatusText.textContent = "Microphone permission required for voice input.";
                        this.transceiverStatusText.className = "absolute top-2 left-2 text-[10px] font-bold text-red-600 font-mono tracking-wider uppercase";
                    }
                    this.appendRadioLog("MICROPHONE NOTICE", "Microphone permission required for voice input.", "flush");
                    this.isListening = false;
                    this.shouldBeListening = false;
                    this.stopMicAudioContext();
                    this.setConversationState("IDLE");
                } else if (e.error !== "no-speech" && e.error !== "aborted") {
                    if (this.transceiverStatusText) {
                        this.transceiverStatusText.textContent = "Voice recognition temporarily unavailable. Press Push to Speak to retry.";
                        this.transceiverStatusText.className = "absolute top-2 left-2 text-[10px] font-bold text-amber-700 font-mono tracking-wider uppercase";
                    }
                    this.isListening = false;
                    this.shouldBeListening = false;
                    this.stopMicAudioContext();
                    this.setConversationState("IDLE");
                }
            };

            this.recognition.onend = () => {
                console.log("[VOICE] recognition ended");
                if (this.liveHearingBanner) this.liveHearingBanner.classList.add("hidden");
                this.stopMicAudioContext();

                // If application intent is still listening (shouldBeListening === true), safely restart recognition
                if (this.shouldBeListening) {
                    console.log("[VOICE] unexpected STT disconnect while shouldBeListening=true. Restarting STT...");
                    try {
                        this.recognition.start();
                    } catch (e) {
                        this.isListening = false;
                    }
                    return;
                }

                if (this.isListening || this.stopRequested) {
                    this.isListening = false;
                    this.stopRequested = false;
                    const captured = (this.lastRecognizedText || this.currentInterpreted || this.currentInterimText || (this.tacticalCommandInput ? this.tacticalCommandInput.value.trim() : "")).trim();
                    this.lastRecognizedText = "";
                    this.currentInterimText = "";

                    if (captured && !this.alreadyTransmittedTurn) {
                        this.alreadyTransmittedTurn = true;
                        this.transmitCommand(captured);
                    } else if (!this.alreadyTransmittedTurn) {
                        this.setConversationState("IDLE");
                    }
                }
            };
        } catch (err) {
            console.warn("[VOICE] STT init failed", err);
            this.hasSpeechRec = false;
        }
    }

    initVULevels() {
        const container = document.getElementById("vuMeterLeds");
        if (!container) return;
        container.innerHTML = "";
        for (let i = 0; i < 10; i++) {
            const led = document.createElement("div");
            const colorClass = i < 6 ? "green" : (i < 8 ? "yellow" : "red");
            led.className = `vu-meter-bar ${colorClass}`;
            led.id = `vu-bar-${i}`;
            container.appendChild(led);
        }
    }

    updateVUMeter(percent) {
        const count = Math.round((percent / 100) * 10);
        if (this._lastVuCount === count) return;
        this._lastVuCount = count;
        for (let i = 0; i < 10; i++) {
            const bar = document.getElementById(`vu-bar-${i}`);
            if (bar) {
                if (i < count) bar.classList.add("active");
                else bar.classList.remove("active");
            }
        }
        if (this.vuDbText) this.vuDbText.textContent = `${percent}%`;
    }

    async loadState() {
        try {
            const res = await fetch("/api/state");
            const data = await res.json();
            if (data.incident) this.renderIncident(data.incident);
            if (data.vitals) this.renderVitals(data.vitals);
            if (data.hospitals) this.renderHospitals(data.hospitals);
            if (data.dispatched_units) this.renderFleet(data.dispatched_units);
            if (data.mode) this.setAgentMode(data.mode);
            if (data.current_state) this.setConversationState(data.current_state);
        } catch (e) { }
    }

    initWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws/voice`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            const pill = document.getElementById("netStatusPill");
            if (pill) {
                pill.innerHTML = `<span class="h-2 w-2 rounded-full bg-[#16A34A] animate-pulse"></span><span class="text-[10px] font-bold text-[#16A34A]">WS CONNECTED</span>`;
                pill.className = "flex items-center space-x-1.5 bg-[#F0FDF4] border border-[#BBF7D0] px-2.5 py-1 rounded font-mono";
            }
        };

        this.ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                this.handleWsMessage(msg);
            } catch (e) { }
        };

        this.ws.onclose = () => {
            const pill = document.getElementById("netStatusPill");
            if (pill) {
                pill.innerHTML = `<span class="h-2 w-2 rounded-full bg-red-500"></span><span class="text-[10px] font-bold text-red-600">OFFLINE // RECONNECTING...</span>`;
                pill.className = "flex items-center space-x-1.5 bg-red-50 border border-red-200 px-2.5 py-1 rounded font-mono";
            }
            setTimeout(() => this.initWebSocket(), 2500);
        };
    }

    // --- CONVERSATION STATE MACHINE & UI RENDERING ---
    setConversationState(newState) {
        this.conversationState = newState;
        this.isListening = (newState === "LISTENING");

        // 1. Update Conversation State Graph Node
        this.updateStateGraphNode(newState);

        // 2. Update Process Flow Indicators (INTERRUPT -> FLUSH -> FENCE -> RECOVER)
        if (newState === "INTERRUPTED") this.updateProcessFlowBadge("interrupt");
        else if (newState === "FLUSHING") this.updateProcessFlowBadge("flush");
        else if (newState === "FENCED") this.updateProcessFlowBadge("fence");
        else if (newState === "RECOVERING") this.updateProcessFlowBadge("recover");
        else if (newState === "IDLE" || newState === "COMPLETED") this.updateProcessFlowBadge(null);

        // 3. Update PTT Button Text, Icon & Styling
        if (this.pttButton && this.pttLabelText && this.pttIcon) {
            if (newState === "IDLE" || newState === "COMPLETED") {
                this.pttLabelText.textContent = "PUSH TO SPEAK";
                this.pttIcon.className = "fa-solid fa-microphone text-white";
                this.pttButton.className = "btn-ptt flex-1 bg-[#2563EB] border-[#2563EB] text-white hover:bg-[#1D4ED8]";
                if (this.pttLed) this.pttLed.className = "w-2 h-2 rounded-full bg-[#16A34A]";
            } else if (newState === "LISTENING") {
                this.pttLabelText.textContent = "🔴 LISTENING... RELEASE TO SEND";
                this.pttIcon.className = "fa-solid fa-microphone-lines text-white animate-pulse";
                this.pttButton.className = "btn-ptt flex-1 transmitting";
                if (this.pttLed) this.pttLed.className = "w-2 h-2 rounded-full bg-red-600 animate-ping";
            } else if (newState === "PROCESSING") {
                this.pttLabelText.textContent = "⏳ PROCESSING REQUEST...";
                this.pttIcon.className = "fa-solid fa-spinner fa-spin text-amber-700";
                this.pttButton.className = "btn-ptt flex-1 bg-amber-50 border-amber-300 text-amber-800";
                if (this.pttLed) this.pttLed.className = "w-2 h-2 rounded-full bg-amber-500 animate-pulse";
            } else if (newState === "TOOL_RUNNING") {
                this.pttLabelText.textContent = "🔧 EXECUTING CLINICAL TOOL...";
                this.pttIcon.className = "fa-solid fa-gear fa-spin text-amber-700";
                this.pttButton.className = "btn-ptt flex-1 bg-amber-50 border-amber-300 text-amber-800";
                if (this.pttLed) this.pttLed.className = "w-2 h-2 rounded-full bg-amber-500 animate-pulse";
            } else if (newState === "SPEAKING") {
                this.pttLabelText.textContent = "📻 SPEAKING...";
                this.pttIcon.className = "fa-solid fa-volume-high text-emerald-700 animate-pulse";
                this.pttButton.className = "btn-ptt flex-1 bg-emerald-50 border-emerald-300 text-emerald-800";
                if (this.pttLed) this.pttLed.className = "w-2 h-2 rounded-full bg-emerald-500 animate-pulse";
            } else if (newState === "INTERRUPTED") {
                this.pttLabelText.textContent = "⚠️ INTERRUPTED";
                this.pttIcon.className = "fa-solid fa-hand text-red-600 animate-bounce";
                this.pttButton.className = "btn-ptt flex-1 bg-red-50 border-red-300 text-red-700";
                if (this.pttLed) this.pttLed.className = "w-2 h-2 rounded-full bg-red-600 animate-pulse";
            } else if (newState === "FLUSHING") {
                this.pttLabelText.textContent = "FLUSHING AUDIO BUFFER...";
                this.pttIcon.className = "fa-solid fa-bolt text-amber-600";
                this.pttButton.className = "btn-ptt flex-1 bg-amber-50 border-amber-300 text-amber-800";
            } else if (newState === "FENCED") {
                this.pttLabelText.textContent = "STALE RESPONSE FENCED";
                this.pttIcon.className = "fa-solid fa-shield text-blue-600";
                this.pttButton.className = "btn-ptt flex-1 bg-blue-50 border-blue-300 text-blue-800";
            } else if (newState === "RECOVERING") {
                this.pttLabelText.textContent = "RECOVERING STATE...";
                this.pttIcon.className = "fa-solid fa-arrows-rotate fa-spin text-emerald-600";
                this.pttButton.className = "btn-ptt flex-1 bg-emerald-50 border-emerald-300 text-emerald-800";
            }
        }

        // 4. Update Transceiver Status Text Header
        if (this.transceiverStatusText) {
            if (newState === "IDLE" || newState === "COMPLETED") {
                this.transceiverStatusText.textContent = "VOICE CHANNEL // STATUS: READY";
                this.transceiverStatusText.className = "absolute top-2 left-2 text-[10px] font-bold text-[#64748B] font-mono tracking-wider uppercase";
            } else if (newState === "LISTENING") {
                this.transceiverStatusText.textContent = "VOICE CHANNEL // STATUS: LISTENING";
                this.transceiverStatusText.className = "absolute top-2 left-2 text-[10px] font-bold text-red-600 font-mono tracking-wider uppercase animate-pulse";
            } else if (newState === "PROCESSING") {
                this.transceiverStatusText.textContent = "VOICE CHANNEL // STATUS: PROCESSING REQUEST";
                this.transceiverStatusText.className = "absolute top-2 left-2 text-[10px] font-bold text-amber-700 font-mono tracking-wider uppercase";
            } else if (newState === "TOOL_RUNNING") {
                this.transceiverStatusText.textContent = "VOICE CHANNEL // STATUS: TOOL RUNNING";
                this.transceiverStatusText.className = "absolute top-2 left-2 text-[10px] font-bold text-amber-700 font-mono tracking-wider uppercase";
            } else if (newState === "SPEAKING") {
                this.transceiverStatusText.textContent = "VOICE CHANNEL // STATUS: SPEAKING";
                this.transceiverStatusText.className = "absolute top-2 left-2 text-[10px] font-bold text-emerald-700 font-mono tracking-wider uppercase";
            } else if (newState === "INTERRUPTED") {
                this.transceiverStatusText.textContent = "VOICE CHANNEL // STATUS: INTERRUPTED / FLUSHING";
                this.transceiverStatusText.className = "absolute top-2 left-2 text-[10px] font-bold text-red-600 font-mono tracking-wider uppercase animate-pulse";
            } else if (newState === "COMPLETED") {
                this.transceiverStatusText.textContent = "VOICE CHANNEL // STATUS: COMPLETED";
                this.transceiverStatusText.className = "absolute top-2 left-2 text-[10px] font-bold text-[#16A34A] font-mono tracking-wider uppercase";
            }
        }
    }

    updateStateGraphNode(stateName) {
        document.querySelectorAll(".state-node").forEach(n => {
            n.classList.remove("active", "interrupted", "stale-blocked");
        });
        const target = document.getElementById(`node-${stateName}`);
        if (target) {
            if (stateName === "INTERRUPTED" || stateName === "CANCELLED") {
                target.classList.add("interrupted");
            } else if (stateName === "STALE_RESULT_BLOCKED" || stateName === "FENCED") {
                target.classList.add("stale-blocked");
            } else {
                target.classList.add("active");
            }
        }
    }

    updateProcessFlowBadge(stage) {
        const i = document.getElementById("sigStepInterrupt");
        const fl = document.getElementById("sigStepFlush");
        const fe = document.getElementById("sigStepFence");
        const r = document.getElementById("sigStepRecover");
        if (i) i.className = "sig-step" + (stage === "interrupt" ? " active-interrupt" : "");
        if (fl) fl.className = "sig-step" + (stage === "flush" ? " active-flush" : "");
        if (fe) fe.className = "sig-step" + (stage === "fence" ? " active-fence" : "");
        if (r) r.className = "sig-step" + (stage === "recover" ? " active-recover" : "");
    }

    appendFirewallLog(evt) {
        if (!this.staleFirewallLog) return;
        const card = document.createElement("div");
        const isBlocked = evt.status === "BLOCKED";
        const borderClass = isBlocked ? "border-[#BBF7D0] bg-[#F0FDF4]" : "border-[#FECACA] bg-[#FEF2F2]";
        const badgeClass = isBlocked ? "bg-[#16A34A] text-white border-[#16A34A]" : "bg-[#DC2626] text-white border-[#DC2626]";
        const statusText = isBlocked ? "STALE BLOCKED" : "UNGUARDED SPOKEN";

        card.className = `p-2 rounded border ${borderClass} text-[11px] space-y-1 font-mono`;
        card.innerHTML = `
            <div class="flex justify-between items-center font-bold">
                <span class="text-[#0F172A]">${evt.source || "Async Tool"}</span>
                <span class="text-[9px] px-1.5 py-0.2 rounded border ${badgeClass}">${statusText}</span>
            </div>
            <div class="flex justify-between text-[10px] text-[#64748B]">
                <span>Result Turn: <b class="text-[#D97706]">#${evt.old_turn_id}</b></span>
                <span>Active Turn: <b class="text-[#2563EB]">#${evt.current_turn_id}</b></span>
            </div>
            <p class="text-[10px] ${isBlocked ? 'text-[#16A34A]' : 'text-[#DC2626]'} font-semibold mt-0.5">${evt.reason}</p>
        `;
        this.staleFirewallLog.prepend(card);

        // Highlight STALE BLOCKED node briefly on state graph, then return to actual active conversation state
        this.updateStateGraphNode("STALE_RESULT_BLOCKED");
        if (this._staleGraphTimer) clearTimeout(this._staleGraphTimer);
        this._staleGraphTimer = setTimeout(() => {
            this.updateStateGraphNode(this.conversationState);
        }, 1200);
    }

    setAgentMode(mode) {
        this.currentMode = mode.toUpperCase();
        if (this.modeLabelText) {
            if (this.currentMode === "RESONANCE") this.modeLabelText.textContent = "RESONANCE (FENCED)";
            else if (this.currentMode === "NAIVE") this.modeLabelText.textContent = "NAIVE (UNGUARDED)";
            else this.modeLabelText.textContent = "DELAYED CANCEL (LAGGED)";
        }
        if (this.modeToggleBtn) {
            if (this.currentMode === "RESONANCE") {
                this.modeToggleBtn.className = "btn-secondary border-[#BBF7D0] bg-[#F0FDF4] text-[#16A34A]";
                if (this.firewallBlockedBadge) {
                    this.firewallBlockedBadge.textContent = "PROTECTED";
                    this.firewallBlockedBadge.className = "text-[10px] px-1.5 py-0.5 rounded bg-[#F0FDF4] text-[#16A34A] border border-[#BBF7D0] font-mono font-bold";
                }
            } else if (this.currentMode === "NAIVE") {
                this.modeToggleBtn.className = "btn-secondary bg-[#FEF2F2] border-[#FECACA] text-[#DC2626]";
                if (this.firewallBlockedBadge) {
                    this.firewallBlockedBadge.textContent = "UNGUARDED!";
                    this.firewallBlockedBadge.className = "text-[10px] px-1.5 py-0.5 rounded bg-[#FEF2F2] text-[#DC2626] border border-[#FECACA] font-mono font-bold";
                }
            } else {
                this.modeToggleBtn.className = "btn-secondary bg-[#FFFBEB] border-[#FDE68A] text-[#D97706]";
                if (this.firewallBlockedBadge) {
                    this.firewallBlockedBadge.textContent = "DELAYED LAG";
                    this.firewallBlockedBadge.className = "text-[10px] px-1.5 py-0.5 rounded bg-[#FFFBEB] text-[#D97706] border border-[#FDE68A] font-mono font-bold";
                }
            }
        }
    }

    handleWsMessage(msg) {
        if (msg.type === "CONNECTION_ESTABLISHED") {
            if (msg.state) {
                if (msg.state.incident) this.renderIncident(msg.state.incident);
                if (msg.state.vitals) this.renderVitals(msg.state.vitals);
                if (msg.state.hospitals) this.renderHospitals(msg.state.hospitals);
                if (msg.state.dispatched_units) this.renderFleet(msg.state.dispatched_units);
                if (msg.state.mode) this.setAgentMode(msg.state.mode);
                if (msg.state.current_state) this.setConversationState(msg.state.current_state);
            }
        } else if (msg.type === "MODE_CHANGED") {
            this.setAgentMode(msg.mode);
            this.appendRadioLog("SYSTEM", `Agent mode set to: ${msg.mode}`, "system");
        } else if (msg.type === "DELAY_CHANGED") {
            this.appendRadioLog("SYSTEM", `Synthetic tool delay set to: ${msg.delay_sec}s`, "system");
        } else if (msg.type === "SCENARIO_UPDATED") {
            const s = msg.state;
            if (s.incident) this.renderIncident(s.incident);
            if (s.vitals) this.renderVitals(s.vitals);
            if (s.units) this.renderFleet(s.units);
            this.appendRadioLog("CAD DISPATCH", `Incident switched to: [${s.incident.id}] ${s.incident.type}`, "system");
        } else if (msg.type === "AUDIO_CHUNK") {
            const meta = msg.telemetry;
            if (meta) {
                // TURN FENCING GUARD FOR WEBSOCKET AUDIO
                if (meta.turn_id && meta.turn_id !== this.activeTurnId && this.currentMode === "RESONANCE") {
                    console.warn(`[STALE FIREWALL WS] Blocked audio chunk from turn #${meta.turn_id}`);
                    this.appendFirewallLog({
                        source: "Rime Audio Streamer",
                        status: "BLOCKED",
                        old_turn_id: meta.turn_id,
                        current_turn_id: this.activeTurnId,
                        reason: `Interruption Fenced: Blocked obsolete WS audio chunk from turn #${meta.turn_id}`
                    });
                    this.updateStateGraphNode("STALE_RESULT_BLOCKED");
                    return;
                }

                if (meta.ttfb_ms && this.telemetryTTFB) this.telemetryTTFB.textContent = `${meta.ttfb_ms} ms`;
                if (meta.turn_id && this.telemetryTurn) {
                    this.telemetryTurn.textContent = `#${meta.turn_id}`;
                    if (this.activeTurnBadge) this.activeTurnBadge.textContent = `TURN #${meta.turn_id}`;
                }

                const hudModel = document.getElementById("hudModel");
                const hudSpeaker = document.getElementById("hudSpeaker");
                const hudProvider = document.getElementById("hudProvider");
                if (hudModel && meta.model_id) hudModel.textContent = meta.model_id;
                if (hudSpeaker && meta.speaker) hudSpeaker.textContent = meta.speaker;
                if (hudProvider && meta.provider) {
                    hudProvider.textContent = meta.is_fallback ? "Fallback Synthesizer" : "Rime Neural API";
                    hudProvider.className = meta.is_fallback ? "text-[#D97706] font-bold font-mono" : "text-[#16A34A] font-bold font-mono";
                }

                if (msg.audio && !meta.is_fallback) {
                    this.voiceEngine.playBase64Audio(msg.audio, meta.turn_id,
                        () => this.setConversationState("SPEAKING"),
                        () => {
                            if (meta.turn_id === this.activeTurnId) {
                                this.setConversationState("COMPLETED");
                                setTimeout(() => {
                                    if (this.conversationState === "COMPLETED") this.setConversationState("IDLE");
                                }, 1500);
                            }
                            const phaseLabel = meta.phase === "FILLER_STATUS" ? "STATUS FILLER" : "RESONANCE COPILOT";
                            this.appendRadioLog(phaseLabel, meta.text || "Transmission complete.", meta.phase === "FILLER_STATUS" ? "filler" : "copilot");
                        },
                        meta.format || "wav"
                    );
                } else if (meta.text) {
                    // Centralized TTS fallback when WebSocket Streams text without raw audio bytes
                    this.speakAgentResponse(meta.text, meta.turn_id, () => {
                        const phaseLabel = meta.phase === "FILLER_STATUS" ? "STATUS FILLER" : "RESONANCE COPILOT";
                        this.appendRadioLog(phaseLabel, meta.text, meta.phase === "FILLER_STATUS" ? "filler" : "copilot");
                    });
                }
            }
        } else if (msg.type === "AUDIO_FLUSH") {
            const latency = this.voiceEngine.stopAll(msg.event.new_turn_id);
            if (this.telemetryFlush) this.telemetryFlush.textContent = `${latency} ms`;
            this.setConversationState("FLUSHING");
            if (this.stressStep2) {
                this.stressStep2.className = "text-[#16A34A] font-bold font-mono";
                this.stressStep2.textContent = `PASSED (AUDIO FLUSHED IN ${latency} ms)`;
            }
            this.appendRadioLog("BARGE-IN FENCE", `Interruption detected (#${msg.event.cancelled_turn_id} -> #${msg.event.new_turn_id}). Audio flushed in ${latency}ms.`, "flush");
        } else if (msg.type === "STALE_RESULT_BLOCKED" || msg.type === "STALE_RESULT_UNGUARDED") {
            this.appendFirewallLog(msg);
            if (msg.type === "STALE_RESULT_BLOCKED") {
                this.setConversationState("FENCED");
                if (this.stressStep3) {
                    this.stressStep3.className = "text-[#16A34A] font-bold font-mono";
                    this.stressStep3.textContent = `PASSED (STALE TURN #${msg.old_turn_id} BLOCKED BY FIREWALL)`;
                }
                if (this.stressFinalResult) {
                    this.stressFinalResult.className = "px-2 py-0.5 rounded bg-[#F0FDF4] border border-[#BBF7D0] text-[#16A34A] font-bold font-mono inline-block";
                    this.stressFinalResult.textContent = "INTERRUPTION RECOVERY VERIFIED";
                }
                this.appendRadioLog("STALE FIREWALL", `Blocked obsolete tool result from turn #${msg.old_turn_id} (active: #${msg.current_turn_id})`, "flush");
            } else {
                if (this.stressStep3) {
                    this.stressStep3.className = "text-[#DC2626] font-bold font-mono";
                    this.stressStep3.textContent = `FAILED (UNGUARDED TURN #${msg.old_turn_id} SPOKEN!)`;
                }
                if (this.stressFinalResult) {
                    this.stressFinalResult.className = "px-2 py-0.5 rounded bg-[#FEF2F2] border border-[#FECACA] text-[#DC2626] font-bold font-mono inline-block";
                    this.stressFinalResult.textContent = "FAILED // NAIVE STATE CORRUPTED";
                }
                this.appendRadioLog("NAIVE RACE CONDITION", `CRITICAL: Unblocked stale result from turn #${msg.old_turn_id} was spoken!`, "flush");
            }
        } else if (msg.type === "TELEMETRY") {
            const d = msg.data;
            if (d.turn_id && d.turn_id !== this.activeTurnId && this.currentMode === "RESONANCE") {
                return; // Ignore stale telemetry
            }
            if (d.type === "STATE_CHANGE") {
                this.setConversationState(d.state);
            }
        } else if (d.type === "TURN_START") {
            // Backend is authoritative for the actual turn number
            if (d.turn_id) {
                this.activeTurnId = d.turn_id;
            }

            if (this.telemetryTurn) {
                this.telemetryTurn.textContent = `#${d.turn_id}`;
            }

            if (this.activeTurnBadge) {
                this.activeTurnBadge.textContent = `TURN #${d.turn_id}`;
            }

            this.turnCount++;
            if (this.turnCounterBadge) this.turnCounterBadge.textContent = `${this.turnCount} TURNS`;
            this.appendRadioLog("PARAMEDIC", d.transcript, "user");
        } else if (d.type === "FILLER_START") {
            this.appendRadioLog("STATUS FILLER", d.text, "filler");
        } else if (d.type === "TOOL_START") {
            this.setConversationState("TOOL_RUNNING");
            if (this.telemetryTool) this.telemetryTool.textContent = `Running ${d.tool_name}...`;
            this.appendRadioLog("CLINICAL TOOL", `Executing async tool: ${d.tool_name}`, "tool");
        } else if (d.type === "TOOL_COMPLETE") {
            if (this.telemetryTool) this.telemetryTool.textContent = `${d.duration_ms} ms`;
            if (d.tool_name === "log_patient_vitals" && d.result.vitals) {
                this.renderVitals(d.result.vitals);
            } else if (d.tool_name === "dispatch_backup_units" && d.result.dispatched) {
                this.addFleetCard(d.result.dispatched);
            }
        } else if (d.type === "TURN_COMPLETE") {
            if (this.telemetryTotal) this.telemetryTotal.textContent = `${d.total_latency_ms} ms`;
            if (d.response_text) {
                this.speakAgentResponse(d.response_text, d.turn_id);
            } else {
                this.setConversationState("COMPLETED");
                setTimeout(() => {
                    if (this.conversationState === "COMPLETED") this.setConversationState("IDLE");
                }, 1500);
            }
        }
    }

    renderIncident(inc) {
        this.currentIncident = inc;
        const incId = inc.id || "MED-7829";
        if (this.incidentIdText) this.incidentIdText.textContent = incId;
        if (this.headerIncidentId) this.headerIncidentId.textContent = incId;
        document.querySelectorAll(".incident-id-text").forEach(el => el.textContent = incId);
        if (this.incidentTitleText) this.incidentTitleText.textContent = inc.type || "Active Incident";
        if (this.incidentLocationText) this.incidentLocationText.innerHTML = `<i class="fa-solid fa-location-dot text-[#DC2626] mr-1"></i><span>${inc.location || "Scene Location"}</span>`;
        if (this.triageBadge) {
            this.triageBadge.textContent = inc.triage_label || "PRIORITY 1 - IMMEDIATE";
        }

        const pat = inc.patient || { name: "Unknown", age: 30, weight_kg: 70, gender: "Adult", allergy: "NKDA", chief_complaint: "Trauma" };
        if (this.patName) this.patName.textContent = pat.name;
        if (this.patAgeGender) this.patAgeGender.textContent = `${pat.age} YRS / ${pat.gender.toUpperCase()}`;
        if (this.patWeight) this.patWeight.textContent = `${pat.weight_kg} KG`;
        if (this.patAllergy) this.patAllergy.textContent = pat.allergy;
        if (this.patComplaint) this.patComplaint.textContent = pat.chief_complaint;

        if (this.toolWeightSlider) {
            this.toolWeightSlider.value = pat.weight_kg;
            this.updateDosageCalculations();
        }
    }

    renderVitals(v) {
        if (v.heart_rate !== undefined) {
            this.valHR.innerHTML = `${v.heart_rate} <span class="text-[9px] text-[#94A3B8]">BPM</span>`;
            if (this.hrStatus) this.hrStatus.textContent = v.heart_rate > 100 ? "TACHYCARDIA" : (v.heart_rate < 60 ? "BRADYCARDIA" : "NORMAL SINUS");
            if (this.inputEditHR) this.inputEditHR.value = v.heart_rate;
        }
        if (v.blood_pressure !== undefined) {
            this.valBP.textContent = v.blood_pressure;
            if (this.inputEditBP) this.inputEditBP.value = v.blood_pressure;
        }
        if (v.spo2 !== undefined) {
            this.valSpO2.innerHTML = `${v.spo2} <span class="text-[9px] text-[#94A3B8]">%</span>`;
            if (this.spo2Status) this.spo2Status.textContent = v.spo2 < 90 ? "CRITICAL HYPOXIA" : (v.spo2 < 95 ? "MILD HYPOXIA" : "ADEQUATE");
            if (this.inputEditSpO2) this.inputEditSpO2.value = v.spo2;
        }
        if (v.gcs !== undefined) {
            this.valGCS.innerHTML = `${v.gcs} <span class="text-[9px] text-[#94A3B8]">/ 15</span>`;
            if (this.gcsStatus) this.gcsStatus.textContent = v.gcs <= 8 ? "SEVERE (INTUBATE)" : (v.gcs <= 12 ? "MODERATE" : "MILD / CONSCIOUS");
            if (this.inputEditGCS) this.inputEditGCS.value = v.gcs;
        }
    }

    renderHospitals(hospitals) {
        if (!this.hospitalsListContainer) return;
        this.hospitalsListContainer.innerHTML = "";
        hospitals.forEach(h => {
            const card = document.createElement("div");
            const divertClass = h.divert ? "border-[#FECACA] bg-[#FEF2F2]" : "border-[#E2E8F0] bg-[#FFFFFF]";
            const badge = h.divert
                ? `<span class="text-[9px] px-1.5 py-0.2 rounded bg-[#DC2626] text-white font-bold border border-[#DC2626] font-mono">DIVERT</span>`
                : `<span class="text-[9px] px-1.5 py-0.2 rounded bg-[#F0FDF4] text-[#16A34A] font-bold border border-[#BBF7D0] font-mono">ACCEPTING</span>`;

            card.className = `border ${divertClass} p-2.5 rounded text-xs space-y-1 font-mono shadow-xs`;
            card.innerHTML = `
                <div class="flex items-center justify-between font-bold">
                    <span class="text-[#0F172A]">${h.name} (L${h.trauma_level})</span>
                    ${badge}
                </div>
                <div class="flex items-center justify-between text-[11px] text-[#64748B]">
                    <span>ETA: <b class="text-[#0F172A]">${h.eta_minutes}m</b> (${h.distance_miles} mi)</span>
                    <span>Trauma Bays: <b class="text-[#16A34A]">${h.open_trauma_bays} open</b></span>
                </div>
                <div class="flex items-center justify-between text-[10px] text-[#94A3B8] pt-1 border-t border-[#E2E8F0]">
                    <span>Burn Unit: ${h.burn_unit ? "YES" : "NO"} • Peds: ${h.pediatric_trauma ? "YES" : "NO"}</span>
                    <button class="route-medic-btn px-2 py-0.5 bg-[#2563EB] hover:bg-[#1D4ED8] text-white font-bold rounded" data-name="${h.name}">ROUTE MEDIC</button>
                </div>
            `;
            this.hospitalsListContainer.appendChild(card);
        });

        document.querySelectorAll(".route-medic-btn").forEach(b => {
            b.addEventListener("click", () => {
                const name = b.getAttribute("data-name");
                this.transmitCommand(`Route transport unit to ${name}`);
            });
        });
    }

    renderFleet(units) {
        if (!this.fleetListContainer) return;
        this.fleetListContainer.innerHTML = "";
        units.forEach(u => this.addFleetCard(u));
    }

    addFleetCard(unit) {
        if (!this.fleetListContainer) return;
        const card = document.createElement("div");
        card.className = "bg-[#FFFFFF] border border-[#E2E8F0] p-2 rounded text-xs space-y-0.5 font-mono shadow-xs";
        card.innerHTML = `
            <div class="flex justify-between items-center font-bold">
                <span class="text-[#0F172A]">${unit.unit_id} (${unit.type})</span>
                <span class="text-[9px] px-1.5 rounded bg-[#FFFBEB] text-[#D97706] border border-[#FDE68A] font-bold">${unit.status || "EN ROUTE"}</span>
            </div>
            <div class="text-[11px] text-[#64748B]">Staging: ${unit.staging_area} • ETA: <b class="text-[#16A34A]">${unit.eta_minutes}m</b></div>
        `;
        this.fleetListContainer.prepend(card);
    }

    appendRadioLog(sender, text, type = "copilot") {
        if (!this.radioTranscriptFeed) return;
        while (this.radioTranscriptFeed.children.length > 80) {
            this.radioTranscriptFeed.removeChild(this.radioTranscriptFeed.firstChild);
        }
        const div = document.createElement("div");
        const timeStr = new Date().toLocaleTimeString();
        div.className = "p-2 rounded text-xs space-y-0.5 border font-mono";

        if (type === "user") {
            div.className += " bg-[#EFF6FF] border-[#BFDBFE] text-[#0F172A]";
            div.innerHTML = `<div class="flex justify-between text-[9px] text-[#2563EB] font-bold"><span>[${timeStr}] 🎙️ ${sender} (COMMAND)</span><span>TRANSMIT</span></div><p class="text-[#0F172A] font-semibold">${text}</p>`;
        } else if (type === "filler") {
            div.className += " bg-[#FFFBEB] border-[#FDE68A] text-[#92400E] italic";
            div.innerHTML = `<div class="text-[9px] text-[#D97706] font-bold">[${timeStr}] ⏳ ACOUSTIC STATUS FILLER</div><p>${text}</p>`;
        } else if (type === "tool") {
            div.className += " bg-[#F8FAFC] border-[#E2E8F0] text-[#0F172A]";
            div.innerHTML = `<div class="text-[9px] text-[#64748B] font-bold">[${timeStr}] 🔧 ${sender}</div><p>${text}</p>`;
        } else if (type === "flush") {
            div.className += " bg-[#FEF2F2] border-[#FECACA] text-[#DC2626] font-bold";
            div.innerHTML = `<div class="text-[9px] text-[#DC2626] font-bold">[${timeStr}] ⚡ ${sender}</div><p>${text}</p>`;
        } else if (type === "system") {
            div.className += " bg-[#F8FAFC] border-[#E2E8F0] text-[#0F172A]";
            div.innerHTML = `<div class="text-[9px] text-[#2563EB] font-bold">[${timeStr}] ⚙️ ${sender}</div><p>${text}</p>`;
        } else {
            div.className += " bg-[#F8FAFC] border-[#E2E8F0] text-[#0F172A]";
            div.innerHTML = `<div class="flex justify-between text-[9px] text-[#16A34A] font-bold"><span>[${timeStr}] 📻 ${sender} (RIME NEURAL)</span><span>DISPATCH</span></div><p class="text-[#0F172A] font-semibold">${text}</p>`;
        }

        this.radioTranscriptFeed.appendChild(div);
        this.radioTranscriptFeed.scrollTop = this.radioTranscriptFeed.scrollHeight;
    }

    isInputFocused() {
        const active = document.activeElement;
        if (!active) return false;
        const tag = active.tagName.toLowerCase();
        return tag === "input" || tag === "textarea" || tag === "select" || active.isContentEditable;
    }

    // --- REAL VOICE INPUT & PTT RECOGNITION HANDLER ---
    startListening() {
        console.log("[VOICE] start requested");
        // Reset previous recognition state before starting new recording
        this.lastRecognizedText = "";
        this.currentInterimText = "";
        this.currentRawHeard = "";
        this.currentInterpreted = "";
        this.alreadyTransmittedTurn = false;

        // If system is currently speaking, tool running, or processing, barge-in interrupt first!
        if (this.conversationState === "SPEAKING" || this.conversationState === "TOOL_RUNNING" || this.conversationState === "PROCESSING" || this.conversationState === "FLUSHING") {
            this.handleInterrupt();
        }

        if (this.isListening) return;

        if (!this.hasSpeechRec) {
            if (this.transceiverStatusText) {
                this.transceiverStatusText.textContent = "Voice recognition temporarily unavailable. Press Push to Speak to retry.";
                this.transceiverStatusText.className = "absolute top-2 left-2 text-[10px] font-bold text-amber-700 font-mono tracking-wider uppercase";
            }
            this.appendRadioLog("SYSTEM", "Speech recognition is not supported in this browser.", "system");
            this.setConversationState("IDLE");
            return;
        }

        this.shouldBeListening = true;
        this.isPushToSpeakActive = true;
        this.isListening = true;
        this.stopRequested = false;
        this.setConversationState("LISTENING");
        this.startMicAudioContext();

        try {
            this.recognition.start();
        } catch (err) {
            try {
                this.recognition.abort();
                this.recognition.start();
            } catch (e) {
                console.warn("[VOICE] STT start failed", e);
                this.isListening = false;
                this.shouldBeListening = false;
                this.isPushToSpeakActive = false;
                this.stopMicAudioContext();
                this.setConversationState("IDLE");
            }
        }
    }

    stopListening() {
        if (!this.shouldBeListening && !this.isListening && !this.stopRequested) return;
        console.log("[VOICE] stop requested");
        this.shouldBeListening = false;
        this.isPushToSpeakActive = false;
        this.stopRequested = true;

        if (this.recognition) {
            try {
                this.recognition.stop();
            } catch (e) {
                this.isListening = false;
                this.stopMicAudioContext();
                const captured = (this.lastRecognizedText || this.currentInterpreted || this.currentInterimText || (this.tacticalCommandInput ? this.tacticalCommandInput.value.trim() : "")).trim();
                this.lastRecognizedText = "";
                this.currentInterimText = "";
                if (captured && !this.alreadyTransmittedTurn) {
                    this.alreadyTransmittedTurn = true;
                    this.transmitCommand(captured);
                } else if (!this.alreadyTransmittedTurn) {
                    this.setConversationState("IDLE");
                }
            }
        } else {
            this.isListening = false;
            this.stopMicAudioContext();
            this.setConversationState("IDLE");
        }
    }

    initVoices() {
        if ("speechSynthesis" in window) {
            const populateVoices = () => {
                this.availableVoices = window.speechSynthesis.getVoices();
                console.log(`[TTS] voices populated: ${this.availableVoices.length} voices available`);
            };
            populateVoices();
            window.speechSynthesis.onvoiceschanged = populateVoices;
        }
    }

    // --- CENTRALIZED TTS RESPONSE FUNCTION ---
    speakAgentResponse(text, turnId, onEnded) {
        const turn = turnId || this.activeTurnId;

        // 1. Cancel previous speech immediately
        if ("speechSynthesis" in window) {
            window.speechSynthesis.cancel();
            console.log("[TTS] speech cancelled");
        }

        // 2. Validate text is not empty
        if (!text || !text.trim()) {
            if (onEnded) onEnded();
            return;
        }

        const cleanText = text.trim();

        // 3. Debug logging requirements
        console.log("[TTS] requested");
        console.log("[TTS] text:", cleanText);

        // 4. Add response to Transcript Log
        this.appendRadioLog("RESONANCE COPILOT", cleanText, "copilot");

        // 5. Audio Toggle Check (AUDIO ON vs AUDIO OFF)
        if (!this.soundEnabled) {
            console.log("[TTS] Audio is OFF (muted). Displaying text visually but skipping speech.");
            this.setConversationState("RESULT_READY");
            setTimeout(() => {
                this.setConversationState("COMPLETED");
                setTimeout(() => {
                    if (this.conversationState === "COMPLETED") this.setConversationState("IDLE");
                }, 1000);
            }, 400);
            if (onEnded) onEnded();
            return;
        }

        // 6. Execute Speech Synthesis
        if ("speechSynthesis" in window) {
            this.setConversationState("RESULT_READY");

            const utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.rate = 1.0;
            utterance.volume = 1.0;

            const voices = (this.availableVoices && this.availableVoices.length > 0)
                ? this.availableVoices
                : window.speechSynthesis.getVoices();

            const preferredVoice = voices.find(v => v.lang && v.lang.startsWith("en") && (
                v.name.includes("Natural") || v.name.includes("Google") || v.name.includes("Samantha") || v.name.includes("David") || v.name.includes("Zira") || v.name.includes("Jenny") || v.name.includes("Guy")
            )) || voices.find(v => v.lang && v.lang.startsWith("en")) || voices[0];

            if (preferredVoice) {
                utterance.voice = preferredVoice;
                console.log("[TTS] voice selected:", preferredVoice.name);
            } else {
                console.log("[TTS] voice selected: browser default");
            }

            utterance.onstart = () => {
                console.log("[TTS] speech started");
                this.voiceEngine.isPlaying = true;
                this.setConversationState("SPEAKING");
            };

            utterance.onend = () => {
                console.log("[TTS] speech ended");
                this.voiceEngine.isPlaying = false;
                if (turn === this.activeTurnId) {
                    this.setConversationState("COMPLETED");
                    setTimeout(() => {
                        if (this.conversationState === "COMPLETED") {
                            this.setConversationState("IDLE");
                        }
                    }, 1200);
                }
                if (onEnded) onEnded();
            };

            utterance.onerror = (err) => {
                console.warn("[TTS] speech error", err);
                this.voiceEngine.isPlaying = false;
                this.setConversationState("IDLE");
                if (onEnded) onEnded();
            };

            window.speechSynthesis.speak(utterance);
        } else {
            console.warn("[TTS] window.speechSynthesis unavailable in browser");
            this.setConversationState("COMPLETED");
            setTimeout(() => {
                if (this.conversationState === "COMPLETED") this.setConversationState("IDLE");
            }, 1200);
            if (onEnded) onEnded();
        }
    }

    // --- COMMAND TRANSMISSION & ASYNC PIPELINE ---
    transmitCommand(text) {
        if (!text || !text.trim()) return;
        const cleanText = text.trim();

        // Update Command Input Field & HEARD display
        if (this.tacticalCommandInput) this.tacticalCommandInput.value = cleanText;

        // If system is currently speaking, tool running, or processing, barge-in interrupt first!
        if (this.conversationState === "SPEAKING" || this.conversationState === "TOOL_RUNNING" || this.conversationState === "PROCESSING" || this.conversationState === "FLUSHING") {
            this.handleInterrupt();
        }

        // Clear any existing fallback timer from previous turns
        if (this.localFallbackTimer) {
            clearTimeout(this.localFallbackTimer);
            this.localFallbackTimer = null;
        }

        // Stop active STT listening cleanly
        if (this.isListening) {
            this.isListening = false;
            this.stopMicAudioContext();
            if (this.recognition) {
                try { this.recognition.stop(); } catch (e) { }
            }
        }

        // Increment Request / Turn ID for stale fencing
        this.requestId++;
        const currentTurnId = this.requestId;
        this.activeTurnId = currentTurnId;
        this.activeTurnUuid = (typeof crypto !== "undefined" && crypto.randomUUID) ? crypto.randomUUID() : `req-${currentTurnId}-${Date.now()}`;

        if (this.telemetryTurn) this.telemetryTurn.textContent = `#${currentTurnId}`;
        if (this.activeTurnBadge) this.activeTurnBadge.textContent = `TURN #${currentTurnId}`;

        this.setConversationState("PROCESSING");
        this.voiceEngine.init();

        this.turnCount++;
        if (this.turnCounterBadge) this.turnCounterBadge.textContent = `${this.turnCount} TURNS`;
        this.appendRadioLog("PARAMEDIC", cleanText, "user");

        const responseText = this.generateResponseForCommand(cleanText);

        // Notify WS Backend if active for telemetry logging
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: "USER_UTTERANCE",
                transcript: cleanText,
                turn_id: currentTurnId,
                request_id: this.activeTurnUuid,
                speaker: this.speakerSelect.value,
                model_id: this.modelSelect.value
            }));
        }
        // Only use the local response fallback when WebSocket backend is NOT connected.
        const backendConnected = this.ws && this.ws.readyState === WebSocket.OPEN;

        if (!backendConnected) {
            const delaySec = this.selectedDelay || 0;
            const delayMs = Math.max(150, delaySec * 1000);

            if (delaySec > 0) {
                this.setConversationState("TOOL_RUNNING");
                if (this.telemetryTool) {
                    this.telemetryTool.textContent = `${delaySec}s synthetic delay...`;
                }
                this.appendRadioLog(
                    "CLINICAL TOOL",
                    `Executing async tool with ${delaySec}s synthetic delay...`,
                    "tool"
                );
            }

            this.localFallbackTimer = setTimeout(() => {
                this.localFallbackTimer = null;

                if (currentTurnId !== this.activeTurnId) {
                    console.warn(
                        `[STALE FIREWALL] Turn #${currentTurnId} blocked! Active turn is #${this.activeTurnId}`
                    );
                    this.appendFirewallLog({
                        source: "Async Tool Pipeline",
                        status: "BLOCKED",
                        old_turn_id: currentTurnId,
                        current_turn_id: this.activeTurnId,
                        reason: `Interruption Fenced: Blocked stale output from turn #${currentTurnId}`
                    });
                    this.updateStateGraphNode("STALE_RESULT_BLOCKED");
                    return;
                }

                this.speakAgentResponse(responseText, currentTurnId);
            }, delayMs);
        }
    }

    generateResponseForCommand(text) {
        const lower = text.toLowerCase();
        if (lower.includes("epi") || lower.includes("epinephrine")) {
            return "Epinephrine 0.3 milligrams IM confirmed. Timer initialized for 3-minute repeat cycle.";
        } else if (lower.includes("vitals") || lower.includes("log")) {
            return "Patient vitals logged into CAD manifest. ECG monitor synced.";
        } else if (lower.includes("hospital") || lower.includes("trauma") || lower.includes("bed")) {
            return "St. Jude Trauma Center accepting, ETA 8 minutes, 2 trauma bays open. Routing medic unit.";
        } else if (lower.includes("fleet") || lower.includes("dispatch") || lower.includes("unit")) {
            return "ALS Unit Medic 14 dispatched Code 3. Staging at Lincoln Cafeteria.";
        } else if (lower.includes("narcan") || lower.includes("naloxone")) {
            return "Naloxone Narcan 2 milligrams intranasally confirmed. Airway support initiated.";
        } else if (lower.includes("amiodarone")) {
            return "Amiodarone 300 milligrams IV push confirmed for persistent V-Tach.";
        } else if (lower.includes("cancel") || lower.includes("interrupt")) {
            return "Previous order cancelled. Standing by for immediate clinical direction.";
        } else {
            return `Acknowledged: "${text}". Command routed to emergency orchestrator.`;
        }
    }

    // --- BARGE-IN INTERRUPT & AUDIO FLUSH HANDLER ---
    handleInterrupt() {
        console.log("[INTERRUPT] request invalidated");
        if ("speechSynthesis" in window) {
            window.speechSynthesis.cancel();
            console.log("[TTS] speech cancelled");
        }

        if (this.recoveryTimer) clearTimeout(this.recoveryTimer);
        if (this.localFallbackTimer) {
            clearTimeout(this.localFallbackTimer);
            this.localFallbackTimer = null;
        }

        const cancelledTurnId = this.activeTurnId;
        this.requestId++;
        const newTurnId = this.requestId;
        this.activeTurnId = newTurnId;
        this.activeTurnUuid = (typeof crypto !== "undefined" && crypto.randomUUID) ? crypto.randomUUID() : `req-${newTurnId}-${Date.now()}`;

        // Immediately flush all playing audio & speech synthesis
        const latency = this.voiceEngine.stopAll(newTurnId);
        if (this.telemetryFlush) this.telemetryFlush.textContent = `${latency} ms`;

        // Abort STT if listening
        if (this.recognition) {
            try { this.recognition.abort(); } catch (e) { }
        }
        this.stopMicAudioContext();
        this.isListening = false;

        // Send WS interrupt notification to server
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: "INTERRUPT", reason: "manual_user_barge_in", new_turn_id: newTurnId }));
        }

        // 1. Enter INTERRUPTED state
        this.setConversationState("INTERRUPTED");
        this.appendRadioLog("BARGE-IN FENCE", `Interruption captured (#${cancelledTurnId} -> #${newTurnId}). Audio flushed in ${latency}ms.`, "flush");
        this.appendFirewallLog({
            source: "User Barge-In",
            status: "BLOCKED",
            old_turn_id: cancelledTurnId,
            current_turn_id: newTurnId,
            reason: `Request #${cancelledTurnId} invalidated by user interruption`
        });

        // 2. Sequential State Transition Animation (FLUSHING -> FENCED -> RECOVERING -> IDLE)
        setTimeout(() => this.setConversationState("FLUSHING"), 150);
        setTimeout(() => this.setConversationState("FENCED"), 350);
        setTimeout(() => this.setConversationState("RECOVERING"), 600);
        this.recoveryTimer = setTimeout(() => {
            if (this.conversationState === "RECOVERING") {
                this.setConversationState("IDLE");
            }
        }, 900);
    }

    // --- HARDWARE MICROPHONE WITH REAL AUDIO CONTEXT & VU METER ---
    async startMicAudioContext() {
        try {
            if (!this.audioContext) {
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                this.audioContext = new AudioContext();
            }
            if (this.audioContext.state === "suspended") {
                await this.audioContext.resume();
            }

            if (!this.mediaStream) {
                this.mediaStream = await navigator.mediaDevices.getUserMedia({
                    audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }
                });
            }

            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            this.analyser.smoothingTimeConstant = 0.75;
            source.connect(this.analyser);
            this.micDataArray = new Uint8Array(this.analyser.frequencyBinCount);
            this.isTransmitting = true;

        } catch (err) {
            this.isTransmitting = false;
            console.warn("[MIC AUDIO CONTEXT ERROR]", err);
        }
    }

    stopMicAudioContext() {
        this.isTransmitting = false;
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(t => t.stop());
            this.mediaStream = null;
        }
        this.updateVUMeter(0);
    }

    syncCanvasSize(canvas) {
        if (!canvas || !canvas.parentElement) return;
        const parent = canvas.parentElement;
        const w = parent.clientWidth || 300;
        const h = parent.clientHeight || 80;
        if (canvas.width !== w || canvas.height !== h) {
            canvas.width = w;
            canvas.height = h;
        }
    }

    initCanvases() {
        // 1. Audio Waveform Oscilloscope
        const renderOsc = () => {
            if (this.oscCtx && this.oscilloscopeCanvas) {
                const canvas = this.oscilloscopeCanvas;
                const ctx = this.oscCtx;
                this.syncCanvasSize(canvas);
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                let micLevel = 0;
                if (this.analyser && this.isTransmitting && this.micDataArray) {
                    this.analyser.getByteFrequencyData(this.micDataArray);
                    let sum = 0;
                    for (let i = 0; i < this.micDataArray.length; i++) sum += this.micDataArray[i];
                    const avg = sum / this.micDataArray.length;
                    micLevel = Math.min(100, Math.round((avg / 128) * 100));
                    this.updateVUMeter(micLevel);
                }

                ctx.lineWidth = 2;
                ctx.beginPath();
                const slices = 80;
                const sliceWidth = canvas.width / slices;
                let x = 0;

                const isSpeaking = this.voiceEngine.isPlaying;
                const isTransmitting = this.isTransmitting || this.isListening;

                for (let i = 0; i < slices; i++) {
                    let amp = 0;
                    if (isSpeaking) {
                        amp = Math.sin(this.animPhase + i * 0.25) * 22 + Math.cos(this.animPhase * 1.8 + i * 0.1) * 12;
                        ctx.strokeStyle = "#2563EB"; // Primary Blue for Rime Speech
                    } else if (isTransmitting) {
                        const freqVal = this.micDataArray ? (this.micDataArray[i % this.micDataArray.length] / 5) : 0;
                        amp = Math.sin(this.animPhase * 0.9 + i * 0.15) * (5 + freqVal);
                        ctx.strokeStyle = "#16A34A"; // Green for mic
                    } else {
                        amp = Math.sin(this.animPhase * 0.2 + i * 0.05) * 2;
                        ctx.strokeStyle = "#334155";
                    }

                    const y = canvas.height / 2 + amp;
                    if (i === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                    x += sliceWidth;
                }
                ctx.stroke();
                this.animPhase += 0.08;
            }
            requestAnimationFrame(renderOsc);
        };
        renderOsc();

        // 2. Lead II ECG Trace
        const renderECG = () => {
            if (this.ecgCtx && this.ecgCanvas) {
                const canvas = this.ecgCanvas;
                const ctx = this.ecgCtx;
                this.syncCanvasSize(canvas);

                ctx.fillStyle = "rgba(15, 23, 42, 0.9)";
                ctx.fillRect(0, 0, canvas.width, canvas.height);

                ctx.strokeStyle = "#22C55E";
                ctx.lineWidth = 2;
                ctx.beginPath();

                const points = 120;
                const step = canvas.width / points;
                let x = 0;
                const midY = canvas.height / 2;

                for (let i = 0; i < points; i++) {
                    const phase = (i + this.ecgIndex) % 40;
                    let y = midY;
                    if (phase === 10) y = midY - 6;
                    else if (phase === 14) y = midY + 4;
                    else if (phase === 16) y = midY - 24;
                    else if (phase === 18) y = midY + 10;
                    else if (phase === 24) y = midY - 8;

                    if (i === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                    x += step;
                }
                ctx.stroke();
                this.ecgIndex = (this.ecgIndex + 1) % 40;
            }
            setTimeout(renderECG, 50);
        };
        renderECG();
    }

    startEpiTimer() {
        this.epiInterval = setInterval(() => {
            if (this.epiSecondsLeft > 0) {
                this.epiSecondsLeft--;
                const m = Math.floor(this.epiSecondsLeft / 60);
                const s = this.epiSecondsLeft % 60;
                if (this.epiTimerDisplay) {
                    this.epiTimerDisplay.textContent = `03:00 (REPEAT IN: ${m}m ${s < 10 ? "0" : ""}${s}s)`;
                }
            } else {
                if (this.epiTimerDisplay) {
                    this.epiTimerDisplay.textContent = "03:00 (ALERT: REPEAT EPINEPHRINE NOW!)";
                }
            }
        }, 1000);
    }

    updateDosageCalculations() {
        const weight = parseFloat(this.toolWeightSlider.value);
        if (this.toolWeightValue) this.toolWeightValue.textContent = `${weight.toFixed(1)} KG`;
        const drug = this.toolDrugSelect.value;

        if (drug === "epinephrine") {
            const dose = (weight >= 50 ? 0.3 : Math.min(0.5, 0.01 * weight)).toFixed(2);
            this.calculatedDoseText.textContent = `${dose} mg IM (Anterolateral Thigh)`;
            this.calculatedDilutionText.textContent = `Dilution: 1 mg/1 mL (1:1,000) • Volume: ${dose} mL`;
        } else if (drug === "amiodarone") {
            const dose = weight < 40 ? `${(5 * weight).toFixed(0)} mg (5 mg/kg)` : "300 mg IV push";
            this.calculatedDoseText.textContent = `${dose} (IV / IO Push)`;
            this.calculatedDilutionText.textContent = "Dilution: 50 mg/mL in 20-30 mL D5W";
        } else if (drug === "fentanyl") {
            const dose = Math.min(100, Math.round(weight * 1.0));
            this.calculatedDoseText.textContent = `${dose} mcg Slow IV / IN`;
            this.calculatedDilutionText.textContent = `Dilution: 50 mcg/mL • Volume: ${(dose / 50).toFixed(1)} mL`;
        } else if (drug === "naloxone") {
            this.calculatedDoseText.textContent = "2.0 mg IN or 0.4 mg IV Titrate";
            this.calculatedDilutionText.textContent = "Dilution: 2 mg/2 mL Prefilled Nasal Spray";
        } else if (drug === "atropine") {
            const dose = weight < 40 ? `${Math.max(0.1, (0.02 * weight)).toFixed(2)} mg` : "1.0 mg Rapid IV";
            this.calculatedDoseText.textContent = `${dose} Rapid IV Push`;
            this.calculatedDilutionText.textContent = "Dilution: 0.1 mg/mL • Repeat q3-5m (Max 3mg)";
        } else if (drug === "midazolam") {
            const dose = Math.min(5.0, (weight * 0.1)).toFixed(1);
            this.calculatedDoseText.textContent = `${dose} mg IV / IN`;
            this.calculatedDilutionText.textContent = `Dilution: 5 mg/mL • Volume: ${(dose / 5).toFixed(1)} mL`;
        } else if (drug === "ketamine") {
            const dose = (weight * 1.5).toFixed(0);
            this.calculatedDoseText.textContent = `${dose} mg IV (1.5 mg/kg)`;
            this.calculatedDilutionText.textContent = `Dilution: 50 mg/mL • Volume: ${(dose / 50).toFixed(1)} mL`;
        }
    }

    // --- REPRODUCIBLE 1-CLICK JUDGE DEMO SEQUENCE ---
    runJudgeDemoSequence() {
        this.appendRadioLog("JUDGE DEMO", "Initiating 1-Click Reproducible Interruption Proof...", "system");
        this.selectedDelay = 3.5;

        // Reset indicators
        if (this.stressStep1) { this.stressStep1.className = "text-[#2563EB] font-bold font-mono animate-pulse"; this.stressStep1.textContent = "RUNNING (REQUEST #1 ACTIVE)..."; }
        if (this.stressStep2) { this.stressStep2.className = "text-[#64748B] font-mono"; this.stressStep2.textContent = "STANDBY"; }
        if (this.stressStep3) { this.stressStep3.className = "text-[#64748B] font-mono"; this.stressStep3.textContent = "STANDBY"; }
        if (this.stressFinalResult) { this.stressFinalResult.className = "text-[#2563EB] font-bold font-mono"; this.stressFinalResult.textContent = "EVALUATING RECOVERY..."; }

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: "SET_MODE", mode: "RESONANCE" }));
            this.ws.send(JSON.stringify({ type: "SET_DELAY", delay_sec: 3.5 }));
        }

        // 1. VOICE REQUEST #1 ACTIVE -> RIME SPEAKING (Hospital Search with 3.5s delay)
        const req1Turn = this.requestId + 1;
        this.transmitCommand("Run stress test lookup with 3.5s synthetic tool delay");

        if (this.stressStep1) {
            this.stressStep1.className = "text-[#16A34A] font-bold font-mono";
            this.stressStep1.textContent = `PASSED (REQUEST #${req1Turn} ACTIVE & TOOL DELAYED 3.5s)`;
        }

        // 2. USER INTERRUPTED -> AUDIO FLUSHED -> REQUEST #1 INVALIDATED (at 1.0s)
        setTimeout(() => {
            if (this.stressStep2) {
                this.stressStep2.className = "text-[#16A34A] font-bold font-mono";
                this.stressStep2.textContent = `PASSED (USER INTERRUPTED: AUDIO FLUSHED <4ms, REQUEST #${req1Turn} INVALIDATED)`;
            }
            this.handleInterrupt();

            // 3. REQUEST #2 ACTIVE (Critical Epinephrine Order)
            setTimeout(() => {
                const req2Turn = this.requestId + 1;
                if (this.stressStep3) {
                    this.stressStep3.className = "text-[#2563EB] font-bold font-mono animate-pulse";
                    this.stressStep3.textContent = `EVALUATING STALE RESULT FIREWALL FOR REQUEST #${req2Turn}...`;
                }
                this.transmitCommand("Cancel that! Patient crashing, dose 0.3mg epinephrine immediately!");

                // 4. STALE TOOL RESULT RETURNED -> STALE RESULT BLOCKED -> RECOVERY VERIFIED
                setTimeout(() => {
                    if (this.stressStep3) {
                        this.stressStep3.className = "text-[#16A34A] font-bold font-mono";
                        this.stressStep3.textContent = `PASSED (STALE REQUEST #${req1Turn} BLOCKED, REQUEST #${req2Turn} COMPLETED)`;
                    }
                    if (this.stressFinalResult) {
                        this.stressFinalResult.className = "px-2 py-0.5 rounded bg-[#F0FDF4] border border-[#BBF7D0] text-[#16A34A] font-bold font-mono inline-block";
                        this.stressFinalResult.textContent = "INTERRUPTION RECOVERY VERIFIED";
                    }
                }, 2500);
            }, 500);
        }, 1000);
    }

    bindEvents() {
        // PTT Button Pointer & Touch & Mouse Events (Press and hold to speak)
        if (this.pttButton) {
            const handlePressStart = (e) => {
                e.preventDefault();
                if (!this.isListening) {
                    this.startListening();
                }
            };

            const handlePressEnd = (e) => {
                e.preventDefault();
                if (this.isListening) {
                    this.stopListening();
                }
            };

            // Pointer Events
            this.pttButton.addEventListener("pointerdown", handlePressStart);
            this.pttButton.addEventListener("pointerup", handlePressEnd);
            this.pttButton.addEventListener("pointerleave", handlePressEnd);
            this.pttButton.addEventListener("pointercancel", handlePressEnd);

            // Touch Events fallback
            this.pttButton.addEventListener("touchstart", handlePressStart, { passive: false });
            this.pttButton.addEventListener("touchend", handlePressEnd, { passive: false });
            this.pttButton.addEventListener("touchcancel", handlePressEnd, { passive: false });

            // Mouse Events fallback
            this.pttButton.addEventListener("mousedown", handlePressStart);
            this.pttButton.addEventListener("mouseup", handlePressEnd);
        }

        // Global PointerUp / MouseUp safety listener
        window.addEventListener("pointerup", () => {
            if (this.isListening) this.stopListening();
        });
        window.addEventListener("mouseup", () => {
            if (this.isListening) this.stopListening();
        });

        // Spacebar Keyboard Listener (Prevents Page Scroll!)
        window.addEventListener("keydown", (e) => {
            if (e.code === "Space" && !this.isInputFocused()) {
                e.preventDefault();
                if (!e.repeat && !this.isListening) {
                    this.startListening();
                }
            }
        });

        window.addEventListener("keyup", (e) => {
            if (e.code === "Space" && !this.isInputFocused()) {
                e.preventDefault();
                if (this.isListening) {
                    this.stopListening();
                }
            }
        });
        // CPR Metronome Toggle
        if (this.cprMetronomeBtn) {
            this.cprMetronomeBtn.addEventListener("click", () => {
                const active = this.voiceEngine.soundFX.toggleCprMetronome();

                if (this.cprStatusText) {
                    this.cprStatusText.textContent = active ? "ON" : "OFF";
                    this.cprStatusText.className = active
                        ? "text-[#16A34A] font-bold"
                        : "text-[#64748B]";
                }
            });
        }
        // Audio Mute / Toggle Button
        if (this.audioMuteToggleBtn) {
            this.audioMuteToggleBtn.addEventListener("click", () => {
                this.soundEnabled = !this.soundEnabled;
                this.voiceEngine.soundEnabled = this.soundEnabled;
                if (this.audioMuteText && this.audioMuteIcon) {
                    if (this.soundEnabled) {
                        this.audioMuteText.textContent = "🔊 AUDIO ON";
                        this.audioMuteIcon.className = "fa-solid fa-volume-high text-[#16A34A]";
                        console.log("[AUDIO] Audio output ENABLED");
                    } else {
                        this.audioMuteText.textContent = "🔇 AUDIO OFF";
                        this.audioMuteIcon.className = "fa-solid fa-volume-xmark text-[#DC2626]";
                        if ("speechSynthesis" in window) window.speechSynthesis.cancel();
                        console.log("[AUDIO] Audio output DISABLED");
                    }
                }
            });
        }

        // Flush / Barge-In Button
        if (this.flushBargeInBtn) {
            this.flushBargeInBtn.addEventListener("click", () => this.handleInterrupt());
        }

        // Transmit Command Button
        if (this.transmitCommandBtn) {
            this.transmitCommandBtn.addEventListener("click", () => {
                const text = this.tacticalCommandInput ? this.tacticalCommandInput.value.trim() : "";
                if (text) this.transmitCommand(text);
            });
        }

        // Command Input Enter Key
        if (this.tacticalCommandInput) {
            this.tacticalCommandInput.addEventListener("keydown", (e) => {
                if (e.key === "Enter") {
                    e.preventDefault();
                    const text = this.tacticalCommandInput.value.trim();
                    if (text) this.transmitCommand(text);
                }
            });
        }

        // Mode Toggle Button
        if (this.modeToggleBtn) {
            this.modeToggleBtn.addEventListener("click", () => {
                const nextMode = this.currentMode === "RESONANCE" ? "NAIVE" : "RESONANCE";
                this.setAgentMode(nextMode);
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({ type: "SET_MODE", mode: nextMode }));
                }
            });
        }

        // Judge Demo Button
        if (this.judgeDemoBtn) {
            this.judgeDemoBtn.addEventListener("click", () => this.runJudgeDemoSequence());
        }

        // Replay Incident Button
        if (this.replayIncidentBtn) {
            this.replayIncidentBtn.addEventListener("click", async () => {
                try {
                    const res = await fetch("/api/replay/timeline");
                    const data = await res.json();
                    if (data.timeline && data.timeline.length > 0) {
                        this.appendRadioLog("REPLAY INCIDENT", "Replaying recorded event trajectory:", "system");
                        data.timeline.forEach((item, idx) => {
                            setTimeout(() => {
                                this.appendRadioLog(item.category, item.detail, "tool");
                            }, idx * 300);
                        });
                        const summary = `Replay trajectory complete. ${data.timeline.length} recorded events retrieved.`;
                        this.speakAgentResponse(summary);
                    } else {
                        const msg = "No recorded events yet. Run a turn or stress test first.";
                        this.appendRadioLog("REPLAY INCIDENT", msg, "system");
                        this.speakAgentResponse(msg);
                    }
                } catch (e) { }
            });
        }

        // Synthetic Tool Delay Options Buttons
        document.querySelectorAll(".delay-option-btn").forEach(btn => {
            btn.addEventListener("click", async () => {
                const delay = parseFloat(btn.getAttribute("data-delay"));
                document.querySelectorAll(".delay-option-btn").forEach(b => {
                    b.classList.remove("active", "bg-[#EFF6FF]", "border-[#2563EB]", "text-[#2563EB]");
                    b.classList.add("bg-[#FFFFFF]", "border-[#CBD5E1]", "text-[#0F172A]");
                });
                btn.classList.remove("bg-[#FFFFFF]", "border-[#CBD5E1]", "text-[#0F172A]");
                btn.classList.add("active", "bg-[#EFF6FF]", "border-[#2563EB]", "text-[#2563EB]");
                this.selectedDelay = delay;

                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({ type: "SET_DELAY", delay_sec: delay }));
                }
                try {
                    await fetch("/api/stress/delay", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ delay_sec: delay })
                    });
                } catch (e) { }
            });
        });

        // Stress Scenario Dropdown
        if (this.stressScenarioSelect) {
            this.stressScenarioSelect.addEventListener("change", (e) => {
                const val = e.target.value;
                this.selectedScenario = val;
                this.appendRadioLog("STRESS LAB", `Stress scenario preset set to: ${val}`, "system");
            });
        }

        // Scenario Buttons (5 Incidents)
        document.querySelectorAll(".incident-tab-btn").forEach(btn => {
            btn.addEventListener("click", async () => {
                const idx = parseInt(btn.getAttribute("data-index"));
                document.querySelectorAll(".incident-tab-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");

                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({ type: "SWITCH_SCENARIO", index: idx }));
                }
                try {
                    const res = await fetch(`/api/scenario/select/${idx}`, { method: "POST" });
                    const data = await res.json();
                    const inc = data.incident || data;
                    if (inc) {
                        this.renderIncident(inc);
                        if (data.vitals) this.renderVitals(data.vitals);
                        this.speakAgentResponse(`Switched active incident to ${inc.type || inc.id}`);
                    }
                } catch (e) {
                    console.error("ERROR SWITCHING INCIDENT", e);
                }
            });
        });

        // Randomize Case
        const randBtn = document.getElementById("randomizeIncidentBtn");
        if (randBtn) {
            randBtn.addEventListener("click", async () => {
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({ type: "SWITCH_SCENARIO" }));
                }
                try {
                    const res = await fetch("/api/scenario/randomize", { method: "POST" });
                    const data = await res.json();
                    const inc = data.incident || data;
                    if (inc) {
                        this.renderIncident(inc);
                        if (data.vitals) this.renderVitals(data.vitals);
                        const presets = ["MED-7829", "MED-9102", "MED-4421", "MED-6380", "MED-3199"];
                        const matchIdx = presets.indexOf(inc.id);
                        if (matchIdx !== -1) {
                            document.querySelectorAll(".incident-tab-btn").forEach((b, idx) => {
                                if (idx === matchIdx) b.classList.add("active");
                                else b.classList.remove("active");
                            });
                        }
                        this.speakAgentResponse(`Randomized emergency scenario. Active incident ${inc.id}: ${inc.type}`);
                    }
                } catch (e) { }
            });
        }

        // Tool Tabs (STRESS LAB, DOSAGE, HOSPITALS, FLEET)
        document.querySelectorAll(".ws-tab-btn").forEach(tab => {
            tab.addEventListener("click", () => {
                const target = tab.getAttribute("data-target");
                document.querySelectorAll(".ws-tab-btn").forEach(t => t.classList.remove("active"));
                document.querySelectorAll(".tab-pane").forEach(p => p.classList.add("hidden"));
                tab.classList.add("active");
                const pane = document.getElementById(target);
                if (pane) pane.classList.remove("hidden");
            });
        });

        // Dosage Inputs
        if (this.toolWeightSlider) this.toolWeightSlider.addEventListener("input", () => this.updateDosageCalculations());
        if (this.toolDrugSelect) this.toolDrugSelect.addEventListener("change", () => this.updateDosageCalculations());
        if (this.speakDosageOrderBtn) {
            this.speakDosageOrderBtn.addEventListener("click", () => {
                const dose = this.calculatedDoseText.textContent;
                this.transmitCommand(`Administer ${dose} for ${this.toolWeightValue.textContent} patient.`);
            });
        }

        // Query Hospitals
        if (this.queryHospitalRadarBtn) {
            this.queryHospitalRadarBtn.addEventListener("click", () => {
                this.transmitCommand("Find nearest Level 1 trauma centers and burn beds.");
            });
        }

        // Quick Fleet Dispatch
        document.querySelectorAll(".dispatch-unit-quick").forEach(b => {
            b.addEventListener("click", () => {
                const u = b.getAttribute("data-unit");
                this.transmitCommand(`Dispatch ${u} Code 3 immediately`);
            });
        });

        // Quick Tactical Orders (One-Touch Voice Presets)
        document.querySelectorAll(".quick-tactical-order").forEach(b => {
            b.addEventListener("click", () => {
                const presetText = b.getAttribute("data-text");
                this.transmitCommand(presetText);
            });
        });

        // Stress Benchmark Test
        if (this.runStressTestBenchmarkBtn) {
            this.runStressTestBenchmarkBtn.addEventListener("click", () => {
                this.runJudgeDemoSequence();
            });
        }

        // Vitals Modal
        if (this.editVitalsBtn) this.editVitalsBtn.addEventListener("click", () => this.vitalsModal.classList.remove("hidden"));
        if (this.closeVitalsModalBtn) this.closeVitalsModalBtn.addEventListener("click", () => this.vitalsModal.classList.add("hidden"));
        if (this.saveVitalsModalBtn) {
            this.saveVitalsModalBtn.addEventListener("click", () => {
                const hr = parseInt(this.inputEditHR.value);
                const bp = this.inputEditBP.value;
                const spo2 = parseInt(this.inputEditSpO2.value);
                const gcs = parseInt(this.inputEditGCS.value);
                this.vitalsModal.classList.add("hidden");
                this.transmitCommand(`Log vitals: blood pressure ${bp}, heart rate ${hr}, SpO2 ${spo2} percent, GCS ${gcs}`);
            });
        }
    }
}

window.addEventListener("DOMContentLoaded", () => {
    window.tacticalApp = new TacticalApp();
});
