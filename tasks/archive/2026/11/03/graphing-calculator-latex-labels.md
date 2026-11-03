# Graphing calculators — LaTeX labels via texExpToPng billboards — DONE

**Status:** done (2026-11-03) — implemented and headless-verified (both graphers show white
typeset-LaTeX labels in-container where texExpToPng is on PATH). On-display legibility/placement is
the maintainer's pass.
**Completed:** 2026-11-03 (William Emerison Six <billsix@gmail.com>, with Claude Opus 4.8)
**Part of:** the graphing-calculator work — base graphers under
`src/modelviewprojection/graphingcalculator/`
(`tasks/archive/2026/11/03/graphing-calculator-2d-3d.md`).

## What was built

A shared TeX billboard label renderer and its use in both graphers:

- **`mvpvisualization/labels.py`** (`LabelRenderer`) + **`billboard.vert`** / **`billboard.frag`** —
  `texExpToPng` renders a LaTeX string to a PNG, which is uploaded as an RGBA texture and drawn as a
  camera-facing, constant-screen-size billboard (`clip.xy += offset * clip.w`, which works in both
  the 2D ortho and 3D perspective views). A two-layer cache (`latex -> (tex, w, h)` dict + on-disk
  sha1 PNG) avoids re-rendering. If `texExpToPng` is absent (`shutil.which` is None),
  `available` is False and every method no-ops. This reintroduces the proven technique that was
  built + display-verified in mvp (2026-06-14), then removed and relocated to multivariate-math
  (`github.com/billsix/multivariate-math` `src/crossproduct/_labels.py`); this copy is adapted to
  mvp conventions. mvp's GL toolkit had no texture pipeline before this — it is now the first.
- **grapher2d** — a `latex` field per `PlottedFunction`; captions each curve (anchored on the curve,
  right of center) plus the `x`/`y` axis names, as white billboards. Toggle: Controls ▸ Labels / `L`.
- **grapher3d** — a `latex` field per `Surface`; billboards the `x`/`y`/`z` axis-tip labels (domain
  x → world x, domain y → world z, height → world y) and the current surface's equation above the
  plot. Toggle: Controls ▸ Labels / `L`.

Durable billboard/texExpToPng lessons harvested to `tasks/reference/gl-and-imgui-gotchas.md` §9.

## Decisions (as built; alternatives logged in the proposal)

1. **Shared `mvpvisualization/labels.py`** (+ billboard shaders), reused by both graphers — not a
   per-grapher copy.
2. **2D:** one caption per curve + `x`/`y` axis names (tick-number labels deferred).
3. **LaTeX authored by hand** as a `latex` field on `PlottedFunction` / `Surface`.
4. **3D:** `x`/`y`/`z` axis-tip labels + the surface equation as a caption.
5. Proven defaults: `--size 600`, `--bg Transparent`, `height_px = 44`.

Two adaptations from the multivariate-math reference, both now in gotchas §9:
- **begin/end save+restore the caller's `GL_BLEND`/`GL_DEPTH_TEST` enable state** instead of forcing
  a fixed state — forcing `glDisable(GL_BLEND)` in `end()` broke grapher2d's line smoothing.
- **The fragment shader paints the glyph white using the PNG's alpha as a coverage mask**, because
  `texExpToPng`/`dvipng` in this image renders the formula black-on-transparent regardless of
  `--fg` (verified across three colour formats). Label colour is the shader's, not `--fg`.

## Verification

ruff-clean (80-col), ty-clean, annotation-checker clean (containerized gate, GATE_STATUS=0).
Rendered headless via `tools/verify_render.sh` (texExpToPng is on PATH in the image): grapher2d
shows white `\sin(x)`/`\cos(x)` captions + italic `x`/`y`; grapher3d shows white `x`/`y`/`z`
axis-tip labels + the `z=\tfrac{xy}{4}` equation caption (confirmed by orbiting the view). The
curve captions for the steep parabola/cubic sit above the default frame (their curves exit the top)
and the 3D equation caption anchor can want on-display tuning — both the maintainer's call.
