# Tighten beatstreets (Code the Classics vol 2)

**Status:** DONE + ARCHIVED 2026-09-05 — frame 180 AE=0 vs HEAD, 1500-frame input trace structurally identical, ruff + ty clean, 104 tests (one of them caught a real trap, below); staged (maintainer commits). **One deliberate visible deviation: the post-intro fade now fades** (see the work record). Audio and gamepad unverified by harness — play-test.
**Priority:** 6
**Difficulty:** 7
**Part of:** `tasks/archive/2026/09/05/codetheclassics-tighten-games.md` · **Depends on:** `tasks/archive/2026/09/05/codetheclassics-tighten-kinetix.md` (vol2 engine) · **Next:** none (umbrella archives after this)
**Engine family:** vol2 (≡ eggzy/leadingedge engine, −1 line offset). Alias line 53 `_text = audio = joystick = surface` — `gldraw`, `transform`, `mask` unreachable. **Keeps the full `_Mixer` (`find_channel`/`get_busy`, 4297)** — but see the trap below.

## BLUF

Apply `tasks/reference/code-the-classics-tightening.md` to
`ports/codetheclassics/vol2/beatstreets/beatstreets.py` (6022 lines). High opportunity: four
large enum `if/elif` chains → `match` (7-, 8-, 5-, 5-branch), `Stage` and `Attack` → `slots=True`,
and a ~130-line scooter-sound-channel path that is dead at runtime. Deepest class hierarchy
(`Fighter` has a 22-field, 13-parameter `__init__`).

## Context (read first)

- Shape (HEAD 2026-09-05): banners 55 … 2667; game code from 2671; `__main__` at 5946. `update()`
  no `dt`. Five `ty: ignore` in the game part: 3114 (`draw(self, offset)` widened override),
  3263, 4670, 4683, 4705.
- Import-time: `debug_drawcalls = []` 2728; `fullscreen_black_bmp = surface.Surface(…)` +
  `.fill` 2852–2853; **`with open(attacks.json)` 3079–3085 — file I/O + `Attack(**value)` per
  entry, and `Attack.__post_init__` rewrites `combo_next` in place (3071–3073)**; `mixer.quit/
  init` + `music.play("theme")` + `set_volume(0.3)` 5919–5922; `setup_joystick_controls()` 5931;
  `game: "Game" = cast("Game", None)` 5939 (documented 5935–5938); `STAGES: Any` 4915 filled later
  by `setup_stages()` from `Game.__init__`.

## Analysis

**Engine dead here:** whole `draw` section 1635–1684, `transform`, `mask`, `_Keys`,
`_MixerSound`/`_pooled_sound`/`mixer.Sound/set_num_channels`, `Sound.stop/set_volume/fadeout/
get_volume` (the `.stop()`/`.set_volume()` hits 4408/4427/4338 are on the scooter *channel*),
`Surface.blit/get_*/gl_texture` (game uses `Surface(...)` 2852, `.fill`, `.set_alpha` 5618),
`_RectBase.contains/move/move_ip/inflate/copy`, `_Music.play_once/get_volume/fadeout`,
`Screen.clear/bounds`, `Renderer.set_clip`/`_Surface.set_clip`, `_Painter.filled_circle`,
`Image.from_rgba/get_rect`, `_Loader.values/clear`, `audio.available`.
**Runtime-dead by design:** `mixer.find_channel()` 2619 returns `None`, so `EnemyScooterboy.
scooter_sound_channel` 4297 is always `None` and every guarded branch (4299, 4338, 4352, 4390,
4408, 4427) never runs; `Game.shutdown` 5718 loops `enemy.died()` only for that channel. Decide:
delete the path (and `find_channel`/`get_busy`), or implement channels in the mixer (a feature).
Used: `images.title0/title1` 5872, 5900, 5902 (attribute) + `getattr(images, …)` ×4 → `load()`;
`getattr(sounds, …)` 5726; **`screen.draw.text` ×6** (3608, 3630, 5627, 5630 + commented
5843–5844); `screen.surface` 5659/5668; `screen.blit` ×11; joystick; `music.play/set_volume`;
`sounds.*.play()` no args 5740.

**Game classes (19):** **`Profiler` 2732 → `@dataclass(slots=True)` + `__post_init__`**;
`Controls` 2914 ABC (keep); `Attack` 3037 dataclass + `flyingkick` InitVar — **`flying_kick`
3066 undeclared** → declare; keep the in-place `combo_next` rewrite (`attacks.json` load depends
on it); `ScrollHeightActor` 3096 (`vpos height_above_ground shadow_actor`); `Fighter` 3155
(ABC; nested `FallingState`; **22 fields, 13 params, straight-line assignment** — a dataclass
candidate but a large one; `kw_only=True` would read well at its call sites — judge); `Player`
3814, `Enemy` 3916 (nested `State`), `EnemyVax`/`EnemyHoodie`/`EnemyBoss` (one big kwarg
`super()` each — boilerplate), `EnemyScooterboy` 4273, `EnemyPortal` 4483, `Scooter` 4615,
`Weapon` 4636 (7 fields, 10 params), `Barrel` 4721, `BreakableWeapon` 4803, `Stick`/`Chain`,
`Powerup` 4855 — **`__init__(self, image, pos)` then `super().__init__(pos, image)`: the
parameter names are swapped** (callers pass `(pos, sprite_name)`) — behaviour-neutral rename;
`HealthPowerup`/`ExtraLifePowerup`; **`Stage` 4904 dataclass → `slots=True` outright**; `Game`
5367 — hand `__init__`: `Player(controls)` 5368, `setup_stages()` 5390, **`choice(stolen_items)`
5411** — RNG order must be kept if converted.

**Function-tightening candidates:** **3277 7-branch `if/elif` on `falling_state`, no else →
`match` + `case _: raise`**; 3642 8-branch + else in `determine_sprite` → `match`/lookup; 3848
5-branch `determine_attack` → `match`; 4530 5-branch `EnemyPortal.determine_sprite` → `match`;
3979 `Enemy.update` state machine → `match`; 3484, 3731, 4223, 4317, 4536, 4695, 5709 `x = …; if
…: x = …` → conditional expressions; 5593/5607/5649 `.format` → f-strings (debug-only); 5761
`sum([...])`; `move_towards` 2903 second return value often discarded; `died()` overrides 4265/
4415; `Game.shutdown` 5718 (scooter channel).

**pygame comments in the game part (12):** 2994 as "no-op here"; 3088–3089 (drop the
attribution, keep "read/write position via vpos"); **5653 keep** (why `screen.surface.blit`
with an area); 5733–5742 (`getattr` idiom); 5818 false; 5916 (mixer restart — no-ops); 5941
false; 5943 → banner; 5992 env var.

## Plan / Verify / Open questions

Engine: splice kinetix's, restoring `Surface`, `screen.draw.text`, `_Mixer.find_channel/get_busy`
only if the scooter path stays. Game: `Stage`/`Attack`/`Profiler` first (safe), then the
`match` conversions, then the constructor-boilerplate classes, `Game` last with its RNG order;
try to remove the causes of the five suppressions; header (vol 2 © 2024); comments. Gates as
boing; key script must fight (attacks), pick up a weapon, and reach a scooterboy wave.

1. **Scooter sound channel:** delete the runtime-dead path, or implement mixer channels?
   *(Recommend delete — the gap is documented as deliberate; deleting is behaviour-identical.)*
2. **`Fighter` → dataclass (`kw_only=True`)?** 22 fields; the subclasses' `super().__init__`
   kwarg calls already read keyword-only. *(Recommend yes, after the smaller classes prove the
   pattern; the trace covers it.)*

## Work record (2026-09-05)

- **Engine:** `splice_vol2_engine.py beatstreets "Beat Streets" left,right,up,down,space,z,lctrl,x,lalt,c,lshift,a
  800x480 joystick,surface,region,rect,lines,circle,text` — one new flag, **`circle`** (`Renderer.circle`
  outline on the `prim` buffer, for the anchor-point debug overlay), and the key table's `lalt`/`ralt`
  aliases. The health and stamina bars are `draw_image_region` cuts of their images (eggzy's flag);
  the level boundary is the engine's float `Rect` (its `left` is a plain field, so scrolling moves it
  as before); `mixer.quit/init` gone.
- **Open question 1 — the scooter sound channel: DELETED** (as recommended). `mixer.find_channel()`
  always returned None, so `scooter_sound_channel` was never set and its six guarded branches, the
  `spawned` override, `Game.get_sound` and the stereo-panning block never ran; ~130 lines gone with no
  behaviour change. `Game.shutdown()` **stays**: upstream used it to stop that sound, but `died()` also
  has real effects (a hoodie or scooterboy may drop a weapon, consuming RNG), so a finished game's
  state is unchanged — the comment says so now.
- **Open question 2 — `Fighter` → `@dataclass(eq=False, slots=True, kw_only=True)`: YES.** Its 22
  attributes are declared with `#:` docs (`speed`/`sprite`/`health` required, nine tunables with
  defaults, thirteen derived `init=False`); the constructor-only inputs are `InitVar`s named
  **`spawn_pos`/`spawn_anchor`** — the repo's `test_ctc_actor_field_collisions` caught my first
  attempt (`pos`/`anchor` shadow the Actor properties: the dataclass takes the property object as the
  field's default). `half_hit_area`'s gacalc-vector default needs a `default_factory` (dataclasses
  reject unhashable defaults). `Player`/`Enemy`/`EnemyPortal`/`EnemyScooterboy`/`Scooter`/`Weapon`/
  `Barrel`/`BreakableWeapon`/`Powerup` (+ the leaf subclasses) are plain classes with `__slots__`
  (their constructors compute the base's keyword inputs); `Attack`/`Stage`/`Profiler`/`Game` →
  `slots=True` (`Game` with `controls` an `InitVar`, `Player(controls)` → `setup_stages()` →
  `choice(stolen_items)` in the original RNG order). `Attack`'s fields are typed by what
  `attacks.json` holds (its `flyingkick`/`grab`/`throw`/`rear_attack` arrive as the string "True",
  which is truthy — noted on the class); its sound specs become tuples. `ScrollHeightActor.draw(offset)`
  (the widened override and its `ty: ignore`) → **`draw_at`** through the whole hierarchy; a
  `ScrollObject` Protocol (`vpos`, `update`, `draw_at`, `get_draw_order_offset`) types the per-frame
  lists. All five `ty: ignore`s are gone (`height_above_ground`/`stamina`/`hit_timer` typed `float`).
- **The fade (deliberate deviation, flagged):** HEAD's shim applied `set_alpha` by scaling the
  surface's pixel alpha *cumulatively* on a surface filled once at import: the post-intro fade
  collapsed to a hard cut within a few frames, and — because the surface's alpha was then 0 for good —
  a second game's intro text drew over the live level instead of over black. The tightened game fills
  then scales each frame, which is the fade upstream's pygame code produces. Frame 180 (title screen)
  is byte-identical; the trace never reached a second game.
- **Functions:** the `object_name`-style chains here are guard chains (kept); `Enemy.update`'s `match`
  gains `case RIDING_SCOOTER | PORTAL | PORTAL_EXPLODE: pass` and `case _: raise`;
  `EnemyPortal.update` gains `case PAUSE: pass` and `case _: raise`; `update()`/`draw()` gain
  `case _: raise`; `determine_sprite` ×2 and the Powerup/portal names → f-strings; four
  "is anyone else…" list-then-`len` checks → `any(...)`; `x_side` → `sign(...) or choice(...)`;
  `getattr(images, …)` ×4 and `images.title0/1`/`status_win/lose` → `images.load(...)`; the two
  upstream debug `print`s in `next_stage`/`update` ("create stage objects") deleted (they went to
  stdout in normal play — and they broke the baseline trace file, see gates); the commented-out debug
  stages and `# weapons=[...]` lines deleted; `Powerup.__init__(image, pos)` → `(pos, image)` (its
  callers always passed `(pos, name)` — behaviour-neutral rename); `Fighter.log`'s `str` parameter
  → `message`.
- **Numbers:** 6022 → 4749 lines (−21%); pygame/pgzero mentions 163 → 3 (the
  `PGZERO_MAX_FRAMES` env var and the int-Rect rationale).
- **Gates:** frame 180 AE=0 vs HEAD (the original 6022-line file); 1500-frame input trace (title →
  controls → play; the intro skipped; punches, a kick, an elbow, a flying kick, walking all four ways;
  the first stage's vax fought and beaten, score 20) identical under `compare_traces.py` with the
  rect-derived keys, `scooter_sound_channel` and the `Image`/`Surface`/`Sound` internals ignored; the
  baseline's dump was filtered to frame lines first (its debug prints were interleaved). ruff + ty clean
  on vol1/vol2; 104 tests. Not reached: weapons, scooterboys, bosses, portals, the second stage's
  scrolling, game over, the gamepad.
