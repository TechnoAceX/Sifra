document.addEventListener("DOMContentLoaded", function () {
    const chatBody = document.getElementById("chat-body");
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const fileInput = document.getElementById("file-input");
    let uploadedFileId = "";

    function appendMessage(sender, text, isTyping = false) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender === "bot" ? "bot-message" : "user-message");

    const messageText = document.createElement("div");
    messageText.classList.add("message-text");

    // FIX: Use innerText instead of innerHTML to avoid formatting issues
    messageText.innerText = isTyping ? "Sifra is typing... 🤔💭" : text;

    if (sender === "bot") {
        const botAvatar = document.createElement("div");
        botAvatar.classList.add("bot-avatar");
        botAvatar.textContent = "🤖";
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
            appendMessage("bot", data.response || "🤖 I'm here to chat! Feel free to ask me anything.");
        })
        .catch(error => {
            console.error("Chat error:", error);
            chatBody.removeChild(typingIndicator);
            appendMessage("bot", "⚠️ Oops! Something went wrong. Try again.");
        });
    }

    chatForm.addEventListener("submit", function (event) {
        event.preventDefault();
        sendMessage();
    });

    userInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    document.getElementById("logout-btn").addEventListener("click", function () {
        window.location.href = "/logout";
    });
});
