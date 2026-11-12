"""Convert raw match fields into plotting data without network access."""

from datetime import datetime
import math
import re

import pandas as pd

from ._parsing import _validate_match_rows

_MATCH_FIELDS = {
    0: "match_date", 1: "tournament", 2: "surface", 4: "result",
    9: "score", 11: "opponent", 16: "_opponent_age_value",
}


def _clean_career_rows(rows: list[list], player_name: str,
                       player_birth_date: str) -> pd.DataFrame:
    """Return played matches with ages in years and player metadata."""
    frame = _match_table(rows)
    frame = _remove_walkovers(frame)
    frame = _add_ages(frame, player_birth_date)
    frame.attrs.update(player_name=player_name, player_birth_date=player_birth_date)
    return frame.drop(columns="_opponent_age_value").reset_index(drop=True)


def _match_table(rows: list[list]) -> pd.DataFrame:
    """Select shared fields without assuming a fixed raw row length."""
    _validate_match_rows(rows)
    frame = pd.DataFrame(rows)[list(_MATCH_FIELDS)].rename(columns=_MATCH_FIELDS)
    if not frame["result"].isin(["W", "L"]).all():
        raise ValueError("Match results must be W or L.")
    frame["match_date"] = pd.to_datetime([
        _parse_date(value, "%Y%m%d", "Match date") for value in frame["match_date"]
    ])
    return frame


def _remove_walkovers(frame: pd.DataFrame) -> pd.DataFrame:
    """Exclude unplayed walkovers; keep retirements and other played matches."""
    walkovers = frame["score"].astype("string").str.contains(
        r"\bW\s*/\s*O\b|\bwalkover\b", case=False, regex=True, na=False)
    return frame.loc[~walkovers].copy()


def _add_ages(frame: pd.DataFrame, player_birth_date: str) -> pd.DataFrame:
    """Use elapsed days / 365.25 for dates and preserve supplied decimal ages."""
    birth = _parse_date(player_birth_date, "%Y-%m-%d", "Player birth date")
    frame["player_age"] = ((frame["match_date"] - birth).dt.days / 365.25).map(
        lambda age: _validate_age(age, "Player"))
    frame["opponent_age"] = [
        _opponent_age(value, date) for value, date in
        zip(frame["_opponent_age_value"], frame["match_date"])]
    frame["age_difference"] = frame["player_age"] - frame["opponent_age"]
    return frame


def _parse_date(value: str, date_format: str, label: str) -> datetime:
    """Reject invalid dates instead of silently coercing them."""
    pattern = r"\d{8}" if date_format == "%Y%m%d" else r"\d{4}-\d{2}-\d{2}"
    try:
        if not isinstance(value, str) or not re.fullmatch(pattern, value):
            raise ValueError("Unexpected date format")
        return datetime.strptime(value, date_format)
    except ValueError as error:
        raise ValueError(f"{label} is invalid: {value!r}.") from error


def _opponent_age(value: str, match_date: pd.Timestamp) -> float:
    """Handle opponent birth dates, decimal ages, and missing values."""
    if pd.isna(value) or value == "":
        return math.nan
    if isinstance(value, str) and re.fullmatch(r"\d{8}", value):
        birth = _parse_date(value, "%Y%m%d", "Opponent birth date")
        return _validate_age((match_date - birth).days / 365.25, "Opponent")
    return _numeric_age(value)


def _numeric_age(value: str) -> float:
    """Convert an opponent's supplied age with a useful error on bad input."""
    try:
        age = float(value)
    except (ValueError, TypeError) as error:
        raise ValueError(f"Opponent age is invalid: {value!r}.") from error
    return _validate_age(age, "Opponent")


def _validate_age(age: float, label: str) -> float:
    """Reject nonfinite ages and dates inconsistent with a human career."""
    if not math.isfinite(age) or not 0 <= age <= 100:
        raise ValueError(f"{label} age must be between 0 and 100 years.")
    return age
