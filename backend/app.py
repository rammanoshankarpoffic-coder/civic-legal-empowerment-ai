"""
Nyaya Sathi — AI for Civic and Legal Empowerment
Flask backend entry point.

Run with:  python backend/app.py
"""

import os
import sys

# Allow running this file directly (python backend/app.py) as well as via
# `python -m backend.app` by ensuring the project root is on sys.path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, request, jsonify
from flask_cors import CORS

from backend.agents import rti_agent, rights_navigator_agent, eligibility_agent, form_filler_agent
from backend.utils.llm_client import get_mode
from backend.utils.language_utils import normalize_language_code

app = Flask(__name__)
CORS(app)

# --------------------------------------------------------------------------
# Orchestrator: routes free-text chat messages to the right specialist agent
# --------------------------------------------------------------------------

_INTENT_KEYWORDS = {
    "rti": [
        "rti", "right to information", "public information officer",
        "why hasn't", "why has my", "why is my", "ask why",
        "passport", "ration card", "pension", "land record",
        "pending", "stuck", "delayed", "delay", "status of my", "application status",
    ],
    "rights": ["landlord", "deposit", "refund", "defective", "employer", "wages", "fired", "tenant", "consumer", "workplace"],
    "eligibility": ["eligible", "eligibility", "qualify", "scheme", "scholarship", "pm-kisan", "pmay", "ayushman"],
    "form": ["fill", "form", "application form", "apply for"],
}


def classify_intent(message: str) -> str:
    text = message.lower()
    scores = {intent: sum(1 for kw in kws if kw in text) for intent, kws in _INTENT_KEYWORDS.items()}
    best_intent = max(scores, key=scores.get)
    return best_intent if scores[best_intent] > 0 else "unknown"


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "mode": get_mode()})


@app.route("/api/chat", methods=["POST"])
def chat():
    body = request.get_json(force=True) or {}
    message = body.get("message", "").strip()
    session_id = body.get("session_id", "default")
    language = normalize_language_code(body.get("language", "en"))

    if not message:
        return jsonify({"error": "message is required"}), 400

    intent = classify_intent(message)

    if intent == "rti":
        result = rti_agent.draft_rti(issue=message, language=language)
    elif intent == "rights":
        result = rights_navigator_agent.navigate_rights(description=message, language=language)
    elif intent == "eligibility":
        # naive scheme extraction for the demo; a real system would use NER
        result = eligibility_agent.check_eligibility(scheme=message, profile={}, language=language)
    elif intent == "form":
        result = form_filler_agent.start_or_continue(
            session_id=session_id, form_type="rti_application", language=language
        )
    else:
        result = {
            "agent": "orchestrator",
            "clarifying_question": (
                "I can help with: (1) drafting an RTI application, (2) explaining "
                "your rights in a tenant/consumer/workplace dispute, (3) checking "
                "eligibility for a government scheme, or (4) filling out a form. "
                "Which of these best matches what you need?"
            ),
        }

    result["detected_intent"] = intent
    return jsonify(result)


@app.route("/api/rti", methods=["POST"])
def rti_endpoint():
    body = request.get_json(force=True) or {}
    result = rti_agent.draft_rti(
        issue=body.get("issue", ""),
        state=body.get("state", "your state"),
        language=normalize_language_code(body.get("language", "en")),
    )
    return jsonify(result)


@app.route("/api/rights", methods=["POST"])
def rights_endpoint():
    body = request.get_json(force=True) or {}
    result = rights_navigator_agent.navigate_rights(
        description=body.get("description", ""),
        dispute_type=body.get("dispute_type"),
        language=normalize_language_code(body.get("language", "en")),
    )
    return jsonify(result)


@app.route("/api/eligibility", methods=["POST"])
def eligibility_endpoint():
    body = request.get_json(force=True) or {}
    result = eligibility_agent.check_eligibility(
        scheme=body.get("scheme", ""),
        profile=body.get("profile", {}),
        language=normalize_language_code(body.get("language", "en")),
    )
    return jsonify(result)


@app.route("/api/form-filler", methods=["POST"])
def form_filler_endpoint():
    body = request.get_json(force=True) or {}
    result = form_filler_agent.start_or_continue(
        session_id=body.get("session_id", "default"),
        form_type=body.get("form_type", "rti_application"),
        answer=body.get("answer"),
        language=normalize_language_code(body.get("language", "en")),
    )
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
