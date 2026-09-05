# Tighten myriapod (Code the Classics vol 1)

**Status:** DONE 2026-09-05 (Fable session) — all gates green, staged; archived. Play-test audio
(mixer stripped to no-arg plays + looping music) when convenient.
**Priority:** 3
**Difficulty:** 4
**Part of:** `tasks/archive/2026/09/05/codetheclassics-tighten-games.md` · **Depends on:** `tasks/archive/2026/09/05/codetheclassics-tighten-cavern.md` (same engine family) · **Next:** `tasks/codetheclassics-tighten-bunner.md`
**Engine family:** vol1-minimal — `myriapod.py:1-1936` ≡ `cavern.py:1-1936` (only lines 8, 25, 36, 41–42, 1512, 1918–1922 differ, all doc text). **Engine: `python tasks/adhoc/codetheclassics-tighten-games/splice_vol1_engine.py myriapod Myriapod <keys>`; hand-tighten only the game half.**

## BLUF

Apply `tasks/reference/code-the-classics-tightening.md` to
`ports/codetheclassics/vol1/myriapod/myriapod.py` (3081 lines). Same engine dead-list as cavern;
the game half has a `Direction` enum with a `match` already, grid-quantized movement, and two
RNG-bearing constructors that must not be reordered.

## Context (read first)

- Shape (HEAD 2026-09-05): banners at the same lines as cavern (52 … 1881); game code from 1937;
  `__main__` at 3005; alias line 50. `update()` takes no `dt`.
- Related: `tasks/swap-myriapod-rotate90-to-gacalc.md` — myriapod's local `rotate_90_degrees`
  (`InvertibleFunction`) is a deliberate temporary duplication of a gacalc feature; **leave it**.

## Analysis

**Engine surface dead here:** cavern's list, except `Actor.collidepoint` (2154, 2311) and the
`Actor.anchor` setter (2264) are **live**. Used: `getattr(sounds, …)` 2890,
`sounds.gameover.play()` 2938 (the only attribute-style sound access in vol1 — becomes
`sounds.load("gameover").play()`), `screen.blit` ×6, `music.play/set_volume` 2989–2990.

**Game classes:** `Explosion` 2009, `Player` 2028, `Bullet` 2286 — `@dataclass(eq=False)` +
`InitVar spawn_pos` (add `slots=True`); `Segment` 2422 — dataclass with positional fields, no
attrs set later; `FlyingEnemy` 2186 and `Rock` 2226 — **RNG-order-bearing `__init__`s**
(`FlyingEnemy`: `randint` for the side, then `choice`, then `randint`; `Rock`: `randint` then
**a sound side effect** `game.play_sound("totem_create")` 2235) — both already annotated as
such at 2183–2184 / 2223–2224; convert only if the statement order is preserved verbatim, else
leave with the reason; `Game` 2678 — hand `__init__` (9 fields 2680–2697) plus **`occupied`
created inside `update()` 2758** → declare it; `game = Game()` 2999 builds a 25×14 grid at
import (no RNG).

**Function-tightening candidates:** 2064–2074 two `dx/dy` if/elif → expressions; `inverse_
direction` 2403–2415 already a `match` with a raise — keep (table form optional);
`is_horizontal` 2417 → `dir in (LEFT, RIGHT)`; `Rock.damage` 2247–2258 nested if/else picking a
sound name → table/expression; 2465–2478 `rock`/`horizontal_blocked` → expressions;
**2803–2807 manual `num_rocks` accumulator → `sum(...)`**; 2385 `SECONDARY_AXIS_POSITIONS`
quadratic `sum(...[:i])` → `itertools.accumulate`; `Game.update` returns `self` (2846) and both
callers discard it → `-> None`; single-use locals 2220, 2277–2282, 2824–2842; 2685 unused `y`.

**pygame comments in the game part (7):** 1952–1953 (anchor explanation — keep the fact, drop
the attribution), 2311 (`collidepoint` "from Pygame's Rect" — false now, it is `Actor`'s),
2884 framing / **2889 keep the rationale**, 2917 false ("Pygame Zero calls…"), 3002 main-loop
history → banner.

**Traps:** module-level list building 2376/2385; `mixer.quit/init` + `music.play("theme")` +
`music.set_volume(0.4)` 2985–2993; no `ty: ignore` in the game part.

## Work record (2026-09-05)

- **Engine:** `splice_vol1_engine.py myriapod Myriapod left,right,up,down,space 480x800` (the script
  gained a window-size parameter for this game; cavern's output is unchanged). The game's gacalc
  imports (`e_12`, `InvertibleFunction`/`identity`/`inverse`) are taken from the file verbatim; the
  local `rotate_90_degrees` stays (`tasks/swap-myriapod-rotate90-to-gacalc.md`).
- **Classes:** `Explosion`/`Player`/`Bullet`/`Segment` → `slots=True` (all attributes were already
  declared); `FlyingEnemy` and `Rock` stay plain (RNG/side-effect constructors, comments say why)
  and get `__slots__`; **`Game` → dataclass** with `player: Player | None`, `grid` built in
  `__post_init__`, and **`occupied` declared** (it was invented inside `update()`), typed
  `set[tuple[int, ...]]` for its (x, y) and (x, y, edge) entries.
- **`GameObject` Protocol** types the per-frame object list; the upstream `sum(self.grid, ...)`
  list-flattening trick became explicit star-unpacking in the SAME order (bullets, segments,
  explosions, player, flying enemy, then the grid's rocks row by row); `draw()` sorts a `list[Actor]`
  with a typed `sort_key` and draws the flying enemy last, as before.
- **Functions:** `dx`/`dy` conditional expressions; `is_horizontal` → `in`; `inverse_direction`'s
  trailing raise moved into `case _:`; the `rock`/`horizontal_blocked` if/else → conditional
  expressions; `num_rocks` accumulator → `sum(...)`; `Game.update` returns `None` (callers
  discarded `self`); `if not self.segments`; sprite names as f-strings; `sounds.gameover.play()` →
  `sounds.load("gameover").play()`; three `assert game.player is not None` at play-only sites.
  Left as upstream wrote it: `SECONDARY_AXIS_POSITIONS = [sum(SPEED[:i]) …]` (its comment teaches
  the prefix sum; `accumulate` would hide it), and the wave-building loop's commented locals.
- **Numbers:** 3081 → 2041 lines (−34%); pygame/pgzero mentions 94 → 2.
- **Gates:** frame 180 AE=0 vs HEAD (the original 3081-line file); 1500-frame input trace
  byte-identical (start, move all four ways, hold fire: waves −1→1, bullets ×636 frames, explosions
  ×1116, flying enemy ×1325, totem rocks, a death and respawn); `make format` clean; 104 tests.

## Open questions — settled (inherits cavern's `Actor` decision: plain class with `__slots__`)

Same three steps and gates as cavern; the key script for the state trace should fire (space)
and move so `FlyingEnemy`/`Rock` spawn (both RNG constructors get exercised). Open question:
none beyond cavern's `Actor` decision, which this game inherits.
