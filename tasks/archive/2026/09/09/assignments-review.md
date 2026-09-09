# Review the assignments against the modern demos; update or re-scope them

**Status:** **DONE — closed 2026-09-09.** Assignment 3 (strafe), the one Bill named when he
filed this, was re-synced onto demo18 and gated; the record is "Assignment 3 — done" below. The
unfinished half — assignments 1 and 2, which each need a *decision* before any code and are not
mechanical re-syncs the way assignment 3 was — was spun out to
**`tasks/assignments-1-and-2-review.md`** rather than archived with this doc, so the open questions
stay visible. `assignments/demo02/vec1.py` needed nothing (already on `mathutils`).

**The verification harness was removed with this archive** (`tasks/adhoc/assignments-review/`,
`git rm`'d — the standing one-shot lifecycle: committed during the task in `3c161dfa`, deleted at
archive, recoverable with `git show 3c161dfa:tasks/adhoc/assignments-review/verify.sh`). It is
*reusable* rather than one-shot — it renders any GL script in this repo headlessly, and
`tools/ctc_verify_game.sh` is the same idea already promoted for the Code-the-Classics games — so
if assignments 1 or 2 get the same treatment, recover it rather than rewriting it; promoting it to
`tools/` at that point would be reasonable. Deleting it was Bill's call (2026-09-09).
**Priority:** 6
**Difficulty:** 5
**Created:** 2026-07-09 (Bill: "Take a look at the assignments, and see how
they should be updated relative to the other demos. For instance, one of
the assignments is just checking to see if they can figure out how to
strafe")

## What's there (survey 2026-07-09)

`assignments/` — four student-facing items, all runnable standalone:

- `assignment1.py` — raw GLFW + immediate-mode GL boilerplate, numpy.
- `assignment2-screenspace.py` — screen-space exercise; carries its own
  hand-rolled `Vertex2D` dataclass (add/translate/scalar-mul).
- `assignment3-strafe.py` — the strafe exercise Bill mentions. ~~carries its own `Vertex2D`~~
  → **re-synced onto demo18 on 2026-09-08** (see below); now speaks the course vocabulary.
- `demo02/` — `vec1.py` + `plot2d.ipynb` (notebook pairing).

## The drift (why they need the look)

The assignments froze while the curriculum moved:

- **Their own vector type**: each ships a private `Vertex2D` with
  hand-rolled `__add__`/`__mul__`/`translate` — pre-dating the gacalc
  migration. The demos' single vector vocabulary is **`gacalc.g2.Vector`,
  imported from gacalc directly** (and rotation is now the plane+angle
  factory). *(Updated 2026-09-08: this doc said `gacalc.g2.Vector2` "via
  `mathutils`" — gacalc dropped the dimension suffix in 0.0.16, and
  `mathutils` stopped re-exporting gacalc types in the same pass, so
  callers import from `gacalc.g2` / `gacalc.g3` themselves.)* An
  assignment teaching "figure out strafing" on a bespoke vector class no
  longer matches the course the student just read.
- **Stale compat shims**: `from __future__ import annotations  # to
  appease Python 3.7-3.9` — the repo floor is 3.13/3.14.
- **No shared helpers**: raw per-file GLFW/window/viewport boilerplate
  the demos have long since factored (and the ports' `_common.py`
  pattern).

## Assignment 3 — done 2026-09-08 (re-synced onto demo18)

**It was based on demo18, not demo17 — despite its window title.** The title string read
`"ModelViewProjection Demo 17"`, but the content matched demo18: camera at `z=40` (demo17 is 15),
the `glfw.joystick_present` / `get_joystick_axes` block (demo17 has none), and a **perspective**
projection via `cs_to_ndc_space_fn` (demo17 uses `ortho`; perspective is what demo18 introduces).
The title was itself part of the drift and is now `"ModelViewProjection Assignment 3 - Strafing"`.

**How far it had drifted.** The file predated not just gacalc but `mathutils`' function stack. It
carried ~135 lines of bespoke `Vertex2D` + `Vertex` classes whose *methods* were the transforms
(`ms.rotate_z(...).translate(...)`, plus its own `.ortho()`, `.perspective()`,
`cs_to_ndc_space_fn()`), and applied them by hand per vertex — the era before
`fn_stack`/`push_transformation` existed. demo18 today composes `gacalc.transforms` functions onto
the function stack and unpacks with `GL.glVertex3f(*v)`. A student who had just read ch16–ch18 met
an assignment written against an API the course never teaches.

**What it is now:** demo18's current source verbatim, minus the doc-region markers (this file is in
no chapter), plus the exercise hole and a header comment explaining the task. `diff` against
`demos/demo18.py` is now just the title, the two holes, and the markers.

**Decisions taken under discretion (Bill can overrule any of these):**

1. **Hand the student the course vocabulary** — this answers question 1 below for assignment 3
   only. Post-gacalc the strafe answer is one composition, and it now sits *visibly parallel* to
   the forward/back code directly above the hole, so the exercise reads as "you have seen this
   move; do it sideways" instead of "learn a private vector class first".
2. **The exercise hole stays exactly where it was** — Shift+Left / Shift+Right in `handle_inputs`,
   still `pass` under a `TODO`. The wording is sharpened ("strafe the camera to its right") and the
   header comment tells the student where to look, but nothing is filled in.
3. **Dropped** `from __future__ import annotations  # to appease Python 3.7-3.9` (floor is 3.13),
   the bespoke vertex classes, the file's private `on_key` / `draw_in_square_viewport` copies (now
   `util.windowing` / `util.clipping`, as in every demo), and three dead fragments: a
   `Paddle.vertices: list[float]` default that every call site overrode with `list[Vertex]`, a
   `square: Paddle` annotation on a `list`, and a `global paddle_1_rotation, paddle_2_rotation`
   naming variables that do not exist.

**Verified — it was actually run, in the project's own image.** `make image BUILD_DOCS=0
USE_EMACS=0 USE_JUPYTER=0` (the trimmed flags are legitimate here: the diff touches one file that
no chapter includes, so it cannot reach the book toolchain), then the script driven headlessly
against an Xvfb in the sandbox whose socket is shared into the container — the standing recipe, so
the project's Dockerfile is untouched. Harness: `tasks/adhoc/assignments-review/verify.sh`.

1. **It renders the demo18 scene.** Framebuffer readback of frame 0 gives four colours —
   `(147,0,255)` ×2700 (paddle 1), `(255,255,0)` ×2700 (paddle 2), `(0,0,255)` ×196 (the square),
   `(7,18,25)` ×244404 (the clear colour) — and the saved PNG shows the expected Pong scene.
2. **It renders EXACTLY what demo18 renders.** The same harness on
   `src/modelviewprojection/demos/demo18.py` returns an identical histogram, count for count. That
   is the re-sync stated as a measurement: the assignment differs from its parent only in the hole.
3. **The hole is still a hole.** Run with Shift+Right held for 10 frames, the camera stays at
   `(0, 0, 40)` with `rot_y` unchanged — so the exercise is genuinely unsolved, and the `elif`
   also correctly stops Shift+Right from falling through to plain turning.
4. **The exercise is solvable.** A temporary solved copy (the holes filled with
   `compose([translate(b=camera.position_ws), rotate_y(camera.rot_y)])(e_1)` and its `-1 * e_1`
   mirror), same 10 frames of Shift+Right, moves the camera `+10.00` on x, `0.00` on z, heading
   unchanged — textbook strafing. Cross-checked against `gacalc` directly: that composition is
   perpendicular to the forward step at every heading and agrees to 1e-9 with the trig the file's
   own joystick block uses.

Also clean: `ruff check`, `ruff format --check`, `py_compile`.

**Still Bill's to check:** how it *feels* on real hardware with a real keyboard — a 10-frame
scripted run cannot judge the movement rate (one unit per frame is what the forward/back keys do,
and it may be too fast for strafing).

**The harness is saved** at `tasks/adhoc/assignments-review/` (`verify.sh` + `render_probe.py`)
because assignments 1 and 2 are still in this task's scope and it works on any of these scripts.
It exists because the obvious approach does not work here: `import -display :99 -window root`
captures **black** for these demos (no window manager maps the GLFW window onto the Xvfb root), so
the probe wraps `glfw.swap_buffers` and reads the back buffer with `glReadPixels` instead — which
is better evidence anyway, and it can hold keys down to exercise a camera path with no human at
the keyboard. Note `verify.sh` must NOT use `$DISPLAY`: in the sandbox that is `:0`, the host
passthrough, which the container cannot authenticate to.

**The joystick block was removed (Bill's call, 2026-09-09) — it contained the answer.** demo18's
controller code strafes on the left-stick X axis:
`camera.position_ws += (axes_list[0][0] * math.cos(camera.rot_y)) * e_1` plus the matching `e_3`
term. That is this exercise's answer, in trigonometric rather than compositional form, forty lines
below the hole. It was equally present in the pre-2026-09-08 version, so the re-sync did not
introduce it — but the exercise is meant to be closed-book, so it is gone.

Three things went with it, all dead once it left: `import math` (the block was its only user, now
that the bespoke vertex classes are gone), and `number_of_controllers =
glfw.joystick_present(...)`, which is assigned and never read — **dead in demo18 too**, worth
noticing if that demo is ever tidied. The header comment gains one neutral line ("Keyboard only --
demo18's gamepad support is not part of this exercise") that says what is missing without saying
why. Net −26 lines.

**Re-verified after the removal**, same harness: the frame histogram is unchanged and still
identical to demo18's, count for count; Shift+Right still moves nothing; the solved copy still
strafes `+10.00` on x with the heading fixed; ruff, format and `py_compile` clean. And the answer
really is gone — no `cos(camera…)`/`sin(camera…)` or camera-relative `e_1` math remains anywhere
in the file.

**Consequence for the "identical to demo18" claim above:** the *rendered frame* is still identical,
but the *source* now differs from demo18 by the joystick block as well as the exercise hole. If
demo18's gamepad handling changes, this assignment does not need to follow.
- Newly under gate (2026-07-09): format.sh now ruff-checks/-formats
  `assignments/` (T201 exempted — printed output is the point), so
  they're at least lint-clean; content is the open question.

## Questions to settle per assignment (Bill's call)

1. Keep-as-exercise vs retire: is "can they figure out how to strafe"
   still the right exercise given where the demos are (strafing is
   camera-relative translation — post-gacalc it's one
   `translate(rotate(angle)(offset))` composition)? If kept, should the
   scaffold hand the student the course vocabulary (`gacalc.g2.Vector`,
   `gacalc.transforms.translate`, `mathutils.rotate`) instead of a bespoke
   `Vertex2D`?
2. Which demo does each assignment pair with, and should they live/point
   there (e.g. `demo02/` already mirrors a demo number)?
3. Solution management: are these handed out as-is (students fill in),
   and if so where do reference solutions live?
4. The book: should chapters reference the assignments at the point the
   matching concept lands?

## Suggested shape (once directions are chosen)

Per assignment: modernize the scaffold (gacalc/mathutils vocabulary,
shared window boilerplate, 3.13+ idioms), keep the *exercise* (the thing
the student must figure out) as the deliberately-missing piece, and gate
with format.sh + a definitions-style run (the exercise hole stubbed).
