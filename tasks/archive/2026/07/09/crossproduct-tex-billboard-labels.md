# Cross-product demo: TeX billboard labels for the vectors

> **ARCHIVED 2026-07-09, superseded by multivariate-math:** mvp's
> crossproduct demo was removed (Bill approved; see
> `remove-crossproduct-demo.md` in this archive dir). The demo, labels
> infra, and proof work continue in the multivariate-math repo.


**Status:** in-progress — **core functionality VERIFIED WORKING by Bill on a real
display (2026-06-14)**: runtime texExpToPng generation -> RGBA texture -> camera-facing
billboard, drawn per step, all good. Remaining is **how the labels are USED** —
content/placement/visibility refinements Bill wants (TBD, his call); the rendering
infrastructure itself is done. Annotate the demo's vectors with LaTeX labels rendered
via `texExpToPng`, drawn as camera-facing billboards.

**Open follow-ups (separate from the rendering infra, which works):**
- Usage/content tweaks Bill mentioned (exact labels, placement, when each shows) —
  awaiting his specifics.
- `imgui-bundle` pin: Bill hit `undefined symbol: glfwGetX11Window` from a drifted
  bundled glfw; the working wheel is **1.92.801**. Consider pinning
  `imgui-bundle==1.92.801` in `requirements.txt` so a clean `make image` is
  reproducible. (Not the label code's fault — it's `_pipeline.py`'s imgui import.)

## Decisions LOCKED 2026-06-14 (final round)

> **Update 2026-07-08 (tasks/unvendor-texexptopng.md):** the vendored-copy
> mechanics below are superseded — the Dockerfile now builds texExpToPng from
> a **SHA-pinned git clone** of `billsix/tex-expression-to-png` (pinned
> `fbbd9a3f…`, byte-identical to what the vendored copy held, `--bg/--fg`
> included). Still under `BUILD_DOCS`, still `/usr/local/bin/texExpToPng`,
> graceful degradation unchanged. The vendored dir is deleted.

- **texExpToPng availability: BUILD IT INTO THE MVP IMAGE, under `BUILD_DOCS`.**
  Inside the existing `BUILD_DOCS` block (which already installs TeX Live +
  meson/glib2-devel), build texExpToPng -> `/usr/local/bin/texExpToPng`.
  Gated on `BUILD_DOCS` (not a new flag) because that is exactly when
  latex+dvipng are present; the demo's `shutil.which("texExpToPng")` check
  finds it. Lean builds (`BUILD_DOCS=0`) / Win/Mac: binary absent -> demo
  skips labels (graceful degradation).
- **Color/DPI: white text, 600 DPI.** `texExpToPng --fg "rgb 1 1 1" --bg Transparent
  --size 600`.

## Label set + per-step visibility (PROPOSED — Bill, please eyeball)

Labels are drawn at each item's tip. `||.||` = magnitude, `theta` = angle(a,b).
The a/b arrows keep their label but its TEXT advances with the stage:

| label LaTeX | on | shown when |
|---|---|---|
| `e_1` `e_2` `e_3` | axis tips | always (while natural basis drawn) |
| `\vec a` | a-arrow tip | beginning |
| `\vec a' = R_z\,\vec a` | a-arrow tip | after rotate_z (a in x-z plane) |
| `\vec a'' = \lVert a\rVert\,e_1` | a-arrow tip | after rotate_y (a on +x) |
| `\vec b` | b-arrow tip | until rotate_x |
| `\vec b'' = R_y R_z\,\vec b` | b-arrow tip | after rotate_x (b in x-y plane) |
| `c = \lVert b\rVert\sin\theta` | perpendicular (vec3) | show_triangle .. scale |
| `\vec a\times\vec b = \lVert a\rVert\,c\;e_3` | cross (vec3) tip | scale_by_mag_a onward |

Exact LaTeX, which intermediate shows when, and the font size are easy to tweak in
the `_LABELS` table once the pipeline renders.

## Implementation layers (this pass)

1. Dockerfile/Makefile: `USE_TEX_LABELS` flag -> build vendored texExpToPng + TeX.
2. `mathdemos/_labels.py`: runtime PNG generation (guarded by `shutil.which`), PIL ->
   RGBA GL texture, a billboard pipeline (eye-space quad: a quad at the label's
   eye-space center always faces the camera; projection-only MVP; alpha-blended),
   and a per-step label table. GL/PIL imports are module-level but the module is only
   imported *inside* `crossproduct.main()`, so the math/test import path stays headless.
3. `mathdemos/billboard.vert` / `billboard.frag`: textured alpha quad.
4. Wire into `crossproduct.py` `main()`/`draw_scene` (after the solids, blending on,
   depth read-only), positions from the same model matrices the vectors use.

## Goal (Bill)

Annotate the vectors with TeX labels, listing each and **what it equals**:
- the natural basis (e_1 / e_2 / e_3),
- the two input vectors a, b,
- the cross product a x b,
- the intermediates a', a'', b', b''.

Billboard OpenGL style: each label keeps the same orientation relative to the
camera regardless of camera position (always faces the viewer).

(The original multivariate-math source had `do_draw_image` billboard labels but they
were commented out, so the port skipped them; this revives that idea with
`texExpToPng`.)

## Dependency: texExpToPng (`/billopt/texExpToPng`)

C CLI: `texExpToPng --exp "<LaTeX>" --size <DPI> --output out.png` (or `--file`).
Wraps the expr in a `standalone` doc, `latex` + `dvipng`. Runs in its podman
container (TeX Live included): `make image` then invoke the binary. Nested podman
works in this sandbox, so labels can be generated here.

- **Open sub-issue — text color / transparency.** `dvipng` defaults to black text on
  a white background; the README exposes only `--exp/--size/--output`. For billboards
  over the 3D scene we want **light text on a transparent background**. Two options:
  1. **Post-process in mvp** (PIL): key the white bg to alpha and recolor the glyphs
     (load once at startup). No texExpToPng change.
  2. **Enhance texExpToPng** to pass `dvipng -bg Transparent -fg <color>` (small
     change to that project; cleaner output). Bill controls that repo too.
  Leaning (1) to keep texExpToPng untouched unless Bill prefers (2).

## Plan (phased)

1. **Label set + content (NEEDS BILL — see Decisions).** Decide each label's exact
   LaTeX and what "equals" it shows.
2. **Generate PNG assets (committed).** A script / make target runs `texExpToPng`
   (its container) once per label string -> PNGs in
   `src/modelviewprojection/mathdemos/labels/`. Committed so a normal run needs no
   TeX Live. (Mirrors how the ports ship media.)
3. **Texture load.** PIL -> RGBA GL texture (+ the color/alpha post-process if option
   1). mvpvisualization has no PNG loader yet; add a small one (reuse the ports' PIL
   pattern).
4. **Billboard pipeline.** New `.vert`/`.frag` (textured quad, alpha-blended). Quad
   built camera-facing: at the label's world position, spanned by the camera right/up
   axes (extracted from the view matrix) so it always faces the viewer; size in a
   fixed screen-ish scale. One pipeline, drawn after the solids with blending on,
   depth-test read-only.
5. **Placement + per-step visibility.** Put each label at its vector's tip; show the
   intermediates only at the steps where they exist (a'' once a is on +x, etc.),
   reusing the `reached(StepNumber.X)` timeline.

## Decisions — ANSWERED (Bill, 2026-06-14)

- **Label content / "what they equal": SYMBOLIC RELATIONS.** Each label shows the
  proof relation, e.g. `a' = R_z a` (a in x-z plane), `a'' = \lVert a\rVert\, e_1`,
  `b'' = R_y R_z b`, `c = \lVert b\rVert \sin\theta`,
  `a \times b = \lVert a\rVert\, c\; e_3`.
- **Basis labels: `e_1, e_2, e_3`** (gacalc/course convention).
- **Text color/transparency: ENHANCE texExpToPng** -- add `dvipng -bg Transparent
  -fg <color>` flags so it emits clean transparent/light PNGs directly (Bill owns
  that repo).  So this feature also entails a small `/billopt/texExpToPng` change
  (new flags) + rebuilding that image before generating the label assets.
- **Asset strategy: RUNTIME-CONDITIONAL, graceful degradation (Bill, 2026-06-14).**
  Do NOT commit PNGs. At demo startup, check whether the `texExpToPng` executable is
  available (`shutil.which("texExpToPng")`, plus maybe a sibling-repo / env-var
  fallback like the ports use).  If present: generate the label PNGs at runtime (to a
  temp/cache dir) and render the billboards.  If absent: **skip generation AND skip
  rendering the labels entirely** -- the demo runs normally, just without labels.
  Rationale: Bill runs on Linux-in-container (has TeX + the wrapper); Windows/Mac
  users without TeX/the wrapper must still get the working demo, minus labels.  So
  ALL label code (generation + texture load + billboard draw) is guarded behind the
  availability check.

Still to nail down when implementing: the exact LaTeX per label, the fg color, the
DPI/size, and the per-step visibility map (which intermediate shows when).

## Verify

Display-only — Bill verifies the labels render, face the camera from any angle, and
sit at the right vectors per step. Headless: PNG generation runs; texture load +
pipeline compile import without a window only where possible (GL is display-bound).
