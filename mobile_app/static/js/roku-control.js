function sendCommand(command) {
    fetch('/api/roku', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
    })
    .then(res => res.json())
    .then(data => console.log("Roku response:", data))
    .catch(err => console.error("Error sending command:", err));
}
