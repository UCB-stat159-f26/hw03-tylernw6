# Example career plot

- `serena_career.pdf`: vector PDF for opening or printing.
- `serena_career.png`: the same chart as a PNG preview.

Generated with `plot_career_matches()` on November 12, 2026 using the existing
downloaded `SerenaWilliamsCareer.js` snapshot reviewed during HW3 development.
The snapshot has 1,038 records spanning October 30, 1995 to August 29, 2022;
the chart includes 1,016 played matches after excluding 22 walkovers.

Data source: [Tennis Abstract career file](https://www.tennisabstract.com/jsmatches/SerenaWilliamsCareer.js).
The original snapshot is not included here. Live data can change, so a new
download may produce a different chart. These examples demonstrate the package
output; they are not the tiny test fixtures under `tests/fixtures/`.

To produce a new chart from the current full available career, after installing
the package (and configuring HTTPS certificates if necessary), run:

```python
from tenniscareer import get_career_matches, plot_career_matches

matches = get_career_matches("Serena Williams")
ax = plot_career_matches(matches)
ax.figure.savefig("outputs/serena_career.pdf")
ax.figure.savefig("outputs/serena_career.png", dpi=150)
```
