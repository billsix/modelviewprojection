# Simplify coefficient access now that gacalc products type precisely

**Status:** proposed — needs go-ahead. **GATED** on a gacalc release carrying the operator
overloads + bumping mvp's `gacalc==` pin (see below). Created 2026-07-21.

## Context

gacalc's generated graded types now type their **operators** precisely via `@typing.overload`
(gacalc `tasks/.../typed-product-helper-functions.md`, 2026-07-21): `v1 ^ v2 : Bivector2`,
`v1 * v2 : Rotor2`, etc. — instead of the old unsound `-> Self` that mistyped `v1 ^ v2` as
`Vector2`.

Because of that old mistype, mvp reads the wedge's bivector coefficient through the base
`.coefficient(...)` reader — `.coeff_e_12` would have been rejected by the checker on a
`Vector2`-typed value. With precise types, the direct field access is available.

## Sites to simplify (verified 2026-07-21)

- `src/modelviewprojection/mathutils.py:209` — `float((v1 ^ v2).coefficient(Bivector2.e_12))`
  → `float((v1 ^ v2).coeff_e_12)` (the `^` result is now `Bivector2`).
- `src/modelviewprojection/framebuffer/softwarerendering.py:58` and `:84` — same
  `(v1 ^ v2).coefficient(Bivector2.e_12)` → `.coeff_e_12`.
- `src/modelviewprojection/mathutils.py:309` (`find_normal`) —
  `bivector = (p2 - p1) ^ (p3 - p1)` now types as **`Bivector3`** (was silently `Vector3`);
  annotate it `bivector: Bivector3` so the intermediate is honest. (`n = bivector.dual()`
  stays a `.coefficient()` read unless `dual()`'s return is also precise — leave as-is.)

These are cosmetic/robustness cleanups, not correctness fixes — the runtime was always correct
(the reader returns the same value). `.coeff_e_12` is a direct field read (faster, clearer)
and lets the checker verify the grade actually exists.

## Gating (why "later")

1. mvp pins `gacalc==0.0.11` (`requirements.txt`), which **predates the operator overloads**.
   The overloads must first ship in a gacalc release, then mvp bumps the pin (and the
   `ARG GACALC_VERSION` in the Dockerfile, which drives the docs-source copy).
2. Checker: **mvp's gate already runs `ty`** (`entrypoint/format.sh`), which accepts the
   overloads — so the gate is fine. (Interactive pyright-in-emacs is a separate concern; see
   `tasks/switch-typechecker-pyright-to-ty.md`.)

## Verify

After the pin bump: apply the edits, `make format` (the `ty` gate) stays green, and `make html`
still builds. Confirm `(v1 ^ v2).coeff_e_12` type-checks (i.e. the released gacalc really
carries the overloads).
