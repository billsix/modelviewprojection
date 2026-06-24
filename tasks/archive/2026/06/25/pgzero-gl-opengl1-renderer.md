# Plan: an OpenGL 1.x (fixed-function) renderer backend for `pgzero_gl`

**Status:** ✅ **done 2026-06-25.** `renderer_gl1.py` (fixed-function GL 1.x)
implemented + render-verified against the 3.3 renderer on all 10 games (identical
output, software EGL). Selected with `PGZERO_GL=1`. **Confirmed on real hardware
2026-06-25:** boing launched on an AMD Radeon RX 7600 XT (radeonsi, Mesa 26, GL
4.6 Compatibility Profile) with `backend=gl1-fixedfunc`. Added `PGZERO_GL_INFO=1`
(prints backend + real GL_VERSION/GL_RENDERER) and `PGZERO_MAX_FRAMES=N`
(auto-close) to the runner for on-hardware smoke testing.
**Relates to:** the Code-the-Classics ports — [`port-codetheclassics-vol1.md`](port-codetheclassics-vol1.md),
[`port-codetheclassics-vol2.md`](port-codetheclassics-vol2.md).

## What landed

- **`pgzero_gl/renderer_gl1.py`** — `Renderer1x`, same interface as the 3.3
  `Renderer`, using `glOrtho` + `glMatrixMode` + the matrix stack
  (`glPushMatrix`/`glTranslatef`/`glRotatef`/`glScalef`) + `glBegin/glEnd`
  immediate mode + fixed-function texturing (`GL_TEXTURE_2D`, `GL_MODULATE` so
  `texture * glColor` reproduces the shader's `texture * tint`). Atlas sub-rects
  via `glTexCoord2f`; flat shapes/lines/polys/circles via `glBegin` with texturing
  off; `set_clip` via `glScissor` (same as 3.3).
- **`runner.py`** — `_select_renderer()` reads `PGZERO_GL`; the legacy path
  requests a **compatibility 2.1 context** (`OPENGL_ANY_PROFILE`, no forward-compat)
  and skips the core-only default-VAO bind. `Image/Surface.gl_texture()` needed no
  change (plain `glGenTextures`/`glTexImage2D`).
- **`_smoketest.py`** — `--gl1` flag (compatibility EGL context + `Renderer1x`)
  so the two backends can be pixel-compared; they match (e.g. boing/eggzy produce
  identical distinct-colour counts).

Run any game on the old pipeline with `PGZERO_GL=1 python <game>.py`.

## Original plan (for reference)

## Goal

Add a second `pgzero_gl` renderer that uses **fixed-function OpenGL 1.x** instead
of 3.3 core + shaders, selectable at runtime, so the ports run on old/limited GL
stacks (ancient GPUs, software GL, Raspberry Pi in GL-compat mode, remote X)
where a 3.3 core context isn't available. It also has pedagogical value: it's the
same fixed-function era the book introduces at **demo19** (`glMatrixMode`,
`glOrtho`, `glBegin/glEnd`, `glEnable(GL_TEXTURE_2D)`), so the two renderers side
by side show "the modern shader pipeline vs the old fixed pipeline doing the
exact same 2-D blits."

**Target version:** OpenGL **1.5** (or 1.4) — has everything a 2-D sprite blitter
needs: `glOrtho`, fixed-function texturing, `glBegin/glEnd` immediate mode (and
optionally VBOs from 1.5). Avoid anything 2.0+ (no shaders). 1.1 would even
suffice (textures + immediate mode); pick 1.4/1.5 as a comfortable floor. Confirm
the exact floor when implementing.

## Why it's tractable

The renderer is already **isolated** in `pgzero_gl/renderer.py` behind a small
interface that the rest of the shim uses:

- `Renderer(width, height)`
- `begin_frame(fb_w, fb_h)`
- `draw_image(image, topleft, angle=, anchor=, tint=, src=)`
- `fill(color)`, `filled_rect`, `rect`, `line`, `circle`, `polygon`
- `set_clip(rect)`
- and `image.gl_texture()` / `surface.gl_texture()` upload textures.

Nothing else in the shim issues GL calls. So an `Renderer1x` implementing the
same methods is a drop-in. `resources.Image.gl_texture` / `surface.Surface.gl_texture`
already use plain `glGenTextures`/`glTexImage2D` (core-compatible) — they likely
need **no change** beyond dropping the assumption that a VAO is bound.

## Design

1. **`renderer_gl1.py`** — a `Renderer` with the same interface, implemented with:
   - `glMatrixMode(GL_PROJECTION)` + `glLoadIdentity` + `glOrtho(0, W, H, 0, -1, 1)`
     (note top-left origin, y-down — same mapping as the current ortho).
   - `glEnable(GL_TEXTURE_2D)`, `glEnable(GL_BLEND)`, `glBlendFunc(...)`.
   - `draw_image`: `glBindTexture`, then a `glBegin(GL_QUADS)` with
     `glTexCoord2f`/`glVertex2f` for the 4 corners (apply rotation/anchor on the
     CPU, or via `glPushMatrix`/`glTranslatef`/`glRotatef`/`glScalef` —
     pedagogically nicer, mirrors demo19). `tint`/alpha via `glColor4f`.
   - `src` sub-rect → compute the 4 `glTexCoord2f` from the pixel rect.
   - flat shapes (`filled_rect`, `line`, `polygon`, `circle`) via
     `glDisable(GL_TEXTURE_2D)` + `glColor` + `glBegin(GL_QUADS/LINES/POLYGON/...)`.
   - `set_clip` → `glScissor` (same as now).
2. **Context creation** — `runner.py` currently requests a 3.3 core profile via
   GLFW hints. Add a path that requests a **compatibility/legacy** context (drop
   the core-profile + forward-compat hints; optionally request 2.1 or no version
   hint so the driver gives a compatibility context that supports 1.x calls).
3. **Selection** — env var `PGZERO_GL=1` (or `=legacy`) picks `Renderer1x` +
   the legacy context; default stays 3.3 core. `runner.go()` chooses which
   `Renderer` class to build and which window hints to set. Keep it a single
   switch so both paths share the loop/input/audio.
4. **Texture upload** — verify `gl_texture()` works without a bound VAO in a
   compatibility context (it should). NPOT textures are fine on 1.x with most
   drivers via `GL_ARB_texture_non_power_of_two`/2.0; if a true 1.x floor must
   support strictly POT, pad textures to POT and adjust texcoords (only if a
   target actually needs it — most "1.x" drivers today are really 2.1+ Mesa and
   handle NPOT). Decide based on the real target; **don't pad pre-emptively.**

## Verification

Same as the main renderer: the EGL headless harness (`_smoketest.py`) can create
a **compatibility** context too (drop the core-profile attribs in
`make_context`), so each game's frame can be pixel-compared between the 3.3 and
1.x renderers — they should look identical. Add a `--gl1` flag to `_smoketest.py`.
Audio/gamepad unchanged.

## Open questions
- Exact GL floor (1.1 / 1.4 / 1.5)? Lower = wider reach, but immediate-mode only.
- Selection mechanism — env var (proposed) vs a `go(renderer=...)` arg?
- Is there a real target machine driving this, or is it pedagogical + insurance?
  That decides how hard to chase a strict low floor (POT textures etc.).
