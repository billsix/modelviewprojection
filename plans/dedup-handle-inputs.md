# Task: de-duplicate the per-demo camera-walk block of `handle_inputs`

**Status:** ready to execute (decisions confirmed 2026-06-01). No code changed
yet. **Type:** refactor of `src/modelviewprojection/demo*.py`, book-coupled.
Spun off from [`extract-duplicated-demo-helpers.md`](extract-duplicated-demo-helpers.md).

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
