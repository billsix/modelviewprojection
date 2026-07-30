# Reference-docs expansion (2026-07-30)

**Status:** COMPLETE 2026-07-30. All five docs written, all four existing
reference docs corrected, cleanups applied. Verified in-sandbox: colorutils
compiles + ruff-clean; pytest 95 passed with the one pre-existing failure
being the stale sibling venv's gacalc 0.0.9 (pin is 0.0.14), not a repo
regression. Containerized `make format` / `make html` remain Bill's gates.

**Goal (Bill, 2026-07-30):** after a full sweep of the repo, the four existing
reference docs, and all 107 archived tasks, create the five missing reference
docs, fix the drift found in the existing four, and clean up the stale docs
found along the way. Approved: "all of them are good to go! do it!"

## Deliverables

New reference docs:
1. `tasks/reference/book-figures-and-images.md` — the five figure toolchains + inlinetex + notebooks pipeline
2. `tasks/reference/gl-and-imgui-gotchas.md` — the ports-era GL/imgui/GLFW trap corpus (incl. the planar-shadow w<0 correction)
3. `tasks/reference/superbible-ports-guide.md` — upstream source map + translation rulebook + chapter/stub inventory
4. `tasks/reference/tests-and-gates.md` — gate chain, contract tests, proof harnesses, bulk-edit playbook
5. `tasks/reference/demo-chapter-inventory.md` — demo↔chapter map, header convention, util ledger

Updates: `architecture-overview.md`, `book-and-docs-pipeline.md`,
`design-decisions.md`, `notable-subsystems.md` (corrections + merges).

Cleanups: harvest+delete `tasks/codebase-overview.md` (fix 3 inbound pointers),
rewrite `tasks/README.md`, refresh `ports/openglsuperbiblev4/README.md` status,
fix root `README.md` texExpToPng section, CLAUDE.md defensive-copies +
slotting staleness, TODO.org R/T/S contradiction, colorutils orphan marker.

## Verification notes (claims corrected against source before writing)

- `#cayleygraph.py#` autosave: already gone from the tree — dropped from scope.
- Camera wiring: only the canary `chapt08/sphereworld` uses `_common`'s
  `bind_camera_inputs` (not 13 files — the other grep hits are local functions).
- Dead doc-region markers: 8, not 9 (`of paddle 1` IS referenced).
- `html_theme` set once in conf.py (not twice); test count 60 (not 63);
  101 port demo files (not 104) + `_common.py`/`_primitives.py`.
- All other headline claims verified: `.coeff_e_12` quotes, bare
  `bivector.dual()` return, gacalc pin 0.0.14 both places, `--python` install
  flag, ch12/ch16 double includes, empty ch21 "The Event Loop" heading,
  `[tool.pytest]` dead table, unused `slow` marker, no `.github/`.
