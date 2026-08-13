# Adopt unsuffixed gacalc types (Vector2 → g2.Vector, …)

**Status:** CODE DONE, verified in-sandbox (2026-08-13). Batches 1–6 below complete; batch 7
(book teaching-prose) awaits Bill's decision; the full containerized `make test` gate is the
only remaining verification (in-sandbox proof is strong — see below).

**Done + verified in-sandbox against gacalc 0.0.16 (installed from PyPI):**
- **Code (64 .py):** 58 via `tasks/adhoc/.../migrate_0016.py` (direct-import + facade split +
  module-qualify) + `mathutils.py` via `migrate_mathutils.py` (4-context: code / doctest-input /
  doctest-repr-output / prose-example). Both codemods idempotent (2nd run = no-op).
- **De-facade:** the 12 SuperBible ports now import `Vector` straight from `gacalc.g3`; mathutils
  re-exports **no** gacalc type (finishes `tasks/defacade-mathutils-gacalc-reexports.md`).
- **Book markers (batch 5):** ch05×2 / ch06×6 / ch14×2 renamed to the **real** 0.0.16 names
  (`Vector declaration`, `Vector __add__/__sub__/__mul__ method`), verified against the 0.0.16
  sdist's baked `g2.py`/`g3.py`; all 10 extract **non-empty** (no silent-empty trap).
- **Dockerfile `ARG GACALC_VERSION` → 0.0.16**; `requirements.txt` already `==0.0.16`.
- **Gates (sandbox venv, gacalc 0.0.16):** ruff clean + `format --check` idempotent; ty clean on
  mathutils + qualify tests; 72 tests pass (16 mathutils doctests, test_mathutils + unpacking = 25,
  cayley/focus = 31); E501 clean; zero leftover suffixed gacalc types in `.py`.

**Remaining:** batch 7 (below) — Bill's call; and the containerized `make test` + `make html`
gate (re-confirms; the change is pure type-renaming, and the one container-only risk — marker
resolution — is already proven).
**Priority:** 4
**Difficulty:** 5
**Created:** 2026-08-13

**Decision (2026-08-13): direct-import / module-qualify, NOT facade-alias.** A facade-alias
approach (`from gacalc.g2 import Vector as Vector2`, keeping mvp's suffixed names) was considered
and **rejected** — it re-adds the suffix locally and fights gacalc's "module is the namespace"
design, and mathutils is already 96% not-a-facade (only `Vector3` leaks, to 12 ports — see below).
The half-written `tasks/adhoc/adopt-unsuffixed-gacalc-graded-types/alias_imports.py` is **dead**;
remove it when this task runs. As part of this pass, finish the de-facade
(`tasks/defacade-mathutils-gacalc-reexports.md`): make the 12 straggler ports import their gacalc
`Vector` directly so mathutils re-exports **no** gacalc type. `mathutils.py` itself switches to
`from gacalc.g3 import Vector` / `from gacalc.g2 import Vector` internally.

## Context

gacalc (`github.com/billsix/geometricalgebra`) is dropping the dimension suffix from **all**
its generated types — `Vector2`/`Vector3` → `Vector`, likewise `Bivector`/`Trivector`/`Rotor`/
`Scalar`, **and the full class `G2`/`G3` → `G`** (its `tasks/drop-graded-type-dimension-suffixes.md`).
**API-breaking**, shipping in gacalc **0.0.16**. The idiom becomes **module-qualified**:
`import gacalc.g2 as g2` → `g2.Vector`, `g2.G`. Adopt against the new release (bump mvp's gacalc
dependency version first; gated on the release, as with the frozen-types / `plane_rotation`
adoptions). gacalc's reprs will also module-qualify (`g2.Vector(coeff_e_1=…, …)`), so any mvp
doctest showing a gacalc repr updates to that form.

## Scope (2026-08-13 scan of tracked files)

mvp's OWN code uses only **`Vector2` (42 files) and `Vector3` (45 files)** — **no** other graded
types and **no** full classes (`G1`/`G2`/`G3`/`Gn`: 0 files), so the `G` rename doesn't touch
mvp. Categories: ~13 `book/docs/*.rst`; the Code-the-Classics + OpenGL-SuperBible ports;
`src/modelviewprojection/{mathutils.py, pgzero_gl/geometry.py, cayley/cayleyscene.py,
demos/demo05-08.py, notebooksrc/plot2d.py}`; `tests/`. **NOT `book/docs/_gacalc_src/`** — that
is an auto-vendored copy of gacalc (regenerated at build by `entrypoint/entrypoint.sh` + the
Makefile; gitignored, a `git clean` removes it) and updates itself against the new gacalc.

## Chunk 1 — the collision: module-qualify, don't split (14 files use both dims)

`book/docs/{ch02,ch04,ch05,ch14,ch16,ch20,glossary,perspective}.rst`,
`ports/codetheclassics/vol2/leadingedge/leadingedge.py`,
`src/modelviewprojection/{mathutils.py, notebooksrc/plot2d.py, pgzero_gl/geometry.py}`,
`tests/{test_gl_vector_unpacking.py, test_mathutils.py}`.

**Assessed (2026-08-13): these can't be split cleanly, and shouldn't be.** The mixing is
intrinsic — `mathutils.py` (V2=27, V3=81) is the shared math hub the whole project imports and
re-exports; `leadingedge.py` (17/40) is one game spanning screen-2D and world-3D; the book
chapters teach both dims. Splitting would fragment cohesive modules to dodge a name clash.

**Fix: module-qualify** — `import gacalc.g2 as g2, gacalc.g3 as g3` → `g2.Vector`, `g3.Vector`,
`g3.Bivector`. Reads well, no restructuring, matches gacalc's "module is the namespace" design.
Do **not** alias (`from gacalc.g2 import Vector as Vector2`) — it re-adds the suffix locally and
fights the whole point. Single-dimension files just switch to `g2.Vector` (or `g3.Vector`).
Notes: `mathutils.py` **re-exports** the vector (`from modelviewprojection.mathutils import
Vector3` in several files) — pick the re-export name and update its consumers; files importing
module constants (`from gacalc.g2 import Vector2, e_1, e_2`) keep `e_1` etc.

## Chunk 2 — book `literalinclude` doc-region markers (build-breaking if missed)

mvp's book pulls gacalc source slices **by suffixed doc-region marker name** — **10 references**:
`ch05.rst` (×2), `ch06.rst` (×6), `ch14.rst` (×2), e.g.:

    :start-after: doc-region-begin Vector2 __add__ method
    :start-after: doc-region-begin Vector3 declaration

gacalc renames those markers (`Vector2 __add__ method` → `Vector __add__ method`). A
`literalinclude` whose anchor no longer matches produces **empty output with no error** (silent
failure), so all 10 must update in the same change. Re-grep at implementation time
(`book/docs/*.rst` for `doc-region-(begin|end) (Vector|Bivector|Rotor|Scalar|G)[123]`) since the
count can drift.

## Chunk 3 — .gitignore tidy (do while here; recommended)

Two small gaps noticed 2026-08-13 (neither urgent):
- `output/` has only `output/.keep` tracked but no ignore rule for its contents — add
  `output/*` + `!output/.keep` if the book build writes artifacts there (mirrors gacalc).
- `book/docs/*.ipynb` is non-recursive — a generated notebook in a `book/docs/notebooks/`
  subdir wouldn't be caught; `book/docs/**/*.ipynb` is future-proof.

## Verify / gates

- `make test` and the book build after — **confirm the book's gacalc `literalinclude`s render
  non-empty** (the silent-empty trap).
- Doctests showing a gacalc repr now print the module-qualified form (`g2.Vector(…)`).
