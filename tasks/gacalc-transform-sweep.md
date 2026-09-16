# Sweep the codebase to apply the "express transformations with gacalc" rule

**Status:** COMPLETE — the in-scope sweep is done, the conversions are proven matrix-identical,
and the exempt boundary was confirmed by the maintainer (2026-09-17). Not archived this session at
the maintainer's request.
**Priority:** 6
**Difficulty:** 7
**Started:** 2026-09-16 (William Emerison Six <billsix@gmail.com>)
**Finished:** 2026-09-17 (William Emerison Six <billsix@gmail.com>)

## BLUF

Enforce the CLAUDE.md rule — *if a transformation can be expressed with gacalc, express it with
gacalc (reverse with `inverse()`, animate with `.at()`, realize to a 4×4 with
`cayleyscene.to_matrix` only when GL needs it); never hand-roll it in raw numpy* — across the
codebase, **except** the sections that deliberately introduce matrices for teaching
(`glPushMatrix`/`glMultMatrix`, the matrix-stack demos) and behaviour-faithful ports. Done = every
in-scope hand-rolled transform is converted or explicitly exempt, `ty` green, `make format` clean,
and behaviour proven unchanged.

## Context

- The rule was added to CLAUDE.md › "Central abstraction" on 2026-09-16 (the bullet beginning "If a
  transformation can be expressed with gacalc…"). It was prompted by the framebuffer work
  (`tasks/framebuffer-in-perspective.md`), where a hand-rolled `np.diag` + translation-column morph
  reversed with hand-computed factors was converted to `to_matrix(compose([...]))` + `.at()` +
  `inverse()`. That conversion is the model for this sweep.
- gacalc gives `translate` / `uniform_scale` / `scale_non_uniform` / `rotate(_x/_y/_z)` / `compose`
  / `inverse` / `identity`, plus `f.at(t)` (interpolation law `1+(m-1)t` for scale, `v·t` for
  translate) and `cayleyscene.to_matrix(f)` (affine → 4×4 for GL upload).

## What was done

Enumerated `np.identity` / `np.diag` / `linalg.inv` / hand-built 4×4 `np.array` / manual `@` chains
across `src`, `ports`, and `assignments`, and classified each hit.

**Converted (the mvpvisualization showcase, which should be gacalc-pure):**
`modelviewperspectiveprojection.py` and `modelvieworthoprojection.py` — the "View From" center-on
used `np.linalg.inv(inv @ to_matrix(placement))`. Replaced with the gacalc inverse of the composed
frame: `to_matrix(inverse(compose([inverse_transform(t), transform(space, t)])))`. Proven
matrix-identical for affine A, B (`to_matrix(inverse(compose([A, B]))) == inv(to_matrix(A) @
to_matrix(B))`) in `tasks/adhoc/gacalc-transform-sweep/verify_inverse_of_frame.py`. The now-unused
`numpy` import was removed from the ortho demo. Verified: ruff + `ty` clean, full `pytest` 75/75.

## Exempt list — deliberate matrix pedagogy and faithful ports (confirmed by the maintainer 2026-09-17)

Left alone, each with its reason:

- `demos/demo22/demo22.py` `np.identity` view/proj/shadow — a demo19+ book demo whose point *is*
  the shader matrix stack (CLAUDE.md: "demo19+ … the FF/shader matrix stack is the same idea on the
  GPU"). Matrix pedagogy.
- `ports/openglsuperbiblev4/**` (`chapt08/toon`, `chapt16/vertexblend`, `chapt18/fbo*`,
  `chapt19/SphereWorld32`, …) — faithful ports of the SuperBible's matrix-based book code;
  converting would betray both port fidelity and the matrix-teaching intent.
- `src/modelviewprojection/pgzero_gl/renderer.py` `np.identity` — a perf-sensitive CtC render hot
  path, owned by `tasks/pgzero-gl-renderer-matrix-via-gacalc-perf.md`.
- `matrix_stack.py` (the stack implementation) and `cayleyscene.to_matrix` (the GL boundary) — the
  rule *expects* these; not violations. `planar_shadow` is deliberately rank-3 (non-invertible).
- `assignments/` — no hits.

**Scope:** ports were scanned; all hits are SuperBible matrix-faithful ports → exempt. So the
effective scope was `src/modelviewprojection` (the mvpviz showcase), now clean. The maintainer
confirmed 2026-09-17 that the exempt list stands and `ports/**` is left alone.

## The smell (for future audits)

Raw-numpy geometry math where gacalc would do: `np.identity(4)` / `np.diag(...)` / a hand-built 4×4
`np.array` / manual `@` chains standing in for translate/scale/rotate/compose / hand-computed
inverses (reciprocal or negated factors) / hand-written interpolation (`1 + (m-1)*t`, or reversed
ratios). Start from `grep -rEn "np\.(identity|diag|array)\(|@ np\.|linalg\.inv" src tools`.

## Adhoc scripts (kept under `tasks/adhoc/gacalc-transform-sweep/`)

- `verify_inverse_of_frame.py` — proves `to_matrix(inverse(compose([A, B])))` equals
  `inv(to_matrix(A) @ to_matrix(B))` for affine A, B.

## See also

- `CLAUDE.md` › "Central abstraction" — the rule this enforces.
- `tasks/framebuffer-in-perspective.md` — the worked example of the conversion.
- `tasks/reference/gacalc-transforms-in-the-renderer.md`, `tasks/reference/architecture-overview.md`
  (§ transform layer).
