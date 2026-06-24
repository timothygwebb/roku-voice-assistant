// Update API_BASE_URL to use https://localhost
const API_BASE_URL = 'https://localhost:8443';

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
