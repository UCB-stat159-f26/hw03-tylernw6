"""Verify plotted coordinates and presentation using only local data."""

from pathlib import Path

from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.colors import to_rgba
import pandas as pd
import pytest

from tenniscareer import plot_career_matches
from tenniscareer._cleaning import _clean_career_rows
from tenniscareer._parsing import _parse_career_js

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.fixture
def matches():
    rows = _parse_career_js((FIXTURES / "MalePlayerCareer.JS").read_text())
    return _clean_career_rows(rows, "Rafael Nadal", "1986-06-03")


def test_plot_positions_and_colors_match_results(matches):
    ax = plot_career_matches(matches)
    assert isinstance(ax, Axes)
    for collection, result, color in zip(ax.collections, ["W", "L"], ["#49cbe7", "#a34ea7"]):
        expected = matches.loc[matches["result"] == result, ["player_age", "age_difference"]]
        assert collection.get_offsets().tolist() == expected.to_numpy().tolist()
        assert collection.get_facecolors()[0] == pytest.approx(to_rgba(color, 0.9))


def test_title_labels_legend_and_zero_reference(matches):
    ax = plot_career_matches(matches)
    assert "Rafael Nadal" in ax.get_title(loc="left")
    assert ax.xaxis.get_ticks_position() == "top"
    assert ax.get_xlabel() == "Player’s age (years)"
    assert ax.get_ylabel() == "Player age − opponent age (years)"
    assert [text.get_text() for text in ax.get_legend().get_texts()] == ["Match won", "Match lost"]
    assert list(ax.lines[0].get_ydata()) == [0, 0]
    assert ax.yaxis.get_major_formatter()(0, 0) == "Same age"
    assert len(ax.texts) == 0


def test_can_draw_into_existing_axes(matches):
    _, ax = plt.subplots()
    assert plot_career_matches(matches, ax=ax) is ax


def test_plot_does_not_modify_input(matches):
    original = matches.copy(deep=True)
    plot_career_matches(matches)
    pd.testing.assert_frame_equal(matches, original)
    assert matches.attrs == original.attrs


def test_missing_age_omits_only_affected_match(matches):
    matches.loc[0, "age_difference"] = float("nan")
    ax = plot_career_matches(matches)
    assert sum(len(collection.get_offsets()) for collection in ax.collections) == 2


def test_bounds_include_older_and_younger_opponents(matches):
    matches["age_difference"] = [-28, 0, 31]
    ax = plot_career_matches(matches)
    assert ax.get_ylim()[0] < -28
    assert ax.get_ylim()[1] > 31
    assert ax.get_xlim()[0] < matches["player_age"].min()
    assert ax.get_xlim()[1] > matches["player_age"].max()


def test_single_match_without_metadata_has_generic_title(matches):
    single = matches.iloc[:1].copy()
    single.attrs.clear()
    ax = plot_career_matches(single)
    assert "Player" in ax.get_title(loc="left")
    assert sum(len(collection.get_offsets()) for collection in ax.collections) == 1


def test_save_png_and_pdf(matches, tmp_path):
    ax = plot_career_matches(matches)
    png, pdf = tmp_path / "career.png", tmp_path / "career.pdf"
    ax.figure.savefig(png)
    ax.figure.savefig(pdf)
    assert png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert pdf.read_bytes().startswith(b"%PDF")


@pytest.mark.parametrize("value", [None, [], "matches"])
def test_reject_non_dataframe_input(value):
    with pytest.raises(TypeError, match="pandas DataFrame"):
        plot_career_matches(value)


@pytest.mark.parametrize("column", ["player_age", "age_difference", "result"])
def test_missing_required_columns(matches, column):
    with pytest.raises(ValueError, match=f"missing required columns: {column}"):
        plot_career_matches(matches.drop(columns=column))


@pytest.mark.parametrize("kind", ["empty", "missing"])
def test_no_plottable_matches(matches, kind):
    if kind == "empty":
        matches = matches.iloc[:0]
    else:
        matches["age_difference"] = float("nan")
    with pytest.raises(ValueError, match="No matches with known"):
        plot_career_matches(matches)
    assert plt.get_fignums() == []


@pytest.mark.parametrize("value", [float("inf"), -float("inf")])
def test_infinite_coordinates(matches, value):
    matches.loc[0, "age_difference"] = value
    with pytest.raises(ValueError, match="finite numbers"):
        plot_career_matches(matches)


def test_invalid_coordinate_text(matches):
    matches["age_difference"] = "unknown"
    with pytest.raises(ValueError, match="must be numeric"):
        plot_career_matches(matches)


def test_invalid_result(matches):
    matches.loc[0, "result"] = "unknown"
    with pytest.raises(ValueError, match="results must be W or L"):
        plot_career_matches(matches)


@pytest.mark.parametrize("age", [-1, 101])
def test_invalid_player_age(matches, age):
    matches.loc[0, "player_age"] = age
    with pytest.raises(ValueError, match="between 0 and 100"):
        plot_career_matches(matches)
