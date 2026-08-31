# Use gacalc's cross product everywhere (bump to gacalc 0.0.18)

**Status:** blocked
**Priority:** 3
**Difficulty:** 4
**Created:** 2026-08-31
**Blocked on:** gacalc 0.0.18 published to PyPI (the release carrying
`gacalc.vectorcalc.cross` and the generated `g3.Vector.cross`; see gacalc's
`tasks/release-0.0.18.md` in github.com/billsix/geometricalgebra).
**Recheck:** WebFetch `https://pypi.org/pypi/gacalc/json` and look for `"0.0.18"`
in `releases` — present means cleared (compare versions with a version-aware sort).

## BLUF

Bump the pin `gacalc==0.0.16` → `==0.0.18` and route **every** cross product in
this repo through gacalc — the maintainer's explicit decision (William Emerison Six
<billsix@gmail.com>, 2026-08-31: "anything in mvp should use the cross product from
gacalc"), including the three `np.cross` (numpy's array cross product) call sites,
not just the gacalc-typed code. Done means: no `np.cross` remains, `find_normal`
reads as a named cross product, and the full mvp container gate is green.

## Context

- gacalc 0.0.18 adds: `gacalc.vectorcalc.cross(a, b)` (free function, 3-D vectors),
  `MultiVectorBase.cross(other)` (method form), and a **generated closed-form
  `g3.Vector.cross` typed `Vector -> Vector`** — so ty-gated mvp code needs no
  casts. Sign convention is the standard right-handed one (`e₁ × e₂ = e₃`),
  pinned by gacalc's tests.
- The pin jump crosses **0.0.17**, whose breaking items (gacalc `CHANGELOG.md`)
  are: `exp()` of a *vector* now raises, and the generated `dual(n)` is
  dimension-locked (raises on `n != DIMENSION`). Expected impact here: none —
  `mathutils.find_normal` already calls `dual()` with the default — but grep for
  `.exp(` and `.dual(` with arguments during the bump to confirm.

## Work list

1. **Pin bump:** `requirements.txt` `gacalc==0.0.16` → `gacalc==0.0.18`; rebuild
   the image (`make image` — deps bake at image build), then the full gate.
2. **`src/modelviewprojection/mathutils.py` — `find_normal`:** body
   `((p2 - p1) ^ (p3 - p1)).dual()` → `(p2 - p1).cross(p3 - p1)` (the generated
   method; types `g3.Vector` on the nose). Keep the dual-of-the-wedge teaching
   docstring — it now *names* the operation gacalc implements — and check the
   surrounding doc-region markers still slice sensibly for the book.
3. **The three `np.cross` sites** (per the maintainer's all-of-mvp decision; both
   are float32 numpy pipelines, so each needs array↔`Vector` shims — build the
   `g3.Vector` from the array components, `cross`, then read coefficients back
   via `list(v)`/`v.coefficient(...)`):
   - `src/modelviewprojection/demos/demo22/demo22.py:642` (`_light_proj_view`,
     the light-space lookAt basis: `s = np.cross(f, upn)`);
   - `src/modelviewprojection/mvpvisualization/_pipeline.py:677` and `:679`
     (cylinder-mesh frame: `right = np.cross(forward_unit, ref)`,
     `up = np.cross(forward_unit, right)`).
   Caveat, inline where it matters: `_pipeline.py` runs per edge per slice — if
   the demo's interactivity visibly degrades, report the measured cost rather
   than silently keeping numpy (the decision to convert is made; the caveat is
   about *surfacing* any cost, not skipping).
4. **Verify:** mvp's containerized gate (`make test` / format+ty), plus running
   demo22 and an mvpvisualization demo headless (Xvfb + screenshot — verify
   pixels, not exit codes) since 3 touches rendering paths.

## Open questions

None at creation — the scope decisions above are the maintainer's, recorded in
BLUF/work list.
