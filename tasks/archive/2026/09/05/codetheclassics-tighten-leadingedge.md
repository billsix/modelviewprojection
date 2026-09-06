# Tighten leadingedge (Code the Classics vol 2)

**Status:** DONE + ARCHIVED 2026-09-05 — frame 180 AE=0 vs HEAD, 1500-frame input trace structurally identical, ruff + ty clean, 104 tests; staged (maintainer commits). **One deliberate visible deviation: the title-screen fade now fades** (see the work record). Audio (engine-note crossfades, skid loop) and gamepad unverified by harness — play-test.
**Priority:** 5
**Difficulty:** 6
**Part of:** `tasks/archive/2026/09/05/codetheclassics-tighten-games.md` · **Depends on:** `tasks/archive/2026/09/05/codetheclassics-tighten-kinetix.md` (vol2 engine) · **Next:** `tasks/codetheclassics-tighten-beatstreets.md`
**Engine family:** vol2 (≡ eggzy/beatstreets engine, +3 line offset). Widest alias line (57): `_text = audio = gldraw = joystick = surface = transform`. **The only game that uses `Sound.play(loops=…, fade_ms=…)`, `Sound.fadeout/set_volume/stop`** (3581–3621, 3306) and `transform.scale` (via `SCALE_FUNC` 2741) — restore the mixer's fade/loop paths and `transform.scale` here. Also the only game with **`update(delta_time)`** (4934; the loop passes `_dt` 5128).

## BLUF

Apply `tasks/reference/code-the-classics-tightening.md` to
`ports/codetheclassics/vol2/leadingedge/leadingedge.py` (5151 lines). Medium-high: `Profiler`,
`Scenery`, `TrackPiece` are prime `@dataclass(slots=True)` targets, `Car.__post_init__` needs its
`image` declared, and the 678-line `Game.draw` (4188–4865) has dozens of single-use locals.
Risk: `Game()` builds the whole attract-mode race at import with RNG.

## Context (read first)

- Shape (HEAD 2026-09-05): banners 59 … 2671; game code from 2675; `__main__` at 5075.
- Import-time: `surface.Surface((WIDTH, HEIGHT))` 2821; `PERFORMANCE_MODE` conditional constants
  2720–2737; `mixer.quit/init` + `play_music("title_theme")` 5047–5049; `setup_joystick_
  controls()` 5058; **`game: Game = Game()` 5062 → `make_track()` → `generate_scenery` (~24
  `images.*` loads) + `CPUCar` RNG (`choice` 3184, `uniform` 3194) per car**. No `ty: ignore`.
- Related: `tasks/archive/2026/09/05/codetheclassics-leadingedge-projection-functions.md`
  (world→camera as `inverse(translate)` in g3 — keep that code as is).

## Analysis

**Engine dead here:** `_Painter.rect/filled_rect/line/circle` (only `screen.draw.text` 4579/4851
live), `draw.rect/line` (`gldraw.polygon` 4429, `gfx_filled_polygon` 4423, `gfx_polygon` 4427
live), `transform.smoothscale` (mentioned only in comment 2741), `Surface.blit/get_*/gl_texture`
(game uses `Surface(...)` 2821, `.set_alpha` 5002, `.fill` 5003 — keep those), `mask`, `_Keys`,
`_MixerSound`, `_RectBase.contains/move/move_ip/inflate/copy`, `_Music.play_once/get_volume/
fadeout`, `Screen.clear/bounds`, `Renderer.set_clip`, `Image.from_rgba/get_rect`,
`_Loader.values/clear`, `audio.available`, `JoystickControls.get_y` 3028 (dead).
Used: **`images.<attr>` ×24** (3060 … 5015) + `getattr(images, …)` ×4 → `load()` (a mechanical
rewrite of 28 sites — or keep `_Loader.__getattr__` un-slotted here; decide once for vol2);
`getattr(sounds, …)` 3284, 4893; `screen.draw.text`; `screen.surface` 4424–4430; `screen.blit`
×9; joystick; `music.play` 5027 / `stop` 5035.

**Game classes:** **`Profiler` 2825 → `@dataclass(slots=True)` + `__post_init__`** (`start_time =
perf_counter()` is derived); `Controls` 2945 ABC (keep); `Scenery` 3043 dataclass — **best
`slots=True` candidate**; `StartGantry`/`Billboard`/`LampLeft`/`LampRight` (single positional
`super()` each; `Billboard.__init__` 3081 computes `half_width`); `TrackPiece` 3118 dataclass
(`cars` default_factory); `TrackPieceStartLine`; `Car` 3136 dataclass — **`image` 3146 set in
`__post_init__` undeclared** → declare; `CPUCar` 3182 (not a dataclass, comment 3179–3181; RNG
in the super call — leave); `PlayerCar` 3263 (try/except sound load, `update_engine_sound()`);
`Game` 3938 — hand `__init__` (`make_track()` 3940, `setup_cars` 3946 sets `cars` 3970,
`play_music` 3965) → declare `cars`, keep order.

**Function-tightening candidates:** 3595–3600 `direction` if/elif → the file's own `sign()`
2884; 3168 4-branch `frame` → `match`/expression; 2926 `sum([...])`; 4850 `range(len(...))`;
4990 `draw()` single `if state == State.TITLE` while `update` uses `match` — make both `match` +
`case _: raise`; `Game.draw` 4357–4401: ten consecutive single-use `*_screen = transform(*)`
locals — inline where used once; `Profiler.get_ms` 2830 single-use locals; `stop_music`/
`play_music` 5025–5035 identical wrappers.

**pygame comments in the game part (12):** 2694/2698 (gfxdraw note — rewrite to "the polygon
helpers live in the draw section"), 3004 as "no-op here", **4627 keep** (the >1 GB bitmap clamp
rationale, reworded without the framework name), 4887–4896 (`getattr` idiom), 4931 false, 5045
(mixer restart — no-ops), 5069 false, 5071 → banner, 5121 env var.

## Plan, as scaffolded before the work (the record below is what happened)

Engine: splice kinetix's, restoring the `Sound` fade/loop/volume/stop paths, `transform.scale`,
`Surface`, `screen.draw.text`, the polygon helpers. Game: the dataclass list, `match` blocks,
`sign()`, inline the `_screen` locals, header (vol 2 © 2024), comments. Gates as boing — note
the trace must call `update(_dt)` (harness: pass `1/60`). Open question: `images.<attr>` ×24 →
`load()` rewrite, or keep the attribute idiom (and an un-slotted `_Loader`) for this game?
*(Recommend rewrite — mechanical, and it is what makes the loader typed and slots-safe.)*

## Work record (2026-09-05)

- **Engine:** `splice_vol2_engine.py leadingedge "Leading Edge" left,right,lctrl,z,lshift,x,escape
  960x540 joystick,surface,sound,fill,polygon,scale,text` — three new flags: **`polygon`**
  (`Renderer.polygon(points, color, filled)`, a triangle fan or line loop on the `prim` buffer;
  replaces `gldraw.polygon`/`gfx_filled_polygon`/`gfx_polygon` and the `USE_GFXDRAW` switch, which
  all reached the same call), **`scale`** (`scale_image(image, w, h)`, nearest-neighbour via
  Pillow — was `transform.scale`/`SCALE_FUNC`), **`text`** (bunner's Pillow text section as
  `draw_system_text`, for the debug overlays; the game's own bitmap `draw_text` keeps its name).
  The vol1 splice's key table gained aliases (`lctrl` → `KEY_LEFT_CONTROL`, `lshift`, `rctrl`,
  `rshift`). `mixer.quit/init` and the `play_music`/`stop_music` wrappers are gone (`music.play`/
  `music.stop`, which never raise).
- **The fade (deliberate deviation, flagged):** HEAD's shim applied `set_alpha` by scaling the
  surface's pixel alpha and then `fill((0,0,0))` reset it to opaque, so the "fade to black" at each
  demo (re)start was a solid black screen for one second (captured: frame 30 of HEAD is black
  behind the logo; the tightened frame 30 shows the race through a translucent black). The
  tightened game fills first, then scales the alpha, which is the fade upstream's pygame code
  produces. Frame 180 (outside the fade window) is byte-identical; the frame-30 gate differs by
  exactly this.
- **Classes:** `Profiler` → `slots=True` dataclass (`start_time` a `perf_counter`
  `default_factory`); `Scenery`/`TrackPiece`/`Car` → `slots=True` (`Car.image` declared
  `init=False`), their subclasses `__slots__ = ()`; `CPUCar`/`PlayerCar` plain with `__slots__`
  (dataclass-over-dataclass would merge the fields into the subclass signature, and `CPUCar` picks
  its letter randomly for the super call); **`Game` → dataclass** (`controls` an `InitVar`; the
  fourteen others `init=False`; `__post_init__` keeps `make_track()` → `setup_cars` → camera →
  background → start timer + music); a new frozen **`TrackPieceScreen`** (ten projected edge points)
  replaces the eight loop-carried `prev_*` locals in `Game.draw` — the ten points share a piece's Z,
  so the old "left and right in front of the clipping plane" test is exactly "all ten are"; the
  `Controls` ABC slotted with `ClassVar` `NUM_BUTTONS`, `button_down -> bool` (was `bool | None`),
  the dead `JoystickControls.get_y` deleted.
- **Functions:** the local `transform(point, w=None, h=None, clipping_plane)` that returned
  `None | Vector | (Vector, w, h) | (None, None, None)` → **`project`** and **`project_sprite`**,
  each with one return type; `draw_polygon`/`any_on_screen`/`draw_points` (redefined every loop
  iteration) → one `draw_points` closure; `cars_to_draw` dicts → `(z, draw call)` tuples;
  `update_sprite`'s frame chain, `sign`, `move_towards`, `inverse_lerp`, the start-gantry index,
  the fill colour, the camera-follow choice → conditional expressions; the PlayerCar `direction`
  chain → the file's own `sign(x_move)`; `is_target_x_too_close_to_nearby_cars` → `any`;
  `times[type]` → `dict.get`; `get_first_track_piece_ahead -> tuple[int | None, float]` (the Z is
  always computed; four `assert … is not None` document that the camera and player never leave
  the track, where the old code would have raised `TypeError`); `cast(CPUCar, car)` → an
  `isinstance` check; `images.<attr>` ×24 and `getattr(images, …)` ×4 → `images.load(...)`;
  `xy(v)` turns a g2 screen vector into the renderer's pixel pair. `Colour` and the other tables
  are typed. Deleted: the DPI-awareness and version-check blocks, the commented-out test polygon.
- **Numbers:** 5151 → 3784 lines (−27%); pygame/pgzero mentions 163 → 2 (the
  `PGZERO_MAX_FRAMES` env var).
- **Gates:** frame 180 AE=0 vs HEAD (the original 5151-line file); 1500-frame input trace (title →
  race; countdown, accelerating, steering both ways, braking, off-track resets — 2358 resetting
  frames — and CPU-car collisions) identical under `compare_traces.py` with only the
  `Image`/`Sound`/`Surface` internals opaque. `state_trace.py` now passes `1/60` to an `update`
  that takes a delta, dumps g3 vectors with their z, and takes a 4th argument of attribute names
  to skip (`track`: 3000 pieces would swamp the dump; the cars' own `track_piece` still dumps).
  ruff + ty clean on vol1/vol2; 104 tests. Not reached: the gamepad, a completed race
  (five laps), the `DEBUG_*` overlays.

## Open question — settled by Fable (maintainer had delegated discretion)

- `images.<attr>` → `images.load(...)`: rewritten (28 sites), as recommended; the loader stays
  typed and slotted.
