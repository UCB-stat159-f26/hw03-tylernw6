"""Exercise parsing with assignment fixtures and malformed local inputs."""

import json
from pathlib import Path

import pytest

from tenniscareer._parsing import _parse_career_js

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("filename, first_date, opponent, age_field", [
    ("FemalePlayerCareer.JS", "19951030", "Anne Miller", "19770119"),
    ("MalePlayerCareer.JS", "20010910", "Guillermo Platel", "22.264202601"),
])
def test_parse_assignment_fixtures(filename, first_date, opponent, age_field):
    rows = _parse_career_js((FIXTURES / filename).read_text())
    assert len(rows) == 3
    assert rows[0][0] == first_date
    assert rows[0][11] == opponent
    assert rows[0][16] == age_field


def test_preserve_result_order_and_variable_row_lengths():
    female = _parse_career_js((FIXTURES / "FemalePlayerCareer.JS").read_text())
    male = _parse_career_js((FIXTURES / "MalePlayerCareer.JS").read_text())
    assert [row[4] for row in female] == ["L", "L", "L"]
    assert [row[4] for row in male] == ["L", "L", "W"]
    assert len(female[0]) != len(male[0])


def test_allow_surrounding_statements_and_brackets_in_strings():
    row = [""] * 17
    row[11] = 'Opponent [name] with "quotes" and a backslash \\'
    javascript = 'var metadata = "example";\nvar morematchmx =\n'
    javascript += json.dumps([row]) + ';\nthrow new Error("must not execute");'
    assert _parse_career_js(javascript) == [row]


@pytest.mark.parametrize("javascript", ["", "var other = [];", "morematchmx()"])
def test_missing_assignment(javascript):
    with pytest.raises(ValueError, match="missing the morematchmx array"):
        _parse_career_js(javascript)


@pytest.mark.parametrize("value", ["[[", "undefined", "[[1,]]", "alert('run')"])
def test_malformed_json(value):
    with pytest.raises(ValueError, match="malformed JSON"):
        _parse_career_js("var morematchmx = " + value)


@pytest.mark.parametrize("value", [[], {}, None, "text", 1])
def test_empty_or_non_array_matches(value):
    with pytest.raises(ValueError, match="nonempty list of rows"):
        _parse_career_js("var morematchmx = " + json.dumps(value))


@pytest.mark.parametrize("row", [[], [""] * 16, "not a row", None, {}])
def test_invalid_match_rows(row):
    with pytest.raises(ValueError, match="at least 17 fields"):
        _parse_career_js("var morematchmx = " + json.dumps([row]))


@pytest.mark.parametrize("value", [None, b"var morematchmx = [];", 42])
def test_non_text_input(value):
    with pytest.raises(TypeError, match="must be text"):
        _parse_career_js(value)
