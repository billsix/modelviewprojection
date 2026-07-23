# Convert in-place vector mutation to rebinding (gacalc vectors become frozen)

**Status:** proposed — **GATED** on a gacalc release (see Gating). Created 2026-07-23.

## Why

gacalc's generated value types (`Vector2`/`Vector3`/…) are changing to
`@dataclass(frozen=True, slots=True)` — **immutable** (gacalc's frozen task, implemented 2026-07-23:
`github.com/billsix/geometricalgebra`). mvp mutates these in place throughout, so once mvp pins the
frozen gacalc, every in-place write breaks (a *field* write raises `FrozenInstanceError`; the ergonomic
`v.x = …` property write raises a `TypeError` — either way it's blocked). All of them must convert to
**rebinding** a new vector.

## Scope — ~150 in-place `.x/.y/.z` mutation sites (Python)

Concentrated in the **Code-the-Classics game ports** (`ports/codetheclassics/vol1|vol2/*`) — boing,
bunner, cavern, myriapod, soccer, avenger, beatstreets, eggzy, kinetix, leadingedge, … — plus a few
**demos** (`demos/demo04.py`, `demo19.py`, `demo20/`, `demo21/`) and `util/cameracontrols.py`.
(Count is ~150 Python sites; the raw grep also hits ~16 GLSL `.vs`/`.fs` swizzles — **not** these,
ignore them.)

The idioms to convert:
- Simple: `self.dir.x = -self.dir.x` → `self.dir = Vector2(-self.dir.x, self.dir.y)`.
- Augmented: `self.dir.y += d` → `self.dir = Vector2(self.dir.x, self.dir.y + d)`.
- **Tuple-unpack (the tricky ones):** `self.vpos.x, self.vel.x = ball_physics(...)` — can't unpack
  straight into rebinds; compute to temporaries, then rebind each vector once
  (`px, vx = ball_physics(...); self.vpos = Vector2(px, self.vpos.y); self.vel = Vector2(vx, self.vel.y)`).

**These are behaviour-faithful ports** (same RNG/update/draw order — see the `ctc-*` history): the
rebind must be *value-identical* to the mutation. Verify gameplay unchanged where feasible (headless
screenshot / smoke per the mvp container recipe), not just that it runs.

## Gating (why "later")

1. **gacalc must ship frozen** — done in `github.com/billsix/geometricalgebra`
   (`tasks/archive/2026/07/23/investigate-frozen-generated-classes.md`).
2. **gacalc must release it** — a **breaking** change → minor version bump + `make release` (PyPI +
   GitHub). Bill is batching this with the other gacalc typing/generator tasks from the same request
   and **won't release until all are handled**, so this stays gated until then.
3. **mvp bumps the pin** — `gacalc==` in `requirements.txt` **and** the Dockerfile `ARG
   GACALC_VERSION` (they must match), to the frozen release.

## Approach

- Do it as a **mechanical sweep with per-file review** (the `.x/.y/.z =` idiom is regular), but the
  tuple-unpack and augmented-assignment sites need care. Consider a small helper if a pattern repeats
  (e.g. `with_x(v, val)`), but rebinding inline is usually clearest.
- The `pgzero_gl` shim's `geometry.py` / Actor `.pos` handling may need a look (it constructs/mutates
  vectors) — check it early.

## Verify

After the pin bump + conversion: `make format` (ty gate) green, `make html` builds, the game ports run
(and behave identically — spot-check a couple headless). No `FrozenInstanceError`/`TypeError` at
runtime.

## Relationships

- Upstream: gacalc's frozen change (`github.com/billsix/geometricalgebra`
  `tasks/archive/2026/07/23/investigate-frozen-generated-classes.md`).
- Same "gated on a gacalc release" shape as the archived
  `tasks/archive/2026/07/22/dual-coefficient-cleanup.md`.
