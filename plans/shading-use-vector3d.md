# Plan: refactor shading helpers to use Vector3D / mathutils

**Status:** Finding 1 **DONE** (2026-05-27, staged) — `_face_normal` now calls
`mathutils.find_normal` and normalizes; verified bit-equivalent to the old inline
formula (max abs diff 2.2e-16 over 200+ triangles incl. degenerate); tuple return
kept so callers are unchanged; `ruff`/`py_compile`/`pytest` green. Finding 2
(`light_dir_ws` return type) = **recommend leave as a tuple (no change)** — awaiting
Bill's confirmation. **Type:** refactor of `src/modelviewprojection/shading.py`.

## Context
`shading.py` currently does its vector math with bare tuples and inline
arithmetic. The course is built around `mathutils.Vector3D` and its operators, and
`mathutils` **already has the exact function `_face_normal` reimplements** —
`find_normal`. Aligning the shading helpers with the abstraction both removes a
duplicate of mathutils and makes the demo read in the course's own vocabulary.

## Finding 1 — `_face_normal` duplicates `mathutils.find_normal` (refactor: yes)
- `_face_normal(a,b,c)` computes `n = (b-a) × (c-a)`, normalizes, returns a tuple.
- `mathutils.find_normal(p1,p2,p3)` returns `(p2-p1).cross(p3-p1)` — **identical
  formula, identical CCW winding** (verified: both give `(0,0,1)` for the xy
  triangle; no sign flip). The only difference is `find_normal` is **not**
  normalized (its length = 2·triangle-area, by design).
- `Vector3D` supports everything needed: `__iter__` (`tuple(v)`/`*v`/unpacking),
  `__abs__` (magnitude), `cross`, `__sub__`, `__rmul__`. Verified live.

**Change (keeps the tuple return → zero caller churn):**
```python
from modelviewprojection.mathutils import Vector3D, find_normal

def _face_normal(a, b, c) -> tuple[float, float, float]:
    """Outward unit normal of triangle (a, b, c), CCW-wound.
    Cross-product + normalize, via mathutils.find_normal."""
    n = find_normal(Vector3D(*a), Vector3D(*b), Vector3D(*c))
    mag = abs(n)
    return tuple((1.0 / mag) * n) if mag else (0.0, 0.0, 0.0)
```
- Inputs `a,b,c` arrive as plain tuples (mesh data / `corners[i]`), so wrap with
  `Vector3D(*a)`. Output stays a tuple, so `demo22a`/`demo23` call sites
  (`_face_normal(corners[...], ...)`, `n = _face_normal(a,b,c)`) are unchanged.
- The `or 1.0` degenerate guard is preserved by the `if mag else (0,0,0)` branch
  (same behavior: a zero-area triangle yields `(0,0,0)`).

## Finding 2 — `light_dir_ws` (refactor: optional / cosmetic)
`light_dir_ws(az,el)` just builds a direction from spherical coords (pure trig);
there's no mathutils op to dedup, so the only change available is the *return
type*. It could return `Vector3D(...)` for consistency, **but** the three callers
consume it by **indexing** — `light_dir[0]/[1]/[2]` (demo22:757, demo22a:592-594,
demo23:511-513) — and `Vector3D` has **no `__getitem__`**. `GL.glUniform3f(u, *light_dir)`
would still work (uses `__iter__`), but the indexed sites would break.

Options (pick with Bill):
- **(A) Leave as a tuple** — recommended; it's a constructor, not vector algebra,
  and the GL boundary wants tuples/floats anyway. Lowest value to change.
- **(B) Return `Vector3D`, update the 3 callers** — change `light_dir[i]` to
  `.x/.y/.z` (or unpack), e.g. demo22:757 `(*light_dir, 0.0)`. Pure consistency
  win; touches callers.
- **(C) Add `__getitem__` to `Vector3D`** — a mathutils-wide API change. The
  course deliberately avoids treating Vectors as index-able arrays, so **not
  recommended**.

## Out of scope but noticed (related)
- `demo22`'s planar-shadow path (`FLOOR_PLANE`, line 755-757) could use
  `mathutils.plane_equation` / `distance_to_plane` — but that belongs with
  `plans/planar-shadow-matrix.md`, not here.
- `set_mvp_uniforms` extraction is still deferred (variant question).

## Recommendation
Do Finding 1 (clear win: dedups mathutils, uses Vector3D, no caller churn). Treat
Finding 2 as option (A) unless Bill wants the consistency of (B).

## Verification
- `cd /mvp && PYTHONPATH=src python3 -c "from modelviewprojection.shading import _face_normal; print(_face_normal((0,0,0),(1,0,0),(0,1,0)), _face_normal((0,0,0),(0,0,0),(0,0,0)))"`
  → expect `(0.0, 0.0, 1.0)` and `(0.0, 0.0, 0.0)` (matches pre-refactor output).
- Compare against the current tuple implementation on the real jet/cube faces
  (assert equality within 1e-9) before committing.
- `ruff check` + `py_compile` on `shading.py` and any touched demo; `pytest` 46/46.
- GL render check (visual) → Bill, since normals feed lighting/culling.
</content>
