# SuperBible v4: the four demos the headless sweep cannot render

**Status:** done 2026-10-14 (William Emerison Six <billsix@gmail.com> requested it 2026-10-14 and
authorized committing for the session)
**Priority:** 9
**Difficulty:** 1

## BLUF

Of the seven `ports/openglsuperbiblev4/` scripts that failed the 2026-10-14 headless sweep
(`tasks/archive/2026/10/14/ports-controls-in-menubar-step-1-superbiblev4.md`), four are this
task: chapt11/thunderbird, chapt11/thundergl and chapt11/vbo die on `import _common` because
they put `chapt11/` on `sys.path` instead of the tree root; chapt03/single is single-buffered
and never swaps, so `tools/render_probe.py`, which counts frames on `glfw.swap_buffers`, never
ends it and never photographs it. Done means: all four render under the probe, the full v4
sweep is 96 of 99 (the other three, texfloat, hdrbloom and motionblur, stay with
`tasks/ports-pbo-floattex-runtime-crashes.md`), and the v4 gates are green.

## Context (cold start)

- Every other v4 demo does `PWD = os.path.dirname(os.path.abspath(__file__))` then
  `sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))`, two `dirname`s above the demo
  directory = the tree root, where `_common.py` lives. The three chapt11 demos wrote
  `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`, one level short, because they
  also import `_thunderbird_data` from `chapt11/`. They have been like this since the port
  landed (e1affef3, 2026-04-28) and only ran when the current directory happened to be the tree
  root (Python puts the script's directory, not the cwd, on `sys.path`; the maintainer's
  `cd ports/openglsuperbiblev4 && python chapt11/vbo/vbo.py` habit put the root on it anyway).
- `single` reproduces GLUT_SINGLE: `glfw.window_hint(DOUBLEBUFFER, FALSE)`, a timed tick that
  draws the spiral, the menubar, then `glFlush()`; no `swap_buffers` ever. The probe's frame
  counter and capture both hang off the swap hook.

## Plan

1. The three demos: keep `chapt11/` on the path for `_thunderbird_data` and add the tree root
   for `_common`, in the shape the other demos use.
2. `tools/render_probe.py`: a `glFlush` hook that ends a frame when the script has never
   swapped (a single-buffered demo), reading the front buffer after the flush; swap-based
   demos are unaffected because a flush counts only while no swap has happened.
3. Gates: ruff; the annotation checker over v4; the four under the probe with
   `MVP_GLFW_X11=1`; the full v4 sweep (96 of 99 expected).

## How it went (2026-10-14)

- thunderbird, thundergl, vbo: the `PWD` shape the other demos use, then both the tree root
  (for `_common`) and `chapt11/` (for `_thunderbird_data`) on `sys.path`. Each now renders
  from the repo root and from its own directory (800×600, 2,128 / 25,876 / 25,875 colours).
- `single`: `tools/render_probe.py` wraps `GL.glFlush`; a flush ends the frame while no swap
  has been seen, and the capture reads the front buffer after it. The capture after four ticks
  is the blue field, the menubar and the first points of the spiral, which is what the demo
  draws (one point per tick, accumulating). glrect and simple, which flush before swapping,
  still render (their swaps are counted, their flushes ignored).
- Gates: ruff clean; the annotation checker clean; full v4 sweep 96 of 99 with
  `MVP_GLFW_X11=1` + `MVP_CONTROLS_WINDOW=1`; the three left are texfloat, hdrbloom and
  motionblur (`tasks/ports-pbo-floattex-runtime-crashes.md`, unchanged).
- Recorded in `headless-verification.md` §3 (the flush rule).

## Open questions

None. The scope (these four, not the three PBO crashes) is my reading of "those four"; the
PBO three have their own task.
