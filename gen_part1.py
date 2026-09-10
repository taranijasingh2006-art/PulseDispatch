with open("static/index.html", "w", encoding="utf-8") as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AEROMED-911 // Tactical Emergency Voice Dispatch Terminal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="style.css">
</head>
<body class="bg-[#07090e] text-slate-100 min-h-screen font-mono antialiased select-none overflow-x-hidden">

    <!-- Top Tactical Ops Header Bar -->
    <header class="border-b-2 border-[#1e293b] bg-[#0c1017] px-4 py-2.5 shadow-xl flex items-center justify-between">
        <div class="flex items-center space-x-3">
            <div class="w-9 h-9 rounded bg-[#161f2e] border-2 border-[#06b6d4]/50 flex items-center justify-center shadow-inner">
                <i class="fa-solid fa-satellite-dish text-[#06b6d4] text-lg animate-pulse"></i>
            </div>
            <div>
                <div class="flex items-center space-x-2">
                    <span class="font-black text-sm tracking-widest text-[#38bdf8] uppercase">AEROMED // CAD-911</span>
                    <span class="text-[9px] px-1.5 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-600/60 font-bold uppercase tracking-wider">TACTICAL VOICE TERMINAL</span>
                </div>
                <div class="text-[10px] text-slate-400 flex items-center gap-2">
                    <span>SYS: RESQ-VOICE 2.4</span>
                    <span>•</span>
                    <span id="activeVoiceEngine" class="text-emerald-400 font-bold">RIME NEURAL TTS (mist // cora)</span>
                </div>
            </div>
        </div>

        <!-- Top Right Hardware Status Indicators -->
        <div class="flex items-center space-x-3 text-xs">
            <button id="cprMetronomeBtn" class="px-2.5 py-1 rounded bg-[#161f2e] hover:bg-[#1e2c42] border border-slate-700 text-slate-300 flex items-center gap-1.5 transition-all text-[11px]">
                <i class="fa-solid fa-heart-circle-bolt text-red-400"></i>
                <span>CPR (110 BPM):</span>
                <span id="cprStatusText" class="text-slate-400 font-bold">OFF</span>
            </button>

            <button id="audioMuteToggleBtn" class="px-2 py-1 rounded bg-[#161f2e] hover:bg-[#1e2c42] border border-slate-700 text-slate-300 flex items-center gap-1 text-[11px]">
                <i class="fa-solid fa-volume-high text-cyan-400"></i>
                <span id="audioMuteText">AUDIO ON</span>
            </button>

            <div id="netStatusPill" class="flex items-center space-x-1.5 bg-[#0a121d] border border-emerald-500/40 px-3 py-1 rounded">
                <span class="h-2 w-2 rounded-full bg-emerald-500 animate-ping"></span>
                <span class="text-[10px] font-bold text-emerald-400">LINK: CONNECTED</span>
            </div>
        </div>
    </header>

    <!-- Incident Scenario Quick Bar -->
    <section class="bg-[#0f141c] border-b border-[#1e293b] px-4 py-2 flex flex-wrap items-center justify-between gap-2">
        <div class="flex items-center space-x-2">
            <span class="text-[10px] text-slate-400 uppercase font-bold tracking-wider flex items-center gap-1">
                <i class="fa-solid fa-clipboard-list text-amber-400"></i> INCIDENTS:
            </span>
            <div class="flex flex-wrap gap-1.5" id="scenarioButtons">
                <button class="scenario-btn active-scenario text-[11px] px-2.5 py-1 rounded bg-[#1a2333] hover:bg-[#25334a] border border-[#38bdf8]/50 text-cyan-300 font-bold transition-all" data-index="0">
                    ① PEDIATRIC ANAPHYLAXIS (18kg)
                </button>
                <button class="scenario-btn text-[11px] px-2.5 py-1 rounded bg-[#121824] hover:bg-[#1a2333] border border-slate-750 text-slate-300 transition-all" data-index="1">
                    ② ROLLOVER ENTRAPMENT (75kg)
                </button>
                <button class="scenario-btn text-[11px] px-2.5 py-1 rounded bg-[#121824] hover:bg-[#1a2333] border border-slate-750 text-slate-300 transition-all" data-index="2">
                    ③ STEMI / V-TACH (85kg)
                </button>
                <button class="scenario-btn text-[11px] px-2.5 py-1 rounded bg-[#121824] hover:bg-[#1a2333] border border-slate-750 text-slate-300 transition-all" data-index="3">
                    ④ FLASH BURN (80kg)
                </button>
                <button class="scenario-btn text-[11px] px-2.5 py-1 rounded bg-[#121824] hover:bg-[#1a2333] border border-slate-750 text-slate-300 transition-all" data-index="4">
                    ⑤ OPIOID OVERDOSE (65kg)
                </button>
            </div>
        </div>

        <button id="randomizeIncidentBtn" class="text-[11px] px-2.5 py-1 rounded bg-amber-950/60 hover:bg-amber-900 border border-amber-600/50 text-amber-300 font-bold flex items-center gap-1">
            <i class="fa-solid fa-shuffle"></i> RANDOMIZE CASE
        </button>
    </section>

    <!-- Main 3-Column Tactical Command Cockpit -->
    <main class="max-w-[1700px] mx-auto p-3.5 grid grid-cols-1 lg:grid-cols-12 gap-3.5">
""")
print("Part 1 written")
