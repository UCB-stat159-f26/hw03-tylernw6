"""Test public retrieval with local responses; no live servers are used."""

from io import BytesIO
import json
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from tenniscareer import get_career_matches
from tenniscareer import _retrieval as retrieval

FIXTURES = Path(__file__).parent / "fixtures"
BASE = "https://www.tennisabstract.com"


@pytest.fixture
def mock_downloads(monkeypatch):
    responses, calls = {}, []
    def download(url):
        calls.append(url)
        return responses[url]
    monkeypatch.setattr(retrieval, "_download_text", download)
    return responses, calls


def _player(name="Serena Williams", tour="W", slug="SerenaWilliams"):
    return {"name": name, "tour": tour,
            "url": f"{BASE}/cgi-bin/wplayer.cgi?p=200033/{slug}"}


def _source(rows, birth="19810926", archive=0):
    return f"var dob={birth}; var careerjs={archive}; var matchmx={json.dumps(rows)};"


@pytest.mark.parametrize("name", ["serena williams", "Serena Williams",
                                  "SerenaWilliams", "  Serena   Williams  "])
def test_public_retrieval_accepts_name_variants(mock_downloads, name):
    responses, calls = mock_downloads
    query = retrieval._search_query(name)
    responses[f"{BASE}/cgi-bin/search.cgi?q={retrieval.quote(query)}"] = json.dumps([_player()])
    responses[f"{BASE}/jsmatches/SerenaWilliams.js"] = _source([], archive=1)
    responses[f"{BASE}/jsmatches/SerenaWilliamsCareer.js"] = (
        FIXTURES / "FemalePlayerCareer.JS").read_text()
    frame = get_career_matches(name)
    assert len(frame) == 3
    assert frame.attrs["player_name"] == "Serena Williams"
    assert frame.attrs["player_birth_date"] == "1981-09-26"
    assert len(calls) == 3


def test_male_profile_can_contain_complete_career(mock_downloads):
    responses, calls = mock_downloads
    player = _player("Rafael Nadal", "M", "RafaelNadal")
    rows = retrieval._parse_career_js((FIXTURES / "MalePlayerCareer.JS").read_text())
    responses[f"{BASE}/cgi-bin/search.cgi?q=Rafael%20Nadal"] = json.dumps([player])
    responses[f"{BASE}/cgi-bin/player-classic.cgi?p=RafaelNadal&f=ACareerqq"] = (
        _source(rows, birth="19860603"))
    frame = get_career_matches("Rafael Nadal")
    assert len(frame) == 3
    assert frame.loc[0, "opponent_age"] == pytest.approx(22.264202601)
    assert len(calls) == 2


def test_merge_recent_and_archive_without_duplicate_matches(mock_downloads):
    responses, _ = mock_downloads
    rows = retrieval._parse_career_js((FIXTURES / "MalePlayerCareer.JS").read_text())
    recent = [row.copy() for row in rows[1:]]
    recent[0][16] = "19770603"
    responses[f"{BASE}/jsmatches/RafaelNadalCareer.js"] = (
        "var morematchmx=" + json.dumps(rows[:2]))
    combined = retrieval._complete_match_rows(_source(recent, archive=1), "RafaelNadal")
    assert len(combined) == 3
    assert [row[0] for row in combined] == ["20010910", "20010917", "20010917"]
    assert combined[1][16] == "19770603"


def test_unknown_player_has_meaningful_error(mock_downloads):
    responses, calls = mock_downloads
    responses[f"{BASE}/cgi-bin/search.cgi?q=Gaston%20Sanchez"] = "[]"
    with pytest.raises(ValueError, match="GastonSanchez.*not found"):
        get_career_matches("GastonSanchez")
    assert len(calls) == 1


@pytest.mark.parametrize("name", ["", " ", "123", "?"])
def test_invalid_name_does_not_download(mock_downloads, name):
    _, calls = mock_downloads
    with pytest.raises(ValueError, match="full name"):
        get_career_matches(name)
    assert calls == []


@pytest.mark.parametrize("name", [None, 42, ["Serena Williams"]])
def test_non_text_name_does_not_download(mock_downloads, name):
    _, calls = mock_downloads
    with pytest.raises(TypeError, match="must be text"):
        get_career_matches(name)
    assert calls == []


def test_search_does_not_accept_partial_matches(mock_downloads):
    responses, _ = mock_downloads
    responses[f"{BASE}/cgi-bin/search.cgi?q=Serena"] = json.dumps([_player()])
    with pytest.raises(ValueError, match="not found"):
        get_career_matches("Serena")


def test_ambiguous_names_are_reported(mock_downloads):
    responses, _ = mock_downloads
    responses[f"{BASE}/cgi-bin/search.cgi?q=Serena%20Williams"] = json.dumps([_player()] * 2)
    with pytest.raises(ValueError, match="ambiguous"):
        get_career_matches("Serena Williams")


@pytest.mark.parametrize("content", ["<html>blocked</html>", "{}", "[null]",
                                    '[{"name": "Serena Williams"}]'])
def test_invalid_search_responses(content):
    with pytest.raises(ValueError, match="invalid player-search response"):
        retrieval._search_results(content)


@pytest.mark.parametrize("source", ["", "var dob=19810230;", "var dob='';"])
def test_missing_or_invalid_birth_date(source):
    with pytest.raises(ValueError, match="birth date"):
        retrieval._player_birth_date(source)


def test_accented_and_punctuated_names_compare_consistently():
    assert retrieval._name_key("Iga Świątek") == retrieval._name_key("IgaSwiatek")
    assert retrieval._name_key("Jean-Julien Rojer") == retrieval._name_key("Jean Julien Rojer")


@pytest.mark.parametrize("url", ["https://example.com/", "?p=../../escape", "?p=bad%3Fname"])
def test_invalid_player_identifiers(url):
    player = _player()
    player["url"] = url
    with pytest.raises(ValueError, match="invalid player identifier"):
        retrieval._player_slug(player)


@pytest.mark.parametrize("error", [URLError("unavailable"), TimeoutError("timeout"),
    HTTPError(BASE, 404, "Not Found", None, None)])
def test_download_failure_preserves_cause(monkeypatch, error):
    def fail(*args, **kwargs):
        raise error
    monkeypatch.setattr(retrieval, "urlopen", fail)
    with pytest.raises(ConnectionError, match="Could not download") as caught:
        retrieval._download_text(BASE)
    assert caught.value.__cause__ is error


def test_download_uses_timeout_and_decodes_utf8(monkeypatch):
    calls = []
    def open_response(request, timeout):
        calls.append((request, timeout))
        return BytesIO(b"\xef\xbb\xbfexample")
    monkeypatch.setattr(retrieval, "urlopen", open_response)
    assert retrieval._download_text(BASE) == "example"
    assert calls[0][1] == 20
    assert calls[0][0].get_header("User-agent").startswith("tenniscareer/")
