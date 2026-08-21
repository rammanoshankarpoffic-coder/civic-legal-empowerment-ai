"""
RTI Drafting Agent — converts a plain-language question into a properly
formatted RTI application addressed to the correct department.
"""

import json
import os

from backend.utils.llm_client import ask_claude
from backend.utils.language_utils import simplify_instruction

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "rti_departments.json")
with open(_DATA_PATH, "r", encoding="utf-8") as f:
    _DEPARTMENTS = json.load(f)

_TOPIC_KEYWORDS = {
    "passport": ["passport"],
    "ration_card": ["ration card", "ration"],
    "pension": ["pension"],
    "land_records": ["land record", "land title", "property record"],
    "municipal_services": ["water supply", "sanitation", "municipal", "property tax"],
}


def _detect_topic(issue: str) -> str:
    issue_lower = issue.lower()
    for topic, keywords in _TOPIC_KEYWORDS.items():
        if any(kw in issue_lower for kw in keywords):
            return topic
    return "default"


def draft_rti(issue: str, state: str = "your state", language: str = "en") -> dict:
    topic = _detect_topic(issue)
    dept_info = _DEPARTMENTS.get(topic, _DEPARTMENTS["default"])

    system_prompt = (
        "You are an RTI Drafting Agent for Indian citizens. You draft RTI "
        "applications strictly following the format required under the RTI Act "
        "2005. Only use the department and fee details provided in the context "
        "below — do not invent department names, addresses, or fee amounts. "
        f"{simplify_instruction(language)}\n\n"
        f"CONTEXT (grounded knowledge base):\n{json.dumps(dept_info, indent=2)}"
    )

    user_prompt = (
        f"Citizen's issue: {issue}\n"
        f"State: {state}\n\n"
        "Write a complete, properly formatted RTI application: addressee line "
        "(Public Information Officer), subject line, application body with "
        "specific numbered questions, and a closing fee note."
    )

    draft_text = ask_claude(system_prompt, user_prompt)

    return {
        "agent": "rti",
        "department": dept_info["department"],
        "pio_contact": dept_info["pio_role"],
        "application_text": draft_text,
        "fee_note": dept_info["fee"],
        "citations": [dept_info["act_section"]],
        "confidence": "grounded" if topic != "default" else "best-effort",
    }
