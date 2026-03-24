"""
fix.py — Agent 5
Suggests a minimal fix and provides the corrected code snippet.
"""

from groq import Groq
import json
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are a Fix Suggestion Agent.

Your ONLY job:
1. Suggest how to fix the error
2. Provide corrected code snippet

STRICT RULES:
- Output MUST be valid JSON
- NO markdown
- NO extra explanation
- Keep description SHORT and actionable
- Code must be clean and minimal

Output format:
{
  "description": "Short fix explanation",
  "correctedCode": "Fixed code snippet"
}

Guidelines:
- Prefer minimal fixes (do not rewrite entire code)
- Preserve original logic
- Add checks, corrections, or missing parts
- Make code language-appropriate
"""


def suggest_fix(input_text: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            temperature=0.2,
            max_tokens=300,
            top_p=1,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze and fix the following code/error:\n\n{input_text}"},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content.strip()
        parsed = _safe_parse(content)
        return _normalize(parsed)
    except Exception as e:
        return {"description": "Agent error occurred", "correctedCode": str(e)}


def _safe_parse(content: str) -> dict:
    try:
        return json.loads(content)
    except Exception:
        try:
            start, end = content.find("{"), content.rfind("}") + 1
            return json.loads(content[start:end])
        except Exception:
            return {"description": "Parsing error", "correctedCode": content}


def _normalize(result: dict) -> dict:
    return {
        "description": result.get("description", "No fix suggested"),
        "correctedCode": result.get("correctedCode", ""),
    }


# Chain-ready wrapper
def run_fix_agent(input_text: str) -> dict:
    return suggest_fix(input_text)


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        "TypeError: cannot read property 'map' of undefined",
        "const user = getUser();\nconsole.log(user.name);\nconst data = user.profile.age;",
    ]
    for t in tests:
        print(f"\nINPUT : {t}")
        print(f"OUTPUT: {run_fix_agent(t)}")
