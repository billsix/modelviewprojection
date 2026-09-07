# CtC `_identity()` cleanup — remove the dead copies, and consider routing the live ones through gacalc

**Status:** DONE 2026-09-07 (both parts; staged for the maintainer)
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

**Done 2026-09-07.** Codemod `tasks/adhoc/ctc-identity-cleanup/apply.py` removed the
four copies (−5 lines each; idempotent — proven by a second no-op run). `make format`
(ruff + ty) clean and ruff left all files unchanged (correct spacing). Frame gates
green: boing / cavern / myriapod / kinetix all `PASS (frame 180 byte-identical, AE=0)`.
Staged for the maintainer. (Owed follow-up per the stage-don't-commit rule: the one-shot
codemod is `git rm`'d only after the commit that carries it lands — do it when Part B
resolves and this task archives, or sooner once Part A's commit exists.)

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

Use the **same wrapper the games already use for `ortho_pixels`** —
`np.asarray(to_matrix(...), dtype=np.float32)` — so the shape mirrors the
existing code exactly and ty is satisfied (`to_matrix` is annotated
`np.ndarray | sympy.Matrix`; the `np.asarray(..., dtype=np.float32)` pins it to
`NDArray[np.float32]`):

```python
_IDENTITY: NDArray[np.float32] = np.asarray(
    to_matrix(identity(), g3.Vector), dtype=np.float32
)
```

**No dtype hazard (earlier note corrected 2026-09-07).** gacalc's
`to_matrix(backend="numpy")` and `MatrixTemplate.fill()` already return
`np.float32` — the games upload gacalc-built `MODEL`/`ortho` straight into
`glUniformMatrix4fv` today. Identity's entries (0.0, 1.0) are exact in float32,
so `to_matrix(identity(), g3.Vector)` is **bit-identical** to `np.identity(4,
dtype=np.float32)`; the `np.asarray(..., dtype=np.float32)` is a no-op copy kept
only for the annotation and to match `ortho_pixels`. There is no float64 in the
path (matrices *must* be float32: the `model` uniform is a GLSL `mat4`, set via
the float variant `glUniformMatrix4fv`, which reads `GLfloat` — ints/float64 do
not apply).

**One real thing to keep in mind:** a module-level `_IDENTITY` constant is shared
across all call sites (the old `_identity()` allocated a fresh array each call).
That is fine because every use is a read-only upload — no caller mutates it.

**Verification:** same gates as Part A across all six games — frame gate AE=0
(identity is identity, so bit-identical output expected).

**Done 2026-09-07** (maintainer chose consistency: "the identity function exists
and the machinery to turn it into a matrix at module load time exists — use
it"). Codemod `tasks/adhoc/ctc-identity-cleanup/route_identity_through_gacalc.py`
did all six: `identity` added to the `gacalc.transforms` import (isort position,
after `compose`), `def _identity()` replaced by the module-level `_IDENTITY`
constant, call sites rewritten (bunner/soccer/avenger/eggzy/leadingedge 1 each,
beatstreets 3). Idempotent (second run no-op). `make format` clean (ty accepts
the import and the `NDArray[np.float32]` assignment via the `np.asarray` wrapper;
ruff left files unchanged). Frame gates: all six `PASS ... AE=0`. Net result:
`_identity` is gone from all ten games — the four dead copies deleted (Part A),
the six live ones now build the identity through gacalc like `MODEL`/`ortho`.

**Owed follow-up (stage-don't-commit ordering):** the two one-shot codemods
(`apply.py`, `route_identity_through_gacalc.py`) are `git rm`'d only *after* the
commit that carries them lands — do it once the maintainer commits this work.

## Related

- `tasks/reference/gacalc-transforms-in-the-renderer.md` — the transform layer.
- `tasks/archive/2026/09/06/ctc-use-gacalc-matrix-template.md` — the prior pass
  that moved `MODEL` to gacalc's `to_matrix_template`.
