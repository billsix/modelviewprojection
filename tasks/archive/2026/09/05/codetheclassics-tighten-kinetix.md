# Tighten kinetix (Code the Classics vol 2)

**Status:** DONE 2026-09-05 (Fable session) — all gates green, staged; archived. Play-test audio
and the gamepad path (both outside the harnesses) when convenient.
**Priority:** 4
**Difficulty:** 5
**Part of:** `tasks/archive/2026/09/05/codetheclassics-tighten-games.md` · **Depends on:** the boing depth read · **Next:** `tasks/codetheclassics-tighten-avenger.md`
**Engine family:** vol2 (kinetix/avenger/eggzy/leadingedge/beatstreets carry the same 17-section engine; eggzy ≡ beatstreets ≡ leadingedge byte-for-byte modulo a 1–3 line offset, kinetix/avenger the same text one line lower). Tighten the vol2 engine ONCE here (first vol2 game) and splice into the other four, restoring per-game the slices each uses (§3 of the reference doc).

## BLUF

Apply `tasks/reference/code-the-classics-tightening.md` to
`ports/codetheclassics/vol2/kinetix/kinetix.py` (4124 lines). High opportunity: the whole
`mask` (1686–1739) and `transform` (1741–1764) sections and all of `_Painter` (1950–1986, no
`screen.draw` anywhere) are dead; `Game` has 15 attributes assigned in `new_level()`; `Bat` is a
dataclass leaking two undeclared attributes.

## Context (read first)

- Shape (HEAD 2026-09-05): banners `_types` 56 … `__init__` 2564, aliases 2668; game code from
  2672; `__main__` at 4048; alias line 54 `_text = audio = joystick = surface =
  sys.modules[__name__]`; `GLImage = Image` 2670 (check for references). `update()` no `dt`.
- Import-time: version check 2678; `mixer.quit/init` + `play_music("title_theme")` +
  `music.set_volume(0.3)` 4020–4028; `setup_joystick_controls()` 4035 (`joystick.get_count()`);
  **`game: Any = Game(ai_controls)` 4038 → `new_level(0)` → two `surface.Surface(...)` +
  `play_sound("start_game")` at import**. No `ty: ignore` in the game part.

## Analysis

**Engine dead here:** whole `mask` and `transform` sections (the "overlap" hits at 3297/3556/3844
are English), all of `_Painter`, `Image.get_width/get_height/get_size/get_rect/from_rgba`,
`_Loader.load/values/clear`, `Screen.clear/fill/bounds`, `Renderer.draw_image(direct)/
filled_rect/rect/line/polygon/circle`, `Surface.set_alpha/get_rect/get_width/height/size`,
`_RectBase.contains/move_ip/inflate`, `Actor.distance_to/colliderect/collidepoint`,
`Sound.fadeout/get_volume`, `_Music.play_once/get_volume/fadeout`, the `gfx_*`/`rect`/
`polygon`/`line` draw helpers, `mixer.set_num_channels/find_channel/get_busy/Sound` (+
`_MixerSound`), `_Keys` (keyboard is by attribute 2885–2894).
Used: `images.bricks` 3641 (attribute style) **and** `getattr(images, …)` 3634 → both become
`images.load(...)` (which makes `_Loader` slots-safe); `getattr(sounds, …)` 3898;
`screen.surface.set_clip` 3845/3862 (**keep `set_clip`**); `screen.blit` ×12;
`surface.Surface`/`SRCALPHA` 3581–3587 + `Surface.fill/blit` ×6 (**keep `Surface`**);
**joystick fully used** (2901–2925, 3914); `music.play/stop/set_volume`; `sounds.*.play()` no args.

**Game classes:** `Controls` 2857 (ABC — keep as ABC: shared state `fire_previously_down`),
`KeyboardControls`/`JoystickControls`/`AIControls`; `Powerup`/`BatType` IntEnums,
`CollisionType` Enum; `Bullet` 3008 dataclass + `InitVar spawn_pos` + `side` InitVar; `Barrel`
3038 — **RNG-bearing `__init__`** (weighted `choice(types)` reading `game.bricks_remaining`/
`portal_active`) — keep statement order or leave; `Impact` 3128 dataclass; `Ball` 3152 — not a
dataclass on purpose (comment 3149–3151: x/y must be set *after* `super().__init__`) — leave,
keep the comment; `Bat` 3400 dataclass — **`shadow` 3414 and `portal_animation_active` 3480 are
undeclared** → declare both before `slots=True`; `Game` 3563 — hand `__init__` (`controls lives
score`) + 15 attributes in `new_level()` (3581–3624) → declare all as `field(init=False)`,
`__post_init__` calls `new_level(0)` (import-time side effects unchanged in order).

**Function-tightening candidates:** 3367–3368 `vec` → conditional expression; 3608–3609 nested
brick loops → `itertools.product`; 3884–3886 `draw_lives` accumulator; `setup_joystick_controls`
3917–3924 shadows the module `joystick` with a local; `play_music`/`stop_music` 4001–4013
identical wrappers → one; `Ball.collision_sound` 3378–3396 → `match` on `CollisionType` +
`case _: raise`; the module `match state:` gets `case _: raise`.

**pygame comments in the game part (8):** 2901 `# Not necessary in Pygame 2.0.0 onwards` (keep
as "no-op here"), 3892–3898 (keep the `getattr` rationale, now moot with `load()`), 3900 (keep
"print the error, it includes the filename"), 3942 false, 4021–4022 (**real rationale for the
mixer restart — but the mixer calls are no-ops now; drop both**), 4043 false, 4045 → banner.

## Work record (2026-09-05)

- **Engine:** the new `splice_vol2_engine.py kinetix Kinetix left,right,space 640x640
  surface,joystick,clip` — the vol1 family engine plus three flag-selected vol2 sections:
  **`Surface`, a dataclass SUBCLASS of `Image`** (adds `_dirty`; `fill`/`blit`/`set_alpha` composite
  on the CPU, `gl_texture` re-uploads when dirty) built by `make_surface(width, height,
  transparent)`, so the renderer draws it like any image and no `Drawable` protocol is needed;
  **`Joystick`** as a dataclass over the GLFW id (+ `joystick_count()`; the pygame `init()` no-ops
  and the `glfw_ready` guard are gone — the window section runs before any game code now);
  **`Renderer.set_clip`** (`glScissor`, also on the `SpriteRenderer` Protocol). The dead `mask`,
  `transform`, `_Painter`, `_MixerSound` and `_Keys` sections are simply not spliced.
- **Classes:** `Bullet`/`Impact` → `slots=True`; `Bat` → `slots=True` with `shadow` and
  `portal_animation_active` declared; `Barrel` and `Ball` stay plain (RNG constructor; x/y set
  after `super().__init__`) with `__slots__`; the `Controls` ABC hierarchy slotted; **`Game` →
  dataclass** (`controls` defaults to a fresh `AIControls`, `lives`, and the fifteen `new_level()`
  attributes declared; `__post_init__` calls `new_level(0)`); a new **`Collision` dataclass**
  (`pos`, `show_impact`, `kind`) replaces the `tuple[Vector, bool, CollisionType]` that callers
  indexed as `c[0]`/`c[1]`/`c[2]`; a `GameObject` Protocol types the per-frame lists.
- **Functions:** `brick_collide`'s two if/else returns → conditional expressions;
  `detect_stuck_balls` → `bool(...) and all(...)`; `collide`'s nested `if` → `continue`s with a
  local `brick`; `draw_score`/`draw_lives` → `enumerate`/`range` arithmetic; the `match` on the
  powerup and on the collision sound gain `case _: raise`; both `match state:` blocks too; the
  `state = state.TITLE` upstream quirk → `State.TITLE`; `play_music`/`stop_music` wrappers gone
  (`_Music` never raises); `getattr(images, …)`/`images.bricks` → `images.load(f"brick{brick:x}")`;
  the redundant `fill((0,0,0,0))` on freshly transparent surfaces dropped (pixel-identical).
- **Numbers:** 4124 → 2651 lines (−36%); pygame/pgzero mentions 137 → 2.
- **Gates:** frame 180 AE=0 vs HEAD (the original 4124-line file); 1500-frame input trace
  (title → play, bat left/right, launches, a lost game, restart; barrels fell for 269 frames)
  identical under the new structural comparator `compare_traces.py` (ignoring the derived
  `left/centerx/centery`, the now-declared `portal_animation_active`, and the surfaces' pixel
  internals); `make format` ruff + ty clean; 104 tests. Not reached by the script: bullets,
  multiball, bat-type powerups (they need specific barrels caught).

## Open questions — settled by Fable (maintainer had delegated discretion)

- `Controls` stays an ABC hierarchy (shared state and behaviour), now slotted.

Engine: the vol2 tightening pass (dead sections above; keep joystick/surface/`set_clip`); write it
splice-ready for avenger/eggzy/leadingedge/beatstreets. Game: `Bat`/`Game` fields, `Barrel` only
with order preserved, `match` conversions, expressions, header (vol 2 © 2024 line), comments.
Gates as boing; key script must launch a ball, hit bricks (impacts), and reach a barrel/powerup.
Open question: `Controls` — keep the ABC (state + inheritance) rather than a Protocol?
*(Recommend keep: it is a base class with shared behaviour, not just an interface.)*
