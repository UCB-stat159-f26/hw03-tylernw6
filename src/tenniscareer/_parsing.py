"""Read career match arrays without executing downloaded JavaScript."""

import json
import re


def _parse_career_js(javascript: str) -> list[list]:
    """Extract nonempty match rows, preserving raw fields for cleaning."""
    if not isinstance(javascript, str):
        raise TypeError("Career JavaScript must be text.")
    assignment = re.search(r"\bvar\s+morematchmx\s*=\s*", javascript)
    if assignment is None:
        raise ValueError("Career JavaScript is missing the morematchmx array.")
    rows = _decode_match_array(javascript[assignment.end():])
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
