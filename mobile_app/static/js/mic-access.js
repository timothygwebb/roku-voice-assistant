async function requestMicrophoneAccess() {
    try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log("Microphone access granted");
        showStatus("Microphone enabled");
    } catch (err) {
        console.error("Microphone access denied", err);
        showStatus("Microphone access denied", true);
    }
}

document.getElementById("request-mic-access")
    .addEventListener("click", requestMicrophoneAccess);
