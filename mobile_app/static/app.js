// Configuration
const API_BASE_URL = window.location.origin;
let rokuIpAddress = localStorage.getItem('rokuIpAddress') || '';

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadConfig();
    checkBrowserSupport();
});

// Configuration Management
function loadConfig() {
    const ipInput = document.getElementById('roku-ip');
    if (rokuIpAddress) {
        ipInput.value = rokuIpAddress;
    }
}

function saveConfig() {
    const ipInput = document.getElementById('roku-ip');
    const ip = ipInput.value.trim();
    
    if (!ip) {
        showStatus('Please enter a valid IP address', 'error');
        return;
    }
    
    // Validate IP format
    const ipRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
    if (!ipRegex.test(ip)) {
        showStatus('Invalid IP address format', 'error');
        return;
    }
    
    rokuIpAddress = ip;
    localStorage.setItem('rokuIpAddress', ip);
    
    // Send to backend
    fetch(`${API_BASE_URL}/api/config`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ roku_ip: ip })
    })
    .then(response => response.json())
    .then(data => {
        showStatus('Configuration saved successfully', 'success');
    })
    .catch(error => {
        showStatus('Failed to save configuration', 'error');
        console.error('Error:', error);
    });
}

// Status Messages
function showStatus(message, type) {
    const statusEl = document.getElementById('status');
    statusEl.textContent = message;
    statusEl.className = `status ${type}`;
    statusEl.classList.remove('hidden');
    
    setTimeout(() => {
        statusEl.classList.add('hidden');
    }, 3000);
}

// Voice Recognition
let recognition = null;

function isIOS() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent);
}

function checkBrowserSupport() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const isSupported = SpeechRecognition !== undefined;

    if (!isSupported) {
        showStatus('Voice recognition is not supported in this browser. Please use a supported browser like Chrome, Edge, or Safari.', 'error');
        return false;
    }

    // Check if microphone permissions are granted
    navigator.permissions.query({ name: 'microphone' }).then(permissionStatus => {
        if (permissionStatus.state === 'denied') {
            showStatus('Microphone access is denied. Please enable it in your browser settings.', 'error');
        } else if (permissionStatus.state === 'prompt') {
            showStatus('Please allow microphone access to use voice recognition.', 'error');
        }
    }).catch(error => {
        console.error('Error checking microphone permissions:', error);
        showStatus('Unable to check microphone permissions. Please ensure your browser supports microphone access.', 'error');
    });

    return isSupported;
}

function startVoiceRecognition() {
    if (!rokuIpAddress) {
        showStatus('Please configure your Roku IP address first', 'error');
        return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        showStatus('Voice recognition is not supported on this device. Please use a supported browser like Chrome, Edge, or Safari.', 'error');
        return;
    }

    try {
        recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        recognition.continuous = false;

        const voiceBtn = document.getElementById('voice-btn');
        const voiceResult = document.getElementById('voice-result');

        voiceBtn.classList.add('listening');
        voiceResult.textContent = 'Listening..
