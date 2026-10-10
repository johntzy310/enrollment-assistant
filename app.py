import os
import json
import joblib
from flask import Flask, request, jsonify, render_template_string
from google import genai

app = Flask(__name__)

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

model = joblib.load("model.pkl") if os.path.exists("model.pkl") else None
faqs = []
if os.path.exists("faq.json"):
    with open("faq.json", "r") as f:
        faqs = json.load(f)

stats = {
    "total_queries": 0,
    "thumbs_up": 0,
    "thumbs_down": 0,
    "categories": {}
}

STOP_WORDS = {"the", "ang", "a", "an", "and", "or", "in", "on", "at", "to", "for", "is", "it", "ng", "sa", "mga", "na", "ay"}

def get_top_3_faqs(user_msg, faq_list):
    q_words = set(user_msg.lower().split()) - STOP_WORDS
    scored = []
    for faq in faq_list:
        text = f"{faq.get('question', '')} {faq.get('answer', '')}".lower()
        f_words = set(text.split()) - STOP_WORDS
        overlap = len(q_words.intersection(f_words))
        scored.append((overlap, faq))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:3]]

@app.route("/")
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bayanihan College Helpdesk</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; max-width: 375px; margin: 20px auto; padding: 15px; background: #f9f9f9; }
            h2 { font-size: 1.2rem; text-align: center; color: #333; }
            #chatbox { border: 1px solid #ccc; height: 350px; overflow-y: scroll; padding: 10px; margin-bottom: 10px; border-radius: 8px; background: #fff; display: flex; flex-direction: column; }
            .user { text-align: right; color: #fff; background: #007bff; padding: 8px 12px; border-radius: 12px; margin: 6px 0; max-width: 80%; align-self: flex-end; }
            .bot { text-align: left; color: #333; background: #e9ecef; padding: 8px 12px; border-radius: 12px; margin: 6px 0; max-width: 80%; align-self: flex-start; }
            .loading { font-style: italic; color: #666; display: none; margin-bottom: 10px; }
            .feedback { font-size: 11px; margin-top: 5px; }
            .controls { display: flex; gap: 5px; }
            input[type="text"] { flex: 1; padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
            button { padding: 8px 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .admin-link { display: block; text-align: center; margin-top: 15px; font-size: 12px; color: #666; text-decoration: none; }
        </style>
    </head>
    <body>
        <h2>Bayanihan Helpdesk</h2>
        <div id="chatbox"></div>
        <div id="loading" class="loading">Assistant is typing...</div>
        <div class="controls">
            <input type="text" id="userInput" placeholder="Ask an enrollment question..." onkeypress="if(event.key==='Enter') sendMessage()">
            <button onclick="sendMessage()">Send</button>
        </div>
        <a class="admin-link" href="/admin" target="_blank">View Admin Stats</a>

        <script>
            async function sendMessage() {
                const input = document.getElementById("userInput");
                const chatbox = document.getElementById("chatbox");
                const loading = document.getElementById("loading");
                const text = input.value.trim();
                if (!text) return;

                chatbox.innerHTML += `<div class="user">${text}</div>`;
                input.value = "";
                chatbox.scrollTop = chatbox.scrollHeight;
                loading.style.display = "block";

                try {
                    const response = await fetch("/api/chat", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ message: text })
                    });
                    const data = await response.json();
                    loading.style.display = "none";

                    if (!response.ok) {
                        chatbox.innerHTML += `<div class="bot" style="color:red;">Error: ${data.error}</div>`;
                        return;
                    }

                    let sources = data.faq_ids && data.faq_ids.length > 0 ? `<br><small style="color:#6c757d;">FAQ IDs: ${data.faq_ids.join(", ")} | Category: ${data.category}</small>` : "";
                    let feedbackBtns = `
                        <div class="feedback">
                            Helpful? <button onclick="sendFeedback(1, this)">👍</button> <button onclick="sendFeedback(-1, this)">👎</button>
                        </div>`;

                    chatbox.innerHTML += `<div class="bot">${data.answer}${sources}${feedbackBtns}</div>`;
                } catch (err) {
                    loading.style.display = "none";
                    chatbox.innerHTML += `<div class="bot" style="color:red;">Connection error.</div>`;
                }
                chatbox.scrollTop = chatbox.scrollHeight;
            }

            async function sendFeedback(value, btnElement) {
                await fetch("/api/feedback", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ feedback: value })
                });
                btnElement.parentElement.innerHTML = "<em>Thank you for your feedback!</em>";
            }
        </script>
    </body>
    </html>
    ''')

@app.route("/api/chat", methods=["POST"])
def chat():
    global stats
    data = request.json or {}
    user_msg = data.get("message", "").strip()

    if not user_msg or len(user_msg) > 500:
        return jsonify({"error": "Message must be between 1 and 500 characters."}), 400

    stats["total_queries"] += 1

    predicted_cat = "general"
    if model:
        try:
            predicted_cat = model.predict([user_msg])[0]
        except Exception:
            pass
    
    stats["categories"][predicted_cat] = stats["categories"].get(predicted_cat, 0) + 1

    top_faqs = get_top_3_faqs(user_msg, faqs)
    faq_ids = [f.get("id") for f in top_faqs]
    context_str = "\n".join([f"ID: {f.get('id')} | Category: {f.get('category')} | Q: {f.get('question')} | A: {f.get('answer')}" for f in top_faqs])

    if client:
        try:
            prompt = f"""You are the official enrollment helpdesk assistant for Bayanihan College.
Answer the user's question using ONLY the provided FAQ context below.
Match the language the user wrote in (English, Filipino, or Taglish).
If the context does not contain the answer, state clearly that you do not know based on official records.

FAQ Context:
{context_str}

User Question: {user_msg}"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            answer = response.text
        except Exception as e:
            answer = f"Error generating response from Gemini API: {str(e)}"
    else:
        answer = "Gemini API Key is not configured."

    return jsonify({
        "answer": answer,
        "faq_ids": faq_ids,
        "category": predicted_cat
    })

@app.route("/api/feedback", methods=["POST"])
def feedback():
    global stats
    data = request.json or {}
    val = data.get("feedback")
    if val == 1:
        stats["thumbs_up"] += 1
    elif val == -1:
        stats["thumbs_down"] += 1
    return jsonify({"status": "success"})

@app.route("/api/stats", methods=["GET"])
def get_stats():
    total_ratings = stats["thumbs_up"] + stats["thumbs_down"]
    pct_up = (stats["thumbs_up"] / total_ratings * 100) if total_ratings > 0 else 0
    return jsonify({
        "total_queries": stats["total_queries"],
        "categories": stats["categories"],
        "thumbs_up": stats["thumbs_up"],
        "thumbs_down": stats["thumbs_down"],
        "thumbs_up_percentage": round(pct_up, 2)
    })

@app.route("/admin")
def admin():
    total_ratings = stats["thumbs_up"] + stats["thumbs_down"]
    pct_up = (stats["thumbs_up"] / total_ratings * 100) if total_ratings > 0 else 0
    cat_items = "".join([f"<li><b>{cat}</b>: {count} queries</li>" for cat, count in stats["categories"].items()])
    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head><title>Admin Dashboard</title></head>
    <body style="font-family: Arial; padding: 20px; max-width: 500px; margin: auto;">
        <h2>Bayanihan Helpdesk Admin Dashboard</h2>
        <hr>
        <p><b>Total Queries:</b> {stats['total_queries']}</p>
        <p><b>Thumbs Up Rating:</b> {pct_up:.1f}% ({stats['thumbs_up']} 👍 / {stats['thumbs_down']} 👎)</p>
        <h3>Queries by Category:</h3>
        <ul>{cat_items if cat_items else "<li>No queries logged yet.</li>"}</ul>
        <br>
        <a href="/">← Back to Chat</a>
    </body>
    </html>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
