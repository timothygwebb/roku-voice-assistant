// Configuration
const API_BASE_URL = window.location.origin;
let rokuIpAddress = localStorage.getItem('rokuIpAddress') || '';

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadConfig();
    updateVoiceButtonState();
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
    return SpeechRecognition !== undefined;
}

function updateVoiceButtonState() {
    const voiceBtn = document.getElementById('voice-btn');
    const voiceSection = document.querySelector('.voice-section');
    
    if (!checkBrowserSupport()) {
        voiceBtn.disabled = true;
        voiceBtn.style.opacity = '0.5';
        voiceBtn.style.cursor = 'not-allowed';
        
        const supportText = document.createElement('p');
        supportText.className = 'support-text';
        supportText.textContent = 'Voice recognition not available. Please use a browser that supports Web Speech API (Chrome, Edge, or Safari on iOS 14.5+).';
        supportText.style.color = '#ff6b6b';
        supportText.style.fontSize = '0.9em';
        supportText.style.marginTop = '10px';
        
        // Remove existing support text if any
        const existing = voiceSection.querySelector('.support-text');
        if (existing) existing.remove();
        voiceSection.appendChild(supportText);
    }
}

function startVoiceRecognition() {
    if (!rokuIpAddress) {
        showStatus('Please configure your Roku IP address first', 'error');
        return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        showStatus('Voice recognition not supported on this device. Please use Chrome, Edge, or update Safari.', 'error');
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
        voiceResult.textContent = 'Listening...';
        
        recognition.start();
        
        // Add timeout for speech recognition (30 seconds)
        const timeout = setTimeout(() => {
            recognition.stop();
        }, 30000);
        
        recognition.onresult = function(event) {
            clearTimeout(timeout);
            const transcript = event.results[0][0].transcript;
            voiceResult.textContent = `You said: "${transcript}"`;
            processVoiceCommand(transcript);
        };
        
        recognition.onerror = function(event) {
            clearTimeout(timeout);
            let errorText = 'Error occurred in recognition';
            
            // Provide more specific error messages
            if (event.error === 'no-speech') {
                errorText = 'No speech detected. Please try again.';
            } else if (event.error === 'network') {
                errorText = 'Network error. Check your connection.';
            } else if (event.error === 'not-allowed') {
                errorText = 'Microphone permission denied. Check settings.';
            }
            
            voiceResult.textContent = errorText;
            showStatus(errorText, 'error');
            voiceBtn.classList.remove('listening');
        };
        
        recognition.onend = function() {
            voiceBtn.classList.remove('listening');
        };
    } catch (error) {
        console.error('Speech Recognition Error:', error);
        showStatus('Failed to initialize voice recognition: ' + error.message, 'error');
    }
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
