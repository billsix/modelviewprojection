# Shell-exit `ty check` floods the terminal and makes `make shell` fail

**Status:** proposed — needs go-ahead
**Created:** 2026-06-13

## Symptom

Exiting the dev shell (`make shell` → type `exit`) dumps **hundreds of `ty` type-check
diagnostics** and ends with:

```
Found 307 diagnostics
...
Found 118 diagnostics
exit
make: *** [Makefile:90: shell] Error 1
```

So every normal shell exit looks like a build failure.

## Mechanism (why it happens)

`entrypoint/dotfiles/.extrabashrc` overrides the shell builtin `exit`:

```bash
exit() {
    echo "Formatting on shell exit"
    cd /mvp/src/ && format.sh
    cd /mvp/tests/ && format.sh
    builtin exit "$@"
}
```

and `entrypoint/format.sh` ends with two type-check passes:

```bash
ruff check src --fix; ruff check tests --fix
ruff format src --line-length=80; ruff format tests --line-length=80
ty check /mvp/src
ty check /mvp/tests
```

Two consequences:

1. **Flood:** `format.sh` runs on exit (twice — once cd'd to `src/`, once to `tests/`), each time
   running `ty check /mvp/src` + `ty check /mvp/tests`. With hundreds of diagnostics outstanding,
   that's a wall of output on every exit.
2. **`make shell` "fails":** `ty check` returns non-zero when it finds anything; that status flows
   through the last `format.sh` into `builtin exit "$@"` (a bare `exit` carries no args, so it inherits
   the last command's code), so the container exits 1 and `make` reports `Makefile:90: shell` Error 1.
   This is the same trap family flagged in spimulator/texExpToPng's `container-build-cleanup` (the
   `exit()` bashrc trap mishandling the shell exit code) — here it *propagates* a tool failure instead
   of dropping it.

## Root cause of the diagnostics

**~95% of them are one issue:** the installed gacalc types `Vector2`/`Vector3` coefficients as
`numbers.Real`, and `ty` (correctly, per the typing spec — the numeric tower is a runtime ABC
registration, not a static subtype relation) refuses plain `int`/`float`/`Literal` there:

```
error[invalid-argument-type]: Argument is incorrect
   T(Vector2(2.0, 0.0))   ^^^ Expected `Real`, found `float`
   Vector3(-1.0, -1.0, 0.0)   ^^^^ Expected `Real`, found `int | float`
```

- mvp pins **`gacalc>=0.0.3`** (`requirements.txt`); only `0.0.2`/`0.0.3` are tagged/released, so the
  image installed **PyPI 0.0.3**, which still annotates coefficients as `numbers.Real`.
- **The fix is already written and committed in local gacalc 0.0.4 (just not released).** Verified by
  generating and inspecting `src/gacalc/g2.py`/`g3.py`: `Vector2`/`Vector3` fields are `coeff_*: Coef`
  (= `int | float | sympy.Expr`), **no `Real` anywhere** in the generated code. `pyproject.toml` is
  already bumped to `version = "0.0.4"`; there is **no `0.0.4` git tag** and PyPI has no 0.0.4. So the
  gacalc-side fix needs **releasing, not writing**.

**The remaining ~5% are genuine, unrelated `ty` findings** worth fixing or suppressing:
- `generate_plots.py:310` — `FigureCanvasBase` has no `renderer` (matplotlib backend typing).
- `wxapp.py:192` — `Frame.__init__` wants `Size`, got `tuple[int, int]`.
- `wxapp2.py:37-38` — `_load_xrc._res` function-attribute pattern (`ty` flags attr-on-function).
- `test_cayley_graph.py` / `test_cayley_scene.py` — `Expected tuple[Step, ...], found list[...]` (a
  `list` literal passed where a `tuple` of `Step` is annotated).

## Proposed fixes (two independent axes — decide each)

### A. Stop a clean exit from looking like a failure
- **Don't let format/type-check status kill the shell.** Make the `exit()` trap end with
  `builtin exit 0` (or capture and re-use the user's intended code via `local rc=$?` *before* running
  format.sh) so `make shell` returns success on a normal exit.
- **Decide ty's role on exit:** keep it but advisory (run, show a one-line summary, never fail), or
  drop `ty check` from the on-exit `format.sh` and run it only via an explicit `make lint`/`make
  typecheck` target. Ruff-format-on-exit is cheap and worth keeping; the noisy/failing part is `ty`.
- Consider whether format-on-exit should run `ty check` over *both* `/mvp/src` and `/mvp/tests` twice
  (it currently does, via the two `cd … && format.sh` calls) — that's redundant.

### B. Fix the underlying diagnostics
- **Bulk (the `Real` flood):** the `Coef` fix is already in committed gacalc 0.0.4 source — it just
  needs **releasing**. Steps: (1) in geometricalgebra, sanity-check the release (`make test`,
  `make check-generated`, `make dist`), then **release 0.0.4 to PyPI** (`git tag` + `make upload` —
  author-run, since PyPI/git are host-side and publishing is outward-facing); (2) bump mvp's pin
  `gacalc>=0.0.3` → `>=0.0.4` in `requirements.txt`; (3) rebuild mvp's image; (4) verify in-container
  with `uv pip show gacalc` (== 0.0.4) and a clean-ish `ty check /mvp/src`. This clears essentially all
  the `Expected Real` errors.
- **Tail:** fix or explicitly suppress the four non-gacalc findings above (e.g. a typed `Size(...)` in
  `wxapp.py`, a real attribute/typed-cast for `_load_xrc`, `tuple(...)` instead of `list` for the
  `Step` sequences, and a guarded/`# ty: ignore`'d matplotlib `renderer` access).

## Progress (2026-06-13)

- **Done:** `requirements.txt` bumped `gacalc>=0.0.3` → `>=0.0.4`.
- **gacalc 0.0.4 verified** (in a sandbox venv): `Vector2.__init__(coeff_e_1: Coef = 0, …)` — `Coef`,
  no `Real`. Running `ty` over `src`+`tests` with 0.0.4 installed: **`Expected \`Real\`` errors = 0**
  (the ~244-error flood is gone). This is the core win.
- **"build" not possible in this sandbox:** mvp's full default image (`BUILD_DOCS=1` → TeX Live +
  Jupyter/Spyder) overflows the 8 GB tmpfs podman store; the lean build hits the pre-existing
  `$(which python)` Dockerfile bug. Verified via a venv instead. **Bill should `make image` on his
  host** to pick up gacalc 0.0.4.
- **Surprise — the remaining debt is much larger than the 4-item tail.** With the Real flood gone,
  `ty` still reports **181** diagnostics (168 src + 13 tests). 16 are venv-only noise (`moviepy`/`wx`
  not installed in the sandbox venv — not real in the container). The **~165 genuine** ones are
  pre-existing type debt the flood had been masking:
  - **38** — `Edge(steps=[…])`: `Edge.steps` is annotated `typing.Tuple[Step, ...]`
    (`mvpvisualization/cayleygraph.py:88`) but the documented contract accepts a *sequence* of `Step`
    **or** `(label, fn)` pairs (coerced in `__post_init__`). Fix needs a small design choice (widen to
    `Sequence[Step | tuple[str, InvertibleFunction]]` and re-narrow for the internal readers at lines
    97/135, or use an `InitVar`/classmethod ctor) — not a pure one-liner.
  - **42** — `Optional`/`| None` not narrowed (e.g. `Expected Frustum, found Frustum | None` across the
    viz code) — per-case asserts/narrowing.
  - **~4** — PyOpenGL stub limitations (`GL_A | GL_B` on `Constant`, `Constant` where `int` expected) —
    arguably `ty.toml`-suppress, not "fix."
  - the named small ones: `_load_xrc._res` (wxapp2, function-attr — clean fix is `@functools.cache`),
    `fig.canvas.renderer` (generate_plots, matplotlib stub gap), wx `Size` vs tuple (wxapp).
  - plus a long tail (~75) of assorted `invalid-argument-type`/`unresolved-attribute`/etc.
  Several of these live in **demo / mvpvisualization** code, where the project's CLAUDE.md says not to
  "clean up" without asking — so this is a real, scoped cleanup decision, not a quick tail.

**Recommendation:** land the gacalc bump now (it's the actual win and what we set out to do). A
*fully clean* `ty` over this GL/wx/matplotlib + viz codebase is a sizable, judgment-heavy effort and
realistically should be paired with **Axis A** (make `ty`-on-exit advisory/non-fatal) so `make shell`
stops reporting failure while the debt is paid down incrementally. Decide scope before grinding the 165.

## Acceptance

- A normal `exit` from `make shell` returns 0 (no `make: *** Error 1`).
- The terminal isn't flooded on exit (ty either gone from the exit path or summarized/non-fatal).
- After the gacalc bump + image rebuild, `ty check /mvp/src` and `/mvp/tests` are clean (or down to a
  small, deliberately-suppressed set).

## Notes

- First, **verify the installed gacalc version** in the container (`uv pip show gacalc`) to confirm the
  0.0.3-vs-0.0.4 diagnosis before bumping.
- Axis A is a quick, self-contained win (the user's immediate annoyance); Axis B is the real cleanup.
  They can land separately.
