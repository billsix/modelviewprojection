# Graphing calculators — LaTeX labels via texExpToPng billboards

**Status:** proposed — needs go-ahead
**Priority:** 6
**Difficulty:** 5
**Started:** 2026-11-03 (William Emerison Six <billsix@gmail.com>)
**Part of:** the graphing-calculator work — base graphers at
`src/modelviewprojection/graphingcalculator/` (done + merged;
`tasks/archive/2026/11/03/graphing-calculator-2d-3d.md`).
**Related:** `tasks/grapher2d-basis-vector-view.md` — if both land, the e₁/e₂ arrows get `e_1`/`e_2`
LaTeX labels from this machinery.

## BLUF

Add rendered-LaTeX labels to `grapher2d.py` and `grapher3d.py`: generate each label with
**texExpToPng** (LaTeX → PNG), upload it as an RGBA texture, and draw it as a **camera-facing
billboard** anchored at a world point. "Done" = the graphers can caption their functions and axes
with real typeset math (e.g. `\sin(x)`, `x`, `y`, `z = x y / 4`), constant screen size at any
zoom/orbit, degrading gracefully (no labels) if the `texExpToPng` binary is absent.

## Context (read first)

- The graphers today draw only geometry — no text. `grapher2d` has a `PlottedFunction.label`
  **plain string** (`"sin(x)"`) that is not displayed; `grapher3d` has `Surface` labels likewise
  unused for drawing. Both are GL 3.3 core, built on `mvpvisualization.cayley_gl` + `_pipeline`.
- **This exact technique already shipped in mvp and was display-verified, then removed.** The
  cross-product demo built runtime `texExpToPng` LaTeX labels → RGBA texture → camera-facing
  billboard quads; **Bill verified it on a real display 2026-06-14**
  (`tasks/archive/2026/07/09/crossproduct-tex-billboard-labels.md`). The whole `mathdemos/` package
  — including `_labels.py` and `billboard.vert`/`billboard.frag` — was then **deleted** and the
  work **relocated to the multivariate-math repo**
  (`tasks/archive/2026/07/09/remove-crossproduct-demo.md`). So the design is proven; the code is
  just no longer in this tree. This task **re-introduces an adapted copy** for the graphers.
- **mvp's current GL toolkit has ZERO texture capability.** `mvpvisualization/_pipeline.py` and
  `cayley_gl.py` only build solid-colour / per-vertex-colour pipelines — no `sampler2D`, no
  `glTexImage2D`, no UV attribute, no billboard. Texture support here is **net-new plumbing** (the
  reason this is Difficulty 5 despite a proven reference).
- **texExpToPng is already in the image.** `Dockerfile` clones + builds
  `github.com/billsix/tex-expression-to-png` (a C binary; needed by the book's Sphinx `inlinetex`
  extension), so `texExpToPng`, `latex` and `dvipng` are on `PATH` in-container. On a bare host
  they may be absent → graceful degradation.

## The reference implementation to adapt

multivariate-math (`github.com/billsix/multivariate-math`) `src/crossproduct/_labels.py` +
`billboard.vert` + `billboard.frag` — the improved copy of the removed mvp code (Pillow-10 fix,
VAO save/restore). Adapt it to mvp conventions (keyword-only `shader_dir`, GL constants typed
`GLenum` not `int`, annotate every binding, 80-col). The technique:

- **`LabelRenderer(shader_dir, *, dpi=600, fg="rgb 1 1 1")`** holds a billboard shader program, a
  dynamic VBO/VAO (7 floats/vertex: `center`(3) + NDC `offset`(2) + `uv`(2), 6 verts/quad), a temp
  cache dir, and a `latex -> (tex_id, w, h)` cache.
- **Per frame:** `begin(view_M, proj_M, (w,h))` (uploads V/P with `GL_TRUE` transpose, enables
  `SRC_ALPHA`/`ONE_MINUS_SRC_ALPHA` blend, **disables depth test**, saves the caller's VAO) →
  `draw(latex, center_world_xyz, *, height_px=44)` per label → `end()` (restores depth test + the
  caller's VAO).
- **`draw`** CPU-projects the world center for a behind-camera cull, computes NDC half-extents from
  `height_px` and the glyph aspect ratio, writes 6 vertices (all sharing the world `center`, each
  with its NDC corner `offset` + `uv`), binds the texture, `glDrawArrays(GL_TRIANGLES, 0, 6)`.
- **Billboard vertex shader** (the whole trick): `clip = pMatrix*vMatrix*vec4(center,1);
  clip.xy += offset*clip.w; gl_Position = clip;` — the NDC offset × `w` survives the perspective
  divide as a **constant screen size**, and works unchanged in **ortho (w=1, the 2D grapher)** and
  **perspective (the 3D grapher)**. Fragment shader just samples the RGBA texture.
- **Texture:** PIL `Image.open(png).convert("RGBA")`, **flip top-bottom** (PIL is top-left origin,
  GL is bottom-left), `glTexImage2D(..., GL_RGBA8, ..., GL_RGBA, GL_UNSIGNED_BYTE, data)`, LINEAR,
  CLAMP_TO_EDGE. (mvp alt refs if PIL is unwanted: `demos/demo24/demo24.py` `load_texture` uses
  imageio.)
- **Caching:** in-memory `latex -> (tex,w,h)` dict (first hit = subprocess + upload, after = dict
  lookup); on-disk PNG named `sha1(f"{latex}|{dpi}|{fg}")[:16].png`. A generation failure caches
  `None` so it is not retried every frame.
- **Graceful degradation:** `TEXEXP = shutil.which("texExpToPng")`; if `None`, `available` is False
  and the whole renderer no-ops.

## texExpToPng interface (verified against the C source)

CLI (no Python API — shell out to the binary): `--exp/-e <latex>`, `--file/-f <path>`, `--size/-s
<DPI>` (**required**; it's DPI passed to `dvipng -D`, not pixels), `--output/-o <png>`
(**required**), `--bg/-b <color>` (e.g. `Transparent`), `--fg/-g <color>` (e.g. `"rgb 1 1 1"`).
The proven settings: `--exp "$<latex>$" --size 600 --fg "rgb 1 1 1" --bg Transparent --output
<png>`.

> **Gotcha — it writes `formula.tex`/`formula.dvi` into the *current working directory*, not a
> temp dir.** Run it with `cwd=<scratch dir>` (the `LabelRenderer`'s temp cache dir). On a `latex`
> failure it prints only a one-line error; the real diagnostic is `formula.log` left in that dir.

## Plan (draft)

- [ ] **`mvpvisualization/labels.py`** — an adapted `LabelRenderer` (from the multivariate-math
      copy), plus `billboard.vert` / `billboard.frag` beside it. Shared module (both graphers use
      it), consistent with the "reuse cayley_gl/_pipeline" decision. (See open question 1 on
      placement.)
- [ ] Wire into **grapher2d**: label each plotted curve with its LaTeX (and optionally the axes).
      Anchor each label at a world point on/near its curve; ortho `w=1` so the billboard is a plain
      constant-size screen quad. Needs a `latex` field on `PlottedFunction` (open question 3).
- [ ] Wire into **grapher3d**: label the x/y/z axes at their tips and/or the current surface's
      equation; billboard anchored in world space, constant size as you orbit.
- [ ] Draw labels **last**, after the depth-clear / solids, with depth test off (per the renderer's
      `begin`/`end`), so they never z-fight the geometry (same family as
      `tasks/reference/gl-and-imgui-gotchas.md` §8).
- [ ] A Controls-menu toggle to show/hide labels.
- [ ] Verify headless via `tools/verify_render.sh` (labels appear in-container where texExpToPng is
      on PATH); confirm graceful no-op when the binary is absent. Final look is Bill's on-display
      pass (text legibility, placement, orbit-stability).
- [ ] Harvest the reusable billboard/texture lesson into `tasks/reference/gl-and-imgui-gotchas.md`
      (mvp regained a textured pipeline) on completion.

## Decisions (batch go-ahead 2026-11-03, William Emerison Six <billsix@gmail.com>)

Options are logged under "Open questions" below; chosen for this pass:
1. **Shared `mvpvisualization/labels.py`** (+ `billboard.vert` / `billboard.frag` beside it),
   reused by both graphers.
2. **2D labels:** one caption per curve + `x` / `y` axis names (tick numbers deferred).
3. **LaTeX authored by hand** as a `latex` field on `PlottedFunction` / `Surface`.
4. **3D labels:** `x` / `y` / `z` axis-tip labels + the current surface's equation as a caption.
5. **Proven defaults:** `--size 600`, `--fg "rgb 1 1 1"`, `--bg Transparent`, `height_px ≈ 44`.

## Open questions

1. **Where does the label code live?** A shared `mvpvisualization/labels.py` (both graphers + any
   future demo reuse it; adds texture capability to the toolkit) — recommended — or a self-contained
   copy inside each grapher (house style for programs, but duplicates ~250 lines and two shaders)?
   Recommendation: shared module, mirroring how the graphers already reuse `cayley_gl`/`_pipeline`.
2. **What gets labelled, 2D?** The function expressions (one caption per curve), the axis names
   (`x`, `y`), the tick numbers (many labels, re-rendered as spacing changes — heavier), or a
   screen-space legend in a corner? Recommendation: start with one caption per curve + `x`/`y` axis
   names; leave tick numbers for a follow-up (they're the expensive, many-label case).
3. **Where do the LaTeX strings come from?** Add a `latex: str` field to `PlottedFunction` /
   `Surface` authored alongside the callable (e.g. `r"\sin(x)"`), since the function is Python and
   can't be auto-transcribed to LaTeX. OK to author them by hand in source (consistent with
   "functions are authored, not parsed")?
4. **3D label targets.** Axis tips (`x`/`y`/`z`) only, or also the current surface's equation (e.g.
   `z = x y / 4`) somewhere in view? Recommendation: axis tips first, surface equation as a corner
   caption if wanted.
5. **DPI / size.** Keep the proven `--size 600`, white `--fg`, `Transparent --bg`, `height_px≈44`?
   (These are display-verified defaults; only revisit if labels look too soft/sharp.)
