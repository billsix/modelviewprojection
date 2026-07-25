# Investigate: are the defensive vector copies now redundant under frozen gacalc?

**Status:** **DONE 2026-07-25.** Investigated all 14 `Vector2(*x)`/`Vector3(*x)` sites;
removed the 12 redundant aliasing copies, kept the 2 that normalize a tuple-or-vector
argument. Verified `ruff`+`ty` clean in-container and behaviour byte-identical by
differential trace (pre-cleanup vs cleaned, both under frozen gacalc 0.0.14). See
"Resolution".
**Created:** 2026-07-23 (deferred out of the frozen-vector rebind migration so that
change stayed a pure mutation→rebinding conversion)

## Resolution (2026-07-25)

The classifier was the **source type** of each `Vector2(*x)`: a vector-typed source is a
pure aliasing copy (redundant, since frozen vectors can't be mutated out from under a
sharer); an `Any`/tuple source is *normalization* (must stay — `*x` also converts a
`(x, y)` tuple to a vector).

**Removed — 12 aliasing copies** (`Vector2(*x)` / `Vector3(*x)` → `x`):
- `beatstreets`: `half_hit_area` (the documented case), `speed`, `self.target = self.vpos`
  (×2 sites). Also rewrote the three now-false comments that claimed "Vector2 is mutable,
  copied not by reference" — the whole point is that it *isn't* mutable anymore.
- `kinetix`: `self.dir = dir`, and deleted the long "make a full copy … reference type …
  the two balls would remain linked" comment plus the class-level "dir param is
  defensively copied" note — both described the pre-frozen hazard.
- `soccer`: `shadow.vpos = self.vpos` (×2), `target = self.home`, `target = ball.vpos`,
  `debug_target = target`, `camera_focus = self.ball.vpos`.
- `leadingedge`: `car_offset = offset`.

**Kept — 2 normalizers** (source typed `Any`, so a caller may pass a `(x, y)` tuple):
`beatstreets` `self.vpos = Vector2(*pos)` (`pos: Any`) and `avenger`
`Vector2(*spawn_pos)` (`spawn_pos: InitVar[Any]`, used inline for a vector subtraction).

**Kept — the `DEFAULT_HALF_HIT_AREA` / `DEFAULT_BALL_DIR` module constants.** They are
still the right *named* defaults: an inline `Vector2(...)` default argument trips ruff
`B008` regardless of frozenness. Only the *copy on store* was removed, not the constant.

**Verification.** `make format` (ruff + ty) exits 0 in-container against gacalc 0.0.14 —
ty specifically would reject `= x` if any simplified `x` were actually a tuple, so a green
ty confirms the classification. Behaviour proven identical by a seeded 300-frame `update()`
differential trace of the four changed games (soccer, beatstreets, kinetix, leadingedge):
pre-cleanup source vs cleaned source, both on frozen gacalc — byte-identical.

## Background

Before gacalc's vectors were frozen (pre-0.0.14), a `Vector2`/`Vector3` in a shared
location was an aliasing hazard: any reader mutating it in place changed it for every
other holder. The **mutable-default-argument** case was the sharp edge — a
`def __init__(…, half_hit_area: Vector2 = Vector2(25, 20))` evaluates once at import,
so every instance taking the default shared **one** object.

The fix (found 2026-07-18) was two parts: a named module-level constant for the
default, **and a defensive copy on assignment** — `self.half_hit_area =
Vector2(*half_hit_area)`. The copy was the load-bearing half; the constant alone only
silenced ruff `B008`.

**gacalc 0.0.14 froze the value types** (`tasks/archive/2026/07/23/frozen-vectors-rebind-migration.md`).
A frozen vector in a shared location can no longer be mutated out from under its other
readers, so **that entire hazard is gone** — which means these defensive copies are
now, in principle, redundant. They were deliberately **kept** during the migration so
that change was a clean conversion; removing them is this separate pass.

## Goal

Decide, per site, whether each defensive copy / dedicated-default-constant is:
- **redundant** (only there for the now-impossible aliasing hazard) → remove;
- **still doing real work** (copies a mutable tuple/list arg, normalizes an incoming
  type, or the surrounding code relies on identity) → keep, with a one-line reason;
- **load-bearing for a non-obvious reason** → keep and document.

Do **not** assume "frozen ⇒ delete them all." A `Vector2(*pos)` at a boundary may
also be **normalizing a tuple-or-vector argument into a vector** (the shim's position
params accept both), which is still needed regardless of freezing. That is exactly the
kind of case the migration's "don't simplify `Vector2(*v)` back to `v`" caution was
about — re-check each one against what it actually guards now.

## Where to look (survey, not exhaustive — grep to confirm)

- **`beatstreets`**: the `half_hit_area` case named above —
  `Player`/`EnemyVax`/`EnemyHoodie`/`EnemyScooterboy` and `DEFAULT_HALF_HIT_AREA`.
  Start here; it's the documented one.
- Grep the ports tree for `Vector2(*` / `Vector3(*` and for any `Vector2(...)` /
  `Vector3(...)` used as a **default argument** or assigned from another vector
  purely to copy it: `grep -rnE "Vector[23]\(\*" ports/codetheclassics` and
  `grep -rnE "= Vector[23]\(" ports/codetheclassics`.
- Check `pgzero_gl` (Actor `pos` setter, `screen.blit`) — its position params
  **unpack** (`x, y = pos`) rather than index so they accept tuples *and* vectors;
  that unpacking is a type-normalization, not an aliasing guard, so it stays.

## Verify

- The same differential-trace harness used for the freeze migration proves any
  removal is behaviour-preserving: seeded, 300 frames of `update()` headless,
  byte-identical actor-state dump before vs after. (Harness reference in the archived
  migration task.)
- `ruff check ports` must stay clean — note that removing a `DEFAULT_*` constant and
  reverting to an inline `Vector2(...)` default would **re-trip `B008`**, so if a
  constant is kept-but-copy-removed, keep the constant.

## Relationships

- Deferred from: `tasks/archive/2026/07/23/frozen-vectors-rebind-migration.md`.
- Origin of the copies: the 2026-07-18 `half_hit_area` aliasing find (recorded in
  `CLAUDE.md` › Code-the-Classics ports, now rewritten for the frozen world).
