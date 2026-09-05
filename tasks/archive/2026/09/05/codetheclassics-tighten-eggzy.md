# Tighten eggzy (Code the Classics vol 2)

**Status:** DONE + ARCHIVED 2026-09-05 — frame 180 AE=0 vs HEAD, 1500-frame input trace structurally identical (two levels, a game over, a second game), ruff + ty clean, 104 tests; staged (maintainer commits). Audio and gamepad unverified by harness — play-test.
**Priority:** 5
**Difficulty:** 5
**Part of:** `tasks/archive/2026/09/05/codetheclassics-tighten-games.md` · **Depends on:** `tasks/archive/2026/09/05/codetheclassics-tighten-kinetix.md` (vol2 engine) · **Next:** `tasks/codetheclassics-tighten-leadingedge.md`
**Engine family:** vol2 — `eggzy.py:56–2671` ≡ `beatstreets.py:55–2670` ≡ `leadingedge.py:59–2674`. Splice kinetix's tightened engine; eggzy's alias line 54 (`_text = audio = gldraw = joystick`) means `surface`/`transform`/`mask` are already unreachable here.

## BLUF

Apply `tasks/reference/code-the-classics-tightening.md` to
`ports/codetheclassics/vol2/eggzy/eggzy.py` (4727 lines). Medium opportunity: two big string
`if/elif` chains → `match`, a string accumulator → `join`, and the unreachable
`surface`/`transform`/`mask`/`_Keys`/`_MixerSound` engine sections. `Player` is the risk.

## Context (read first)

- Shape (HEAD 2026-09-05): banners 56 … 2668; game code from 2672 (`WIDTH` 2674); `__main__` at
  4651. `update()` no `dt`.
- Import-time: `mixer.quit/init` + `play_music("title_theme")` 4619–4622; **`load_replays()` 4635
  (file I/O, `os.getcwd()`/`expanduser` 4368–4369)**; `setup_joystick_controls()` 4633; no
  module-level image loads (`tileset_images = {}` 4628, filled lazily 4054). One `ty: ignore` 4241.

## Analysis

**Engine dead here:** the whole `surface` section 1478–1635 (`Surface`, `SRCALPHA`), `transform`
(`scale`/`smoothscale`), `mask`, `_Keys` + `keys`, `_MixerSound`/`_pooled_sound`/
`mixer.Sound/set_num_channels/get_busy`, `_RectBase.contains/move/move_ip/inflate/copy`,
`Sound.stop/set_volume/fadeout/get_volume` (eggzy only does bare `.play()` 4282), `_Music.stop/
play_once/get_volume/fadeout`, `Screen.clear/bounds`, `Renderer.set_clip`/`_Surface.set_clip`,
`draw.line/polygon/gfx_*`, `_Painter.line/circle/filled_circle/text`, `Image.from_rgba/
get_rect`, `_Loader.values/clear`, `Actor.__iter__`, `audio.available`.
Used: `getattr(images, …)` 3117, 3122, 4296, 4299 and `getattr(sounds, …)` 4281 → `load()`;
`screen.fill` ×2; `screen.surface.blit` 4191 (with `area=` — **keep `draw_image(src=…)`**),
`screen.draw.rect` 3666/3816/4213, `gldraw.rect` 4219; `screen.blit` ×13; joystick fully used
(2895–2931); `music.play/set_volume`.

**Game classes:** `Biome` Enum; `Controls` 2812 ABC (keep); `Gem` 2947 dataclass + `InitVar` —
**`__post_init__` mutates class state** (`next_type` ClassVar, 2964–2967), keep; `Door` 2986
dataclass + two InitVars — `__post_init__` sets `frame` *before* `super().__init__` (image name
depends on it) — keep the order; `Animation` 3023 (5 fields, calls `update_image()`),
`DashTrail`, `CollideActor` 3070 (single `super()` — pure boilerplate), `GravityActor` 3130
(nested `FallState` enum; 4 fields); `Player` 3197 dataclass — **four attributes created outside
`__post_init__`** (`start_pos` 3234, `stomped_last_frame` 3329, `previous_grabbed_wall` 3413,
`flame_image` 3578) and four inherited from the non-dataclass `GravityActor` → declare all eight
before `slots=True`, or leave `Player` un-slotted with the reason; `GhostPlayer` 3677
dataclass; `Enemy` 3704 (not a dataclass, comment 3702–3703 says why — leave); `Game` 3819 —
hand `__init__` calling `Gem.new_game()` 3827 + `next_level()` 3850, which sets `block_rects
doors gems enemies animations exit_open collision_tiles` → declare, `__post_init__` in order.

**Function-tightening candidates:** 3986 4-branch `if/elif` on `object_name` (no else) →
`match` + `case _: raise`; 3574 6-branch + else in `determine_sprite` → `match`/expression; 3587
4-branch on `fall_state` → `match`; 4387–4394 `line += …` accumulator → `";".join(...)`; 4304
`sum([...])`; 3173 `.format` → f-string (3057's `image_format_str.format` is data — keep);
3281/3746 `del detect` dead parameter (documented); 4071/4073/4175 `range(len(...))` →
`enumerate`; 4085/4087 duplicated `if current_rect is not None: add()`; `Controls.button_name`
2851 abstract with a body.

**pygame comments in the game part (12):** keep-the-rationale: 3106 ("we don't use the sprite
bounds" — why `get_rect` is custom), 4183–4184 (why `screen.surface.blit` with `area`), 4275–4284
(`getattr` idiom — moot with `load()`); 2895 as "no-op here"; **delete/rewrite:** 4454 false,
4617 (mixer restart — no-ops now), 4646 false, 4648 → banner; 4697 env var.

## Plan / Verify / Open questions

Engine: splice kinetix's, restore `draw_image(src=…)`, `screen.draw.rect`, `gldraw.rect`,
joystick. Game: `Game`/`Player` fields, the `match` conversions, `join`, header (vol 2 © 2024),
comments; drop the 4241 suppression's cause if possible. Gates as boing; run the trace from the
game dir (replay files are CWD-relative) with a key script that moves, dashes and collects a gem.
Open question: `Player` → `slots=True` with eight declared fields, or leave un-slotted?
*(Recommend declare — the list is known and the trace proves it.)*

## Work record (2026-09-05)

- **Engine:** `splice_vol2_engine.py eggzy Eggzy left,right,up,down,space,z 825x550
  joystick,collide,fill,rect,region` — four new flags for this game: **`collide`** (a `RectLike`
  Protocol of four edges; `Rect.colliderect`; **`IntRect`**, pygame's whole-pixel mutable rectangle
  the level builder grows in place; `Actor.colliderect`/`distance_to`/`centerx`/`centery`),
  **`fill`** (`Renderer.fill`), **`rect`** (`Renderer.filled_rect` on the quad + the one-pixel
  outline `rect` on the `prim` buffer, shared with `lines` via an idempotent `ensure_prim`), and
  **`region`** (`Renderer.draw_image_region(image, topleft, region)` — one tile of the tileset;
  replaces `screen.surface.blit(..., area=)`). The engine's float `Rect` stays the Actor's; the
  game's collision rects are `IntRect`, truncated at the one float call site (`get_rect`) exactly
  as pygame's `Rect` did.
- **Classes:** `Gem`/`Door`/`Player`/`GhostPlayer` → `slots=True` with every attribute declared
  (`Gem.type`, `Door.opening/last_frame/frame`, `Player.flame/start_pos/stomped_last_frame/
  previous_grabbed_wall` — the last two with defaults that are never read before being set);
  **`Game` → dataclass** (`player` + an `InitVar` `replays`; the nineteen others `init=False`;
  `__post_init__` keeps the order `Gem.new_game()` → ghosts → `next_level()`); `Animation`,
  `CollideActor`, `GravityActor`, `Enemy` plain with `__slots__` (constructors compute the base's
  inputs). **`GravityActor.update(detect)` → `fall(detect)`**: each subclass's `update()` calls it
  first, so the two `del detect` Liskov shims and their `@override`s are gone. A `GameObject`
  Protocol types the per-frame lists; `Replay` is a `type` alias. `game: Game` is a bare declaration
  (bound at the first start); the one real "is there a game yet" check — `Player.reset` runs during
  `Game` construction, when the global is unbound (or, on a later game, still the *previous* game,
  whose nearby enemies it then destroys, consuming RNG exactly as upstream) — is `if "game" in
  globals()`, the honest typed spelling of upstream's `if game is not None`.
- **Functions:** the two `object_name` chains → `match` with `case _: raise` (the 21 level files
  contain only PlayerStart/Gem/Enemy*/Door/EntranceDoor objects — checked); `button_name` ×2 and
  `draw_text`'s alignment → `match`; `save_replays`' accumulator → `";".join`; `load_replays`
  unpacks entries; `high_score` → `max(..., default=0)`; `position_blocked` → one `any`/`or`
  expression (same short-circuit order); the grid → a comprehension; `generate_block_rects` →
  `enumerate` + `next(..., None)`; `_find(node, path)` replaces the `cast(Any, …)` XML lookups and
  raises on a malformed level file; `getattr(images, …)` ×4 → `images.load(...)` (the special
  font symbols via `dict.get`); the dead `self.flame_image = "blank"` write (a typo for
  `self.flame.image`, which was already blank) deleted; the redundant `screen.fill((0,0,0))` on the
  controls screen dropped (the frame is cleared to black); `mixer.quit/init` and the `play_music`
  try/except gone (`play_music` stays: three callers, two lines). **Left as if-chains:**
  `determine_sprite`'s in-air branch (mixed enum equality and a `dash_timer` guard).
- **Numbers:** 4727 → 3326 lines (−30%); pygame/pgzero mentions 162 → 4 (the
  `PGZERO_MAX_FRAMES` env var and the int-Rect rationale).
- **Gates:** frame 180 AE=0 vs HEAD (the original 4727-line file); 1500-frame input trace (title →
  controls → play; runs, jumps, dashes, wall grabs; all gems of level 1 collected and the exit
  taken; the timer ran out, game over, a second game started with the first as a ghost — which
  exercises the previous-game `reset` quirk) identical under `compare_traces.py`, ignoring the
  rect-derived keys (`x/y/w/h/right/bottom/center*/mid*/size/class`: the old `Rect` dumped
  fourteen derived properties, `IntRect` dumps its four fields — `left/top/width/height` compared),
  the four newly-declared `Player` fields, and the `Image` internals. `state_trace.py` now sets
  `sys.path[0]` to the game's directory (eggzy finds `tilemaps/` there); the replay save file the
  game writes at game over was deleted between runs so neither run loaded the other's. ruff + ty
  clean on vol1/vol2; 104 tests. Not reached: the gamepad, the `~/.code-the-classics-vol-2` save
  path, the `DEBUG_*` overlays.

## Open question — settled by Fable (maintainer had delegated discretion)

- `Player` → `slots=True` with the eight fields declared (the trace proved the list).
