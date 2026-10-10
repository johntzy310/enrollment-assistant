import os
import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Safe Gemini Client Initialization
client = None
try:
    from google import genai
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        client = genai.Client(api_key=api_key)
except Exception as e:
    print(f"GenAI init warning: {e}")

# Load FAQ data safely
faqs = []
try:
    if os.path.exists("faq.json"):
        with open("faq.json", "r", encoding="utf-8") as f:
            faqs = json.load(f)
except Exception as e:
    print(f"FAQ load warning: {e}")

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
    try:
        data = request.get_json() or {}
        query = data.get("message", "").strip()
        if not query:
            return jsonify({"response": "Please enter a valid question."}), 400

        stats["total_queries"] += 1

        # Simple FAQ matching
        context_list = []
        matched_ids = []
        category = "general"
        
        for faq in faqs:
            q_text = faq.get("question", "").lower()
            if any(word in query.lower() for word in q_text.split()):
                context_list.append(f"Q: {faq.get('question')}\nA: {faq.get('answer')}")
                matched_ids.append(faq.get("id"))
                category = faq.get("category", "enrollment")

        context_str = "\n\n".join(context_list) if context_list else "Standard college enrollment helpdesk."

        prompt = f"""You are the Bayanihan College Enrollment Helpdesk Assistant. Answer concisely.
Context:
{context_str}

User Question: {query}"""

        answer = "Hello! Welcome to the Bayanihan Enrollment Helpdesk. How can I help you enroll today?"
        if client:
            try:
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt,
                )
                if response and hasattr(response, 'text'):
                    answer = response.text
            except Exception as api_err:
                answer = f"Gemini API Response: {str(api_err)}"

        log_entry = {"query": query, "response": answer, "rating": None}
        stats["logs"].append(log_entry)

        return jsonify({
            "response": answer,
            "faq_ids": matched_ids if matched_ids else [1, 2, 3],
            "category": category
        })
    except Exception as e:
        return jsonify({"response": f"Server Error: {str(e)}"}), 500

@app.route("/feedback", methods=["POST"])
def feedback():
    try:
        data = request.get_json() or {}
        if data.get("helpful"):
            stats["helpful_yes"] += 1
        else:
            stats["helpful_no"] += 1
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
