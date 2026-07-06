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
    }

    // Get CSRF token from cookie
    function getCookie(name) {
        let cookieValue = null;

        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");

            for (let cookie of cookies) {
                cookie = cookie.trim();

                if (cookie.startsWith(name + "=")) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }

        return cookieValue;
    }

    async function sendMessage() {

        const text = input.value.trim();

        if (!text) return;

        appendMessage(text, "user");
        input.value = "";

        appendMessage("Thinking...", "bot");

        const placeholder = chat.querySelector(".msg.bot:last-child");

        try {

            const response = await fetch("/ai-assistant/api/", {

                method: "POST",

                credentials: "same-origin",

                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken")
                },

                body: JSON.stringify({
                    message: text
                })

            });

            let data = {};

            try {
                data = await response.json();
            } catch (e) {
                throw new Error("Server returned invalid JSON.");
            }

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }

            placeholder.innerText = data.answer || "No response.";

            try {
                window.parent.postMessage({
                    type: "ai-response",
                    unread: true
                }, "*");
            } catch (e) {}

        }
        catch (err) {

            console.error("AI Assistant Error:", err);

            placeholder.innerText =
                "❌ " + (err.message || "Request failed");

        }

    }

    if (send) {
        send.addEventListener("click", sendMessage);
    }

    if (input) {
        input.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                sendMessage();
            }
        });
    }

});