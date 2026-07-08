# Task: migrate the Code-the-Classics ports' math to gacalc (as much as reasonable)

**Status:** ACCOMPLISHED (and exceeded) 2026-07-09 — archived. What this
proposed was delivered by the ctc-vector2-deferral →
upgrade-rotation-and-ctc-vector-mapping (gacalc repo) → shim-dynamism-audit
chain: the games use `gacalc.g2.Vector2`/`g3.Vector3` DIRECTLY (the shim
vector types were deleted, not migrated), `Actor.pos` returns a gacalc
vector, kinetix rotates via `plane_rotation`, and gacalc grew the missing
ergonomics (x/y/z properties, quotient `/`) in 0.0.8. The background notes
below predate all of that and are stale.
**Created:** 2026-06-28
**Area:** `ports/codetheclassics/`
**Related:** `tasks/gacalc-math-migration.md` (the mvp-core precedent), `tasks/codetheclassics-types-and-docstrings.md` (just-completed Phase 0/1 typed the shim — do this *after*, on the typed baseline)

## Goal

Replace the ports tree's hand-rolled vector/matrix math with **gacalc** (the
geometric-algebra library mvp core already sits on) **wherever it's reasonable**
— i.e. wherever gacalc can back the math without breaking the two hard
constraints below. The phrase "as much as reasonable" is load-bearing: part of
this task is deciding, per component, whether migration is a net win or a
compatibility liability, and saying so.

## Why

mvp core already did this: `mathutils.py` is a façade over `gacalc.g2.Vector2` /
`gacalc.g3.Vector3` / `gacalc.transforms`, so the whole curriculum speaks one
vector vocabulary (see root `CLAUDE.md`). The Code-the-Classics ports are the
last island of bespoke linear algebra in the repo — a second `Vector2`/`Vector3`
implementation plus a hand-rolled 4×4 matrix stack. Consolidating onto gacalc
(where sensible) means one math library to maintain, test, and teach.

## Background — what gacalc actually offers (measured 2026-06-28)

`from gacalc.g2 import Vector2` / `from gacalc.g3 import Vector3`:
- Coordinates are **`coeff_e_1` / `coeff_e_2` / `coeff_e_3`**, *not* `.x`/`.y`/`.z`.
- `repr` → `Vector2(coeff_e_1=1.0, coeff_e_2=2.0)`. Iterates in `(e_1, e_2[, e_3])`
  order, so `*v` unpacks to the right arity (mvp relies on this for `glVertex*`).
- **Mutable** (dataclass `frozen=False`) — but **`eq=False`**, so there is *no*
  value equality (`a == b` is identity, unlike pygame's value-equal vectors).
- Rich GA API: `dot`, `wedge`/`outer_product`, `magnitude`, `normalize`,
  `project`/`reject`/`reflect`, `rotate`, `sandwich`, `rotor_from_vectors`, …
  Rotation is rotor-based (GA), conceptually radians + a plane — **not** pygame's
  "degrees, screen-space (y-down) counter-clockwise" `Vector2.rotate(deg)`.
- `gacalc.transforms`: `InvertibleFunction` + `translate`/`compose`/
  `scale_non_uniform`/`rotate*` — these operate **on vectors**, they are *not*
  4×4 matrices and don't directly produce a GL uniform.

## The compatibility gap (this is the crux of "reasonable")

The ports' `pgzero_gl/geometry.py` `Vector2`/`Vector3` are **`pygame.math` work-
alikes**, and the games (faithful BSD ports) use that exact surface:
- `.x` / `.y` / `.z` attribute names, read **and written** (`v.x += dx`), plus
  `.normalize_ip()` in-place mutation.
- **Value equality** (`__eq__` compares components) and tuple interop
  (`v + (1, 2)`, `v == (1, 2)`, `v[0]`, `len(v)`).
- `.rotate(degrees)` in **screen-space (y-down) CCW** — a specific sign
  convention the games depend on.
- `.length()`, `.length_squared()`, `.magnitude()`, `.dot()`, `.distance_to()`,
  `.cross()` (3D), `.copy()`.

gacalc's vectors disagree on attribute names, equality semantics, and rotation
convention. So a *drop-in* swap is **not** reasonable — it would break the
unmodified games. The realistic options are about *backing* the shim with gacalc,
not replacing it.

## Inventory of bespoke math in the ports tree

1. **`pgzero_gl/geometry.py`** — `Vector2` (~85 ln), `Vector3` (~75 ln), plus
   `Rect` (no vector math; pure float box — out of scope). The main target.
2. **`pgzero_gl/renderer.py`** — `_identity`/`_translate`/`_scale`/`_rotate_z`/
   `ortho_pixels` as **numpy 4×4 matrices** uploaded to a GL uniform
   (`uModel`/`uOrtho`). An honest-to-goodness GL matrix pipeline.
3. **`pgzero_gl/renderer_gl1.py`** — uses **fixed-function** `glTranslatef`/
   `glRotatef`/`glScalef`/`glOrtho` (no numpy matrices at all). Nothing to migrate.
4. **The 10 game ports** — do their movement/collision math through the shim's
   `Vector2`/`Vector3` and plain floats. `leadingedge` leans on `Vector3` for its
   pseudo-3D road. **Faithful ports → annotations/structure frozen** (see the
   sibling task's constraints); not migration targets.

## Proposed approach (per component, with a reasonableness verdict)

- **`Vector2`/`Vector3` (geometry.py) — REASONABLE, with care.** Keep the
  pygame-compatible class and public surface (so games are untouched), but
  **delegate the numeric core to gacalc internally**: store a `gacalc.g2.Vector2`
  (or keep `x`/`y` floats and build a gacalc vector on demand) and route
  `dot`/`length`/`normalize`/`cross`/`rotate` through gacalc ops. Must preserve
  exactly: `.x`/`.y`/`.z` r/w, value-`__eq__`, tuple interop, in-place
  `normalize_ip`, and the **screen-space degrees** `rotate` sign convention
  (translate degrees→gacalc rotor and verify the direction with a unit test
  against the current implementation). Open question: whether the indirection
  earns its keep for what is mostly 2-float arithmetic, or whether a thinner
  "share gacalc for the non-trivial ops only (rotate/normalize/cross)" is the
  reasonable line.
- **renderer.py 4×4 matrices — PROBABLY NOT reasonable.** gacalc's transform
  layer models `InvertibleFunction`s on vectors, not the 4×4 matrices GL uniforms
  need; mvp's own GL matrix stack is `pyMatrixStack` (separate from gacalc) for
  exactly this reason. Recommend **leaving the numpy GL matrices as-is** unless a
  clean gacalc→matrix bridge exists. Flag for Bill's call; don't force it.
- **renderer_gl1.py / Rect / the games — out of scope** (no numpy math, frozen
  ports, or non-vector code).

## Constraints

- **Don't break the games.** The shim's public vector API must stay
  pygame-compatible (names, equality, rotation convention, mutability, tuple
  interop). The games are faithful BSD ports and are **not** edited here.
- **No behaviour change.** Movement, collisions, and on-screen results must be
  identical. gacalc rotation is rotor/radian-based; the screen-space-degrees
  conversion is the highest-risk spot — pin it with a direct
  old-vs-new comparison test before trusting it.
- **Build on the typed baseline.** Do this after
  `codetheclassics-types-and-docstrings.md` Phase 1 (done) so `ty` guards the
  refactor; keep `ty check /mvp/ports/codetheclassics/pgzero_gl` green throughout.
- **Mind the iteration-order contract.** mvp guards gacalc's `(e_1, e_2, …)`
  unpacking order with `tests/test_gl_vector_unpacking.py`; if the shim starts
  unpacking gacalc vectors, add an equivalent guard here.

## Open questions
- Is the win worth the indirection for 2-/3-float vectors, or is "use gacalc only
  for the genuinely GA-flavoured ops" the reasonable stopping point?
- gacalc's `eq=False` vs pygame value equality: confirm the shim's own `__eq__`
  stays authoritative (don't inherit gacalc identity-equality).
- Should the renderer's GL matrices be considered at all, or explicitly declared
  out of scope (gacalc isn't a 4×4 GL matrix lib)?
- Does gacalc add meaningful import-time/per-op cost in a 60 Hz game loop? (mvp
  core is not frame-timing-sensitive the way a game is — measure before
  committing.)

## Verification
- [ ] Decision recorded per component (migrate / leave) with rationale.
- [ ] `Vector2`/`Vector3` public API unchanged; a test asserts `.rotate(deg)`
      matches the pre-migration output across a sweep of angles (sign convention).
- [ ] `ty check /mvp/ports/codetheclassics/pgzero_gl` green.
- [ ] Each game still launches and plays identically (Bill-verified on-window).
- [ ] Vector iteration-order guard in place if the shim unpacks gacalc vectors.
