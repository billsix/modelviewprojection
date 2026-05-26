# Plan: extract duplicated demo helpers into a shared module

**Status:** planned (inventory + design done 2026-05-27; no code edits yet).
**Type:** refactor of `src/modelviewprojection/demo*.py`, coordinated with the book.
**Approach (Bill's choice):** *teach-once-then-import* — the first chapter that
teaches a helper keeps its inline copy; from the next demo onward, import it from
a shared module, and update those later chapters' `literalinclude`s to show the
import instead of a redefinition.

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
| `load_texture`, `_build_marker_cone/sphere`, `draw_unit_axes`, `planar_shadow_matrix` | 2–3 | all distinct | 1 | KEEP |

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
