# Fix demo01's empty `import first module` doc-region (Sphinx anchor warning)

**Status:** proposed — needs go-ahead. Created 2026-07-22. Found while confirming the book renders
after the gacalc-0.0.13 bump. **Pre-existing**, unrelated to gacalc/find_normal. Trivial.

## Symptom

`make html` emits:

```
ch01.rst:169: WARNING: end-before pattern not found: doc-region-end import first module [docutils]
```

`ch01.rst` (~line 171-172) `literalinclude`s `demos/demo01.py` with
`:start-after: doc-region-begin import first module` / `:end-before: doc-region-end import first
module` — so the chapter renders an **empty** listing where the first-module imports should be.

## Root cause (verified)

In `src/modelviewprojection/demos/demo01.py` the two markers are **adjacent, with nothing between
them**, and the imports come *after* the end marker:

```python
# doc-region-begin import first module
# doc-region-end import first module
import sys
import typing
import glfw
import OpenGL.GL as GL
```

The region is empty; Sphinx's `end-before` search (which starts *after* the `start-after` line) can't
resolve to a non-degenerate slice, hence the warning + empty include.

## Fix

Move `# doc-region-end import first module` to **below** the import block, so the region contains the
imports the chapter means to show:

```python
# doc-region-begin import first module
import sys
import typing
import glfw
import OpenGL.GL as GL
# doc-region-end import first module
```

Check ch01.rst's surrounding prose to confirm which imports it intends to display (the whole block
above, or a subset), and place the end marker accordingly.

## Note

This lands **inside a published doc-region**, so it changes the ch01 listing (currently empty → the
imports). That's the point. `make check-regions` should stay green (the markers remain balanced and
uniquely named).

## Verify

Clean `make html`: no `end-before pattern not found` warning; ch01 renders the import listing.

## Relationships

- Sibling findings: `tasks/archive/2026/07/23/fix-editable-install-system-flag.md`,
  `tasks/texexptopng-standalone-display-math.md`.
- Context: `tasks/archive/2026/07/22/dual-coefficient-cleanup.md`.
