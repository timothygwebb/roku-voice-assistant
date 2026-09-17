// Function to request microphone access
async function requestMicrophoneAccess() {
    try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log("Microphone access granted");
        // Use the stream for audio processing
    } catch (err) {
        console.error("Microphone access denied", err);
        alert("Microphone access is required to use this feature.");
    }
}

showStatus("Please enable microphone access in browser settings.");
