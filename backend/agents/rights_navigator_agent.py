"""
Rights Navigator Agent — explains, in simple terms, what a person can do
about a specific tenant, consumer, or workplace dispute.
"""

import json
import os

from backend.utils.llm_client import ask_claude
from backend.utils.language_utils import simplify_instruction

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "rights_faq.json")
with open(_DATA_PATH, "r", encoding="utf-8") as f:
    _RIGHTS_FAQ = json.load(f)

_TYPE_KEYWORDS = {
    "tenant": ["landlord", "rent", "deposit", "tenant", "eviction"],
    "consumer": ["refund", "defective", "warranty", "seller", "product", "service provider"],
    "workplace": ["employer", "salary", "wages", "termination", "fired", "workplace", "hr"],
}


def _detect_dispute_type(description: str) -> str:
    text = description.lower()
    for dispute_type, keywords in _TYPE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return dispute_type
    return "default"


def navigate_rights(description: str, dispute_type: str = None, language: str = "en") -> dict:
    resolved_type = dispute_type if dispute_type in _RIGHTS_FAQ else _detect_dispute_type(description)
    faq_entry = _RIGHTS_FAQ.get(resolved_type, _RIGHTS_FAQ["default"])

    system_prompt = (
        "You are a Rights Navigator helping Indian citizens understand civic and "
        "legal disputes (tenant, consumer, workplace). Ground your explanation "
        "strictly in the context provided below. If the context is the 'default' "
        "fallback (no specific legal basis available), clearly say this is general "
        "guidance and recommend contacting a legal aid clinic. "
        f"{simplify_instruction(language)}\n\n"
        f"CONTEXT (grounded knowledge base):\n{json.dumps(faq_entry, indent=2)}"
    )

    user_prompt = (
        f"Dispute description: {description}\n\n"
        "Explain in plain language what this person's rights are and what they "
        "can concretely do next, step by step."
    )

    explanation_text = ask_claude(system_prompt, user_prompt)

    return {
        "agent": "rights_navigator",
        "dispute_type": resolved_type,
        "explanation": explanation_text,
        "legal_basis": faq_entry["legal_basis"],
        "next_steps": faq_entry["next_steps"],
        "escalation_path": faq_entry["escalation_path"],
        "confidence": "grounded" if resolved_type != "default" else "best-effort",
    }
