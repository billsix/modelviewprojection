# Using gacalc math for fast transforms: symbolic derivation + lambdify

**Reference document** (never archived; update in place). Author: William Emerison Six
<billsix@gmail.com>, 2026-09-04. Records the ideas + measurements from the 2026-09-04 investigation
into whether the `pgzero_gl` renderer (and the games) can build their transforms from the
maintainer's own gacalc math without paying a runtime cost. **Every number below is measured** in
the mvp container (software GL); absolute microseconds vary by host — the **ratios** are the point.
Reproduce with `tasks/adhoc/gacalc-lambdify-transforms/perf_test.py`.

## BLUF — the technique worth remembering

**When a transform's composition is known statically** (its *structure* is fixed and only a few
numbers vary per call — e.g. the renderer's `translate(tx,ty) @ scale(w,h)`, or a fixed 90°
rotation), you can have **gacalc define it and still run fast**:

1. Build the transform **once at module-load time** with **symbolic** parameters (`sympy` symbols)
   using the maintainer's own gacalc transforms.
2. Convert it **once** to a symbolic matrix with `gacalc.transforms.to_matrix(fn, cls,
   backend="sympy")` (or apply it symbolically).
3. `sympy.lambdify((params...), expr, "numpy")` → a **compiled numeric function**.
4. **Per call** (the hot path), call the lambdified function with the numbers. No gacalc `Vector`
   objects, no sympy, in the loop.

**This is gacalc as the single source of truth AND full speed** — for the renderer's model matrix
it measured *faster than the current hand-written numpy*. It's the maintainer's own idea
(2026-09-04: "if the composition of transformations is known, we can do the lambdify method").

## The measurements (renderer model matrix: translate + scale, per sprite per frame)

The renderer builds a 4×4 `uModel` per sprite (`renderer.py:227`) as hand-written numpy
`_translate(tx,ty) @ _scale(w,h)`. gacalc can produce the **identical** matrix from
`translate(b=Vector(tx,ty,0)) @ scale_non_uniform(w,h,1)` — verified `np.allclose` True, same
homogeneous shape, translation in the last column (mvp's `matrix_stack` convention). Speed:

| approach | per-call | vs hand | verdict |
|---|---|---|---|
| hand-built numpy (current) | ~3.9 µs | 1× | the baseline |
| gacalc `to_matrix` **called per draw** | ~1669 µs | **~492×** | correct but **non-starter** — it probes gacalc `Vector`s (basis + origin) every call |
| **symbolic `to_matrix` once + `lambdify`** | ~1.5 µs | **~0.4×** | correct **and faster** — one compiled numpy expression |

The symbolic matrix gacalc produced for the renderer's transform:

```
⎡w  0  0  tx⎤
⎢0  h  0  ty⎥
⎢0  0  1  0 ⎥
⎣0  0  0  1 ⎦
```

So the naive "call `to_matrix` in the hot loop" idea is dead (492×); the **lambdify** idea is the
one that works (and wins).

## Applying it to rotations — the "quarter turn" (and why it does NOT need sympy)

The 90° rotation in the e₁e₂ plane came up via `myriapod`, done as `offset * e_12`. **A quarter
turn is exact and sympy-free by construction** — do not reach for the lambdify machinery here:

| form | exact? | sympy? | speed | notes |
|---|---|---|---|---|
| **`v * e_12` (multiply by the unit pseudoscalar)** | **yes** (±1 only) | **no** | ~1.1 µs | `(x,y)→(-y,x)`; the right form; what myriapod uses |
| `Vector.dual()` (gacalc method) | yes | no | (method) | same operation, **opposite direction** (`v·I⁻¹` = −90°) |
| `plane_rotation(e_1,e_2)(math.radians(90))` | **NO** | no | — | **float** angle → `cos`/`sin` of π/2 carry ~6e-17 dirt (the reason `* e_12` was chosen) |
| `plane_rotation(e_1,e_2)(sympy.pi/2)` | yes | **YES** | ~44 µs | exact but **needlessly drags in sympy** and is 41× slower — see below |

**Why sympy is the wrong tool for a quarter turn (maintainer, 2026-09-04):** `plane_rotation(θ)`
is the *general-angle* rotor — it builds `exp(−B·θ/2)` from `cos`/`sin`. Feeding it 90° forces the
choice "float (dirty) or symbolic (sympy, slow)". But **a quarter turn is not "rotate by an angle
that happens to be 90°" — it is the pseudoscalar product**, which is exact ±1 arithmetic with no
angle, no `cos`/`sin`, and no sympy. So the right implementation is `v * e_12` (or `.dual()` for
the other sense), full stop. **The lambdify technique above is for the *parametrised matrix* case;
a fixed quarter turn does not need it and should not use sympy.**

**Subtlety to know:** `plane_rotation(...)(sympy.pi/2)` and `* e_12` are numerically equal but
differ in the **sign of zero** (`-0.0` vs `0.0`); after `int()`/pixels both give the same pixel, so
it is frame-identical but not raw-bit-identical. (One more reason to prefer the direct `* e_12`.)

## Roads NOT taken (and why — recorded on purpose)

- **Call `to_matrix` per draw in the renderer** — rejected (492× regression).
- **Float `plane_rotation` for a 90° turn** — rejected (inexact; ~1e-16 that can flip an
  `int()`-truncated pixel; this is what sent `myriapod` to `* e_12` in the first place).
- **`Vector.dual()` for myriapod** — wrong rotation direction (−90° vs the needed +90°); would need
  inverted `in_edge` indexing, less clear.
- **Convert the renderer without lambdify** — same as the 492× point.
- **Convert `bunner`/`avenger` cameras** — separate concern; structural poor fits, left raw (see
  `tasks/archive/2026/09/05/codetheclassics-camera-as-inverse-other-scrollers.md`).
- **Move the game-logic direct-path onto gacalc wholesale** — already largely true and done
  opportunistically (soccer/leadingedge/beatstreets `inverse(translate)`, myriapod `* e_12`,
  kinetix `plane_rotation`); no big-bang needed.

## Where this could go next (options, not decisions)

1. **Renderer model matrix via lambdify** — viable and *faster*; rollout touches the shim renderer
   + the 10 inlined game copies (or lands via step 3 re-extract). Owned by
   `tasks/pgzero-gl-renderer-matrix-via-gacalc-perf.md`.
2. **A named, exact, fast `quarter_turn`** — lambdify the symbolic `plane_rotation(e_1,e_2)(pi/2)`,
   or add a real `quarter_turn` to gacalc so it's a first-class call (see
   `tasks/add-quarter-turn-to-gacalc.md`). Then `myriapod` could read `quarter_turn(offset)` instead
   of `offset * e_12`.
3. **General reuse:** any hot-path transform with a fixed composition is a candidate — derive once
   symbolically, lambdify, cache the function. The one-time matrices (e.g. `ortho_pixels`) can use
   `to_matrix` directly with no perf concern at all.

## Related

- `tasks/adhoc/gacalc-lambdify-transforms/perf_test.py` — the runnable harness for every number here.
- `tasks/gacalc-transforms-for-rotate-translate.md` — the parent study (the crux: `to_matrix`
  exists + is correct).
- `tasks/pgzero-gl-renderer-matrix-via-gacalc-perf.md` — the perf/rollout task for the renderer.
- geometricalgebra `tasks/add-quarter-turn-to-g2.md` — proposal to make `quarter_turn` a real
  gacalc function (**g2-only**; the removed `rotate_90_degrees` — which mis-transformed e₃+ vectors
  — is why it must be dimension-specific).
- `tasks/archive/2026/09/05/codetheclassics-myriapod-rotation-via-pseudoscalar.md` — where `* e_12` lives today.
