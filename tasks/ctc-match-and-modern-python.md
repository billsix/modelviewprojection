# Code the Classics: adopt `match` where reasonable + modern-Python audit

**Status:** in progress — the `match` half is DONE (2026-07-08); the
modern-features half (`@override` sweep, StrEnum, Self) remains
**Created:** 2026-07-08

## Progress (2026-07-08)

- [x] **`match` conversions: ~27 chains across all 10 games.** Every
      top-level `state` machine (update/draw in each game), plus the inner
      enum machines that are pure chains: bunner's `PlayerState`, avenger's
      `EnemyState` + the four `EnemyType` speed/sprite tables, beatstreets'
      four `Enemy.State` machines, eggzy's `State` pair. Done via a chain
      transformer (scratchpad `to_match.py`) that only converts chains where
      EVERY branch is exactly `subject == Enum.MEMBER` (+ optional trailing
      `else` → `case _`), and **rejects chains with trailing non-enum
      elif/else branches** — those (kinetix's Powerup chain, eggzy's
      `fall_state`, beatstreets' `falling_state`, bunner's direction ints)
      correctly remain if/elif per "wherever reasonable". Transformer bug
      found and fixed during the run: a converted enum-prefix would orphan a
      trailing `elif self.hit_timer > 0:`-style branch (SyntaxError caught
      by the compile gate; beatstreets/eggzy reverted to HEAD and redone
      with the hardened version).
- [x] Gates: all 10 games + shim compile; ruff clean + format idempotent;
      ty at exact baselines (vol1 clean, vol2 120 pre-existing).
- [ ] `@override` on the Actor-subclass update/draw overrides (the
      dispatch-audit companion; hundreds of sites, mechanical).
- [ ] StrEnum for string-y state enums; `typing.Self` in the shim.

## NOTE for ctc-more-types (raised 2026-07-08)

The container's ty (Fedora 44 package) updated and now reports vol2's ~120
pre-existing `game`-union diagnostics in the OFFICIAL format.sh gate (exit
1), matching the strict local ty. Those diagnostics predate all of today's
work (verified byte-identical via git stash) but now block a green
`make format` — clearing them (proper Optional handling for the
module-level `game`) should move up ctc-more-types' priority.

## Goal (Bill, 2026-07-08)

Across pgzero_gl + vol1 + vol2: use Python's `match` statement wherever
reasonable, and — after reviewing the codebase — adopt whatever other newer
Python features genuinely improve it.

## Survey (2026-07-08)

`match` is used **nowhere** in the tree today. The biggest candidates are the
`elif` chains, concentrated in: beatstreets (44 `elif`s), eggzy (29),
avenger (26), bunner (17), kinetix (15), leadingedge (13). Two shapes
dominate:

1. **State-enum dispatch** — `if state == State.TITLE: … elif state ==
   State.CONTROLS: …` (eggzy:1474ff, every game's update/draw switch) and
   actor-state machines (`fall_state == GravityActor.FallState.JUMPING /
   WALL_JUMPING`, enemy `EnemyState`/`EnemyType` in avenger). These read
   strictly better as `match state: / case State.TITLE:` — note enum cases
   must be dotted (`case State.TITLE`), a bare name is a capture pattern
   (the classic match footgun).
2. **Value/range chains** — direction integers (bunner's 0–3 headings),
   tile/brick codes (kinetix), key codes. `match` with literal patterns and
   `case _:` fits the code-as-teaching-material style; chains that mix
   ranges/inequalities stay `if/elif` ("wherever *reasonable*").

The repo's own house style already uses structural `match` heavily
(gacalc's `decrease_grade`, mvp's mathutils), so this aligns the ports with
the rest of the codebase.

## Modern-feature audit (image is Fedora 44 / Python 3.14; no external floor)

Already in use: PEP 604 unions (`X | None`), `from __future__ import
annotations` in places, Enum. Worth adopting:

- **`typing.override` (3.12)** on every Actor-subclass `update()`/`draw()`
  override — the tree has hundreds (see [[ctc-dataclasses-and-dispatch]]'s
  dispatch audit); `@override` turns a renamed base method into a type error
  instead of silently-dead dispatch. Highest-value item after `match`.
  (The 22 `# ty: ignore[invalid-method-override]` faithful-port variances
  stay suppressions, now with `@override` documenting intent.)
- **`enum.StrEnum` / `enum.auto()` (3.11/3.4)** for the string-y state enums
  and image-name prefixes (several games build image names from state
  strings — StrEnum removes the `.value`/`str()` noise).
- **`dataclass(slots=True)` (3.10)** — belongs to
  [[ctc-dataclasses-and-dispatch]]; listed here only for sequencing: land
  dataclasses first, then `match`, so patterns can use class patterns
  (`case Car(dx=dx):`) where they help.
- **`typing.Self` (3.11)** in the shim's fluent/factory methods
  (`Vector2.normalize() -> Self` etc. in pgzero_gl/geometry.py).
- **`math.dist`/`math.hypot`** for the few remaining hand-rolled distance
  computations (overlaps [[ctc-vector2-deferral]] layer 1 — do whichever
  lands first).
- **PEP 695 `type` aliases (3.12)** for the shim's `VectorLike`-style
  aliases.
- Judged NOT worth it: walrus in game loops (hurts the teaching style),
  f-string nesting tricks, `itertools.batched` (no call sites found),
  exception groups (no concurrency).

## Constraints / sequencing

- Behaviour-identical, same as the other CTC tasks (this is restructuring, so
  it rides on the same CLAUDE.md faithful-port rule relaxation as
  [[ctc-dataclasses-and-dispatch]] — one CLAUDE.md update covers all of them).
- Recommended order within the CTC series: dataclasses → vector2-deferral →
  match/modern (this task) → more-types last. `match` conversions and
  `@override` land here; per-game chunks, `format.sh` (`ty check`) green after
  each.
- `case` with enum members: always dotted; add a `case _:` that raises or
  replicates the original fall-through *exactly* (some upstream chains have
  deliberate no-op fall-throughs — preserve them, don't "fix" them).

## Gates

- `format.sh` (ruff + `ty check`) green per chunk; each converted game boots
  and plays identically (Bill's on-display check).
