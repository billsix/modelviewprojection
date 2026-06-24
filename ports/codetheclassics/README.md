# Code the Classics — GLFW + OpenGL 3.3 ports

Ports of the *Code the Classics* games (Raspberry Pi Press) from **PyGame Zero**
to **GLFW + OpenGL 3.3 core profile** — the rendering stack the ModelViewProjection
book ends on (cf. `demos/demo21`+). The original games are 2-D sprite-blitters; the
math/3-D abstractions of the course don't apply, so these live under `ports/`
(like the SuperBible ports), not in the curriculum proper.

## ⚠️ Licensing / attribution

The upstream repos have **no license file** — under default copyright that is
*all rights reserved*. The original code, graphics, and audio are © **Raspberry
Pi Press** and the authors (Andrew Gillett, Eben Upton et al.; graphics by Dan
Malone; audio by Allister Brimble). These ports are included for **educational
use** within this course on Bill Six's authorization (2026-06-24). Every ported
file carries an attribution header linking back to the source. If this tree is
ever published, confirm redistribution permission with Raspberry Pi Press first.

- Vol 1: https://github.com/raspberrypipress/Code-the-Classics-Vol1
- Vol 2: https://github.com/raspberrypipress/Code-the-Classics-Vol2
- Book:  https://magazine.raspberrypi.com/books/code-the-classics-vol-I-2ed

## Layout

```
codetheclassics/
├── pgzero_gl/        shared shim: reimplements the slice of the PyGame Zero API
│                     the games use, on GLFW + OpenGL 3.3 core
├── vol1/<game>/      one ported game per dir, with its own images/sounds/music
└── vol2/<game>/      (vol2 games also vendor tilemaps/ etc. as needed)
```

## How `pgzero_gl` works

PyGame Zero injects `Actor`, `screen`, `keyboard`, `sounds`, `music`, ... as
magic globals and runs an `update()`/`draw()` loop at 60 Hz. The shim provides
the same names; a ported game is a **near-verbatim copy of the original** whose
only change is its first import line:

```python
import pygame, pgzero, pgzrun          # original
from pgzero_gl import *                 # port  (+ a sys.path line to find the shim)
```

The shim reproduces PyGame Zero's top-left-origin, y-down **pixel coordinate
system** with an orthographic projection and draws every sprite as a textured
quad, so the game's original pixel coordinates work unchanged. Notable pieces:

- `renderer.py` — GL 3.3 sprite + flat-colour shaders, pixel-space ortho,
  atlas sub-rect sampling (`area=`), scissor for `set_clip`.
- `actor.py` / `geometry.py` — `Actor` (centre-anchored sprite), `Rect`,
  `Vector2`.
- `resources.py` — image/sound loaders; images decode to CPU pixels immediately
  (game objects are built at import, before the window exists) and upload their
  GL texture lazily on first draw.
- `text.py` — `screen.draw.text` via a Pillow-rendered glyph bitmap (no pygame).
- `audio.py` — `sounds`/`music` via `just_playback` (miniaudio); **best-effort**,
  silently no-ops if no audio backend/device, like the originals.
- `input.py` / `joystick.py` — `keyboard`/`keys` and gamepad, backed by GLFW.

## Running a game

Inside the project's container (which has glfw + PyOpenGL + a display):

```sh
python src/.../  # the usual env, then:
python ports/codetheclassics/vol1/boing/boing.py
python ports/codetheclassics/vol2/eggzy/eggzy.py
```

### Renderer backends

Default is **OpenGL 3.3 core + shaders** (`renderer.py`). Set `PGZERO_GL=1` to use
the **fixed-function OpenGL 1.x** backend instead (`renderer_gl1.py` — `glOrtho` +
`glBegin/glEnd`, the demo19 era), for old/compat-only GL stacks:

```sh
PGZERO_GL=1 python ports/codetheclassics/vol1/boing/boing.py
```

Both produce the same picture (verify with `_smoketest.py <game> --gl1`).

Verified on real hardware: AMD Radeon RX 7600 XT (radeonsi, Mesa 26, GL 4.6
Compatibility Profile) — the fixed-function backend runs on the GPU's compat
context.

#### Checking it on your hardware

Two env vars help confirm a real-GPU run:

- `PGZERO_GL_INFO=1` — prints the active backend + real `GL_VERSION`/`GL_RENDERER`
  at startup (confirms GPU vs software, and which renderer path is live).
- `PGZERO_MAX_FRAMES=N` — auto-closes after N frames, for unattended sweeps.

```sh
cd ports/codetheclassics

# one game, watch it (look for backend=gl1-fixedfunc + a real GL_RENDERER):
PGZERO_GL=1 PGZERO_GL_INFO=1 python vol1/boing/boing.py

# all ten, unattended (each window flashes ~2s then closes):
for g in vol1/*/*.py vol2/*/*.py; do
  echo "=== $g ==="
  PGZERO_GL=1 PGZERO_GL_INFO=1 PGZERO_MAX_FRAMES=120 python "$g" || echo "FAILED: $g"
done
```

Audio and gamepad input require a real device and are **verified by hand**.
**Rendering, though, can be checked headless** — `_smoketest.py` renders one
frame to an offscreen EGL pbuffer (Mesa llvmpipe, no display/GPU) and writes a
PNG:

```sh
python _smoketest.py vol1/boing/boing.py     # -> /tmp/boing.png
python _smoketest.py vol2/eggzy/eggzy.py      # -> /tmp/eggzy.png
```

It exits non-zero if the frame is mostly black, so it doubles as a CI guard.
Game *logic* (and eggzy's Tiled-map loading) is covered by import/run tests.

## Games

All ten are ported and render-verified (headless EGL):

- **Vol 1:** boing, cavern, myriapod, bunner, soccer
- **Vol 2:** eggzy, avenger, beatstreets, kinetix, leadingedge

The shim covers `Actor`, `screen` (`blit`/`fill`/`draw.{text,rect,filled_rect,
line,circle,polygon}`/`surface` with `set_clip` + atlas `area=` blits),
`keyboard`/`keys`, `sounds`/`music`, `Rect`/`Vector2`/`Vector3`, a CPU-buffer
`Surface`, `mask`, gamepad (`joystick`), and stub `pygame`/`pgzrun`/`pgzero`
modules (with real `pygame.*` submodules registered so `from pygame.math import
Vector2` etc. resolve). Each game file is byte-identical to upstream except a
prepended bootstrap + a cleaned import line.

## Status

See `tasks/port-codetheclassics-vol1.md`, `tasks/port-codetheclassics-vol2.md`,
and `tasks/pgzero-gl-opengl1-renderer.md` (a proposed fixed-function renderer
backend). Remaining: human verification of full gameplay + audio on a real
display/device.
