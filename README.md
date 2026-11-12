# Tennis Career — HW3

A Python package in development for retrieving career match data from
[Tennis Abstract](https://www.tennisabstract.com/) and reproducing the HW2
scatter plot for different players, without annotations.

**Current stage:** package scaffold, setup guide, and local women's and men's
JS fixtures. Retrieval, plotting, and tests are not implemented yet.

## Assignment requirements

The authoritative requirements are in [instructions.md](instructions.md).

- Provide two public functions: retrieve clean career data and plot that data.
- Accept names such as `serena williams`, `Serena Williams`, and `SerenaWilliams`.
- Give a meaningful error for an invalid player name.
- Support both women's opponent birth dates and men's opponent ages.
- Keep every function to at most 20 code lines, excluding comments and blanks;
  aim for at most 10 lines for private helpers.
- Test parsing and cleaning with local JS fixtures; automated tests must never
  contact live servers.
- Support installation directly from this GitHub repository.
- Make small, coherent commits with descriptive messages.

HW3 does not require a Makefile or `environment.yml`.

## Package structure

This uses the Python Packaging User Guide's
[src layout](https://packaging.python.org/en/latest/tutorials/packaging-projects/).
The initial files are:

```text
hw03-tylernw6/
├── instructions.md
├── README.md
├── .gitignore
├── pyproject.toml            # metadata, dependencies, build settings
├── src/
│   └── tenniscareer/
│       └── __init__.py       # package entry point
└── tests/
    └── fixtures/            # assignment samples and source notes
```

Next we will add modules for retrieval, cleaning, and plotting under
`src/tenniscareer/`, with corresponding tests under `tests/`.

## Setup and downloads, one step at a time

Run these commands in Terminal from this repository's root folder.
Python 3.11.9, pip, and Git were already available on this Mac when checked.
You do not need to download another Python installer.

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
python -m pip install 'build>=1'
python -m build
```

This produces a wheel and source archive in the ignored `dist/` folder.
We will check package installation and offline tests as implementation proceeds.

Python's built-in `urllib`, `json`, and date tools need no separate download.
This package workflow does not need Quarto, LaTeX, Jupyter, or Conda.

## Data and the earlier homework

The existing HW2 instructions, downloaded `SerenaWilliamsCareer.js`, and
`serena_matches.png` were reviewed for context. The earlier chart uses player
age on the x-axis, player age minus opponent age on the y-axis, and colors
for wins and losses. HW3 will generalize this to other players and omit the
annotations.

You do not need to manually download career files for automated tests. Small
women's and men's fixtures from the mock examples in `instructions.md` are
stored in [tests/fixtures/](tests/fixtures/README.md). Live downloads belong
in the public retrieval function, not in the automated test suite.

## Planned commit sequence

1. Initialize package structure and setup documentation.
2. Add local women's and men's JS fixtures.
3. Implement parsing with offline tests.
4. Implement cleaning, including opponent age handling.
5. Implement player-name handling and career retrieval.
6. Add the scatter plot and plotting tests.
7. Finish usage documentation and verify installation from a built package.

Each commit will contain one completed step and its relevant verification.
