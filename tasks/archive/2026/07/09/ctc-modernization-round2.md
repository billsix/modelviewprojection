# CTC modernization round 2: two IntEnums + the remaining match chains

**Status:** DONE + boot-passed 2026-07-09 (Bill: "looks fine") — archived.

Implementation notes:
- `Direction(IntEnum)` landed in both bunner and myriapod as designed;
  myriapod's `min(range(4), key=...)` became `min(Direction, key=...)`
  (member iteration order == range(4) order, verified), `rank()`'s
  Callable annotation followed, and `inverse_direction` is now a match
  over Direction with the explicit unreachable raise as the tail.
  Runtime contract verified in-container: inverses, is_horizontal,
  DX/DY indexing, sprite-name str() (`"sit2"`), min-over-members.
- `Fruit.Type(IntEnum)` nested in cavern (choice pools + comparisons +
  the `types` list retyped).
- Matches: beatstreets `button_down` (with an explicit `case _: None`),
  kinetix Powerup effects (dict-membership arm as a guarded
  `case t if t in POWERUP_BAT_TYPES`), kinetix collision sounds (the
  compound first arm as an or-pattern
  `CollisionType.BRICK | INDESTRUCTIBLE_BRICK`).
- **The three flagged beatstreets sites were NOT converted, as suspected**:
  650 and 1009 are nested-if shapes (detector false positives), 1046 is a
  mixed-subject chain (falling_state arms followed by hit_timer /
  pickup_animation arms) — the exact shape that produced the
  orphaned-elif crash in the first match pass; restructuring it would
  trade clarity for match-ness.
- Gates: ty all-clean, ruff/format clean, 60 pytest, definitions gate on
  all five touched games, Direction behavior contract.
**Created:** 2026-07-09 (Bill: "is there any more stuff... more dataclasses,
if reasonable? or what about enum types... or more match expressions?" —
survey answers below; task per his ask, including the opted-out items)

## Recommended work

### 1. `Direction` IntEnum (bunner + myriapod)

Both games define loose module ints:

    DIRECTION_UP: int = 0
    DIRECTION_RIGHT: int = 1
    DIRECTION_DOWN: int = 2
    DIRECTION_LEFT: int = 3

Convert to an `IntEnum` per game (they're separate files; no shared module
for two faithful ports).

- **Must be `IntEnum`, not `Enum`**: myriapod does modular arithmetic on
  directions (`(self.direction + rotation) % 4`,
  `rotation_table[difference % 4]`) and both games index lists by
  direction.
- **Image-name safety**: since Python 3.11, `str(IntEnum_member)` formats
  as the plain number, so `"sit" + str(direction)`-style sprite-name
  construction stays byte-identical. Verify each str/f-string use anyway
  during the pass.
- Pairs with converting myriapod's `inverse_direction` /
  neighbouring direction chains (see match list) — do together.

### 2. `FruitType` IntEnum (cavern)

`Fruit.APPLE/RASPBERRY/LEMON/EXTRA_HEALTH/EXTRA_LIFE` are loose
class-level ints (`APPLE: int = 0`, ...) used in `choice([...])` pools and
`==` tests. Convert to a nested `IntEnum` following the existing
`avenger Player.Timer(IntEnum)` precedent. Check sprite-name uses of the
type value (same 3.11 str rule applies).

### 3. The remaining match conversions (~8 sites)

The 2026-07-08 match pass took the clean enum-prefix chains; these are the
chains its transformer rightly refused, all hand-convertible:

- `vol2/beatstreets/beatstreets.py:360` — `button == 0/1/2/3` keyboard
  mapping in `KeyboardControls.button_down` — textbook `match button`.
- `vol2/kinetix/kinetix.py:~488` — Powerup effects: a
  `self.type in POWERUP_BAT_TYPES` dict-membership branch followed by
  `elif self.type == Powerup.X` arms — keep the membership test as a
  leading `if` (or a guarded `case _ if ...`), match the rest.
- `vol2/kinetix/kinetix.py:~772` — `CollisionType` sound chain whose
  first arm has a compound condition — guarded first case.
- `vol1/myriapod/myriapod.py:475/477` — the direction chains
  (`inverse_direction`, neighbour fn) — fold into the Direction enum
  work; keep the new explicit unreachable `raise` as `case _`.
- `vol2/beatstreets/beatstreets.py:647/1006/1043` — flagged by the chain
  detector; needs eyes-on (at least one looks like a nested-if false
  positive, not a real chain). Convert only the genuine ones.

### Gates

Behaviour-faithful as always (same RNG call order, same branch outcomes —
IntEnum arithmetic/indexing/str all preserve int semantics); format.sh
(now fail-on-any-step), 60 pytest, 10/10 definitions gate, and Bill
boot-passes bunner/myriapod/cavern/kinetix/beatstreets (the touched
games).

## Surveyed and deliberately NOT doing (with reasons)

- **More dataclasses: none.** The 2026-07-08 conversion took everything
  reasonable (~35 classes). The kept-manual list was kept for init-LOGIC
  reasons that still stand: RNG ordering inside constructors (bunner's
  row classes, cavern Fruit, avenger Enemy, myriapod Rock), computed
  super-args (avenger Laser, myriapod FlyingEnemy), and kinetix Ball
  (its x/y params deliberately overwrite Actor's after super().__init__).
  The static-Actor property-collision rule (see
  tests/test_ctc_actor_field_collisions.py) makes Ball DOUBLY
  unconvertible — x/y fields would shadow Actor properties. Shim classes
  (Surface, Sound, Joystick, _MixerSound) all have real constructor
  logic; marginal gain, real churn.
- **soccer's 0-7 compass `dir`: stays a plain int.** It is
  arithmetic-native by design — `angle_to_vec(self.dir + d)`, averaging,
  wrap-around math everywhere. An enum would fight the math that IS the
  mechanic. (Same verdict as the x/y→Vector2 survey gave its per-axis
  physics.)
- **kinetix brick-type ints: stay ints.** They're level DATA (grid cell
  values, indexed against sprite tables), not symbolic states.
- **boing/cavern/soccer/myriapod `State(Enum)` families: already enums**
  (from the earlier match pass); avenger has EnemyState/EnemyType/Timer,
  kinetix has CollisionType/BatType/Powerup, bunner PlayerState —
  coverage there is already good.
