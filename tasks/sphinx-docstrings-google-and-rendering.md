# Sphinx docstrings: Google style + clean autodoc rendering (mirror of the gacalc work)

**Status:** proposed — needs go-ahead. **Priority:** 6 **Difficulty:** 6
**Created:** 2026-09-26 (William Emerison Six <billsix@gmail.com>)

## BLUF

The `geometricalgebra` project (github.com/billsix/geometricalgebra) just did a "make the book's
autodoc render everything well" pass — full **napoleon-Google** docstrings + several Sphinx/LaTeX
rendering fixes. This book (`modelviewprojection`) has the **same** kind of Sphinx book (napoleon
on, autodoc over the package, lualatex PDF), and its package is **not** Google-style yet
(`src/modelviewprojection/mathutils.py` has 0 `Args:`/`Returns:`) and its `conf.py` lacks the
autodoc-typehints fix — so the same work likely applies here. "Done" = this book's package
docstrings are full-Google and `make docs` renders clean (0 substitution warnings, no undefined
cross-refs, no dropped glyphs). Assess against an actual build first (below).

## Context

Cross-project standard (see the where-logged decision, likely `python-coding-standard.md`):
**Google/napoleon is the maintainer's docstring standard.** gacalc adopted it; this book should too.

gacalc's worked example lives in that repo (github.com/billsix/geometricalgebra):
- `tasks/docstrings-for-sphinx.md` — the task, incl. the full-Google execution spec and the
  session operational notes (how to measure Sphinx warnings, the font facts, etc.).
- `tasks/reference/generated-docstrings.md` — the doctest conventions to follow (explicit unit
  coefficients, typed comparisons, type-annotations-not-assertions).
- `tasks/reference/symbolic-equality.md` — the "a value never `==` a bare number" doctest gotcha.

## What gacalc did (the pattern to mirror)

1. **Coverage sweep** — a docstring on every autodoc-rendered public symbol.
2. **docutils rendering fixes** — bare `|A|` / unbalanced `` ` `` in docstrings produce
   "undefined substitution" / "start-string without end-string" warnings; wrap the tokens in the
   `` `` `` code-role (or make ASCII math a `::` literal block). **Build the book FIRST and read the
   real warnings** — don't guess (gacalc's predicted `|A|` fixes were mostly moot).
3. **Undefined hyper-references (PDF)** — `autodoc_typehints = "none"` (so annotations aren't turned
   into unresolvable cross-refs; the types live in the Google `Args:`/`Returns:` prose) + make sure
   `api.rst` `automodule`s **every** package module so `:func:`/`:class:` refs resolve.
4. **Missing glyphs / font** — if lualatex logs `Missing character: ... <glyph>`, add a luaotfload
   fallback in `conf.py` `latex_elements['preamble']` to a font that has it (gacalc used DejaVu Sans
   by file). Only needed if this book uses Unicode glyphs the main font lacks — CHECK the build log.
5. **Full napoleon-Google rewrite** — `Args:`/`Returns:`/`Raises:`/`Example:` on **every** documented
   method (maintainer's chosen depth). Keep existing prose as summary+description; `self`/`cls` not
   in `Args:`; existing doctests move under `Example:`.

## What to do here (assess, then apply)

- [ ] Build the book (`make docs`) and capture the ACTUAL warnings — substitution, undefined
      hyperref (grep `-oE "Hyper reference .api:..."`, not `-c ... undefined`, which undercounts due
      to LaTeX line-wrap), `Missing character`, font-shape.
- [ ] Coverage audit of the package (`mathutils.py`, and whatever else `api.rst` documents).
- [ ] Full-Google rewrite of the package docstrings (0 → full `Args:`/`Returns:` per method).
- [ ] `conf.py`: add `autodoc_typehints = "none"`; ensure `api.rst` covers all package modules; add
      a font fallback only if the build shows a missing glyph.
- [ ] Verify: docstrings pass `pytest --doctest-modules`; `make docs` exit 0 with 0 substitution
      warnings; the app/tests still green.

## Open questions

1. Confirm the maintainer wants the full-Google depth here too (gacalc chose it), and whether the
   demos (`src/modelviewprojection/demos/*`) are in scope or just the library modules
   (`mathutils` and whatever `api.rst` renders).
