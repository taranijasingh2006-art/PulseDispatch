with open("static/app.js", "w", encoding="utf-8") as f:
    f.write("""/**
 * AEROMED-911 // Tactical Voice Transceiver & Clinical Telemetry Engine
 * Full-Duplex WebAudio + Hardware Mic VU Analyser + Rime Neural TTS Streamer
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
            osc.frequency.setValueAtTime(1200, now + 0.05);
            gain.gain.setValueAtTime(0.15, now);
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
            osc.frequency.exponentialRampToValueAtTime(120, now + 0.07);
            gain.gain.setValueAtTime(0.25, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.07);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(now);
            osc.stop(now + 0.07);
        } catch (e) {}
    }

    toggleCprMetronome(onTick) {
        this.init();
        if (this.cprActive) {
            clearInterval(this.cprInterval);
            this.cprActive = false;
            return false;
        } else {
            this.cprActive = true;
            // 110 BPM = 545.45 ms interval
            this.cprInterval = setInterval(() => {
                try {
                    const now = this.ctx.currentTime;
                    const osc = this.ctx.createOscillator();
                    const gain = this.ctx.createGain();
                    osc.type = "square";
                    osc.frequency.setValueAtTime(1000, now);
                    gain.gain.setValueAtTime(0.08, now);
                    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);
                    osc.connect(gain);
                    gain.connect(this.ctx.destination);
                    osc.start(now);
                    osc.stop(now + 0.04);
                    if (onTick) onTick();
                } catch (e) {}
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
    }

    speak(text, turnId) {
        if (!this.soundEnabled || !text) return;
        this.currentTurnId = turnId;
        this.isPlaying = true;

        if ("speechSynthesis" in window) {
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 1.05;
            utterance.pitch = 1.0;
            
            const voices = window.speechSynthesis.getVoices();
            const femaleVoice = voices.find(v => v.lang.includes("en") && (v.name.includes("Female") || v.name.includes("Samantha") || v.name.includes("Zira") || v.name.includes("Natural")));
            if (femaleVoice) {
                utterance.voice = femaleVoice;
            }

            utterance.onend = () => {
                if (this.currentTurnId === turnId) {
                    this.isPlaying = false;
                }
            };

            utterance.onerror = () => {
                this.isPlaying = false;
            };

            this.soundFX.playRogerBeep();
            window.speechSynthesis.speak(utterance);
        }
    }

    stopAll(newTurnId = null) {
        const t0 = performance.now();
        if ("speechSynthesis" in window) {
            window.speechSynthesis.cancel();
        }
        this.isPlaying = false;
        this.currentTurnId = newTurnId;
        this.soundFX.playFlushClick();
        return (performance.now() - t0).toFixed(2);
    }
}
""")
print("App JS Part 1 written")
