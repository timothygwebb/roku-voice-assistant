// Function to request microphone access
async function requestMicrophoneAccess() {
    try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log("Microphone access granted");
        // Use the stream for audio processing
    } catch (err) {
        console.error("Microphone access denied", err);
    }
}

// Call this function when the user interacts with the app
document.getElementById("request-mic-access").addEventListener("click", () => {
    requestMicrophoneAccess();
});});});