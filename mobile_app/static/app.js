const API_BASE_URL = 'https://localhost:8443';
let rokuIpAddress = localStorage.getItem('rokuIpAddress') || null;

document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
    checkBrowserSupport();
});

// Load saved IP
function loadConfig() {
    const ipInput = document.getElementById('roku-ip');
    if (rokuIpAddress) ipInput.value = rokuIpAddress;
}

// Save IP + send to backend
function saveConfig() {
    const ipInput = document.getElementById('roku-ip');
    const ip = ipInput.value.trim();

    if (!ip) return showStatus('Please enter a valid IP address', true);

    const ipRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
    if (!ipRegex.test(ip)) return showStatus('Invalid IP address format', true);

    rokuIpAddress = ip;
    localStorage.setItem('rokuIpAddress', ip);

    fetch(`${API_BASE_URL}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ roku_ip: ip })
    })
    .then(res => res.json())
    .then(() => showStatus('Configuration saved'))
    .catch(err => {
        console.error(err);
        showStatus('Failed to save configuration', true);
    });
}

// Status display
function showStatus(message, isError = false) {
    const status = document.getElementById("status");
    status.textContent = message;
    status.classList.remove("hidden");
    status.classList.toggle("error", isError);
    setTimeout(() => status.classList.add("hidden"), 2000);
}

// Voice recognition
let recognition = null;

function checkBrowserSupport() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        showStatus('Voice recognition not supported', true);
        return false;
    }
    return true;
}

function startVoiceRecognition() {
    if (!rokuIpAddress) return showStatus('Set Roku IP first', true);

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return showStatus('Voice recognition not supported', true);

    recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;

    const voiceBtn = document.getElementById('voice-btn');
    const voiceResult = document.getElementById('voice-result');

    voiceBtn.classList.add('listening');
    voiceResult.textContent = 'Listening...';

    recognition.start();

    recognition.onresult = event => {
        const transcript = event.results[0][0].transcript;
        voiceResult.textContent = `You said: "${transcript}"`;
        processVoiceCommand(transcript);
    };

    recognition.onerror = event => {
        showStatus(event.error || 'Voice error', true);
        voiceBtn.classList.remove('listening');
    };

    recognition.onend = () => voiceBtn.classList.remove('listening');
}

// FIXED: Correct Roku endpoint
function sendCommand(command) {
    fetch(`${API_BASE_URL}/api/roku`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
    })
    .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    })
    .then(() => showStatus(`Sent: ${command}`))
    .catch(err => {
        console.error(err);
        showStatus(`Error sending ${command}`, true);
    });
}

// Launch Roku app
function launchApp(name, appId) {
    sendCommand(`Launch:${appId}`);
}
