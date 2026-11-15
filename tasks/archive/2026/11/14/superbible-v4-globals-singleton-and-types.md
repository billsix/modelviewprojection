# SuperBible v4 ports: per-app `AppState` singleton dataclass + full types

**Created:** 2026-10-23 (William Emerison Six <billsix@gmail.com>). **Done:** 2026-11-14, except the
host verification owed below.

## Outcome

Every app under `ports/openglsuperbiblev4/` keeps its mutable state in one
`@dataclasses.dataclass class AppState` with one module-level instance `state: AppState = AppState()`,
and every reference goes through it. No `global` or `nonlocal` statement remains in the tree (there
were 364). Everything is annotated, including the sites `tools/check_local_annotations.py` exempts:
tuple unpacks, `for` and `with ... as` targets, and every def parameter and return. Committed one
commit per chapter (the shared helpers with chapt01/02's model file first). The course demos,
`src/modelviewprojection/` and the book were not touched; no port file is a book `literalinclude`
source (no `doc-region` markers under the tree).

## Decisions (William Emerison Six <billsix@gmail.com>, 2026-11-14)

1. One module-level instance per app: class `AppState`, instance `state`. GLFW callbacks keep their
   fixed signatures and reach the state through `state`; the window handle is `state.window`.
2. Genuine constants (never rebound, never mutated after import) stay module-level annotated
   constants under their current names; only mutable state goes in the dataclass.
3. Unpack sites use an annotated intermediate plus indexed reads:
   `size: tuple[int, int] = glfw.get_framebuffer_size(window)`, then `size[0]`, `size[1]`.
   The same form covers imgui's `(changed, value)` returns.
4. `ty` stays out of scope: the tree is not ty-checked (see
   `tasks/reference/tests-and-gates.md` §5), so the annotations were checked by reading and by the
   annotation checkers.

## How it was done

- `bounce.py` was refactored by hand first as the model, then the shared helpers `_common.py` and
  `_primitives.py` (annotations only; neither holds app state — `_common._view_states` is a
  per-window cache mutated in place, left module-level). The 101 apps were then refactored in
  seven parallel batches of chapters, each batch verified with the three checks below before it was
  accepted.
- The two checks below were one-shot scripts, committed in aca4865d and removed when the task was
  archived. `tasks/adhoc/superbible-v4-globals-singleton-and-types/strict_annotations.py` reported
  `global`/`nonlocal`, tuple-unpack assignments, unannotated `for`/`with` targets, and unannotated
  params/returns: 1335 findings before, 0 after.
- `tasks/adhoc/superbible-v4-globals-singleton-and-types/frame_identity.sh` +
  `capture_frames.py` ran an app headlessly for 12 frames under Xvfb with a fake clock
  (`time.monotonic`/`time`/`perf_counter`/`glfw.get_time` = frames / 30) and seeded `random`, and
  compare frames 3 and 12 with the pre-refactor commit's tree (baseline captured twice as a
  determinism check). A deliberate one-value change was confirmed to show as `DIFF`.

## Verification

- `make format` and `make type-check` green on the whole tree (the type-check gate runs the
  annotation checker over the ports).
- Frame identity, against the pre-refactor commit: 89 apps `SAME`. Not checkable headlessly, with
  the baseline failing identically:
  - `chapt03/single/single.py`: single-buffered and redraws only when the clock passes its tick, so
    the fake clock (which advances per frame) never produces a frame; killed at 120 s in both trees.
  - `chapt06/motionblur/motionblur.py`: `GLError 1282` on `glAccum` (Xvfb has no accumulation
    buffer).
  - `chapt18/hdrbloom/hdrbloom.py`: `GLError 1282` on `glReadPixels` into a bound PBO (see below).
  - `chapt18/texfloat/texfloat.py`: `OSError` — imageio has no EXR backend in the image.
  - `chapt21/fonts/font.py`: `imgui.set_window_font_scale` does not exist in this imgui_bundle.
  - Stubs with no state, left unchanged: `chapt19/GLView`, `chapt19/RThread`, `chapt20/*`,
    `chapt22/ES_example`.
- **Owed by the maintainer:** display, audio and gamepad checks on host GL (the agent cannot run
  them): open a sample of apps from each chapter, exercise the menubar Controls, F11, and the keys,
  especially the five apps above that headless runs could not reach.

## Judgment calls

- **State vs constant.** State = anything rebound from a function or mutated in place at run time
  (GL ids assigned in setup, lists filled in `setup_rc`, `camera_pos` lists nudged by keys, numpy
  arrays written in place, `_common.Camera`/`WindowState` objects passed to helpers that mutate them).
  Never-rebound scalars that sit next to state (`rsize` beside `x`/`y`, `camera_y` beside
  `camera_x`/`camera_z`/`yaw`, `camera_zoom`, `usage_hint`, `ambient_shadow_available`, hdrbloom's
  `light_pos`) were first put in `AppState` by some batches and then moved back out to module
  constants, so decision 2 is applied the same way in every file.
- **Module-level enum unpacks** (`SIMPLE, DIFFUSE = 0, 1`, `= range(7)`) became one annotated
  `int` constant per name, same values.
- **Field defaults that read a constant** (`i_mode: int = MODE_SOLID`, `[0] * TOTAL_SHADERS`) put
  `AppState` after those constants in a few files; no run-time order changed.
- **Placeholders.** `proctex` and `hdrbloom` created `sphere_mesh` only through `global` inside
  `rebuild_sphere()` (called at import); it is now a field with an empty `(0, [])` default that the
  unchanged import-time call fills. `imaging`'s bare `image_data: np.ndarray` became a field with an
  empty-array default, overwritten by `load_image()` before use.
- **GL enum loop targets** are typed `Constant` where the file already imports
  `OpenGL.constant.Constant`, else `typing.Any  # GL enum`; GL constants are not `int`.
- **Exempt from the strict check:** the discard name `_`, comprehension targets, `except ... as`
  targets and lambdas (no place for a type in the language). Chained assignments
  (`a = b = np.zeros(...)`) were left as written.
- **Comments:** each field kept its comment; `points`-family `_rot` helpers' comment "Lambdas can't
  rebind a module global" became "Lambdas can't assign to a field".
- One existing annotation was corrected: `chapt09/multitexture` `load_image`'s fourth return value
  is a `Constant`, not an `int`.

## Pre-existing bugs noticed and left alone (behaviour-faithful refactor)

- `chapt18/hdrbloom`: passes `None` as the `glReadPixels` data pointer with a PBO bound
  (`GL_INVALID_OPERATION`); `pixbufobj` fixed the same bug with `ctypes.c_void_p(0)`. Also draws two
  "View" menus (`_common.draw_view_menu` plus its own stop-point menu). Related open task:
  `tasks/ports-pbo-floattex-runtime-crashes.md`.
- `chapt18/texfloat`: no EXR backend for imageio in the image.
- `chapt21/fonts/font.py`: calls `imgui.set_window_font_scale`, absent from this imgui_bundle.
- `chapt11` `thunderbird`/`thundergl`/`vbo` bind `PWD` twice (once unannotated).
- `chapt10/axes3d`: `CYLINDER_RINGS` is annotated `list[list[tuple[float, ...]]]` but holds
  `(float, float, tuple, tuple)` elements.
- `chapt01/Block.py`: `window_width`/`window_height` are written but never read.
- `chapt03/pointsz`: `step` is annotated `float` but `glGetFloatv` returns a numpy value (used through
  `float(step)`, so harmless).
