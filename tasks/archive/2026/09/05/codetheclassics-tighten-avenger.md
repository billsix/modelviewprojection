# Tighten avenger (Code the Classics vol 2)

**Status:** DONE + ARCHIVED 2026-09-05 — frame 180 AE=0 vs HEAD, 1500-frame input trace structurally identical, ruff + ty clean, 104 tests; staged (maintainer commits). Audio (thrust loop fade-in/out, per-shot volume) and gamepad are unverified by harness — play-test.
**Priority:** 5
**Difficulty:** 6
**Part of:** `tasks/archive/2026/09/05/codetheclassics-tighten-games.md` · **Depends on:** `tasks/archive/2026/09/05/codetheclassics-tighten-kinetix.md` (vol2 engine) · **Next:** `tasks/codetheclassics-tighten-eggzy.md`
**Engine family:** vol2 — splice kinetix's tightened engine; avenger is the **only game that builds `mixer.Sound(...)`** (4196) and uses `Sound.play(loops=-1, fade_ms=200)`, `fadeout`, `set_volume`, `stop` — restore `_MixerSound`, `_pooled_sound`, `mixer.set_num_channels` and the mixer's fade/loop paths here.

## BLUF

Apply `tasks/reference/code-the-classics-tightening.md` to
`ports/codetheclassics/vol2/avenger/avenger.py` (4456 lines). `Game` (3880) is the cleanest
dataclass target in the tree (13 fields, none set later); `transform` is dead and `Mask` is
partly live; `Enemy.__init__` is the single highest-risk conversion (five RNG calls interleaved
with `match`).

## Context (read first)

- Shape (HEAD 2026-09-05): banners `_types` 55 … aliases 2667; game code from 2671; `__main__` at
  4380; alias line 53 `_text = audio = joystick = mask = sys.modules[__name__]`. `update()` no `dt`.
- Import-time: version check 2673; **`mixer.quit/init/set_num_channels(16)` + `play_music("menu_
  theme")` 4342–4353**; `setup_joystick_controls()` 4360; `game: "Game" = cast("Game", None)` 4372
  (4-line justification 4368–4371 — no `Game` at import). One `ty: ignore` 2888 (`WrapActor.draw`).

## Analysis

**Engine dead here:** whole `transform` 1740–1763; `Mask.overlap` 1721 (`from_surface`/`get_size`/
`get_at` **live** at 3903/3857/3863); `Image.get_height/get_rect/from_rgba` (`get_width` live
4047/4214); `_Loader.load/values/clear`; `Screen.clear/fill` (`bounds` live 3026);
`Renderer.draw_image(direct)/filled_rect/polygon/circle`; `_Painter.filled_rect/circle/
filled_circle`; `_Painter.rect` (only the commented-out 3743) and `_Painter.text` (all six call
sites 4135–4140 commented out); `Surface` class (3 game `Surface`s are `Image`s) + `set_alpha/
get_rect/blit/fill`; `_Surface.get_width/get_height/get_size/blit` (`set_clip` live 4088/4107);
`_RectBase.contains/move_ip/inflate/copy`; `Actor.distance_to`; `Sound.get_volume`;
`_Music.play_once/stop/set_volume/get_volume/fadeout`; `gfx_filled_polygon/gfx_polygon/
polygon`; `mixer.find_channel/get_busy`; `_Keys`.
Used: `images.background` 4047, `images.terrain` 3902 (attribute style) + `getattr(images, …)`
4213 → `load()`; `getattr(sounds, …)` 4199; `sounds.thrust0` 3021; `screen.draw.line` 3737
(**live, behind `SHOW_DEBUG_LINES`**); `screen.surface.set_clip`; `screen.blit` ×10; joystick
fully used; **`mixer.Sound("sounds/…ogg")` 4196 + `set_volume`**; `Sound.play(loops=-1,
fade_ms=200)` 3189–3191, `fadeout(200)` 3052/3196, `set_volume` 3188, `stop` 3048.
**7 commented-out debug lines** (3743, 4135–4140) — delete outright.

**Game classes:** `Controls` 2762 ABC (keep); `WrapActor` 2873 (pure `super()`); `Bullet` 2907
dataclass + `InitVar spawn_pos` (`__post_init__` plays a distance-attenuated sound); `Laser`
2939 (not a dataclass — super args computed, comment 2937–2938, leave); `Player` 2977 dataclass —
all set-later attrs are declared **except `thrust_sound` 3021** (try/except load in
`__post_init__`) → declare `thrust_sound: Sound | None = field(default=None, init=False)`, keep
the load in `__post_init__`; `Radar` 3318; `Enemy` 3348 — **RNG-order-bearing `__init__`**
(`randint` 3363, `uniform` ×2 3389–3390, `randint` 3411, `randint` 3419, two `match self.type`
blocks assigning the same attrs in different arms) — convert only with the exact order
preserved, else leave and say why; `Human` 3747 dataclass + `InitVar` (all declared); **`Game`
3880 → dataclass** (13 fields; `__post_init__` calls `new_wave()` 3906 and
`play_music("ambience")` 3907 in that order).

**Function-tightening candidates:** 3205–3206 `tilt` → conditional expression; `Human.update`
3810/3813 if/elif chains on `self.carrier` → `match` + `case _: raise`; 3642 two-branch
`EnemyType` check → `match` with `case _: raise`; 3507 `len(...) > 0`; 3944 loop-var rebinding →
comprehension; 4130–4133 `y` accumulator → `enumerate`; 4142–4166 `get_wave_end_text` appends →
list literal/slice; 3443–3450 RNG loop — **leave**; `get_joystick_if_exists`/`setup_joystick_
controls` 4241–4253 duplicate kinetix's (fine — per-game duplication is intended), but fix the
local shadowing the module `joystick`.

**pygame comments in the game part (7):** 2831 (keep as "no-op here"), 4185–4190 (keep the
`getattr` rationale or drop with `load()`), 4202–4203 keep ("print the error, includes the
filename"), 4264 false, 4343–4348 (mixer restart rationale — the mixer calls are no-ops now; keep
only the `set_num_channels(16)` reason if the real mixer honours it), 4375 false, 4377 → banner.

## Plan, as scaffolded before the work (the record below is what happened)

Engine: splice kinetix's, restoring `_MixerSound`/`_pooled_sound`, the `Sound` fade/loop/
volume/stop paths, `Mask` (minus `overlap`), `set_clip`, `screen.draw.line`. Game: `Game` and
`Player` fields, `Enemy` decision, `match` conversions, delete the 7 commented lines, header,
comments. Gates as boing; key script: thrust + fire so bullets/lasers/enemies spawn (RNG paths).
Open question: does the real mixer honour `set_num_channels(16)`? If not, it and its comment go.

## Work record (2026-09-05)

- **Engine:** `splice_vol2_engine.py avenger Avenger left,right,up,down,space 960x540
  joystick,clip,sound,mask,lines` — kinetix's vol2 engine plus three new flags added for this game:
  **`sound`** (the full software-mixer sound API: `Sound.play(loops=, fade_ms=, volume=)`,
  `fadeout`, `set_volume`, `stop`, and `_Music.fadeout`), **`mask`** (`Mask` dataclass +
  `mask_from_image(image)`, `get_at`/`width`/`height`; `overlap` not spliced — dead here), **`lines`**
  (`Renderer.line` with its own `prim` GL buffer, behind `SHOW_DEBUG_LINES`). `Renderer.set_clip`
  now takes floats (the radar rect is float arithmetic; kinetix updated to match). The old
  `_MixerSound`/`_pooled_sound`/`mixer.Sound("sounds/…ogg")` path is gone: its only purpose was a
  per-play volume, which `Sound.play(volume=…)` gives directly, so `Game.play_sound` is three lines.
  `mixer.quit/init/set_num_channels(16)` dropped — the software mixer has no voice cap (its
  `_CHANNELS = 2` is stereo output), so the open question ("does the real mixer honour
  `set_num_channels`?") resolves as: nothing to honour.
- **Classes:** `Bullet`/`Player`/`Human` → `slots=True` (`Player.thrust_sound: Sound | None`
  declared `init=False`, still loaded in `__post_init__`; `Player.carried_human: Human | None`;
  `Human.carrier: Player | Enemy | None`; `Enemy.target_human: Human | None`); **`Game` →
  dataclass** (`player` the one init field; the twelve others `init=False`, `__post_init__` keeps
  the original order: camera offset, terrain image + `mask_from_image`, `new_wave()`,
  `music.play("ambience")`); `Enemy` **left plain** (its `__init__` interleaves five RNG calls
  with two `match self.type` blocks — converting would risk the RNG order for no gain), now with
  `__slots__` and `case _: raise` on both `match self.type` blocks plus explicit `case
  EnemyType.POD | EnemyType.SWARMER: pass` (appear silently) and `case EnemyState.DEAD: pass`;
  `Laser`/`Radar`/`WrapActor` slotted; the `Controls` ABC slotted with `NUM_BUTTONS` a `ClassVar`;
  `JoystickControls` takes the engine's `Joystick` (its pygame `init()` call gone). The widened
  `WrapActor.draw(offset_x, offset_y)` override (and its `ty: ignore`) → **`draw_at`**, with a
  `GameObject` Protocol typing the per-frame draw list. `game: Game` is a bare module-level
  declaration (bound at the first start; the title screen never reads it), replacing
  `cast("Game", None)` and the reset-to-None on returning to the title — the finished game
  simply lingers until replaced.
- **Functions:** `sign`, the tilt suffix, the camera target, the unit-vector fallback, the
  wave-end line → conditional expressions; `wrap_distance` hoisted out of the 20-iteration
  respawn loop (it captured nothing); `new_wave`'s human loop → comprehension; `laser_hit_test`
  ×2 → early return; `text_width` → generator; the wave-end `y` accumulator → `enumerate`;
  `getattr(images, font + "0" + str(ord(c)))` → `images.load(f"{font}0{ord(char)}")`,
  `images.background.get_width()` → `.width`, `get_size()` → `.width/.height`; the seven
  commented-out `screen.draw.text/rect` debug lines deleted; `play_music` wrapper and the
  `get_joystick_if_exists` shadowing of the module `joystick` gone; the `sys.version_info` check
  gone. **Left as an if-chain:** `Human.update`'s sprite selection (mixed guards on
  carrier/falling/waving — a `match` there would be boolean-guard cases, which the house rule
  says not to convert).
- **Numbers:** 4456 → 2989 lines (−33%); pygame/pgzero mentions 159 → 2
  (the `PGZERO_MAX_FRAMES` env var).
- **Gates:** frame 180 AE=0 vs HEAD (the original 4456-line file); 1500-frame input trace
  (title → play; thrust left/right/up/down, fire; enemies appear, one explodes, a life is lost,
  score 150) identical under `compare_traces.py` (ignoring the derived
  `left/right/centerx/centery/width/height`, the `thrust_sound` object, and the `Image`/`Mask`
  internals: the mask's ndarray and the image's path are new/removed attributes, not state);
  the title-screen frames' `'game': None` (now unbound) stripped from the baseline before
  comparing. ruff + ty clean on vol1/vol2; 104 tests. Not reached by the script: human pick-up
  and rescue, pods/swarmers (wave 1 has none), the gamepad.
- **Found, not fixed (recorded on the umbrella):** `ports/codetheclassics/_smoketest.py` imports a
  game as a module, which no game has allowed since the games own their loops (and the import
  guard now exits) — it is dead, and `verify_game.sh` supersedes it.
