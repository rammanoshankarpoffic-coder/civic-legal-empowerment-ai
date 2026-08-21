"""
Small helpers for plain-language output and (future) multi-language support.
"""

SUPPORTED_LANGUAGES = ["en", "hi", "kn", "ta", "mr", "bn"]


def simplify_instruction(language: str = "en") -> str:
    """
    Returns a system-prompt fragment instructing the model to keep language
    simple and, where relevant, respond in the requested language.
    """
    base = (
        "Use short sentences and everyday words. Avoid legal jargon unless you "
        "immediately explain it in plain language. Assume the reader may have "
        "limited familiarity with government processes."
    )
    if language != "en" and language in SUPPORTED_LANGUAGES:
        base += f" Respond in the '{language}' language."
    return base


def normalize_language_code(code: str) -> str:
    code = (code or "en").lower().strip()
    return code if code in SUPPORTED_LANGUAGES else "en"
