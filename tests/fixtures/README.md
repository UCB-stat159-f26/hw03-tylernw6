# Offline career samples

These two JavaScript fixtures are copied from the mock examples in the
HW3 [assignment requirements](../../instructions.md). Only the introductory
`#` comment was removed, since it is not JavaScript syntax. Match values and
row order are unchanged. Neither file was downloaded from a live server.

- `FemalePlayerCareer.JS`: three matches, with opponent birth dates such as
  `19770119` in field 16 (counting from zero).
- `MalePlayerCareer.JS`: three matches, with decimal opponent ages such as
  `22.264202601` in field 16.

Both files assign an array to `var morematchmx`. Useful shared fields are
match date (0), tournament (1), surface (2), result (4), and opponent name (11).
The different row lengths must not be treated as a single fixed-width schema.

Upcoming parser and cleaning tests will read these files locally. The women's
sample contains only losses; the men's sample includes both wins and losses.
Additional edge cases will be tested separately as the implementation grows.
