# Step 2 — per game: strip the dead slice, restructure, and absorb the loop

**Status:** DONE — all 10 games converted, every one frame-180 byte-identical, ty+ruff clean (2026-09-04). Awaiting maintainer commit + play-test. Then step 3 (re-extract).
**Priority:** 6
**Difficulty:** 7

> **Behavior-preservation is already tooled.** Step 1 built `tasks/adhoc/pgzero-gl-inline/capture_frame.py` +
> a byte-identical frame-trace. Every step-2 restructure of a game must keep that property: capture frame N of
> the game before the change, capture after, assert AE=0. Since step 2 *absorbs the loop* (a real structural
> change, not a pure move), pair the trace with human play-testing — the trace only covers the no-input path.
**Part of:** `tasks/pgzero-gl-inline-strip-reextract.md` (umbrella) · **Depends on:** `tasks/pgzero-gl-step1-inline-per-game.md` · **Next:** `tasks/pgzero-gl-step3-reextract-library.md`

## BLUF

For each of the 11 now-self-contained game files: (a) **delete the engine code this game never uses**, (b)
**restructure the rest** as the game needs — dataclasses preferred, and (c) **absorb the loop** so the game owns
`while not should_close: update(); draw()` directly instead of handing control to the inlined `runner.main()` —
flipping it from framework-style to library-style, so it reads like a course demo. **Behavior-preserving**
(same RNG order, same update/draw order, same gameplay), proven per game by a seeded differential state trace.
This spans sessions; track per-game status in the table below.

## Context

- **Read first:** the umbrella `tasks/pgzero-gl-inline-strip-reextract.md`, and
  `tasks/reference/library-not-framework-authorship-style.md` (why absorbing the loop is the whole point — it
  removes the last inversion of control, the thing the course argues against). The per-game **usage slices**
  (which game uses joystick/surface/mask/transform, what is load-bearing vs. dead) are in
  `tasks/reference/pgzero-gl-design-for-a-personal-learning-library.md` — that doc IS the strip list.
- **Fidelity rule** (`CLAUDE.md` › Code-the-Classics): behavior-faithful — structure may change, behavior may not.
  The safety net is the **seeded differential state trace** (`tasks/archive/2026/07/23/frozen-vectors-rebind-migration.md`).

## Design decisions & the abstraction gradient (maintainer, 2026-09-04)

**The governing principle — an abstraction GRADIENT across the games, mirroring the demos.** Just as the book's
demos start WET/procedural and abstract things out slowly as they grow, the ports run the same arc from vol1 to
vol2: **the simplest games (boing) carry the LEAST shared machinery — closest to raw procedural OpenGL, like a
demo; the most complex games (vol2) keep the MOST helper abstractions.** The invariant across all of them is
**library, never framework** — the game owns its loop and calls *down* into helpers; nothing calls *up* into the
game. So "strip depth" is per-game: strip boing to the bone; let vol2 keep `Actor` and the richer helpers where
they earn their keep. The abstraction *emerges* as the games get complex, exactly like the demos.

**Is an `Actor` class necessary? — the decision (per-game):** No class is *necessary*, but a *sprite* game needs
*some* sprite helper (the demos draw geometry by matrix; a sprite game draws named textures by pixel anchor). So:
**drop `Actor` for the simplest games (boing) in favour of plain `@dataclass`es + a couple of module functions;
keep `Actor` for vol2** (many animated actors, where the class earns its ~230 lines). This is the gradient made
concrete.

**boing (the rawest) — what was done (all proven frame-180 byte-identical, ty+ruff clean; 3617-line inline →
1851 lines, −49%):**
- **Absorbed the loop** — `runner.main()` dissolved; boing owns its own `while` loop at the bottom, hardcoded to
  3.3-core, calling `update()`/`draw()` directly and *down* into the renderer. The framework→library flip.
- **Stripped every module boing never touches** — joystick, mask, transform, renderer_gl1, runner, surface,
  draw, text, and `screen` itself; plus `geometry` (Rect/ZRect) and `Image.get_rect`/`get_size` once their only
  users were gone. Also `exit()`, `_MixerSound`, `_pooled_sound`, `__all__`.
- **Dropped `Actor` and `Screen`** in favour of two module functions — `blit(name, x, y)` (top-left, for
  backgrounds/UI) and `draw_sprite(name, cx, cy)` (centre, for the moving objects) — and made **Ball/Bat/Impact
  plain `@dataclass`es** holding `x`/`y`/`image` + their game state (the combined update/draw loops iterate the
  `Bat | Ball | Impact` union, which ty resolves cleanly). This is the demos' function-and-struct style.
- **Kept, deliberately, for now:** the `resources` image loader and the `Renderer` class (the GL quad drawer).
  These are the next candidates for the "raw" gradient — see below — but were left as the one remaining engine
  layer so this increment stayed a clean, verifiable step.

**DECISION (maintainer, 2026-09-04): boing SHIPS AT THIS DEPTH ("depth 1")** — `blit`/`draw_sprite` + dataclasses
over the *kept* `resources` image loader and `Renderer` class. The two deeper "raw OpenGL, no manager" moves
below were **considered and deferred** — not rejected; revisit anytime the maintainer wants boing fully raw.

**FOLLOW-ON (maintainer, 2026-09-04): a GL 1.4 fixed-function COMPANION to boing** — `boing_gl1.py` beside
`boing.py`, same game, drawn with the fixed-function OpenGL 1.x pipeline (2.1-compat context, `Renderer1x`)
so a student can `diff` the two and compare the old immediate-mode pipeline (demo19 era) against 3.3 Core +
shaders. The 3.3 `boing.py` is untouched. Planned in **`tasks/pgzero-gl-boing-gl14.md`** (awaiting go-ahead).

**Further raw steps still available on boing ("depth 2" — deferred, the gradient can go deeper if wanted):**
(a) replace the lazy `resources` loader with demo-style **eager texture loading up front + `glDeleteTextures`
cleanup at exit** (a `load_texture(path)->int` function + a name→id dict); (b) dissolve the `Renderer` **class**
into module-level GL state + functions (`compile_program`, `make_quad_vao`, a `draw_textured_quad` function),
matching the demos' `compile_shader_program`/`make_vao`/`draw` shape. Both are behaviour-preserving and provable
by the frame trace; they're the last "no manager" moves for boing. **To revisit:** re-open this task, do (a)+(b)
on boing, prove frame-180 byte-identical, and re-baseline the gradient's bottom rung.

## Per-game work

1. **Strip the dead slice.** Using the reference doc's per-game usage table, delete the inlined engine parts this
   game never touches (e.g. vol1 games carry no joystick; only some use `surface`/`mask`/`transform`). Each file
   shrinks a lot and becomes readable as "this game's own engine."
2. **Restructure what remains** to fit the game — dataclasses where they earn it, `match`, precise types. Not a
   rewrite; make it read well as one file.
3. **Absorb the loop (the framework→library flip — decided 2026-09-04).** Today the inlined `runner.main()` owns
   the loop and calls back into the game's `update`/`draw`. Move that loop into the game's own top level so the
   game owns it and calls *down* into its renderer. **Preserve every behavior-load-bearing detail of the current
   loop while moving it:** the fixed 60 Hz timestep and the `update(dt)`-vs-`update()` arity (only leadingedge
   takes `dt`), the exact update-then-draw order, Esc-to-quit, the SIGINT/SIGTERM handlers, and the
   `audio.shutdown()` in the `finally` (without it a music-playing game hangs on exit —
   `tasks/reference/notable-subsystems.md`). The flip is structural; the frame sequence must stay identical.

## Behavior-preserving verification (per game)

- Seeded differential state trace vs. the step-1 (pre-strip) game — **zero divergence** over N seeded frames.
- Headless run (Xvfb + `PGZERO_MAX_FRAMES` + pixel-mean) matches.
- `ruff` + `ty` clean.

## Per-game status (fill in as you go)

| Game | vol | stripped | restructured | loop absorbed | trace clean | notes |
|---|---|---|---|---|---|---|
| boing | 1 | ✅ | ✅ | ✅ | ✅ | **DONE (template)** — Actor dropped → dataclasses + blit/draw_sprite; 3617→1851 lines (−49%); frame-180 byte-identical. **Follow-on:** GL 1.4 companion `boing_gl1.py` planned (`tasks/pgzero-gl-boing-gl14.md`) |
| cavern | 1 | ✅ | ✅ | ✅ | n/a | **DONE** — kept Actor (gradient); loop absorbed, unused modules stripped, screen→blit; 4024→2971 (−26%); byte-identical |
| myriapod | 1 | ✅ | ✅ | ✅ | n/a | **DONE** — kept Actor; same pattern as cavern; 4106→3053 (−26%); byte-identical |
| bunner | 1 | ✅ | ✅ | ✅ | n/a | **DONE** — richest vol1: KEEPS surface/draw/text/screen (uses screen.draw.text + gldraw.rect + screen.surface) + Actor; only loop absorbed + unused standalone modules stripped; 4128→3583 (−13%); byte-identical; pre-existing scroll_pos suppressed |
| soccer | 1 | ✅ | ✅ | ✅ | n/a | **DONE** — richest vol1 (like bunner): keeps surface/draw/text/screen + Actor; loop absorbed + unused stripped; 4417→3872 (−12%); byte-identical |
| kinetix | 2 | ✅ | ✅ | ✅ | n/a | **DONE** — vol2 keeps the most: loop absorbed + renderer_gl1/runner stripped + exit/__all__ trimmed; keeps joystick/surface/mask/transform/draw/text/screen/Actor; 4444→4124 (−7%); byte-identical |
| avenger | 2 | ✅ | ✅ | ✅ | n/a | **DONE** — keeps joystick/mask/surface/draw/text/_MixerSound; loop absorbed + renderer_gl1/runner stripped; 4776→4456 (−7%); byte-identical |
| eggzy | 2 | ✅ | ✅ | ✅ | n/a | **DONE** — keeps joystick/gldraw/surface/draw/screen/Actor; loop absorbed + renderer_gl1/runner stripped; 5047→4727 (−6%); byte-identical; pre-existing time_remaining suppressed |
| leadingedge | 2 | ✅ | ✅ | ✅ | n/a | **DONE** — the one `update(dt)` game (absorbed loop calls `update(_dt)`); keeps joystick/gldraw/surface/transform/draw/screen/Actor; 5458→5139 (−6%); byte-identical |
| beatstreets | 2 | ✅ | ✅ | ✅ | n/a | **DONE** — richest game: keeps joystick/surface/draw/screen/Actor + full _Mixer (find_channel/get_busy); loop absorbed + renderer_gl1/runner stripped; 6334→6014 (−5%); byte-identical; pre-existing height_above_ground ×4 suppressed |

## Open questions

1. **Do boing first as the template**, get the loop-absorption + strip pattern right on the simplest game, show
   the maintainer, then replicate across the other 10? *(Recommended — one clean template beats 11 parallel
   half-migrations.)*
