import os, json, re, joblib
from flask import Flask, request, jsonify, render_template_string
from google import genai

app = Flask(__name__)

# Load KB and ML Model
with open('faq.json', 'r') as f:
    faq_data = json.load(f)

model = joblib.load('model.pkl')
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# In-memory statistics store
stats_logs = [] # list of {"category": str, "rating": bool}

STOPWORDS = {"the", "ang", "a", "an", "is", "are", "in", "at", "to", "sa", "na", "ng", "of", "and", "or", "what", "how", "kailan", "ano", "paano"}

def get_top_3_faqs(user_query):
    words = set(re.findall(r'\w+', user_query.lower())) - STOPWORDS
    scored_faqs = []
    for item in faq_data:
        faq_words = set(re.findall(r'\w+', (item['question'] + " " + item['answer']).lower())) - STOPWORDS
        overlap = len(words.intersection(faq_words))
        scored_faqs.append((overlap, item))
    scored_faqs.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored_faqs[:3]]

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    msg = data.get('message', '').strip()

    # 1. Validation
    if not msg or len(msg) > 500:
        return jsonify({"error": "Message must be between 1 and 500 characters."}), 400

    # ML Classification
    predicted_category = str(model.predict([msg])[0])

    # 2. RAG Retrieval
    top_faqs = get_top_3_faqs(msg)
    faq_ids = [item['id'] for item in top_faqs]

    # 3. Prompt Construction & Gemini Call
    prompt = f"""
You are an official enrollment helpdesk assistant for Bayanihan College.
Answer the user question using ONLY the FAQ context provided below.
Respond in the same language as the user (English, Filipino, or Taglish).
If the answer cannot be answered strictly from the context, state clearly that you do not know or do not have that information.

Context FAQs:
{json.dumps(top_faqs)}

User Question: {msg}
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        answer = response.text
    except Exception as e:
        answer = "Sorry, I am currently experiencing connection issues. Please try again later."

    return jsonify({
        "answer": answer,
        "faq_ids": faq_ids,
        "category": predicted_category
    })

@app.route('/api/rating', methods=['POST'])
def rating():
    data = request.get_json() or {}
    stats_logs.append({
        "category": data.get("category", "unknown"),
        "rating": bool(data.get("thumbs_up"))
    })
    return jsonify({"status": "ok"})

@app.route('/api/stats', methods=['GET'])
def stats():
    total = len(stats_logs)
    category_counts = {}
    thumbs_up_count = sum(1 for log in stats_logs if log['rating'])

    for log in stats_logs:
        cat = log['category']
        category_counts[cat] = category_counts.get(cat, 0) + 1

    satisfaction = (thumbs_up_count / total * 100) if total > 0 else 0
    return jsonify({
        "total_queries": total,
        "category_counts": category_counts,
        "satisfaction_percentage": round(satisfaction, 2)
    })

# Front-End UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; max-width: 375px; margin: 0 auto; padding: 10px; background: #f4f4f9; }
        .chat-box { height: 400px; border: 1px solid #ccc; overflow-y: scroll; padding: 10px; background: #fff; border-radius: 8px; }
        .msg { margin: 8px 0; padding: 8px 12px; border-radius: 12px; max-width: 80%; font-size: 14px; }
        .user { background: #007bff; color: white; margin-left: auto; text-align: right; }
        .bot { background: #e9ecef; color: black; margin-right: auto; }
        .meta { font-size: 10px; color: #666; margin-top: 4px; }
        .input-area { display: flex; margin-top: 10px; }
        input { flex: 1; padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
        button { padding: 8px 12px; background: #28a745; color: white; border: none; border-radius: 4px; margin-left: 5px; }
        .loading { display: none; font-size: 12px; color: #888; margin: 5px 0; }
    </style>
</head>
<body>
    <h3>Bayanihan Helpdesk</h3>
    <div class="chat-box" id="chat"></div>
    <div class="loading" id="loading">Assistant is typing...</div>
    <div class="input-area">
        <input type="text" id="msg" placeholder="Ask about enrollment...">
        <button onclick="send()">Send</button>
    </div>

    <script>
    async function send() {
        const input = document.getElementById('msg');
        const chat = document.getElementById('chat');
        const loading = document.getElementById('loading');
        const text = input.value.trim();
        if (!text) return;

        chat.innerHTML += `<div class="msg user">${text}</div>`;
        input.value = '';
        loading.style.display = 'block';

        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: text})
        });
        const data = await res.json();
        loading.style.display = 'none';

        if (res.ok) {
            const botMsgId = 'msg-' + Date.now();
            chat.innerHTML += `
                <div class="msg bot" id="${botMsgId}">
                    ${data.answer}
                    <div class="meta">Sources: FAQ IDs ${JSON.stringify(data.faq_ids)} | Cat: ${data.category}</div>
                    <button onclick="rate('${data.category}', true)">👍</button>
                    <button onclick="rate('${data.category}', false)">👎</button>
                </div>`;
        } else {
            chat.innerHTML += `<div class="msg bot">Error: ${data.error}</div>`;
        }
        chat.scrollTop = chat.scrollHeight;
    }

    async function rate(cat, thumbsUp) {
        await fetch('/api/rating', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({category: cat, thumbs_up: thumbsUp})
        });
        alert('Feedback submitted!');
    }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/admin')
def admin():
    return """
    <html><body>
    <h2>Admin Dashboard</h2>
    <div id="stats">Loading stats...</div>
    <script>
        fetch('/api/stats').then(r=>r.json()).then(d=>{
            document.getElementById('stats').innerHTML = `
                <p><b>Total Queries:</b> ${d.total_queries}</p>
                <p><b>Satisfaction:</b> ${d.satisfaction_percentage}%</p>
                <pre><b>Categories:</b>\n${JSON.stringify(d.category_counts, null, 2)}</pre>
            `;
        });
    </script>
    </body></html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)