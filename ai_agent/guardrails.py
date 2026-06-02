from __future__ import annotations


UNSAFE_TERMS = {
    "delete all files",
    "steal",
    "password",
    "api key",
    "secret key",
    "private key",
    "malware",
    "phishing",
    "bypass login",
}


def check_prompt_safety(prompt: str) -> dict[str, object]:
    lowered = prompt.lower()
    for term in UNSAFE_TERMS:
        if term in lowered:
            return {
                "blocked": True,
                "reason": f"Prompt contains unsafe request: {term}",
            }
    return {"blocked": False, "reason": "Prompt passed basic safety checks."}
