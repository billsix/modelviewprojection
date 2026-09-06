# Tighten cavern (Code the Classics vol 1)

**Status:** DONE 2026-09-05 (Fable session) — all gates green, staged; archived. The maintainer
commits mid-work; play-test audio (mixer stripped to no-arg plays + looping music) when convenient.
**Priority:** 2
**Difficulty:** 4
**Part of:** `tasks/archive/2026/09/05/codetheclassics-tighten-games.md` · **Depends on:** the boing pilot's depth read · **Next:** `tasks/codetheclassics-tighten-myriapod.md`
**Engine family:** vol1-minimal — `cavern.py:1-1936` is byte-identical to `myriapod.py:1-1936` bar the game name in 5 doc lines. **Tighten this engine half once and splice it into myriapod** (reference doc §3).

## BLUF

Apply the standard in `tasks/reference/code-the-classics-tightening.md` to
`ports/codetheclassics/vol1/cavern/cavern.py` (2971 lines): strip the engine surface cavern never
calls, convert to demo-style ordering (module-level window/renderer, no `__main__` guard),
dataclass + `slots=True` the game classes with every attribute declared, `match … case _: raise`,
structural Protocols where the loop treats objects uniformly, drop the pygame framing. Gate:
frame-180 AE=0 + a scripted-input state trace + `make format`.

## Context (read first)

- Shape (HEAD 2026-09-05; line numbers shift once editing starts — re-grep): banners `_types` 52,
  `geometry` 102, `context` 434, `audio` 514, `resources` 964, `renderer` 1134, `screen` 1474,
  `actor` 1522, `input` 1783, `__init__` 1881; game code from 1937; `__main__` at 2895. Alias line
  50 `_text = audio = sys.modules[__name__]`. `update()` takes no `dt`.
- cavern keeps `Actor` (the step-2 gradient decision: only boing dropped it). `Actor` (1568) has
  its four fields class-annotated and nothing set outside `__init__` — a clean
  `@dataclass(slots=True)` candidate, BUT its subclasses use the `InitVar spawn_pos` pattern and
  `tests/test_ctc_actor_field_collisions.py` guards field/property name collisions — re-run it.

## Analysis

**Engine surface with zero callers in the file** (delete): `_RectBase.contains/move/move_ip/
inflate/copy/__repr__/_pair/__iter__` + the 9 pair properties (`topleft`…`midright`, 290–354);
`Image.get_width/get_height/get_size/get_rect/from_rgba`; `_Loader.values/clear`;
`Sound.stop/set_volume/get_volume/fadeout`; `_Music.play_once/get_volume/stop/fadeout`;
`Renderer.fill/filled_rect/rect/line/polygon/circle/set_clip/_draw_prim`; `Actor.distance_to/
colliderect/__iter__` + the `left/top/bottom/centerx/centery/center/width/height` setters
(1692–1750); `Keyboard.__getitem__`; `_Keys` (no `keys.*` use); `audio.available`;
`_Mixer.set_num_channels`; the `_Voice` fade/loop machinery (cavern's sounds play with no args).
Used: `getattr(sounds, …)` 2711 (→ `sounds.load(f"…")`), `screen.blit` ×7 (→ `blit`),
`music.play/set_volume` 2878–2879.

**Game classes:** `CollideActor` 2042 (plain, delegates); `Orb` 2094 / `Bolt` 2159 / `Pop` 2189 /
`Robot` 2435 — `@dataclass(eq=False)` with `InitVar spawn_pos` (add `slots=True`; `Robot`'s
`speed` is set in `__post_init__` 2450 — declare it); `GravityActor` 2204 (hand `__init__`:
`vel_y`, `landed`); `Fruit` 2238 (**RNG-bearing `__init__`** 2248: two `choice()` calls, then
`time_to_live` — keep statement order); `Player` 2306 — `@dataclass(eq=False)` whose six
attributes (`vel_y direction_x fire_timer hurt_timer health blowing_orb`, 2317–2322) are set in
`reset()`, not `__post_init__` → **declare them as fields before `slots=True`**; `Game` 2531 —
hand `__init__` that calls `next_level()` (2537), which sets `grid timer fruits bolts enemies
pops orbs pending_enemies` (2552–2587) and **`shuffle`s at import** (2889 `game = Game()`) — a
dataclass with all of those as `field(init=False)` + `__post_init__` calling `next_level()` keeps
the order; verify with the trace.

**Function-tightening candidates:** `block()` 2021 if/else returning bools → one expression;
2373–2378 `dx` if/elif → conditional expression; the three `detect` overrides that `del detect`
(2275, 2344, 2453) — dead parameter kept for the override signature, document or drop the
parameter from the base; 2418–2431 the 4-branch `self.image` ladder → `match`/expression;
2523–2528 image-name accumulator → one expression; 2657–2668 nested `len(...) == 0` → one
`and`; 2759 `sum([...])` → generator; 2676 `"bg%d" %` → f-string; single-use locals 2183, 2184,
2301, 2420, 2522, 2749; `space_pressed()` 2797–2809 → expression; the `cast("Player", player)`
2532 → a `Player | None` field.

**pygame comments in the game part (5):** 2705 framing; **2710 keep the rationale** (why
`getattr`); 2812 "Pygame Zero calls update and draw" — false now, delete; 2892 "Was
pgzero_gl.runner.main()" — rewrite as the main-loop banner; 2941 is the env var (identifier).

**Traps:** `mixer.quit/init` + `music.play` at 2874–2882 (drop the mixer no-ops, keep the
music); `game = Game()` at 2889 consumes RNG at import; no `ty: ignore` in the game part.

## Plan, as scaffolded before the work (the record below is what happened)

1. Engine half: apply boing's engine tightening (reference doc §1.2–§1.5), keeping `Actor`,
   `screen.blit`-style `blit`, and the `Rect`/`ZRect` slice cavern's `Actor` needs; write it so
   the same text splices into myriapod.
2. Game half: dataclass/slots per the class list above; `match` + `case _: raise` for the
   `self.image` ladder and the module `match state:`; the function list above; strip the 5
   comments; BSD-2-Clause header (vol 1 line from `LICENSE`).
3. Gates: `verify_game.sh` (AE=0), `state_trace.py` with a key script that reaches PLAY and a
   death/level change, `make format`, `tests/test_ctc_actor_field_collisions.py`.

## Work record (2026-09-05)

- **Engine:** generated from boing's tightened engine by
  `tasks/adhoc/codetheclassics-tighten-games/splice_vol1_engine.py` (parameters: name, title,
  the four keys cavern reads), which adds back a float `Rect` dataclass (only the surface the
  Actor uses: left/top/width/height + right/bottom/centerx/centery/center/topleft +
  `collidepoint`) and the `Actor` sprite. **`Actor` stays a plain class with `__slots__`** (its
  setup is ordered: image → size → pos; a dataclass base would push InitVars into every subclass's
  generated `__init__`/`__post_init__` signature). `CollideActor`/`GravityActor`/`Fruit` are plain
  slotted classes (Fruit's constructor consumes RNG in a branch — left as is, with the reason in
  a comment); `Orb`/`Bolt`/`Pop`/`Player`/`Robot` are `@dataclass(eq=False, slots=True)` with
  every attribute declared (`Player`'s five per-life attrs and `Robot.speed` as
  `field(init=False)`). Verified on Python 3.14 that zero-arg `super()` works inside a slotted
  dataclass (it did not before 3.14).
- **`GravityActor.update(detect)` → `update()` + `fall(detect)`**, so the three overrides no longer
  carry a dead `detect` parameter and `Player.update` calls `self.fall(detect=self.health > 0)`.
- **`GameObject` Protocol** (`update()`, `draw()`) types the two per-frame object lists
  (different orders for update and draw, so two literal lists, player included only when present).
- **`Game` → dataclass**: `player: Player | None` (the old `cast("Player", None)` lie is gone; two
  `assert game.player is not None` at the PLAY-only sites), the eight `next_level()` attributes
  declared `field(init=False)`, `__post_init__` calls `next_level()` in the same order (so the
  import-time `shuffle` is unchanged).
- **Fruit pickup `if/elif` → `match self.type:`** with `case _: raise`; both `match state:` blocks
  end in `case _: raise`; `space_pressed()` is three lines; `dx` a conditional expression; the
  sprite-name ladders are f-strings; `sounds.load(f"…")` replaces `getattr`; `screen.blit(name,
  (x, y))` → `blit(name, x, y)`; the Python-3.5 version check and the `mixer` no-ops are gone.
- **Numbers:** 2971 → 1932 lines (−35%); pygame/pgzero mentions 92 → 2 (the harness env var).
- **Gates:** `verify_game.sh` frame 180 AE=0 vs HEAD (the original 2971-line file, confirmed);
  `state_trace.py` 1500 frames with start/run/jump/fire/left/right script byte-identical (covered
  orbs ×357 frames, bolts ×627, fruit pickups to score 800, health 3→0, a lost life and respawn;
  no enemy got trapped, so `Orb`'s trap branch ran only via the frame gate's attract mode);
  `make format` ruff + ty clean; `pytest` 104 passed incl. `test_ctc_actor_field_collisions`.

## Open questions — settled

1. ~~`Actor` itself → `@dataclass(slots=True)`?~~ → **No: plain class with `__slots__`** (see above). *(Recommend yes for this family — it is the cleanest
   candidate in the tree — after running the field-collision test.)*
