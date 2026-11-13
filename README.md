# Tennis Career — HW3

A Python package for retrieving career match data from
[Tennis Abstract](https://www.tennisabstract.com/) and reproducing the HW2
scatter plot for different players, without annotations.

Both public functions are implemented, with offline tests for retrieval,
parsing, cleaning, and plotting. Example charts are saved in `outputs/`.

Assignment requirements are in [instructions.md](instructions.md).

## Package structure

This uses the Python Packaging User Guide's
[src layout](https://packaging.python.org/en/latest/tutorials/packaging-projects/).
The repository contains:

```text
hw03-tylernw6/
├── instructions.md
├── README.md
├── .gitignore
├── pyproject.toml            # metadata, dependencies, build settings
├── MANIFEST.in               # include offline fixtures in the source archive
├── outputs/                  # example Serena PDF, PNG, and source notes
├── src/
│   └── tenniscareer/
│       ├── __init__.py       # package entry point
│       ├── _cleaning.py      # match fields and age calculations
│       ├── _parsing.py       # private JS match-array parser
│       ├── _plotting.py      # scatter plot and input validation
│       └── _retrieval.py     # player lookup and full-career downloads
└── tests/
    ├── conftest.py          # blocks network connections during tests
    ├── test_cleaning.py     # schema, ages, walkovers, and invalid fields
    ├── test_retrieval.py    # mocked search, downloads, and public function
    ├── test_parsing.py      # fixture and malformed-input tests
    ├── test_plotting.py     # coordinates, labels, and PNG/PDF exports
    └── fixtures/            # assignment samples and source notes
```

The public functions are `get_career_matches()` and `plot_career_matches()`.

## Setup and downloads, one step at a time

Use Python 3.11 or newer and Git. Run these commands from the repository root.

### Step 1: create an isolated environment (no download)

```bash
python3 -m venv .venv
source .venv/bin/activate
python --version
python -m pip --version
```

The environment keeps this project's packages separate. Activate it again
when opening a new terminal. `.venv/` is ignored by Git.

### Step 2: download pandas for match tables

```bash
python -m pip install 'pandas>=2'
python -c 'import pandas; print(pandas.__version__)'
```

Pip also installs pandas' required dependencies automatically.

### Step 3: download Matplotlib for the scatter plot

```bash
python -m pip install 'matplotlib>=3.7'
python -c 'import matplotlib; print(matplotlib.__version__)'
```

### Step 4: download pytest for offline tests

```bash
python -m pip install 'pytest>=7'
python -m pytest --version
```

### Step 5: install this package locally

```bash
python -m pip install -e .
python -c 'import tenniscareer; print(tenniscareer.__file__)'
```

This makes changes under `src/` available to Python. Pip downloads the
setuptools build dependency automatically if needed.

### Step 6: download the build tool when checking distribution files

```bash
python -m pip install 'build>=1' 'setuptools>=68' wheel
python -m build --no-isolation
```

This produces a wheel and source archive in the ignored `dist/` folder.
Once the build tools are installed, this build command works offline.

Python's built-in `urllib`, `json`, and date tools need no separate download.

### HTTPS certificates on this Mac

If Python reports `CERTIFICATE_VERIFY_FAILED` on macOS, use the existing
macOS certificate bundle before making live downloads:

```bash
export SSL_CERT_FILE=/etc/ssl/cert.pem
```

This keeps HTTPS verification enabled. Computers with working Python
certificate settings do not need this Mac-specific step.

## Retrieve a player's career

After the local installation in Step 5, run Python and use the public function:

```python
from tenniscareer import get_career_matches

serena = get_career_matches("serena williams")
rafa = get_career_matches("RafaelNadal")
print(serena.head())
print(rafa.attrs)
```

For the assignment's direct GitHub installation, use:

```bash
python -m pip install git+https://github.com/UCB-stat159-f26/hw03-tylernw6.git
```

Spaced names and joined CamelCase names are accepted. Search requires a full
name, rather than guessing from a partial match. An unknown name such as
`GastonSanchez` raises a descriptive `ValueError`. Failed downloads raise
`ConnectionError` with the underlying cause preserved. Each request has a
20-second timeout.

The function resolves the canonical name using Tennis Abstract's player
search. It reads women's metadata and recent matches from the player's JS
file, and men's metadata and matches from the classic player page. When the
source sets `careerjs=1`, it also retrieves `Career.js`. Overlapping matches
are combined using date, tournament, round, opponent, result, and score;
recent versions take precedence. Matches are returned in date order.

## Plot and save a career

```python
import matplotlib.pyplot as plt
from tenniscareer import get_career_matches, plot_career_matches

serena = get_career_matches("Serena Williams")
ax = plot_career_matches(serena)
ax.figure.savefig("outputs/serena_career.png", dpi=150)
ax.figure.savefig("outputs/serena_career.pdf")
plt.show()
```

The plot places player age on the top x-axis and player age minus opponent
age on the y-axis. Wins are cyan and losses are purple. The zero reference
line means the players were the same age. A positive value means the player
was older than the opponent. Bounds adapt to the data. The title uses the
player name from the data frame's metadata, falling back to `Player` when it
is unavailable. Match annotations are omitted as required by HW3.

The function returns a Matplotlib `Axes` so you can save or customize the
figure. To draw in an existing subplot, use `plot_career_matches(serena, ax=ax)`.
It does not modify the input table or call `plt.show()` automatically.
Matches with missing coordinates are omitted from the plot; if no matches
remain, it raises a clear `ValueError`. Invalid results, nonnumeric or infinite
coordinates, and player ages outside 0–100 years also raise clear errors.

Saved examples are available in [outputs/](outputs/README.md), including the
[PDF](outputs/serena_career.pdf) and [PNG](outputs/serena_career.png).

## Running the offline tests

With `.venv` active, run:

```bash
python -m pytest -q
```

Tests read the source from `src/` and block network connections. The
[women's and men's fixtures](tests/fixtures/README.md) come from the assignment;
retrieval tests mock server responses. No manual data download is needed.
Tests cover parsing, age calculations, name variants, errors, archive merging,
plot coordinates and colors, and PNG/PDF saving. Downloaded JavaScript is
parsed as data and never executed.

## Clean match data

`get_career_matches()` returns these columns:

| Column | Meaning |
| --- | --- |
| `match_date` | Match date as a pandas datetime |
| `tournament`, `surface`, `score`, `opponent` | Source match details |
| `result` | `W` or `L` from the player's perspective |
| `player_age` | Player's age at the match, in years |
| `opponent_age` | Opponent's age at the match, in years |
| `age_difference` | Player age minus opponent age; positive means older |

For dates of birth, ages use elapsed days divided by 365.25. Men's supplied
decimal opponent ages are preserved. Missing opponent ages remain missing,
and the match stays in the table. Invalid nonempty ages or dates raise clear
errors. Walkovers (`W/O` or `walkover` in the score) are excluded to match
the earlier chart; retirements remain. Player name and birth date are stored
in the data frame's `attrs` metadata. Raw rows are never modified.

## Package verification

Verified on November 12, 2026: 106 offline tests passed, including tests from
the source archive against an installed wheel outside the repository. Both
fixtures and the network-blocking configuration are included in the archive.
Editable installation, dependency checks, and installation directly from
GitHub also succeeded. The example PDF was rendered and visually reviewed.

All package functions meet the 20-line limit; private helpers are at most
10 lines, including definitions and docstrings. Generated build files and
caches are ignored by Git. HW3 does not require a Makefile or `environment.yml`.
