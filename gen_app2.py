with open("static/app.js", "a", encoding="utf-8") as f:
    f.write("""
class TacticalApp {
    constructor() {
        this.ws = null;
        this.voiceEngine = new SpeechVoiceEngine();
        this.isTransmitting = false;
        this.recognition = null;
        this.turnCount = 0;
        this.currentIncident = null;

        // Hardware Microphone & Audio Analyser
        this.mediaStream = null;
        this.audioContext = null;
        this.analyser = null;
        this.micDataArray = null;
        this.micLevel = 0;

        // Canvas Elements
        this.oscilloscopeCanvas = document.getElementById("oscilloscopeCanvas");
        this.oscCtx = this.oscilloscopeCanvas ? this.oscilloscopeCanvas.getContext("2d") : null;
        this.ecgCanvas = document.getElementById("ecgCanvas");
        this.ecgCtx = this.ecgCanvas ? this.ecgCanvas.getContext("2d") : null;
        this.animPhase = 0;
        this.ecgIndex = 0;

        // Epinephrine timer
        this.epiSecondsLeft = 180;
        this.epiInterval = null;

        this.initDOMElements();
        this.initVULevels();
        this.initWebSocket();
        this.initCanvases();
        this.startEpiTimer();
        this.bindEvents();
        this.loadState();
    }

    initDOMElements() {
        // Transceiver
        this.pttButton = document.getElementById("pttButton");
        this.pttIcon = document.getElementById("pttIcon");
        this.pttLabelText = document.getElementById("pttLabelText");
        this.pttLed = document.getElementById("pttLed");
        this.flushBargeInBtn = document.getElementById("flushBargeInBtn");
        this.transceiverStatusText = document.getElementById("transceiverStatusText");
        this.liveHearingBanner = document.getElementById("liveHearingBanner");
        this.liveHearingPillText = document.getElementById("liveHearingPillText");
        this.vuDbText = document.getElementById("vuDbText");

        // Commands & Transcripts
        this.tacticalCommandInput = document.getElementById("tacticalCommandInput");
        this.transmitCommandBtn = document.getElementById("transmitCommandBtn");
        this.radioTranscriptFeed = document.getElementById("radioTranscriptFeed");
        this.turnCounterBadge = document.getElementById("turnCounterBadge");

        // Telemetry
        this.telemetryTTFB = document.getElementById("telemetryTTFB");
        this.telemetryFlush = document.getElementById("telemetryFlush");
        this.telemetryTurn = document.getElementById("telemetryTurn");
        this.telemetryTool = document.getElementById("telemetryTool");

        // Patient & Vitals
        this.triageBadge = document.getElementById("triageBadge");
        this.incidentIdText = document.getElementById("incidentIdText");
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
        this.speakerSelect = document.getElementById("speakerSelect");
        this.modelSelect = document.getElementById("modelSelect");

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

        // Stress Bench
        this.runStressTestBenchmarkBtn = document.getElementById("runStressTestBenchmarkBtn");
        this.stressStep1 = document.getElementById("stressStep1");
        this.stressStep2 = document.getElementById("stressStep2");
        this.stressStep3 = document.getElementById("stressStep3");
        this.stressFinalResult = document.getElementById("stressFinalResult");

        // Top Toggles
        this.cprMetronomeBtn = document.getElementById("cprMetronomeBtn");
        this.cprStatusText = document.getElementById("cprStatusText");
        this.audioMuteToggleBtn = document.getElementById("audioMuteToggleBtn");
        this.audioMuteText = document.getElementById("audioMuteText");
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

    initVULevels() {
        const container = document.getElementById("vuMeterLeds");
        if (!container) return;
        container.innerHTML = "";
        for (let i = 0; i < 10; i++) {
            const led = document.createElement("div");
            const colorClass = i < 6 ? "green" : (i < 8 ? "yellow" : "red");
            led.className = `vu-led ${colorClass}`;
            led.id = `vu-led-${i}`;
            container.appendChild(led);
        }
    }

    updateVUMeter(percent) {
        const count = Math.round((percent / 100) * 10);
        for (let i = 0; i < 10; i++) {
            const led = document.getElementById(`vu-led-${i}`);
            if (led) {
                if (i < count) led.classList.add("active");
                else led.classList.remove("active");
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
        } catch (e) {}
    }

    initWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws/voice`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            const pill = document.getElementById("netStatusPill");
            if (pill) {
                pill.innerHTML = `<span class="h-2 w-2 rounded-full bg-emerald-500 animate-ping"></span><span class="text-[10px] font-bold text-emerald-400">LINK: CONNECTED</span>`;
                pill.className = "flex items-center space-x-1.5 bg-[#0a121d] border border-emerald-500/40 px-3 py-1 rounded";
            }
        };

        this.ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            this.handleWsMessage(msg);
        };

        this.ws.onclose = () => {
            const pill = document.getElementById("netStatusPill");
            if (pill) {
                pill.innerHTML = `<span class="h-2 w-2 rounded-full bg-red-500"></span><span class="text-[10px] font-bold text-red-400">LINK: RECONNECTING</span>`;
                pill.className = "flex items-center space-x-1.5 bg-red-950/40 border border-red-500/40 px-3 py-1 rounded";
            }
            setTimeout(() => this.initWebSocket(), 2500);
        };
    }

    handleWsMessage(msg) {
        if (msg.type === "CONNECTION_ESTABLISHED") {
            if (msg.state) {
                if (msg.state.incident) this.renderIncident(msg.state.incident);
                if (msg.state.vitals) this.renderVitals(msg.state.vitals);
                if (msg.state.hospitals) this.renderHospitals(msg.state.hospitals);
                if (msg.state.dispatched_units) this.renderFleet(msg.state.dispatched_units);
            }
        } else if (msg.type === "SCENARIO_UPDATED") {
            const s = msg.state;
            if (s.incident) this.renderIncident(s.incident);
            if (s.vitals) this.renderVitals(s.vitals);
            if (s.units) this.renderFleet(s.units);
            this.appendRadioLog("CAD DISPATCH", `Emergency Scenario Switched to: [${s.incident.id}] ${s.incident.type}`, "system");
        } else if (msg.type === "AUDIO_CHUNK") {
            const meta = msg.telemetry;
            if (meta) {
                if (meta.ttfb_ms && this.telemetryTTFB) this.telemetryTTFB.textContent = `${meta.ttfb_ms} ms`;
                if (meta.turn_id && this.telemetryTurn) this.telemetryTurn.textContent = `#${meta.turn_id}`;
                if (meta.text) this.voiceEngine.speak(meta.text, meta.turn_id);
            }
        } else if (msg.type === "AUDIO_FLUSH") {
            const latency = this.voiceEngine.stopAll(msg.event.new_turn_id);
            if (this.telemetryFlush) this.telemetryFlush.textContent = `${latency} ms`;
            this.appendRadioLog("BARGE-IN FENCE", `Interruption detected (Turn #${msg.event.cancelled_turn_id} -> #${msg.event.new_turn_id}). Audio queue instantly cleared.`, "flush");
        } else if (msg.type === "TELEMETRY") {
            const d = msg.data;
            if (d.type === "TURN_START") {
                if (this.telemetryTurn) this.telemetryTurn.textContent = `#${d.turn_id}`;
                this.turnCount++;
                if (this.turnCounterBadge) this.turnCounterBadge.textContent = `${this.turnCount} TURNS`;
                this.appendRadioLog("PARAMEDIC", d.transcript, "user");
            } else if (d.type === "FILLER_START") {
                this.appendRadioLog("ACOUSTIC FILLER", d.text, "filler");
                this.voiceEngine.speak(d.text, d.turn_id);
            } else if (d.type === "TOOL_START") {
                if (this.telemetryTool) this.telemetryTool.textContent = `Running ${d.tool_name}...`;
                this.appendRadioLog("CLINICAL TOOL", `Executing tool: ${d.tool_name}`, "tool");
            } else if (d.type === "TOOL_COMPLETE") {
                if (this.telemetryTool) this.telemetryTool.textContent = `${d.duration_ms} ms`;
                if (d.tool_name === "log_patient_vitals" && d.result.vitals) {
                    this.renderVitals(d.result.vitals);
                } else if (d.tool_name === "dispatch_backup_units" && d.result.dispatched) {
                    this.addFleetCard(d.result.dispatched);
                }
                const summary = d.result.spoken_summary || JSON.stringify(d.result);
                this.appendRadioLog("PULSEDISPATCH", summary, "copilot");
                this.voiceEngine.speak(summary, d.turn_id);
            }
        }
    }
""")
print("App JS Part 2 written")
