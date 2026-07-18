# `make format` — the repo's only gate is red on master

**Status:** **layer 1 FIXED 2026-07-18** — Bill approved the image change; `setuptools`
+ `wheel` are installed into `/venv` in the `Dockerfile`, the image was rebuilt with the
repo's default flags, and `make format` now RUNS (it previously died in
`loadpackages.sh` and executed no checks at all). **Layer 2 partly resolved:** the
`GLenum = int | Constant` alias removed 3 copy-pasted `# ty: ignore`s; the 6 glfw
diagnostics are deliberately left (Bill: "leave them"), so `make format` still exits 1
by design. Remaining: the 4 `ComposableFunction` errors, which clear themselves once
gacalc 0.0.10 is released and `requirements.txt` is bumped.
**Created:** 2026-07-18
**Found by:** trying to run the gate during
[apply-python-coding-standard](apply-python-coding-standard.md)

`make format` is mvp's only real verification gate — there is no `make test` target. It
**exits 1 on master**, and has been failing for long enough that a second layer of
breakage accumulated behind the first, invisibly.

## Layer 1 — the gate never starts

`entrypoint/loadpackages.sh` runs

```sh
uv pip install --no-deps --no-index --no-build-isolation -e . --python $(which python)
```

which dies with `ModuleNotFoundError: No module named 'setuptools'`. Because
`loadpackages.sh` fails, **`format.sh` never runs at all** — no ruff, no ty. The gate
isn't reporting a problem; it is reporting nothing.

### It is NOT a uv-vs-pip problem, and NOT a missing `build-system.requires`

Two plausible-sounding diagnoses, both wrong:

- **"Add `setuptools` to `build-system.requires`."** It is already there
  (`pyproject.toml:13`). `--no-build-isolation` tells the installer *not* to create an
  isolated build env and *not* to install the build requires — it expects `setuptools`
  to already exist in `/venv`. The declaration is correctly written and simply unused.
- **"Switch from uv to plain pip."** Same failure. With `--no-build-isolation`, pip has
  the identical requirement. And the isolation cannot simply be re-enabled, because
  `--no-index` makes the install **offline** — an isolated build env would have to
  download `setuptools` and there is no index to fetch it from. Either tool, the
  package must be present locally.

**Root cause: Python 3.12+ venvs no longer seed `setuptools` by default**, and mvp's
image never installs it.

### The actual difference from gacalc (which works)

| | gacalc | mvp |
|---|---|---|
| `python3-setuptools` via dnf | `Dockerfile:18` | **absent** |
| `setuptools` into the venv | `:56` `uv pip install ... setuptools wheel numpy sympy` | **absent** (`:120` installs only `pyright`) |
| venv creation | `:53` `python3 -m venv --system-site-packages` | `:117` identical |
| install command | `uv pip ... --no-build-isolation -e .` | identical |

Both repos use uv, both use `--no-build-isolation`, both use `--system-site-packages`.
gacalc installs `setuptools` twice over; mvp not at all.

### Proposed fix — mirror gacalc

Add to mvp's `Dockerfile`, matching gacalc's shape:

1. `python3-setuptools` (and `python3-wheel`) to the dnf list, and/or
2. a `uv pip install --python $(which python) setuptools wheel` line beside the
   existing `pyright` install at `:120`.

**This is a permanent change to what the image ships, so it needs Bill's explicit
go-ahead** (per the standing rule: temporary dev aids are pre-authorized, real
dependencies are not). Verified in a throwaway container that installing `setuptools`
into `/venv` is sufficient — `loadpackages.sh` then succeeds and `format.sh` runs to
completion.

## Layer 2 — with the gate unblocked, `format.sh` exits 1 on 15 ty diagnostics

These were hidden behind layer 1. `ruff check` and `ruff format` are **clean**; all of
these are `ty`.

### 2a. glfw / PyOpenGL stub mismatches (6)

GL constants are `OpenGL.constant.IntConstant`, but the glfw stubs declare `int`:

- `ports/codetheclassics/pgzero_gl/runner.py:72` (`window_hint`)
- `src/modelviewprojection/mvpvisualization/_pipeline.py:103` (`window_hint`), `:151`
- `src/modelviewprojection/demos/demo21/demo21.py:62`, `:90`
- `src/modelviewprojection/demos/demo22/demo22.py:104`
- `src/modelviewprojection/demos/demo22a/demo22a.py:80`
- `src/modelviewprojection/demos/demo23/demo23.py:78`
- `src/modelviewprojection/demos/demo24/demo24.py:87`
- `src/modelviewprojection/mvpvisualization/cayley_gl.py:531` (`set_window_monitor`)

**RESOLVED for the signatures we own (2026-07-18):** `_pipeline.py` now defines
`GLenum = int | OpenGL.constant.Constant`, and `make_vbo` in `_pipeline`, `demo21` and
`demo22` use it — replacing three copy-pasted `# ty: ignore[invalid-parameter-default]`
with one typed alias. Note a plain `GLenum = int` does **not** work: ty resolves PyOpenGL
constants to the base `Constant`, not `int`, even though `IntConstant` subclasses `int`
at runtime. Verified by probing four candidate definitions.

**The remaining 6 are DELIBERATELY LEFT (Bill, 2026-07-18: "leave them").** They are
calls *into* glfw (`window_hint`, `set_scroll_callback`) whose stubs declare `int`; we do
not own those signatures, so no alias on our side fixes them. The options were per-call
suppressions or wrapping glfw's typed surface — both are a lot of machinery to satisfy a
third-party stub, and the diagnostics are honest signal. **`make format` is expected to
report these; that is not a regression.**

### 2b. `ComposableFunction` vs `InvertibleFunction` (4) — cross-repo regression

- `src/modelviewprojection/demos/demo06.py:135`, `:151`
- `src/modelviewprojection/demos/demo07.py:146`, `:162`

> `Object of type ComposableFunction[Vector2] is not assignable to InvertibleFunction[Vector2]`

**This is fallout from a gacalc change, not an mvp bug.** gacalc split its function
hierarchy (`functions.py`, 2026-07-17): `ComposableFunction` is compose + label with **no
inverse**, and `InvertibleFunction` extends it. `project` / `reject` now return
`ComposableFunction`, because a projection discards information and genuinely is not
invertible — gacalc's `CLAUDE.md` states that making this a *type* error rather than a
runtime surprise was the entire point of the split.

**RESOLVED UPSTREAM 2026-07-18 — and the demos needed no edits.** The root cause was
not the demos and not `project`/`reject`: it was that `ComposableFunction.__matmul__`
was declared once, returning `ComposableFunction`, even though it delegates to
`compose()` — which *is* overloaded and *does* return an `InvertibleFunction` when every
part is invertible. So `InvertibleFunction @ InvertibleFunction` returned an invertible
function at runtime while typing as a non-invertible one. Fixed in gacalc by adding
`@typing.overload`s on `InvertibleFunction.__matmul__`.

Verified by installing the fixed gacalc over the PyPI one in a throwaway container:
demo06 and demo07 go from 4 errors to "All checks passed!" with **zero changes to mvp
source**. Correct outcome — these are book chapters teaching invertible-function
composition, and the code was right all along.

**RESOLVED 2026-07-18.** gacalc 0.0.10 is released and mvp is bumped to it; these 4
errors are gone with **zero changes to mvp source**, and a 5th (`to_matrix`) cleared with
them. Tracked in geometricalgebra's `tasks/archive/2026/07/18/release-0-0-10-and-bump-mvp.md`;
once that lands, bump `requirements.txt` to `>=0.0.10`, rebuild, and these 4 disappear
on their own.

### 2c. `to_matrix` argument type (1)

`src/modelviewprojection/mvpvisualization/modelview2d.py:159` →
`src/modelviewprojection/cayley/cayleyscene.py:430`.

## Gates for this task

`make format` exits **0**. Note that requires resolving both layers — installing
`setuptools` alone leaves it red at 15 diagnostics, which is arguably the more useful
milestone since it makes the gate *informative* for the first time.
