# Rename `pyMatrixStack` to a pythonic module name

**Status:** **COMPLETE 2026-07-19.** `pyMatrixStack.py` -> `matrix_stack.py` via
`git mv` (history follows). 22 Python references updated across 16 files, plus prose in
`README.md` (1) and `CLAUDE.md` (10). **Both `N813` exemptions deleted from
`pyproject.toml`** -- the whole `mvpvisualization/**` entry and `N813` from `demos/**` --
and `ruff --select N813` is clean, so the suppression is gone at the source rather than
carried. The **last 3 annotations** this was blocking are done: the repo is now at
**0 missing returns and 0 missing params**.

**Two things the plan missed, found while doing it:**
- **The ports referenced it** (`chapt01/block/Block.py`, `chapt05/shadow/shadow.py`) --
  only in comments about a future task, so nothing broke, but they would have gone stale.
  Updated.
- **gacalc referenced it too**: `src/gacalc/transforms.py:499` said "matching mvp's
  ``pyMatrixStack``". A cross-repo doc reference the inventory did not anticipate.
  Updated in gacalc.

**Verified:** 67 tests; `ty check src` at 11 diagnostics (unchanged -- all third-party
stubs); `ruff` clean; all 10 stack consumers render under Xvfb (demos 21/22/22a/23/24 and
mvpvisualization modelview2d/coordinatesystems/pushmatrix/model/modelview). The
module-level-mutable-state risk was checked explicitly: both import forms resolve to **one**
`sys.modules` entry and share state, so there is no double-stack.
**Created:** 2026-07-18
**Requested by:** Bill, 2026-07-18
**Unblocks:** deleting two `N813` exemptions added during the naming pass
(see [apply-python-coding-standard](apply-python-coding-standard.md))

## Why

`src/modelviewprojection/pyMatrixStack.py` is the only camelCase module name in the
first-party tree. It is also the *root cause* of a naming exemption that currently has to
be repeated in two places in `pyproject.toml`:

```
N813  Camelcase `pyMatrixStack` imported as lowercase `ms`
```

Every consumer writes `import modelviewprojection.pyMatrixStack as ms`, and ruff flags
each one — not because `ms` is a bad alias (it is the repo-wide idiom and should stay)
but because the *module* being aliased is camelCase. Rename the module and **all 9+2
N813 violations disappear at the source**, rather than being suppressed.

Note the filename itself is *not* flagged: `N999` (invalid-module-name) passes, because
ruff's default module-name rule tolerates it. So this is a deliberate cleanup, not a
lint failure being worked around.

## Naming

`matrix_stack.py` is the obvious choice — it is what the module is, it matches the
`mathutils.py` / `colorutils.py` neighbours, and it keeps `ms` a sensible alias
(`import modelviewprojection.matrix_stack as ms`).

## Scope (measured 2026-07-18)

| where | refs | note |
|---|---|---|
| `*.py` | 23 refs across 16 files | the real work |
| `book/**/*.rst` | **0** | the book never references it directly — big relief, no `literalinclude` paths to fix |
| `pytest.ini` | 1 | in the doctest allow-list |
| `pyproject.toml` | 3 | the two exemption blocks and their comments |
| `README.md` / `CLAUDE.md` | several | prose |
| `tasks/**` | 80 | historical docs — **leave them alone**, they describe what was true when written |

The zero book references is the important measurement: unlike the demo main-guard work,
this rename does not touch the book build at all.

## Steps

1. `git mv src/modelviewprojection/pyMatrixStack.py src/modelviewprojection/matrix_stack.py`
   — use `git mv` so history follows the file.
2. Update the 23 Python references. They are near-uniformly
   `import modelviewprojection.pyMatrixStack as ms`; the alias `ms` **stays** — it is the
   established idiom and is not what N813 was complaining about.
3. Update `pytest.ini`'s allow-list entry.
4. **Delete the `N813` exemptions from `pyproject.toml`** — the whole
   `"src/modelviewprojection/mvpvisualization/**" = ["N813"]` entry (N813 is its only
   member), and `N813` from the `demos/**` list, leaving the rest of that list intact.
   Trim the explanatory comments that reference the camelCase filename.
5. Update prose in `README.md` and `CLAUDE.md`.
6. Leave `tasks/**` untouched.

## Gotchas

- **`tasks/archive/2026/07/18/pymatrixstack-bugs.md` deferred the naming of this module's *contents*** to
  the `N` pass, which is done: `matrixStack` -> `matrix_stack`, `copyOfM` -> `copy_of_m`,
  and the fake-dunders `__pushMatrix__` / `__popMatrix__` -> `_push_matrix` /
  `_pop_matrix`. This task is only the **file** name, so the two do not collide.
- The module holds **module-level mutable state** (`__modelStack__`, `__viewStack__`,
  `__projectionStack__`). If anything imports it twice under two names during the
  transition, there would be two independent stacks. Do the rename in one commit rather
  than leaving a compatibility shim; a shim here is genuinely dangerous.
- Check `entrypoint/*.sh` and any Makefile target for a hardcoded path before finishing.

## Gates

`make format` clean, `pytest` green headless and with a display, `ruff check --select N`
shows no `N813` anywhere, and the demos that use the stack (21, 22, 22a, 23, 24) still
render under Xvfb.
