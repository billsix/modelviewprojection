# Authorship style: library-not-framework, and repetition-with-incremental-complexity

**What this is:** the durable characterization of *how* the modelviewprojection teaching code is written, and
*why* — stated by the maintainer (William Emerison Six <billsix@gmail.com>) and verified against the source
2026-09-04 by two `file:line`-anchored reading passes over the actual demos + `pgzero_gl`. It is a design-values
record: read it before "improving" the demos or the ports, because both traits below are **deliberate**, and a
well-meaning DRY/framework refactor would destroy the pedagogy. Project: `github.com/billsix/modelviewprojection`.

## The two claims (maintainer's own framing)

1. **"It's written as LIBRARY code, not a FRAMEWORK like Qt."** With a framework (Qt), the framework is the main
   app and your code is a plugin it calls into (`OnPaint`, …); with a library, *your* code is the main program
   and you call the library. This is inversion of control / the Hollywood principle ("don't call us, we'll call
   you"): **library = you own `main()` and the loop and call *down*; framework = it owns the loop and calls *up*
   into your callbacks.**
2. **"I use a lot of repetition, increasingly adding complexity."** Each demo re-inlines most of the previous
   one and adds ~one new concept, rather than DRY-factoring. Deliberately WET.

Both were assessed **ACCURATE**. Evidence below.

## Claim 1 — library, not framework: ACCURATE

**Every teaching demo (demo01–24) owns its own render loop and calls down into helpers.** Each is a top-to-bottom
script with exactly one module-level `while not glfw.window_should_close(window):` and no enclosing class, no
runner, no base class. Nothing calls the demo.

- The loop is the demo's own, at module scope: `demos/demo02.py:49`, `demo07.py` (loop body `:133-140` polls +
  calls `draw_in_square_viewport(window)` + `handle_movement_of_paddles()`), and identically across the modern
  demos — `demo16.py:161`, `demo21.py:488`, `demo22.py:1354`, `demo24.py:592`.
- The demo does its own GLFW/GL setup, runs the loop, then tears down itself: `demo21.py:633-638` deletes its
  VAOs/VBOs and `demo21.py:640` ends the file with a bare `glfw.terminate()`.
- Control flows *outward* — the demo calls down into the math/matrix/util libraries: `demo07.py:146-152`
  (`rotate(...) @ translate(...)`), `demo10.py:175-181` (`inverse(translate(b=camera.position_ws))`),
  `demo21.py:571-577` (`ms.rotate_x(...)`, `with ms.push_matrix(...)`).
- The library modules own **zero** loops: `grep -c "while not glfw"` is `0` for `mathutils.py`,
  `matrix_stack.py`, and every `util/*.py`. They are pure functions/classes the demo invokes.
- Even input is **pulled**, not pushed: gameplay keys are polled inside the demo's own `handle_inputs`
  (`demo05.py:99` `glfw.get_key(window, glfw.KEY_S) == glfw.PRESS`), and `util/windowing.py:23-24` documents the
  split ("Per-frame, per-demo key handling lives in each demo's own `handle_inputs`, which is intentionally not
  shared").

**The repo contains its own framework foil, which proves the author knows the difference.** `wxapp.py` is
framework-style: `wxapp.py:292` `app.MainLoop()` (wx owns the loop), `:82`/`:84` bind `EVT_PAINT`/`EVT_TIMER`,
and `:88 OnPaint` / `:99 OnTimer` / `:115 InitGL` / `:180 OnDraw` / `:284 OnInit` are the magic-name callbacks wx
calls *up* into (this is why `CLAUDE.md` exempts `wxapp.py` from ruff `N802`). The demos are the library side;
`wxapp.py` is the framework side — the exact contrast the maintainer draws, present in one repo.

**The honest nuance (does NOT undercut the claim):** two real up-calls exist, but neither owns the render loop.
(a) glfw's escape-to-quit key callback — `demo01.py:72` / `demo16.py:49` / `demo21.py:137`
`glfw.set_key_callback(window, on_key)`, `on_key` at `util/windowing.py:39` — used only for Esc; glfw still does
not own the loop. (b) imgui's GLFW backend in demo21+ — `demo21.py:126` `GlfwRenderer(window)` installs
mouse/char/scroll callbacks, but the demo pumps imgui explicitly each frame (`imgui.new_frame()` …
`impl.render(imgui.get_draw_data())`), so imgui is a library the demo drives, not a framework owning control.

### The corollary that matters most: `pgzero_gl` is the framework side

The Code-the-Classics games (`ports/codetheclassics/{vol1,vol2}/`) are the **exception** to the house style:
they are **framework-style**. Each game defines `WIDTH`/`HEIGHT`/`update()`/`draw()`/`on_*` and hands control to
`pgzero_gl.runner.main()`, which owns the `while` loop and calls *back* into the game's `update`/`draw` — the same
inversion as `wxapp.py`'s `OnPaint`. This is faithful to upstream PyGame Zero (whose whole point is that
inversion), but it means the ports are written in the one style the course otherwise argues against. That gap is
the motivation for the **inline / strip / re-extract** initiative
(`tasks/pgzero-gl-inline-strip-reextract.md`): flip the games to library style so each owns its own loop and
reads like a demo.

## Claim 2 — repetition, increasingly adding complexity: ACCURATE

The demos are deliberately WET; the policy is stated in `CLAUDE.md` ("Duplication across `demos/` is deliberate —
'teach once, then share'"; "Each demo introduces exactly one new concept on top of the previous").

**Line counts climb monotonically** — copy-forward-and-extend, not DRY factoring:
`demo01 97 → 02 81 → 03 131 → 04 170 → 05 159 → 07 178 → 08 179 → 10 216 → 11 253 → 12 261 → 13 265 → 14 273 →
15 279`, continuing up through the 3D/shader era (`demo23 549`, `demo24 788`, `demo22 1518`).

**Verbatim copy-paste units, demo-to-demo:**
- The ~20-line GLFW/GL boilerplate header is identical across demo02–15 but for the title string
  (`demo05.py:37-58` ≡ `demo07.py:38-59` ≡ `demo10.py:41-61`).
- The `@dataclass Paddle` + its two instantiations + the paddle-vertex literal are re-declared per demo
  (`demo16.py:60-75`, `demo17.py:68-82`, `demo18.py:69-83`); `CLAUDE.md` names "the ~20 near-identical
  `Paddle`/`Camera` dataclasses".
- `handle_inputs()` / `handle_movement_of_paddles()` — the key-poll block — is re-inlined nearly whole each time
  (`demo16.py:137-153` ≡ `demo17.py:164-180` ≡ … ≡ `demo21.py:452-468`), each appending one new block.
- The 60 fps busy-wait limiter preamble is verbatim (`demo16.py:163-167` ≡ `demo17.py:190-194` ≡ …).
- The joystick-axes camera block is copy-pasted (`demo18.py:197-218` ≡ `demo19.py:181-194` ≡ `demo21.py:555-568`).
- The per-vertex transform stanza is copy-pasted even *within* a demo, once per drawn object (`demo12.py:180-200`,
  `:205-230`, `:237-257`).
- Shader-compile boilerplate is re-inlined then only lightly promoted: demo20 inlines `shaders.compileShader`
  (`demo20.py:163-169`); demo21 wraps it in a local `compile_program()` (`demo21.py:157-169`) — but that helper
  is itself re-copied into demo22/22a/23/24 rather than shared.
- Shared extraction is used **sparingly and only after a concept has been taught once** — `windowing.on_key`,
  `clipping.draw_in_square_viewport`, `cameracontrols.walk_around_camera`, `shading._face_normal` — each
  documented as "teach once in the demo where it appears, then import."

**Complexity is monotonic — one machine layer per demo, same Pong scene throughout:**
function-stack + `InvertibleFunction` (demo16) → depth test + `ortho` + `push_transformation` (demo17) →
`perspective` + gamepad (demo18) → **fixed-function matrices**, first `glMatrixMode`/`gluPerspective`/
`glPushMatrix` (demo19, bridged in comments: "just like putting the identity function on the lambda stack") →
+ pass-through shaders (demo20) → **OpenGL 3.3 Core**, `matrix_stack` → `mvpMatrix` uniform (demo21) → Lambert
lighting, planar shadows, texturing, per-vertex normals (demo22–24). The cleanest single-concept delta:
`diff demo11 demo12` = **+16 lines** for the nested "square space" relative to paddle1.

## Why this matters / how to apply

- **Do not DRY the demos, and do not frameworkify them.** The repetition is the teaching (a student reads one
  self-contained file top-to-bottom and sees exactly what changed from the last), and the library style is the
  point of the whole course (transformations you *call*, not callbacks a framework invokes). Both are load-bearing
  pedagogy, not tech debt. This is the demo-side form of the general convention "duplication across demos is
  deliberate."
- **The one place the style is violated is `pgzero_gl`/the ports** — and correcting that (library-izing the
  games) is tracked in `tasks/pgzero-gl-inline-strip-reextract.md`, which flows directly from this record.
- **When adding a demo:** keep it a single top-to-bottom script that owns its loop, calls down into
  `mathutils`/`matrix_stack`/`util`, adds ~one concept over its predecessor, and shares a helper only after the
  concept it embodies has been taught inline once.

## Taught abstractions ARE library, not framework — the ports' gradient (maintainer, 2026-09-04)

**"Library, not framework" is about control flow and dependency, NOT about avoiding the book's own
math.** A recurring mistake (Claude made it 2026-09-04, framing "use `InvertibleFunction` in a
game" as a *tension* with the house style) is to read "clearer code over abstractions" as "no
abstractions." It is not. The principle targets exactly two things: **(1) framework-style
inversion of control** — a runner owning the loop and calling *up* into the game (pgzero's
`runner.main()`, wx's `OnPaint`) — and **(2) depending on PyGame Zero as a framework.** The
maintainer's *own taught abstractions* — `InvertibleFunction`, `translate`, `rotate`
(`plane_rotation`), `inverse`, `compose`, `perspective`, the camera-as-inverse hinge — are
**library functions the game calls *down* into.** Using them is the library side, not the
framework side. And because the book *teaches* them, a game (or a book section referencing that
game) that uses them is coherent with the curriculum — not a violation of it.

So the ports have an **abstraction gradient**, mirroring the demos' own WET→abstracted arc
(Claim 2): the simplest game, `boing_gl1.py` (fixed-function GL 1.x), uses **zero** abstractions —
raw OpenGL, an early teaching point; richer games use progressively more of the taught
abstractions. Every rung is still "library, not framework" (each game owns its loop after the
inline/strip initiative). The two real constraints on introducing a taught abstraction into a
game are:

1. **Book sequencing** — a book section that references game code using an abstraction must come
   *after* the chapter that teaches it (e.g. `inverse(translate(...))` after the camera chapters
   ch16/ch19; `perspective` after ch19). The maintainer teaches all the math, so the code and the
   prose must be ordered so the reader has met the abstraction first.
2. **Don't reintroduce the pgzero framework** — the thing to avoid is a full-blown PyGame-Zero
   *framework* dependency (its runner/inversion), not the book's math.

This is why the three "express X as a taught function" tasks are *consistent* with the philosophy,
not exceptions to it: `tasks/codetheclassics-camera-as-inverse.md` (camera = `inverse(translate)`),
`tasks/codetheclassics-myriapod-rotation-as-functions.md` (segment placement = `rotate ∘ translate`,
built with **integer-exact** `InvertibleFunction`s so it replicates the original bit-for-bit), and
`tasks/codetheclassics-leadingedge-projection-functions.md` (world→camera = `inverse(translate)` in
`g3`). Each imports from `gacalc.transforms`, keeps behaviour byte-identical, and is placed in the
book only where the abstraction has been taught. Evidence base for all three:
`tasks/reference/coordinate-spaces-in-code-the-classics.md`.

## Doc drift found in passing (fix separately)

`CLAUDE.md` says "demo12: Matrix-stack concept introduced", but the `FunctionStack`/`fn_stack` abstraction
(`mathutils.py`) first appears in **demo16–18**; demos 01–15 use only explicit `compose(...)`/`inverse(...)`,
no stack. Small inaccuracy in the doc, not in the claims above — worth correcting in a `CLAUDE.md` pass.

## Related

- `tasks/pgzero-gl-inline-strip-reextract.md` — the initiative to flip the ports from framework- to library-style
  (the direct consequence of this record).
- `tasks/reference/pgzero-gl-design-for-a-personal-learning-library.md` — the `pgzero_gl` design + per-game usage
  slices (the shim that is the framework exception).
- `CLAUDE.md` — "Duplication across `demos/` is deliberate", the demo01→demo24 pedagogical arc, and the
  `wxapp.py` `N802` naming exemption (the framework foil).
