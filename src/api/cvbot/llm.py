from typing import Any

# Swap provider or model here and nowhere else.
MODEL = "@cf/mistralai/mistral-small-3.1-24b-instruct"
MAX_TOKENS = 400


def _extract_text(result: Any) -> str:
    """Workers AI chat models answer either {"response": ...} or OpenAI-style {"choices": [...]}."""
    if isinstance(result, dict):
        if isinstance(result.get("response"), str):
            return result["response"]
        choices = result.get("choices") or []
        if choices:
            return choices[0].get("message", {}).get("content") or ""
    return ""


async def ask_llm(env: Any, system: str, question: str) -> str:
    """Send the system prompt and the question to the model and return the answer text."""
    from js import Object  # only importable inside the Workers (Pyodide) runtime
    from pyodide.ffi import to_js

    payload = to_js(
        {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
            "max_tokens": MAX_TOKENS,
        },
        dict_converter=Object.fromEntries,
    )
    result = await env.AI.run(MODEL, payload)
    if hasattr(result, "to_py"):
        result = result.to_py()
    return _extract_text(result).strip()
