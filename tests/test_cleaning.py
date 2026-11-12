"""Check age calculations and cleaning entirely from local sample data."""

from copy import deepcopy
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from tenniscareer._cleaning import _clean_career_rows
from tenniscareer._parsing import _parse_career_js

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def female_rows():
    return _parse_career_js((FIXTURES / "FemalePlayerCareer.JS").read_text())


@pytest.fixture
def male_rows():
    return _parse_career_js((FIXTURES / "MalePlayerCareer.JS").read_text())


def test_female_birth_dates_become_ages(female_rows):
    frame = _clean_career_rows(female_rows, "Serena Williams", "1981-09-26")
    match = datetime(1995, 10, 30)
    expected_player = (match - datetime(1981, 9, 26)).days / 365.25
    expected_opponent = (match - datetime(1977, 1, 19)).days / 365.25
    assert frame.loc[0, "player_age"] == pytest.approx(expected_player)
    assert frame.loc[0, "opponent_age"] == pytest.approx(expected_opponent)
    assert frame.loc[0, "age_difference"] == pytest.approx(-1711 / 365.25)
    assert frame["result"].tolist() == ["L", "L", "L"]


def test_male_decimal_ages_are_preserved(male_rows):
    frame = _clean_career_rows(male_rows, "Rafael Nadal", "1986-06-03")
    assert frame["opponent_age"].tolist() == pytest.approx(
        [22.264202601, 24.2902121834, 18.7597535934])
    assert frame["result"].tolist() == ["L", "L", "W"]
    assert (frame["age_difference"] < 0).all()
    assert frame.loc[0, "player_age"] == pytest.approx(5578 / 365.25)


def test_clean_schema_and_metadata(female_rows):
    frame = _clean_career_rows(female_rows, "Serena Williams", "1981-09-26")
    assert frame.columns.tolist() == [
        "match_date", "tournament", "surface", "result", "score", "opponent",
        "player_age", "opponent_age", "age_difference"]
    assert pd.api.types.is_datetime64_any_dtype(frame["match_date"])
    assert frame.loc[0, "opponent"] == "Anne Miller"
    assert frame.attrs == {"player_name": "Serena Williams",
                           "player_birth_date": "1981-09-26"}


def test_raw_rows_are_not_modified(female_rows):
    original = deepcopy(female_rows)
    _clean_career_rows(female_rows, "Serena Williams", "1981-09-26")
    assert female_rows == original


@pytest.mark.parametrize("missing", ["", None])
def test_missing_opponent_age_keeps_match(male_rows, missing):
    male_rows[0][16] = missing
    frame = _clean_career_rows(male_rows, "Rafael Nadal", "1986-06-03")
    assert len(frame) == 3
    assert pd.isna(frame.loc[0, "opponent_age"])
    assert pd.isna(frame.loc[0, "age_difference"])
    assert pd.notna(frame.loc[0, "player_age"])


@pytest.mark.parametrize("score", ["W/O", "w/o", "Walkover", "W / O"])
def test_walkovers_are_excluded_but_retirements_remain(male_rows, score):
    male_rows[0][9] = score
    male_rows[1][9] = "6-2 1-0 RET"
    frame = _clean_career_rows(male_rows, "Rafael Nadal", "1986-06-03")
    assert frame["opponent"].tolist() == ["Stefano Galvani", "Israel Matos Gil"]
    assert frame.index.tolist() == [0, 1]
    assert frame.loc[0, "score"] == "6-2 1-0 RET"


def test_age_difference_can_be_positive_or_zero(female_rows):
    female_rows[0][16] = "19810926"
    female_rows[1][16] = "19820926"
    frame = _clean_career_rows(female_rows, "Serena Williams", "1981-09-26")
    assert frame.loc[0, "age_difference"] == pytest.approx(0)
    assert frame.loc[1, "age_difference"] == pytest.approx(365 / 365.25)


def test_only_walkovers_returns_empty_plotting_table(male_rows):
    for row in male_rows:
        row[9] = "W/O"
    frame = _clean_career_rows(male_rows, "Rafael Nadal", "1986-06-03")
    assert frame.empty
    assert "age_difference" in frame.columns
    assert frame.attrs["player_name"] == "Rafael Nadal"


@pytest.mark.parametrize("date", ["19950230", "1995103", "not-a-date", None])
def test_invalid_match_date(female_rows, date):
    female_rows[0][0] = date
    with pytest.raises(ValueError, match="Match date is invalid"):
        _clean_career_rows(female_rows, "Serena Williams", "1981-09-26")


@pytest.mark.parametrize("birth", ["1981-02-30", "19810926", "", None])
def test_invalid_player_birth_date(female_rows, birth):
    with pytest.raises(ValueError, match="Player birth date is invalid"):
        _clean_career_rows(female_rows, "Serena Williams", birth)


def test_player_born_after_match(female_rows):
    with pytest.raises(ValueError, match="Player age must be between"):
        _clean_career_rows(female_rows, "Serena Williams", "2000-01-01")


@pytest.mark.parametrize("value", ["-1", "101", "nan", "inf", "unknown",
                                  "19770230", "20000101"])
def test_invalid_opponent_age(female_rows, value):
    female_rows[0][16] = value
    with pytest.raises(ValueError, match="Opponent (age|birth date)"):
        _clean_career_rows(female_rows, "Serena Williams", "1981-09-26")


def test_invalid_result(female_rows):
    female_rows[0][4] = "unknown"
    with pytest.raises(ValueError, match="Match results must be W or L"):
        _clean_career_rows(female_rows, "Serena Williams", "1981-09-26")
