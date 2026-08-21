"""
Conversational Form-Filler — interviews the user turn by turn and
auto-populates an official form template.

Sessions are kept in-memory for the hackathon demo (swap for Redis/DB in
production).
"""

from backend.utils.llm_client import ask_claude
from backend.utils.language_utils import simplify_instruction

# Simple ordered question sets per form type. Each entry: (field_key, question)
_FORM_TEMPLATES = {
    "rti_application": [
        ("state", "Which state are you filing this RTI in?"),
        ("department", "What is the name of the department you want to ask?"),
        ("issue", "In one or two sentences, what do you want to know or resolve?"),
        ("applicant_name", "What is your full name (as it should appear on the application)?"),
        ("applicant_address", "What is your postal address for the response?"),
    ],
    "consumer_complaint": [
        ("product_service", "What product or service is this complaint about?"),
        ("seller_name", "What is the name of the seller/service provider?"),
        ("issue", "Briefly describe what went wrong."),
        ("desired_outcome", "What outcome are you looking for — refund, replacement, repair, or compensation?"),
        ("applicant_name", "What is your full name?"),
        ("applicant_contact", "What is your phone number or email for follow-up?"),
    ],
}

# In-memory session store: {session_id: {"form_type": ..., "answers": {...}, "step": int}}
_SESSIONS = {}


def start_or_continue(session_id: str, form_type: str, answer: str = None, language: str = "en") -> dict:
    if form_type not in _FORM_TEMPLATES:
        return {"error": f"Unknown form_type. Available: {list(_FORM_TEMPLATES.keys())}"}

    questions = _FORM_TEMPLATES[form_type]

    session = _SESSIONS.setdefault(
        session_id, {"form_type": form_type, "answers": {}, "step": 0}
    )

    # Record the answer to the previous question, if any
    if answer is not None and session["step"] > 0:
        prev_key = questions[session["step"] - 1][0]
        session["answers"][prev_key] = answer

    if session["step"] >= len(questions):
        # Already complete — regenerate rendered doc idempotently
        return _finalize(session, language)

    next_key, next_question = questions[session["step"]]
    session["step"] += 1

    complete = session["step"] >= len(questions)

    if complete:
        result = _finalize(session, language)
        result["next_question"] = None
        return result

    return {
        "next_question": next_question,
        "form_state": dict(session["answers"]),
        "complete": False,
    }


def _finalize(session: dict, language: str) -> dict:
    system_prompt = (
        "You are a Conversational Form-Filler. Take the collected answers and "
        "render them as a clean, properly formatted official document ready for "
        "the citizen to review and submit. Do not add information not provided "
        f"by the user. {simplify_instruction(language)}"
    )
    user_prompt = (
        f"Form type: {session['form_type']}\n"
        f"Collected answers: {session['answers']}\n\n"
        "Render the final document."
    )
    rendered = ask_claude(system_prompt, user_prompt)

    return {
        "form_state": dict(session["answers"]),
        "rendered_document": rendered,
        "complete": True,
    }


def reset_session(session_id: str) -> None:
    _SESSIONS.pop(session_id, None)
