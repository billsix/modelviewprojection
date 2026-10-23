# SuperBible v4 ports: wrap module globals in a per-app singleton dataclass + fully type them

**Status:** proposed — needs go-ahead (ready to execute; large, so batch per chapter).
**Priority:** 6 **Difficulty:** 6
**Created:** 2026-10-23 (William Emerison Six <billsix@gmail.com>). Requested: wrap each port app's
globals in one singleton dataclass, update every reference, and add types to everything per the
Python standard (the flagged example of *missing* a type: `w, h = glfw.get_framebuffer_size(window)`).

## BLUF

Each OpenGL SuperBible v4 port under `ports/openglsuperbiblev4/**` is a single-file demo that keeps
its mutable state in **module-level globals** mutated through `global` statements (see the model file
`ports/openglsuperbiblev4/chapt02/bounce/bounce.py`). For **each app**, replace those globals with a
single **per-app dataclass** holding that app's state, instantiated once, and rewrite every reference
to go through the instance (removing all `global` statements). Separately, **add explicit type
annotations to everything** — including sites the annotation checker currently *exempts* (tuple
unpack, `for`/`with`, augmented assignment), the flagged case being
`w, h = glfw.get_framebuffer_size(window)`. "Done" = every app refactored, `make format` +
`make type-check` green, each app renders **frame-identically** to before (behavior-faithful —
structural change only), and the display/audio/gamepad verification Bill runs on host GL passes.

## Context (read first)

- **Scope:** `ports/openglsuperbiblev4/**` — ~104 `.py` files across `chapt01`–`chapt22`, plus the
  shared helpers `ports/openglsuperbiblev4/_common.py` and `_primitives.py`. Each demo is one
  self-contained file with a `main()` and GLFW/imgui glue.
- **The current style (the model):** `chapt02/bounce/bounce.py` — module-level mutable state
  (`x`, `y`, `rsize`, `xstep`, `ystep`, `window_width`, `window_height`, `last_tick`, `paused`,
  `_window`), a module const (`TICK_INTERVAL`), and functions that mutate state via `global x, y, …`.
  GLFW callbacks (`on_key`, `on_framebuffer_size`) have **fixed signatures** set by the glfw API, so
  they cannot receive the state as an extra parameter — they must reach it some other way.
- **IMPORTANT — this does NOT contradict "don't clean up the globals."** The mvp CLAUDE.md says the
  **course demos** (demo01–24, `src/modelviewprojection/` + the book) deliberately use procedural
  globals and must not be "cleaned up" *unless asked*. This task is **explicitly asked**, and it is
  scoped to the **`ports/openglsuperbiblev4/` porting source only** — do **not** touch the course
  demos, the book listings, or `src/modelviewprojection/`.
- **The annotation rule and its enforcement:** `make type-check` runs `ty` **plus**
  `tools/check_local_annotations.py --include-module` — the AST checker requiring every local and
  module-level binding across `src`, `tests`, and `ports/**` to carry an explicit annotation. It
  **exempts** tuple-unpack, `for`/`with as`/`except as`/comprehension/walrus targets, augmented
  assignment, and attribute/subscript targets. **The maintainer wants types even at those exempt
  sites** — so `w, h = glfw.get_framebuffer_size(window)` must become something annotated, e.g.
  `size: tuple[int, int] = glfw.get_framebuffer_size(window)` then `w: int = size[0]` /
  `h: int = size[1]` (final wording a decision — see open questions).
- **ty scope caveat:** `ports/openglsuperbiblev4` is currently kept **out of the `ty` step** (it has
  pre-existing glfw/imgui stub diagnostics unrelated to annotations — see
  `tasks/openglsuperbible-ty-diagnostics.md`). So the annotation **completeness** is enforced by
  `check_local_annotations.py`; full `ty` type-checking of these files is a separate, pre-existing
  concern. GL constants are not `int` and have their own gotchas (`tasks/reference/gl-and-imgui-gotchas.md` §7).

## Approach (per app — confirm the pattern on bounce.py first, then batch)

1. **Define a per-app dataclass** for that app's **mutable runtime state** — a plain
   `@dataclass` (mutable; state changes every frame, so **not** `frozen`), fields fully annotated with
   defaults. Include the window handle. Truly-constant module values (e.g. `TICK_INTERVAL`) stay
   module-level annotated constants — or move into the dataclass as a default — decide once and apply
   uniformly (open question 2).
2. **Instantiate once** at module level and have functions reference it. Because glfw callbacks have
   fixed signatures, the pragmatic shape is a **module-level singleton instance** the functions read
   and mutate (`state.x = …`), which deletes every `global` statement. (Threading the instance through
   each function as a parameter is cleaner in principle but impossible for the fixed-signature
   callbacks without per-app closures — decide the convention, open question 1.)
3. **Rewrite all references** from bare `x`/`paused`/`_window` to `state.x`/`state.paused`/`state.window`.
   No `global` should remain.
4. **Annotate everything**, including the checker-exempt sites (the `w, h` unpack and friends).
5. **Keep behavior identical** — this is a structure-only refactor; the render must be frame-for-frame
   the same.

## Scale / batching

~104 files is too many for one commit. Do it **per chapter** (`chapt01`, `chapt02`, …), each chapter a
work commit after its apps pass the gates + headless render check. Keep this as **one task doc with a
per-chapter checklist** rather than splitting into step-tasks (don't over-scaffold) — promote to
step-tasks only if the maintainer wants per-chapter commit/review boundaries. The shared
`_common.py`/`_primitives.py` are done first (everything imports them) and only where they hold
mutable state; they may just need annotations.

Per-chapter checklist (fill in as done):
- [ ] `_common.py`, `_primitives.py` (annotations; state only if any)
- [ ] chapt01 … chapt22 (one row each when batching begins)

## Gates / verify

- **`make format`** — ruff (line-length 80) clean.
- **`make type-check`** — `ty` + `tools/check_local_annotations.py --include-module` clean across
  `ports/openglsuperbiblev4/**` (this is what proves "types everywhere", exempt sites included).
- **Per-app render identity** — `tools/verify_render.sh <script> [frames] [png] [hold-keys]` against a
  pre-refactor reference (needs `make image` + Xvfb `:99`); the refactor must not change pixels.
  `tools/render_probe.py` masks the Wayland GLFW gotcha, so a green headless sweep is **not**
  sufficient evidence by itself (`gl-and-imgui-gotchas.md` §1).
- **Book regions** — confirm none of these port files are pulled into the book via
  `doc-region` markers before editing (grep `doc-region` under `ports/openglsuperbiblev4/`); if any
  are, move the markers with the code and run `make check-regions`.
- **Display / audio / gamepad** — Bill verifies on host GL (the agent cannot).

## Decisions / open questions

1. **Singleton wiring:** module-level instance the functions reference (removes `global`; works with
   fixed-signature glfw callbacks), vs passing the dataclass through non-callback functions as a param.
   Recommend the **module-level instance**. Which do you want, and one consistent name across all apps
   (e.g. class `AppState`, instance `state`)?
2. **Constants:** leave truly-constant module values (`TICK_INTERVAL`) as annotated module consts, or
   fold them into the dataclass as defaults? Recommend **keep genuine constants module-level**; only
   mutable state goes in the dataclass.
3. **How to annotate the exempt unpack sites:** `size: tuple[int, int] = glfw.get_framebuffer_size(window)`
   + indexed reads, vs keeping `w, h = …` and accepting the checker's exemption. The request is to
   type them, so recommend the annotated-intermediate form. Confirm the spelling you want.
4. **ty scope:** leave `ports/openglsuperbiblev4` out of the `ty` step (status quo; annotation checker
   still covers it), or also bring it into `ty` as part of this work? That overlaps
   `tasks/openglsuperbible-ty-diagnostics.md` — recommend keeping it out here and tracking ty there.

## Pointers

- `ports/openglsuperbiblev4/chapt02/bounce/bounce.py` — the model file (globals + `global` + callbacks).
- `tasks/ports-ux-pass.md` — the SuperBible-ports UX umbrella (read first; this is a code-structure
  axis, distinct from UX).
- `tasks/openglsuperbible-ty-diagnostics.md` — the pre-existing glfw/imgui ty-stub diagnostics.
- `tasks/reference/superbible-ports-guide.md` — port placement/structure guide.
- `tasks/reference/python-coding-standard-mvp.md` + `runClaudeInContainer/.../python-coding-standard.md`
  — the annotation policy and mvp specifics.
- `tasks/reference/gl-and-imgui-gotchas.md` — GL constants aren't `int`, the Wayland GLFW masking
  gotcha, menubar conventions.
- `tools/check_local_annotations.py`, `tools/verify_render.sh`, `tools/render_probe.py` — the gates.
