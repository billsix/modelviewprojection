# check_doc_regions: catch empty slices; decide fate of dead markers

**Status:** not started
**Created:** 2026-07-30

## Problem 1 — degenerate (empty) regions pass the checker

`tools/check_doc_regions.py` asserts only that the `doc-region-begin <name>` /
`doc-region-end <name>` strings **exist** in the target file. Two *adjacent*
markers with no lines between them therefore pass, while Sphinx warns
`end-before pattern not found` and renders an **empty listing**. This shipped:
ch01's "Importing Libraries" listing was empty
(`tasks/archive/2026/07/23/demo01-import-region-empty.md`).

**Fix:** for each `literalinclude`'s resolved anchor pair, also assert the
slice between the begin line and the end line is non-empty (≥1 non-marker
line). Mirror Sphinx's containing-line match semantics, as the existing
checks do. Runs in-container like the rest of the checker (gacalc anchors
resolve against `_gacalc_src` — see `tasks/reference/book-and-docs-pipeline.md`
§2).

## Problem 2 — decide the fate of the 7 dead markers

The checker validates book→code only; markers no chapter includes are
invisible. Current dead set (verified 2026-07-30; list also in
`tasks/reference/tests-and-gates.md` §7):

- `clockwise`, `counter clockwise`, `parallel` —
  `framebuffer/softwarerendering.py`
- `define find normal`, `define plane equation`, `define distance to plane` —
  `mathutils.py`
- `planar shadow` — `demos/demo22/demo22.py`

**Bill's call per marker:** keep as a future book anchor (plausible for the
mathutils trio and `planar shadow`, given `tasks/planar-shadow-matrix.md` and
the drift trackers), or delete. Optionally: add a dead-marker *report* mode to
the checker (not a failure — reuse across files is legitimate and scoped by
target path, so only truly-unreferenced names should be listed).

## Verification

`make check-regions` green; deliberately create an adjacent-marker pair in a
scratch branch and confirm the new check fails loudly on it.
