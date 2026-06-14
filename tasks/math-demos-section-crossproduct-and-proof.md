# Math demos section + cross-product demo + its proof

**Status:** proposed — needs go-ahead. Plan only; nothing built yet. Written
2026-06-14 from a read of `multivariate-math/src/crossproduct/` and
`multivariate-math/proofs/crossproduct.tex`.

## Goal

Stand up a **general "math demos" section** in mvp, structured like
`src/modelviewprojection/mvpvisualization/` — i.e. built on the **Cayley-graph**
abstraction (`cayleygraph.py` + `cayleyscene.py`) the book already teaches — so
future math demos drop in with a consistent shape. The first demo is the
**cross product** (porting the multivariate-math animation), and its **LaTeX
proof** gets ported into the book in a new derivations section. Cross product is
the seed; the structure is the point (other math demos should fit even if they
aren't in any repo yet).

## What's in the source (multivariate-math)

**Demo — `src/crossproduct/` (~1100 LOC + assets):**
- `crossproduct.py` — glfw + **`imgui`** (not imgui_bundle) + PyOpenGL animation.
  Drives the derivation with a 12-member `StepNumber` enum (`beginning`,
  `rotate_z`, `rotate_y`, `rotate_x`, `show_triangle`, `project_onto_y`,
  `rotate_to_z`, `undo_rotate_x/y/z`, `scale_by_mag_a`, `show_plane`) plus a
  ~40-field `Globals` dataclass of `do_*` / `draw_*_relative_coordinates` flags,
  hand-toggled per step. imgui panels: **Cross Product** (per-step description via
  `match` on `StepNumber`), **Input Vectors** (`input_float3` for a, b + swap),
  **Camera** (auto-rotate, view-down-axis buttons, ortho toggle), **Time**
  (autoplay, restart, seconds-per-operation).
- `renderer.py` — its own harness: `compile_shader(vert,frag,geom)`,
  `do_draw_lines`, `do_draw_vector`, `do_draw_axis`, `do_draw_image`, `Camera`,
  `Vector`. **Duplicates** what mvp's `mvpvisualization/_pipeline.py` already does.
- `pyMatrixStack.py` — its **own** copy (mvp has `src/modelviewprojection/pyMatrixStack.py`).
- shaders: `lines.{vert,geom,frag}` (thick lines), `image.{vert,frag}` (textured
  billboards), and `images/` = `a/aprime/aprimeprime/b/bprimeprime/bprimeprimeprime/x/y/z.png`
  — the vector *labels* (a, a′, a″, b, …, x, y, z) drawn as textures in 3-space.

**Proof — `proofs/crossproduct.tex` (449 lines):** an `article` with custom
`problem`/`proof`/`theorem`/`lemma` environments and heavy `flalign`. It derives
a×b in exactly the demo's language: define `f_a^{zx}`, compose `f_{a'}^x ∘ f_a^{zx}`
to get `a''`, transform `b''`, apply `f_{b''}^{xy}`, project, undo the rotations,
scale by |a|. **The functions in the proof are the edges of the Cayley graph.**
(Sibling proofs `quaternions.tex`, `multivariatebasics.tex` exist — future
candidates for the same book section, out of scope here.)

## Target structure in mvp

mvp already has the machinery this needs, in `mvpvisualization/`:
- `cayleygraph.py` — immutable DAG; nodes = coordinate **spaces** (per-demo Enum),
  edges = sequences of interpolable `InvertibleFunction`s; `path()` composes /
  auto-inverts. Pure data/math, no GL, unit-testable.
- `cayleyscene.py` — turns a graph + declarative scene into an **animation**: a
  timeline, per-frame object transforms, the world→camera inverse, visibility, and
  the two imgui trees — *derived from the one graph, no hand-kept parallel state.*
- `cayley_gl.py` — the GL shell; `_pipeline.py` — shared procedural pipeline +
  shaders (`per_vertex_color.vert`, `thick_lines.geom`, `uniform_color.vert`,
  `project_*.glsl`).

**Proposed layout** (mirrors `mvpvisualization/`):
```
src/modelviewprojection/mathdemos/
    __init__.py
    crossproduct.py          # the demo: declares a CayleyGraph + scene, run by path
    crossproduct.vert/.geom  # only if it needs shaders beyond the shared set
    images/                  # a.png … z.png label textures (or render text instead)
```

### Design decision (needs Bill): where does the shared Cayley machinery live?

`cayleygraph.py` / `cayleyscene.py` are general (pure math), but currently sit in
`mvpvisualization/`. Options:
1. **Import across packages** — `mathdemos/` imports
   `from modelviewprojection.mvpvisualization import cayleygraph, cayleyscene`.
   Zero churn; slightly odd dependency direction (math demo → mvp-viz).
2. **Promote to a neutral home** — move `cayleygraph.py`/`cayleyscene.py` (and the
   reusable bits of `_pipeline.py`) to e.g. `src/modelviewprojection/cayley/` (or
   `util/`), and have *both* `mvpvisualization/` and `mathdemos/` import from there.
   Cleaner conceptually; touches existing imports + ch10/17/19 references.

Recommend **2** if the math-demos section is meant to grow; **1** for a quick first
demo. Decide before Phase 1.

## Phase 1 — scaffold the section

- Create `mathdemos/` package + its `__init__.py`; resolve the shared-machinery
  decision above.
- Add an image/billboard pipeline if keeping the `.png` labels: mvp's `_pipeline.py`
  is line/triangle oriented; the source's `image.{vert,frag}` + `do_draw_image`
  would need porting (or replace label textures with rendered text). Flag which.

## Phase 2 — port the cross-product demo as a Cayley scene

The real work is **re-expressing the hand-rolled state machine as a graph**, not a
line-by-line translation:
- **Nodes** = the coordinate frames the derivation passes through (natural basis →
  a-aligned frame after `f_a^{zx}` → after `f_{a'}^x` → b″ frame → …). **Edges** =
  the proof's `InvertibleFunction`s (`rotate_x/y/z`, `compose`, `inverse` from
  `mathutils`). The 12 `StepNumber` steps become the scene **timeline** over the
  graph's edge-substeps; the ~40 `Globals.do_*/draw_*` flags collapse into the
  scene's derived visibility/animation (the whole reason to use `cayleyscene`).
- **Math:** replace numpy/its vectors with mvp's **gacalc-based** `Vector3` +
  `InvertibleFunction` (`mathutils`). This is the natural representation — the proof
  is already in this language.
- **Rendering:** drop the vendored `renderer.py` + `pyMatrixStack.py`; use mvp's
  `pyMatrixStack.py`, `_pipeline.py`, and `mvpvisualization` shaders. Reuse the
  cylinder/thick-line visual style.
- **imgui:** port the four panels to **`imgui_bundle`** (mvp's binding; source uses
  `imgui`). Every adjustable parameter stays an imgui widget (input a/b, camera,
  autoplay/seconds-per-op, ortho, axis highlights).
- **Run by path** like the mvpvisualization demos
  (`python src/modelviewprojection/mathdemos/crossproduct.py`); part of the
  installed package. **No absolute paths** — load shaders/images via env var +
  sibling-walk + fallback (the ports convention).
- Add a `tests/` data-only test for the graph (the cross-product result for known
  a, b) — `cayleygraph` is unit-testable headless; rendering stays Bill's to verify.

## Phase 3 — port the proof into the book

- New book section for derivations. The toctree (`book/docs/index.rst`) already
  carries non-chapter sections (`mathhomework1`, `perspective`, `miscellany`), so
  add e.g. `derivations.rst` (or `crossproductderivation.rst`) as an appendix-style
  entry. Cross-link it from the cross-product demo and from the relevant chapter on
  composition.
- Convert `crossproduct.tex` → Sphinx: the custom `problem`/`proof`/`theorem`
  environments and `flalign` must map to the book's math tooling (the
  `math-dollar` / inline-tex extensions already in `conf.py`; see the done
  `archive/.../sphinx-*-inlinetex` work). This is the fiddly part — budget for it.
- Keep the proof's notation (`f_a^{zx}` etc.) consistent with the demo's edge names
  and the book's Cayley-graph vocabulary so proof ↔ demo read as one thing.

## Conventions to honor

- imgui widgets for every parameter; keyboard only as accelerator.
- No hardcoded absolute paths in the demo (env var + sibling-walk + sandbox fallback).
- gacalc `Vector3` / `InvertibleFunction` for the math; mvp `pyMatrixStack` + the
  shared pipeline/shaders for rendering; don't re-vendor `renderer.py`/`pyMatrixStack.py`.
- Build/package locally; Bill verifies anything needing a display.

## Future (not this task)
- Same section: `quaternions.tex`, `multivariatebasics.tex`, and further math demos
  (each a Cayley scene under `mathdemos/`).
