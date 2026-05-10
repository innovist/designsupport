"""
Flexible JSON parsing utilities for AI-generated responses.

Handles: markdown code blocks, trailing commas, truncated arrays,
and responses that mix prose with a JSON structure.
"""

from __future__ import annotations

import json
import re


def parse_json_object(raw: str) -> dict:
    """
    Parse AI response into a single dict.
    Strategies: code-block strip → direct parse → regex extraction.
    Raises ValueError if no dict can be extracted.
    """
    text = _strip_code_block(raw)
    text = _remove_trailing_commas(text)

    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
        if isinstance(result, list) and result and isinstance(result[0], dict):
            return result[0]
    except json.JSONDecodeError:
        pass

    # Find outermost {...}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        fragment = _remove_trailing_commas(match.group())
        try:
            result = json.loads(fragment)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Cannot parse JSON object from response ({len(raw)} chars)")


def parse_json_array(raw: str, required_key: str | None = None) -> list[dict]:
    """
    Parse AI response into a list of dicts.
    Strategies: code-block strip → direct parse → regex array →
                individual-object extraction (handles truncated arrays).
    Raises ValueError if no objects can be extracted.
    """
    text = _strip_code_block(raw)
    text = _remove_trailing_commas(text)

    # Strategy 1: direct parse
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return _filter_dicts(result, required_key)
        if isinstance(result, dict):
            return _filter_dicts([result], required_key)
    except json.JSONDecodeError:
        pass

    # Strategy 2: find outermost [...] array
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        fragment = _remove_trailing_commas(match.group())
        try:
            result = json.loads(fragment)
            if isinstance(result, list):
                return _filter_dicts(result, required_key)
        except json.JSONDecodeError:
            pass

    # Strategy 3: extract individual complete {...} objects
    # Handles truncated arrays where the closing ] is missing
    objects = _extract_objects(text, required_key)
    if objects:
        return objects

    raise ValueError(f"No parseable JSON objects found in response ({len(raw)} chars)")


def _strip_code_block(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]  # drop ```json or ```
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]  # drop closing ```
        text = "\n".join(lines).strip()
    return text


def _remove_trailing_commas(text: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", text)


def _filter_dicts(items: list, required_key: str | None) -> list[dict]:
    if required_key:
        return [i for i in items if isinstance(i, dict) and i.get(required_key)]
    return [i for i in items if isinstance(i, dict)]


def _extract_objects(text: str, required_key: str | None) -> list[dict]:
    objects: list[dict] = []
    depth = 0
    start: int | None = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                fragment = _remove_trailing_commas(text[start : i + 1])
                try:
                    obj = json.loads(fragment)
                    if isinstance(obj, dict):
                        if not required_key or obj.get(required_key):
                            objects.append(obj)
                except json.JSONDecodeError:
                    pass
                start = None
    return objects
