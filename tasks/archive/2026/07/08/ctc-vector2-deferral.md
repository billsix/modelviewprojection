# Code the Classics: defer game math to Vector2 (and Vector2's own lineage)

**Status:** DONE 2026-07-08 — Phase A committed (explicit dots +
loud-fail operator); Phase B implemented once gacalc 0.0.7 shipped the
subclass-preserving ops + LGPL relicense. Staged, uncommitted (Bill
commits).

## Phase B: DONE (2026-07-08, gacalc 0.0.7)

`pgzero_gl.geometry.Vector2` is now a subclass of `gacalc.g2.Vector2`
(requirements pin bumped to `gacalc>=0.0.7`):

- `x`/`y` are settable property views over `coeff_e_1`/`coeff_e_2` (the
  fields are re-annotated `float` in the subclass -- every write path
  coerces). `__init__` accepts pygame forms (scalar pair, sequence,
  vector) AND gacalc's `coeff_e_1=`/`coeff_e_2=` keywords, because the
  generated ops rebuild same-type results via `type(self)(coeff_...)`.
- pygame surface as documented overrides: tuple-accepting
  `+`/`-`/`==`/`rsub`, float `dot()`, zero-safe `normalize()`,
  `normalize_ip`/`scale_to_length`/`distance_to`/`copy`,
  `__getitem__`/`__len__`.
- **`rotate(degrees)` uses the rotor machinery** (Bill's pedagogy call,
  2026-07-08): the target is the basis scaled by cosine/sine and
  `rotor_from_vectors(e_1, cos t e_1 + sin t e_2)` derives the rotor;
  one rotor per angle, `functools.cache`d (games use a handful of fixed
  angles), coefficients coerced to float at cache time (the exact-int
  basis constants would keep sympy in the loop). Sandwich matches the
  trig formula to 1 ulp (max 8.9e-16 over a test sweep); 1.74 us/call.
- `*`: scalars scale (returning the shim type); a gacalc vector operand
  falls through to the parent = geometric product -> `Rotor2`; a bare
  sequence still raises the loud TypeError. Wedge `^` works on game
  vectors.
- Two permanent documented ty variances (`invalid-method-override`):
  `dot` (float vs multivector) and `rotate` (angle instance method vs
  gacalc's from/to rotor-factory classmethod). All other overrides are
  Liskov-clean (params renamed to the parent's `rhs`/`lhs`/`other` --
  ty checks keyword-callability; `__radd__ = __add__` aliasing was
  replaced by a real def for the same reason).

**Benchmark (adopt-vs-facade gate):** representative busy-actor frame
mix: old float-slots 2.20 us vs gacalc-backed 2.82 us per actor-frame
-> 200 actors = 2.6% vs 3.4% of a 60 fps frame budget. Adopted the
subclass; the facade fallback wasn't needed.

**Gates (in mvp container, gacalc 0.0.7 image):** format.sh -- ruff
clean, ty clean on pgzero_gl/vol1/vol2/tests (src keeps its 79
pre-existing diagnostics, tracked in src-ty-diagnostics-after-ty-bump);
mvp pytest 62 passed (incl. the gl-vector-unpacking iteration guard);
shim contract suite (26 checks) passes; all 10 games compile.
**Not verified: an actual game boot with a display** -- Bill's morning
pass should boot a few games (kinetix exercises rotate; soccer
exercises dot + heavy per-frame vector mutation).

**Optional follow-up (not done):** Vector3 could subclass
`gacalc.g3.Vector3` the same way (leadingedge is its only consumer;
needs cross() kept shim-side). Decide separately.

## Phase A: DONE (2026-07-09)

Both `vec * vec` sites (soccer's `targetable()` — the only two in all 10
games; everything else is vec * scalar) now call `.dot()` explicitly, and
the shim's `Vector2.__mul__`/`Vector3.__mul__` RAISE TypeError on a vector
operand ("use a.dot(b) explicitly") — a missed site now fails loudly
instead of silently changing meaning when `*` later becomes the geometric
product. In-container: format.sh green + a runtime contract check
(dot works, scalar scaling works, vector operand raises).

## Phase B experiment result: subclassing needs a gacalc generator change

The 2026-07-09 in-container experiment: mutation via x/y properties works,
iteration order is right, magnitude/normalize exist — **but
`type(sub + sub)` is base `Vector2`, not the subclass** (gacalc's generated
closed-form ops construct the concrete class by name), so a subclass loses
its pygame API on every arithmetic result. Also `vec + tuple` raises in
gacalc, and the games' tuple-interop needs remain.

## Open issues for Bill

- [x] ~~geometricalgebra subclass-preserving generated ops~~ — **DONE
      2026-07-08** (Bill authorized; archived in gacalc at
      `tasks/archive/2026/07/08/subclass-preserving-generated-ops.md`).
      Generator now emits `type(self)(...)` for same-type results; all
      gacalc gates green; the shim experiment reruns 10/10 (including
      `normalize()` preserving the subclass). gacalc changes are staged,
      uncommitted — needs Bill's commit (and a release/version bump
      before mvp's `requirements.txt` pin can see it).
- [x] ~~geometricalgebra relicense-to-lgpl~~ — **DONE 2026-07-08** (Bill
      authorized; archived in gacalc at
      `tasks/archive/2026/07/08/relicense-to-lgpl.md`). gacalc is now
      LGPL-2.1-only (same as pgzero_gl): LICENSE, SPDX per-file headers,
      generator's emitted headers, PEP 639 pyproject metadata; all gacalc
      gates + `make dist` green. Staged, uncommitted — needs Bill's
      commit, then a version bump + `make release` so mvp can depend on
      a released LGPL gacalc with the subclass fix.
- [ ] After Bill releases gacalc: implement the subclass (x/y properties over
      coeff_e_1/e_2, tuple-accepting __add__/__sub__/__eq__, y-down
      rotate(), zero-safe normalize(), __getitem__/__len__), and benchmark
      a 60 fps game loop before adopting (gacalc objects are heavier than
      two float slots — if it drags, prefer the facade).
**Created:** 2026-07-08

## NEW DIRECTION (Bill, 2026-07-09): make dot products explicit, then subclass

Bill's call: since we own all 10 games, change **every vector-times-vector
call site to an explicit `.dot()` call** instead of preserving pygame's
`*`-means-dot operator contract. That removes the main technical blocker
from the 2026-07-08 analysis: with no caller relying on `vec * vec`,
a gacalc-Vector2-backed shim vector no longer needs to override `*` to
contradict the parent algebra (scalar `vec * k` already means the same
thing in both worlds — gacalc e1*e2 -> Rotor2 stays available, unused by
the games).

### Plan
1. **Sweep the 10 games for `vec * vec` sites** and convert to `.dot()`.
   Finding them: grep `*` uses where both operands are vector-ish
   (targetable()'s `v0 * v1` and `v0 * angle_to_vec(...)` in soccer are
   the known ones; audit all `Vector2` arithmetic). Then remove/deprecate
   the vector-operand branch of the shim `Vector2.__mul__` so any missed
   site fails loudly instead of silently changing meaning.
2. **Then implement the gacalc-backed subclass** (the original ask):
   shim Vector2 as a subclass of (or facade over) `gacalc.g2.Vector2`,
   mapping `.x`/`.y` to `coeff_e_1`/`coeff_e_2` (mutation verified to work
   in the 2026-07-08 container experiment), keeping pygame's y-down
   `rotate()` and zero-vector `normalize() -> (0,0)` behaviours as
   documented overrides.
3. **Licensing (Bill's call, not a blocker):** pgzero_gl is LGPL-2.1,
   gacalc is GPL v2+ — both are Bill's own code, so coupling them is a
   licensing decision he can simply make; record the choice in the shim's
   header when this lands. (The 2026-07-08 analysis treated this as a hard
   stop; corrected — it's owner's prerogative.)
4. Perf note from the original matrix still applies: gacalc objects in
   60 fps loops are heavier than two float slots — benchmark a game loop
   before/after; if it matters, the facade (option c) beats the subclass.

## SUPERSEDED 2026-07-08 analysis (kept for the record)

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
