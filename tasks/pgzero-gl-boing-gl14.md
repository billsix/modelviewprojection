# boing, twice: a GL 1.4 fixed-function companion beside the 3.3-core original

**Status:** IMPLEMENTED 2026-09-04 (on a branch) — `boing_gl1.py` verified ruff+ty clean, renders
the real scene under a fixed-function 2.1 context, and is **byte-identical (AE=0)** to the 3.3
boing frame 180. Awaiting maintainer play-test (input/audio, which the frame trace can't cover).
**Priority:** 4
**Difficulty:** 3

## Implementation record (2026-09-04, while maintainer away — for review)

- **Generated** `ports/codetheclassics/vol1/boing/boing_gl1.py` (1725 lines) from `boing.py` via
  the saved generator `tasks/adhoc/pgzero-gl-boing-gl14/make_boing_gl1.py` — a guarded,
  re-runnable transform (asserts every anchor; regenerates from pristine `boing.py`). It swaps the
  3.3 `Renderer` + shader/matrix/VAO support for the inlined fixed-function `Renderer1x`
  (`renderer_gl1.py`), swaps the window hints to a **2.1 compatibility context**, drops the
  core-profile VAO bind, and rewrites the renderer-section banner/docstring + the `Context`
  renderer-type annotations (`Renderer` → `Renderer1x`) so ruff/ty resolve.
- **Verification (nested mvp container + Xvfb, software GL):** captured frame 180 with the step-1
  harness. `ruff check` clean; `ty check` clean (same as the baseline `boing.py`); renders the
  BOING! title/menu (800×480, 14 534 colors, mean 0.578 — not black), no GL errors, clean exit
  (ALSA/audio no-ops headless as designed).
- **BONUS — byte-identical.** `magick compare -metric AE` of the 3.3 `boing.py` vs `boing_gl1.py`
  frame 180 = **0**. GL_NEAREST + the same pixel-space ortho + the same unit-quad geometry make the
  fixed-function and shader pipelines produce identical pixels on llvmpipe — a strong "same pixels,
  different pipeline" demonstration for the study.
- **Decisions taken (per the recorded conventions; flag if you disagree):**
  1. Filename `boing_gl1.py`, reciprocal one-line docstring cross-reference added to **both**
     `boing.py` and `boing_gl1.py` (the sole, comment-only edit to the otherwise-frozen `boing.py`
     — still byte-identical, confirmed by the AE=0 above).
  2. `Renderer1x`'s own docstrings keep their "same interface as the 3.3 `Renderer`" design notes
     (intentional cross-references, not stale).
  3. `boing_gl1.py` inherits `boing.py`'s current (interim) LGPL header — the license cleanup is
     deliberately deferred to `tasks/codetheclassics-licensing-after-shim-inline.md`.
- **Open for maintainer:** play-test input/audio/gameplay (frame trace covers the no-input path
  only); then this task can be archived.

## BLUF

Add a **second, parallel boing** — `boing_gl1.py`, a **fixed-function OpenGL 1.x (2.1 compat
context)** rendering of the same game — living beside the existing 3.3-core `boing.py`, so a
student can `diff` the two files and see *exactly* what changes between the old immediate-mode
fixed-function pipeline (the book's demo19 era) and modern 3.3 Core + shaders, with the game
logic held identical. **The 3.3 `boing.py` is not touched** (its frame-180 byte-identical proof
stays intact); the new file is a study companion. The GL-1.x renderer already exists and is
proven — `src/modelviewprojection/pgzero_gl/renderer_gl1.py`'s `Renderer1x` — so this is a
scoped derivation: inline `Renderer1x` in place of the inlined 3.3 `Renderer`, and swap the
window-creation hints from 3.3-core to 2.1-compat.

## Context (read first, act cold)

- **Why this exists (maintainer, 2026-09-04):** the course deliberately teaches the *old*
  rendering style first — **demo19–19e are fixed-function OpenGL 1.x/2.1** (`glMatrixMode` /
  `glOrtho` / `glBegin` / `glTexCoord2f` / `glVertex2f` / `glPushMatrix`), demo20 adds a trivial
  shader, demo21+ are 3.3 Core (see `CLAUDE.md` › pedagogical arc). Boing is the *simplest* game
  (the rawest rung of the step-2 abstraction gradient), so it is the right place to show the
  oldest pipeline. The maintainer asked for **both** a 1.4 and a 3.3 boing "so a student can
  study the difference" — not a conversion.
- **What already exists and is proven:**
  - `boing.py` (this dir) — the step-2 result: 3.3-core, library-style (owns its loop),
    Actor dropped → `@dataclass`es + `blit`/`draw_sprite`, 1851 lines, **frame-180
    byte-identical** to the pre-strip inline. Its inlined 3.3 renderer is `class Renderer`.
  - `src/modelviewprojection/pgzero_gl/renderer_gl1.py` — `class Renderer1x`, a **drop-in with
    the identical interface** to the 3.3 `Renderer` (`begin_frame` / `draw_image` / `fill` /
    `filled_rect` / `rect` / `line` / `polygon` / `circle` / `set_clip`). Fixed-function:
    `glOrtho` pixel projection, `glBegin(GL_QUADS)` + `glTexCoord2f`/`glVertex2f` immediate mode,
    `GL_MODULATE` texture env. Targets GL 1.4/1.5 (really ≥1.1). This is the **study source** to
    inline — the same way `boing.py` inlined the 3.3 `Renderer`.
- **The texture upload is already 1.x-compatible.** `Image.gl_texture()` (in `boing.py`, from
  the shim's `resources.py`) uploads via `glGenTextures` / `glTexImage2D` / `glTexParameteri`
  — all core since GL 1.1, no VAO, no shader. So the image loader is **shared unchanged**; only
  the renderer and the context version differ.
- **Fidelity:** this is a *rendering-pipeline* variant of a faithful port. The game code
  (RNG order, update/draw order, gameplay) is copied verbatim from `boing.py` and must stay
  identical — only the drawing back end changes.

## The derivation — `boing_gl1.py` = `boing.py` with two regions swapped

Copy `boing.py` to `boing_gl1.py` in the **same directory** (so `Context.asset_root =
dirname(__file__)` still resolves to `boing/`, and it shares the existing `images/` `sounds/`
`music/` folders — **no asset duplication**). Then make exactly these changes; nothing else.

### Region 1 — the renderer and its support code (the bulk of the diff)

**Remove** (these exist only to serve the 3.3 shader pipeline):
- the GLSL shader strings `_VERT` / `_FRAG` (~`boing.py:848-876`);
- `_compile()` (~879-889);
- the matrix helpers `_identity()` / `_translate()` / `_scale()` / `ortho_pixels()`
  (~811-840) — fixed-function builds its transform with `glOrtho`/`glTranslatef`/`glScalef`;
- `class Renderer` (~892-1102).

**Insert in their place** `class Renderer1x`, inlined verbatim from
`renderer_gl1.py:46-198` (drop that module's `from __future__ import annotations` and the
`from .renderer import _rgba` line — `_rgba` is already defined in the boing file just below the
renderer). Keep its docstring; it *is* the teaching text (it explains `glOrtho` / `glBegin` /
`GL_MODULATE` and why the two renderers "draw the same pixels").

**Keep** `_rgba()` (~1104+) — both renderers call it — and everything else in the file
unchanged.

Net effect: the 1.4 file is *shorter* than the 3.3 file (no shaders, no VAO/VBO setup, no
manual 4×4 matrices). That asymmetry is the lesson, not a defect — don't manufacture parallel
boilerplate to make the diff symmetric.

### Region 2 — the window hints + renderer construction in `__main__`

In `boing.py:1781-1794` the 3.3-core setup reads:

```python
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
window = glfw.create_window(WIDTH, HEIGHT, TITLE, None, None)
...
glfw.make_context_current(window)
glfw.swap_interval(1)
# macOS core profile requires a non-zero VAO bound at all times.
GL.glBindVertexArray(GL.glGenVertexArrays(1))
Context.window = window
Context.renderer = Renderer(WIDTH, HEIGHT)
```

Replace with the **2.1 compatibility** setup (maintainer confirmed 2.1 compat is fine):

```python
# OpenGL 2.1 compatibility context: 2.1 predates the core/compat split, so
# request version 2.1 with the default (ANY) profile and no forward-compat.
# The fixed-function pipeline this game draws with (glOrtho + glBegin) is not
# available in a 3.3 core context -- that is the whole point of this variant.
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
window = glfw.create_window(WIDTH, HEIGHT, TITLE, None, None)
...
glfw.make_context_current(window)
glfw.swap_interval(1)
# No VAO: the fixed-function pipeline needs none (VAOs are a 3.0+ construct).
Context.window = window
Context.renderer = Renderer1x(WIDTH, HEIGHT)
```

(The `create_window` failure check, key callback, SIGINT/SIGTERM handlers, the 60 Hz loop
body, and the `audio.shutdown()` + `glfw.terminate()` finally are all **unchanged** — the loop
calls `Context.renderer.begin_frame(...)` / `draw()` through the identical interface.)

## Verification

- **NOT byte-identical to the 3.3 boing, by design.** Fixed-function vs shader rendering on the
  software rasterizer (llvmpipe) can differ by a pixel or two (rasterization/blend rules), so do
  **not** gate on AE=0 against `boing.py`. What to prove instead:
  1. `boing_gl1.py` **runs headless** N frames without a GL error (fresh Xvfb + `DISPLAY=:99` +
     `PGZERO_MAX_FRAMES`, the step-1/step-2 harness in `tasks/adhoc/pgzero-gl-inline/`), and
  2. a captured frame is **non-black and looks like boing** (pixel-mean / unique-colour check +
     eyeball the PNG) — i.e. the fixed-function path actually draws the scene.
  - *Bonus, worth capturing if it holds:* frame 180 of `boing_gl1.py` vs `boing.py` — GL_NEAREST
    sampling + the same ortho + the same quad geometry *may* come out byte-identical; if it does,
    note it (it's a strong "same pixels" demonstration). If it differs slightly, that's expected;
    record the AE delta and move on.
- `ruff` + `ty` clean on `boing_gl1.py` (it's under `ports/codetheclassics/vol1/`, which
  `format.sh` checks). Watch for the same pre-existing game int/float-Coef debt boing carried;
  reuse whatever suppressions `boing.py` needed.
- **Maintainer play-test** (input/audio path the frame trace can't cover), same as every step-2
  game.
- **Reproducibility:** if the copy-and-swap turns out mechanical enough to script, save it under
  `tasks/adhoc/pgzero-gl-boing-gl14/` per the ad-hoc-scripts convention; if it's a hand-authored
  second file (likely — `Renderer1x` is inlined by hand), the "two regions" spec above IS the
  record, so a script isn't required.

## Docs to update when it lands (ship with the unit, don't defer to a sweep)

- `CLAUDE.md` › Code-the-Classics: note that **boing ships twice** — `boing.py` (3.3 Core, the
  gradient's rawest *modern* rung) and `boing_gl1.py` (fixed-function GL 1.x / 2.1-compat, the
  demo19-era pipeline) — a deliberate side-by-side for studying the pipeline difference; the
  other 9 games are 3.3 Core only.
- `tasks/pgzero-gl-step2-strip-and-restructure.md` › boing row + the boing design-decision
  block: cross-link this companion.
- `tasks/reference/pgzero-gl-design-for-a-personal-learning-library.md`: record that the
  fixed-function `Renderer1x` back end now has a live consumer in the ports (boing_gl1), not just
  the `PGZERO_GL=1` shim switch.

## Decisions (maintainer, 2026-09-04)

1. **Filename: `boing_gl1.py`** — mirrors the shim's own `renderer_gl1.py` and reads as "the GL
   1.x boing." (Confirmed.)
2. **Each boing file gets a one-line header cross-reference** to the other, so a reader of either
   knows the sibling exists and that a `diff` is the intended study path — e.g. atop `boing.py`:
   `# See boing_gl1.py for the fixed-function GL 1.x rendering of this same game (diff the two to
   compare pipelines).`, and the mirror atop `boing_gl1.py`. (Confirmed.) This is the one edit
   that touches the otherwise-frozen `boing.py`; it is comment-only, so re-proving `boing.py`
   frame-180 byte-identical is trivial.

**Both decisions resolved — no open questions remain; task is ready to implement on go-ahead.**

## Related

- `tasks/pgzero-gl-step2-strip-and-restructure.md` — where boing became the rawest game (the
  base this derives from); the boing depth-1/depth-2 decision block.
- `tasks/pgzero-gl-inline-strip-reextract.md` — the umbrella initiative (inline → strip →
  re-extract).
- `src/modelviewprojection/pgzero_gl/renderer_gl1.py` — the fixed-function `Renderer1x` study
  source being inlined.
- `CLAUDE.md` › pedagogical arc (demo19 fixed-function → demo20 shader → demo21+ 3.3 core) — the
  progression this port variant mirrors.
