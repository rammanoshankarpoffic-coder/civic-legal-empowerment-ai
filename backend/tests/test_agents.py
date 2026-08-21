"""
Basic unit tests — run with: pytest backend/tests/
These run entirely in mock mode (no ANTHROPIC_API_KEY needed).
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.agents import rti_agent, rights_navigator_agent, eligibility_agent, form_filler_agent
from backend.app import classify_intent


def test_classify_intent_rti():
    assert classify_intent("How do I file an RTI about my pending passport?") == "rti"


def test_classify_intent_rights():
    assert classify_intent("My landlord won't return my security deposit") == "rights"


def test_classify_intent_eligibility():
    assert classify_intent("Am I eligible for PM-KISAN as a farmer?") == "eligibility"


def test_classify_intent_unknown():
    assert classify_intent("Hello, how are you?") == "unknown"


def test_rti_agent_returns_department():
    result = rti_agent.draft_rti(issue="My passport renewal is delayed", state="Karnataka")
    assert result["department"]
    assert "application_text" in result
    assert result["citations"]


def test_rti_agent_topic_detection():
    result = rti_agent.draft_rti(issue="My ration card is not being issued")
    assert "Food" in result["department"] or "Civil Supplies" in result["department"]


def test_rights_navigator_tenant():
    result = rights_navigator_agent.navigate_rights(
        description="My landlord is not returning my deposit after I moved out"
    )
    assert result["dispute_type"] == "tenant"
    assert result["legal_basis"]


def test_rights_navigator_unknown_falls_back():
    result = rights_navigator_agent.navigate_rights(description="My neighbor's tree fell on my car")
    assert result["dispute_type"] == "default"
    assert result["confidence"] == "best-effort"


def test_eligibility_known_scheme():
    result = eligibility_agent.check_eligibility(
        scheme="PM-KISAN", profile={"occupation": "farmer", "land_acres": 1.5}
    )
    assert result["scheme"]
    assert result["required_documents"]


def test_eligibility_unknown_scheme():
    result = eligibility_agent.check_eligibility(scheme="Some Made Up Scheme", profile={})
    assert result["eligible"] is None
    assert result["confidence"] == "unknown"


def test_form_filler_flow():
    session_id = "test-session-1"
    form_filler_agent.reset_session(session_id)

    r1 = form_filler_agent.start_or_continue(session_id, "rti_application")
    assert r1["complete"] is False
    assert r1["next_question"]

    r2 = form_filler_agent.start_or_continue(session_id, "rti_application", answer="Karnataka")
    assert r2["form_state"]["state"] == "Karnataka"
