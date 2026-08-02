# Voice-review the drafted glossary definitions

**Status:** open — deferred, for Bill (the definitions are his voice to set)
**Created:** 2026-08-02

## What

The 2026-08-02 glossary expansion added **69 terms** to `book/docs/glossary.rst`, each with a
book-derived definition, a vetted "Further reading:" link, and `:term:` cross-links. The
definitions were **AI-drafted from the book's own explanations** and committed as drafts.
This task is Bill's pass to **refine those definitions into his own voice** — the book prose
is his, and the drafts are a starting point, not final wording.

Conventions for the glossary (definition voice, the source-accessibility criterion, the
`:term:`-linking rules, the gates) live in `tasks/reference/glossary-authoring.md`. The
completed expansion work is recorded in
`tasks/archive/2026/08/02/glossary-expansion-with-sources.md`.

## Scope

- Read each of the 69 entries in `book/docs/glossary.rst`; rewrite wording where it doesn't
  sound like you. The *structure* (definition + Further-reading + cross-links) can stay;
  it's the prose voice to adjust.
- Re-check that each "Further reading:" source still meets the accessibility criterion
  (programmer/student audience, not mathematician — see the reference doc) and that any
  caveat reads the way you want.

## Reader-flagged notes to resolve (not blockers, surfaced during the pass)

- **`Spaces's`** — a source typo in `book/docs/ch06.rst` (spotted while linking; fix in prose).
- **"lambda stack"** — the informal phrase was left **unlinked** (it isn't a literal
  `Function Stack` word-match). Decide whether to link it to `Function Stack` or leave it.
- **`ortho` → Orthographic Projection** — a loose (abbreviated) `:term:` match; confirm you
  want the abbreviation linked to the full term.
- **Figure captions** — `:term:` linking was skipped uniformly in captions; linkable later
  if you want them.

## Gate

`make html` (in-container) + aspell, as usual — the aspell run may surface a few more words
to add to `book/docs/mvp_dict.pws` beyond those already whitelisted.
