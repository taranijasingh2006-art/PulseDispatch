with open("static/index.html", "a", encoding="utf-8") as f:
    f.write("""
        <!-- RIGHT COLUMN: Interactive Clinical Tools & Resource Dispatch (Cols 9-12) -->
        <div class="lg:col-span-4 space-y-3">
            <div class="bg-[#0c1017] border-2 border-[#223046] rounded-lg shadow-xl overflow-hidden">
                <div class="grid grid-cols-4 bg-[#080b10] border-b-2 border-slate-800 text-[10px] font-bold">
                    <button class="tool-tab active-tab py-2.5 text-center text-cyan-300 border-r border-slate-800 hover:bg-[#121824] transition-all" data-target="tabDosage">
                        💉 DOSAGE
                    </button>
                    <button class="tool-tab py-2.5 text-center text-slate-400 border-r border-slate-800 hover:bg-[#121824] transition-all" data-target="tabHospital">
                        🏥 HOSPITALS
                    </button>
                    <button class="tool-tab py-2.5 text-center text-slate-400 border-r border-slate-800 hover:bg-[#121824] transition-all" data-target="tabFleet">
                        🚁 FLEET
                    </button>
                    <button class="tool-tab py-2.5 text-center text-slate-400 hover:bg-[#121824] transition-all" data-target="tabStress">
                        ⚠️ STRESS
                    </button>
                </div>

                <!-- TAB 1: Clinical Medication Calculator -->
                <div id="tabDosage" class="tab-pane p-3.5 space-y-3">
                    <div class="text-[11px] text-slate-400 font-bold uppercase flex justify-between">
                        <span>EMERGENCY DRUG DOSAGE CALCULATOR</span>
                        <span class="text-amber-400">WEIGHT PROTOCOL</span>
                    </div>

                    <div>
                        <label class="text-[10px] text-slate-400 block mb-1 font-bold uppercase">SELECT MEDICATION</label>
                        <select id="toolDrugSelect" class="w-full bg-black text-white border-2 border-slate-800 rounded p-2 text-xs font-bold focus:border-cyan-500">
                            <option value="epinephrine">Epinephrine (Anaphylaxis 1:1,000 / Arrest 1:10,000)</option>
                            <option value="amiodarone">Amiodarone (V-Tach / V-Fib)</option>
                            <option value="fentanyl">Fentanyl Citrate (Severe Pain / Trauma)</option>
                            <option value="naloxone">Naloxone Narcan (Opioid Reversal)</option>
                            <option value="atropine">Atropine Sulfate (Symptomatic Bradycardia)</option>
                            <option value="midazolam">Midazolam Versed (Status Epilepticus)</option>
                            <option value="ketamine">Ketamine HCl (RSI / Dissociative Analgesia)</option>
                        </select>
                    </div>

                    <div>
                        <div class="flex justify-between items-center mb-1">
                            <span class="text-[10px] text-slate-400 font-bold uppercase">PATIENT WEIGHT</span>
                            <span id="toolWeightValue" class="text-base font-black text-cyan-400 font-mono">18.0 KG</span>
                        </div>
                        <input id="toolWeightSlider" type="range" min="3" max="130" step="1" value="18" class="w-full accent-cyan-500 cursor-pointer">
                    </div>

                    <div class="bg-black border-2 border-emerald-600/60 rounded p-3 space-y-1">
                        <div class="text-[9px] text-emerald-400 font-bold uppercase">CALCULATED DOSE & ROUTE</div>
                        <div id="calculatedDoseText" class="text-base font-black text-emerald-300 font-mono">0.18 mg IM (Anterolateral Thigh)</div>
                        <div id="calculatedDilutionText" class="text-[11px] text-slate-400">Dilution: 1 mg in 1 mL (1:1,000) • Volume: 0.18 mL</div>
                    </div>

                    <button id="speakDosageOrderBtn" class="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-black font-black text-xs uppercase rounded tracking-wider shadow-lg flex items-center justify-center gap-2 transition-all">
                        <i class="fa-solid fa-volume-high"></i> TRANSMIT & SPEAK ORDER VIA RIME
                    </button>
                </div>

                <!-- TAB 2: Regional Trauma & Burn Hospital Radar -->
                <div id="tabHospital" class="tab-pane p-3.5 space-y-3 hidden">
                    <div class="flex items-center justify-between text-[11px] text-slate-400 font-bold uppercase">
                        <span>REGIONAL TRAUMA / BURN BEDS</span>
                        <span class="text-emerald-400">LIVE STATUS</span>
                    </div>

                    <div class="space-y-2 max-h-72 overflow-y-auto pr-1" id="hospitalsListContainer"></div>

                    <button id="queryHospitalRadarBtn" class="w-full py-2 bg-[#0284c7] hover:bg-[#0369a1] text-white font-bold text-xs uppercase rounded transition-all flex items-center justify-center gap-1.5">
                        <i class="fa-solid fa-radar"></i> QUERY ALL REGIONAL BEDS
                    </button>
                </div>

                <!-- TAB 3: Fleet & Resource Dispatch Console -->
                <div id="tabFleet" class="tab-pane p-3.5 space-y-3 hidden">
                    <div class="flex items-center justify-between text-[11px] text-slate-400 font-bold uppercase">
                        <span>DISPATCHED UNIT MANIFEST</span>
                        <span class="text-cyan-400 font-mono">GPS TRACKING</span>
                    </div>

                    <div class="space-y-2 max-h-64 overflow-y-auto pr-1" id="fleetListContainer"></div>

                    <div class="grid grid-cols-2 gap-2 pt-1 border-t border-slate-800">
                        <button class="dispatch-unit-quick text-[10px] p-2 bg-[#16202e] hover:bg-[#1e2d42] border border-slate-700 rounded text-cyan-300 font-bold" data-unit="Air Evac Medevac Helicopter">
                            🚁 AIR MEDEVAC
                        </button>
                        <button class="dispatch-unit-quick text-[10px] p-2 bg-[#16202e] hover:bg-[#1e2d42] border border-slate-700 rounded text-amber-300 font-bold" data-unit="Heavy Extrication Rescue Squad">
                            🚒 RESCUE SQUAD
                        </button>
                    </div>
                </div>

                <!-- TAB 4: Hackathon 3.5s Delay Stress Test -->
                <div id="tabStress" class="tab-pane p-3.5 space-y-3 hidden">
                    <div class="text-[11px] text-amber-400 font-black uppercase flex items-center gap-1.5">
                        <i class="fa-solid fa-flask-vial"></i> HARD-VOICE ACCEPTANCE TEST BENCH
                    </div>

                    <p class="text-[10px] text-slate-300 leading-relaxed bg-black p-2.5 rounded border border-slate-800">
                        Injects a 3.5s delay into a regional lookup. While speaking status filler, simulates a clinician barge-in. Verifies queued audio stops in &lt;5ms and stale tool results are fenced.
                    </p>

                    <button id="runStressTestBenchmarkBtn" class="w-full py-3 bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-500 hover:to-amber-500 text-white font-black text-xs uppercase rounded tracking-wider shadow-lg flex items-center justify-center gap-2 transition-all">
                        <i class="fa-solid fa-bolt"></i> RUN 3.5s DELAY + BARGE-IN BENCHMARK
                    </button>

                    <div class="bg-black border border-slate-800 p-2.5 rounded text-[10px] space-y-1 font-mono">
                        <div class="text-slate-400">TEST STEP 1: <span id="stressStep1" class="text-slate-500">STANDBY</span></div>
                        <div class="text-slate-400">TEST STEP 2: <span id="stressStep2" class="text-slate-500">STANDBY</span></div>
                        <div class="text-slate-400">TEST STEP 3: <span id="stressStep3" class="text-slate-500">STANDBY</span></div>
                        <div class="text-slate-400">TEST RESULT: <span id="stressFinalResult" class="text-slate-500">STANDBY</span></div>
                    </div>
                </div>
            </div>

            <!-- Quick Clinical Voice Triggers Box -->
            <div class="bg-[#0b0f16] border-2 border-[#1e293b] rounded-lg p-3 space-y-2">
                <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between">
                    <span>⚡ ONE-TOUCH TRANSMISSIONS</span>
                    <span class="text-cyan-400">CLICK OR SPEAK</span>
                </div>

                <div class="grid grid-cols-2 gap-1.5">
                    <button class="quick-tactical-order text-[10px] p-2 bg-[#101722] hover:bg-[#1a2538] border border-slate-800 hover:border-cyan-500 text-slate-200 font-bold rounded text-left transition-all" data-text="Calculate weight-based epinephrine dosage immediately for this patient">
                        💉 Dose Epinephrine
                    </button>
                    <button class="quick-tactical-order text-[10px] p-2 bg-[#101722] hover:bg-[#1a2538] border border-slate-800 hover:border-cyan-500 text-slate-200 font-bold rounded text-left transition-all" data-text="Find nearest Level 1 trauma center with burn beds">
                        🏥 Level 1 Trauma
                    </button>
                    <button class="quick-tactical-order text-[10px] p-2 bg-[#101722] hover:bg-[#1a2538] border border-slate-800 hover:border-cyan-500 text-slate-200 font-bold rounded text-left transition-all" data-text="Log vitals: blood pressure 82/50, heart rate 138, SpO2 91%, GCS 12">
                        📊 Log Trauma Vitals
                    </button>
                    <button class="quick-tactical-order text-[10px] p-2 bg-[#101722] hover:bg-[#1a2538] border border-slate-800 hover:border-cyan-500 text-slate-200 font-bold rounded text-left transition-all" data-text="Dispatch Air Evac Medevac helicopter priority Code 3">
                        🚁 Air Medevac
                    </button>
                    <button class="quick-tactical-order text-[10px] p-2 bg-[#101722] hover:bg-[#1a2538] border border-slate-800 hover:border-cyan-500 text-slate-200 font-bold rounded text-left transition-all" data-text="Calculate 300 milligrams amiodarone for persistent ventricular fibrillation">
                        ⚡ Dose Amiodarone
                    </button>
                    <button class="quick-tactical-order text-[10px] p-2 bg-[#101722] hover:bg-[#1a2538] border border-slate-800 hover:border-cyan-500 text-slate-200 font-bold rounded text-left transition-all" data-text="Administer naloxone narcan 2 milligrams intranasally">
                        💊 Dose Narcan
                    </button>
                </div>
            </div>
        </div>

    </main>

    <!-- Modal: Vitals Manual Editor -->
    <div id="vitalsModal" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 hidden flex items-center justify-center p-4">
        <div class="bg-[#0f141c] border-2 border-[#1e293b] rounded-lg max-w-sm w-full p-4 space-y-3 shadow-2xl">
            <div class="flex justify-between items-center border-b border-slate-800 pb-2">
                <span class="text-xs font-black text-white uppercase">UPDATE PATIENT VITALS</span>
                <button id="closeVitalsModalBtn" class="text-slate-400 hover:text-white"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="space-y-2 text-xs">
                <div>
                    <label class="text-[10px] text-slate-400 font-bold">HEART RATE (BPM)</label>
                    <input id="inputEditHR" type="number" value="142" class="w-full bg-black border border-slate-750 p-1.5 rounded text-white font-mono">
                </div>
                <div>
                    <label class="text-[10px] text-slate-400 font-bold">BLOOD PRESSURE (mmHg)</label>
                    <input id="inputEditBP" type="text" value="78/48" class="w-full bg-black border border-slate-750 p-1.5 rounded text-white font-mono">
                </div>
                <div>
                    <label class="text-[10px] text-slate-400 font-bold">OXYGEN SATURATION (SpO2 %)</label>
                    <input id="inputEditSpO2" type="number" value="89" class="w-full bg-black border border-slate-750 p-1.5 rounded text-white font-mono">
                </div>
                <div>
                    <label class="text-[10px] text-slate-400 font-bold">GLASGOW COMA SCALE (GCS / 15)</label>
                    <input id="inputEditGCS" type="number" value="13" class="w-full bg-black border border-slate-750 p-1.5 rounded text-white font-mono">
                </div>
            </div>
            <button id="saveVitalsModalBtn" class="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-black font-black text-xs uppercase rounded">
                SAVE & SYNC TELEMETRY
            </button>
        </div>
    </div>

    <script src="app.js"></script>
</body>
</html>
""")
print("Part 3 written")
