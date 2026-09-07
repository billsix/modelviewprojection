# CtC `_identity()` cleanup — remove the dead copies, and consider routing the live ones through gacalc

**Status:** Part A in progress (approved); Part B proposed — needs go-ahead
**Priority:** 5
**Difficulty:** 2

## BLUF

A dead-code sweep of the ten Code the Classics ports (2026-09-07) found one
unused private helper: `_identity()` (raw `np.identity(4, dtype=np.float32)`)
is defined but never called in **four** games (`boing`, `cavern`, `myriapod`,
`kinetix`). **Part A (approved):** delete those four dead copies. **Part B
(proposed):** the **six** games that *do* call `_identity()` build the identity
model matrix with raw numpy rather than through gacalc's `to_matrix(identity(),
g3.Vector)` — inconsistent with how each game already builds `MODEL` and
`ortho`. Decide whether to route them through gacalc too.

## Context

- **Read first:** `tasks/reference/gacalc-transforms-in-the-renderer.md` (how
  `MODEL` / `ortho` are built from gacalc), and any one game, e.g.
  `ports/codetheclassics/vol1/bunner/bunner.py` (imports at the top; `_identity`
  helper; the `glUniformMatrix4fv(self.uniforms.model, ...)` call sites).
- **How the sweep was done:** an `ast`-based unused-private-symbol finder over
  all ten games (functions, methods, module-level `_CONST`), plus the library
  modules (`mathutils`, `matrix_stack`, `wxapp`, `wxapp2`) as one cross-file
  universe, and `tools/`. Only `_identity` came back dead. `src/…/demos/` (the
  book's teaching exhibits, some pulled into Sphinx via doc-regions, some run by
  wxPython callbacks) was **excluded** — a naive in-file-ref check false-positives
  on pedagogical code there; a doc-region/callback-aware sweep of the demos is a
  separate, higher-care job if wanted.
- **The helper, identical in every game it appears in:**
  ```python
  def _identity() -> NDArray[np.float32]:
      """Return a 4x4 identity matrix."""
      return np.identity(4, dtype=np.float32)
  ```
- **Why four are dead and six are live:** the six live games call `_identity()`
  to set the model uniform to identity for a background / full-screen draw; the
  four dead games draw everything through their `MODEL` template and never need
  an identity model matrix. So the dead copies are leftover copy-paste, **not** a
  missing call — confirmed each dead copy appears exactly once (the def only, no
  string / `getattr` use), so removal cannot change the render.

## Part A — remove the four dead `_identity()` copies (APPROVED)

| File | Line of `def _identity` |
|---|---|
| `ports/codetheclassics/vol1/boing/boing.py` | 530 |
| `ports/codetheclassics/vol1/cavern/cavern.py` | 528 |
| `ports/codetheclassics/vol1/myriapod/myriapod.py` | 533 |
| `ports/codetheclassics/vol2/kinetix/kinetix.py` | 635 |

Delete the 3-line def (plus its surrounding blank line) in each. `np` /
`NDArray` remain used elsewhere in all four files, so no import is orphaned —
let `make format` (ruff + ty) confirm. A small idempotent codemod under
`tasks/adhoc/ctc-identity-cleanup/` performs it, as the audit trail.

**Verification:** `make format` clean; `make test`; the frame gate for the four
games (`tools/ctc_verify_game.sh`) — must stay AE=0 (the deleted function is
uncalled, so the render cannot change).

## Part B — route the six live `_identity()` through gacalc? (PROPOSED)

The six games (`bunner`, `soccer`, `avenger`, `beatstreets` — 3 call sites —,
`eggzy`, `leadingedge`) already import `to_matrix` and build `MODEL` /`ortho`
from gacalc, but the identity model matrix still uses the raw numpy helper. For
consistency it could be a module-level constant built once through gacalc, the
same way the other matrices are:

```python
from gacalc.transforms import identity, to_matrix   # add `identity` to the import
_IDENTITY: NDArray[np.float32] = to_matrix(identity(), g3.Vector).astype(np.float32)
# ... then at the call site:
GL.glUniformMatrix4fv(self.uniforms.model, 1, GL.GL_TRUE, _IDENTITY)
```

**Risks / things to verify before doing this:**

- **dtype + contiguity.** `to_matrix(..., backend="numpy")` returns an
  `np.ndarray` whose dtype is likely float64; `glUniformMatrix4fv` needs a
  contiguous float32. Keep the `.astype(np.float32)` (and confirm C-contiguity)
  or the swap is not byte-identical to `np.identity(4, dtype=np.float32)`.
- **Transpose convention.** The call passes `GL_TRUE` (transpose); identity is
  symmetric so transpose is a no-op here, but confirm nothing else assumes the
  helper returns a fresh array per call (it currently allocates each call; a
  shared module constant is fine only if no caller mutates it — none should).
- **Is it worth it?** This is a taste/consistency call, not a bug. The counter-
  argument: `np.identity(4)` is clearer and cheaper than routing a trivial
  identity through the GA machinery. Decide before implementing.

**Verification if approved:** same gates as Part A across all six games —
frame gate AE=0 (identity is identity, so bit-identical output expected).

## Related

- `tasks/reference/gacalc-transforms-in-the-renderer.md` — the transform layer.
- `tasks/archive/2026/09/06/ctc-use-gacalc-matrix-template.md` — the prior pass
  that moved `MODEL` to gacalc's `to_matrix_template`.
