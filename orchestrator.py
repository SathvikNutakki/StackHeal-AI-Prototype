"""
orchestrator.py
Runs all 7 agents in sequence and merges their outputs into one result dict.
"""

from error_detection import run_error_agent
from error_line import run_line_agent
from error_classify import run_classification_agent
from root_cause import run_root_cause_agent
from fix import run_fix_agent
from explain import run_explanation_agent
from confident import run_confidence_agent


def run_stackheal_pipeline(input_text: str) -> dict:
    """
    Runs the full 7-agent StackHeal pipeline.
    Returns a single merged dict ready for the FastAPI response model.
    """
    result: dict = {}

    # Agent 1 — Detect error type + message
    result.update(run_error_agent(input_text))

    # Agent 2 — Find failing line + snippet
    result.update(run_line_agent(input_text))

    # Agent 3 — Classify error + severity + language
    # NOTE: Agent 3 also returns "type" — we keep Agent 1's type value
    #       so we only pull severity and language from classification.
    classification = run_classification_agent(input_text)
    result["severity"] = classification.get("severity", "Medium")
    result["language"] = classification.get("language", "Unknown")
    # Only override type if Agent 1 returned a generic/unknown value
    if result.get("type") in ("UnknownError", "AgentError", "NoError", ""):
        result["type"] = classification.get("type", result.get("type", "Unknown Error"))

    # Agent 4 — Root cause
    result.update(run_root_cause_agent(input_text))

    # Agent 5 — Fix suggestion
    result.update(run_fix_agent(input_text))

    # Agent 6 — Explanation (simple + detailed)
    result.update(run_explanation_agent(input_text))

    # Agent 7 — Confidence score (uses full result so far)
    result["confidence"] = run_confidence_agent(result)

    return result


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json

    test_input = """
    const user = getUser();
    console.log(user.name);
    const data = user.profile.age;
    TypeError: Cannot read property 'profile' of undefined at line 22
    """

    output = run_stackheal_pipeline(test_input)
    print("\n── STACKHEAL PIPELINE OUTPUT ──\n")
    print(json.dumps(output, indent=2))
