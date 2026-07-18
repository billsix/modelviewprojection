# pyMatrixStack — latent bugs and a deprecated NumPy dependency

**Status:** **COMPLETE** 2026-07-18 — bugs 1-5 fixed; 6 (naming) was folded into the
`N` pass in [apply-python-coding-standard](apply-python-coding-standard.md) and is done.
**Created:** 2026-07-18
**Found by:** the first-party source read during
[apply-python-coding-standard](apply-python-coding-standard.md)

`src/modelviewprojection/pyMatrixStack.py` is the book's matrix-stack layer (the
OpenGL-1.x-style `glPushMatrix`/`glMultMatrix` model the chapters teach). It carries
several defects that are latent today only because no caller happens to hit them.

## 1. `get_current_matrix` could silently return `None` — FIXED

**Was:** five `if` branches, no `else`, no final `raise`. Any unhandled `MatrixStack`
member fell off the end returning `None`, while the signature promises `np.ndarray` and
every mutator (`rotate_x`, `rotate_y`, `rotate_z`, `translate`, `scale`, `multiply`)
indexes the result immediately. All five current members are handled, so this was a trap
for the *next* member added, not a live failure.

**Now:** a `match` statement with `case _: raise ValueError(...)`, so the unreachable
branch is loud. Verified in-container that all five members still return a 4x4.

## 2. `set_current_matrix` was a silent no-op for two of its five cases — FIXED

**Was:** `set_current_matrix(MatrixStack.modelview, m)` and
`(...modelviewprojection, m)` did nothing — the branches were literally `pass`, under
`# TODO, figure out how to throw exception, or whatever`. Same shape in `__pushMatrix__`
and `__popMatrix__`.

This is arguably *correct semantics* — `modelview` and `modelviewprojection` are derived
products, not stored stacks, so there is nothing to assign — but it is expressed as a
silent success. A caller writing to a derived stack gets no feedback and no effect.

**Caller audit first (2026-07-18):** every direct and indirect call site passes
`model`, `view`, or `projection` — **zero** pass a derived stack. Counted the indirect
path too (`set_to_identity_matrix` wraps `set_current_matrix` and is called 37 times),
and the `push_matrix` context manager, whose 20 call sites all push `model`. So raising
breaks nothing that exists today.

**Fixed:** `set_current_matrix`, `__pushMatrix__`, and `__popMatrix__` all converted to
`match`, with `case MatrixStack.modelview | MatrixStack.modelviewprojection:` (or-pattern)
raising via a shared `__not_a_stack__` helper, plus a `case _:` for any member added
later. **Reading a derived product still works** — `get_current_matrix` computes it, which
was always the asymmetry: you could read `modelview` but writing it silently did nothing.

Verified in-container: model/view/projection still set/push/pop/restore correctly; the
derived stacks raise on all three operations; `get_current_matrix` on them still returns
a 4x4.

## 3. `np.matrix` is deprecated and pending removal in NumPy — FIXED

`np.matrix` is constructed at `:38`, `:50`, `:62`, `:168`, `:392`, `:424` while every
annotation says `np.ndarray` (`:37`, `:49`, `:61`, `:74`, `:96`), and `:113`/`:117`/`:121`
`typing.cast(np.matrix, np.copy(...))` cast to a type the signatures disclaim.

The subtle one: `multiply` does `m[0:4, 0:4] = np.matmul(m.copy(), rhs)` — in-place
mutation of the stack top via slice assignment, which **behaves differently for
`np.matrix` than for `ndarray`** (`np.matrix` overloads `*` as matmul and keeps
everything 2-D). Migrating to plain `ndarray` is therefore not a pure find-and-replace;
it needs the demos exercised afterward.

**FIXED 2026-07-18.** Migrated to `np.ndarray` throughout; the `typing.cast(np.matrix,
...)` casts are gone and the annotations are now true. `demo22.py`'s
`planar_shadow_matrix` and `demo24.py`'s `np.matrix(shadow_matrix)` were migrated with
it, since they feed `ms.multiply`.

**Verified equivalent by construction, not by inspection:** rather than hand-writing a
reference implementation of the old code (a first attempt at that introduced a sign
error and produced a phantom 14.5-unit "regression"), the pre-migration module was
rebuilt *mechanically* from the current source by reverting the one thing that changed
(`np.array(` -> `np.matrix(`), loaded as a second module, and driven through the same
transform chain. **Max |new - old| = 0.0** across every stack and derived product
(model, view, projection, modelview, modelviewprojection, ortho, and push/pop
isolation). Demos re-run under Xvfb.

## 4. Hardcoded pi — FIXED

Was `math.tan(field_of_view * 3.14159265358979323846 / 360.0)` in a file that already
imports `math`. Now `math.tan(math.radians(field_of_view) / 2.0)` — which also says the
half-angle outright instead of hiding it in a `/ 360`. Verified **bit-identical** for
fov 1..179, and the perspective matrix is unchanged.

## 5. Dead `PushMatrix` class

Two context managers with identical semantics and different capitalization: the class
`PushMatrix` (`:142`) and the `@contextlib.contextmanager` `push_matrix` (`:153`).
`push_matrix` is the one actually used. **FIXED: the class is deleted.** Confirmed
unreferenced in Python first; note `book/docs/ch19.rst:247` mentions "PushMatrix" but is
talking about OpenGL's `glPushMatrix`, not this class, so no prose was orphaned.

Note `PushMatrix.__exit__(self, type, val, tp)` shadows the builtin `type` and names the
traceback `tp`; if the class survives, the params are `exc_type, exc_value, traceback`.

## 6. Naming — deferred to the `N` pass, not this task

The module is the single largest concentration of camelCase in first-party code: the
filename itself, `__modelStack__`/`__viewStack__`/`__projectionStack__` (a fake-dunder
convention that is not Python's), `matrixStack` as a parameter in ~10 functions,
`copyOfM` locals, `__pushMatrix__`/`__popMatrix__`. **18 `N` violations.** Left alone
here so the rename lands as one reviewable commit in
[apply-python-coding-standard](apply-python-coding-standard.md) rather than being
smeared across two tasks.

## Gates

`ruff check src` clean, `ruff format --check` clean, module compiles, and the demos that
use the stack still run. Bug 3 in particular needs a real demo run, not just a lint pass.
