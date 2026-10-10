import os
import json
import joblib
from flask import Flask, request, jsonify, render_template_string
from google import genai

app = Flask(__name__)

# Initialize Gemini Client
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# Load ML model and FAQs
model = joblib.load("model.pkl") if os.path.exists("model.pkl") else None
faqs = []
if os.path.exists("faq.json"):
    with open("faq.json", "r") as f:
        faqs = json.load(f)

# Analytics tracking
stats = {"total_queries": 0, "thumbs_up": 0, "thumbs_down": 0}

@app.route("/")
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enrollment Helpdesk Assistant</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; }
            #chatbox { border: 1px solid #ccc; height: 300px; overflow-y: scroll; padding: 10px; margin-bottom: 10px; border-radius: 5px; }
            .user { text-align: right; color: #0056b3; margin: 8px 0; }
            .bot { text-align: left; color: #28a745; margin: 8px 0; }
            .feedback { font-size: 12px; margin-top: 5px; }
            button { cursor: pointer; }
        </style>
    </head>
    <body>
        <h2>Enrollment Helpdesk Assistant</h2>
        <div id="chatbox"></div>
        <input type="text" id="userInput" style="width: 75%; padding: 8px;" placeholder="Ask an enrollment question...">
        <button onclick="sendMessage()" style="padding: 8px 15px;">Send</button>

        <script>
            async function sendMessage() {
                const input = document.getElementById("userInput");
                const chatbox = document.getElementById("chatbox");
                const text = input.value.trim();
                if (!text) return;

                chatbox.innerHTML += `<div class="user"><b>You:</b> ${text}</div>`;
                input.value = "";
                chatbox.scrollTop = chatbox.scrollHeight;

                try {
                    const response = await fetch("/api/chat", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ message: text })
                    });
                    const data = await response.json();

                    let sources = data.faq_ids && data.faq_ids.length > 0 ? `<br><small style="color:#6c757d;">Sources: ${data.faq_ids.join(", ")}</small>` : "";
                    let feedbackBtns = `
                        <div class="feedback">
                            Was this helpful? 
                            <button onclick="sendFeedback(1)">👍</button>
                            <button onclick="sendFeedback(-1)">👎</button>
                        </div>`;

                    chatbox.innerHTML += `<div class="bot"><b>Assistant:</b> ${data.answer}${sources}${feedbackBtns}</div>`;
                } catch (err) {
                    chatbox.innerHTML += `<div class="bot" style="color:red;"><b>Assistant:</b> Connection error. Please try again.</div>`;
                }
                chatbox.scrollTop = chatbox.scrollHeight;
            }

            async function sendFeedback(value) {
                await fetch("/api/feedback", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ feedback: value })
                });
                alert("Thank you for your feedback!");
            }
        </script>
    </body>
    </html>
    ''')

@app.route("/api/chat", methods=["POST"])
def chat():
    global stats
    stats["total_queries"] += 1
    data = request.json or {}
    user_msg = data.get("message", "")

    # Machine Learning Intent Prediction
    predicted_cat = "general"
    if model:
        try:
            predicted_cat = model.predict([user_msg])[0]
        except Exception:
            pass

    # Context Retrieval from FAQs
    context_items = [f"{item.get('question','')}: {item.get('answer','')}" for item in faqs]
    faq_ids = [item.get("id","") for item in faqs]
    context_str = "\n".join(context_items)

    # Gemini API Generation
    if client:
        try:
            prompt = f"Context:\n{context_str}\n\nUser Question: {user_msg}\nProvide a helpful answer based on the context above."
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            answer = response.text
        except Exception as e:
            answer = f"Error connecting to Gemini API: {str(e)}"
    else:
        answer = "Gemini API Key is not configured."

    return jsonify({
        "answer