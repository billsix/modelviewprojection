# Migrate mvp math onto gacalc (delete overlapping math, import gacalc vectors)

**Status:** proposed — needs go-ahead
**Started:** 2026-06-07
**Owner decisions pending:** see "Open decisions for Bill" — do not start coding until these are answered.

## Goal

Stop maintaining mvp's home-grown vector algebra and transform layer. Depend on
the published **`gacalc`** package (PyPI) for everything that overlaps, **delete
the duplicated code from `mathutils.py`**, and rebuild only the genuinely
graphics-specific math *on top of* gacalc. The MVP vector representation
(`Vector`/`Vector1D`/`Vector2D`/`Vector3D`) is **deleted** — demos use gacalc's
multivector vectors (`G1`/`Vector1`, `G2`/`Vector2`, `G3`/`Vector3`) instead.

This is "Option B" from the investigation: switch the vector *type*, not just
import a few helpers. It is the larger change but removes the most duplication.

## Hard constraint: the ports are parked — DO NOT touch them

The 13 SuperBible ports under `ports/openglsuperbiblev4/` are parked (don't edit).
But they **do** use mvp math: each imports `Vector3D` plus `find_normal` /
`plane_equation` from `modelviewprojection.mathutils`, and they rely on exactly
the named-field API gacalc lacks — **positional** construction `Vector3D(0.0,
-25.0, 0.0)` and `.x`/`.y`/`.z` reads (`GL.glNormal3f(n.x, n.y, n.z)`,
`glVertex3f(p1.x, p1.y, p1.z)`). A bare `Vector3D = Vector3` alias keeps the
import line valid but **breaks them at runtime**.

**Therefore the migration must preserve a backward-compatible surface** — the
named-field `Vector3D` (positional ctor + `.x/.y/.z` + `.cross`), `find_normal`,
`plane_equation`, `distance_to_plane` — kept in mvp **as-is, for the ports**, so
those 13 files keep running with **zero edits**. "Delete the vector
representation" applies to the **curriculum** side (demos / book / visualizations
/ tests), which moves to raw gacalc; a thin compat layer lives on for the parked
ports until they're un-parked and modernized in a separate, later task. The port
files (chapt01 block; chapt05 litjet/shinyjet/shadow/sphereworld; chapt06
fogged/multisample/sphereworld; chapt08 pyramid/sphereworld; chapt09/11
sphereworld; chapt19 SphereWorld32) are **out of scope** here.

## Decision: what moves where

| mvp `mathutils` symbol(s) | Disposition |
|---|---|
| `Vector`, `Vector1D`, `Vector2D`, `Vector3D` | **DELETE from the curriculum** → use gacalc `AbstractMultiVector` / `Vector1` / `Vector2` / `Vector3`. **Exception:** a named-field `Vector3D` compat type stays for the parked ports (see "Hard constraint" above) |
| `InvertibleFunction`, `inverse`, `compose`, `identity`, `compose_intermediate_fns`, `compose_intermediate_fns_and_fn`, `translate`, `uniform_scale`, `scale_non_uniform_2d/3d` | **DELETE** → import from `gacalc.transforms` (`scale_non_uniform_2d/3d` → general `scale_non_uniform(*factors)`) |
| `InvertibleFunction.at()`, `.steps()`, `interpolate`/`components` fields (the animation layer) | **PORT UPSTREAM to gacalc** (new module) — Phase G. mvp then gets it for free via the import. |
| `rotate`, `rotate_90_degrees`, `rotate_around` (angle-based 2D) | **REBUILD in mvp on gacalc** — these were deliberately removed from gacalc (planar-only, e₁e₂ plane) |
| `rotate_x`, `rotate_y`, `rotate_z` (axis rotations) | **REBUILD in mvp on gacalc** |
| `ortho`, `perspective`, `cs_to_ndc_space_fn` | **REBUILD in mvp on gacalc** (graphics-only) |
| `find_normal`, `plane_equation`, `distance_to_plane` | **KEEP AS-IS in mvp** — the parked ports import these and expect named-field `Vector3D` in/out. (A gacalc-backed reimplementation, cross → wedge+dual, is possible later when the ports are modernized — not now.) |
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
- **Ports (13 files) — DO NOT TOUCH.** Out of scope (parked). They keep importing
  the retained compat `Vector3D` + `find_normal` / `plane_equation`; verify they
  still import and run after the curriculum migration, but make **zero edits**.
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
  examples` from `test_mathutils.py`): **these point at source that will no longer
  exist in mvp.** This is the crux decision (below). The book is the product;
  do not break it silently.

This phase interacts with two existing trackers — `book-code-drift-ch1-6.md`,
`book-code-drift-ch7-15.md`, `book-code-drift-ch16-21.md` — and the
`archive/book-explain-natural-basis.md` work that just introduced `e_1/e_2/e_3`
in ch05/ch14. A type switch re-opens exactly that material.

## Open decisions for Bill (blocking)

1. **Book strategy for the deleted-vector slices (Phase 4).** Options:
   (a) re-point those `literalinclude`s at the *installed gacalc source* (fragile:
   site-packages path, gacalc's `coeff_e_*`/generated style won't read like the
   current hand-written pedagogy, and `Vector2/3` are generated files);
   (b) rewrite ch05/06/14 prose+code to teach gacalc vectors as the vector type
   (large doc rewrite, but arguably the honest end state);
   (c) keep a small *teaching-only* vector shim in mvp that the book slices from,
   while demos use raw gacalc (contradicts "delete the representation," but
   preserves the chapters). **This choice gates how much of `mathutils.py` can
   actually be deleted.**
2. **Raw gacalc vs. a thin mvp convenience layer.** You said "delete the
   representation, use gacalc vectors." Confirm you want demos written in raw
   gacalc idiom (`v.coeff_e_1`, `Vector3.e_1`, `v.dot(w).scalar_part()`,
   `float(v.coeff_e_1)` at GL calls) — **not** a `Vector3D` convenience subclass
   that restores `.x`/`.cross()`/`e_1()`/keyword-ctor. The subclass would cut
   Phase 2 churn by a lot and keep book idioms, at the cost of not being "pure"
   gacalc. (Default per your instruction: raw gacalc.)
3. **Phase G module shape** (new `gacalc/animation.py` housing an enriched
   `InvertibleFunction`, vs. enriching `transforms.py`). Your call as gacalc's
   architect.
4. **`scale_non_uniform` protocol gap.** gacalc's `scale_non_uniform` uses
   `cls.project(onto=cls.basis_vector(i))`, which needs the full multivector
   protocol — fine for gacalc vectors (our new world), but confirms why the old
   mvp `Vector2D` couldn't have used it.

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

**~43 files in scope** (curriculum): 14 demos (demo05–18) · 9 visualizations ·
2 util · 3 tests · 3 notebooksrc · 1 assignment · 11 book `.rst` (~27 doc-region
slices). **Plus 13 ports OUT OF SCOPE** (parked; kept running via the compat
surface, zero edits).
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
