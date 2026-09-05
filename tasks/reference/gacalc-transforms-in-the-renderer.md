# gacalc transforms and the renderer's matrices: the bridge, the cost, and the compile-once fast path

**What this is:** the standing record of how mvp's Code-the-Classics renderer relates to gacalc's
transforms (`github.com/billsix/geometricalgebra`, `gacalc.transforms`) — what exists, what it costs, and
the pattern that makes "gacalc as the single source of truth for the GPU matrix" free. Harvested
2026-09-06 from `tasks/archive/2026/09/06/gacalc-transforms-for-rotate-translate.md` (the 2026-09-04
study) and `tasks/archive/2026/09/06/pgzero-gl-renderer-matrix-via-gacalc-perf.md` (the perf half, measured
2026-09-06 with `tasks/adhoc/pgzero-gl-renderer-matrix-via-gacalc-perf/bench_model_matrix.py`, gacalc 0.0.19).
Project: `github.com/billsix/modelviewprojection`.

## The bridge exists and matches mvp's convention

`gacalc.transforms.to_matrix(fn, cls, n=None, *, backend="numpy"|"sympy")` returns the homogeneous
`(n+1)×(n+1)` matrix of a linear/affine `InvertibleFunction` — 4×4 for `g3` — by probing the basis and
the origin (column i = `fn(e_i) - fn(0)`, last column = `fn(0)`). Translation lands in the **last
column** (column-vector, premultiply), which is exactly what the renderer uploads with
`glUniformMatrix4fv(..., GL_TRUE, m)` (row-major, transposed on upload). Verified bit-for-bit: the
renderer's `_translate(tx, ty) @ _scale(w, h)` equals
`to_matrix(translate(b=tx * g3.Vector.e_1 + ty * g3.Vector.e_2) @ scale_non_uniform(w, h, 1), g3.Vector)`
(the translation written as gacalc's idiom, a linear combination of the basis vectors with every
coefficient explicit — the maintainer's correction of 2026-09-06 to a `g3.Vector(tx, ty, 0)` draft). A non-linear
`fn` (leadingedge's perspective divide) correctly raises `ValueError` — that projection stays
hand-rolled, as decided in `tasks/archive/2026/09/05/codetheclassics-leadingedge-projection-functions.md`.

## Where matrices are built, and where they are not

- **Matrix path (feeds `uModel`)** — the renderer only, inlined in every game: `Renderer.draw_image`
  (and `filled_rect`/`draw_image_region`) build `translate @ scale` **per sprite per frame**; the
  ortho projection (`ortho_pixels`) is built **once per renderer**. There is **no rotation** in
  `uModel`: sprites are axis-aligned. `boing_gl1` uses the fixed-function equivalents.
- **Direct path (CPU point math)** — already gacalc: rotations via `myriapod`'s `* e_12` and
  kinetix's `plane_rotation`/`_turn`; camera/scroll via `inverse(translate(...))` in soccer,
  leadingedge, beatstreets. The 2026-09-06 census of hand-rolled trig left in the game halves:
  avenger's `Vector(cos(a), sin(a))` bullet direction (a polar-to-cartesian of an `atan2` angle),
  soccer's angle-to-sprite-index lookup, leadingedge's `cos(i/20)` hill shape — none is a
  transform of a point; nothing left to convert.

## The cost, measured (µs per 4×4 model matrix, project image, 2026-09-06)

| builder | µs/call | vs today |
|---|---|---|
| hand-built numpy, `_translate @ _scale` (today) | 3.19 | 1.0× |
| template fill (copy an identity, poke 4 numbers) | 0.34 | 0.11× |
| `to_matrix` per call | 514 | **161×** |
| gacalc once with sympy symbols, `sympy.lambdify` per call | 1.45 | 0.45× |
| **gacalc once with sympy symbols, compiled fill per call** | **0.47** | **0.15×** |

(2026-09-04's first measurement was 1669 µs / 492×; gacalc 0.0.19 reads coordinates from the
blade dict instead of computing products, hence 514.) `to_matrix` per draw is out: ~50 sprites at
60 Hz would spend ~1.5 ms/frame building matrices. But the matrix's **structure** is fixed — only
`tx, ty, w, h` vary — so the transform can be defined in gacalc **once, symbolically**:

```python
STX, STY, SW, SH = sympy.symbols("tx ty w h")
M = to_matrix(translate(b=STX * g3.Vector.e_1 + STY * g3.Vector.e_2)
              @ scale_non_uniform(SW, SH, 1),
              g3.Vector, backend="sympy")        # [[w,0,0,tx],[0,h,0,ty],[0,0,1,0],[0,0,0,1]]
```

and either `sympy.lambdify((STX, STY, SW, SH), M, "numpy")` (2× faster than today) or, reading off
which entries hold which symbol, a template + four assignments per draw (7× faster than today).
gacalc is then the *definition* of the sprite transform, checked once at import, and the per-draw
cost is below the hand-built numpy it replaces. The same applies to `ortho_pixels`
(`translate(b=-1 * g3.Vector.e_1 + 1 * g3.Vector.e_2) @ scale_non_uniform(2/w, -2/h, -1)`), which
is built once anyway.

## Adopted (2026-09-06, the maintainer: "I love it")

Every GL 3.3 game engine now carries a `MatrixTemplate` (frozen dataclass: the constant 4×4 plus
`(row, col, parameter)` slots, `compile(fn, params)` from `to_matrix(..., backend="sympy")`, `fill`)
and defines `MODEL = MatrixTemplate.compile(translate(b=_TX * g3.Vector.e_1 + _TY * g3.Vector.e_2)
@ scale_non_uniform(_W, _H, 1), (_TX, _TY, _W, _H))`; `ortho_pixels` is `to_matrix` of
`translate(b=-1 * e_1 + 1 * e_2) @ scale_non_uniform(2/w, -2/h, -1)` with numbers, once per
renderer. `_translate`/`_scale` are gone. Gated frame-identical and trace-identical in all games
(`tasks/archive/2026/09/06/renderer-model-matrix-from-gacalc.md`). **Next:** the template becomes a
gacalc feature (geometricalgebra `tasks/matrix-template-compile-once.md`, a method on the function
types) and the ten copies are deleted — mvp `tasks/ctc-use-gacalc-matrix-template.md`, blocked on it.

## The recommendation as it stood before adoption (Fable, 2026-09-06)

- Keep the direct path as is; nothing hand-rolled remains that a gacalc transform would express better.
- The renderer's `uModel` **can** come from gacalc at no cost with the compile-once pattern; whether to
  do it is a taste call ("one source of truth" vs. eleven engine copies + gates to re-run, and step 3
  of `tasks/pgzero-gl-inline-strip-reextract.md` — parked — would be the natural moment). Filed as
  `tasks/renderer-model-matrix-from-gacalc.md` (READY, awaiting go-ahead) with the exact code.
- If it is done, `boing_gl1`'s fixed-function `glTranslatef`/`glScalef` path is out of scope (no matrix
  to build).
