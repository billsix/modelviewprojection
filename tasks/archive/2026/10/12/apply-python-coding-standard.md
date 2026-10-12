# Apply the Python coding standard to modelviewprojection

**Status:** done 2026-10-12 (William Emerison Six <billsix@gmail.com>). Archived.
**Priority:** 4
**Difficulty:** 6
**Created:** 2026-07-18

## BLUF

Bring modelviewprojection up to the maintainer's shared Python coding standard — turn on the
ruff-enforced tier and fix the fallout, then apply the judgment-call tier module by module
across the first-party code *and* the ports, annotating generously and cleaning up names.
Done: the repo is ruff- and ty-clean at the standard, every documented decision below is
settled, and the durable rules now live in reference docs (this task is the lean work record).

The authored rules are no longer in this doc — they were harvested to:
- **mvp's own `tasks/reference/python-coding-standard-mvp.md`** — mvp's specializations and
  worked examples (line-length 80, the wx boundary, book-shorthand naming, the `m·x+b`
  keyword rule, composition style, GL/matrix conventions, the gacalc vector dialect,
  behaviour-faithful ports, mvp's inner-function precedents).
- the **shared** `runClaudeInContainer/tasks/reference/python-coding-standard.md` — the
  portable rules mvp's `CLAUDE.md` points at.
- **`tasks/reference/tests-and-gates.md` §6** — the bulk-edit playbook (the hard-won lessons).

## What was done

- **Enforced tier.** `N` (pep8-naming) enabled repo-wide, every violation fixed by renaming
  (0 violations remain); `line-length = 80` set in one `pyproject.toml` key governing both
  `ruff format` and E501 (80 because the book is a PDF). `make format` green.
- **Annotation sweep (2026-07-19): 439 → 0.** Every function in `src/modelviewprojection`
  (65 files) carries typed params + return; a separate checker enforces every local and
  module-level binding is annotated. Domain type aliases added (`GLenum`, `Mesh`/`GLHandle`/
  `VertexCount`, …). `ty check src` added zero new diagnostics.
- **`CLAUDE.md` standard section + `README` Contributing pointer** written 2026-07
  (later restructured — see "the full split" below).
- **Ports (the high-churn half).** Lint cleanup (UP007/UP035, E711, B007/B008, E741, E731);
  **E722 fixed, not kept** (`except Exception:`); the **B008 shared-mutable-default** latent
  bug fixed with module-level named defaults + defensive copy; **E501 retired for
  `ports/openglsuperbiblev4/`** (six comment paragraphs reflowed whole, one 107-char
  annotation replaced by the `Point3`/`PlanePoints` PEP-695 `type` aliases) while **kept for
  `ports/codetheclassics/`** (1567 teaching-comment lines) — done by splitting the broad
  `ports/**` ignore into per-port scoped entries; **ten per-file-ignores that suppressed
  nothing deleted** (E711/E712/B007/UP035/E722/E741/E731/B008/F841/UP007).
- **`m·x+b` named-parameter conversion (2026-10-12): all 88 first-party call sites.**
  gacalc's `translate`/`uniform_scale` are now called `translate(b=…)` / `uniform_scale(m=…)`
  to make `f(x) = m·x + b` explicit. Done by a one-shot AST + doctest codemod that
  discriminated by call shape (one positional arg = gacalc's) so the four-arg
  `matrix_stack.translate(stack, x, y, z)` was correctly left positional; `rotate`/
  `scale_non_uniform` untouched. Verified: ruff clean at gate scope, 74 doctests/tests pass.
- **mvp-specific rules + inner-function-first precedents** written, then relocated by the
  full split (below). The verified mvp precedents are `CayleyGraph._route` and
  `_assert_acyclic`; `mathutils.ortho`/`perspective`'s `f`/`f_inv` are flagged non-precedents.

## Decisions (William Emerison Six <billsix@gmail.com>)

- **Scope = everything, ports included** (2026-07-18). Nothing exempt (unlike gacalc's
  vendored Emacs tree). The ports were a short mechanical cleanup + two config calls; the
  real judgment work was first-party naming.
- **An externally-defined name overrides the naming rules** — wx's `OnPaint`/`OnTimer`/…
  and `attribList=` are matched exactly and scoped-ignored, with the reason at the site.
- **`E722` fixed, not kept** — a bare `except:` also swallows `KeyboardInterrupt`/`SystemExit`.
- **E501: kept for `codetheclassics`, retired for `openglsuperbiblev4`** (3 vs 1303 long
  lines at 88) — split the `ports/**` ignore per-port.
- **The ten unused ignores: deleted** (2026-09-09) — a retired ignore must not stay
  documented as live; re-add a single rule with a reason if a future upstream import trips it.
- **`m·x+b` conversion scope = every first-party call site** (2026-10-12), not only the
  teaching-facing ones.
- **The full split (2026-10-12).** The 2026-09-13 trim had moved mvp's rules *into* the
  shared standard; that was reversed — the shared doc is now portable-only and mvp's rules
  live in `tasks/reference/python-coding-standard-mvp.md`. Tracked in runClaudeInContainer
  `tasks/split-python-standard-project-specifics.md`.

## Hard-won lessons (full detail in `tasks/reference/tests-and-gates.md` §6)

Bulk `def`-signature rewrites damaged source twice before the rules were pinned: find a
signature's end with the AST (never text), re-apply indentation, preserve trailing comments,
**derive the replacement from the source** (a hardcoded table invented a `self` param — ruff
and ty both passed; only launching the app caught it), and verify def-counts + per-function
parameter lists are identical before/after. **Run the artifact, not just the checkers.** And
**prose reflow cannot be fully automated here** — comment blocks carry lists, banners,
commented-out code, jupytext markers and math notation; use a read allowlist.
