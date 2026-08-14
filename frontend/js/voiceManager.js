/**
 * Centralized Universal Voice Announcement System
 * Built with Web Speech Synthesis API (window.speechSynthesis) and Queue Management.
 * Guarantees zero speech overlap and clear speech delivery across Kiosks, TV Display, and Agent Console.
 */
class VoiceManager {
    constructor() {
        this.synth = window.speechSynthesis;
        this.queue = [];
        this.isSpeaking = false;
        this.voice = null;
        
        this.initVoice();
    }
    
    initVoice() {
        if (!this.synth) return;
        
        const loadVoices = () => {
            const voices = this.synth.getVoices();
            if (!voices || voices.length === 0) return;
            
            // Search for high-quality English voice
            this.voice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Microsoft') || v.name.includes('Samantha'))) 
                        || voices.find(v => v.lang.startsWith('en')) 
                        || voices[0];
        };
        
        loadVoices();
        if (this.synth.onvoiceschanged !== undefined) {
            this.synth.onvoiceschanged = loadVoices;
        }
    }
    
    speak(text, options = {}) {
        if (!this.synth) {
            console.warn("Web Speech Synthesis API not supported in this browser environment.");
            return;
        }
        
        const announcement = {
            text: text,
            rate: options.rate || 0.9,
            pitch: options.pitch || 1.0,
            volume: options.volume || 1.0,
            onEnd: options.onEnd
        };
        
        this.queue.push(announcement);
        this.processQueue();
    }
    
    processQueue() {
        if (this.isSpeaking || this.queue.length === 0) return;
        
        const item = this.queue.shift();
        this.isSpeaking = true;
        
        // Ensure synthesis engine is not stuck
        if (this.synth.paused) {
            this.synth.resume();
        }
        
        const utterance = new SpeechSynthesisUtterance(item.text);
        if (this.voice) {
            utterance.voice = this.voice;
        }
        utterance.rate = item.rate;
        utterance.pitch = item.pitch;
        utterance.volume = item.volume;
        
        utterance.onend = () => {
            this.isSpeaking = false;
            if (item.onEnd) item.onEnd();
            setTimeout(() => this.processQueue(), 150); // Pause between queued speeches
        };
        
        utterance.onerror = (err) => {
            console.error("Voice Announcement Error:", err);
            this.isSpeaking = false;
            setTimeout(() => this.processQueue(), 150);
        };
        
        this.synth.speak(utterance);
    }
    
    // Core Announcement Functions
    announceTokenCall(tokenNumber, counterNumber, serviceName = "") {
        const tokenSpoken = this.formatTokenForSpeech(tokenNumber);
        const text = serviceName 
            ? `Token ${tokenSpoken}, please proceed to Counter ${counterNumber} for ${serviceName}.`
            : `Token ${tokenSpoken}, please proceed to Counter ${counterNumber}.`;
        this.speak(text, { rate: 0.88, pitch: 1.05 });
    }
    
    announceTokenRecall(tokenNumber, counterNumber) {
        const tokenSpoken = this.formatTokenForSpeech(tokenNumber);
        const text = `Re-calling Token ${tokenSpoken}, please proceed to Counter ${counterNumber}.`;
        this.speak(text, { rate: 0.88, pitch: 1.1 });
    }
    
    announceTokenGeneration(tokenNumber) {
        const tokenSpoken = this.formatTokenForSpeech(tokenNumber);
        const text = `Your token number is ${tokenSpoken}. Please wait for your turn.`;
        this.speak(text, { rate: 0.9, pitch: 1.0 });
    }
    
    announceRedirection(centerName) {
        const text = `Redirecting to ${centerName} kiosk.`;
        this.speak(text, { rate: 0.95, pitch: 1.0 });
    }
    
    // Format token numbers for clear speech (e.g., "AC-01" -> "A C 0 1")
    formatTokenForSpeech(tokenNumber) {
        if (!tokenNumber) return "";
        return tokenNumber.replace("-", " ").split("").join(" ");
    }
}

// Global Voice Manager instance
window.voiceManager = new VoiceManager();
