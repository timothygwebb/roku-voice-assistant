// Function to request microphone access
async function requestMicrophoneAccess() {
    try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log("Microphone access granted");
        alert("Microphone access granted. You can now use the microphone.");
        // Use the stream for audio processing
    } catch (err) {
        console.error("Microphone access denied", err);
        alert("Microphone access is required. Please allow it in your browser settings.");
    }
}

// Call this function when the user interacts with the app
document.getElementById("request-mic-access").addEventListener("click", () => {
    requestMicrophoneAccess();
});