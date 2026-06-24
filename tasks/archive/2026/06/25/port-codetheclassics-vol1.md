# Plan: Port Code the Classics **Vol 1** from PyGame Zero → GLFW + OpenGL 3.3 core

**Status:** ✅ **ALL 5 Vol 1 games ported + render-verified 2026-06-24** (boing,
cavern, myriapod, bunner, soccer). Shared shim built. **Audio confirmed working
on hardware 2026-06-25** (`just_playback`). Remaining: human play-feel pass.
**Sibling task:** [`port-codetheclassics-vol2.md`](port-codetheclassics-vol2.md) — same job for Vol 2.
**This task owns the shared shim** (`pgzero_gl`); the Vol 2 task consumes it.

## Progress (2026-06-24)

- **`ports/codetheclassics/pgzero_gl/` shim built** — `renderer` (GL3.3 sprite +
  flat shaders, pixel ortho, atlas sub-rect, scissor), `actor`, `geometry`
  (`Rect`, `Vector2`), `resources` (lazy-GL image + sound loaders), `text`
  (Pillow glyph bitmaps), `audio` (`just_playback`, best-effort/guarded),
  `input` + `joystick` (GLFW), `runner` (60 Hz loop), `__init__` (exports +
  `pygame`/`pgzrun`/`pgzero` compat stubs). README at the tree root.
- **boing ported** → `vol1/boing/boing.py`, assets vendored. Body byte-identical
  to upstream from `# Set up constants` onward; only the import line + dropped
  version-check changed. Attribution header + repo/book links added.
- **Verified headless:** Rect/ortho/Actor-anchor unit checks; full module exec
  with GL/window stubbed — assets load, `Game()` builds, AI sim moves the ball,
  keyboard shim drives the paddle. **GL window + audio are Bill's to verify** (no
  display in the build container).
- **`just_playback` added to `requirements.txt`** (audio backend; pulls
  miniaudio — a C ext built by pip, needs the image's gcc; verify on next
  `make image`, per the Dockerfile/requirements sync rule).

### Bugs found + fixed on first real run (2026-06-24)
Bill ran both games; **boing was a black screen, eggzy crashed.** Root causes:
1. **Black screen (boing):** the sprite draw's default `tint` was integer
   `(1,1,1,1)`; the colour normaliser read ints as 0–255 and divided by 255, so
   every sprite drew at ~0.4% brightness + alpha. Fixed: default tint is floats.
2. **HiDPI:** viewport used logical size, not the framebuffer size — would fill
   only a corner on a scaled display. Fixed: viewport + scissor use the real
   framebuffer size each frame.
3. **eggzy crash:** the joystick shim queried GLFW at import (before
   `glfw.init()`), returning garbage → a phantom controller whose button bytes
   failed to parse. Fixed with a `context.glfw_ready` guard + defensive parsing.
4. **White box around sprites (eggzy):** many CtC PNGs are palette-mode (`P`)
   with transparency; `imageio.imread` returned them as 3-channel RGB, dropping
   the alpha → transparent backgrounds rendered as opaque white. Fixed: the
   image loader now decodes via `PIL.Image.open(path).convert("RGBA")`, which
   turns palette/grayscale transparency into a real alpha channel. (imageio no
   longer used by the shim.)

**Rendering is now actually verified headless**, not just by eye: EGL surfaceless
(Mesa llvmpipe) works in the container, so `_smoketest.py` renders a frame to a
pbuffer and reads it back. Both canaries render correctly (boing = the BOING!
menu over the table; eggzy = brick tilemap + player + on-screen text). **Audio +
gamepad still need real hardware.**

### Phase 2 ✅ done — cavern, myriapod, bunner, soccer
All four ported via a generic transform (prepend shim bootstrap, clean the
`pygame`/`pgzero`/`pgzrun` import line, keep the body verbatim). The shim's
`pgzero.__version__` is reported as "2.0" so each game's version-check passes
untouched — no need to strip it. soccer needed `pygame.rect.Rect` +
`from pygame.math import Vector2` (handled by registering pygame submodules in
`sys.modules`); bunner needed `pygame.draw.rect`/`set_clip` (already present).
All four render their menu/title screens correctly via the EGL smoke test.

> ⛔ **Pre-flight blocker — licensing (resolve before any code lands).** The source
> lives in `/mvp/Code-the-Classics-Vol1` (origin `github.com/raspberrypipress/Code-the-Classics-Vol1`).
> Checked 2026-06-24: **no LICENSE file, no license/copyright headers in any `.py`,
> nothing in git history, and the GitHub repo page shows no license** — which under
> default copyright means **all rights reserved**. README only credits the authors
> and links to buy the book. Games are © Raspberry Pi Press / the individual
> authors. Porting into modelviewprojection (GPL-2.0+) creates a redistributable
> derivative work of third-party code whose terms are unstated. **Confirm with Bill**
> that redistribution + attribution is OK before any ported game code or copied
> assets are committed. Everything below assumes this clears.

---

## Goal

Re-implement the five Vol 1 games as GLFW + OpenGL 3.3 core-profile programs, in
the style the book ends on (demo20+: `glfw`, `OpenGL.GL`, `imgui_bundle`,
textures via `imageio`, no fixed function, no pygame). Land them under the ports
tree, one subdirectory per game. Dependencies stay within what the book/code
already uses, plus **one** small audio library (see *Dependencies*).

The five games (all single-file PyGame Zero, all 2-D, pixel-coordinate,
sprite-blitting):

| Game | LOC | pygame.* refs | uses `screen.surface` | uses `img.get_*` | notes |
|------|----:|----:|:--:|:--:|------|
| **boing** | 475 | 2 | no | no | Pong. Simplest. **Recommended canary.** |
| bunner | 899 | 5 | yes (2) | yes (1) | Frogger; `on_key_down`, one `Rect` |
| cavern | 783 | 2 | no | no | Bubble Bobble-like |
| myriapod | 911 | 2 | no | no | Centipede; uses `transform` (sprite flip) |
| soccer | 1126 | 10 | yes (4) | no | biggest; `screen.surface.set_clip`, `pygame.math.Vector`, `joystick` |

None of the five use pgzero's `clock`/`animate` scheduler. Only bunner uses an
event hook (`on_key_down`). That keeps the shim's surface small.

---

## Architecture (decided with Bill, 2026-06-24)

Three decisions were taken up front:

1. **Reusable pgzero-compat shim, not per-game raw rewrites.** Build one
   GLFW+GL3.3 layer that provides the slice of the PyGame Zero API these games
   use (`Actor`, `screen`, `keyboard`/`keys`, `sounds`, `music`, `Rect`, the
   `update()`/`draw()` loop, `pgzrun.go()`). Each game is then a **near-verbatim
   copy of the original** with only its imports (and the version-check / mixer
   boilerplate) swapped. This maximises reuse and keeps each port diffable
   against the upstream file — important because these are *ports of someone
   else's code*, not new curriculum demos.

2. **Shim first, then one game per volume**, remaining games as follow-on tasks.
   Phase 1 here = build the shim + port **boing** as the proof. The other four
   Vol 1 games become Phase 2 sub-tasks once the shim is proven.

3. **Render text and audio in-stack, no pygame.** pgzero gets both from pygame;
   we don't take a pygame dependency. Text → a bitmap-font atlas drawn as
   textured quads (or imgui draw-lists as a fallback). Audio → one small library
   added to `requirements.txt` (see below).

Consistent with the existing SuperBible ports, the shim does **not** use the
curriculum's `InvertibleFunction`/Cayley-graph abstraction — these are ports, so
plain matrix/ortho math is fine (the abstraction is a teaching device for
demos 01–18, not a constraint on the ports tree).

---

## Proposed directory layout

```
ports/codetheclassics/              # umbrella
├── pgzero_gl/                      # the shared shim package (THIS task builds it)
│   ├── __init__.py                 #   re-exports Actor, screen, keyboard, keys, sounds, music, Rect, go
│   ├── runner.py                   #   GLFW window + 60 Hz update/draw loop + event dispatch
│   ├── actor.py                    #   Actor (anchored textured-quad sprite)
│   ├── screen.py                   #   screen.blit / fill / draw.{text,rect,line,circle,...}
│   ├── renderer.py                 #   sprite-quad + solid-color shaders, ortho pixel projection
│   ├── resources.py                #   image/sound loaders (attr access like pgzero), asset root
│   ├── input.py                    #   keyboard object + keys constants (GLFW key map)
│   ├── text.py                     #   bitmap-font atlas → draw.text
│   └── audio.py                    #   sounds + music on the chosen audio lib
├── vol1/                           # ← "subdirectory" for Vol 1 (the main 2 = vol1, vol2)
│   └── boing/
│       ├── boing.py                #   ported game
│       ├── images/  sounds/  music/   (this game's assets only — see Assets)
└── vol2/                           # built by the sibling task
```

Naming (`codetheclassics`, `pgzero_gl`, `vol1/vol2`) is a proposal — confirm
before scaffolding; trivial to change. Import pattern mirrors the superbible
ports' `_common.py` trick (`sys.path` insert to reach `pgzero_gl`).

---

## The shim spec (`pgzero_gl`)

Built against the actual PyGame Zero 1.2.1 source (studied 2026-06-24, cached at
`/tmp/pgzero-1.2.1/` this session; re-fetch with `pip download pgzero --no-deps
--no-binary :all:`). Match these semantics exactly so the ported games behave
identically:

### Coordinate system & rendering
- **Pixel space, origin top-left, y-down**, `WIDTH`×`HEIGHT` (boing 800×480).
  Build an **orthographic projection** mapping (0,0)→top-left, (WIDTH,HEIGHT)→
  bottom-right (i.e. flip y vs GL clip space). One 4×4 ortho; no perspective.
- Sprites are **textured quads** (two triangles) with a `vec4` tint/alpha
  uniform (default white, opaque). One shader pair for sprites, one for solid
  fills (rects/lines/polys). Track VAOs/VBOs for cleanup as demo21+ does.
- macOS core profile needs a non-zero VAO bound at all times (see demo22's
  `_default_vao` note) — replicate that.

### `Actor` (from `actor.py`; the contract the games depend on)
- `Actor(image_name, pos=topleft, anchor=center, **symbolic_pos)`. **Default
  anchor is center**; default position is topleft (0,0).
- `.image` is a *name* → loads `images/<name>.png` (loader strips/adds ext;
  pgzero tries `png gif jpg jpeg bmp`, lowercase-only). Setting `.image`
  re-loads and keeps `.pos` stable.
- Position API the games use: `.pos`, `.x`, `.y`, and **rect-delegated**
  attrs (`.topleft`, `.center`, `.width`, `.height`, `.midbottom`, …). pgzero
  delegates everything on `ZRect` — implement at least the ones the five games
  touch (audit: `grep -oE '\.(topleft|center|mid\w+|width|height|left|right|top|bottom)\b'`).
- `.angle` (degrees, CCW, y inverted) — rotate the quad about the anchor. boing/
  bunner/cavern don't use it; myriapod/soccer do (sprite facing). pgzero rotates
  the *surface* and recomputes the anchor offset (`transform_anchor`); the GL
  port rotates the quad — match the **visual** result, verify against original.
- `.draw()` blits at `.topleft`. `angle_to(target)`, `distance_to(target)`,
  `__iter__` (yields rect) — implement; some games iterate Actors as rects.

### `screen`
- `screen.blit(name_or_surface, pos)` — draw sprite at topleft `pos`.
- `screen.fill(color)`, `screen.clear()`.
- `screen.draw.text(...)`, `.rect(Rect,color)`, `.filled_rect`, `.line`,
  `.circle`, `.filled_circle`. Across **all 10 games** the draw.text kwargs used
  are: `color`, `fontsize`, `center`, `pos`, `topleft` (plus the ptext defaults).
  Only the Vol 2 games lean on text heavily; Vol 1 uses it in bunner/cavern/
  soccer only.
- **`screen.surface`** — bunner & soccer reach the raw pygame Surface directly
  (`set_clip`, `blit`). There is no CPU surface in GL. Map:
  `surface.set_clip(rect)` → `glScissor` + `GL_SCISSOR_TEST`;
  `surface.blit(img, pos)` → a sprite-quad draw. Provide a thin `screen.surface`
  facade exposing just `set_clip`, `blit`, `get_width/height`. (Vol 1 needs only
  these; Vol 2 needs more — that task extends the facade.)

### `keyboard` / `keys`
- `keyboard.<name>` boolean attribute access (`keyboard.space`, `.up`, `.z`,
  `.lctrl`, …). Back it with GLFW key state. Vol 1 keys used: space, up, down,
  left, right, z, a, m, k, escape, lctrl, lshift, x, c.
- `keys.SPACE`/`keys.UP`/… constants for the one `on_key_down` hook (bunner).
- Implement GLFW→pgzero key-name mapping once, in `input.py`.

### `sounds` / `music`
- `sounds.<name>` → a playable sound; `getattr(sounds, name+str(n))` pattern is
  used everywhere (random variant selection) — support attribute access that
  loads `sounds/<name>.{ogg,wav}` and caches, raising the same way on miss
  (games wrap in try/except, so graceful failure is fine).
- `music.play(name)`, `music.set_volume(v)`, `music.stop()`, `music.fadeout(t)`
  — streamed background track from `music/`.

### `Rect`
- A `pygame.Rect`-compatible rectangle (the games use `.colliderect`,
  `.contains`, `.collidepoint`, attrs). Either vendor a small pure-Python Rect
  or reuse pgzero's `ZRect` (it's standalone, ~500 LOC, MIT — but that re-imports
  pygame for color; a trimmed copy avoids that). Decide during impl.

### The loop / `pgzrun.go()`
- `clock.tick(60)`-equivalent fixed 60 FPS; call module `update()` (0-arg form
  these games use) then `draw()` each frame; dispatch `on_key_down`/etc. to
  module hooks if present; `keyboard` state updated from GLFW callbacks.
- The games end with `pgzrun.go()`; the shim provides `go()` that finds the
  caller module's `WIDTH/HEIGHT/TITLE/update/draw` and runs. Simplest port edit:
  replace `import pgzero, pgzrun, pygame` with `from pgzero_gl import *` (and a
  shim `pgzrun`/`pygame` stub for the `pygame.mixer.init` boilerplate at the
  bottom of each file — or just delete that block).

---

## Dependencies

Stay within the book/code stack: `glfw`, `PyOpenGL`, `numpy`, `imageio`,
`imgui_bundle`, `Pillow` are all already in `requirements.txt`. New pulls:

- **Text** — no new dep. Build a bitmap-font atlas at startup (render glyphs once
  to a texture; draw runs of textured quads). Pillow (already present) can
  rasterize a TTF to the atlas. Fallback if it gets fiddly: imgui draw-lists
  (imgui_bundle already present) can stamp text. Match ptext's default
  (center/topleft anchoring, color, fontsize); don't need ptext's full feature
  set — the games use a tiny subset.
- **Audio** — the one genuinely new dependency. Candidates: **`miniaudio`**
  (decodes ogg/wav/mp3, simple playback, few transitive deps — leading choice),
  or `soundfile`+`sounddevice` (libsndfile; ogg ok), or `pyopenal`. Needs:
  multiple simultaneous SFX + one streamed music track + per-source volume.
  **Note (host caveat):** CLAUDE.md flags that Bill's Fedora host runs the
  SDL2-compat-on-SDL3 shim which breaks SDL2 audio — so prefer an audio lib that
  does **not** route through SDL (another reason to avoid pygame.mixer here).
  Pick during Phase 1; add to `requirements.txt` **and** check whether it needs a
  Fedora `python3-*` distro package in the `Dockerfile` (per the "keep Dockerfile/
  Makefile/requirements in sync" rule in CLAUDE.md).

---

## Assets

Each game's `images/`/`sounds/`/`music/` live in its `*-master/` source dir.
boing's footprint is small; copy **just that game's** assets into
`ports/codetheclassics/vol1/boing/` so the port is self-contained (matches how
demo22 vendors its `.tga`s). Don't bulk-copy — Vol 1 is 843 PNGs across 5 games,
Vol 2 is 3382. The shim's resource loader takes a configurable asset root so a
game points at its own dir. (Asset copying is gated on the licensing blocker.)

---

## Phasing

### Phase 0 — licensing (blocker)
Resolve the redistribution/attribution question above. No game code or assets
committed until cleared.

### Phase 1 — shim + **boing** canary
1. Scaffold `ports/codetheclassics/pgzero_gl/` per the spec.
2. Sprite renderer + ortho pixel projection; get one textured quad on screen.
3. `Actor`, `screen.blit/fill`, `keyboard`, the 60 Hz loop, `go()`.
4. Audio lib chosen + `sounds`/`music`; text atlas + `draw.text`.
5. Port **boing**: copy `boing.py`, swap imports, drop the version-check + mixer
   boilerplate, point assets at the vendored `boing/images|sounds|music`.
6. Verify (see below). boing is ideal first: no `screen.surface`, no rotation,
   no masks, 2 trivial `pygame.*` refs — and it's Pong, which rhymes with the
   course's own running paddle scene.

### Phase 2 — remaining Vol 1 games (one follow-on sub-task each)
Order by added shim surface, easiest first:
- **cavern** — like boing; mainly more sprites + `draw.text`.
- **myriapod** — adds sprite **rotation/flip** (exercise `Actor.angle` + a
  flipped-quad path; the `transform` refs are sprite flips).
- **bunner** — adds `on_key_down` hook, `screen.surface.set_clip` (→ scissor),
  one `Rect`, `img.get_width`.
- **soccer** — heaviest: 10 `pygame.*` refs incl. `pygame.math.Vector`
  (replace with mathutils/gacalc vectors or plain tuples), `joystick`
  (→ GLFW joystick API), four `screen.surface` uses. Do last.

---

## Verification

On-screen GL **cannot be verified headless** in the nested container (no display/
GPU/xauth — same constraint as the rest of the repo; see CLAUDE.md). What CI/agent
work *can* do: byte-compile every ported file, import the shim, run the sprite
renderer against a hidden/offscreen GLFW context if one initializes, and unit-test
the pure logic (collision, AI, scoring — these are framework-independent). **Bill
verifies the actual window** (gameplay, audio, fonts). Build a 2–3 line "does it
launch + first frame renders" smoke check per game for him to run.

---

## Open questions
- Exact dir/package names (`codetheclassics`/`pgzero_gl`/`vol1`)?
- Audio library choice (leaning `miniaudio`) — confirm + Dockerfile distro pkg.
- Text: bitmap atlas vs imgui draw-lists — decide in Phase 1 against bunner/soccer.
- Vendor a trimmed `Rect` vs depend on the original behavior — decide in Phase 1.
- Should these ports get the superbible ports' imgui menubar/fullscreen `_common`
  treatment, or stay minimal? (Probably minimal — they have their own menus.)
