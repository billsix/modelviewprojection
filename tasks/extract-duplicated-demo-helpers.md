# Plan: extract duplicated demo helpers into a shared module

**Status:** in progress (2026-05-27) — `shading.py` (`_face_normal`,
`light_dir_ws`), `windowing.py` (`on_key`), and `clipping.py`
(`draw_in_square_viewport`) all extracted & committed (see Progress below).
Remaining: `shaderutils.py` / `set_mvp_uniforms` (deferred — demo22 variant) and
per-demo `handle_inputs` (separate, [`dedup-handle-inputs.md`](archive/2026/06/01/dedup-handle-inputs.md)).
**Type:** refactor of `src/modelviewprojection/demo*.py`, coordinated with the book.
**Approach (Bill's choice):** *teach-once-then-import* — the first chapter that
teaches a helper keeps its inline copy; from the next demo onward, import it from
a shared module, and update those later chapters' `literalinclude`s to show the
import instead of a redefinition.

## Progress
- **2026-05-27 — `shading.py` DONE (staged, not committed).** Created
  `src/modelviewprojection/shading.py` with the byte-identical
  `_face_normal` + `light_dir_ws`; removed the inline copies from `demo22`,
  `demo22a`, `demo23` (left a one-line breadcrumb comment at each site) and added
  the import. Verified: `ruff` clean, `py_compile` OK, `pytest` 46/46, functions
  import & return correct values. Zero book impact (these demos aren't in any
  chapter). **Bill still needs to run the three GL demos to confirm visually.**
- **2026-05-27 — `windowing.py` DONE (staged, not committed).** Created
  `src/modelviewprojection/windowing.py` with `import glfw` + the canonical
  `on_key` (escape-to-quit). Investigation confirmed all 30 `on_key` copies are
  escape-only (the 1 outlier, demo12, differed only in the param name
  `window`→`win`), and `on_key`'s *code* is **not** shown via `literalinclude`
  in any chapter (ch01 only mentions it in prose) — so **zero chapter edits**.
  Kept the inline def in `demo01` (ch01 teaches it there); replaced the def with
  the import in the **other 29 demos** (net +29/−203). Verified: only
  demo01+windowing define `on_key`; import in 29; `set_key_callback` still wired
  in all 30; `py_compile` clean on all; `pytest` 47/47. (5 remaining ruff errors
  in demo19e/demo21/demo24 are **pre-existing**, unrelated.) glfw runtime import
  not testable here (no glfw in container) → Bill's build/GL run confirms.
- **Deferred:** `shaderutils.py` / `set_mvp_uniforms` — demo22 is a variant
  (3-of-4 identical), the variant-reconciliation question Bill asked to handle
  later. Not touched.
- **2026-05-27 — `clipping.py` DONE (staged, not committed).** Created
  `clipping.py` with `draw_in_square_viewport(window)` — **parameterized on
  `window`** (the function read the module global, so it couldn't move unchanged).
  23 defs → 3: kept **demo03** inline (ch03 dissects it; updated its def+call to
  take/pass `window` so signatures stay consistent) and **demo19e** inline
  (intentional different background color); the other **21** (demo04–20, 19a–d,
  demo12) now import it and call `draw_in_square_viewport(window)`. Book reality:
  only **ch03** (teaches/dissects the def) and **ch04** (shows the call) reference
  it — *not* ch06/09/11/13/17 as earlier guessed — and both auto-update via
  `literalinclude` (no `.rst` edits), now showing the `(window)` signature/call.
  Verified: def only in clipping/demo03/demo19e; 21 imports; `py_compile` all;
  `pytest` 47/47; the 5 leftover ruff errors are pre-existing.
- **Deferred:** `shaderutils.py` / `set_mvp_uniforms` — demo22 is a variant
  (3-of-4 identical), the variant-reconciliation question Bill asked to handle
  later. Not touched. Per-demo `handle_inputs` dedup tracked separately in
  [`dedup-handle-inputs.md`](archive/2026/06/01/dedup-handle-inputs.md).
- **2026-06-01 — `axes.py` DONE (staged, not committed).** Created
  `src/modelviewprojection/axes.py` with `draw_unit_axes(scale: float = 1.0)`
  plus three private primitives (`_draw_solid_cylinder`, `_draw_solid_cone`,
  `_draw_solid_sphere`) ported from demo19a's local copies. Wraps the gizmo
  draw in `glPushAttrib(GL_POLYGON_BIT)` + `glPolygonMode(GL_FILL)` so the
  arrows render solid even when the surrounding scene uses wireframe.
  **demo19a** replaced its local helpers + def with the import (−104 lines).
  **demo19e** originally got the import too (to make its axes match 19a's),
  but Bill subsequently asked to drop the gizmos entirely from sphereworld
  (visually too busy with 30+ per-actor markers), so demo19e now has neither
  the import nor any `draw_unit_axes` calls.

## Context
This is teaching code, so *some* repetition is intentional (a student reads one
demo top-to-bottom). But a few helpers are duplicated verbatim a dozen-plus times
with no pedagogical payoff after their introduction — pure noise that also means
a bug fix must be applied N times. The clipping helper Bill named
(`draw_in_square_viewport`, introduced in demo03 to teach `glScissor`/`glViewport`)
is the prime example.

## Inventory (measured across all `demo*.py`, bodies normalized for whitespace)

| helper | copies | distinct variants | largest identical cluster | recommendation |
|--------|-------:|------------------:|--------------------------:|----------------|
| `on_key` | 30 | 2 | 29 | **EXTRACT** — 29/30 identical (escape-to-quit) |
| `draw_in_square_viewport` | 23 | 4 | 20 | **EXTRACT** after demo03 — 20/23 identical |
| `light_dir_ws` | 3 | 1 | 3 | **EXTRACT** — all identical |
| `_face_normal` | 2 | 1 | 2 | **EXTRACT** — all identical |
| `set_mvp_uniforms` | 4 | 2 | 3 | extract the 3 identical; check the outlier |
| `handle_inputs` | 21 | 18 | 3 | **KEEP** — varies per demo by design (teaching) |
| `handle_movement_of_paddles` | 6 | 4 | 3 | **KEEP / partial** — mostly varies |
| `make_vao` | 4 | 3 | 2 | mostly keep (evolves) |
| `draw_sphere` | 4 | 4 | 1 | **KEEP** — all different |
| `compile_shader_program` | 4 | 4 | 1 | **KEEP** — evolves per demo |
| `load_texture`, `_build_marker_cone/sphere`, `planar_shadow_matrix` | 2–3 | all distinct | 1 | KEEP |
| `draw_unit_axes` | ~~2~~ → 1 | ~~all distinct~~ → consolidated | n/a | **EXTRACTED** 2026-06-01 to `axes.py` — demo19a imports it; demo19e dropped the gizmo entirely per Bill |

Reproduce: the AST/normalized-hash script in this repo's session notes (groups
each top-level def across files by normalized body).

## The book-coupling constraint
Chapters pull these via `literalinclude` + `doc-region`. Book-referenced demos
are **demo01–demo21** (chNN → demoNN; ch20→demo20, ch21→demo21). The
**non-referenced** demos — `demo19a–e`, `demo22`, `demo22a`, `demo23`, `demo24` —
have no chapter, so they can import freely with zero book impact (do these first,
they're risk-free). For referenced demos, each switch from definition→import is
also a chapter edit.

## Design — per-concept modules (decided 2026-05-27)
One small module per *concept*, named for the idea it teaches, so a demo's import
line reads like a sentence and reinforces what's being reused. Each holds the
canonical (majority-cluster) version of its helper:

| New module (sibling of `mathutils.py`) | Helper(s) | Concept |
|---|---|---|
| `clipping.py` | `draw_in_square_viewport` | the `glScissor`/`glViewport` square-viewport lesson |
| `windowing.py` | `on_key` | escape-to-quit key handler |
| `shading.py` | `light_dir_ws`, `_face_normal` | lighting / face-normal geometry |
| `shaderutils.py` | `set_mvp_uniforms` | MVP uniform upload |

Naming follows Bill's existing convention (`mathutils.py`, `colorutils.py`,
`pyMatrixStack.py`) — plain `clipping.py` style chosen over `*utils` for the
concept-named ones; adjust if Bill prefers the `clippingutils.py` form. Imports
read e.g. `from modelviewprojection.clipping import draw_in_square_viewport`.

### Per-helper rollout (teach-once-then-import)
- **`draw_in_square_viewport` → `clipping.py`**: taught in **demo03 / ch03** (the
  clipping lesson) — keep the full inline definition there. From **demo04** on,
  `from modelviewprojection.clipping import draw_in_square_viewport`; wrap that
  import in a `doc-region` (e.g. `import clipping helper`) and point the
  `literalinclude` in **ch04, ch06, ch09, ch11, ch13, ch17** (the chapters that
  currently re-show the body) at the import line instead. Reconcile the 3
  non-identical variants to the canonical one first — diff them and confirm the
  difference is incidental, not pedagogical.
- **`on_key` → `windowing.py`**: keep inline in the first demo that defines it
  (demo01/02 era), import everywhere after; inspect the single outlier (1 of 30)
  before collapsing it.
- **`light_dir_ws`, `_face_normal` → `shading.py`** and **`set_mvp_uniforms` →
  `shaderutils.py`**: these live in the non-book-referenced demos (22/22a/23/24),
  so extract them first — zero book impact, proves the pattern out.

## Open questions for Bill (please confirm before any edits)
1. ~~Module shape~~ — **decided: per-concept modules** (`clipping.py`,
   `windowing.py`, `shading.py`, `shaderutils.py`). Confirm only the exact names
   (`clipping.py` vs `clippingutils.py`, etc.).
2. For `draw_in_square_viewport`, OK to show **`ch04+`** displaying just the
   `import` line (so the chapter says "same clipping helper as demo03")? That's
   the crux of teach-once-then-import.
3. Scope: curriculum demos only, or also fold the **ports** `_common.py` idea in?
   (Recommend: curriculum only here; ports are parked.)
4. Is the 1/30 `on_key` and the variant `draw_in_square_viewport`s an intentional
   difference, or just drift to be normalized?

## Verification
- After each extraction: `pytest` (build gate) and `ruff check` stay green;
  `python -c "import modelviewprojection.demoNN..."` or a syntax compile of each
  touched demo. The GL demos themselves need a display — Bill runs those.
- For book-referenced demos, Bill's `make html` confirms the updated
  `literalinclude`s resolve and the chapters still read correctly.
- Start with the **non-referenced demos** (19a–e, 22–24) to prove the module out
  with zero book risk, then do the referenced ones chapter-by-chapter.
</content>
