"""Read career match arrays without executing downloaded JavaScript."""

import json
import re


def _parse_career_js(javascript: str) -> list[list]:
    """Extract nonempty match rows, preserving raw fields for cleaning."""
    return _parse_match_array(javascript, "morematchmx")


def _array_content(javascript: str, variable: str) -> str:
    """Locate a named array assignment without executing JavaScript."""
    if not isinstance(javascript, str):
        raise TypeError("Career JavaScript must be text.")
    assignment = re.search(rf"\bvar\s+{re.escape(variable)}\s*=\s*", javascript)
    if assignment is None:
        raise ValueError(f"Career JavaScript is missing the {variable} array.")
    return javascript[assignment.end():]


def _parse_match_array(javascript: str, variable: str,
                       allow_empty: bool = False) -> list[list]:
    """Read current or archived matches, allowing an empty recent array."""
    rows = _decode_match_array(_array_content(javascript, variable))
    if rows != [] or not allow_empty:
        _validate_match_rows(rows)
    return rows


def _decode_match_array(content: str) -> list:
    """Decode only the assigned JSON value, allowing later JS statements."""
    try:
        rows, _ = json.JSONDecoder().raw_decode(content.lstrip())
    except json.JSONDecodeError as error:
        raise ValueError("Career match array contains malformed JSON.") from error
    return rows


def _validate_match_rows(rows: list) -> None:
    """Require enough fields to read dates, results, opponents, and ages."""
    if not isinstance(rows, list) or not rows:
        raise ValueError("Career match array must be a nonempty list of rows.")
    if any(not isinstance(row, list) or len(row) < 17 for row in rows):
        raise ValueError("Each career match row must contain at least 17 fields.")
