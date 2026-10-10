import os
import json
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)

# Initialize Gemini Client
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# Load FAQ data
faqs = []
if os.path.exists("faq.json"):
    with open("faq.json", "r", encoding="utf-8") as f:
        faqs = json.load(f)

# In-memory stats storage
stats = {
    "total_queries": 0,
    "helpful_yes": 0,
    "helpful_no": 0,
    "logs": []
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin")
def admin():
    total = stats["total_queries"]
    yes = stats["helpful_yes"]
    no = stats["helpful_no"]
    ratio = (yes / total * 100) if total > 0 else 0
    return render_template("admin.html", total=total, yes=yes, no=no, ratio=round(ratio, 1), logs=stats["logs"])

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    query = data.get("message", "").strip()
    if not query:
        return jsonify({"response": "Please enter a valid question."}), 400

    stats["total_queries"] += 1

    # Simple FAQ keyword matching
    context_list = []
    matched_ids = []
    category = "general"
    
    for faq in faqs:
        q_text = faq.get("question", "").lower()
        if any(word in query.lower() for word in q_text.split()):
            context_list.append(f"Q: {faq.get('question')}\nA: {faq.get('answer')}")
            matched_ids.append(faq.get("id"))
            category = faq.get("category", "enrollment")

    context_str = "\n\n".join(context_list) if context_list else "No specific FAQ context found."

    prompt = f"""You are the Bayanihan College Enrollment Helpdesk Assistant.
Answer the user query concisely using the provided context below.

Context:
{context_str}

User Question: {query}"""

    try:
        if client:
            response = client.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt,
            )
            answer = response.text
        else:
            answer = "API Key not configured."
    except Exception as e:
        answer = f"Error generating response from Gemini API: {str(e)}"

    log_entry = {"query": query, "response": answer, "rating": None}
    stats["logs"].append(log_entry)

    return jsonify({
        "response": answer,
        "faq_ids": matched_ids if matched_ids else [1, 2, 3],
        "category": category
    })

@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json() or {}
    helpful = data.get("helpful")
    if helpful:
        stats["helpful_yes"] += 1
    else:
        stats["helpful_no"] += 1
    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
