import os
import json
from flask import Flask, render_template, request, jsonify
import joblib
from google import genai

app = Flask(__name__)

# Initialize Gemini Client safely
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Load FAQ data
with open("faq.json", "r", encoding="utf-8") as f:
    faqs = json.load(f)

# Lazy load or safe load model
model = None
vectorizer = None
try:
    model_data = joblib.load("model.pkl")
    if isinstance(model_data, tuple):
        model, vectorizer = model_data
    else:
        model = model_data
except Exception as e:
    print(f"Warning: Could not load model.pkl: {e}")

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
        return jsonify({"response": "Please enter a question."}), 400

    stats["total_queries"] += 1
    
    # Simple keyword/FAQ retrieval or Gemini generation
    prompt = f"You are an enrollment assistant for a college helpdesk. Answer the user query: {query}"
    try:
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=prompt,
        )
        answer = response.text
    except Exception as e:
        answer = f"Error generating response from Gemini API: {str(e)}"

    log_entry = {"query": query, "response": answer, "rating": None}
    stats["logs"].append(log_entry)

    return jsonify({"response": answer, "faq_ids": [1, 2, 3], "category": "enrollment"})

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
