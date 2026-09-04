# Code the Classics: express myriapod's segment rotation as rotate ∘ translate functions

**Status:** SUPERSEDED 2026-09-04 by `tasks/codetheclassics-myriapod-rotation-via-pseudoscalar.md`. This doc declined the `rotate ∘ translate` framing because gacalc has no exact integer `rotate` — but that missed the exact answer: a 90° rotation in 2-D GA is multiplication by the **unit pseudoscalar `e_12`** (implemented, byte-identical). Kept for the decision history; the "Feasibility findings" below record *why the rotor-based approach was wrong*, which is still useful.
**Priority:** 5
**Difficulty:** 4

## Feasibility findings (2026-09-04, while maintainer away — for review)

I studied this in the mvp container (the task said "feasibility first"), and the conclusion is to
**leave myriapod's rotation as-is.** Reasoning, be-critical per your instruction:

- **The taught rotation primitive is float, and there is no `rotate` in `gacalc.transforms`.**
  `gacalc.transforms` has `translate`/`inverse`/`compose`/`InvertibleFunction` but **not**
  `rotate`; rotation is gacalc's `plane_rotation` rotor (or mvp's `mathutils.rotate` binding of
  it), which uses `sin`/`cos` of the half-angle — so a 90° rotation is **not exactly `0`/`±1`**
  (~1e-16 dirt). On this **integer** game the rotated offset feeds `cell2pos` and an `int()` pixel
  truncation, where that dirt can **flip a pixel** at an integer boundary — exactly the "use
  integers, not floats, to replicate" concern you raised. So the float rotor is unsafe here (and
  the two translation tasks confirmed the value of *proven* byte-exactness).
- **An exact-integer `InvertibleFunction` is bespoke ceremony, not a clarity win.** The only exact
  route is to hand-build four `InvertibleFunction`s with integer-body lambdas (a signed axis
  swap). But `InvertibleFunction(func, latex_repr, inverse, latex_repr_inv, …)` is built for the
  course's **LaTeX-annotated** transforms — using it in a game means **unused `latex_repr`
  strings** and injecting gacalc types (or int-tuples) into what is currently a clean integer
  path. The current code is an **explicit, exact, heavily-commented 2×2 rotation matrix** that
  literally shows the rotation — arguably *more* legible than four lambda-wrapped
  `InvertibleFunction`s. Converting it **fails "clearer code over abstractions"** without using
  the actual taught `rotate` primitive.
- **Contrast with the two that DID land:** camera-as-inverse (soccer) and leadingedge world→camera
  are **translations**, and `gacalc.transforms.translate`/`inverse` express those exactly and
  cleanly (both verified byte-identical AE=0). The rotation case simply lacks the equivalent
  clean, exact, existing primitive — so the refactor doesn't "build on existing code" the way the
  translation ones do; it reinvents an integer rotation inside a course container.

**Recommendation:** leave `myriapod.py:2588-2604` as the exact integer matrix. If you still want
the `InvertibleFunction` version for pedagogical uniformity, it's ~20 lines and byte-identical by
construction (integer bodies) — say the word and I'll add it; I just don't think it earns its keep
by your own stated principles.

## BLUF

`myriapod`'s segment placement is the **only** 2-D game code across the ten games that composes a
**rotation with a translation** to reach screen space — a hand-rolled 2×2 matrix indexed by the
entry edge, then the `cell2pos` translate. Study the feasibility of expressing it with the
course's own `rotate` (gacalc `plane_rotation`) composed with `translate` — turning a hidden
ad-hoc transform into an explicit Cayley-graph edge, as a pedagogical showcase. **Build on the
existing book/gacalc functions — `rotate`, `translate`, `compose`, `InvertibleFunction` — do NOT
invent new machinery** (maintainer, 2026-09-04). Feasibility-first; the port is behaviour-faithful
so it must stay **byte-identical**; discuss before implementing.

## Context (read first)

- **The verified code** (`myriapod.py:2592-2604`, read firsthand 2026-09-04): a segment's
  cell-local `(offset_x, offset_y)` is multiplied by one of four literal integer 2×2 matrices
  chosen by `self.in_edge`, then handed to `cell2pos` (a translate to the cell's pixel centre):

  ```python
  rotation_matrix = [[1, 0, 0, 1], [0, -1, 1, 0], [-1, 0, 0, -1], [0, 1, -1, 0]][self.in_edge]
  offset_x, offset_y = (offset_x*rm[0] + offset_y*rm[1], offset_x*rm[2] + offset_y*rm[3])
  self.pos = cell2pos(self.cell_x, self.cell_y, offset_x, offset_y)
  ```

- **These four matrices ARE the axis rotations by `in_edge · 90°`** (verified by reading the
  values): `in_edge=0` → identity; `1` → `(x,y)↦(−y,x)`; `2` → `(x,y)↦(−x,−y)`; `3` →
  `(x,y)↦(y,−x)`. So `rotate(in_edge · 90°)` reproduces them — **modulo the exactness caveat
  below** — and the whole placement is `translate(cell_centre) ∘ rotate(in_edge·90°)` applied to
  the local offset: a genuine two-edge Cayley path (segment-local → rotate → cell frame →
  translate → screen).
- **The machinery to build on:** gacalc's `plane_rotation(e_1, e_2)` (mvp binds it as `rotate`;
  see `CLAUDE.md` › Central abstraction), `translate`, and `compose`/`@` on `InvertibleFunction`
  — all existing. `kinetix` already uses `_turn = plane_rotation(Vector.e_1, Vector.e_2)`
  (`kinetix.py:2674`) as precedent for a gacalc rotor in a port.
- **Screen space is y-down**, so the rotation *convention* (sign/direction) must be chosen to
  match the existing matrices exactly; the byte-identical trace is the arbiter.
- **Fidelity rule + harness:** behaviour-faithful; verify with the frame-180 byte-identical
  harness in `tasks/adhoc/pgzero-gl-inline/`.

## Design principle (settled — maintainer, 2026-09-04)

Using the book's **taught** math abstractions here is **consistent** with the ports' "library, not
framework" / "clearer code over abstractions" philosophy — not an exception to it. That principle
targets **framework-style inversion of control** (PyGame Zero's runner owning the loop, calling
*up* into the game) and depending on **pgzero-the-framework** — NOT the book's own math.
`InvertibleFunction`/`rotate`/`translate`/`compose` are library functions the game calls *down*
into, and the maintainer *teaches* them, so a game (and a book section) that uses them is coherent
with the curriculum. The abstraction **gradient** is exactly this: `boing_gl1.py` uses **zero**
abstractions (rawest, fixed-function GL, an early teaching point); richer games use more of the
taught abstractions — all still "library, not framework." Two real constraints remain: **(1) book
sequencing** — a book section referencing this code must come *after* the chapter teaching the
abstraction; **(2) don't reintroduce the pgzero framework.** Import from **`gacalc.transforms`**
(decided) — the ports already depend on gacalc and stay off course-layer code.

## Exactness — use INTEGER InvertibleFunctions, not the float rotor (maintainer, 2026-09-04)

The rotation the game needs is by **90° multiples** (`in_edge ∈ {0,1,2,3}`), and a 90°·k rotation
is a **signed coordinate permutation** — exactly representable with integers (the existing 2×2
matrices are all `0`/`±1`). So the right way to express this with the course's abstraction is an
**`InvertibleFunction` whose body is exact integer arithmetic** (the signed axis swap/negate),
*not* gacalc's float `plane_rotation` rotor. `plane_rotation` exists for arbitrary θ and would run
`sin`/`cos` of π/2, injecting ~6.12e-17 dirt into what should be clean `0`/`±1` — unnecessary
here. Building the rotation as an integer `InvertibleFunction` (paired with the already-integer
`translate`/`cell2pos`) makes the whole `translate ∘ rotate` composition **byte-identical by
construction** — no reliance on `int()` rounding absorbing float error, no trace-gated exactness
risk. (This is the maintainer's point — "couldn't the rotate and translate use integers and not
floats, to replicate?" — yes, and it dissolves the risk.)

This still uses the taught abstraction: `InvertibleFunction` is the course's *type*; constructing
one with an exact integer body is a legitimate instance of it (see "Design principle" above). Two
ways to build the four rotations, to settle during the study: **(a)** four hand-written
`InvertibleFunction`s (func = integer swap/negate, inverse = the opposite), selected by `in_edge`;
or **(b)** an integer-exact right-angle rotation constructor if gacalc/mathutils already offers one
— **verify before assuming one exists.** The float `rotate(90°·k)` is kept only as a possible
*teaching presentation* the book may show, never the shipped path. Verify byte-identity with the
frame-trace harness regardless.

## Open questions

1. **Build the four 90° rotations as hand-written integer `InvertibleFunction`s, or reuse an
   integer-exact right-angle rotation from gacalc/mathutils if one exists?** *(Recommend: verify
   what gacalc/mathutils already offers first; if nothing integer-exact, four hand-written integer
   `InvertibleFunction`s — exact by construction, still the taught type. Screen space is y-down, so
   pick the swap/negate signs that reproduce the existing matrices exactly; the trace confirms it.)*
2. **Book sequencing:** any book section that references this game code must come *after* the
   chapter teaching `InvertibleFunction`/`rotate`/`compose`. Which chapter is the earliest
   appropriate anchor for a myriapod cross-reference? *(Your call — you teach the math; I'll point
   the code comment at whatever chapter you name.)*

## Related

- `tasks/reference/coordinate-spaces-in-code-the-classics.md` › "The two genuine composed
  transforms" — the evidence base (myriapod is exception #1).
- `tasks/codetheclassics-camera-as-inverse.md` — the 2-D *translate* sibling (this is the *rotate*
  sibling); same "build on existing book/gacalc functions" guidance.
- `tasks/codetheclassics-leadingedge-projection-functions.md` — the 3-D projection case.
- `tasks/adhoc/pgzero-gl-inline/` — the byte-identical trace harness (and the exactness check).
