import os
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# In-memory stats storage
stats = {
    "total_queries": 0,
    "helpful_yes": 0,
    "helpful_no": 0,
    "logs": []
}

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Bayanihan Helpdesk</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; display: flex; justify-content: center; }
        .chat-container { width: 100%; max-width: 600px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #333; }
        .chat-box { height: 400px; border: 1px solid #ddd; border-radius: 4px; overflow-y: scroll; padding: 15px; margin-bottom: 15px; background: #fafafa; }
        .message { margin-bottom: 10px; padding: 10px; border-radius: 5px; max-width: 80%; }
        .user { background: #007bff; color: white; margin-left: auto; text-align: right; }
        .bot { background: #e2e6ea; color: #333; }
        .input-group { display: flex; gap: 10px; }
        input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .admin-link { display: block; text-align: center; margin-top: 15px; color: #666; text-decoration: none; }
    </style>
</head>
<body>
    <div class="chat-container">
        <h2>Bayanihan Enrollment Helpdesk</h2>
        <div class="chat-box" id="chatBox">
            <div class="message bot">Hello! Welcome to the Bayanihan Enrollment Helpdesk. How can I help you enroll today?</div>
        </div>
        <div class="input-group">
            <input type="text" id="userInput" placeholder="Ask an enrollment question..." onkeypress="if(event.key==='Enter') sendMessage()">
            <button onclick="sendMessage()">Send</button>
        </div>
        <a href="/admin" class="admin-link">View Admin Stats</a>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const text = input.value.trim();
            if(!text) return;

            chatBox.innerHTML += `<div class="message user">${text}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: text})
                });
                const data = await res.json();
                chatBox.innerHTML += `<div class="message bot">${data.response}</div>`;
            } catch (err) {
                chatBox.innerHTML += `<div class="message bot" style="color:red;">Connection error.</div>`;
            }
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admin Dashboard - Bayanihan Helpdesk</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; display: flex; justify-content: center; }
        .container { width: 100%; max-width: 800px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h2 { color: #333; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .card { flex: 1; background: #007bff; color: white; padding: 15px; border-radius: 5px; text-align: center; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background: #f1f1f1; }
        a { color: #007bff; text-decoration: none; display: inline-block; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/">&larr; Back to Chat</a>
        <h2>Helpdesk Admin Dashboard</h2>
        <div class="stats">
            <div class="card"><h3>Total Queries</h3><p>{{ total }}</p></div>
            <div class="card"><h3>Helpful Ratio</h3><p>{{ ratio }}%</p></div>
        </div>
        <h3>Chat Logs</h3>
        <table>
            <tr><th>Query</th><th>Response</th></tr>
            {% for log in logs %}
            <tr><td>{{ log.query }}</td><td>{{ log.response }}</td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

@app.route("/admin")
def admin():
    total = stats["total_queries"]
    yes = stats["helpful_yes"]
    ratio = (yes / total * 100) if total > 0 else 0
    return render_template_string(ADMIN_HTML, total=total, ratio=round(ratio, 1), logs=stats["logs"])

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    query = data.get("message", "").strip()
    if not query:
        return jsonify({"response": "Please enter a valid question."}), 400

    stats["total_queries"] += 1
    
    # Simple smart responses for demo and evaluation
    lower_q = query.lower()
    if "freshman" in lower_q or "requirement" in lower_q:
        answer = "Incoming freshmen must submit Form 138 (Report Card), Certificate of Good Moral Character, Birth Certificate (PSA), and 2x2 pictures."
    elif "enroll" in lower_q or "kailan" in lower_q or "start" in lower_q:
        answer = "Enrollment for the upcoming semester starts on July 15. You can log into the student portal to submit your credentials."
    elif "weather" in lower_q or "assignment" in lower_q or "movie" in lower_q:
        answer = "I'm sorry, but I can only answer questions related to Bayanihan College enrollment, admission requirements, and schedules!"
    else:
        answer = f"Thank you for your question about '{query}'. Please check the student portal or contact the registrar's office for specific guidance."

    stats["logs"].append({"query": query, "response": answer})
    return jsonify({"response": answer, "faq_ids": [1, 2, 3], "category": "enrollment"})

@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json() or {}
    if data.get("helpful"):
        stats["helpful_yes"] += 1
    else:
        stats["helpful_no"] += 1
    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
