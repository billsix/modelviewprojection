# mvp tests, gates & verification

**Reference document** — how modelviewprojection is actually verified: the gate
chain, the tests that encode contracts, the proof harnesses that past migrations
built, and the playbooks for type-checking and bulk edits. Not a task; update in
place. Last updated 2026-07-30.

Complements `tasks/reference/book-and-docs-pipeline.md` (which owns the book
build and the doc-region checker) and `design-decisions.md` (which owns the
*decisions* behind the gates). This doc is the operational map.

---

## 1. The gate chain — and the fact that there is no CI

**There is no CI.** `.github/` does not exist; every gate is local or
in-container, and `make html` on Bill's machine is the de-facto pipeline. The
gates, in the order they bite:

1. **`make format`** — the only standing code gate. Runs in-container:
   `loadpackages.sh` (activate `/venv`, `cd /mvp`, editable install) then
   `entrypoint/format.sh` (ruff check `--fix`, ruff format, `ty check` over
   `src`, `tests`, and the three `ports/codetheclassics/*` trees). Every step
   always runs; the script exits nonzero if *any* step failed (see
   `design-decisions.md` › "format.sh fails on ANY step"). Since 2026-08-04 there
   is also a **`make test`** target — in-container pytest (glfw present, so the
   windowing modules and their doctests actually run), venv activated, `pythonpath
   = src` from `pytest.ini` (no editable install), and WITHOUT `--exitfirst` so it
   reports every failure. It does **not** replace the book build's own inline
   pytest gate (gate 2 below); both exist.
2. **`entrypoint.sh`'s pytest gate** — `pytest --exitfirst` runs before the
   book builds; a failing test (doctests included) aborts the whole build.
3. **`tools/check_doc_regions.py`** — the anchor checker, run in-container
   after `_gacalc_src` is populated (details in the pipeline doc).
4. **The book build itself** (`make html`) — the loudest gate; a wrong
   `literalinclude` path or a missing aspell word stops it.

**The primary gate can fail OPEN — it has happened.** From ~2026-07-18 to
2026-07-24, `make format` reported *nothing* (not "green" — nothing): the
`loadpackages.sh` editable install died on `ModuleNotFoundError: setuptools`
before `format.sh` ever ran. Root cause: **Python 3.12+ venvs no longer seed
setuptools**, and `--no-build-isolation --no-index` means it must already be
present in the venv (gacalc's Dockerfile installs it explicitly; mvp's didn't).
71 `ty` diagnostics had accumulated behind the dead gate. When the gate looks
quiet, first confirm it actually *ran*.
(`tasks/archive/2026/07/24/make-format-gate-is-red.md`)

**Makefile gotcha:** the `format` recipe must `cd /mvp` in the `bash -c`
itself — `loadpackages.sh`'s own `cd` is subprocess-local and does not carry to
`format.sh`, which uses relative paths (`ruff check src`).

## 2. Shape of the test suite

Seven files under `tests/`, ~60 test functions, **no `conftest.py` anywhere** —
imports work solely via `pythonpath = src` in `pytest.ini`.

- **The doctest allow-list in `pytest.ini` is a workaround, not the design**
  (its own comment says so): `--doctest-modules` *imports* what it collects,
  and the runnable demo scripts execute on import, so the list names only the
  library areas. It already covers every library module — see
  `design-decisions.md` › "The main-guard + `:dedent:` plan was CLOSED".
- **The `slow` marker is declared but unused** — `pytest.ini` defines it and
  `addopts` deselects it, but no `@pytest.mark.slow` exists in the tree. It's
  inherited convention from gacalc, currently a no-op here.
- **`pyproject.toml` has a dead `[tool.pytest]` table** (`testpaths`); pytest
  reads `[tool.pytest.ini_options]`, and `pytest.ini` wins anyway. Edit
  `pytest.ini`, not that table.
- **Two test files are published into the book**, so they're under the
  doc-region marker regime and their text lands in chapters:
  `tests/test_firstclassfunctions.py` → `book/docs/miscellany.rst`;
  `tests/test_mathutils.py` → `book/docs/ch16.rst` (function-stack examples).
  Editing them can change a printed page.

## 3. Tests that encode contracts (each guards a specific incident)

- **`tests/test_gl_vector_unpacking.py`** — pins gacalc `Vector2`/`Vector3`
  **iteration order and arity**, so `GL.glVertex3f(*v)` (used in demos 05–18)
  can't silently mis-draw after a gacalc upgrade. Uses a positional-args
  recorder; no GL required.
- **`tests/test_ctc_actor_field_collisions.py`** — a pure-AST guard: scans
  every CtC game's Actor-rooted dataclass field names against the property
  names of `pgzero_gl/actor.py`. Exists because a dataclass field named like a
  base-class property picks up the *property object* as its default — and it
  only exploded for some field orders ("bunner survived by luck while cavern
  and avenger crashed", 2026-07-09). This is why those fields are `spawn_pos`.
- **`tests/test_focus_to_matrix.py`** — pins `cayleyscene.to_matrix`'s
  `dtype=float` coercion: gacalc `magnitude()` routes through `sympy.sqrt`, and
  without the cast `np.linalg.inv` fails on `dtype=object`
  (`tasks/archive/2026/06/13/mvpviz-focus-failure.md`).
- **`tests/test_cayley_scene.py` is a parity harness, not a unit test.** Its
  constants are copied *verbatim* from `modelviewperspectiveprojection.py`
  (the header says so), and it re-implements that demo's hand-coded interp.
  **Changing that viz demo's numbers requires changing this test in lockstep**
  — nothing else declares the coupling.

## 4. Proof harnesses worth reusing

Built for past migrations; reach for these shapes instead of reinventing them.

- **Differential state trace** (frozen-vector migration, 2026-07-23): same
  seed, 300 frames of headless `update()`, canonical dump of every actor's
  numeric state, run old-source-old-dep vs new-source-new-dep and diff —
  byte-identical for all six games. Gotcha: an `id()`-keyed visited-set gives
  **false skips** (`Actor.pos` returns a fresh `Vector2` per call and freed
  temporaries' ids get reused) — check leaves before the cycle guard.
  (`tasks/archive/2026/07/23/frozen-vectors-rebind-migration.md`)
- **Definitions gate** (`runpy.run_path` with `go` stubbed): executes class
  bodies, which `py_compile` does not — this caught ~20 latent bugs in the
  shim-dynamism audit. (`tasks/archive/2026/07/09/ctc-shim-dynamism-audit.md`)
- **Pixel-identical figure gate**: `PIL.ImageChops.difference(...).getbbox()
  is None` over all 170 book SVGs, used to prove a plotting refactor changed
  nothing. (`tasks/archive/2026/07/19/investigate-plotting-transform-model.md`)
- **GL-stub call recorder**: byte-identical `glBegin`/`glNormal`/`glVertex`
  emission sequences, used to prove the `_primitives.py` extraction faithful
  (recurring ≤1 ULP torus discrepancy is expected — `(i+1)*step` vs
  `a0+step`). (`tasks/archive/2026/05/29/extract-data-generation.md`)
- **CtC smoke test** (`ports/codetheclassics/_smoketest.py`): renders one
  frame per game to an offscreen EGL pbuffer and fails if mostly black.
  **Nothing runs it automatically** — it was silently broken 2026-07-08 →
  2026-07-25 and is a manual tool, not a gate. Env facts it depends on: both
  `PYOPENGL_PLATFORM=egl` *and* `EGL_PLATFORM=surfaceless` must be set
  **before** `from OpenGL import …`, or PyOpenGL binds GLX and every call
  raises "no valid context". And judge the output by *looking at the PNGs*,
  not only the non-black percentage.
  (`tasks/archive/2026/07/25/fix-smoketest-broken-pgzrun.md`)
- **Headless plotting**: `plotsforbook/plotutils/matplotgraphs.py` falls back
  to `Agg` when `DISPLAY` is unset (it once hardcoded `TkAgg` and couldn't be
  imported headless). (`tasks/archive/2026/07/19/doctests-everywhere.md`)

## 5. Type-checker playbook (ty)

- **GL constants:** the working alias is `GLenum = int | Constant`
  (PyOpenGL's `OpenGL.constant.Constant`) — plain `GLenum = int` does *not*
  work, because ty resolves PyOpenGL constants to base `Constant` even though
  `IntConstant` subclasses `int` at runtime. Copies live in `_pipeline.py`,
  `wxapp.py` (deliberate local copy — importing `_pipeline` would drag
  glfw+imgui into a wx app), `demo21.py`, `demo24.py`.
- **Suppressions can leak into the book.** `demo21.py` is included by
  `ch21.rst` — so a `# ty: ignore` on a flagged line would have printed in the
  chapter; the fix chosen instead was making the code clean
  (`glfw.window_hint(..., glfw.TRUE)` not `GL.GL_TRUE`). Check whether a file
  is book-included before suppressing in it.
- **ty parses the literal text `ty:` inside ordinary prose comments** as a
  malformed suppression directive — a comment *describing* old suppressions
  was itself a diagnostic. Spell it out ("the ty checker") in prose comments.
  (all three: `tasks/archive/2026/07/24/make-format-gate-is-red.md`)
- **ty is a partial oracle for frozen-vector writes:** it flags `v.x = …`
  (invalid-assignment) but says nothing about `v.x += …` — pair it with a grep
  (see `CLAUDE.md` › Code-the-Classics).
- **Never check mvp against an installed gacalc with `ty --python <prefix>`**
  — it gives false readings (e.g. `Vector − Vector → G3`). The container's
  gate works because `/venv --system-site-packages` puts pip and ty in one
  environment; outside it, use a venv or `PYTHONPATH`.
  (`tasks/archive/2026/07/22/precise-product-types-coefficient-cleanup.md`)

## 6. Bulk-edit playbook (hard-learned, 2026-07-18/19)

From the coding-standard sweep (`tasks/apply-python-coding-standard.md`, which
carries the full detail). Any future bulk mechanical pass should follow these:

1. **Find a signature's end with the AST** (`node.body[0].lineno`), never by
   text-scanning for `:` — the text heuristic deleted three functions from
   `modelvieworthoprojection.py`.
2. **Never hardcode a replacement signature** — a lookup table invented a
   `self` param for `wxapp2._load_xrc`; **ruff and ty both passed**, only
   launching the app caught it. Derive params from the AST.
3. **Re-apply original indentation and preserve trailing comments.**
4. **Diff structure against `git show HEAD:<path>`** — `def` counts *and*
   per-function parameter tuples.
5. **Run the artifact, not just the checkers** (demos launch under Xvfb,
   notebooks execute, generators emit figures).
6. **Let the checker find your wrong annotations** — ~1 in 10 was too narrow
   and ty caught every one. Treat its complaints as findings.
7. **Prose reflow cannot be automated in this repo.** A reflow pass matched 87
   paragraphs, mostly deliberate line breaks; even narrowed, it caught
   Controls lists (`demo22.py`), face-index lists (`demo22a.py`),
   commented-out code, jupytext `# %%` markers, and math notation
   (`softwarerendering.py`'s `|v1||v2|`). Use an explicit allowlist of
   paragraphs you have read.
8. **Invoke the tool the way the gate does.** "The ports are not
   ruff-formatted" was a measurement error — measured at ruff's default 88
   while `format.sh` formats at 80 (130 of 133 files were already formatted).
9. **Classifier for `Vector2(*x)` copy sites** (post-frozen-gacalc): a
   *vector-typed* source is a pure aliasing copy (redundant now); an
   `Any`/tuple-typed source is *normalization* and must stay. A green ty run
   is itself the proof (it would reject `= x` for a tuple source). And a
   `DEFAULT_*` constant whose copy is removed re-trips ruff `B008` — the
   constant stays even when the copy goes.
   (`tasks/archive/2026/07/25/redundant-vector-defensive-copies.md`)

## 7. What the gates do NOT cover

- **check_doc_regions validates book→code only.** A marker no chapter includes
  is invisible. Current dead markers (verified 2026-07-30, excluding string
  literals inside the checker itself): `clockwise`, `counter clockwise`,
  `parallel` (`framebuffer/softwarerendering.py`); `define find normal`,
  `define plane equation`, `define distance to plane` (`mathutils.py`);
  `planar shadow` (`demos/demo22/demo22.py`). These are candidate future
  book anchors, not garbage — don't delete without Bill. (The `is_clockwise`
  recursion bug hid precisely in a no-test, no-book-slice region.)
- **`:caption:` text is unvalidated** — see the pipeline doc's gotchas.
- **The CtC games have no automatic gate** — the smoke test is manual (§4),
  and `ty` covers the shim + games only via `format.sh`.
- **The SuperBible ports have no gate at all** beyond ruff formatting; they
  are hardware-verified by Bill only.

## 8. Vestigial / trap files a reader will trip over

- **`setup.py`** — a 4-line setuptools shim; `pyproject.toml` is authoritative
  (`dynamic = ['dependencies']` ← `requirements.txt`).
- **`entrypoint/spyder.sh`** — mounted by `FILES_TO_MOUNT` but `USE_SPYDER`
  defaults to 0 and there is no `make spyder` target.
- **`entrypoint/jupyter.sh`** — deliberately wide open (`--allow-root`, empty
  token/password, XSRF off): fine for an ephemeral single-user container,
  a footgun anywhere else.
