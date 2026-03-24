"""
error_detection.py — Agent 1
Detects whether an error exists and extracts its type + message.
"""

from groq import Groq
import json
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are a strict Error Detection Agent.

Your ONLY job:
1. Detect if an error exists in the input
2. Identify the error type (e.g., TypeError, SyntaxError, NullPointerException, etc.)
3. Extract the exact error message

STRICT RULES:
- Output MUST be valid JSON
- NO markdown
- NO explanation
- NO extra text
- ONLY one JSON object

Output format:
{
  "type": "ErrorType",
  "message": "Exact error message"
}

If no error is found:
{
  "type": "NoError",
  "message": "No error detected"
}
"""


def detect_error(input_text: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            temperature=0,
            max_tokens=200,
            top_p=1,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze the following input and detect error:\n\n{input_text}"},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content.strip()
        parsed = _safe_parse(content)
        return parsed
    except Exception as e:
        return {"type": "AgentError", "message": str(e)}


def _safe_parse(content: str) -> dict:
    try:
        return json.loads(content)
    except Exception:
        try:
            start, end = content.find("{"), content.rfind("}") + 1
            return json.loads(content[start:end])
        except Exception:
            return {"type": "ParsingError", "message": content}


# Chain-ready wrapper
def run_error_agent(input_text: str) -> dict:
    result = detect_error(input_text)
    return {
        "type": result.get("type", "UnknownError"),
        "message": result.get("message", ""),
    }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        "TypeError: cannot read property 'map' of undefined",
        "NullPointerException at line 42",
        "SyntaxError: invalid syntax",
        "Everything executed successfully",
    ]
    for t in tests:
        print(f"\nINPUT : {t}")
        print(f"OUTPUT: {run_error_agent(t)}")
