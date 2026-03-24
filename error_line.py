"""
error_line.py — Agent 2
Identifies the exact line number and code snippet where the error occurs.
"""

from groq import Groq
import json
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are an Error Line Identification Agent.

Your ONLY job:
1. Identify the exact line number where the error occurs
2. Extract the failing code snippet from that line

STRICT RULES:
- Output MUST be valid JSON
- NO explanations
- NO markdown
- ONLY one JSON object

Output format:
{
  "line": <line_number_integer>,
  "snippet": "exact code causing error"
}

If line cannot be determined:
{
  "line": -1,
  "snippet": "Not found"
}
"""


def identify_error_line(input_text: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            temperature=0,
            max_tokens=200,
            top_p=1,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze the following code/logs and find the exact failing line:\n\n{input_text}"},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content.strip()
        parsed = _safe_parse(content)
        return _normalize(parsed)
    except Exception as e:
        return {"line": -1, "snippet": f"AgentError: {str(e)}"}


def _safe_parse(content: str) -> dict:
    try:
        return json.loads(content)
    except Exception:
        try:
            start, end = content.find("{"), content.rfind("}") + 1
            return json.loads(content[start:end])
        except Exception:
            return {"line": -1, "snippet": content}


def _normalize(result: dict) -> dict:
    return {
        "line": result.get("line", -1),
        "snippet": result.get("snippet", "Not found"),
    }


# Chain-ready wrapper
def run_line_agent(input_text: str) -> dict:
    return identify_error_line(input_text)


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample = """
    20 | const user = getUser();
    21 | console.log(user.name);
    22 | const data = user.profile.age;
    TypeError: Cannot read property 'profile' of undefined at line 22
    """
    print(run_line_agent(sample))
