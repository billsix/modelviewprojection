# Code the Classics — GLFW + OpenGL 3.3 ports

Ports of the *Code the Classics* games (Raspberry Pi Press) from **PyGame Zero**
to **GLFW + OpenGL 3.3 core profile**, the rendering stack the ModelViewProjection
book ends on (cf. `demos/demo21`+). They live under `ports/` (like the SuperBible
ports), not in the curriculum proper: they are faithful translations, not
re-pedagogized demos.

- **Vol 1:** boing (plus `boing_gl1.py`, the same game on fixed-function OpenGL
  1.x), cavern, myriapod, bunner, soccer
- **Vol 2:** eggzy, avenger, beatstreets, kinetix, leadingedge

## Running a game

`[CONTAINER]` from the repo root, inside `make shell` (glfw, PyOpenGL and the
editable `modelviewprojection` install are there):

```sh
python ports/codetheclassics/vol1/boing/boing.py
PGZERO_MAX_FRAMES=120 python ports/codetheclassics/vol2/eggzy/eggzy.py  # auto-close after 120 frames
```

## Checking a change

`[HOST]` (or the dev sandbox) from the repo root; the scripts start the image
with podman, so they need it built (`make image`) and an X server on `:99`
(the dev sandbox's Xvfb):

```sh
tools/ctc_verify_game.sh ports/codetheclassics/vol1/boing/boing.py 180   # frame 180 pixel-identical to HEAD?
tools/ctc_state_trace.py <game.py> <frames> <keyscript>                   # scripted-input state dump (run in the container)
tools/ctc_compare_traces.py base.txt cur.txt                              # structural diff of two dumps
```

> Audio and gamepad input are never gated: check them by playing the game.

Details: `tasks/reference/tests-and-gates.md`.

## Layout

```
codetheclassics/
├── vol1/<game>/<game>.py   one game per file, with its own images/ sounds/ music/
└── vol2/<game>/<game>.py   (vol2 games also carry tilemaps/ etc. as needed)
```

Each game file reads top to bottom like the course's demos: its engine (the
renderer and shaders, `Actor`/`Rect`, keyboard and gamepad), then the game,
then the loop the game owns. The parts that are the same in every game import
from the package, `src/modelviewprojection/pgzero_gl/`: `audio` (the software
mixer), `resources` (`Image`, the asset `Loader`) and `gl` (shader and buffer
helpers, the pixel-space projection). The file shape and conventions:
`tasks/reference/code-the-classics-tightening.md`; the shared modules:
`tasks/reference/notable-subsystems.md` §4a.

## Licensing / attribution

- **Game code:** BSD-2-Clause, © Eben Upton (vol 1 2019, vol 2 2024), per the
  upstream Debian packaging; full text and the engine-code terms in `LICENSE`.
- **Shared engine modules** (`src/modelviewprojection/pgzero_gl/`): LGPL-2.1.
- **Graphics and audio:** © Raspberry Pi Press and the authors (graphics by Dan
  Malone; audio by Allister Brimble). Included for educational use within this
  course on the maintainer's authorization (2026-06-24).

> The upstream GitHub repos ship no licence file. If this tree is published,
> confirm redistribution of the assets with Raspberry Pi Press first.

- Vol 1: https://github.com/raspberrypipress/Code-the-Classics-Vol1
- Vol 2: https://github.com/raspberrypipress/Code-the-Classics-Vol2
- Book:  https://magazine.raspberrypi.com/books/code-the-classics-vol-I-2ed
