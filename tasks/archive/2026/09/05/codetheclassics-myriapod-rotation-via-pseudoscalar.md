# myriapod segment rotation via the unit pseudoscalar (exact 90° in GA)

**Status:** IMPLEMENTED 2026-09-04 (branch `codetheclassics-gl1-and-space-refactors`) — byte-identical (frame-180 AE=0), ruff+ty clean.
**Priority:** 5
**Difficulty:** 3

## BLUF

Express myriapod's four `in_edge` segment rotations as **multiplication by the unit pseudoscalar
`e_12`** — the geometric-algebra-native 90° rotation. `in_edge` selects `I^0..I^3` (rotate by
0/90/180/270°), so the cell-local offset is right-multiplied by `I = e_1 e_2` once per `in_edge`
step. This replaces the hand-written 2×2 integer rotation matrices with the algebra the whole
course is built on, and it is **exact**: `I`'s components are `±1`, so there is **no `sin`/`cos`
and no floating-point error** (unlike a general `rotate(θ)` rotor). Proven byte-identical.

## Decision trail (for review — this corrects an earlier wrong call)

- **Sibling task `tasks/archive/2026/09/05/codetheclassics-myriapod-rotation-as-functions.md` first RECOMMENDED NOT
  doing this** (2026-09-04), on the reasoning that `gacalc.transforms` has no `rotate`, the rotor
  (`plane_rotation`) is float and inexact for 90° (unsafe on this integer game), and a bespoke
  integer `InvertibleFunction` was ceremony that didn't beat the exact 2×2 matrix.
- **That was a real miss.** The maintainer pointed out (2026-09-04) that a 90° rotation in 2-D GA
  is simply multiplication by the **unit pseudoscalar** — exact, no rotor. gacalc exposes it as
  `g2.e_12` (and `e_1 * e_2` yields it as a `Rotor(coeff_e_12=1)`). So there *was* a clean,
  exact, existing-code answer all along — I was tunnel-visioned on `rotate(θ)` and forgot the
  library is a geometric-algebra library. This task supersedes that recommendation.
- **Verified before implementing:** in the mvp container, `Vector(x, y) * e_12^k` reproduces all
  four `in_edge` matrices **bit-for-bit** (packed IEEE-754 doubles compared) for every test
  vector and every `k ∈ {0,1,2,3}`; `Vector * Rotor` returns a `Vector`.

## The GA (why it is exact)

For `v = x·e_1 + y·e_2` and `I = e_1 e_2` (I² = −1):

- `v · I` (right product) = `(-y)·e_1 + (x)·e_2`, i.e. `(x, y) → (-y, x)` = rotate **+90°**.
- `I^0..I^3 = 1, I, -1, -I` → rotate by 0/90/180/270°.

Mapped to myriapod's matrices (`[[1,0,0,1],[0,-1,1,0],[-1,0,0,-1],[0,1,-1,0]][in_edge]`):
`in_edge=0`→I⁰ (identity), `1`→I¹ `(x,y)→(-y,x)`, `2`→I² `(-x,-y)`, `3`→I³ `(y,-x)`. Exact match.

## Change

`ports/codetheclassics/vol1/myriapod/myriapod.py` — added `e_12` to the gacalc import; replaced
the 2×2-matrix block (`~:2588-2601`) with:

```python
# A 90° rotation in 2-D geometric algebra is multiplication by the unit
# pseudoscalar I = e_1 e_2 -- EXACT (I's components are ±1; no sin/cos). in_edge
# picks I^0..I^3 (rotate 0/90/180/270°), so right-multiply once per edge-step.
rotated: Vector = Vector(offset_x, offset_y)
for _ in range(self.in_edge):
    rotated = rotated * e_12
offset_x, offset_y = int(rotated.x), int(rotated.y)
```

The rotated components are exact integer-valued floats, so `int(...)` recovers the original ints
with no truncation — the downstream `cell2pos` and `self.pos` stay integer, byte-identical.

## Verification

- `Vector(x,y) * e_12^k` == the 2×2-matrix result, bit-for-bit (pre-implementation check).
- Frame-180 differential trace, original (HEAD) vs converted (mvp container + Xvfb) — **AE = 0**.
- `ruff` + `ty` clean.

## Open for maintainer

- Book-sequencing: the comment says "the algebra the course is built on"; pin the chapter that
  introduces the pseudoscalar / `e_12` if you cross-reference this from the book.
- This is arguably the **best** of the game-refactors for the course: it shows a bedrock GA
  identity (90° rotation = ×pseudoscalar) inside a real game.

## Related

- `tasks/archive/2026/09/05/codetheclassics-myriapod-rotation-as-functions.md` — the superseded `rotate∘translate`
  framing (kept for the decision history).
- `tasks/reference/coordinate-spaces-in-code-the-classics.md` — myriapod is the one game with a
  genuine composed rotate-then-translate; this makes the rotate half a course-native operation.
- `tasks/archive/2026/09/05/codetheclassics-camera-as-inverse.md`, `...-leadingedge-projection-functions.md` — the
  translation siblings (both landed byte-identical).
