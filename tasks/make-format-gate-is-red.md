# `make format` — the repo's only gate is red on master

**Status:** **layer 1 FIXED** (2026-07-18) and **layer 2b/2c RESOLVED** (gacalc bump).
The gate now runs and is **red *by design*** — the only remaining diagnostics are
third-party-stub mismatches Bill chose to leave, plus one ty comment-parsing
false-positive. `ruff` is fully clean. See "Current state" below.
**Created:** 2026-07-18
**Found by:** trying to run the gate during
[apply-python-coding-standard](apply-python-coding-standard.md)

## Current state (re-measured 2026-07-24, image rebuilt against gacalc 0.0.14)

`ruff check` and `ruff format` are **clean** across `assignments`/`src`/`tests`/`ports`.
`ty` reports **12 diagnostics, all pre-existing / by-design** — none are a bug in mvp
source, and none were introduced by the frozen-vector migration (verified by running
the same gate against `a4168504^`: the set is identical there, alongside the 58
now-fixed read-only errors). So `make format` exits 1, as designed.

- **10 — third-party glfw stub mismatches** (`window_hint`'s value arg is a PyOpenGL
  `Constant`, not `int`; `set_scroll_callback`/`set_window_monitor` reject `None`).
  Across `demos/demo21`–`demo24`, `mvpvisualization/_pipeline.py`, `cayley_gl.py`,
  `pgzero_gl/runner.py`. **Deliberately left (Bill, 2026-07-18: "leave them")** — we
  don't own the glfw stubs; the count grew from 6 → 10 only because newer demos
  (`demo22a/23/24`) and a newer glfw `.pyi` cover more call sites, not because of any
  regression.
- **1 — `wxapp2.py:195` `XmlResource.LoadFrame(self, None, "MainFrame")`.** Same class
  as the glfw ones: the wx stub types `parent` as `wx.Window`, we pass `None`. A
  third-party-stub mismatch surfaced by a newer wx `.pyi`; leave with the glfw set
  unless we decide to suppress that family.
- **1 — `_pipeline.py:75` `invalid-ignore-comment` — a ty FALSE POSITIVE.** Line 75 is
  a *comment* that quotes the string "`# ty: ignore`" in prose; ty parses the embedded
  text as a real (malformed) directive. Fix, if wanted, is to reword the comment so it
  doesn't contain that literal — not a code change.
- ~~1 — `soccer.py:467` unused `# ty: ignore[unsupported-operator]`~~ — **REMOVED
  2026-07-24.** gacalc 0.0.14's precise operator typing made the suppressed
  `unsupported-operator` resolve, so the directive was dead; dropped the directive,
  kept the "faithful upstream" explanation.

**The frozen-vector migration's effect on this gate:** it removed **58** read-only
errors (in-place writes to now-frozen gacalc vectors) and unmasked exactly one latent
issue (`beatstreets.py:2901`, a `Rect.left = Coef` assignment previously hidden behind
an adjacent read-only error), fixed with a `float(...)` coercion. Net 71 → 12.

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

## Layer 2 — the ty diagnostics behind the (now-unblocked) gate

These were hidden behind layer 1. `ruff check` and `ruff format` are **clean**; all of
these are `ty`. The **live inventory is now the "Current state" section at the top**
(re-measured 2026-07-24); the subsections below are kept for the history of what each
class was and how it was resolved. **2b and 2c are fully resolved and no longer appear.**

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
them. Tracked in gacalc's `tasks/archive/2026/07/18/release-0-0-10-and-bump-mvp.md` (`github.com/billsix/geometricalgebra`);
once that lands, bump `requirements.txt` to `>=0.0.10`, rebuild, and these 4 disappear
on their own.

### 2c. `to_matrix` argument type (1)

`src/modelviewprojection/mvpvisualization/modelview2d.py:159` →
`src/modelviewprojection/cayley/cayleyscene.py:430`.

**RESOLVED** — cleared alongside 2b when `requirements.txt` was bumped past gacalc
0.0.10 (the pin is now 0.0.14); no longer appears in the gate output.

## Gates for this task

**The gate is now as green as it is going to get without a policy decision.** Layer 1
runs, layers 2b/2c are gone, and `ruff` is fully clean. The only thing keeping
`make format` at exit 1 is the **12 deliberately-left / third-party-stub diagnostics**
in "Current state" — Bill's standing call is to leave the glfw family, so a literal
`exit 0` would require a *new* decision (suppress the glfw/wx third-party-stub family,
and reword the one prose comment that ty misparses). Until then, "informative and red"
is the intended steady state, not an open bug. Re-open only if a *new* mvp-source
diagnostic appears (i.e. anything in "Current state" that is not glfw/wx-stub or the
comment false-positive).
