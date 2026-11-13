"""Resolve player names and retrieve complete Tennis Abstract match data."""

import json
import re
import unicodedata
from urllib.parse import parse_qs, quote, urlparse
from urllib.request import Request, urlopen

import pandas as pd

from ._cleaning import _clean_career_rows, _parse_date
from ._parsing import _parse_career_js, _parse_match_array

_BASE_URL = "https://www.tennisabstract.com"


def get_career_matches(player_name: str) -> pd.DataFrame:
    """Fetch a player's complete available career as a clean match table.

    Accept spaced or CamelCase names. Invalid names raise ValueError;
    download failures raise ConnectionError. This function contacts the site.
    """
    player = _find_player(player_name)
    slug = _player_slug(player)
    source = _download_text(_profile_url(player, slug))
    birth_date = _player_birth_date(source)
    rows = _complete_match_rows(source, slug)
    return _clean_career_rows(rows, player["name"], birth_date)


def _name_key(name: str) -> str:
    """Compare names without case, accents, spacing, or punctuation."""
    folded = unicodedata.normalize("NFKD", name.casefold())
    return "".join(char for char in folded if char.isalnum())


def _search_query(player_name: str) -> str:
    """Validate input and split joined CamelCase player names."""
    if not isinstance(player_name, str):
        raise TypeError("Player name must be text.")
    if len(_name_key(player_name)) < 2 or not any(c.isalpha() for c in player_name):
        raise ValueError("Provide a player's full name, such as Serena Williams.")
    return " ".join(re.sub(r"(?<=[a-z])(?=[A-Z])", " ", player_name).split())


def _find_player(player_name: str) -> dict:
    """Require one exact normalized match from the site's player search."""
    query = _search_query(player_name)
    candidates = _search_results(_download_text(
        f"{_BASE_URL}/cgi-bin/search.cgi?q={quote(query)}"))
    matches = [p for p in candidates if _name_key(p["name"]) == _name_key(query)]
    if not matches:
        raise ValueError(f"Player {player_name!r} was not found on Tennis Abstract.")
    if len(matches) > 1:
        raise ValueError(f"Player name {player_name!r} is ambiguous on Tennis Abstract.")
    return matches[0]


def _search_results(content: str) -> list[dict]:
    """Detect changed or blocked search responses before using them."""
    try:
        results = json.loads(content)
        if not isinstance(results, list) or not all(map(_valid_player, results)):
            raise ValueError("Invalid search results")
    except ValueError as error:
        raise ValueError("Tennis Abstract returned an invalid player-search response.") from error
    return results


def _valid_player(player: dict) -> bool:
    """Check search fields before selecting a canonical player."""
    return isinstance(player, dict) and all(
        isinstance(player.get(key), str) for key in ("name", "tour", "url"))


def _player_slug(player: dict) -> str:
    """Use only the player identifier from the canonical search URL."""
    query = parse_qs(urlparse(player["url"]).query)
    match = re.fullmatch(r"(?:\d+/)?([A-Za-z0-9'-]+)", query.get("p", [""])[0])
    if match is None or player["tour"] not in ("M", "W"):
        raise ValueError("Tennis Abstract returned an invalid player identifier.")
    return match[1]


def _profile_url(player: dict, slug: str) -> str:
    """Women's metadata is external; men's classic pages embed match data."""
    if player["tour"] == "W":
        return f"{_BASE_URL}/jsmatches/{quote(slug)}.js"
    return f"{_BASE_URL}/cgi-bin/player-classic.cgi?p={quote(slug)}&f=ACareerqq"


def _player_birth_date(source: str) -> str:
    """Read the player's DOB assignment, not opponents' dates."""
    match = re.search(r"\bvar\s+dob\s*=\s*['\"]?(\d{8})['\"]?\s*;", source)
    if match is None:
        raise ValueError("Player birth date is missing from Tennis Abstract data.")
    return _parse_date(match[1], "%Y%m%d", "Player birth date").strftime("%Y-%m-%d")


def _complete_match_rows(source: str, slug: str) -> list[list]:
    """Combine recent and archived arrays when the source requests both."""
    recent = _parse_match_array(source, "matchmx", allow_empty=True)
    archived = []
    if re.search(r"\bvar\s+careerjs\s*=\s*1\s*;", source):
        archived = _parse_career_js(_download_text(
            f"{_BASE_URL}/jsmatches/{quote(slug)}Career.js"))
    return _merge_match_rows(recent, archived)


def _merge_match_rows(recent: list[list], archived: list[list]) -> list[list]:
    """Keep recent versions of overlapping matches, then order by date."""
    matches = {}
    for row in recent + archived:
        key = tuple(row[index] for index in (0, 1, 8, 11, 4, 9))
        matches.setdefault(key, row)
    return sorted(matches.values(), key=lambda row: row[0])


def _download_text(url: str) -> str:
    """Download text with a finite timeout and preserve the failure cause."""
    request = Request(url, headers={"User-Agent": "tenniscareer/0.1.0 (Python urllib)"})
    try:
        with urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise ConnectionError(f"Could not download Tennis Abstract data: {url}") from error
