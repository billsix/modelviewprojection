# Remove the crossproduct demo from mvp (it lives in multivariate-math now)

**Status:** DONE 2026-07-09 (Bill: "I approve the removal"). Deleted the
whole crossproduct layer: `mathdemos/` (demo + `_labels.py` + billboard
shaders — package removed entirely, nothing else lived there),
`notebooksrc/crossproduct.py` (standalone gacalc notebook — the material
lives in multivariate-math), `tests/test_crossproduct.py` (imported the
demo). Repo-wide grep: zero remaining references. **`ty check src` went
79 → 0** (better than the predicted 76). pytest 60 passed. Staged,
uncommitted. The two dependent task docs archived as superseded-by-mvm.
**Created:** 2026-07-08

## Goal (Bill, 2026-07-08)

The cross-product visualization work moved to the multivariate-math repo
(ported there 2026-07-08 with billboard labels + menubar, display-verified);
mvp's copy is now redundant. Remove it.

## What removal touches (survey — confirm scope before executing)

- **`src/modelviewprojection/mathdemos/crossproduct.py`** — the demo itself
  (1,317 lines). Deleting it also removes **76 of the 79** `ty check src`
  diagnostics tracked in tasks/src-ty-diagnostics-after-ty-bump.md, shrinking
  that task to 3 findings in nbplotutils/plotsforbook/notebooksrc.
- **`mathdemos/_labels.py` + `billboard.vert`/`billboard.frag`** — used only
  by the crossproduct demo (verify no other consumer). The improved copy
  (Pillow-10 fix, VAO save/restore) lives in multivariate-math.
- **`src/modelviewprojection/notebooksrc/crossproduct.py`** and
  **`tests/test_crossproduct.py`** — same question: delete or keep? (the
  notebook/test may cover math that predates the demo).
- **Task docs that die or change with it:**
  - `tasks/crossproduct-tex-billboard-labels.md` (in-progress; its remaining
    items are refinements to the demo being deleted) → archive as
    superseded-by-mvm.
  - `tasks/math-demos-section-crossproduct-and-proof.md` (proposed; its
    first demo WAS the crossproduct port) → re-scope or archive.
  - `tasks/backport-labels-fixes-from-mvm.md` → **deleted 2026-07-08 per
    Bill** (no backports; the demo is leaving).
- **What STAYS:** the texExpToPng build in the Dockerfile (the BOOK's
  inlinetex extension uses the binary — independent of the demo), and
  `pyMatrixStack` (used by mvpvisualization).

## Open questions for Bill

- [ ] Delete `notebooksrc/crossproduct.py` + `tests/test_crossproduct.py`
      too, or keep the math/notebook layer and remove only the GL demo?
- [ ] `math-demos-section-crossproduct-and-proof.md`: archive outright, or
      re-scope to "math demos section" with a different first demo?
