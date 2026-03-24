"""
confident.py — Agent 7
Scores the overall confidence of the debugging result (0.0 – 1.0).
"""

from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are a Confidence Scoring Agent.

Your ONLY job:
- Analyze the given debugging result
- Output a confidence score between 0 and 1

STRICT RULES:
- Output MUST be ONLY a number
- NO JSON
- NO explanation
- NO text
- Example: 0.87

Scoring Guidelines:
- 0.9 - 1.0 → Very clear error, precise fix
- 0.7 - 0.89 → Good confidence, minor ambiguity
- 0.5 - 0.69 → Moderate confidence
- 0.3 - 0.49 → Low confidence
- 0.0 - 0.29 → Very uncertain
"""


def get_confidence(input_text: str) -> float:
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            temperature=0,
            max_tokens=10,
            top_p=1,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Evaluate confidence for this debugging result:\n\n{input_text}"},
            ],
        )
        content = response.choices[0].message.content.strip()
        return _normalize_score(content)
    except Exception:
        return 0.5  # neutral fallback


def _normalize_score(content: str) -> float:
    try:
        score = float(content)
        return round(max(0.0, min(1.0, score)), 2)
    except Exception:
        return 0.5


# Chain-ready wrapper — receives the full accumulated pipeline dict
def run_confidence_agent(full_result: dict) -> float:
    return get_confidence(str(full_result))


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample = {
        "type": "Runtime Error",
        "message": "cannot read property 'map' of undefined",
        "line": 22,
        "snippet": "user.profile.age",
        "severity": "High",
        "language": "JavaScript",
        "root_cause": "Object is null before method call",
        "description": "Add null check before accessing property",
        "correctedCode": "if (user && user.profile) { const data = user.profile.age; }",
    }
    print("Confidence Score:", run_confidence_agent(sample))
