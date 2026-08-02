# Expand the glossary from the whole book, with accessible external references

**Status:** complete
**Completed:** 2026-08-02
**Created:** 2026-08-02

Completed work record. The reusable **how-to** (definition voice, the source-accessibility
criterion, the `:term:`-linking rules, the gates) was harvested to
`tasks/reference/glossary-authoring.md`. Bill's remaining **voice-review** of the drafted
definitions is tracked separately in `tasks/glossary-definitions-voice-review.md`.

## Goal

Sweep the entire book, decide which terms deserve a glossary entry, and for each: add a
book-derived definition (in the course's voice), a **vetted accessible** external reference,
`:term:` cross-links, and a `:term:` link on every prose occurrence.

## What was done (2026-08-02)

- **Term selection.** Whole-book sweep → curated candidate list → Bill approved the whole
  *Recommend* set plus a chosen subset of *Borderline* (Frame/Hertz, Window, Monitor, GLFW,
  Non-commutativity of rotations, Z-fighting, OpenGL Core Profile, Standard perspective
  matrix); the rest skipped. (The full approved/rejected breakdown is in git history for
  this file if needed.)
- **Entries assembled.** ~56 new entries drafted (5 parallel readers) + the 6 pre-existing
  entries given "Further reading" links → **69 terms total** in
  `book/docs/glossary.rst`, as a `.. glossary:: :sorted:` block. Each has a book-voice
  definition, `:term:` cross-links, and a vetted accessible source (caveated where only a
  technical source exists).
- **Book-wide `:term:`-linking pass.** 6 parallel readers over non-overlapping chapter sets.
  **714 `:term:` uses across the book** (206 glossary cross-links + ~508 in-prose;
  ~450 newly added). Verified: every `:term:` target resolves (0 orphans), 0 links in
  section headings, code/`literalinclude`/RST-hyperlink refs left intact.
- **Spelling.** New proper nouns (Scratchapixel, songho, Zucconi, …) added to
  `book/docs/mvp_dict.pws`.
- **Committed** across `added glossary` / `working on glossary` / `added references to
  terms` (fold these together when squashing).

## Verification

Confirmed in the nested-container `make html` (2026-08-02): build succeeds, glossary renders,
`:term:` targets resolve. Definitions were committed as **drafts in Bill's voice** — refining
them is the follow-up review task above, not a defect in this work.

## Follow-ups spawned

- `tasks/reference/glossary-authoring.md` — the durable methodology.
- `tasks/glossary-definitions-voice-review.md` — Bill's voice-review of the 69 definitions,
  carrying the reader-flagged notes (ch06 `Spaces's` typo, unlinked "lambda stack",
  loose `ortho` match, skipped figure captions).
