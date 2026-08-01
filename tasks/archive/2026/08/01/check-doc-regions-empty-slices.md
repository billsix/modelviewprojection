# check_doc_regions: catch empty slices; decide fate of dead markers

**Status:** DONE 2026-08-01 — both problems resolved (empty-slice check +
report mode landed; the 7 dead markers deleted per Bill's call). Archived.

## Problem 2 — DONE (2026-08-01, Bill: "delete" + "add the report mode")

- **Deleted the 7 dead marker pairs** (14 comment lines; the code between each
  stays): `clockwise` / `counter clockwise` / `parallel` in
  `framebuffer/softwarerendering.py`; `define find normal` / `define plane
  equation` / `define distance to plane` in `mathutils.py`; `planar shadow` in
  `demos/demo22/demo22.py`. ruff + ty + `py_compile` clean afterward.
- **Added an opt-in `--report-dead` mode** to the checker
  (`_referenced_anchors` + `_dead_marker_report`): lists every first-party
  doc-region marker no `literalinclude` references (matched by target file +
  name + begin/end kind). Informational only — **outside** the pass/fail total,
  never changes the exit code (an unreferenced marker may be a deliberate anchor
  for an unwritten chapter). Off by default so `make check-regions` /
  `entrypoint.sh` stay focused on the 3 pass/fail checks.
- **Fixed a real marker-regex bug found en route:** `_BEGIN_MARKER`/`_END_MARKER`
  matched `# doc-region-begin` *anywhere* on a line, so marker syntax inside a
  string literal (the new test file) or mid-line in prose (this checker's own
  line 63) registered as a marker — which had started tripping the existing
  **name-collision** check. Anchored both to line-start
  (`^[ \t]*#[ \t]*doc-region-…`); all real markers are their own comment line,
  so nothing genuine is lost. New tests lock this in.

Tests (now 10, all green): the empty-region set above, plus
`test_markers_match_only_comment_lines` (anchoring) and
`test_dead_marker_report_flags_only_unreferenced`.

### Newly surfaced, NOT acted on — 23 more dead markers (Bill to decide separately)

`--report-dead` also found **23** dead markers beyond the curated 7, all in
demos the book includes only *partially* (a chapter includes some regions of the
file, not these): `demo15.py` (7 regions), `demo16.py` (3), `demo12.py` (1),
`demo19.py`/`demo20.py` (`of paddle 1`, 1 each), `demo22.py`. These are
**book-drift** territory (a chapter that should include them, or markers to
retire), distinct from the orphaned 7 — left untouched pending Bill's call;
relate to `tasks/book-code-drift-ch7-15.md` / `book-code-drift-ch16-21.md`.
Run `python tools/check_doc_regions.py --report-dead` to see the current list.

**Created:** 2026-07-30

## Problem 1 — DONE (2026-08-01)

## Problem 1 — DONE (2026-08-01)

Added a third check to `tools/check_doc_regions.py`:
- `_region_is_empty(source, start_name, end_name)` — a pure helper: `True` iff
  no content line (non-blank, non-marker) lies strictly between the first
  `doc-region-begin <start>` line and the first *following* `doc-region-end
  <end>` line. Mirrors Sphinx's "first line *containing* the anchor, end
  searched after start" semantics. Returns `False` when the ordered pair can't
  be located (existence/order stay checks 1's job — no double-report).
- `_empty_region_errors()` — runs it for every directive that has BOTH a
  `:start-after:` and an `:end-before:` and whose target + both markers exist;
  a one-sided include (runs to BOF/EOF) is a different case and skipped.
- `main()` aggregates and prints an EMPTY REGIONS section; success message and
  the module docstring updated (Problem 1 was the ch01 "Importing Libraries"
  bug). Handles split regions (begin/end names differ) and marker-only/blank
  slices.

Tests: `tests/test_check_doc_regions.py` — 7 parametrized `_region_is_empty`
cases + an end-to-end `_empty_region_errors` case (adjacent flagged, good
region passed), loading the gate script by path (it isn't on the test
`pythonpath`). ruff + ty clean; 8/8 pass. Real-book run adds **0** empty-region
findings (the only sandbox output is the 15 `_gacalc_src/*` targets, which exist
only in-container — unchanged from baseline). In-container `make check-regions`
stays green (ch01's empty region was already fixed).

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
