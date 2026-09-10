with open("static/index.html", "a", encoding="utf-8") as f:
    f.write("""
        <!-- LEFT COLUMN: Patient Telemetry & Live Vitals Monitor (Cols 1-3) -->
        <div class="lg:col-span-3 space-y-3">
            <div class="bg-[#0e131b] border-2 border-[#1e293b] rounded-lg p-3.5 shadow-lg relative overflow-hidden">
                <div class="flex items-center justify-between border-b border-slate-800 pb-2 mb-2.5">
                    <span id="triageBadge" class="text-[11px] font-black px-2 py-0.5 rounded bg-red-950 text-red-400 border border-red-600/80 uppercase">
                        PRIORITY 1 - IMMEDIATE
                    </span>
                    <span id="incidentIdText" class="text-xs font-bold text-slate-400">MED-7829</span>
                </div>

                <h2 id="incidentTitleText" class="text-sm font-black text-white leading-tight uppercase mb-1">
                    Pediatric Anaphylaxis & Severe Stridor
                </h2>
                <div id="incidentLocationText" class="text-[11px] text-slate-400 mb-2.5 flex items-center gap-1">
                    <i class="fa-solid fa-location-crosshairs text-red-400"></i>
                    <span>Lincoln Elementary Cafeteria, Zone 2</span>
                </div>

                <div class="bg-[#080b10] border border-slate-800 rounded p-2 text-[11px] space-y-1 mb-2">
                    <div class="flex justify-between"><span class="text-slate-400">PATIENT:</span><span id="patName" class="text-white font-bold">Tommy R.</span></div>
                    <div class="flex justify-between"><span class="text-slate-400">AGE / GENDER:</span><span id="patAgeGender" class="text-cyan-300 font-bold">5 YRS / MALE</span></div>
                    <div class="flex justify-between"><span class="text-slate-400">WEIGHT:</span><span id="patWeight" class="text-amber-400 font-bold">18.0 KG</span></div>
                    <div class="flex justify-between"><span class="text-slate-400">ALLERGIES:</span><span id="patAllergy" class="text-red-400 font-bold">Peanut / Ingestion</span></div>
                </div>

                <div class="text-[10px] text-slate-400 bg-[#080b10] p-2 rounded border border-slate-800">
                    <span class="font-bold text-slate-300">CHIEF COMPLAINT:</span>
                    <p id="patComplaint" class="text-slate-200 mt-0.5">Acute respiratory distress, facial angioedema, inspiratory stridor.</p>
                </div>
            </div>

            <!-- Live Clinical Vitals Monitor -->
            <div class="bg-[#080c12] border-2 border-[#1a2333] rounded-lg p-3 shadow-xl space-y-2.5">
                <div class="flex items-center justify-between border-b border-slate-800 pb-1.5">
                    <span class="text-[11px] font-bold text-slate-300 flex items-center gap-1.5">
                        <i class="fa-solid fa-heart-pulse text-red-500"></i> PHYSIO TELEMETRY MONITOR
                    </span>
                    <button id="editVitalsBtn" class="text-[10px] text-cyan-400 hover:text-cyan-300 font-bold uppercase underline">
                        [EDIT VITALS]
                    </button>
                </div>

                <!-- Live ECG Canvas -->
                <div class="bg-black border border-emerald-900/50 rounded h-16 relative overflow-hidden flex items-center">
                    <canvas id="ecgCanvas" class="w-full h-full"></canvas>
                    <div class="absolute top-1 left-2 text-[9px] text-emerald-500 font-bold tracking-widest">LEAD II // 25mm/s</div>
                </div>

                <div class="grid grid-cols-2 gap-2 text-center">
                    <div class="bg-[#0d131c] border border-red-900/60 p-2 rounded">
                        <div class="text-[10px] text-slate-400 font-bold uppercase">HEART RATE</div>
                        <div class="text-2xl font-black text-red-400 mt-0.5" id="valHR">142 <span class="text-[10px] text-slate-400 font-normal">BPM</span></div>
                        <div class="text-[9px] text-red-500 font-bold" id="hrStatus">TACHYCARDIA</div>
                    </div>
                    <div class="bg-[#0d131c] border border-blue-900/60 p-2 rounded">
                        <div class="text-[10px] text-slate-400 font-bold uppercase">NIBP (mmHg)</div>
                        <div class="text-2xl font-black text-blue-400 mt-0.5" id="valBP">78/48</div>
                        <div class="text-[9px] text-blue-400 font-bold" id="bpStatus">HYPOTENSION</div>
                    </div>
                    <div class="bg-[#0d131c] border border-emerald-900/60 p-2 rounded">
                        <div class="text-[10px] text-slate-400 font-bold uppercase">SpO2 %</div>
                        <div class="text-2xl font-black text-emerald-400 mt-0.5" id="valSpO2">89 <span class="text-[10px] text-slate-400 font-normal">%</span></div>
                        <div class="text-[9px] text-emerald-400 font-bold" id="spo2Status">HYPOXEMIA</div>
                    </div>
                    <div class="bg-[#0d131c] border border-purple-900/60 p-2 rounded">
                        <div class="text-[10px] text-slate-400 font-bold uppercase">GCS SCORE</div>
                        <div class="text-2xl font-black text-purple-400 mt-0.5" id="valGCS">13 <span class="text-[10px] text-slate-400 font-normal">/ 15</span></div>
                        <div class="text-[9px] text-purple-400 font-bold" id="gcsStatus">MILD IMPAIRMENT</div>
                    </div>
                </div>

                <!-- Epinephrine Timer Clock -->
                <div class="bg-[#0a0f16] border border-amber-600/40 p-2 rounded flex items-center justify-between text-xs">
                    <div>
                        <div class="text-[10px] text-amber-400 font-bold uppercase flex items-center gap-1">
                            <i class="fa-solid fa-stopwatch"></i> EPI DOSE INTERVAL TIMER
                        </div>
                        <div class="text-sm font-black text-white font-mono" id="epiTimerDisplay">03:00 (REPEAT IN: 2m 45s)</div>
                    </div>
                    <button id="resetEpiTimerBtn" class="px-2 py-1 bg-amber-950 hover:bg-amber-900 text-amber-300 border border-amber-600/60 text-[10px] font-bold rounded">
                        RESET 3M
                    </button>
                </div>
            </div>
        </div>

        <!-- CENTER COLUMN: Tactical Voice Radio Transceiver & Telemetry (Cols 4-8) -->
        <div class="lg:col-span-5 space-y-3">
            <div class="bg-[#0d1118] border-2 border-[#223046] rounded-lg p-3.5 shadow-2xl relative">
                <div class="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
                    <div class="flex items-center space-x-2">
                        <span class="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" id="pttLed"></span>
                        <h3 class="text-xs font-black tracking-widest text-slate-200 uppercase">
                            TACTICAL TRANSCEIVER // VOICE CHANNEL 1
                        </h3>
                    </div>
                    <button id="flushBargeInBtn" class="px-3 py-1 bg-red-950 hover:bg-red-900 border-2 border-red-600 text-red-300 text-[11px] font-black rounded uppercase tracking-wider shadow-lg shadow-red-950/60 flex items-center gap-1.5 transition-all">
                        <i class="fa-solid fa-hand"></i> EMERGENCY FLUSH
                    </button>
                </div>

                <!-- Audio Oscilloscope & Live Mic VU Meter -->
                <div class="grid grid-cols-12 gap-2 mb-3">
                    <div class="col-span-10 bg-black border-2 border-[#1a2333] rounded h-28 relative overflow-hidden flex items-center justify-center">
                        <canvas id="oscilloscopeCanvas" class="w-full h-full"></canvas>
                        
                        <div id="liveHearingBanner" class="absolute bottom-2 left-2 right-2 bg-[#0c1420]/95 border border-[#38bdf8] px-2.5 py-1 rounded text-xs text-[#38bdf8] flex items-center gap-2 shadow-lg hidden">
                            <i class="fa-solid fa-microphone text-emerald-400 animate-pulse"></i>
                            <span class="font-bold text-slate-400 uppercase text-[10px]">MIC HEARING:</span>
                            <span id="liveHearingPillText" class="text-white font-bold italic">...</span>
                        </div>

                        <div id="transceiverStatusText" class="absolute top-2 left-2 text-[9px] font-bold text-slate-500 tracking-wider uppercase">
                            STANDBY // CLICK PTT BUTTON OR PRESS SPACE TO TALK
                        </div>
                    </div>

                    <div class="col-span-2 bg-black border-2 border-[#1a2333] rounded p-1.5 flex flex-col justify-between items-center">
                        <div class="text-[8px] text-slate-400 font-bold uppercase">VU dB</div>
                        <div class="w-full flex-1 flex flex-col-reverse gap-0.5 py-1" id="vuMeterLeds"></div>
                        <div class="text-[9px] font-mono text-emerald-400 font-bold" id="vuDbText">0%</div>
                    </div>
                </div>

                <!-- Big Tactile PTT (Push-To-Talk) Button -->
                <div class="mb-3">
                    <button id="pttButton" class="w-full py-4 rounded-lg bg-gradient-to-b from-[#1e293b] to-[#0f172a] hover:from-[#2a384f] hover:to-[#162238] border-2 border-[#38bdf8]/60 text-white font-black text-sm tracking-widest uppercase shadow-2xl flex items-center justify-center gap-3 transition-all active:scale-[0.99] active:border-emerald-500">
                        <i class="fa-solid fa-microphone-lines text-xl text-[#38bdf8]" id="pttIcon"></i>
                        <span id="pttLabelText">PUSH TO TALK (OR PRESS SPACE)</span>
                    </button>
                </div>

                <!-- Command Line Text Input -->
                <div class="flex items-center gap-2 mb-3">
                    <div class="relative flex-1">
                        <input id="tacticalCommandInput" type="text" placeholder="TRANSMIT CLINICAL ORDER OR COMMAND (e.g. 'Dose 0.3mg epi', 'Find burn beds')..." class="w-full bg-black border-2 border-[#1e293b] focus:border-[#38bdf8] rounded px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none font-mono">
                    </div>
                    <button id="transmitCommandBtn" class="px-4 py-2 bg-[#0284c7] hover:bg-[#0369a1] text-white text-xs font-black uppercase rounded tracking-wider transition-all">
                        SEND
                    </button>
                </div>

                <!-- Voice Engine Selector Options -->
                <div class="flex items-center justify-between text-[11px] bg-[#070a0f] p-2 rounded border border-slate-800">
                    <div class="flex items-center space-x-1.5">
                        <span class="text-slate-400">SPEAKER:</span>
                        <select id="speakerSelect" class="bg-black text-cyan-300 font-bold border border-slate-750 px-2 py-0.5 rounded text-[11px]">
                            <option value="cora">Cora (Flight Dispatch)</option>
                            <option value="marsh">Marsh (Tactical Field Ops)</option>
                            <option value="allison">Allison (Critical Care)</option>
                            <option value="amber">Amber (Incident Command)</option>
                            <option value="creed">Creed (Heavy Rescue)</option>
                        </select>
                    </div>

                    <div class="flex items-center space-x-1.5">
                        <span class="text-slate-400">MODEL:</span>
                        <select id="modelSelect" class="bg-black text-emerald-400 font-bold border border-slate-750 px-2 py-0.5 rounded text-[11px]">
                            <option value="mist">mist (Ultra-Low Latency Streaming)</option>
                            <option value="arcana">arcana (Dynamic Range)</option>
                            <option value="aura">aura (Standard)</option>
                        </select>
                    </div>
                </div>
            </div>

            <!-- Hard Voice Telemetry Diagnostics HUD -->
            <div class="bg-[#0b0f16] border-2 border-[#1e293b] rounded-lg p-3">
                <div class="flex items-center justify-between border-b border-slate-800 pb-1 mb-2">
                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                        <i class="fa-solid fa-gauge text-cyan-400"></i> REALTIME HARD-VOICE TELEMETRY
                    </span>
                    <span class="text-[9px] font-mono text-cyan-400">ACCEPTANCE GAUGES</span>
                </div>

                <div class="grid grid-cols-4 gap-2 text-center text-xs">
                    <div class="bg-black p-2 rounded border border-slate-800">
                        <div class="text-[9px] text-slate-400 uppercase font-bold">RIME TTFB</div>
                        <div class="text-sm font-black text-cyan-400 font-mono mt-0.5" id="telemetryTTFB">-- ms</div>
                    </div>
                    <div class="bg-black p-2 rounded border border-slate-800">
                        <div class="text-[9px] text-slate-400 uppercase font-bold">FLUSH DELAY</div>
                        <div class="text-sm font-black text-emerald-400 font-mono mt-0.5" id="telemetryFlush">< 3.8 ms</div>
                    </div>
                    <div class="bg-black p-2 rounded border border-slate-800">
                        <div class="text-[9px] text-slate-400 uppercase font-bold">TURN FENCE</div>
                        <div class="text-sm font-black text-purple-400 font-mono mt-0.5" id="telemetryTurn">#0</div>
                    </div>
                    <div class="bg-black p-2 rounded border border-slate-800">
                        <div class="text-[9px] text-slate-400 uppercase font-bold">TOOL LATENCY</div>
                        <div class="text-sm font-black text-amber-400 font-mono mt-0.5" id="telemetryTool">-- ms</div>
                    </div>
                </div>
            </div>

            <!-- Real-time Spoken Conversation Transcript Log -->
            <div class="bg-[#090d13] border-2 border-[#1e293b] rounded-lg p-3 flex flex-col h-64 shadow-inner">
                <div class="flex items-center justify-between border-b border-slate-800 pb-1.5 mb-2">
                    <span class="text-[10px] font-bold text-slate-300 uppercase flex items-center gap-1.5">
                        <i class="fa-solid fa-tower-broadcast text-cyan-400"></i> TACTICAL TRANSCRIPT FEED
                    </span>
                    <span id="turnCounterBadge" class="text-[9px] text-slate-400 font-mono">0 TURNS</span>
                </div>
                
                <div id="radioTranscriptFeed" class="flex-1 overflow-y-auto space-y-2 pr-1 text-xs">
                    <div class="p-2 rounded bg-black/60 border border-slate-800/80 text-slate-300">
                        <div class="flex items-center justify-between text-[10px] text-cyan-400 font-bold mb-0.5">
                            <span>[00:00:01] PULSEDISPATCH DISPATCH COPILOT</span>
                            <span class="text-slate-500">INIT</span>
                        </div>
                        <p class="text-slate-300">Tactical voice channel active on Incident MED-7829. Standing by for hands-free orders, dosage calculations, and hospital diversion queries.</p>
                    </div>
                </div>
            </div>
        </div>
""")
print("Part 2 written")
