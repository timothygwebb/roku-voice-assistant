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

function checkBrowserSupport() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        console.log('Speech recognition not supported');
        return false;
    }
    return true;
}

function startVoiceRecognition() {
    if (!rokuIpAddress) {
        showStatus('Please configure your Roku IP address first', 'error');
        return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        showStatus('Voice recognition not supported on this device', 'error');
        return;
    }
    
    recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    
    const voiceBtn = document.getElementById('voice-btn');
    const voiceResult = document.getElementById('voice-result');
    
    voiceBtn.classList.add('listening');
    voiceResult.textContent = 'Listening...';
    
    recognition.start();
    
    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        voiceResult.textContent = `You said: "${transcript}"`;
        processVoiceCommand(transcript);
    };
    
    // Update the recognition.onerror handler to log the error and provide detailed feedback
    recognition.onerror = function(event) {
        console.error('Voice recognition error:', event.error);
        let errorMessage = 'Voice recognition error';

        switch (event.error) {
            case 'no-speech':
                errorMessage = 'No speech detected. Please try again.';
                break;
            case 'audio-capture':
                errorMessage = 'No microphone detected. Please check your microphone settings.';
                break;
            case 'not-allowed':
                errorMessage = 'Microphone access denied. Please allow microphone access in your browser settings.';
                break;
            default:
                errorMessage = `An error occurred: ${event.error}`;
        }

        voiceResult.textContent = errorMessage;
        showStatus(errorMessage, 'error');
        voiceBtn.classList.remove('listening');
    };
    
    recognition.onend = function() {
        voiceBtn.classList.remove('listening');
    };
}

function processVoiceCommand(command) {
    const lowerCommand = command.toLowerCase();
    
    // Send to backend for processing
    fetch(`${API_BASE_URL}/api/voice`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command: command })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showStatus(data.message || 'Command executed', 'success');
        } else {
            showStatus(data.message || 'Command failed', 'error');
        }
    })
    .catch(error => {
        showStatus('Failed to process voice command', 'error');
        console.error('Error:', error);
    });
}

// Roku Commands
function sendCommand(key) {
    if (!rokuIpAddress) {
        showStatus('Please configure your Roku IP address first', 'error');
        return;
    }
    
    fetch(`${API_BASE_URL}/api/keypress`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ key: key })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showStatus(`${key} pressed`, 'success');
        } else {
            showStatus(data.message || 'Command failed', 'error');
        }
    })
    .catch(error => {
        showStatus('Failed to send command', 'error');
        console.error('Error:', error);
    });
}

function launchApp(appName, appId) {
    if (!rokuIpAddress) {
        showStatus('Please configure your Roku IP address first', 'error');
        return;
    }
    
    fetch(`${API_BASE_URL}/api/launch`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ app_id: appId, app_name: appName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showStatus(`Launching ${appName}`, 'success');
        } else {
            showStatus(data.message || 'Failed to launch app', 'error');
        }
    })
    .catch(error => {
        showStatus('Failed to launch app', 'error');
        console.error('Error:', error);
    });
}

// PWA Installation
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
});

// Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then(reg => console.log('Service Worker registered'))
            .catch(err => console.log('Service Worker registration failed'));
    });
}
