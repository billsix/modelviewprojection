# Task: investigate de-duplicating the per-demo `handle_inputs`

**Status:** investigated 2026-05-27 — refined approach below; **execution
deferred** (Bill will revisit another day). No code changed. **Type:** refactor
of `src/modelviewprojection/demo*.py`, book-coupled. Spun off from
[`extract-duplicated-demo-helpers.md`](extract-duplicated-demo-helpers.md).

## Context
`handle_inputs` is the per-frame, key-*polling* function each demo calls in its
event loop (`glfw.get_key(window, KEY_X) == glfw.PRESS` → mutate state). Unlike
`on_key` (the discrete escape-to-quit callback, now shared in
`windowing.py`), `handle_inputs` is **genuinely different per demo**: measured at
**21 copies / 18 distinct variants**. So it is *not* a copy-paste-identical case
like `on_key`/`draw_in_square_viewport` — most of it is pedagogically meaningful
(each demo wires up the keys relevant to what it teaches: paddle move, square
rotate, camera placement, jet yaw/pitch, etc.).

## Findings (2026-05-27): the "camera-walk" block is THREE idioms, not one
Clustering all `handle_inputs` by key-set and comparing the camera blocks (13
demos carry the 6 walk keys) shows they map to *different teaching stages*:

1. **Function / Vector style — `demo17`, `demo18` (2).** Forward motion uses the
   course abstraction: `camera.position_ws` + `compose([translate(...),
   rotate_y(...)])` — the InvertibleFunction approach the book is teaching there.
2. **Raw-float / GL style — `demo19, 20, 21, 22, 22a, 23, 24` (7).** Forward
   motion is `camera.x/z` with `math.sin/cos(camera.rot_y)`. These 7 are
   **identical except the `move_step` constant** (and trailing paddle keys), and
   already share the `camera.x/z/rot_x/rot_y` dataclass shape.
3. **Orbit — `demo19a`(–d) (~4).** Different semantics: `PAGE_UP/DOWN` change
   `camera_distance`, rotation tracked as `x_rot/y_rot`. Not walk-around.

Plus per-demo **paddle-move** (`W/S`,`A/D`,`I/K`,`J/L`) and **square-rotate**
(`Q/E`) blocks in the 2D demos — those *are* the lesson; leave inline.

## Recommended approach (conservative)
- **Extract only cluster #2** (the 7 raw-float walk demos) into
  `walk_around_camera(window, camera, move_step)` — new `cameracontrols.py` (or
  fold into `windowing.py`). Each demo replaces its inline block with
  `walk_around_camera(window, camera, move_step=<its value>)` (the only real
  difference becomes the parameter).
  - **Order:** `demo22, 22a, 23, 24` are **not** book-referenced → do these first
    (zero chapter impact, proves it out). `demo19, 20, 21` ARE chapter-referenced
    → then coordinate their `literalinclude`s (teach-once: whichever chapter
    introduces the GL walk-camera keeps it inline).
  - **Use the same helper for the ports** — this is exactly
    [`ports-walkaround-camera.md`](ports-walkaround-camera.md)'s logic; share one.
- **Leave inline:** #1 (demo17/18 — teaches the InvertibleFunction abstraction;
  only 2 demos), #3 (orbit — different behavior), and all paddle/square blocks.
- **Net:** ~85 lines of true duplication removed across the 7 GL demos; one place
  to tune camera feel; the teaching parts untouched.

## Book coupling
`handle_inputs` IS shown via `literalinclude` in several chapters (ch05 "Handling
User Input", ch06 "define handle movement of paddles", ch10+, and the 3D
chapters). Extracting the camera-walk sub-block changes what ch19/20/21 display →
coordinate those (teach-once-then-import). The non-book demos (22–24) have no such
constraint.

## Decisions for Bill (when he revisits)
- Confirm the conservative scope (only the 7 raw-float walk demos).
- Module name: `cameracontrols.py` vs. adding `walk_around_camera` to `windowing.py`.
- Share one helper with `ports-walkaround-camera.md`? (recommended.)
- Verify `demo19b/c/d` are orbit (assumed — only `demo19a` was inspected) before
  excluding them from the extraction.

## Verification (when done)
`pytest`, `ruff`, `py_compile` each touched demo; Bill runs the GL demos (no
display / glfw in the container). For book-referenced demos, Bill's `make html`
confirms the updated `literalinclude`s.
