document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ Script loaded successfully!");

    // Helper: Handle form submissions via AJAX
    function handleFormSubmission(formId, url, successMessage, resultId = null) {
        const form = document.getElementById(formId);
        if (!form) return;

        form.addEventListener("submit", function (event) {
            event.preventDefault();
            const formData = new FormData(form);
            fetch(url, {
                method: "POST",
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(successMessage);
                    if (resultId) {
                        document.getElementById(resultId).innerText = successMessage;
                        document.getElementById(resultId).style.display = "block";
                    }
                    form.reset();
                } else {
                    alert("Error: " + data.error);
                }
            })
            .catch(error => console.error("❌ Error:", error));
        });
    }

    // Apply Form Submissions for Different Pages
    handleFormSubmission("analytics-form", "/student-performance", "Analytics report generated!", "report-output");
    handleFormSubmission("announcement-form", "/announcements", "Announcement posted!", "announcement-list");
    handleFormSubmission("grade-form", "/assign-grade", "Grade assigned successfully!", "grade-message");
    handleFormSubmission("attendance-form", "/mark-attendance", "Attendance marked successfully!", "attendance-message");
    handleFormSubmission("notification-form", "/notifications", "Notification sent successfully!", "notification-message");
    handleFormSubmission("plagiarism-form", "/plagiarism-check", "Plagiarism check completed!", "plagiarism-result");
    handleFormSubmission("schedule-form", "/schedule", "Class scheduled successfully!", "schedule-message");
    handleFormSubmission("assignment-form", "/upload-assignment", "Assignment uploaded successfully!", "assignment-message");

    // Handle AI Insights button click
    const aiInsightsBtn = document.getElementById("fetch-ai-insights");
    if (aiInsightsBtn) {
        aiInsightsBtn.addEventListener("click", function () {
            fetch("/ai-insights")
            .then(response => response.json())
            .then(data => {
                document.getElementById("ai-output").innerHTML = `<p>${data.insights}</p>`;
            })
            .catch(error => console.error("❌ Error fetching AI insights:", error));
        });
    }

    // Chatbot functionality
    const chatbox = document.getElementById("chatbox");
    const chatInput = document.getElementById("chatInput");
    const chatBtn = document.getElementById("chatBtn");
    const voiceBtn = document.getElementById("voiceBtn");

    if (chatbox && chatInput && chatBtn) {
        function appendMessage(sender, message) {
            chatbox.innerHTML += `<p><strong>${sender}:</strong> ${message}</p>`;
            chatbox.scrollTop = chatbox.scrollHeight;
        }

        chatBtn.addEventListener("click", function () {
            sendMessage(chatInput.value);
        });

        chatInput.addEventListener("keypress", function (event) {
            if (event.key === "Enter") {
                sendMessage(chatInput.value);
            }
        });

        function sendMessage(message) {
            if (message.trim() === "") return;
            appendMessage("You", message);
            chatInput.value = "";

            fetch("/chatbot-query", {
                method: "POST",
                body: JSON.stringify({ question: message }),
                headers: { "Content-Type": "application/json" },
            })
                .then(response => response.json())
                .then(data => appendMessage("Chatbot", data.response))
                .catch(error => appendMessage("Chatbot", "Error processing request"));
        }

        // Voice recognition setup
        if (voiceBtn && (window.SpeechRecognition || window.webkitSpeechRecognition)) {
            const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = "en-US";
            recognition.interimResults = false;

            voiceBtn.addEventListener("click", function () {
                recognition.start();
            });

            recognition.onresult = function (event) {
                const voiceText = event.results[0][0].transcript;
                chatInput.value = voiceText;
                sendMessage(voiceText);
            };

            recognition.onerror = function (event) {
                appendMessage("Chatbot", "Voice recognition error. Try again.");
            };
        }
    }
    
    // Voice Command Processing (OpenAI Whisper)
    const recordBtn = document.getElementById("recordBtn");
    const output = document.getElementById("output");

    if (recordBtn) {
        recordBtn.addEventListener("click", function () {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    const mediaRecorder = new MediaRecorder(stream);
                    let audioChunks = [];
                    mediaRecorder.ondataavailable = event => {
                        audioChunks.push(event.data);
                    };
                    mediaRecorder.onstop = () => {
                        const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
                        const formData = new FormData();
                        formData.append("audio", audioBlob);
                        fetch("/process-voice", {
                            method: "POST",
                            body: formData
                        })
                        .then(response => response.json())
                        .then(data => {
                            output.innerHTML = `<p>Command: ${data.command}</p>`;
                        })
                        .catch(error => {
                            output.innerHTML = `<p>Error processing voice command.</p>`;
                            console.error("❌ Error:", error);
                        });
                    };
                    mediaRecorder.start();
                    recordBtn.textContent = "🎤 Recording... (Click to Stop)";
                    setTimeout(() => {
                        mediaRecorder.stop();
                        recordBtn.textContent = "🎤 Start Speaking";
                    }, 4000);
                })
                .catch(error => console.error("❌ Error accessing microphone:", error));
        });
    }

    // Virtual Classroom - Google Meet Integration via Voice Command
    const startClassBtn = document.getElementById("startVirtualClassBtn");
    if (startClassBtn && (window.SpeechRecognition || window.webkitSpeechRecognition)) {
        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = "en-US";
        recognition.interimResults = false;

        startClassBtn.addEventListener("click", function () {
            startClassBtn.textContent = "Listening...";
            recognition.start();
        });

        recognition.onresult = function (event) {
            const voiceText = event.results[0][0].transcript.toLowerCase();
            console.log("Voice command recognized:", voiceText);

            if (voiceText.includes("start class") || voiceText.includes("google meet")) {
                window.open("https://meet.google.com/new", "_blank");
            } else if (voiceText.includes("zoom") || voiceText.includes("zoom meeting")) {
                window.open("https://zoom.us/start", "_blank");
            }

            startClassBtn.textContent = "🎙️ Speak Command";
        };

        recognition.onerror = function (event) {
            console.error("Speech recognition error:", event);
            startClassBtn.textContent = "🎙️ Speak Command";
        };
    }

    // Lecture Summarization (Added for lecture_capture.html)
    const summarizeBtn = document.getElementById("summarizeBtn");
    if (summarizeBtn) {
        summarizeBtn.addEventListener("click", function () {
            const transcriptText = document.getElementById("transcript").innerText;
            fetch("/summarize-lecture", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ transcript: transcriptText })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById("summaryOutput").innerHTML = `<p>${data.summary}</p>`;
            })
            .catch(error => console.error("Error summarizing lecture:", error));
        });
    }
});