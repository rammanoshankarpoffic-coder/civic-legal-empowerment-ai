"""
Scheme Eligibility Reader — reads (locally cached) government scheme rules
and answers eligibility questions in plain language.
"""

import json
import os

from backend.utils.llm_client import ask_claude
from backend.utils.language_utils import simplify_instruction

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "schemes.json")
with open(_DATA_PATH, "r", encoding="utf-8") as f:
    _SCHEMES = json.load(f)


def list_schemes() -> list:
    return list(_SCHEMES.keys())


def _rule_based_check(scheme_key: str, profile: dict) -> tuple:
    """Very simple deterministic pre-check before handing to Claude for the
    natural-language explanation. Returns (eligible_bool_or_none, notes)."""
    scheme = _SCHEMES[scheme_key]
    rules = scheme["eligibility_rules"]
    notes = []

    if "occupation" in rules and profile.get("occupation"):
        if profile["occupation"].lower() not in [o.lower() for o in rules["occupation"]]:
            notes.append(f"Scheme typically targets: {', '.join(rules['occupation'])}")

    if "max_family_income" in rules and profile.get("family_income") is not None:
        if profile["family_income"] > rules["max_family_income"]:
            notes.append(
                f"Family income exceeds the ₹{rules['max_family_income']} threshold"
            )
            return False, notes

    return None, notes  # inconclusive from rules alone -> let Claude reason with context


def check_eligibility(scheme: str, profile: dict, language: str = "en") -> dict:
    scheme_key = scheme.strip().upper().replace(" ", "_")
    if scheme_key not in _SCHEMES:
        # fuzzy fallback: try direct match on full name
        matches = [k for k, v in _SCHEMES.items() if scheme.lower() in v["full_name"].lower()]
        scheme_key = matches[0] if matches else None

    if not scheme_key:
        return {
            "agent": "eligibility",
            "eligible": None,
            "reasoning": (
                "This scheme is not in our current knowledge base. Please check "
                "the National Scholarship Portal / MyScheme.gov.in directly, or "
                "ask about: " + ", ".join(list_schemes())
            ),
            "required_documents": [],
            "apply_link": "https://www.myscheme.gov.in",
            "confidence": "unknown",
        }

    scheme_data = _SCHEMES[scheme_key]
    rule_result, rule_notes = _rule_based_check(scheme_key, profile)

    system_prompt = (
        "You are a Scheme Eligibility Reader for Indian government welfare "
        "schemes. Base your answer strictly on the scheme rules provided in the "
        "context. Be explicit about which criteria the citizen meets and which "
        "are uncertain given the information provided. "
        f"{simplify_instruction(language)}\n\n"
        f"CONTEXT (grounded knowledge base):\n{json.dumps(scheme_data, indent=2)}\n\n"
        f"RULE-BASED PRE-CHECK NOTES: {rule_notes if rule_notes else 'none'}"
    )

    user_prompt = (
        f"Scheme: {scheme_data['full_name']}\n"
        f"Citizen profile: {json.dumps(profile)}\n\n"
        "Explain in plain language whether this person is likely eligible, what "
        "they should double check, and what documents they'll need."
    )

    reasoning_text = ask_claude(system_prompt, user_prompt)

    return {
        "agent": "eligibility",
        "scheme": scheme_data["full_name"],
        "eligible": rule_result,  # True / False / None (needs manual review)
        "reasoning": reasoning_text,
        "required_documents": scheme_data["required_documents"],
        "apply_link": scheme_data["apply_link"],
        "confidence": "grounded",
    }
