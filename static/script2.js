document.addEventListener("DOMContentLoaded", function () {
    const chatBody = document.getElementById("chat-body");
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const fileInput = document.getElementById("file-input");
    const voiceInputButton = document.getElementById("voice-input");
    let uploadedFileId = "";
    let lastInputType = "text";

    function appendMessage(sender, text, isTyping = false) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender === "bot" ? "bot-message" : "user-message");

        const messageText = document.createElement("div");
        messageText.classList.add("message-text");
        messageText.innerText = isTyping ? "Sifra is thinking... 🤔💭" : text;

        if (sender === "bot") {
            const botAvatar = document.createElement("div");
            botAvatar.classList.add("bot-avatar");
            botAvatar.textContent = "👩‍⚕️";
            messageDiv.appendChild(botAvatar);
        }

        messageDiv.appendChild(messageText);
        chatBody.appendChild(messageDiv);
        chatBody.scrollTo({ top: chatBody.scrollHeight, behavior: "smooth" });

        return messageDiv;
    }

    fileInput.addEventListener("change", function () {
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            const allowedTypes = ["application/pdf", "text/plain"];

            if (!allowedTypes.includes(file.type) || file.size > 20 * 1024 * 1024) {
                appendMessage("bot", "⚠️ Invalid file type or file too large. Please upload a valid document.");
                return;
            }

            const formData = new FormData();
            formData.append("file", file);
            appendMessage("bot", "📤 Uploading file...");

            fetch("/upload", {
                method: "POST",
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                if (data.file_id) {
                    uploadedFileId = data.file_id;
                    appendMessage("bot", "✅ File uploaded successfully! Now, ask me anything about your health report. 💪😊");
                } else {
                    appendMessage("bot", "⚠️ File upload failed. Please try again.");
                }
            })
            .catch(error => {
                console.error("Upload error:", error);
                appendMessage("bot", "🚨 Error uploading file. Check your internet connection.");
            });
        }
    });

    function sendMessage() {
        const message = userInput.value.trim();
        if (message === "") return;

        appendMessage("user", message);
        userInput.value = "";

        const typingIndicator = appendMessage("bot", "", true);

        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message, file_id: uploadedFileId || null }),
        })
        .then(response => response.json())
        .then(data => {
            chatBody.removeChild(typingIndicator);
            appendMessage("bot", data.response || "🤖 I'm here to chat!");
            if (lastInputType === "voice") speak(data.response);
        })
        .catch(error => {
            console.error("Chat error:", error);
            chatBody.removeChild(typingIndicator);
            appendMessage("bot", "⚠️ Oops! Something went wrong.");
        });
    }

    chatForm.addEventListener("submit", function (event) {
        event.preventDefault();
        lastInputType = "text";
        sendMessage();
    });

    userInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            lastInputType = "text";
            sendMessage();
        }
    });

    document.getElementById("logout-btn").addEventListener("click", function () {
        window.location.href = "/logout";
    });

    fetch('/get_quote')
        .then(response => response.json())
        .then(data => {
            document.getElementById("sifra-quote").textContent = data.quote;
        })
        .catch(error => console.error("Error fetching quote:", error));

    fetch('/get_greeting')
        .then(response => response.json())
        .then(data => {
            appendMessage("bot", data.greeting);
        })
        .catch(error => console.error("Error fetching greeting:", error));

    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    voiceInputButton.addEventListener("click", function () {
        recognition.start();
    });

    recognition.onresult = function (event) {
        const userMessage = event.results[0][0].transcript;
        lastInputType = "voice";
        userInput.value = userMessage;
        sendMessage();
    };

    recognition.onerror = function (event) {
        console.error("Speech recognition error:", event.error);
        appendMessage("bot", "⚠️ I couldn't hear you clearly. Try again!");
    };

    function speak(text) {
        if (!text) return;
        const speech = new SpeechSynthesisUtterance(text);
        speech.pitch = 1.8;
        speech.rate = 1.1;
        speech.volume = 1.0;
        speechSynthesis.speak(speech);
    }
});
