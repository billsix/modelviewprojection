# Convert in-place vector mutation to rebinding (gacalc vectors became frozen)

**Status:** **DONE 2026-07-23.** Pin bumped and every in-place coordinate write
converted; verified behaviour-identical. Created 2026-07-23.

The durable findings (why the scope estimate was wrong, why `ty` is only a partial
oracle, and how the differential trace was built) are harvested into
`tasks/reference/design-decisions.md` › "gacalc's value types became frozen". This
file is the work record.

## What was done

1. **Pin bumped, both halves together** — `requirements.txt` `gacalc==0.0.14` and
   `Dockerfile` `ARG GACALC_VERSION=0.0.14` (the runtime wheel and the docs-only
   sdist must match, so the book never quotes a gacalc the code doesn't run).
2. **~80 sites converted to rebinding** across six game files:
   `vol1/boing`, `vol1/soccer`, `vol2/avenger`, `vol2/beatstreets` (the bulk),
   `vol2/kinetix`, `vol2/leadingedge`.
   - Simple: `self.dir.x = -self.dir.x` → `self.dir = Vector2(-self.dir.x, self.dir.y)`.
   - Augmented: `self.vpos.x += self.vel.x` →
     `self.vpos = Vector2(self.vpos.x + self.vel.x, self.vpos.y)`.
   - Tuple-unpack (soccer's `ball_physics`, beatstreets' `move_towards`): computed to
     temporaries, then one rebind per vector, in the original statement order.
   - `leadingedge` got two module-level helpers, `with_x` / `with_z`, because 11 of
     its sites replace a single coordinate of a `Vector3` and the inline
     three-argument constructor buried the arithmetic.

## Scope that turned out NOT to be in scope

The demos (`demo04`, `demo19`, `demo20/`, `demo21/`), `assignments/`, and
`util/cameracontrols.py` were listed in the original plan but mutate their **own**
plain-float dataclasses (`Vector`, `Vertex`, `Camera`), not gacalc vectors — 44 of
the 182 raw grep hits. Unaffected by the freeze; left alone. Same for `self.x += …`
on an `Actor` (Actor's own float property over a `ZRect`) and `pgzero_gl/geometry.py`
(`Rect`/`ZRect` carry plain floats).

## Verify — what was actually run

- **`ty`**: 58 `invalid-assignment` (read-only property) diagnostics across the ports
  tree before, **0** after. Augmented assignments are invisible to it, so those were
  found by grep and converted too; the post-sweep grep is empty.
- **`ruff check ports`** clean; **`ruff format --check ports`** reports 133 files
  already formatted.
- **Differential state trace** (`update()` driven headless, seeded, 300 frames, every
  actor's numeric state dumped): **original source on mutable gacalc vs migrated
  source on frozen 0.0.14 is byte-identical** for all six games — boing 675, soccer
  3395, avenger 6285, beatstreets 1140, kinetix 3178, leadingedge 8604 trace lines.
  Zero `FrozenInstanceError`/`TypeError` at runtime.

## Not done (deliberately out of scope)

- **The now-redundant defensive copies** (`self.half_hit_area = Vector2(*half_hit_area)`
  and the `DEFAULT_HALF_HIT_AREA` constant in `beatstreets`) were kept, so this change
  stayed a pure mutation→rebinding conversion. Immutability makes them unnecessary;
  removing them is a separate pass.
- **`make format` / `make html` were not run** — they need the container image
  rebuilt against the new pin, which needs nested podman. The ty/ruff gates above were
  run directly against gacalc 0.0.14 instead.
- **`ports/codetheclassics/_smoketest.py` is broken** (pre-existing, unrelated): it
  calls `pgzero_gl.pgzrun`, which the 2026-07-08 honest-imports pass deleted. It could
  not be used as the render gate; no task doc exists for it yet.

## Relationships

- Upstream: gacalc's frozen change, released as **0.0.14** (`github.com/billsix/geometricalgebra`,
  `tasks/archive/2026/07/23/investigate-frozen-generated-classes.md`).
- Rationale digest: `tasks/reference/design-decisions.md` › "gacalc's value types became frozen".
