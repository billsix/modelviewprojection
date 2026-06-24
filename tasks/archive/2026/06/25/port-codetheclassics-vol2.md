# Plan: Port Code the Classics **Vol 2** from PyGame Zero → GLFW + OpenGL 3.3 core

**Status:** ✅ **ALL 5 Vol 2 games ported + render-verified 2026-06-24** (eggzy,
avenger, beatstreets, kinetix, leadingedge). **Audio confirmed working on
hardware 2026-06-25** (`just_playback`). Remaining: human play-feel pass.
**Sibling task:** [`port-codetheclassics-vol1.md`](port-codetheclassics-vol1.md) — same job for Vol 1, **and owns the shared `pgzero_gl` shim this task builds on.**
**Depends on:** Vol 1 Phase 1 (the shim must exist + be proven on boing first). ✅

## Progress (2026-06-24)

**Canary changed kinetix → eggzy.** On closer read kinetix needs FBO-backed
offscreen `Surface`s (its brick/shadow accumulation buffers) and heavy joystick
— both unverifiable headless and well beyond the boing-proven core. A finer
per-game survey (below) showed **eggzy** is the genuinely lightest Vol 2 lift for
this shim: **no** offscreen `Surface`, **no** mask, **no** gfxdraw, **no** text.
This matches the fallback noted in the original plan ("if kinetix leans on
something awkward, pick another"). kinetix remains a Phase 2 game.

Per-game shim-extension burden (refined survey):

| Game | Surface() | mask | gfxdraw | joystick | Vector2 | draw.text |
|------|:--:|:--:|:--:|:--:|:--:|:--:|
| **eggzy** | 0 | 0 | 0 | 27 | 1 | 0 | ← canary |
| avenger | 0 | 3 | 0 | 30 | 30 | 6 |
| beatstreets | 1 | 0 | 0 | 27 | 24 | 6 |
| kinetix | 2 | 0 | 0 | 29 | 15 | 0 |
| leadingedge | 1 | 0 | 4 | 27 | 18 | 2 |

- **Shim extended for Vol 2** (all in the shared `pgzero_gl`): `Vector2`
  (`pygame.math.Vector2`), GLFW-backed `joystick` (best-effort; keyboard play
  works with no pad), `pygame.image.load`, `pygame.draw.rect`/`line`, and
  **atlas sub-rect sampling** (`screen.surface.blit(img, pos, area=rect)` — used
  for tilemaps). boing re-verified after these changes (no regression).
- **eggzy ported** → `vol2/eggzy/eggzy.py`, assets + `tilemaps/` vendored. Body
  byte-identical to upstream from `# Set up constants` onward. Uses
  `sys.path.append` (not insert) because eggzy reads `sys.path[0]` for its
  tilemaps/save folder. Attribution header + repo/book links added.
- **Verified headless:** module exec + real Tiled level load (XML parse, tileset
  decode 975×2850, 8 collision rects from the grid) + 120-frame PLAY sim with the
  player walking/colliding. Sprite transparency confirmed preserved on decode.
- **Rendering verified headless via EGL** (`_smoketest.py`, Mesa llvmpipe):
  eggzy's frame renders correctly — **brick tilemap (atlas sub-rect path),
  player sprite, and on-screen text** all draw. The three first-run shim bugs
  (integer-tint black screen, HiDPI viewport, joystick-before-init crash — see
  the Vol 1 task) were all fixed in the shared shim; eggzy specifically exercised
  + fixed the joystick-before-init crash. **Audio + gamepad need real hardware.**

### Phase 2 ✅ done — avenger, beatstreets, kinetix, leadingedge
Shim extensions added (all in the shared `pgzero_gl`), simpler than first feared:
- **`pygame.mask`** (`mask.py`) — `from_surface`/`get_at`/`get_size` from the
  image's CPU alpha channel (avenger's terrain). No GL.
- **`pygame.Surface`** (`surface.py`) — a **CPU RGBA buffer**, not an FBO: the
  games only need solid fills (beatstreets/leadingedge fades) and sprite
  accumulation (kinetix bricks/shadows), which are `fill(color, rect)` +
  `blit(img, pos, area)` composited on the CPU and uploaded as a texture when
  dirty. Far simpler + more robust than render-to-FBO. **kinetix's brick wall
  renders correctly in gameplay** (verified — the riskiest path).
- **`pygame.gfxdraw` + `pygame.draw.polygon`** → `renderer.polygon` (GL triangle
  fan / line loop) for leadingedge's road.
- **`Vector3`** (leadingedge's pseudo-3D), `pygame.rect.Rect`, and proper
  **submodule registration** in `sys.modules` so `from pygame.X import Y` /
  `import pygame.gfxdraw` resolve.
- Data files: beatstreets' `attacks.json` vendored alongside it; games are run
  from their own dir (relative `open()`).

All five render their title screens via the EGL smoke test (leadingedge's title
is a logo on black, ~18% coverage — legitimately, not a bug).

> ⛔ **Pre-flight blocker — licensing.** Source: `/mvp/Code-the-Classics-Vol2`
> (origin `github.com/raspberrypipress/Code-the-Classics-Vol2`). Checked
> 2026-06-24: **no LICENSE file, no headers, nothing in git history, nothing on
> the GitHub repo page** — default "all rights reserved." Games are © Raspberry
> Pi Press / Andrew Gillett et al. (graphics by Dan Malone, audio by Allister
> Brimble). Same blocker as Vol 1 — see that task's licensing note. Confirm
> redistribution + attribution before any port code or assets land.

---

## Goal

Same as Vol 1: re-implement the five Vol 2 games as GLFW + OpenGL 3.3 core
programs (book demo20+ style — `glfw`, `OpenGL.GL`, `imgui_bundle`, `imageio`,
no pygame, no fixed function), on top of the shared `pgzero_gl` shim, one
subdirectory per game under `ports/codetheclassics/vol2/`.

The five games (single-file PyGame Zero, 2-D sprite-blitting, but **markedly
heavier** than Vol 1):

| Game | bytes | pygame.* refs | `screen.surface` | `img.get_*` | draw.text | heavy bits |
|------|----:|----:|:--:|:--:|----:|------|
| **kinetix** | 46.6 K | 7 | 2 | 0 | 0 | `transform.scale`; no text. **Recommended canary.** |
| avenger | 62.4 K | 8 | 2 | 3 | 10 | scrolling shmup; text-heavy |
| eggzy | 68.5 K | 7 | 3 | 11 | 7 | tilemaps (`tilemaps/` dir); masks |
| leadingedge | 80.5 K | 15 | 4 | 16 | 20 | racer; most `pygame.*` + most text + transforms |
| beatstreets | 106.6 K | 4 | 2 | 5 | 10 | beat-em-up; ~2400 LOC, largest |

---

## What's new vs Vol 1 (shim extensions this task drives)

Vol 1 establishes the core shim (sprites, `Actor`, `screen.blit/fill/draw.text`,
keyboard, audio, the loop). Vol 2 games reach further into pygame, so the shim
grows. Audit per game, but across the five the extra surface is:

- **`pygame.mask.from_surface` / pixel-perfect collision** (eggzy, leadingedge).
  No CPU surface in GL. Options: keep a CPU-side alpha bitmap per loaded image
  (cheap — we already decode PNGs with imageio, so retain the alpha channel as a
  mask array) and implement `colliderect`-then-mask overlap on the CPU; or
  approximate with AABB where the game can tolerate it. Pixel-mask collision is
  gameplay-critical in these two — do it properly with the retained alpha array.
- **`pygame.gfxdraw.filled_polygon` / `polygon`** and **`pygame.draw.polygon`**
  (leadingedge — the pseudo-3D road). Map to GL triangle fans / `GL_TRIANGLES`
  in the solid-color shader. leadingedge's road rendering is the single biggest
  rendering departure from "just blit sprites" — budget for it.
- **`pygame.transform.scale` / `smoothscale`** (kinetix, leadingedge). In GL this
  is just a scaled quad (`smoothscale` ≈ linear texture filtering, `scale` ≈
  nearest). Add a scale to the sprite-draw path.
- **`pygame.joystick`** (`Joystick`, `get_count`) — gamepad support. Map to the
  GLFW joystick/gamepad API in `input.py`. Several Vol 2 games support pads.
- **`pygame.Surface` + `SRCALPHA` offscreen render targets** (avenger, eggzy,
  leadingedge build intermediate surfaces). Map to **FBO-backed textures**: a
  `Surface` becomes an offscreen color texture you render quads into, then blit
  as a sprite. This is the most involved extension — design it once in the shim.
- **`pygame.math.Vector`** — replace with mathutils/gacalc `Vector2` or plain
  tuples (consistent with the rest of the repo).
- **tilemaps** (eggzy has a `tilemaps/` dir) — a tile renderer (grid of textured
  quads from a tileset + map data). Game-specific; lives in the eggzy port, not
  the shim, unless a second game needs it.
- **heavy `draw.text`** (leadingedge 20, avenger/beatstreets 10) — the bitmap
  font atlas must be solid before these. Confirm kwargs: across all games only
  `color`, `fontsize`, `center`, `pos`, `topleft` are used.

---

## Assets (size caveat)

Vol 2 is **3382 PNGs** plus 193 audio files across the five games — do **not**
bulk-copy. Vendor only the *one* game's assets into its port dir (the shim's
loader takes a configurable asset root). eggzy additionally needs its
`tilemaps/`. (Gated on the licensing blocker.)

---

## Phasing

### Phase 0 — licensing (blocker, shared with Vol 1).

### Phase 1 — **kinetix** canary (after Vol 1's shim is proven)
kinetix is the smallest Vol 2 game, has **no `draw.text`** and **no
`img.get_*`**, and its only real new need is `transform.scale` (scaled quad).
Best first contact with Vol 2. Port: copy `kinetix.py`, swap imports, drop the
version-check/mixer boilerplate, vendor kinetix's assets, add the scaled-quad
path to the shim.

> If kinetix turns out to lean on something awkward on closer read, **avenger**
> is the fallback canary (straightforward scrolling shmup), but it pulls in the
> text atlas immediately. Confirm canary before coding.

### Phase 2 — remaining Vol 2 games (one follow-on sub-task each), easiest first
- **avenger** — scrolling shmup; mostly sprites + lots of `draw.text`. Exercises
  the font atlas at volume; one offscreen `Surface`.
- **beatstreets** — largest by LOC but a fairly conventional beat-em-up; depth-
  sorted sprites, text. No masks/polygons. Mostly "more of the same."
- **eggzy** — adds the **tile renderer** + **mask collision** + offscreen
  surfaces. Real shim work.
- **leadingedge** — last and hardest: pseudo-3D road via **filled polygons**,
  the most `pygame.*` (15) and most text (20), transforms, offscreen surfaces.
  Treat as its own mini-project.

---

## Verification
Same constraint as Vol 1 and the rest of the repo: **on-screen GL can't be
verified headless** in the nested container. Byte-compile + import + unit-test
pure logic (collision math, scoring, road projection in leadingedge are all
framework-independent and worth direct tests); **Bill verifies the window,
audio, fonts, and gamepad.** Per-game smoke launcher for him.

---

## Open questions
- Same naming questions as Vol 1 (`codetheclassics`/`vol2`).
- FBO-backed `Surface` emulation: build the general version in Phase 1 even
  though kinetix may not need it, or defer to avenger/eggzy? (Lean: defer, but
  design the `screen.surface` facade so it's extensible.)
- leadingedge's road: faithful polygon port vs. re-expressing as a textured
  ground quad — decide when we get there; faithful first.
- Gamepad: in scope for the first pass or keyboard-only until Bill asks?
