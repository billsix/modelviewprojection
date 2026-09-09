# Extract duplicated demo helpers into shared `util/` modules

**Status:** **DONE 2026-09-09.** All five helpers are extracted and live in
`src/modelviewprojection/util/`. The last one, `set_mvp_uniforms` → `shaderutils.py`, was
done today; `shading.py`, `windowing.py`, `clipping.py` and `axes.py` landed 2026-05/06 and
have been committed since the 2026-06-03 restructure
(`tasks/archive/2026/06/03/restructure-directories.md`).
**Priority:** 5
**Difficulty:** 5

## BLUF

A handful of helpers were duplicated verbatim a dozen-plus times across the teaching demos
with no pedagogical payoff after their introduction — noise, and a bug fix that had to be
applied N times. Each moved to a per-concept module under `util/`, on the maintainer's
**teach-once-then-import** rule: the chapter that *teaches* a helper keeps its inline copy;
every demo after that imports it. Done = five modules extracted, the demos importing them,
and no chapter changed except where the `literalinclude` follows the source automatically.

## What the durable record is, and where it lives

This doc is the work log. The knowledge outlived it and was harvested:

- **The adoption ledger** — which demo introduced each helper, who consumes it, who keeps a
  deliberate private copy — `tasks/reference/demo-chapter-inventory.md` §4.
- **What was measured and deliberately NOT extracted** (`handle_inputs` at 21 copies / 18
  variants, `make_vao`, `draw_sphere`, `compile_shader_program`, …) — same doc, the
  "Measured, and deliberately NOT extracted" table. Read that before re-proposing a DRY pass.
- **Why the camera dedup worked and `handle_inputs` didn't** —
  `tasks/reference/design-decisions.md`.
- **Why the repetition is deliberate in the first place** —
  `tasks/reference/library-not-framework-authorship-style.md` ("repetition with incremental
  complexity").

## Decisions, and why

- **Teach-once-then-import (maintainer's choice).** The first chapter that teaches a helper
  keeps the full inline definition; later demos import it. This is why `demo03` still defines
  `draw_in_square_viewport` and `demo01` still defines `on_key`.
- **Per-concept modules, named for the idea** — `clipping.py`, `windowing.py`, `shading.py`,
  `shaderutils.py`, `axes.py` — not one `helpers.py`, so a demo's import line reads like a
  sentence and reinforces what is being reused. Plain names over `*utils` for the
  concept-named ones, matching `matrix_stack.py`.
- **Non-chapter demos first** (19a–e, 22–24) to prove each module out at zero book risk,
  then the chaptered ones.
- **Curriculum only.** The ports tree got its own `_common.py`; no code is shared between
  the curriculum and `ports/`.
- **A helper that reads a module global cannot move unchanged** — it gets parameterized.
  `draw_in_square_viewport` gained `window`; `set_mvp_uniforms` gained `u_mvp, u_model`.

## Rollout

| helper → module | when | notes |
|---|---|---|
| `on_key` → `windowing.py` | 2026-05-27 | 30 copies, 29 identical (demo12's outlier differed only in a parameter name). demo01 keeps its inline copy for ch01. `on_key`'s body is in no `literalinclude`, so zero chapter edits. |
| `draw_in_square_viewport` → `clipping.py` | 2026-05-27 | 23 defs → 3. Parameterized on `window` (it had read the module global). demo03 keeps an annotated copy; demo19e keeps its own (different background colour). Only ch03 and ch04 reference it, and both auto-update through `literalinclude`. |
| `_face_normal`, `light_dir_ws` → `shading.py` | 2026-05-27 | demo22/22a/23. No chapters. |
| `draw_unit_axes` → `axes.py` | 2026-06-01 | demo19a only (−104 lines), with the gizmo wrapped in `glPushAttrib(GL_POLYGON_BIT)` so the arrows stay solid in wireframe scenes. demo19e initially got it too, then dropped gizmos entirely — too busy with 30+ per-actor markers. |
| `set_mvp_uniforms` → `shaderutils.py` | 2026-09-09 | See below. |

## The last item: `set_mvp_uniforms` (2026-09-09)

Deferred since May because demo22 was a fourth, variant copy. **Re-measured 2026-09-08:
three copies, not four** — demo22 no longer defines it — and the three (`demo22a`, `demo23`,
`demo24`) are byte-identical, so the variant-reconciliation question that had deferred this
no longer exists. None of those three has a book chapter and none has a `doc-region` near
the function, so the extraction carried zero book risk.

The function read two module globals, `u_mvp` and `u_model` — the uniform locations each
demo looks up beside the program it compiles — so it could not move unchanged. It is now
`set_mvp_uniforms(u_mvp, u_model)`, and the **14 call sites** (4 + 4 + 6) pass them. Each
demo keeps a one-line breadcrumb comment where the definition used to be, matching the
`_face_normal` sites.

### Verification (2026-09-09)

- `make format` (ruff + ty over `src`, `tests`, `ports`, `assignments`) — clean.
- `make check-regions` — the book's doc-region anchors all resolve.
- `make test` — 104 passed.
- **The three demos still render**, headlessly via `tools/verify_render.sh` under Xvfb —
  and, more to the point, render the *same*: the pre-change file was checked out and
  re-rendered for each, and the colour histograms match. demo22a and demo23 match exactly;
  demo24's distinct-colour count wobbles by a couple of colours **in the baseline too**
  (8770 / 8772 / 8774 across three runs of the unmodified file), so that demo is
  frame-nondeterministic and its top-six colour counts, which are identical, are the signal.
  Rendering alone would not have proved this change correct — a wrong uniform location still
  draws *something* — which is why the before/after comparison was worth doing.
- Not checked: `make html`. This image was built `BUILD_DOCS=0`. No published region's text
  changed and `check-regions` is green, so the anchor half is covered; the build is Bill's.
