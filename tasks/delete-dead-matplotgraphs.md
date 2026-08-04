# Delete the dead module: plotutils/matplotgraphs.py

**Status:** done (2026-08-03) — deleted (`git rm`) as part of the gacalc plot-transforms
rewrite; staged, not committed. See `tasks/rewrite-book-plot-transforms-with-gacalc.md`.
**Priority:** 5
**Difficulty:** 1

## The dead file (note)

`src/modelviewprojection/plotsforbook/plotutils/matplotgraphs.py` is **dead code**. Evidence
(checked 2026-08-03):

- **No importers** — `grep -rl 'matplotgraphs' src` returns only the file itself (and the bespoke
  `mpltransformations.py`); nothing imports it.
- **Not a console script** — it is not registered in `pyproject.toml` `[project.scripts]`.
- **Not in the book** — no `literalinclude` / `.. figure::` references it; `grep -rl 'matplotgraphs' book` is empty.

It is a small standalone demo (draws a rotated grid) and one of only two consumers of the
pre-gacalc `mpltransformations.py`.

## Task

Delete `matplotgraphs.py` (and its doctests). Because it is one of the two importers of the
bespoke `plotutils/mpltransformations.py`, removing it — together with migrating the *live*
consumer `generate_plots.py` off the bespoke lib — lets `mpltransformations.py` itself be deleted.

## Execution

Being handled by [[rewrite-book-plot-transforms-with-gacalc]] (the in-flight rewrite):
- `generate_plots.py` (the live book-SVG generator) → migrated to gacalc.
- `matplotgraphs.py` → **deleted** (`git rm`), not migrated (dead; Bill's call, 2026-08-03).
- `mpltransformations.py` → deleted once both importers are gone.

No baseline/pixel-diff applies to `matplotgraphs.py` — it produces no book figure. The pixel-perfect
gate covers only `generate_plots.py`'s output.

## Notes

- Origin: Bill (2026-08-03) — "make a note of the dead file and make a task to delete it."
