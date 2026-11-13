"""Plot career matches by player age and opponent age difference."""

import math

from matplotlib.axes import Axes
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator, MultipleLocator
import pandas as pd

_COORDINATES = ["player_age", "age_difference"]
_COLORS = {"W": "#49cbe7", "L": "#a34ea7"}


def plot_career_matches(matches: pd.DataFrame, ax: Axes | None = None) -> Axes:
    """Return a scatter-plot Axes for a cleaned career table.

    Player age is horizontal; player minus opponent age is vertical.
    Missing coordinates are omitted. Save with ax.figure.savefig(...).
    """
    frame = _plot_data(matches)
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 8), layout="constrained")
    _draw_matches(ax, frame)
    _style_axes(ax)
    _set_age_ticks(ax, frame)
    _label_plot(ax, matches.attrs.get("player_name", "Player"))
    return ax


def _validate_plot_input(matches: pd.DataFrame) -> None:
    """Require a data frame with the plotting fields and known results."""
    if not isinstance(matches, pd.DataFrame):
        raise TypeError("Matches must be a pandas DataFrame from get_career_matches().")
    missing = set(_COORDINATES + ["result"]) - set(matches.columns)
    if missing:
        raise ValueError(f"Match data is missing required columns: {', '.join(sorted(missing))}.")
    if not matches["result"].isin(["W", "L"]).all():
        raise ValueError("Match results must be W or L.")


def _plot_data(matches: pd.DataFrame) -> pd.DataFrame:
    """Prepare a separate plotting table without changing the input."""
    _validate_plot_input(matches)
    frame = matches[_COORDINATES + ["result"]].copy()
    frame[_COORDINATES] = _numeric_coordinates(frame)
    frame = frame.dropna(subset=_COORDINATES)
    _check_coordinates(frame)
    return frame


def _numeric_coordinates(frame: pd.DataFrame) -> pd.DataFrame:
    """Accept numeric coordinates and report invalid values clearly."""
    try:
        return frame[_COORDINATES].apply(pd.to_numeric, errors="raise")
    except (ValueError, TypeError) as error:
        raise ValueError("Player ages and age differences must be numeric.") from error


def _check_coordinates(frame: pd.DataFrame) -> None:
    """Reject unplottable tables before creating a figure."""
    if frame.empty:
        raise ValueError("No matches with known player and opponent ages to plot.")
    if not all(frame[column].map(math.isfinite).all() for column in _COORDINATES):
        raise ValueError("Plot coordinates must be finite numbers.")
    if not frame["player_age"].between(0, 100).all():
        raise ValueError("Player age must be between 0 and 100 years.")


def _draw_matches(ax: Axes, frame: pd.DataFrame) -> None:
    """Draw one point per match with separate win and loss colors."""
    for result, color in _COLORS.items():
        group = frame.loc[frame["result"] == result]
        label = "Match won" if result == "W" else "Match lost"
        ax.scatter(group["player_age"], group["age_difference"], s=18,
                   color=color, alpha=0.9, edgecolors="none", label=label, zorder=3)


def _style_axes(ax: Axes) -> None:
    """Use a white background, light grid, and a same-age reference line."""
    ax.set_facecolor("white")
    ax.set_axisbelow(True)
    ax.grid(color="#e5e5e5", linewidth=0.8)
    ax.axhline(0, color="#888888", linewidth=1, zorder=2)
    ax.spines[["top", "right", "bottom", "left"]].set_visible(False)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.tick_params(axis="both", length=0, labelcolor="#777777", pad=8)


def _set_age_ticks(ax: Axes, frame: pd.DataFrame) -> None:
    """Choose bounds from the data, always including the same-age line."""
    ax.set_xlim(math.floor(frame["player_age"].min()) - 0.6,
                math.ceil(frame["player_age"].max()) + 0.6)
    extent = max(20, math.ceil(frame["age_difference"].abs().max() / 5) * 5)
    ax.set_ylim(-extent - 1, extent + 1)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=14, integer=True))
    ax.yaxis.set_major_locator(MultipleLocator(10))
    ax.yaxis.set_major_formatter(FuncFormatter(_age_difference_label))


def _age_difference_label(value: float, position: int) -> str:
    """Label zero as same age and show signed differences elsewhere."""
    return "Same age" if value == 0 else f"{value:+.0f}"


def _label_plot(ax: Axes, player_name: str) -> None:
    """Add a player-specific title and legend, without match annotations."""
    ax.set_title(f"{player_name}’s Professional Matches", loc="left",
                 fontsize=18, fontweight="bold", pad=80)
    ax.set_xlabel("Player’s age (years)", color="#777777", labelpad=12)
    ax.set_ylabel("Player age − opponent age (years)", color="#777777", labelpad=12)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.10), ncol=2,
              frameon=False, borderaxespad=0, markerscale=1.3)
