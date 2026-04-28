# Postmortem: Phase 2 (walk-around camera) — first attempt, reverted 2026-04-29

**Status:** ❌ rolled back via `git reset`. Tasks #38 and #39 returned to `pending`. Phase 1 (#33/#34 menubar + window size) was untouched and remains in place.

**Why this file exists:** save the design that worked on the canary, the bugs that broke the bulk pass, and the corrections to make next time. The Camera-class code itself was lost in the reset; it's described below in enough detail to re-implement.

## What I had built in `_common.py` (lost; re-implement next time)

```python
@dataclass
class SceneObject:
    name: str
    position: Callable[[], Tuple[float, float, float]]   # callable so animated
                                                          # objects keep tracking

@dataclass
class Camera:
    position: List[float] = field(default_factory=lambda: [0.0, 0.0, 10.0])
    rot_y: float = 0.0          # angle around world Y, radians
    rot_x: float = 0.0          # angle around camera-local X, radians, clamped ±π/2
    focus_index: int = -1        # -1 = walk-around; ≥ 0 = orbit scene_objects[i]
    focus_radius: float = 25.0
    move_speed: float = 1.0
    look_step: float = math.radians(2.0)
    mouse_look_speed: float = 0.005
    scroll_speed: float = 1.0
    _prev_mouse: Optional[Tuple[float, float]] = None
    _scroll_accum: float = 0.0


def bind_camera_inputs(window, camera):
    # Register scroll cb that chains with previous (so imgui's scroll
    # callback isn't clobbered).
    prev_cb = glfw.set_scroll_callback(window, None)   # ⚠ see "Bug 1"
    def cb(_w, x, y):
        camera._scroll_accum += y
        if prev_cb: prev_cb(_w, x, y)
    glfw.set_scroll_callback(window, cb)


def update_camera(window, camera, scene_objects):
    io = imgui.get_io()
    # WASD/QE keys (when not io.want_capture_keyboard)
    # Arrow keys for look
    # Left-mouse drag for look (when not io.want_capture_mouse)
    # Scroll: forward/back in walk-around, radius in focus
    # Clamp rot_x ±π/2

def apply_camera(camera, scene_objects):
    if 0 <= camera.focus_index < len(scene_objects):
        ox, oy, oz = scene_objects[camera.focus_index].position()
        GL.glTranslatef(0, 0, -camera.focus_radius)
        GL.glRotatef(math.degrees(camera.rot_x), 1, 0, 0)
        GL.glRotatef(math.degrees(-camera.rot_y), 0, 1, 0)
        GL.glTranslatef(-ox, -oy, -oz)
    else:
        GL.glRotatef(math.degrees(-camera.rot_x), 1, 0, 0)
        GL.glRotatef(math.degrees(-camera.rot_y), 0, 1, 0)
        GL.glTranslatef(-camera.position[0], -camera.position[1], -camera.position[2])

def draw_camera_controls(camera, scene_objects, state: WindowState):
    if not state.show_camera_controls: return
    expanded, state.show_camera_controls = imgui.begin(
        "Camera", state.show_camera_controls)
    # ... mode display, position/radius display, radio buttons for focus,
    # text reminder of WASD/QE/arrows/scroll bindings ...
    imgui.end()
```

`WindowState` got a `show_camera_controls: bool = False` field. `draw_menubar` got a `has_camera_controls=False` keyword arg; when True it adds a "Show Controls" menu_item under View bound to `state.show_camera_controls`.

## The canary worked

**`chapt08/sphereworld`** was migrated by hand and Bill confirmed "that's good enough for now." The exact form:

```python
camera = _common.Camera(
    position=[0.0, 0.5, 6.0],
    rot_y=0.0,
    rot_x=math.radians(-5.0),
    move_speed=0.2,
    scroll_speed=0.5,
    focus_radius=4.0,
)
def torus_orbiter_position():
    angle = math.radians(-y_rot * 2.0)
    return (math.cos(angle), 0.1, -2.5 - math.sin(angle))
scene_objects = [
    _common.SceneObject("Torus (center)", lambda: (0.0, 0.1, -2.5)),
    _common.SceneObject("Torus orbiter", torus_orbiter_position),
    _common.SceneObject("Ground center", lambda: (0.0, -0.4, 0.0)),
]
```

In `main()`: `_common.bind_camera_inputs(window, camera)` after `_common.init_imgui`. In the loop: `_common.update_camera(window, camera, scene_objects)` after `impl.process_inputs()`, then existing `render_scene()` (which called `_common.apply_camera(camera, scene_objects)` instead of the old `apply_camera_transform`). `_common.draw_menubar(window, win_state, has_camera_controls=True)` and `_common.draw_camera_controls(camera, scene_objects, win_state)` before `imgui.render()`.

Smoke test passed. Walk-around with WASD/QE worked, arrow-look worked, mouse-drag look worked, focus radio buttons worked, "Torus orbiter" tracked the animated position correctly.

## Why the bulk pass broke

**Bug 1: body-replacement regex was fragile.** The migration script's `neutralize_handle_camera_keys` regex pattern was:

```python
r"def handle_camera_keys\(window\)[^:]*:\n"
r"(?:[ \t]+(?:global\s+[^\n]+|if\s+glfw\.[^\n]+|[ \t]*camera_[xyz][^\n]*|else:[^\n]*)\n)+"
```

This expected each body line to start with `global`, `if glfw.`, `else:`, or `camera_x`. But many demos had `move_step = 0.1` (local-var assignment) before the if-blocks. The non-greedy alternation didn't match that, so the regex consumed only `def handle_camera_keys(window) -> None:\n` and inserted `pass` — but **left the rest of the original body untouched**. Result:

```python
def handle_camera_keys(window) -> None:
    pass  # camera now driven by _common.update_camera
    move_step = 0.1                                   # ← orphan, but valid syntax
    rot_step = 0.1                                    # ← orphan
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera_x += move_step * math.sin(camera_yaw)  # ← NameError at runtime
        camera_z += -move_step * math.cos(camera_yaw)
    ...
```

The file compiled clean (the orphan code is syntactically valid), so my "all 100 files compile" check passed. At runtime, `camera_x` etc. are undefined, the function raises `NameError` on every frame. **This is why "controls weren't working".**

The same flavor of bug hit `apply_camera_transform` in `chapt04/sphereworld` (had a docstring my regex didn't account for) — function was left with the OLD `glRotatef(-math.degrees(camera_yaw), ...)` that referenced now-replaced globals.

**Bug 2: hand-fixes I added re-broke the bulk-script-touched files.** I tried to clean up 4 stragglers manually (`chapt04/sphereworld`, `chapt05/sphereworld`, `chapt06/sphereworld`, `chapt19/SphereWorld32`) — those got fixed. But the same bug pattern was present in OTHER migrated files that I didn't see because my "stale ref" grep only flagged files where the bad code was at the top level. Function-internal `camera_x` references slipped through.

**Bug 3: scroll callback chaining is suspect.** `glfw.set_scroll_callback(window, None)` returns the *previous* callback in some bindings but I never confirmed it does in `python-glfw`. If it returns `None`, our chain silently swallowed imgui's scroll callback, breaking imgui scroll behavior in panels. Worth testing in isolation before re-doing.

**Bug 4: imgui mouse-drag interaction wasn't carefully tested.** `update_camera` reads `glfw.get_mouse_button(...)` directly and only gates on `io.want_capture_mouse`. If the user starts a drag inside the Camera panel and then drags out into the viewport, `want_capture_mouse` flips from True to False mid-drag and `_prev_mouse` resync is jittery. Probably fine on the canary; shows up worse on demos with more imgui content.

**Bug 5: scope of "what counts as 3D" was too aggressive.** I tried to migrate the explicit-cam group plus sphereworld variants in one pass — that's 24 files. Each demo had small per-demo specifics (e.g., `chapt09/cubemap` reads `camera_yaw` to inverse-rotate the texture matrix for cubemap reflections). The script handled the standard pattern but left these cases referencing dead variables. They compiled, ran, and silently displayed wrong reflections.

## What to do differently next attempt

1. **Hand-migrate one demo per pattern group, verify each, before any bulk pass.** Phase 1 had mostly-uniform structure (every demo opens a window, has a main loop, calls swap_buffers). Phase 2 patterns are more varied — `cameraPos = [...]` + `gluLookAt` is one pattern, `camera_x/y/z/yaw` + `apply_camera_transform()` is another, inlined transform in `render_scene` is a third. Verify each pattern group on a single demo first.

2. **Don't body-replace functions with regex.** Either:
   - **(a)** Hand-edit each function. With ~25 files this is annoying but reliable.
   - **(b)** Use `libcst` (concrete syntax tree) — has a Python AST that preserves comments/whitespace and lets you replace function bodies surgically. This is the right tool for "replace body of function `apply_camera_transform`".
   - **(c)** A regex that anchors on the *next* `def `/top-level keyword AFTER the target function, and replaces everything between. E.g., `r"def apply_camera_transform.*?(?=^\S|^def )"` with `re.DOTALL` and `re.MULTILINE`. More fragile than libcst but no new dep.

3. **After any bulk migration, grep for ALL references to the replaced names** (`camera_x`, `camera_y`, `camera_z`, `camera_yaw`, `camera_pos[`) — including inside function bodies. Don't just `compile()`. Use `grep -n` on the migrated tree. If any reference remains, that file is broken even if it compiles.

4. **Verify `glfw.set_scroll_callback(window, None)` actually returns the previous callback** in `python-glfw`. If not, change strategy: have `bind_camera_inputs` accept the GlfwRenderer's scroll callback as an explicit arg, or just install our scroll callback FIRST (before `init_imgui`) and let imgui chain off it.

5. **Per-demo gotchas to watch for:**
   - `chapt09/cubemap` uses `camera_yaw` to inverse-rotate the cube-map texture matrix for reflections. Replacement is `camera.rot_y`. (I caught this one.)
   - `chapt19/SphereWorld32` inlines the camera transform in `render_scene` rather than via a named helper. (I caught this one too, but only after a stale-ref grep.)
   - `chapt04/sphereworld` and `chapt06/sphereworld` had docstrings in `apply_camera_transform` / `handle_camera_keys` that broke the strict regex.
   - Demos in the static-or-rotate group don't have a movable camera at all — they push the scene back with `glTranslatef(0,0,-N)` and rotate objects. Migrating those means changing their pedagogy: arrow keys go from "rotate this object" to "rotate the camera." For demos like `chapt04/transform`, `chapt04/transformgl` that are *about* object rotation, this is probably wrong; ask Bill before migrating them.

6. **Consider reducing scope.** Maybe Phase 2's first goal should be just "fix sphereworld variants" (~10 files, all near-identical). Once those work end-to-end (not just compile), expand to the cameraPos shader-era group. The mistake last time was treating both groups as one bulk pass.

## Inventory snapshot (for reference; was correct as of 2026-04-29)

- **3D[explicit-cam]** (24 ports): camera_pos array + gluLookAt, OR camera_x/y/z/yaw + apply_camera_transform. Migrate first.
- **3D[static-or-rotate]** (~25 ports): no movable camera. Migrate cautiously; some are explicitly demos about object rotation.
- **3D[lookat]** (1 port): chapt19/Text3D. Hand-migrate.
- **2D / stub** (~50 ports): skip.

Full file list is in this conversation's transcript or via:
```
find /mvp/ports/openglsuperbiblev4 -name "*.py" -not -name "_*" | xargs grep -l "gluPerspective\|glFrustum"
```
