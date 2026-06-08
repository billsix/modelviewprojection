# Migrate mvp math onto gacalc (delete overlapping math, import gacalc vectors)

**Status:** IN PROGRESS — Phase 0 + Phase 1 landed 2026-06-08
**Started:** 2026-06-07

## Progress log

- **2026-06-08 — Phase 0 (dependency + façade) + Phase 1 (rebuild graphics math) DONE.**
  - `gacalc>=0.0.3` added to `requirements.txt`; installed into a fresh `/mvp/venv`
    (direct `pip install`, no podman). Math tests run via
    `PYTHONPATH=/mvp/src /mvp/venv/bin/python -m pytest tests/test_mathutils.py`.
  - `src/modelviewprojection/mathutils.py` is now a **gacalc façade**: re-exports
    the transform layer + `Vector1/Vector2/Vector3`, and **rebuilds the
    graphics-only math on gacalc vectors** — `rotate`/`rotate_90_degrees`/
    `rotate_around`, `rotate_x/y/z` (each carries its interpolation law +
    `Linearity.LINEAR`), `ortho` (AFFINE) / `perspective` (NONLINEAR) /
    `cs_to_ndc_space_fn`, `find_normal` (cross = `wedge` then `dual`) /
    `plane_equation` / `distance_to_plane`, the predicates, and `FunctionStack`.
    doc-region markers preserved for ch07/08/14/16/17/18.
  - `tests/test_mathutils.py` rewritten as a focused suite for the retained
    graphics math (vector-arithmetic/transform-core tests now live in gacalc).
    **22 passing**, incl. a test tying mvp's `rotate_z` to gacalc `to_matrix`.
  - **Latent bug fixed:** the old `perspective` inverse un-scaled by the NDC-space
    z instead of the recovered camera-space z, so it wasn't a true inverse; the
    rebuild fixes it (round-trip test guards it).
  - **gacalc-side follow-up:** restored `InvertibleFunction` as `Generic[V]`
    (bound to `AbstractMultiVector`) — it had been generic in mvp but gacalc's
    plainer version wasn't; `InvertibleFunction[Vector2]/[Vector3]` annotate again.
- **2026-06-08 — Phase 2 (call-site migration) STARTED; ports phase DONE.**
  - **Key idiom finding:** gacalc `Vector3` takes **positional** args, so
    `Vector3D(x, y, z)` → `Vector3(x, y, z)` is a straight rename; `.x/.y/.z` →
    `.coeff_e_1/2/3`. `find_normal`/`plane_equation` already return gacalc
    `Vector3`. So the port migration was mechanical (rename + attribute swap),
    no construction helper needed.
  - **All 13 SuperBible ports migrated** (chapt01 block; chapt05
    litjet/shinyjet/shadow/sphereworld; chapt06 fogged/multisample/sphereworld;
    chapt08 pyramid/sphereworld; chapt09/11 sphereworld; chapt19 SphereWorld32) —
    every `.x/.y/.z` was on a vector (`plane_normal`/`pn`/vertices), so no
    non-vector clobbering. Zero `Vector3D`/`.x/.y/.z` leftovers; all `py_compile`
    clean. (GL run-verification is Bill's — the venv has no glfw/GL.)
- **2026-06-08 — Phase 2 (call-site migration) COMPLETE.** `grep Vector[123]D`
  over `src/`+`tests/`+`assignments/`+`ports/` `.py` returns **nothing**.
  Migrated this session beyond the ports: 14 demos (demo05–18), 9 viz/util,
  4 plotting helpers (notebooksrc plot2d/ndc/framebuffer + util/nbplotutils),
  2 cayley tests, the demo02 assignment, and `framebuffer/softwarerendering.py`.
  - **Mechanical transform** per file: `Vector{1,2,3}D`→`Vector{1,2,3}`,
    `.e_N()`→`.e_N` (basis static-method → class constant), `.x/.y/.z`→`.coeff_e_N`,
    `.isclose`→`.is_close` (preserving `math.isclose`), keyword `Vector2D(x=,y=)`→
    positional, `scale_non_uniform_{2,3}d`→`scale_non_uniform`. No GL `float()`
    needed — `ctypes.c_float` accepts sympy `Float`.
  - **Natural basis inlined** (per Bill): top-of-file `e_1 = Vector2.e_1` locals
    removed, usages inlined to `Vector2.e_1`. Considered sourcing a bare `e_1`
    from `from gacalc.g2 import e_1`, but that yields the **full `G2`**, not
    `Vector2` — which loses the graded type AND defeats the fast generated
    sandwich (a `G2` rotor has no closed-form `sandwich`). gacalc's own
    convention prescribes `Vector2.e_1`, so the inlined form stays.
  - **Verified headless:** `test_cayley_graph` **14 passed**; `vec1.py` worked
    examples pass (its remaining failing assert is a deliberate student-TODO
    placeholder). GL demos/ports are `py_compile`-clean; Bill run-verifies those.
    `ports/README.md` still names `Vector3D` in prose — doc, left as-is.
- **NOT yet done:** **Phase 4** (rewrite ch05/06/14 on
  gacalc).

## Goal

Stop maintaining mvp's home-grown vector algebra and transform layer. Depend on
the published **`gacalc`** package (PyPI) for everything that overlaps, **delete
the duplicated code from `mathutils.py`**, and rebuild only the genuinely
graphics-specific math *on top of* gacalc. The MVP vector representation
(`Vector`/`Vector1D`/`Vector2D`/`Vector3D`) is **deleted** — demos use gacalc's
multivector vectors (`G1`/`Vector1`, `G2`/`Vector2`, `G3`/`Vector3`) instead.

This is "Option B" from the investigation: switch the vector *type*, not just
import a few helpers. It is the larger change but removes the most duplication.

## Ports: Path Y — port them (DECIDED 2026-06-07)

The 13 SuperBible ports under `ports/openglsuperbiblev4/` use mvp math: each
imports `Vector3D` plus `find_normal` / `plane_equation` from
`modelviewprojection.mathutils`, relying on the named-field API gacalc lacks —
**positional** construction `Vector3D(0.0, -25.0, 0.0)` and `.x`/`.y`/`.z` reads
(`GL.glNormal3f(n.x, n.y, n.z)`, `glVertex3f(p1.x, p1.y, p1.z)`).

**Decision: Path Y.** No compat type is kept. Rewrite the ports to gacalc idioms
(positional → scaled-sum `x*e_1 + y*e_2 + z*e_3` or `Vector3(coeff_e_*=…)`;
`.x/.y/.z` → `float(v.coeff_e_1)` etc. at the GL boundary), and **rebuild
`find_normal`/`plane_equation`/`distance_to_plane` on gacalc** (cross →
wedge+dual) so they take/return gacalc `Vector3`. This fully removes mvp's
named-field vector type — the maximal-removal end-state Bill wants — at the cost
of editing these parked files (bounded, mechanical). The 13 files:
chapt01 block; chapt05 litjet/shinyjet/shadow/sphereworld;
chapt06 fogged/multisample/sphereworld; chapt08 pyramid/sphereworld;
chapt09/11 sphereworld; chapt19 SphereWorld32. They use **only** the plane
geometry helpers — no transform/stack/animation surface — so the rewrite is
purely vector-idiom + the two helpers.

## Decision: what moves where

| mvp `mathutils` symbol(s) | Disposition |
|---|---|
| `Vector`, `Vector1D`, `Vector2D`, `Vector3D` | **DELETE entirely** (Path Y) → use gacalc `AbstractMultiVector` / `Vector1` / `Vector2` / `Vector3` everywhere, incl. the rewritten ports. No compat type kept. |
| `InvertibleFunction`, `inverse`, `compose`, `identity`, `compose_intermediate_fns`, `compose_intermediate_fns_and_fn`, `translate`, `uniform_scale`, `scale_non_uniform_2d/3d` | **DELETE** → import from `gacalc.transforms` (`scale_non_uniform_2d/3d` → general `scale_non_uniform(*factors)`) |
| `InvertibleFunction.at()`, `.steps()`, `interpolate`/`components` fields (the animation layer) | **PORT UPSTREAM to gacalc** (new module) — Phase G. mvp then gets it for free via the import. |
| `rotate`, `rotate_90_degrees`, `rotate_around` (angle-based 2D) | **REBUILD in mvp on gacalc** — these were deliberately removed from gacalc (planar-only, e₁e₂ plane) |
| `rotate_x`, `rotate_y`, `rotate_z` (axis rotations) | **REBUILD in mvp on gacalc** |
| `ortho`, `perspective`, `cs_to_ndc_space_fn` | **REBUILD in mvp on gacalc** (graphics-only) |
| `find_normal`, `plane_equation`, `distance_to_plane` | **REBUILD on gacalc** (Path Y; cross → wedge+dual, take/return gacalc `Vector3`) and update the ports that call them. Keep the CCW-winding tests as the oracle. |
| `sine`, `cosine`, `is_counter_clockwise`, `is_clockwise`, `is_parallel`, `abs_sin` | **REBUILD in mvp on gacalc** (gacalc's `cosine`/`is_parallel_to` are different-API multivector methods, self-flagged uncertain — don't depend on them) |
| `FunctionStack`, `fn_stack`, `push_transformation` | **LEAVE IN MVP** (rewire `modelspace_to_ndc_fn` to call gacalc `compose`) |

After migration, `mathutils.py` becomes a **thin façade**: it imports the gacalc
transform/vector names and re-exports them, and defines the rebuilt
graphics-only helpers + the function stack locally. Keeping the façade means most
`from modelviewprojection.mathutils import translate, compose, …` lines in demos
keep working unchanged — only *vector construction and attribute access* must be
rewritten (the type genuinely differs; that can't be façaded away).

## Hard sequencing constraint (read first)

mvp imports gacalc **from PyPI**, and the animation layer (`at`/`steps`) does not
exist in gacalc yet. So the order is forced:

1. **Phase G** lands the animation layer in gacalc **and is released to PyPI**
   (gacalc is at `0.0.3` locally; this needs a bump, e.g. `0.0.4`).
2. Only then can mvp pin `gacalc>=0.0.4` and rip out its own `InvertibleFunction`.

Until the release exists, mvp could develop against an editable/local gacalc
checkout, but the merge to mvp `main` must wait for the PyPI release. Phase G is a
**gacalc-side task** — when we start it, give it its own task doc in the
`/geometricalgebra` repo; this section is just the mvp-side contract.

## gacalc API the demos must adopt (verified against generated `g2.py`/`g3.py`)

This is the idiom-translation cheat-sheet. The biggest source of churn.

| mvp idiom | gacalc idiom | note |
|---|---|---|
| `Vector3D(x=1, y=2, z=3)` | `1*Vector3.e_1 + 2*Vector3.e_2 + 3*Vector3.e_3` (or `Vector3(coeff_e_1=1, coeff_e_2=2, coeff_e_3=3)`) | fields are `coeff_e_1/2/3`, not `x/y/z` |
| `Vector3D.e_1()` (method, parens) | `Vector3.e_1` (class **constant**, no parens) | static-method → ClassVar |
| `Vector3D.zero()` | `Vector3.zero()` | still a classmethod — unchanged |
| `v.x` / `v.y` / `v.z` | `v.coeff_e_1` / `…e_2` / `…e_3`, or `v.component(Vector3.e_1)` | **~126 read sites.** For GL calls wrap in `float(...)` |
| `v.dot(w)` → float | `v.dot(w).scalar_part()` | gacalc `dot`/`inner_product` returns a **multivector**, not a float |
| `v * w` (not used on vectors in mvp) | returns a **Rotor** (geometric product) | gotcha if anyone multiplies two vectors |
| `v.cross(w)` | `(v ^ w).dual()` (𝒢₃: dual of the bivector) | **verify sign** against the existing `find_normal` CCW tests |
| `abs(v)` | `abs(v)` (→ `magnitude()`, a sympy expr) | wrap `float(...)` at GL boundaries |
| `v.isclose(w)` | `v.is_close(w)` | underscore spelling |
| `glVertex3f(*v)` / `list(v)` | **BREAKS** — gacalc `__iter__` yields per-blade *multivectors*, not scalar components | replace with explicit `float(v.coeff_e_1), float(v.coeff_e_2), float(v.coeff_e_3)` |
| `Vector` (type annotation) | `AbstractMultiVector` (`from gacalc.base import AbstractMultiVector`) | |
| `Vector1D` | `gacalc.g1.Vector1` (or `G1`) | |

## Phases

### Phase G — upstream the animation layer to gacalc (gacalc repo, blocks everything)
Port mvp's `InvertibleFunction.at()` / `.steps()` + the `interpolate`/`components`
fields into a **new module** under `gacalc` (e.g. `src/gacalc/animation.py`).
Required pieces, lifted from mvp `mathutils.py`:
- the optional `interpolate: Callable[[float], InvertibleFunction]` and
  `components: list[InvertibleFunction]` fields on `InvertibleFunction`;
- `at(t)` three-tier resolution (stored law → recurse into components → step) and
  `steps()` leaf-flattening;
- factories attach laws: `translate(b*t)`, `uniform_scale(1+(m-1)t)`,
  `scale_non_uniform(...)`, and `compose(...)` must store `components=` (gacalc's
  `compose` currently does **not**);
- **the hard part:** `inverse()` must make *inverse commute with at* at every `t`
  (reverse+invert components, invert the interpolate law). Port mvp's logic and
  the guard test `test_inverse_commutes_with_at_for_compose_and_primitive`.
- Decide module boundary with Bill (new file housing an enriched
  `InvertibleFunction`, vs. enriching `transforms.py` and putting only `at`/`steps`
  helpers in the new module). Bill owns gacalc's architecture — confirm before
  building. **Then release gacalc to PyPI.**

### Phase 0 — wire the dependency + façade (mvp)
- Add `gacalc>=<release-from-Phase-G>` to `requirements.txt`.
- Turn `mathutils.py` into a façade: re-export `InvertibleFunction, inverse,
  compose, identity, compose_intermediate_fns, compose_intermediate_fns_and_fn,
  translate, uniform_scale, scale_non_uniform` from `gacalc.transforms`, and
  `Vector1/Vector2/Vector3` (aliased as needed) from `gacalc.g1/g2/g3`.
- Keep `__all__` stable where possible so demo import lines survive.

### Phase 1 — rebuild graphics-only math in mvp on top of gacalc
Reimplement, in mvp, against gacalc vectors + gacalc `InvertibleFunction`:
- **Rotations:** `rotate(θ)`, `rotate_90_degrees`, `rotate_around`, `rotate_x/y/z`
  — each builds a gacalc `InvertibleFunction` and attaches its own interpolation
  law (`interpolate=lambda t: rotate_x(angle*t)`), exactly as today.
- **Projections:** `ortho`, `perspective`, `cs_to_ndc_space_fn` — port verbatim;
  they already compose `scale_non_uniform`/`translate`, now from gacalc.
- **Plane geometry:** `find_normal` (`(p2-p1) ∧ (p3-p1)` then `.dual()`),
  `plane_equation`, `distance_to_plane`. Keep the existing CCW-winding tests as
  the oracle; verify the wedge+dual sign matches.
- **Predicates:** `sine`, `cosine`, `is_counter_clockwise`, `is_clockwise`,
  `is_parallel`, `abs_sin` — straightforward on gacalc vectors (remember `dot`
  returns a multivector → `.scalar_part()`).
- Preserve every `# doc-region-begin/-end` marker name on the functions that the
  book slices (see Phase 4) so the relocated source still feeds the book.

### Phase 2 — migrate the call sites (the bulk of the work)
Rewrite vector construction / attribute access / iteration across the audited
surface using the cheat-sheet above. Order by risk, lowest first:
- **Ports (13 files) — in scope (Path Y).** Easiest conversion to do first: they
  use only `Vector3D` + `find_normal`/`plane_equation`, mostly positional ctor +
  `.x/.y/.z` reads, no transform/stack/animation. Good place to validate the
  gacalc vector idioms before the harder demo/visualization edits.
- **util** — `nbplotutils.py` (`sine`/`cosine`) migrates. `shading.py` uses
  `find_normal`; check whether it's curriculum (demo22 lighting) or shared with
  ports — if curriculum-only it can move to gacalc-backed vectors, otherwise it
  stays on the compat surface.
- **2D demos (demo05–13)**, then **3D demos (demo14–18)** — vectors, transforms,
  `fn_stack`, `ortho`/`perspective`.
- **Visualizations (9 files)** — `rotate_x/y/z`, `translate`, `compose`,
  `inverse`; this is also the **only** place that uses the animation layer
  (`.at()`/`.steps()`), so it's the real-world test of Phase G.
- **notebooksrc (`plot2d.py`, `ndc.py`, `framebuffer.py`)**, **assignment
  `demo02/vec1.py`**.
- **tests (`test_mathutils.py`, `test_cayley_graph.py`, `test_cayley_scene.py`)**
  — `test_mathutils.py` shrinks dramatically (vector-arithmetic and
  transform-core tests now belong to gacalc); keep only tests for the math that
  still lives in mvp (rotations, projections, plane geometry, predicates, stack).
  Watch `.isclose` → `.is_close`.

### Phase 3 — function stack (stays, minimal change)
`FunctionStack` / `fn_stack` / `push_transformation` remain in mvp.
`modelspace_to_ndc_fn` calls `compose(self.stack)` — now gacalc's `compose`.
Verify the `test_vec3_fn_stack` push/pop sequence still passes against gacalc
`InvertibleFunction`.

### Phase 4 — the book (HIGHEST RISK — needs a Bill decision before Phase 2)
11 `.rst` chapters `literalinclude` ~27 `doc-region` slices from `mathutils.py`
and `test_mathutils.py`. Splitting into two cases:
- **Slices of math that STAYS in mvp** (ch07 rotate, ch08 rotate_around, ch14
  rotate_x/y/z, ch16 function stack, ch17 ortho + cs_to_ndc, ch18 perspective):
  keep working **iff** we preserve the `doc-region` marker names in the relocated
  mvp source. Mechanical.
- **Slices of the deleted vector type + core transforms** (ch05 `Vector2D` class +
  basis; ch06 add/sub/mul/`translate`/`InvertibleFunction`/`inverse`/uniform_scale;
  ch14 `Vector3D` class + basis; ch06 `translate test` + ch16 `function stack
  examples` from `test_mathutils.py`): the source these point at is deleted.
  **DECIDED (2026-06-07): rewrite these chapters to teach gacalc vectors as THE
  vector type** — `Vector2`/`Vector3`, `e_1` class-constants, `component()`,
  scaled-sum construction — rather than the old named-field `Vector2D`/`Vector3D`.
  This is the honest end-state (book code = demo code) and the largest single doc
  effort. It re-opens the natural-basis material just landed in
  `archive/book-explain-natural-basis.md` (ch05 2D / ch14 3D), so re-do that
  pedagogy in gacalc terms. New `literalinclude` targets: prose-authored snippets
  or, where a slice is still wanted, gacalc-backed mvp helper source — **not** the
  generated `coeff_e_*` gacalc files. Coordinate with the three
  `book-code-drift-*` trackers; this supersedes their vector-class findings.

This phase interacts with two existing trackers — `book-code-drift-ch1-6.md`,
`book-code-drift-ch7-15.md`, `book-code-drift-ch16-21.md` — and the
`archive/book-explain-natural-basis.md` work that just introduced `e_1/e_2/e_3`
in ch05/ch14. A type switch re-opens exactly that material.

## Decisions

**RESOLVED 2026-06-07:**
0. **Ports → Path Y.** Rebuild `find_normal`/`plane_equation` on gacalc and edit
   the 13 ports to gacalc idioms. No compat type kept.
1. **Book → rewrite chapters on gacalc.** ch05/06/14 (+ the two `test_mathutils`
   slices) are rewritten to teach gacalc vectors as the vector type.
2. **Raw gacalc, no convenience subclass** (implied by 0+1). Curriculum + ports
   both use raw gacalc idiom (`Vector3.e_1`, `v.coeff_e_1`,
   `v.dot(w).scalar_part()`, `float(v.coeff_e_1)` at GL calls). *Allowed:* small
   **stateless** ergonomic free-functions (e.g. a `gl3f(v)` returning the three
   floats) — these don't reintroduce a vector *type*, so they're fine if they cut
   GL-boundary noise. A `Vector3D` subclass restoring `.x`/`e_1()`/keyword-ctor is
   **out**.

**STILL OPEN (non-blocking for mvp; gacalc-side):**
3. **Phase G module shape** — new `gacalc/animation.py` housing an enriched
   `InvertibleFunction`, vs. enriching `transforms.py`. gacalc-architect call;
   tracked in `/geometricalgebra/tasks/port-animation-layer-from-mvp.md`.

**Informational:**
4. **`scale_non_uniform` protocol** — gacalc's version uses
   `cls.project(onto=cls.basis_vector(i))` (full multivector protocol); fine for
   gacalc vectors, and the reason the old named-field `Vector2D` couldn't have
   used it.

## Verification

- `python -m pytest -q` green (mvp tests, post-migration shape).
- gacalc side: its own suite + the ported `at/steps/inverse-commutes` tests green,
  **and a PyPI release cut**, before mvp pins it.
- Each converted demo still **imports and constructs its scene without error**
  (Bill runs anything needing a GL display — I can't run graphical/GL here).
- Book: `doc-region` markers resolve for all *retained* slices; the
  deleted-vector slices handled per decision #1. (PDF/EPUB build is
  blocked-on-Bill — no doc-build toolchain in this container.)
- Grep gates (curriculum only — **excluding `ports/`**): no remaining `from
  modelviewprojection.mathutils import (… Vector2D …)` once the curriculum type is
  gone; no `.x`/`.y`/`.z` on gacalc vectors; no `glVertex*f(*v)` splat on a gacalc
  vector. The parked ports legitimately keep `Vector3D` + `.x/.y/.z` against the
  compat surface — they are exempt from these gates.

## Blast-radius reference (from the rewrite-surface audit)

**~56 files in scope** (Path Y, everything migrates): 14 demos (demo05–18) · 9
visualizations · 2 util · 3 tests · 3 notebooksrc · 1 assignment · **13 ports** ·
11 book `.rst` (~27 doc-region slices, ch05/06/14 rewritten on gacalc).
`.x/.y/.z` read ~126×; `Vector2D`/`Vector3D` in ~30 files; `rotate_x/y/z` in 22;
`ortho`/`perspective` in 24. Animation layer (`.at`/`.steps`) used **only** in
`mvpvisualization/` (+ `notebooksrc/plot2d.py`). Ports use **only** the plane
geometry helpers — no transform/stack/animation surface.
```
demos:          demo05–demo18  (+ demo19a–e fixed-function 3D)
visualizations: cayleygraph, cayleyscene, coordinatesystems, model,
                modelview, modelview2d, modelvieworthoprojection,
                modelviewperspectiveprojection, pushmatrix
util:           shading.py (find_normal), nbplotutils.py (sine/cosine)
ports:          chapt01 block; chapt05 litjet/shinyjet/shadow/sphereworld;
                chapt06 fogged/multisample/sphereworld; chapt08 pyramid/
                sphereworld; chapt09/11 sphereworld; chapt19 SphereWorld32
book:           ch05, ch06, ch07, ch08, ch14, ch16, ch17, ch18, mathhomework1
```
```
```
