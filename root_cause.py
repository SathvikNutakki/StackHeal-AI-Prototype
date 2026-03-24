"""
root_cause.py — Agent 4
Explains WHY the error occurs in one concise line.
"""

from groq import Groq
import json
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are a Root Cause Analysis Agent.

Your ONLY job:
- Explain WHY the error occurs

STRICT RULES:
- Output MUST be valid JSON
- NO markdown
- NO extra explanation
- Keep response SHORT and precise (1 line preferred)

Output format:
{
  "root_cause": "Concise reason why error happens"
}

Examples:
- "Object is null before method call"
- "Variable used before initialization"
- "Incorrect data type passed to function"
- "Missing dependency causes module load failure"
"""


def analyze_root_cause(input_text: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            temperature=0,
            max_tokens=100,
            top_p=1,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze the following error/code and find root cause:\n\n{input_text}"},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content.strip()
        parsed = _safe_parse(content)
        return _normalize(parsed)
    except Exception as e:
        return {"root_cause": f"AgentError: {str(e)}"}


def _safe_parse(content: str) -> dict:
    try:
        return json.loads(content)
    except Exception:
        try:
            start, end = content.find("{"), content.rfind("}") + 1
            return json.loads(content[start:end])
        except Exception:
            return {"root_cause": content}


def _normalize(result: dict) -> dict:
    return {"root_cause": result.get("root_cause", "Unable to determine root cause")}


# Chain-ready wrapper
def run_root_cause_agent(input_text: str) -> dict:
    return analyze_root_cause(input_text)


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        "TypeError: cannot read property 'map' of undefined",
        "NullPointerException at line 42",
        "ModuleNotFoundError: No module named 'pandas'",
    ]
    for t in tests:
        print(f"\nINPUT : {t}")
        print(f"OUTPUT: {run_root_cause_agent(t)}")
