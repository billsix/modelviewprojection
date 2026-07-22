# Simplify `find_normal`'s dual coefficient reads once gacalc `dual()` types precisely

**Status:** proposed — **GATED** on gacalc shipping precise `dual()` typing **and** a release +
mvp pin bump (see Gating). Created 2026-07-22. Follow-on to
`tasks/precise-product-types-coefficient-cleanup.md` (the one site that task had to leave alone).

## Context

`src/modelviewprojection/mathutils.py` `find_normal` computes a triangle normal via the dual of the
edge wedge:

```python
bivector = (p2 - p1) ^ (p3 - p1)   # Bivector3 (after the 0.0.12 wedge-overload cleanup)
n = bivector.dual()                # a Vector3 at runtime, but gacalc types it Bivector3 (Self) today
return Vector3(
    coeff_e_1=float(n.coefficient(Vector3.e_1)),
    coeff_e_2=float(n.coefficient(Vector3.e_2)),
    coeff_e_3=float(n.coefficient(Vector3.e_3)),
)
```

`n` is genuinely a `Vector3` (in 𝒢₃ the dual of a bivector is a vector), but gacalc currently
declares `Bivector3.dual() -> Self` (an unsound `cast`), so the checker sees a `Bivector3` — which
has no `coeff_e_1`/`e_2`/`e_3` fields, forcing the base `.coefficient(...)` reader.

## The change (once unblocked)

With `Bivector3.dual() -> Vector3` (gacalc `tasks/precise-dual-typing.md`), `n` types as `Vector3`
and the reads become direct fields — and the whole tail likely collapses:

```python
bivector: Bivector3 = (p2 - p1) ^ (p3 - p1)
n: Vector3 = bivector.dual()
return Vector3(coeff_e_1=float(n.coeff_e_1), coeff_e_2=float(n.coeff_e_2),
               coeff_e_3=float(n.coeff_e_3))
```

(Consider whether `return Vector3(*(float(c) for c in n))` — using gacalc's coordinate iteration —
is cleaner; decide at implementation.) Cosmetic/robustness only; runtime is unchanged.

Re-scan for any other `.coefficient()` reads sitting on a `dual()` result at that point.

## Gating (why "later")

1. **gacalc must ship precise `dual()`** — `tasks/precise-dual-typing.md` in
   `github.com/billsix/geometricalgebra`.
2. **gacalc must release it** (bump to 0.0.13, `make release` → **PyPI** + GitHub). mvp consumes
   gacalc only from PyPI: the `gacalc==` wheel in `requirements.txt` and the sdist the `Dockerfile`
   `ARG GACALC_VERSION` fetches from the PyPI JSON API.
3. **mvp bumps the pin** `gacalc==0.0.12 → 0.0.13` in `requirements.txt` **and** `Dockerfile`
   `ARG GACALC_VERSION` (they must match).

## Verify

After the pin bump: apply the edit, `make format` (the `ty` gate) stays green, `make html` still
builds, and the `find_normal` doctests still pass. Confirm `bivector.dual().coeff_e_1` type-checks
(i.e. the released gacalc really types `dual()` precisely).

## Relationships

- gacalc `tasks/precise-dual-typing.md` (the upstream typing change + its release step).
- `tasks/precise-product-types-coefficient-cleanup.md` (this is its deferred residual).
