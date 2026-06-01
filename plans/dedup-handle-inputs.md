# Task: de-duplicate the per-demo camera-walk block of `handle_inputs`

**Status:** Phase A + B done 2026-06-01 (staged, not committed) — pending
Bill's visual check of all 10 converted demos. **Type:** refactor of
`src/modelviewprojection/demo*.py`, book-coupled. Spun off from
[`extract-duplicated-demo-helpers.md`](extract-duplicated-demo-helpers.md).

## Progress
- **2026-06-01 — Phase A DONE (staged, not committed).** Created
  `src/modelviewprojection/cameracontrols.py` with `walk_around_camera(window,
  camera, move_step)` (LEFT/RIGHT yaw, PAGE_UP/PAGE_DOWN pitch, UP/DOWN walk).
  Replaced the inline walk block in **6 demos**: demo20, 21 (book — ch20 only
  slices doc-regions, doesn't show the walk block; ch21 dumps the whole file
  and now shows the import call, which actually reinforces teach-once),
  demo22, 22a, 23, 24 (no book chapters). **demo19 kept inline** as the
  teach-once anchor (first GL walk-camera demo, taught in ch19).
  **demo19e dropped from this batch** — it uses FPS-style W/A/S/D instead of
  arrow keys (sphereworld convention), and the helper is arrow-key-only.
  Verified: py_compile clean on all 7 touched files; pytest 47/47; ruff
  clean on `cameracontrols.py`; the 3 ruff errors in demo20/21/24 are
  pre-existing (confirmed by `git stash` + re-run). Net diff: +16/−99 across
  the 6 demos, plus ~40 lines of new helper. **Bill needs to run the 6 GL
  demos to confirm visually.**
- **demo19e** — re-classified 2026-06-01 per Bill: "make it consistent with
  the rest." Swapped WASD→arrow keys and converted to
  `walk_around_camera(window, camera, move_step=0.15)`. Header comment
  updated to match the standard scheme. Sphereworld now uses the same
  control idiom as the other 3D demos.
- **2026-06-01 — Phase B DONE (staged, not committed).** Converted
  **demo19a (axes3d)**, **demo19b (atom)**, **demo19c (solar)**, and
  **demo19d (moons)** from orbit (`x_rot`/`y_rot`/`camera_distance` globals)
  to walk-around (a `Camera` dataclass instance + `walk_around_camera()`).
  Per-demo changes:
  - Added `import dataclasses` and the `cameracontrols` import.
  - Replaced the three globals with a `Camera` dataclass (`x`, `y`, `z`,
    `rot_y`, `rot_x`) and an instance whose `z` matches the demo's old
    `camera_distance` default (5 / 25 / 60 / 90). `rot_x`/`rot_y` start at 0
    so the scene is dead-center at launch.
  - Replaced `handle_inputs` with a one-line call to `walk_around_camera`
    with a per-demo `move_step` (0.1 / 0.5 / 2.0 / 3.0, scaled to each
    scene's size).
  - Swapped the modelview transform from the orbit pattern
    (`translate(0,0,-distance) → rotate_x → rotate_y`) to the walk-around
    pattern (`rotate_x(-rot_x) → rotate_y(-rot_y) → translate(-x,-y,-z)`).
    The sign flip is because walk-around rotates the world opposite the
    camera's heading rather than rotating the world around its own origin.
  - Updated the controls comment in each header.
  Verified: py_compile clean on all 4; pytest 47/47; ruff clean on all 4.
  Net diff: +85/−87 across 4 files. **Bill needs to run all 4 GL demos to
  confirm the SuperBible scene's visual content is preserved.** Expected
  starting view at t=0: dead-center on the scene (axes / nucleus + electrons
  / sun-earth-moon / sun + planets-with-moons) at the same camera distance
  as the old orbit defaults; the rotated/pitched starting frame is gone
  (user rotates from there with arrows).

## Context
`handle_inputs` is the per-frame key-*polling* function each demo calls in its
event loop (`glfw.get_key(window, KEY_X) == glfw.PRESS` → mutate state). Unlike
`on_key` (the discrete escape-to-quit callback, now shared in `windowing.py`),
`handle_inputs` is **genuinely different per demo** — measured at 21 copies /
18 distinct variants — because the keys it wires up are part of the lesson
(paddle move, square rotate, camera placement, etc.). The dedup target is **not**
`handle_inputs` itself, but the camera-walk *sub-block* that's repeated identically
across the 3D demos.

## Findings: the camera-walk block is THREE idioms
Clustering the 13 demos that carry the 6 walk keys, by code shape:

| # | Idiom | Demos | Notes |
|---|-------|-------|-------|
| 1 | Function/Vector | `demo17`, `demo18` (2) | `camera.position_ws` + `compose([translate(...), rotate_y(...)])` — the InvertibleFunction abstraction the book is *teaching* there. |
| 2 | **Raw-float / GL** | `demo19`, `20`, `21`, `22`, `22a`, `23`, `24`, **`19e`** (8) | `camera.x/z` + `math.sin/cos(camera.rot_y)`. Identical across all 8 except the `move_step` constant (and trailing paddle keys in `demo19/20/21/22`). |
| 3 | Orbit | `demo19a`, `19b`, `19c`, `19d` (4) | `camera_distance` + `x_rot`/`y_rot` + PAGE_UP/DOWN. **Converting these to walk-around** (decision below) so they join cluster #2. |

Per-demo paddle-move (`W/S`,`A/D`,`I/K`,`J/L`) and square-rotate (`Q/E`) blocks
are part of the lesson — leave inline.

## Decisions confirmed (2026-06-01)
1. **Scope: the 8 raw-float walk demos + the 4 orbit demos converted.** Cluster
   #1 (demo17/18) stays inline — it teaches the InvertibleFunction abstraction.
2. **Module: new `src/modelviewprojection/cameracontrols.py`** (per-concept
   sibling of `mathutils.py`, matching the `clipping.py`/`windowing.py`/
   `shading.py` pattern from the parent plan).
   *(Read of "sure" as the first option in the question; redirect if you meant
   fold into `windowing.py` instead.)*
3. **Ports tree gets its own helper.** No code shared with
   [`ports-walkaround-camera.md`](ports-walkaround-camera.md); the ports tree's
   `_common.py` already exists. Curriculum and ports stay independent.
4. **Convert demo19a/b/c/d (axes3d/atom/solar/19d) from orbit to walk-around.**
   These should behave like the rest of the 3D demos. None has a book chapter
   (they're SuperBible ports, demo19a–e have no `chNN.rst`), so the conversion
   is risk-free book-wise.

## Helper signature
```python
# src/modelviewprojection/cameracontrols.py
def walk_around_camera(window, camera, move_step: float) -> None:
    """Per-frame WASD/arrow camera polling for the raw-float walk idiom.

    Reads UP/DOWN/LEFT/RIGHT; mutates ``camera.x``, ``camera.z``,
    ``camera.rot_y`` (sin/cos forward motion + yaw turn). The camera
    object must expose ``x``, ``z``, ``rot_y`` floats — matches the
    ``Camera`` dataclass used by demo19–24.
    """
```
Bodily identical to the existing cluster-#2 block; `move_step` is the only
per-demo knob.

## Per-demo rollout plan

### Phase A — easy wins (cluster #2, no behavior change)
Replace the inline walk block with `walk_around_camera(window, camera, move_step=...)`.
Eight demos:

- **demo22, 22a, 23, 24** — no book chapter → zero risk, do these first.
- **demo19, 20, 21** — book-referenced. Teach-once: whichever of these chapters
  introduces the GL walk-camera keeps its inline definition; the others'
  `literalinclude`s repoint at the import line.
- **demo19e** — no book chapter (SuperBible sphereworld port); already cluster
  #2, just drop in the helper.

### Phase B — orbit-to-walk-around conversion (cluster #3)
Four demos: **demo19a, 19b, 19c, 19d**. None book-referenced. For each:

1. Replace state — drop `x_rot`/`y_rot`/`camera_distance` globals, add a
   `Camera` dataclass instance (same shape as the cluster #2 demos:
   `x`, `y`, `z`, `rot_y`). Pick a starting `camera.z` that gives a similar
   default framing (e.g. demo19a's `camera_distance=5.0` → `camera.z=5.0`).
2. Replace modelview transform — swap
   `glTranslatef(0, 0, -camera_distance); glRotatef(x_rot, 1,0,0); glRotatef(y_rot, 0,1,0)`
   for the walk-around pattern
   `glRotatef(-degrees(camera.rot_y), 0,1,0); glTranslatef(-camera.x, -camera.y, -camera.z)`.
3. Replace input wiring — drop the orbit polling (PAGE_UP/DOWN distance,
   arrow rotation around origin) and call `walk_around_camera(window, camera, move_step=...)`.
   `move_step` chosen per-demo to feel similar to the previous orbit speed at
   typical viewing distance (demo19c's solar system is large → bigger step than
   demo19a's axes).
4. Confirm the SuperBible scene's key visual is preserved (axes3d shows the
   axis triplet; atom shows orbits; solar shows the sun-earth-moon nest;
   demo19d shows whatever it shows — to be verified during the conversion).

## Book coupling
`handle_inputs` is shown via `literalinclude` in ch05 ("Handling User Input"),
ch06 ("define handle movement of paddles"), ch10+, and the 3D chapters. After
Phase A, the displayed bodies in ch19/20/21 change (one of them keeps the inline
walk block; the others show the import). Coordinate when those phase-A book
demos land. Phase B's four demos have no chapter → no book edits.

## Verification
- After each extraction: `pytest`, `ruff check`, `py_compile` on each touched demo.
- For book-referenced demos (phase A's demo19/20/21), Bill's `make html`
  confirms the updated `literalinclude`s resolve.
- For phase B's behavior conversion, Bill runs the GL demos visually
  (no display / glfw in the container). The pass criterion is: the
  SuperBible scene's pedagogical content is preserved, with walk-around
  controls replacing orbit controls.

## Estimated diff
- Phase A (cluster #2, 8 demos): ~85 lines of true duplication removed, replaced
  with 1 import + 1 call per demo. ~+16 / −85 = net **−69 lines**.
- Phase B (cluster #3, 4 demos): per-demo state/transform/input rewrite,
  ~ +5 / −12 each. ~+20 / −48 = net **−28 lines** plus a behavior change.
- New file `cameracontrols.py`: ~15 lines.
- **Total: ~−82 lines net**, plus 4 demos changed in behavior.
