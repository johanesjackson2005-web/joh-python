document.addEventListener('DOMContentLoaded', function () {

    const chat = document.getElementById('chat');
    const input = document.getElementById('message');
    const send = document.getElementById('send');

    function appendMessage(text, cls) {
        const div = document.createElement('div');
        div.className = 'msg ' + cls;
        div.innerText = text;
        chat.appendChild(div);
        chat.scrollTop = chat.scrollHeight;
        return div; // 🔥 important (we use it later)
    }
    const messageBox = document.getElementById("message");


if(messageBox){

    messageBox.addEventListener("input", function(){

        this.style.height = "auto";

        this.style.height =
        Math.min(this.scrollHeight,150) + "px";

    });


    messageBox.addEventListener("keydown", function(e){

        // Enter = new line
        // Ctrl + Enter = send

        if(e.key === "Enter" && e.ctrlKey){

            e.preventDefault();

            document.getElementById("send").click();

        }

    });

}

    // CSRF helper
    function getCookie(name) {
        let cookieValue = null;

        if (document.cookie) {
            const cookies = document.cookie.split(';');

            for (let cookie of cookies) {
                cookie = cookie.trim();

                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    async function sendMessage() {

        const text = input.value.trim();
        if (!text) return;

        // show user message
        appendMessage(text, "user");
        input.value = "";

        // show loading message
        const placeholder = appendMessage("Thinking...", "bot");

        try {

            const response = await fetch("/ai-assistant/api/", {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: JSON.stringify({ message: text })
            });

            let data;

            try {
                data = await response.json();
            } catch {
                throw new Error("Server did not return valid JSON");
            }

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }

            // replace loading message
            placeholder.innerText = data.answer || "No response";

            // 🔊 OPTIONAL: voice AI (uncomment if needed)
            // speak(data.answer);

            // notify parent iframe
            window.parent.postMessage({
                type: "ai-response",
                unread: true
            }, "*");

        } catch (err) {

            console.error("AI Error:", err);

            placeholder.innerText = "❌ " + err.message;

        }
    }

    // click send
    if (send) {
        send.addEventListener("click", sendMessage);
    }

    // enter key
    if (input) {
        input.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // 🔊 TEXT TO SPEECH (VOICE AI)
    function speak(text) {
        if (!text) return;

        const msg = new SpeechSynthesisUtterance(text);
        msg.lang = "sw-TZ"; // unaweza badilisha "sw-TZ"
        msg.rate = 1;

        window.speechSynthesis.speak(msg);
    }
const voiceBtn = document.getElementById("voice");
const message = document.getElementById("message");


const SpeechRecognition =
window.SpeechRecognition ||
window.webkitSpeechRecognition;


if(SpeechRecognition){

const recognition = new SpeechRecognition();


recognition.lang = "sw-TZ";

recognition.continuous = false;

recognition.interimResults = false;


if(voiceBtn && SpeechRecognition){

const recognition = new SpeechRecognition();

recognition.lang = "sw-TZ";
recognition.continuous = false;
recognition.interimResults = false;


voiceBtn.onclick = function(){

    recognition.start();

};


recognition.onresult = function(event){

    const text =
    event.results[0][0].transcript;


    message.value = text;

    message.dispatchEvent(
        new Event("input")
    );

};


recognition.onerror=function(e){

console.log("Voice error:",e.error);

};

}
};




});