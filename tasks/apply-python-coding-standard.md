# Apply the Python coding standard to modelviewprojection

**Status:** proposed — needs go-ahead
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
- **Inner-function-first (Scheme-style) shape**, project conventions, the full idiom
  checklist — carry over from gacalc's section; adapt examples to mvp.

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

## Open questions for Bill

- Which port `per-file-ignores` entries are **load-bearing idioms to keep** vs
  **upstream sloppiness to fix**? (See the Scope section's list — F403/F405, E402,
  S311 are the likely keepers; naming/F841/E711/UP035/missing-annotations are the
  likely fixes. Confirm before deleting each.)
- Retire **E501** on the ports (reflow long upstream teaching comments)? High churn,
  low value — default is to leave E501 ignored on the ports unless Bill wants it.
- Should mvp's `CLAUDE.md` **copy** the standard, or **reference** gacalc's? (Bill's
  gacalc decision was per-repo canonical `CLAUDE.md`; copying keeps mvp
  self-contained but risks drift with gacalc's copy.)
- Any mvp-specific rules to add that gacalc's standard doesn't cover (OpenGL/matrix
  conventions, pgzero idioms)?
