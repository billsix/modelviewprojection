# myriapod: a named local `rotate_90_degrees` over the raw `* e_12`

**Status:** IMPLEMENTED 2026-09-04 (branch `codetheclassics-gl1-and-space-refactors`) — byte-identical (frame-180 AE=0), ruff+ty clean.
**Priority:** 6
**Difficulty:** 2

## BLUF

Wrap myriapod's raw `offset * e_12` (the exact GA quarter turn) in a **named local**
`rotate_90_degrees` — an `InvertibleFunction` defined at module scope in `myriapod.py`, composed
into a 4-element `_rotations` table (`I^0..I^3`) indexed by `in_edge`. This keeps the maintainer's
two goals at once: a **named** function (discoverable, composable) whose one-line body is visibly
`v * e_12`, so a student still sees that **multiplying by the pseudoscalar rotates 90°**.
Byte-identical to the prior `* e_12` loop.

## Context / decision trail (2026-09-04)

- Builds directly on `tasks/codetheclassics-myriapod-rotation-via-pseudoscalar.md`, which replaced
  the hand-rolled 2×2 matrices with `offset * e_12`.
- The maintainer wanted a **named** form too ("I like named functions", and "students should know
  `* e_12` rotates 90°"). Both are served by a named local function whose body is `* e_12`.
- **Decided LOCAL, not in gacalc.** A gacalc `rotate_90_degrees` was researched and **parked** —
  geometricalgebra `tasks/add-quarter-turn-to-g2.md` — because it would serve a single downstream
  use and gacalc's generate→test→release cycle is heavy for a 4-line function; a local definition is
  trivial and shows the primitive at the use site. (A g2-only gacalc version stays viable on its own
  merits if broad reuse ever emerges — that task stands alone.)

## What was done (`ports/codetheclassics/vol1/myriapod/myriapod.py`)

- Import `InvertibleFunction`, `identity` from `gacalc.transforms` (`Vector`, `e_12` already
  imported).
- Module-level, after `cell2pos`:
  ```python
  rotate_90_degrees: InvertibleFunction[Vector] = InvertibleFunction(
      func=lambda v: v * e_12,        # a 90° turn in the e1-e2 plane IS * e_12
      latex_repr=r"R_{+90}",
      inverse=lambda v: v * -e_12,
      latex_repr_inv=r"R_{-90}",
  )
  _rotations: list[InvertibleFunction[Vector]] = [
      identity(),
      rotate_90_degrees,
      rotate_180_degrees,          # e_12^2 = -1: 180° = negate (its own inverse)
      inverse(rotate_90_degrees),  # e_12^3 = -e_12: 270° = inverse of one turn
  ]
  ```
  (The 180°/270° entries use the cheaper `rotate_180_degrees` = `× -1` and
  `inverse(rotate_90_degrees)` rather than two/three composed products — fewer
  geometric products per segment placement, byte-identical.)
- The segment placement now does `rotated = _rotations[self.in_edge](Vector(offset_x, offset_y))`
  (was a `for _ in range(in_edge): rotated = rotated * e_12` loop).

## Verification

- Frame-180 differential trace, prior `* e_12` version (HEAD) vs the named-function version, mvp
  container + Xvfb — **AE = 0** (byte-identical; the composed table reproduces `(*e_12)^in_edge`
  bit-for-bit, pre-verified separately). `ruff` + `ty` clean.

## Related

- `tasks/codetheclassics-myriapod-rotation-via-pseudoscalar.md` — the `* e_12` this builds on.
- geometricalgebra `tasks/add-quarter-turn-to-g2.md` — the (parked, standalone) gacalc alternative.
- `tasks/reference/gacalc-symbolic-transforms-and-lambdify.md` — the wider gacalc-transforms study.
