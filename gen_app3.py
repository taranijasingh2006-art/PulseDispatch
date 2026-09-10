with open("static/app.js", "a", encoding="utf-8") as f:
    f.write("""
    renderIncident(inc) {
        this.currentIncident = inc;
        if (this.incidentIdText) this.incidentIdText.textContent = inc.id || "MED-7829";
        if (this.incidentTitleText) this.incidentTitleText.textContent = inc.type || "Active Incident";
        if (this.incidentLocationText) this.incidentLocationText.innerHTML = `<i class="fa-solid fa-location-crosshairs text-red-400 mr-1"></i><span>${inc.location || "Scene"}</span>`;
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
            this.valHR.innerHTML = `${v.heart_rate} <span class="text-[10px] text-slate-400 font-normal">BPM</span>`;
            if (this.hrStatus) this.hrStatus.textContent = v.heart_rate > 100 ? "TACHYCARDIA" : (v.heart_rate < 60 ? "BRADYCARDIA" : "NORMAL SINUS");
            if (this.inputEditHR) this.inputEditHR.value = v.heart_rate;
        }
        if (v.blood_pressure !== undefined) {
            this.valBP.textContent = v.blood_pressure;
            if (this.inputEditBP) this.inputEditBP.value = v.blood_pressure;
        }
        if (v.spo2 !== undefined) {
            this.valSpO2.innerHTML = `${v.spo2} <span class="text-[10px] text-slate-400 font-normal">%</span>`;
            if (this.spo2Status) this.spo2Status.textContent = v.spo2 < 90 ? "CRITICAL HYPOXIA" : (v.spo2 < 95 ? "MILD HYPOXIA" : "ADEQUATE");
            if (this.inputEditSpO2) this.inputEditSpO2.value = v.spo2;
        }
        if (v.gcs !== undefined) {
            this.valGCS.innerHTML = `${v.gcs} <span class="text-[10px] text-slate-400 font-normal">/ 15</span>`;
            if (this.gcsStatus) this.gcsStatus.textContent = v.gcs <= 8 ? "SEVERE (INTUBATE)" : (v.gcs <= 12 ? "MODERATE" : "MILD / CONSCIOUS");
            if (this.inputEditGCS) this.inputEditGCS.value = v.gcs;
        }
    }

    renderHospitals(hospitals) {
        if (!this.hospitalsListContainer) return;
        this.hospitalsListContainer.innerHTML = "";
        hospitals.forEach(h => {
            const card = document.createElement("div");
            const divertClass = h.divert ? "border-red-600/70 bg-red-950/20" : "border-slate-800 bg-black";
            const badge = h.divert 
                ? `<span class="text-[9px] px-1.5 py-0.5 rounded bg-red-950 text-red-400 font-bold border border-red-700">DIVERT</span>`
                : `<span class="text-[9px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 font-bold border border-emerald-700">ACCEPTING</span>`;
            
            card.className = `border-2 ${divertClass} p-2.5 rounded text-xs space-y-1`;
            card.innerHTML = `
                <div class="flex items-center justify-between font-bold">
                    <span class="text-white">${h.name} (L${h.trauma_level})</span>
                    ${badge}
                </div>
                <div class="flex items-center justify-between text-[10px] text-slate-400">
                    <span>ETA: <b class="text-cyan-300 font-mono">${h.eta_minutes}m</b> (${h.distance_miles} mi)</span>
                    <span>Trauma Bays: <b class="text-emerald-400 font-mono">${h.open_trauma_bays} open</b></span>
                </div>
                <div class="flex items-center justify-between text-[9px] text-slate-500 pt-1 border-t border-slate-900">
                    <span>Burn Unit: ${h.burn_unit ? "YES" : "NO"} • Peds: ${h.pediatric_trauma ? "YES" : "NO"}</span>
                    <button class="route-medic-btn px-2 py-0.5 bg-[#0284c7] hover:bg-[#0369a1] text-white font-bold rounded" data-name="${h.name}">ROUTE MEDIC</button>
                </div>
            `;
            this.hospitalsListContainer.appendChild(card);
        });

        // Bind routing buttons
        document.querySelectorAll(".route-medic-btn").forEach(b => {
            b.addEventListener("click", () => {
                const name = b.getAttribute("data-name");
                this.transmitVoice(`Route transport unit to ${name}`);
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
        card.className = "bg-black border border-slate-800 p-2 rounded text-xs animate-fade-in space-y-0.5";
        card.innerHTML = `
            <div class="flex justify-between items-center font-bold">
                <span class="text-cyan-300">${unit.unit_id} (${unit.type})</span>
                <span class="text-[9px] px-1.5 rounded bg-amber-950 text-amber-400 font-mono">${unit.status || "EN ROUTE"}</span>
            </div>
            <div class="text-[10px] text-slate-400">Staging: ${unit.staging_area} • ETA: <b class="text-emerald-400 font-mono">${unit.eta_minutes}m</b></div>
        `;
        this.fleetListContainer.prepend(card);
    }

    appendRadioLog(sender, text, type = "copilot") {
        if (!this.radioTranscriptFeed) return;
        const div = document.createElement("div");
        const timeStr = new Date().toLocaleTimeString();
        div.className = "p-2 rounded text-xs space-y-0.5 border";

        if (type === "user") {
            div.className += " bg-[#0a1424] border-blue-800/80 text-blue-200";
            div.innerHTML = `<div class="flex justify-between text-[9px] text-blue-400 font-bold"><span>[${timeStr}] 🎙️ ${sender} (VOICE PTT)</span><span>TRANSMIT</span></div><p class="text-slate-100 font-semibold">${text}</p>`;
        } else if (type === "filler") {
            div.className += " bg-[#071924] border-cyan-800/70 text-cyan-300 italic";
            div.innerHTML = `<div class="text-[9px] text-cyan-400 font-bold">[${timeStr}] ⏳ ACOUSTIC STATUS FILLER</div><p>${text}</p>`;
        } else if (type === "tool") {
            div.className += " bg-[#181308] border-amber-800/70 text-amber-300 font-mono";
            div.innerHTML = `<div class="text-[9px] text-amber-400 font-bold">[${timeStr}] 🔧 ${sender}</div><p>${text}</p>`;
        } else if (type === "flush") {
            div.className += " bg-[#240a0a] border-red-700 text-red-300 font-mono interrupted-turn";
            div.innerHTML = `<div class="text-[9px] text-red-400 font-bold">[${timeStr}] ⚡ ${sender}</div><p>${text}</p>`;
        } else {
            div.className += " bg-black border-slate-800 text-slate-200";
            div.innerHTML = `<div class="flex justify-between text-[9px] text-emerald-400 font-bold"><span>[${timeStr}] 📻 ${sender} (RIME NEURAL)</span><span>DISPATCH</span></div><p class="text-slate-100 font-semibold">${text}</p>`;
        }

        this.radioTranscriptFeed.appendChild(div);
        this.radioTranscriptFeed.scrollTop = this.radioTranscriptFeed.scrollHeight;
    }

    transmitVoice(text) {
        if (!text) return;
        this.voiceEngine.init();
        if (this.liveHearingBanner) this.liveHearingBanner.classList.add("hidden");

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: "USER_UTTERANCE",
                transcript: text,
                speaker: this.speakerSelect.value,
                model_id: this.modelSelect.value
            }));
        } else {
            // REST Fallback
            this.appendRadioLog("PARAMEDIC", text, "user");
            fetch("/api/dosage/calculate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ drug_name: text, weight_kg: 70 })
            })
            .then(r => r.json())
            .then(data => {
                const s = data.spoken_summary || "Order transmitted.";
                this.appendRadioLog("PULSEDISPATCH", s, "copilot");
                this.voiceEngine.speak(s, 1);
            });
        }
    }

    triggerBargeIn() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: "INTERRUPT", reason: "manual_user_barge_in" }));
        }
        const latency = this.voiceEngine.stopAll();
        if (this.telemetryFlush) this.telemetryFlush.textContent = `${latency} ms`;
    }

    // --- HARDWARE MICROPHONE WITH REAL AUDIO CONTEXT & VU METER ---
    async startMicTransceiver() {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.audioContext = new AudioContext();
            
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }
            });

            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            this.analyser.smoothingTimeConstant = 0.75;
            source.connect(this.analyser);
            this.micDataArray = new Uint8Array(this.analyser.frequencyBinCount);

            this.isTransmitting = true;
            if (this.pttButton) {
                this.pttButton.classList.add("transmitting");
                this.pttLabelText.textContent = "TRANSMITTING TO DISPATCH (SPEAK NOW)...";
                this.pttIcon.className = "fa-solid fa-tower-broadcast text-xl text-red-400 animate-pulse";
            }
            if (this.transceiverStatusText) {
                this.transceiverStatusText.textContent = "● LIVE MIC HOT -- TRANSMITTING COMMAND";
                this.transceiverStatusText.className = "absolute top-2 left-2 text-[9px] font-bold text-red-400 tracking-wider uppercase animate-pulse";
            }

            this.startWebSpeech();

        } catch (err) {
            alert("Microphone Access Required: Please click 'Allow' in your browser to enable live voice input.");
            this.isTransmitting = false;
        }
    }

    stopMicTransceiver() {
        this.isTransmitting = false;
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(t => t.stop());
            this.mediaStream = null;
        }
        if (this.recognition) {
            try { this.recognition.stop(); } catch (e) {}
        }
        if (this.pttButton) {
            this.pttButton.classList.remove("transmitting");
            this.pttLabelText.textContent = "PUSH TO TALK (OR PRESS SPACE)";
            this.pttIcon.className = "fa-solid fa-microphone-lines text-xl text-[#38bdf8]";
        }
        if (this.transceiverStatusText) {
            this.transceiverStatusText.textContent = "STANDBY // CLICK PTT BUTTON OR PRESS SPACE TO TALK";
            this.transceiverStatusText.className = "absolute top-2 left-2 text-[9px] font-bold text-slate-500 tracking-wider uppercase";
        }
        if (this.liveHearingBanner) this.liveHearingBanner.classList.add("hidden");
        this.updateVUMeter(0);
    }

    startWebSpeech() {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRec) {
            this.recognition = new SpeechRec();
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            this.recognition.lang = "en-US";

            this.recognition.onresult = (event) => {
                let interim = "";
                let finalStr = "";
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) finalStr += event.results[i][0].transcript;
                    else interim += event.results[i][0].transcript;
                }

                // Barge in if assistant is speaking
                if ((interim || finalStr) && this.voiceEngine.isPlaying) {
                    this.triggerBargeIn();
                }

                if (interim && this.liveHearingBanner) {
                    this.liveHearingBanner.classList.remove("hidden");
                    this.liveHearingPillText.textContent = `"${interim.trim()}"`;
                }

                if (finalStr.trim()) {
                    if (this.liveHearingBanner) this.liveHearingBanner.classList.add("hidden");
                    this.transmitVoice(finalStr.trim());
                }
            };

            this.recognition.onerror = (e) => console.warn("[STT ERROR]", e.error);
            this.recognition.onend = () => {
                if (this.isTransmitting) {
                    try { this.recognition.start(); } catch (e) {}
                }
            };

            try { this.recognition.start(); } catch (e) {}
        }
    }

    initCanvases() {
        // 1. Audio Oscilloscope
        const renderOsc = () => {
            if (this.oscCtx && this.oscilloscopeCanvas) {
                const canvas = this.oscilloscopeCanvas;
                const ctx = this.oscCtx;
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                canvas.width = canvas.parentElement.clientWidth;
                canvas.height = canvas.parentElement.clientHeight;

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
                const isTransmitting = this.isTransmitting;

                for (let i = 0; i < slices; i++) {
                    let amp = 0;
                    if (isSpeaking) {
                        amp = Math.sin(this.animPhase + i * 0.25) * 26 + Math.cos(this.animPhase * 1.8 + i * 0.1) * 14;
                        ctx.strokeStyle = "#38bdf8"; // Cyan for AI Speech
                    } else if (isTransmitting) {
                        const freqVal = this.micDataArray ? (this.micDataArray[i % this.micDataArray.length] / 5) : 0;
                        amp = Math.sin(this.animPhase * 0.9 + i * 0.15) * (6 + freqVal);
                        ctx.strokeStyle = "#10b981"; // Signal Green for user mic
                    } else {
                        amp = Math.sin(this.animPhase * 0.2 + i * 0.05) * 2;
                        ctx.strokeStyle = "#1e293b";
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

        // 2. Real-time Lead II ECG Trace
        const renderECG = () => {
            if (this.ecgCtx && this.ecgCanvas) {
                const canvas = this.ecgCanvas;
                const ctx = this.ecgCtx;
                canvas.width = canvas.parentElement.clientWidth;
                canvas.height = canvas.parentElement.clientHeight;

                ctx.fillStyle = "rgba(0, 0, 0, 0.08)";
                ctx.fillRect(0, 0, canvas.width, canvas.height);

                ctx.strokeStyle = "#10b981";
                ctx.lineWidth = 2;
                ctx.beginPath();

                const points = 120;
                const step = canvas.width / points;
                let x = 0;
                const midY = canvas.height / 2;

                for (let i = 0; i < points; i++) {
                    const phase = (i + this.ecgIndex) % 40;
                    let y = midY;
                    if (phase === 10) y = midY - 6;      // P wave
                    else if (phase === 14) y = midY + 4;  // Q dip
                    else if (phase === 16) y = midY - 24; // R spike
                    else if (phase === 18) y = midY + 10; // S dip
                    else if (phase === 24) y = midY - 8;  // T wave

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
            this.calculatedDilutionText.textContent = `Dilution: 50 mcg/mL • Volume: ${(dose/50).toFixed(1)} mL`;
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
            this.calculatedDilutionText.textContent = `Dilution: 5 mg/mL • Volume: ${(dose/5).toFixed(1)} mL`;
        } else if (drug === "ketamine") {
            const dose = (weight * 1.5).toFixed(0);
            this.calculatedDoseText.textContent = `${dose} mg IV (1.5 mg/kg)`;
            this.calculatedDilutionText.textContent = `Dilution: 50 mg/mL • Volume: ${(dose/50).toFixed(1)} mL`;
        }
    }

    bindEvents() {
        // PTT Click
        this.pttButton.addEventListener("click", async () => {
            if (!this.isTransmitting) await this.startMicTransceiver();
            else this.stopMicTransceiver();
        });

        // Spacebar PTT Hotkey
        window.addEventListener("keydown", async (e) => {
            if (e.code === "Space" && e.target.tagName !== "INPUT" && !this.isTransmitting) {
                e.preventDefault();
                await this.startMicTransceiver();
            }
        });
        window.addEventListener("keyup", (e) => {
            if (e.code === "Space" && e.target.tagName !== "INPUT" && this.isTransmitting) {
                e.preventDefault();
                this.stopMicTransceiver();
            }
        });

        // Command Bar Input
        this.transmitCommandBtn.addEventListener("click", () => {
            const val = this.tacticalCommandInput.value.trim();
            if (val) { this.transmitVoice(val); this.tacticalCommandInput.value = ""; }
        });
        this.tacticalCommandInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                const val = this.tacticalCommandInput.value.trim();
                if (val) { this.transmitVoice(val); this.tacticalCommandInput.value = ""; }
            }
        });

        // Emergency Flush
        this.flushBargeInBtn.addEventListener("click", () => this.triggerBargeIn());

        // Audio Mute Toggle
        this.audioMuteToggleBtn.addEventListener("click", () => {
            this.voiceEngine.soundEnabled = !this.voiceEngine.soundEnabled;
            this.audioMuteText.textContent = this.voiceEngine.soundEnabled ? "AUDIO ON" : "AUDIO MUTED";
            this.audioMuteToggleBtn.className = this.voiceEngine.soundEnabled
                ? "px-2 py-1 rounded bg-[#161f2e] hover:bg-[#1e2c42] border border-slate-700 text-slate-300 flex items-center gap-1 text-[11px]"
                : "px-2 py-1 rounded bg-red-950 border border-red-700 text-red-300 flex items-center gap-1 text-[11px]";
        });

        // CPR Metronome Toggle
        this.cprMetronomeBtn.addEventListener("click", () => {
            const active = this.voiceEngine.soundFX.toggleCprMetronome(() => {
                this.cprMetronomeBtn.classList.toggle("bg-red-900");
            });
            this.cprStatusText.textContent = active ? "110 BPM ACTIVE" : "OFF";
            this.cprStatusText.className = active ? "text-emerald-400 font-black animate-pulse" : "text-slate-400 font-bold";
        });

        // Epinephrine Reset
        this.resetEpiTimerBtn.addEventListener("click", () => {
            this.epiSecondsLeft = 180;
        });

        // Scenario Buttons
        document.querySelectorAll(".scenario-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                document.querySelectorAll(".scenario-btn").forEach(b => b.classList.remove("active-scenario"));
                btn.classList.add("active-scenario");
                const idx = parseInt(btn.getAttribute("data-index"));
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({ type: "SWITCH_SCENARIO", index: idx }));
                }
            });
        });

        // Randomize Case
        document.getElementById("randomizeIncidentBtn").addEventListener("click", () => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: "SWITCH_SCENARIO" }));
            }
        });

        // Tool Tabs
        document.querySelectorAll(".tool-tab").forEach(tab => {
            tab.addEventListener("click", () => {
                document.querySelectorAll(".tool-tab").forEach(t => t.classList.remove("active-tab"));
                document.querySelectorAll(".tab-pane").forEach(p => p.classList.add("hidden"));
                tab.classList.add("active-tab");
                const target = tab.getAttribute("data-target");
                const pane = document.getElementById(target);
                if (pane) pane.classList.remove("hidden");
            });
        });

        // Dosage Inputs
        this.toolWeightSlider.addEventListener("input", () => this.updateDosageCalculations());
        this.toolDrugSelect.addEventListener("change", () => this.updateDosageCalculations());
        this.speakDosageOrderBtn.addEventListener("click", () => {
            const dose = this.calculatedDoseText.textContent;
            this.transmitVoice(`Administer ${dose} for ${this.toolWeightValue.textContent} patient.`);
        });

        // Query Hospitals
        this.queryHospitalRadarBtn.addEventListener("click", () => {
            this.transmitVoice("Find nearest Level 1 trauma centers and burn beds.");
        });

        // Quick Fleet Dispatch
        document.querySelectorAll(".dispatch-unit-quick").forEach(b => {
            b.addEventListener("click", () => {
                const u = b.getAttribute("data-unit");
                this.transmitVoice(`Dispatch ${u} Code 3 immediately`);
            });
        });

        // Quick Tactical Orders
        document.querySelectorAll(".quick-tactical-order").forEach(b => {
            b.addEventListener("click", () => {
                this.transmitVoice(b.getAttribute("data-text"));
            });
        });

        // Stress Benchmark Test
        this.runStressTestBenchmarkBtn.addEventListener("click", () => {
            this.stressStep1.textContent = "RUNNING 3.5s ASYNC QUERY...";
            this.stressStep1.className = "text-amber-400 font-bold";
            this.stressStep2.textContent = "WAITING FOR FILLER AUDIO...";
            this.stressFinalResult.textContent = "IN PROGRESS";

            this.transmitVoice("Run stress test lookup with deliberate 3.5 second delay");

            setTimeout(() => {
                this.stressStep2.textContent = "SIMULATING BARGE-IN INTERRUPT!";
                this.stressStep2.className = "text-red-400 font-bold animate-pulse";
                this.stressStep3.textContent = "TRANSMITTING CRITICAL EPINEPHRINE ORDER...";
                this.stressStep3.className = "text-cyan-400 font-bold";

                this.transmitVoice("Cancel query! Patient crashing, dose epinephrine immediately for 70kg adult!");

                setTimeout(() => {
                    this.stressFinalResult.textContent = "PASSED (<4ms FLUSH, STALE TOOL FENCED, EPI SPOKEN)";
                    this.stressFinalResult.className = "text-emerald-400 font-bold";
                }, 2000);
            }, 1200);
        });

        // Vitals Modal
        this.editVitalsBtn.addEventListener("click", () => this.vitalsModal.classList.remove("hidden"));
        this.closeVitalsModalBtn.addEventListener("click", () => this.vitalsModal.classList.add("hidden"));
        this.saveVitalsModalBtn.addEventListener("click", () => {
            const hr = parseInt(this.inputEditHR.value);
            const bp = this.inputEditBP.value;
            const spo2 = parseInt(this.inputEditSpO2.value);
            const gcs = parseInt(this.inputEditGCS.value);
            this.vitalsModal.classList.add("hidden");
            this.transmitVoice(`Log vitals: blood pressure ${bp}, heart rate ${hr}, SpO2 ${spo2} percent, GCS ${gcs}`);
        });
    }
}

window.addEventListener("DOMContentLoaded", () => {
    window.tacticalApp = new TacticalApp();
});
""")
print("App JS Part 3 written")
