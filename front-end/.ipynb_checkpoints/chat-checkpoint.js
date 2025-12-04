const config = {
    region: "us-east-1",
    userPoolId: "us-east-1_222mvHFqQ",
    userPoolClientId: "3a6uhb892lnilc37vblunhnokl",
    wsUrl: "wss://rt0tfsc8b0.execute-api.us-east-1.amazonaws.com/prod"
};

const token = localStorage.getItem("idToken");
if (!token) {
    window.location.href = "index.html";
}

let ws = new WebSocket(`${config.wsUrl}?token=${token}`);

ws.onopen = () => appendMessage("Connected to chat server.\n");
ws.onclose = () => appendMessage("Disconnected.\n");
ws.onerror = e => appendMessage("WebSocket error.\n");

ws.onmessage = event => {
    appendMessage(event.data);
};

function appendMessage(msg) {
    const box = document.getElementById("messages");
    box.value += msg + "\n";
    box.scrollTop = box.scrollHeight;
}

function sendMessage() {
    const input = document.getElementById("input");
    const text = input.value.trim();
    if (!text) return;

    if (text.startsWith("/join")) {
        const room = text.split(" ")[1];
        ws.send(JSON.stringify({
            action: "$joinroom",
            room: room
        }));
    }
    else {
        ws.send(JSON.stringify({
            action: "$sendmessage",
            message: text
        }));
    }

    input.value = "";
}

const inputBox = document.getElementById("input");

inputBox.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
});

