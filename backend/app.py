import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)

SYSTEM_PROMPT = """You are NetSage AI, a Cisco-style network troubleshooting assistant.
Analyze the user's symptom and show-command output. Return ONLY valid JSON with:
root_cause, confidence, osi_layer, evidence, next_command, fix_steps.
Do not claim certainty when evidence is missing. A human must review every diagnosis."""

@app.get("/")
def home():
    return send_from_directory("../frontend", "index.html")

@app.post("/api/diagnose")
def diagnose():
    data = request.get_json(force=True)
    symptom = data.get("symptom", "").strip()
    show_output = data.get("show_output", "").strip()

    if not symptom:
        return jsonify({"error": "Please enter a network symptom."}), 400

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        return jsonify({
            "demo": True,
            "root_cause": "Possible gateway, routing, VLAN, or ACL configuration issue",
            "confidence": "Low",
            "osi_layer": "Layer 3/4",
            "evidence": "No AI API key is configured. This is a demo diagnosis.",
            "next_command": "show ip route; show access-lists; show interfaces trunk",
            "fix_steps": [
                "Check the default gateway.",
                "Check VLAN and trunk configuration.",
                "Check routing table.",
                "Check ACL rules.",
                "Have a human reviewer approve the final fix."
            ]
        })

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        prompt = f"Network symptom:\n{symptom}\n\nShow-command output:\n{show_output}"
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        result = json.loads(response.choices[0].message.content)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"AI request failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
