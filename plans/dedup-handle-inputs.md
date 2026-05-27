# Task: investigate de-duplicating the per-demo `handle_inputs`

**Status:** not started (investigation task). **Type:** refactor of
`src/modelviewprojection/demo*.py`, book-coupled. Spun off from
[`extract-duplicated-demo-helpers.md`](extract-duplicated-demo-helpers.md) on
2026-05-27 at Bill's request.

## Context
`handle_inputs` is the per-frame, key-*polling* function each demo calls in its
event loop (`glfw.get_key(window, KEY_X) == glfw.PRESS` → mutate state). Unlike
`on_key` (the discrete escape-to-quit callback, now shared in
`windowing.py`), `handle_inputs` is **genuinely different per demo**: measured at
**21 copies / 18 distinct variants**. So it is *not* a copy-paste-identical case
like `on_key`/`draw_in_square_viewport` — most of it is pedagogically meaningful
(each demo wires up the keys relevant to what it teaches: paddle move, square
rotate, camera placement, jet yaw/pitch, etc.).

**But** there is likely repeated *sub-structure* worth extracting — the same
block recurs across many demos even though the whole function differs:
- The **walk-around camera** block (`LEFT`/`RIGHT` yaw, `PAGE_UP`/`PAGE_DOWN`
  pitch, `UP`/`DOWN` walk forward/back using `sin/cos(camera.rot_y)`) appears
  near-verbatim across the 3D demos (~demo16–24, and the SuperBible ports).
- Paddle move/rotate blocks (`W/S`, `A/D`, `I/K`, `J/L`) recur across the 2D
  paddle demos.

## What to do (investigation, then propose before editing)
1. Cluster the 21 `handle_inputs` bodies and identify the shared sub-blocks
   (camera-walk, paddle-move, square-rotate). Quantify how many demos share each.
2. For each shared sub-block, decide: extract into a helper (e.g.
   `walk_around_camera(window, camera)` — note this overlaps the **ports**
   [`ports-walkaround-camera.md`](ports-walkaround-camera.md) and demo22's
   camera) vs. leave inline (teaching value). Repetition is *good* here when the
   point is for the student to read the keys in context — so be conservative.
3. **Book coupling:** `handle_inputs` IS shown via `literalinclude` in several
   chapters (e.g. ch05's "Handling User Input", ch06's "define handle movement of
   paddles", ch10+). Extracting a sub-block changes what those chapters display,
   so any extraction must be coordinated chapter-by-chapter (teach-once-then-import,
   per the umbrella plan) — and may not be worth it for the early teaching demos.

## Open questions for Bill
- How aggressive? (e.g. only extract the `walk_around_camera` block from the 3D
  demos, where it's near-identical and not the teaching focus — leave the 2D
  paddle-input blocks inline since reading them *is* the lesson.)
- Should this fold into / coordinate with `ports-walkaround-camera.md` (same
  camera logic, ports side)?

## Verification (when done)
`pytest`, `ruff`, `py_compile` each touched demo; Bill runs the GL demos (no
display / glfw in the container). For book-referenced demos, Bill's `make html`
confirms the updated `literalinclude`s.
