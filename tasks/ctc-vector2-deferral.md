# Code the Classics: defer game math to Vector2 (and Vector2's own lineage)

**Status:** proposed — needs go-ahead
**Created:** 2026-07-08

## Goal (Bill, 2026-07-08)

Two layers, per Bill's ask ("see how much math can defer to vector2d,
reasonably; and if it makes sense to make a subclass of vector2d that adds
some stuff for the pygame zero shim, go ahead — or tell me about
alternatives"):

1. **Games → Vector2:** audit vol1/vol2 for hand-rolled component math
   (`dx/dy` pairs, `math.hypot`/`atan2`/manual normalization) that could
   reasonably become `pgzero_gl.geometry.Vector2` operations. Survey note
   2026-07-08: only ~5 raw `sqrt/atan2/hypot` sites remain (e.g. soccer's
   `atan2` sprite-direction helper at soccer.py:129), so most math already
   flows through Vector2 — this layer is a modest cleanup, done per-game.
   Constraint: behaviour-identical (float-op order changes can drift physics;
   compare frame traces where feasible).
2. **Shim Vector2 → mvp's Vector2 (gacalc):** decide whether
   `pgzero_gl/geometry.py`'s hand-rolled `Vector2` (a pygame.math.Vector2
   work-alike) should become a **subclass of** (or defer to)
   `modelviewprojection.mathutils.Vector2` — i.e. gacalc's graded vector.

## Layer-2 decision matrix (analyze, then pick)

The shim Vector2's contract is **pygame semantics**, several of which clash
with gacalc's vector type. Verify each against gacalc's actual behaviour
before choosing:

- **Mutability:** games mutate in place (`v.x += …`, `normalize_ip`,
  `scale_to_length`); gacalc's graded vectors are (check) immutable
  coefficient objects.
- **`*` operator:** pygame = dot product for vector operands, scaling for
  scalars (shim implements exactly this, documented in CLAUDE.md); gacalc =
  its own algebra semantics. A subclass changing `*` meaning violates
  Liskov and would be confusing in a codebase that teaches gacalc.
- **`rotate()`:** pygame rotates counter-clockwise in *screen space (y
  down)*; mathutils rotations are mathematical convention via rotors.
- **Quirks:** pygame's `normalize()` on a zero vector returns (0,0) in the
  shim (games rely on it); `Vector2(seq_or_obj)` polymorphic constructor;
  `__eq__` against any indexable.
- **Perf:** these run in 60 fps loops over many actors; gacalc objects are
  heavier than two float slots.

### Options

a. **Status quo** — standalone work-alike. Keeps pgzero_gl a self-contained
   clean-room shim with no dependency on the mvp package/gacalc.
b. **Subclass mathutils.Vector2, add the pygame API on top.** Bill's
   suggested shape. Works only if gacalc's type tolerates subclassing +
   mutation; expect to override most operators anyway (see clashes above),
   at which point the "deferral" is mostly nominal.
c. **Composition:** shim Vector2 keeps its API but implements the
   interesting ops (rotate via `rotor`/`sandwich`, dot, norms) by converting
   to mathutils under the hood. Pedagogically nice (the course's rotor math
   drives the games), pays a per-op conversion cost.
d. **Implementation-level deferral only:** keep the class, reimplement just
   `rotate`/`rotate_ip` on mathutils rotors (the one op with real math in
   it), leave the float-slot arithmetic alone.

Leaning at survey time: (d) or (a) — the pygame semantic surface (mutation,
dot-`*`, y-down rotate, zero-normalize) is exactly what a gacalc subclass
can't inherit cleanly, so (b) likely means overriding nearly everything.
But verify gacalc's actual constraints first; if its Vector2 subclasses
cleanly and tolerates an `.x/.y` mutable facade, (b) becomes viable and is
Bill's stated preference.

## Gates

- `tests/` for pgzero_gl (geometry/mask tests) + `test_gl_vector_unpacking.py`
  (gacalc iteration contract) stay green; `format.sh` `ty check` green.
- Each touched game boots and plays identically (Bill's on-display check —
  physics feel is the regression surface here).

## Related

- [[ctc-dataclasses-and-dispatch]] (same tree, same rule-change note: the
  games' "no restructuring" rule in CLAUDE.md is being relaxed to
  "behaviour-faithful, structure may modernize" — update CLAUDE.md once
  either task lands).
