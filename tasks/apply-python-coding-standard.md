# Apply the Python coding standard to modelviewprojection

**Status:** **in progress — naming and annotations DONE; type aliases partly done.**

Landed 2026-07-18/19: ports lint cleanup; 80-column limit from one config key; **`N`
enabled repo-wide with 0 violations**; the `## Coding standard (Python)` section written
into `CLAUDE.md` in three reviewed parts and a `Contributing` section into `README.md`;
and the **annotation sweep, 439 -> 43 missing** (returns 165->19, params 274->24) across
`cayley_gl`, `util/nbplotutils`, all seven `mvpvisualization/*` demos,
`plotsforbook/generate_plots`, both `wxapp*`, the `demos/*`, and `_pipeline` -- the last
completing the type chain, so `setup_window`'s `(window, impl, imguiio)` is typed
end-to-end into every consumer.

**Domain type aliases landed so far:** `GLenum` (`_pipeline`, and a deliberate local copy
in `wxapp.py` -- importing `_pipeline` there would drag glfw+imgui into a wx app),
`Mesh` / `MutableMesh` / `GLHandle` / `VertexCount` (`cayley_gl`), `Axis` /
`PlotTransform` (`generate_plots`).

**Remaining:** the last 43 annotations are stragglers, 1-5 per file across twelve files.
**Deliberately deferred: `plotsforbook/plotutils/mpltransformations.py` (5)** -- its types
depend on the outcome of
[investigate-plotting-transform-model](investigate-plotting-transform-model.md), so
annotating it now would likely be redone. Bill wants that investigation done first, then
the remaining type work.
**Created:** 2026-07-18

## Goal

Do for **modelviewprojection** what was just done for **gacalc**: articulate a
Python coding standard into this repo's `CLAUDE.md` (canonical) with a `README`
pointer, turn on the enforceable slice in ruff and fix the fallout, then apply the
judgment-call slice module-by-module across the **first-party** code — annotating
generously and cleaning up names — leaving the repo ruff- and ty-clean with all
gates green.

The gacalc standard is the template. Read
`../geometricalgebra/CLAUDE.md` → the **`## Coding standard (Python)`** section
first; it is the authored source of truth. This task records what Bill wanted while
that standard was built and applied, so the mvp pass reproduces the *intent*, not
just the letter.

## Scope — everything, ports included (Bill, 2026-07-18)

The whole repo is in scope: `src/modelviewprojection/` (the library — the
Cayley-graph engine, `InvertibleFunction`, first-party demos), any first-party
`assignments/`/tooling, **and the ports** (`ports/codetheclassics/`,
`ports/openglsuperbiblev4/`). Bill explicitly wants the standard applied to the
ported code too — unlike gacalc's off-limits vendored Emacs tree, nothing here is
exempt.

**The tension to handle deliberately (this is the crux of the ports work):** the
ports currently carry a large `per-file-ignores` block (in `pyproject.toml`, with a
rationale comment in `CLAUDE.md`) that preserves *upstream* style — it exempts them
from E501, F403/F405, S311, T201, E711/E712, B007, UP035, E722, E402, E741, E731,
B008, F841, UP007, etc. Applying the standard to the ports means **retiring those
ignores rule-by-rule and fixing the code to satisfy them — which diverges the ports
from their upstream source.** That divergence is the point now, but:

- **Confirm rule-by-rule, not wholesale.** Some ignores encode a real upstream idiom
  that's genuinely intended (e.g. pgzero's `from pgzero_gl import *` → F403/F405; the
  `sys.path`-then-import dance → E402; game RNG → S311). Before deleting an ignore and
  "fixing" its violations, check with Bill whether that specific idiom should be
  reworked or kept. Delete-and-fix the ones that are just upstream sloppiness
  (naming, unused vars, `== None`, missing annotations); keep (and keep documenting)
  the ones that are load-bearing idioms.
- **Update the `CLAUDE.md` rationale block as you go** so it always describes the
  *remaining* ignores accurately (open-issues-list discipline: don't leave a
  retired ignore documented as if it's still there).
- Retiring E501 on the ports means reflowing long upstream teaching comments — check
  that's wanted before doing it (it's the highest-churn, lowest-value one).

## The standard, as Bill wants it (distilled from the gacalc session)

Enforced-vs-prose split — the standard has two halves: what ruff enforces (turn it
on, fix don't suppress) and prose judgment calls (apply with taste, module by
module). Concretely:

- **Turn on `N` (pep8-naming)** in `[tool.ruff.lint] select` and fix every violation
  *by renaming*, not by ignoring — **including in the ports** (upstream game code is
  full of camelCase like `WIDTH`/`numGhosts`/`gameState`; those get renamed now).
  (In gacalc this caught `graphBounds`→`graph_bounds`,
  `extraLinesMultiplier`→`extra_lines_multiplier`, uppercase math locals `M`→`m`,
  etc.) Check whether any *other* enforceable rule gacalc's standard names is off here
  and worth turning on the same way.
- **An externally-defined name overrides the naming rules (Bill, 2026-07-18).** Where a
  name is dictated from outside the code — a framework superclass method being
  overridden, a protocol/dunder, a fixed callback signature — match it **exactly**;
  renaming unbinds it and breaks the code. This needs no case-by-case discussion.
  **In mvp this covers `wxapp.py` / `wxapp2.py`** (`OnPaint`, `OnTimer`, `InitGL`,
  `OnDraw`, `OnInit` — wxPython looks up those exact names; 7 of the repo's `N`
  violations), and any GLFW/imgui callback whose signature is fixed by the API taking
  it. **Do NOT rename these.** Add a scoped `per-file-ignores` entry for the wxapp files
  with the reason written at the site, and document the carve-out in `CLAUDE.md` so the
  next person doesn't "fix" it. The exemption covers only the externally-fixed name —
  parameters and locals inside those methods still follow house style.
- **Annotate as generously as reasonable — "when in doubt, annotate."** This is the
  single most-repeated preference. Locals, params, returns. Including **loop and
  tuple-unpack targets**, via a bare `name: Type` declaration line *directly above*
  the `for`/unpacking statement (NOT comprehensions — those can't be annotated; and
  NOT where it would fight the checker). If a loop variable is **reused across two
  loops with different types**, do NOT leave it untyped — type each and **rename** the
  second binding to something distinct.
- **"Don't fight the checker."** Where an annotation makes ty *worse* (widens a match,
  breaks gradual typing on a `.dual()`/`.to()` chain, forces a spurious cast), leave
  it off and add a one-line comment saying why. Bill will ask "why did you remove a
  type?" — the answer must be a real checker interaction, documented at the site. Use
  `Mapping`/`Sequence` (covariant, read-only) over `dict`/`list` for params;
  `MultiVectorBase`-style base types only where genuinely polymorphic, the concrete
  type otherwise.
- **Naming grammar.** A local bound to a **class/type object is named `cls`** — never
  `representation`, `klass`, etc. Mutate-vs-return / CQS: `sort` mutates, `sorted`
  returns; a function named for a noun returns it, a verb-phrase that mutates returns
  `None`. Rename junk/placeholder names (gacalc had `asdf`, `aoeu` → real names).
- **Inline single-use, and it takes precedence over typing.** A value used exactly
  once is inlined rather than bound-then-typed (gacalc inlined `forward`/`inv_str`/
  etc.). Keep a name only when it aids reading (tests, teaching, a semantic role) —
  then type it.
- **Introduce domain type aliases** the way gacalc added `Blade = tuple[int, ...]`
  (beside `Coef`/`BladeCoef`) and threaded it through. Look for mvp's raw-typed
  domain concepts — a vertex/edge/path in the Cayley graph, a matrix, a vector tuple,
  a color — and give the recurring ones a named alias, then thread it.
- **New code vs. existing code — and why this task is the exception (Bill,
  2026-07-18).** gacalc's standard says a rule is "preferred for *new* code; don't
  churn existing early-return code." Bill wants **mvp's `CLAUDE.md` to carry that same
  general rule** — going forward, these shapes apply to new code and nobody rewrites
  working code to chase them. **But this task is the one-time sweep that brings the
  existing code up to the standard**, so within it *all* the code gets changed now.
  Write the `CLAUDE.md` rule in its don't-churn form; do the sweep once here. After
  this task lands, don't-churn governs.
- **Use modern Python, and flag it proactively (Bill, 2026-07-18).** Bill runs
  **Python 3.14** (mvp's container is 3.14.6; gacalc declares `requires-python >=3.13`)
  and **compatibility with older Pythons is explicitly not a concern.** So: prefer the
  current-language solution over the historical one, and — this is the active part —
  **when a newer feature would solve a problem in code you are touching, say so** rather
  than silently preserving the old form. Bill particularly likes `match` (structural
  pattern matching) and asked for it by name.
  Worth flagging when encountered: `match` in place of `if`/`elif` chains over an enum or
  a shape-dispatch (with `case _:` making the fall-through explicit — see
  [pymatrixstack-bugs](archive/2026/07/18/pymatrixstack-bugs.md) bug 1); `X | Y` unions and builtin generics
  over `typing.Optional`/`Union`/`Dict`/`Tuple` (already swept in the ports);
  `@override`; `Self`; `typing.TypeIs`; PEP 695 `type` aliases and the `class C[T]:` /
  `def f[T]()` generic syntax in place of explicit `TypeVar`s; `enum.StrEnum`;
  `dataclass(slots=True, kw_only=True)`; `itertools.batched`; `tomllib`; the
  `except*` group syntax where it fits. Do not force one in where it reads worse — the
  point is to stop *defaulting* to the old spelling.
- **Inner-function-first (Scheme-style) shape**, project conventions, the full idiom
  checklist — carry over from gacalc's section; adapt examples to mvp.

  **The worked example and the precedent list must be re-derived against mvp source,
  not copied.** gacalc's rule ends with "Precedent already in the tree: …" naming four
  functions. Those names are gacalc-specific and meaningless here — mvp needs its own
  list, and it has to be *verified*, not guessed. Two failures found in gacalc's copy
  on 2026-07-18, both of which copying would reproduce:
  - Its example called a helper (`rejection(r)`) that the snippet never defined —
    a condensed example that drifted from the real `base.reject` it was drawn from.
    Whatever mvp's example is, write it from the actual function and re-read it.
  - Its precedent list cited `base.project`, which does the **opposite** of the rule
    (dispatch above the core inner fn), and `to_matrix`, which only illustrates the
    cheap-`raise` caveat. A reader opening the cited code to learn the shape learned
    the wrong one.

  Cheap way to build mvp's list: AST-walk every function containing a nested `def`
  and report what precedes it (guards/dispatch vs. plain setup), then hand-classify
  — the rule's "a cheap top-of-function `raise` is fine" carve-out means a mechanical
  scan over-reports. That sweep over gacalc took one pass and found exactly one real
  deviation. Expect mvp (bigger, ports included) to surface more; some will be
  don't-churn-existing-code, and the standard should say which.

## Bulk signature rewriting: the four things that broke it (2026-07-18/19)

The annotation sweep is done with scripts that rewrite `def` lines across many files.
Two of those scripts damaged source before being caught. Both were recoverable
(`git checkout`, since the files were committed) but the failures are systematic, not
bad luck — each new script re-solved problems the previous one had already solved. Any
future bulk-signature edit must do **all four**:

1. **Find the signature's end with the AST, never with text.** The end is
   `node.body[0].lineno`, i.e. the line before the first body statement. A "scan forward
   until a line ends with `:`" heuristic walks straight past
   `def _cam_back():  # +Z cameraspace` and **swallows the following functions** — that
   deleted `_cam_back`, `_cam_left` and `_cam_right` from
   `mvpvisualization/modelvieworthoprojection.py`.
2. **Re-apply the original indentation** to every line of the replacement. Dropping it
   silently un-indents nested `def`s and the file stops parsing
   (`plotsforbook/generate_plots.py`).
3. **Preserve any trailing comment** on the `def` line (`# +Z cameraspace`), or the
   rewrite quietly discards documentation.
4. **Never hardcode a replacement signature -- derive it from the source.** A lookup
   table of hand-written `def` lines invented a `self` parameter for
   `wxapp2._load_xrc`, a module-level function that has none. Every caller then failed
   with `TypeError: missing 1 required positional argument`. **`ruff` and `ty` both
   passed**; only *launching the app* caught it. Read the existing parameter names from
   the AST and add annotations to them.
5. **Verify nothing changed structurally before moving on.** Compare against
   `git show HEAD:<path>` on two axes -- `def` counts (catches deletions, failure 1) and
   **parameter lists per function** (catches invented/dropped parameters, failure 4):

   ```python
   # for each function: tuple(a.arg for a in args.posonlyargs+args.args+args.kwonlyargs)
   # must be IDENTICAL before and after; only annotations may differ
   ```
6. **Run the artifact, not just the checkers.** Three of the four failures above were
   invisible to ruff and ty. Demos and apps must actually launch (Xvfb), notebooks must
   execute, plot generators must emit their figures.

**Then let the checker find your wrong annotations.** Roughly one annotation in ten was
too narrow, and `ty` caught every one: `transform_matrix: np.ndarray` (`to_matrix`
returns `ndarray | sympy.Matrix`), `_focus(node: Space)` (the `FOCUS` menu includes
`("NDC", None)`), `draw_screen(width: float)` (it indexes `range()`, so `int`),
`create_single_frame(...) -> None` (it *yields* figures), `create_graphs` (a
`@contextmanager` that returns the figure after yielding), `procedures: Sequence`
(the code calls `.copy()`). Annotating is not transcription — run `ty` per module and
treat its complaints as findings, not noise.

## Process — how Bill wants it run (hard-learned this session)

- **Module by module, incrementally, each finish → Bill reviews → Bill commits.**
  Bill explicitly asked to go "one by one … finish it, let me review it, and then I
  commit." Do not batch the whole repo into one giant diff.
- **Bill commits; you don't.** Stage if helpful; never `git commit`/`push` unless
  told in-session.
- **Do NOT run long, blocking, out-of-sight subagent passes.** A ~24-minute
  synchronous subagent pass this session was the one real process failure — Bill
  noticed the stall twice. Keep passes small and their progress visible; if you
  delegate, keep it short and check in. Prefer doing the module yourself over a
  black-box agent for anything under review.
- **If a subagent does a pass, re-check its work** — the gacalc tests subagent
  introduced 5 ty errors (over-broad base types where a concrete type was needed) and
  left some diffs unmade. Verify types compile *and* that edits actually landed.

## Gates (mvp's own, containerized)

Per this repo's `CLAUDE.md`: verification = the repo's own container gates, not an
in-sandbox run. After each module:

- **Format/typecheck:** `entrypoint/format.sh` (ruff check `--fix` + ruff format +
  `ty check` on `pgzero_gl` + `vol1` + `vol2`) — run it *inside the container* via the
  `make format` target (mirror `shell.sh` setup: `loadpackages.sh`, editable install,
  correct cwd — see gacalc CLAUDE.md's format-gotcha note about the `cd` living in the
  `bash -c`).
- **Tests:** `make test` (or the repo's suite target). Green before handing a module
  to Bill.
- Nested podman: every inner `podman run` needs `--cgroups=disabled` (transient
  add-run-revert per the standing arrangement); check `/dev/fuse` first.
- **No generated code in mvp** (unlike gacalc) as of this writing — so no
  generator-vs-output split to worry about. If that changes, apply the gacalc rule:
  fix the generator, check the emitted output against the standard, never hand-edit
  generated files.

## Suggested module order (refine after a look)

1. `pyproject.toml` — add `N` to `select`. Land the ruff config change first so the
   rest of the pass sees the violations. Leave the ports' `per-file-ignores` in place
   *for now* — retire its entries one at a time as each port module is cleaned (below),
   not up front.
2. Draft the `## Coding standard (Python)` section into this repo's `CLAUDE.md`
   (adapt gacalc's; note that the ports are now in scope, and keep the shrinking
   `per-file-ignores` rationale accurate) + a `README` Contributing pointer.
3. The first-party library core (`src/modelviewprojection/…` — the
   `InvertibleFunction` / Cayley-graph engine, shared with gacalc's `functions.py`;
   keep the two consistent).
4. First-party demos, then first-party assignments/tooling.
5. **The ports**, one module at a time — the biggest, highest-churn part. Per port
   module: rename (N + naming grammar), annotate, then retire the `per-file-ignores`
   entries it no longer needs (checking the load-bearing-idiom ones with Bill first,
   per the Scope section) and update the `CLAUDE.md` rationale. Each is its own
   review → commit unit; this is where "small, visible passes" matters most.
6. Final full-gate pass with the repo's **default** flags.

## Decisions (Bill, 2026-07-18)

- **Scope: everything, ports included.** See Scope section.
- **`CLAUDE.md`: COPY gacalc's standard into mvp and adapt as needed** — not a
  cross-repo reference. Accepts drift between the two copies as the cost of each repo
  being self-contained.
- **`E722`: fixed, not kept.** Bare `except:` is not allowed; `except Exception:` is
  the replacement. All 10 sites were sound/music guards with `pass` — the documented
  rationale was accurate, but the fix is strictly better (a bare except also swallows
  `KeyboardInterrupt`/`SystemExit`, so Ctrl-C during a game could be eaten). Done.
- **`line-length = 80` is the target for mvp** — Bill builds a PDF of this repo, so 80
  is a real constraint, not a preference. `format.sh` already formats at 80; the lint
  config leaves `line-length` unset so **E501 fires at 88**. Close the gap by setting
  `[tool.ruff] line-length = 80`. **Cost, measured:** that turns on **71 new E501 in
  `src`** and 2 in `assignments` (both are 0 at 88), plus 1557 in `codetheclassics` and
  7 in `openglsuperbiblev4` — the ports already ignore E501, so they are unaffected.
  The 71 are lines `ruff format` cannot break (long comments, strings, URLs) and need
  hand reflowing. **Do this as part of the first-party pass, not before** — setting it
  earlier just makes the gate red while unrelated work is in flight.
- **E501 on the ports: stays ignored** for `codetheclassics` (1303 long teaching
  comments at 88, 1557 at 80). Retiring it for `openglsuperbiblev4` alone remains cheap
  (3 at 88, 7 at 80) — split the `ports/**` entry per-port.

## Cross-repo: `f(x) = m*x + b` named parameters

Bill wants `translate` / `uniform_scale` called with their keyword names
(`translate(b=e_1 + 3*e_2)`) to make the line-equation connection explicit. The
parameters are **already** named `b` and `m` in gacalc; the work is docstrings plus
**214 call sites in this repo** (276 across both). Tracked in geometricalgebra's
`tasks/mx-plus-b-named-parameters.md` — it owns the API and the docstrings; this repo
supplies most of the call sites. **Open scope question there:** whether every call site
converts, or only the teaching-facing ones (demos/notebooks/assignments), leaving
library internals positional.

## Still open

- **The 4 `F841`s in `leadingedge.py`** — see the section below; possible rendering bug,
  needs Bill's read.
- **mvp-specific rules the gacalc standard doesn't cover.** Candidates to propose once
  the first-party read happens (all unverified guesses at this point, listed so the
  question isn't lost): OpenGL/PyOpenGL conventions (GL constants vs `int` typing — the
  live `ty` diagnostic at `runner.py:72` is exactly this), matrix/coordinate conventions
  (row vs column, the `pyMatrixStack` idiom), the gacalc vector dialect (already
  documented in `CLAUDE.md`'s ports section — the standard should point at it rather
  than restate it), and the behaviour-faithful-port rule as a *coding* constraint
  (structure may change, observable behaviour may not).

## Measurement pass (2026-07-18) — the doc's premise about the ports was wrong

Ran ruff read-only with `--isolated` (bypasses `per-file-ignores`; mvp sets no
`line-length`/`target-version`, so isolated defaults match the repo's).

**`N` (naming) by area — the crater is first-party, not the ports:**

| area | N |
|---|---|
| `src/modelviewprojection/` | **86** |
| `ports/codetheclassics/` | 7 |
| `ports/openglsuperbiblev4/` | 4 |
| `assignments/` | 0 |

The Scope section above says the ports are "full of camelCase like `WIDTH`/
`numGhosts`/`gameState`" and treats them as the big naming job. **They aren't** — 11
violations across 49k lines of ported code. The camelCase is in first-party code:
N806 21, N803 17, N813 14, N816 12, N802 10. First-party order by count: `demos` 27,
`pyMatrixStack.py` 18, `plotsforbook` 14, `mvpvisualization` 11, `wxapp.py` 6,
`notebooksrc` 4, `cayley` 3, `util` 2, `mathutils.py` 0, `framebuffer` 0.

**So the plan's step order inverts:** the ports are a short mechanical cleanup plus
two config decisions; first-party naming is the real judgment work.

**What each `ports/**` ignore actually hid:** E501 1306 (**1303 of them in
`codetheclassics`; only 3 in `openglsuperbiblev4`**), S311 145, T201 91, E711 20,
UP007 15, UP035 13, B007 12, E722 10, E402 6, E741/B008/F841 4 each, E731 1,
**E712 0**.

Decisions this supports:
- **E501: keep ignored for `codetheclassics`** (1303 long teaching comments — the
  high-churn/low-value case). **Split the `ports/**` entry per-port and retire E501
  for `openglsuperbiblev4`** — 3 violations, essentially free.
- **E712 suppresses nothing — delete the entry.**
- S311 / T201 / E402 keepers as documented. E722 (10 bare excepts) still needs eyes.

## Ports cleanup — done 2026-07-18 (commit 2fb0f499), 68 of 73 fixed, 21 files

Fixed: UP007/UP006/UP035 44 (incl. 15 dead `typing` imports; UP006 was needed because
fixing the import without rewriting `Tuple[...]` usages would NameError, and UP006 is
not in `select` — add it), E711 20, B007 12, B008 4, E741 4, E731 1. Verified zero
F821, all touched files compile. `per-file-ignores` NOT yet touched — retire entries
in a follow-up now that the violations are gone.

**`B008` was a real latent bug, not a lint nit.** gacalc's `Vector2` is
`@dataclass(slots=True)` but **not frozen** — mutable. `beatstreets` had
`half_hit_area: Vector2 = Vector2(25, 20)` and stored it **by reference with no copy**,
so every fighter shared one object. Fixed with a `None` sentinel.

### Open — 4 `F841` in `leadingedge.py` may be a rendering bug, deliberately not deleted

`prev_yellow_line_{left,right}_{outer,inner}_screen` are assigned beside
`prev_track_screen` / `prev_rumble_*` (which *are* used) under the comment "Store
screen positions ... as they form half of the polygon for the next track piece."
Either the yellow-line rendering lost its use of them, or it should be using them.
Needs Bill's call — do not silently delete.

### Resolved — named default constants + defensive copy (replaces the `None` sentinels)

First attempt used `X | None = None` sentinels. Bill flagged the resulting
`self.dir = Vector2(*dir) if dir is not None else Vector2(0, 0)` in `kinetix`: that
class had **already** neutralized the shared default by copying, with a class comment
saying so ("and the dir param is defensively copied"), so the sentinel was a busier
line for a hazard the code had solved. *Lesson: a signature change to satisfy a lint
rule can force unrelated body edits — check whether the flagged hazard is already
handled before changing the signature.*

Final shape, applied to all four B008 sites:

- **Module-level named constant** for the default: `DEFAULT_HALF_HIT_AREA`,
  `DEFAULT_ENEMY_SPEED` (beatstreets), `DEFAULT_BALL_DIR` (kinetix).
- **Defensive copy on assignment** — `self.half_hit_area = Vector2(*half_hit_area)`,
  `self.speed = Vector2(*speed)`, `self.dir = Vector2(*dir)` — reusing the idiom
  kinetix already documented.

**The constant alone fixes nothing** — B008 only flags *calls* in defaults, so a bare
name silences the lint while every instance still shares one object. The copy is the
part that fixes it. Don't let a future pass "simplify" the copy away.

Signatures stay `Vector2` (no `| None`), and `speed` picked up a copy it was missing:
the base stored `self.speed = speed` by reference too.

**Scale of the original hazard (verified):** in beatstreets, `Player`, `EnemyVax`,
`EnemyHoodie`, and `EnemyScooterboy` all omit `half_hit_area`, so every instance of
all four shared one `Vector2(25, 20)`. Only `EnemyBoss` and `EnemyPortal` pass their
own. **No code mutates it today** — all uses are `.x`/`.y` reads — so this was a live
trap, not a live bug. (An earlier note here called it "a real bug"; that oversold it.)

### RETRACTED — "the ports are NOT ruff-formatted" was a measurement error

An earlier note here claimed 97 of 133 port files would reformat, and that
`pyproject.toml`'s "the ports are ruff-FORMATTED" comment was stale. **Both wrong.**
`entrypoint/format.sh` formats with **`--line-length=80`**; the measurement used
ruff's default 88. At the correct width: **130 of 133 already formatted**, and the 3
that drifted were this task's own edits. The pyproject comment is accurate — leave it.

*Lesson: when checking whether a repo's own gate is satisfied, invoke the tool the way
the gate does. `ruff format --check` without the gate's flags measures a different
question.* Note the repo runs the formatter at 80 but leaves the linter's `line-length`
unset (E501 fires at 88) — that gap is real and worth a decision, but it is not drift.

### Gate run 2026-07-18 — ports green; two pre-existing failures unrelated to this task

Run in-container (`--cgroups=disabled`, nested podman).

- **`ruff check ports` → All checks passed.**
- **`ruff format --line-length=80 ports` → 133/133 formatted** (3 files fixed, all
  from this task's edits).
- **`ty check` on the ports → 1 diagnostic, pre-existing:**
  `pgzero_gl/runner.py:72` `glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)`
  — "Expected `int`, found `Constant`", a glfw/PyOpenGL stub mismatch. This task's only
  edit to that file was `Dict`/`Tuple` → `dict`/`tuple`; line 72 is untouched.
- **`make format` itself does NOT currently run**, for a reason unrelated to this task:
  `loadpackages.sh`'s editable install fails with `ModuleNotFoundError: No module named
  'setuptools'` under uv's build isolation. Needs `setuptools` in
  `build-system.requires` (or `[tool.uv.extra-build-dependencies]`). **The repo's
  primary gate is red on `master` independent of this work** — worth its own task.

Two ruff warnings also surface each run: `E231`/`E302` in `select` "have no effect
because preview is not enabled".

## 80-column pass — done 2026-07-18 (uncommitted)

`[tool.ruff] line-length = 80` added to `pyproject.toml`, governing **both** the
formatter and E501; the four now-redundant `--line-length=80` flags dropped from
`entrypoint/format.sh` so there is one source of truth. Ports unaffected (E501 stays
ignored there). Final state: `ruff check src assignments tests ports` → **All checks
passed**; `ruff format --check` → 209 files already formatted; everything compiles.

### The discretion calls (78 over-long lines, one instruction)

- **70 prose lines** (comments + docstrings) rewrapped automatically. No consultation.
- **2 `import a.b.c as name`** at 88 chars → `from a.b import name`. Identical binding,
  71 chars. A *different mechanism* than wrapping, because wrapping an import is ugly.
  (Side effect: re-sorted those two import blocks, fixed with `ruff --fix I001`. Safe
  here because they are matplotlib files — **not** the GL-loader files where import
  order is semantically load-bearing; see `cayley_gl.py:30-35`.)
- **1 f-string** split via implicit concatenation — cannot change the runtime value.
- **1 `//` comment inside a GLSL shader string** (`demo22.py:402`). Wrapping would have
  pushed half a comment onto a new line as **invalid GLSL** — the linter cannot see that
  it is shader source. Shortened the comment text instead.
- **4 lines of a hand-aligned 4x4 matrix** (`pyMatrixStack.py:426-429`). Kept long with
  `# noqa: E501` + a written reason. It already carried `# fmt: off`, so the alignment
  was deliberate, and in a book *about matrices* that layout is the documentation.
  Reflowing would have been compliant and actively worse.

### Defect found and fixed in that pass — orphaned comment words (Bill, 2026-07-18)

The first rewrap operated **per line instead of per paragraph**, so a line 1-2 chars over
was split in place, leaving a dangling fragment on its own line:

```
    # stored ``steps`` field stay typed tuple[Step, ...] for readers while
    # the
    # constructor accepts the broader input.
```

**Rule: never leave a comment line holding a single word / short fragment. Reflow the
whole paragraph, not the offending line.** Fixed in 11 paragraphs
(`cayleygraph`, `cayleyscene`, `softwarerendering` x4, `cayley_gl`, `coordinatesystems`
x2, `plot2d`, `test_gl_vector_unpacking`, `demo21`).

**Automating the repair was itself a trap, worth recording.** A "reflow every ragged
paragraph" pass matched **87** paragraphs — most being the author's own deliberate line
breaks in files the 80-col pass never touched. Narrowing to "reflows shorter AND contains
a stub line" still matched 28, and *still* caught content that must not be reflowed:
`demo22.py:66-71` is a **Controls:** list and `demo22a.py:258-263` is a face-index list —
joining those into a paragraph destroys them. Two more near-misses: merging a
commented-out code line into prose (`demo21.py:66-68`, caught and reverted), and
splitting a math formula mid-expression (`softwarerendering.py:43`, `|v1||v2|` /
`sin(theta)`, hand-fixed to preserve the notation and its double-spacing).
**Conclusion: prose reflow cannot be fully automated in this repo** — comment blocks
carry lists, banners, commented-out code, jupytext `# %%` cell markers, license headers,
`doc-region` markers, and math notation. Use an explicit allowlist of verified prose
paragraphs and read the before/after.
