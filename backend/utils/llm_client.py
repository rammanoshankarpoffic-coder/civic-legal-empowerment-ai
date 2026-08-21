"""
Multi-provider LLM client.

Provider priority (first available wins), so the project keeps working even
after a free trial / paid API key runs out — and so it can honestly support
the hackathon's recommended Google stack:

    1. Anthropic Claude   — if ANTHROPIC_API_KEY is set (paid, best quality)
    2. Google Gemini        — if GEMINI_API_KEY is set (FREE tier — Google AI Studio)
    3. Groq                  — if GROQ_API_KEY is set (FREE tier, cloud, fast Llama models)
    4. Ollama                 — if a local Ollama server is running (FREE, fully offline)
    5. Mock mode              — deterministic templated output (FREE, no network needed)

You can also force a specific provider by setting
LLM_PROVIDER=anthropic|gemini|groq|ollama|mock in your .env file, regardless
of what's detected.

Nothing else in the codebase needs to change when you switch providers — every
agent calls ask_claude()/ask_llm() the same way.
"""

import os
import textwrap

import requests

ANTHROPIC_MODEL = "claude-sonnet-4-6"
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MAX_TOKENS = 1000

_anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
_gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
_groq_key = os.environ.get("GROQ_API_KEY", "").strip()
_forced_provider = os.environ.get("LLM_PROVIDER", "").strip().lower() or None


def _ollama_is_running() -> bool:
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=1)
        return resp.status_code == 200
    except requests.exceptions.RequestException:
        return False


def _detect_provider() -> str:
    if _forced_provider in ("anthropic", "gemini", "groq", "ollama", "mock"):
        return _forced_provider
    if _anthropic_key:
        return "anthropic"
    if _gemini_key:
        return "gemini"
    if _groq_key:
        return "groq"
    if _ollama_is_running():
        return "ollama"
    return "mock"


_PROVIDER = _detect_provider()

_anthropic_client = None
if _PROVIDER == "anthropic":
    try:
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=_anthropic_key)
    except ImportError:
        # anthropic package not installed — gracefully drop to next provider
        _anthropic_client = None
        if _gemini_key:
            _PROVIDER = "gemini"
        elif _groq_key:
            _PROVIDER = "groq"
        elif _ollama_is_running():
            _PROVIDER = "ollama"
        else:
            _PROVIDER = "mock"


def get_mode() -> str:
    """Returns the active provider name — shown on /api/health and in the UI."""
    return _PROVIDER


def _call_anthropic(system_prompt: str, user_prompt: str) -> str:
    response = _anthropic_client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def _call_gemini(system_prompt: str, user_prompt: str) -> str:
    # Google Gemini API — free tier via Google AI Studio, no credit card
    # required. Get a key at https://aistudio.google.com/apikey
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={_gemini_key}"
    )
    resp = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json={
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"maxOutputTokens": MAX_TOKENS},
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    parts = data["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts)


def _call_groq(system_prompt: str, user_prompt: str) -> str:
    # Groq exposes an OpenAI-compatible /chat/completions endpoint — free tier,
    # sign up at https://console.groq.com (no credit card required).
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {_groq_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_MODEL,
            "max_tokens": MAX_TOKENS,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _call_ollama(system_prompt: str, user_prompt: str) -> str:
    # Fully local, fully free. Install: https://ollama.com
    # Then: `ollama pull llama3.1` and `ollama serve` (usually auto-starts).
    resp = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["message"]["content"]


def _mock_response(system_prompt: str, user_prompt: str, note: str = "") -> str:
    header = "[MOCK RESPONSE — no LLM provider configured/reachable]"
    if note:
        header += f" ({note})"
    return textwrap.dedent(f"""
        {header}

        System instructions received:
        {system_prompt[:200]}...

        Based on your request:
        "{user_prompt[:300]}"

        This is a templated placeholder for the demo. Configure one of:
        ANTHROPIC_API_KEY, GEMINI_API_KEY (free), GROQ_API_KEY (free), or a
        running local Ollama server to get real generated text here. See
        README.md → "LLM Provider Options" for step-by-step setup.
    """).strip()


def ask_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Single entry point every agent calls. Routes to whichever provider is
    active; falls back to mock mode automatically on any provider error so
    a flaky/expired key never crashes the demo.
    """
    try:
        if _PROVIDER == "anthropic":
            return _call_anthropic(system_prompt, user_prompt)
        if _PROVIDER == "gemini":
            return _call_gemini(system_prompt, user_prompt)
        if _PROVIDER == "groq":
            return _call_groq(system_prompt, user_prompt)
        if _PROVIDER == "ollama":
            return _call_ollama(system_prompt, user_prompt)
    except Exception as exc:  # noqa: BLE001 - demo-grade graceful fallback
        return _mock_response(system_prompt, user_prompt, note=f"{_PROVIDER} error: {exc}")

    return _mock_response(system_prompt, user_prompt)


# Backwards-compatible alias — agents were originally written against
# ask_claude(); kept so no other file needs to change.
def ask_claude(system_prompt: str, user_prompt: str) -> str:
    return ask_llm(system_prompt, user_prompt)
