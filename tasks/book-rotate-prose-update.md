# Book: update the rotate/orientation prose to match the plane_rotation code

**Status:** proposed — Bill will fix the book sources himself later
(2026-07-09: "just update the book's sources with a todo — I'll fix book
sources later, add in a task for this particular one").
**Created:** 2026-07-09

## What changed in the included code (the prose still tells the old story)

`src/modelviewprojection/mathutils.py`, 2026-07-09 (the plane_rotation
adoption + Bill's inline/typing/wedge follow-ups — details in
`tasks/plane-rotation-mathutils-adoption.md`):

- **`rotate` / `rotate_x` / `rotate_y` / `rotate_z` are no longer `def`s**:
  each is a typed module-level binding of gacalc's `plane_rotation`
  factory — the plane (`e_1 ∧ e_2`, or the per-axis 3D planes) is derived
  ONCE at import into a normalized unit bivector, and every call/`.at(t)`
  just assembles the half-angle rotor from it. The old per-call
  build-a-to-vector-and-call-`rotor_rotation` shape the chapters narrate
  is gone.
- **`rotate_90_degrees` was retired** (no external callers; a quarter
  turn is `rotate(math.radians(90))`).
- **The orientation predicates moved and changed spelling**:
  `is_counter_clockwise` / `is_clockwise` / `is_parallel` now live in
  `framebuffer/softwarerendering.py` (their only consumer, the
  point-in-triangle test) and compute the sign of the **wedge**
  (`(v1 ^ v2).coeff_e_12` — the 2D cross product / signed area) instead
  of the rotate-by-90-then-dot trick. Their doc-region markers moved
  with them (no chapter currently includes those regions, but prose may
  reference the old trick).

## Where the TODOs sit (grep `TODO (2026-07-09` in book/docs/)

- `book/docs/ch07.rst` — above the `define rotate` literalinclude.
- `book/docs/ch14.rst` — above the `define rotate z` include (covers
  z/x/y, which follow consecutively).

## What the rewrite should teach (raw material)

The plane+angle story: two vectors define a plane; their normalized wedge
is the plane's unit bivector `i` (`i² = −1`); `R = cos(θ/2) − sin(θ/2)·i`;
rotation is the sandwich `R v R̃`; establishing the plane once and varying
θ is what makes interpolation (`.at(t)`) natural. For ch07's orientation
material (if touched): the wedge IS the 2D cross product — the
rotate-90-then-dot trick computes exactly `(v1 ∧ v2).coeff_e_12`.
Overlaps with gacalc-math-migration Phase 4 (the book) — fold or
cross-reference there as convenient.
