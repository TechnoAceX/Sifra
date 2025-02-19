document.addEventListener("DOMContentLoaded", function () {
    const chatBody = document.getElementById("chat-body");
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const fileInput = document.getElementById("file-input");
    const voiceInputButton = document.getElementById("voice-input");
    let uploadedFileId = "";

    function appendMessage(sender, text, isTyping = false) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender === "bot" ? "bot-message" : "user-message");

        const messageText = document.createElement("div");
        messageText.classList.add("message-text");
        messageText.innerText = isTyping ? "Sifra is thinking...🤔💭" : text;

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

    function sendMessage(message, mode = "text") {
        if (!message) return;

        appendMessage("user", message);
        userInput.value = "";

        const typingIndicator = appendMessage("bot", "", true);

        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message, file_id: uploadedFileId || null, mode: mode }),
        })
        .then(response => response.json())
        .then(data => {
            chatBody.removeChild(typingIndicator);
            appendMessage("bot", data.response || "🤖 I'm here to chat!");
            if (mode === "audio") {
                speak(data.response);
            }
        })
        .catch(error => {
            console.error("Chat error:", error);
            chatBody.removeChild(typingIndicator);
            appendMessage("bot", "⚠️ Oops! Something went wrong.");
        });
    }

    chatForm.addEventListener("submit", function (event) {
        event.preventDefault();
        sendMessage(userInput.value.trim(), "text");
    });

    userInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage(userInput.value.trim(), "text");
        }
    });

    fileInput.addEventListener("change", function () {
        const file = fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        appendMessage("user", `📂 Uploading file: ${file.name}`);
        const typingIndicator = appendMessage("bot", "", true);

        fetch("/upload", {
            method: "POST",
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            chatBody.removeChild(typingIndicator);
            if (data.file_id) {
                uploadedFileId = data.file_id;
                appendMessage("bot", "✅ File uploaded successfully! Now you can ask questions about it.");
            } else {
                appendMessage("bot", "⚠️ Failed to upload the file.");
            }
        })
        .catch(error => {
            console.error("File upload error:", error);
            chatBody.removeChild(typingIndicator);
            appendMessage("bot", "⚠️ Oops! File upload failed.");
        });
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
        sendMessage(userMessage, "audio");
    };

    recognition.onerror = function (event) {
        console.error("Speech recognition error:", event.error);
        appendMessage("bot", "⚠️ I couldn't hear you clearly. Try again!");
    };

    function speak(text) {
        if (!text) return;
        const cleanedText = text.replace(/[\p{Emoji_Presentation}\p{Extended_Pictographic}]/gu, "");
        const speech = new SpeechSynthesisUtterance(cleanedText);
        const availableVoices = speechSynthesis.getVoices();

        let selectedVoice = availableVoices.find(voice => voice.name.includes("Google US English Female")) ||
                            availableVoices.find(voice => voice.name.includes("Microsoft Zira")) ||
                            availableVoices.find(voice => voice.name.includes("Samantha")) ||
                            availableVoices.find(voice => voice.lang.startsWith("en-US") && voice.gender === "female") ||
                            availableVoices[0];

        if (selectedVoice) {
            speech.voice = selectedVoice;
        }

        speech.pitch = 1.8;  // Higher pitch for extra cuteness
        speech.rate = 1.1;   // Balanced speed for excitement
        speech.volume = 1.0;

        speechSynthesis.speak(speech);
    }

    speechSynthesis.onvoiceschanged = () => {
        speak("Hiii! I'm Sifra! How can I help you today? 💖");
    };
});