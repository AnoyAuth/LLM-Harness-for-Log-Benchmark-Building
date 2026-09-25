import json


def validate_json(text: str) -> str:
    """校验 JSON 是否合法。返回原文本或错误信息（含行列号）。"""
    if not isinstance(text, str):
        return "Error: input is not a string"

    stripped = text.strip()
    if not stripped:
        return "Error: empty input"

    try:
        json.loads(stripped)
        return stripped
    except json.JSONDecodeError as e:
        return f"Error: invalid JSON at line {e.lineno}, column {e.colno} — {e.msg}"
