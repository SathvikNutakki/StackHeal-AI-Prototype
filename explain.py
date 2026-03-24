"""
explain.py — Agent 6
Converts technical errors into human-friendly explanations (simple + detailed).
"""

from groq import Groq
import json
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are an Explanation Agent.

Your ONLY job:
- Convert technical errors into human-friendly explanations

You must return TWO formats:
1. Simple (for beginners)
2. Detailed (for developers)

STRICT RULES:
- Output MUST be valid JSON
- NO markdown
- NO extra text
- Simple = very short, easy to understand (1 line)
- Detailed = clear technical explanation (2-3 lines max)

Output format:
{
  "simple": "Beginner-friendly explanation",
  "detailed": "Technical explanation"
}
"""


def generate_explanation(input_text: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            temperature=0.3,
            max_tokens=250,
            top_p=1,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Explain the following error/code:\n\n{input_text}"},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content.strip()
        parsed = _safe_parse(content)
        return _normalize(parsed)
    except Exception as e:
        return {"simple": "Unable to explain error", "detailed": f"AgentError: {str(e)}"}


def _safe_parse(content: str) -> dict:
    try:
        return json.loads(content)
    except Exception:
        try:
            start, end = content.find("{"), content.rfind("}") + 1
            return json.loads(content[start:end])
        except Exception:
            return {"simple": content, "detailed": content}


def _normalize(result: dict) -> dict:
    return {
        "simple": result.get("simple", "No simple explanation available"),
        "detailed": result.get("detailed", "No detailed explanation available"),
    }


# Chain-ready wrapper
def run_explanation_agent(input_text: str) -> dict:
    return generate_explanation(input_text)


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        "TypeError: cannot read property 'map' of undefined",
        "ModuleNotFoundError: No module named 'pandas'",
    ]
    for t in tests:
        print(f"\nINPUT : {t}")
        print(f"OUTPUT: {run_explanation_agent(t)}")
