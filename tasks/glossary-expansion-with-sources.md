# Expand the glossary from the whole book, with accessible external references

**Status:** proposed — needs go-ahead (Bill, 2026-08-02). A book-wide pass, and
the definitions are book prose (Bill's voice), so drafts need his review.

## Goal

Go through the **entire book** (`book/docs/ch*.rst`, `perspective.rst`,
`mathhomework*.rst`, etc.), decide which terms deserve a glossary entry, and for
each:

1. **Add a definition derived from the book itself** — write it in the course's
   own voice/notation (the paddle-scene, Cayley-graph, invertible-function
   vocabulary), the way the chapter that introduces the term explains it. Match
   the existing `book/docs/glossary.rst` entries' style (see Frame Buffer / NDC /
   Screen Space / Event Loop, and the World Space / Modelspace drafts added
   2026-08-02 in `tasks/archive/2026/08/02/book-config-cruft.md`).
2. **Add an external reference** for further reading (Wikipedia or similar) —
   **but vetted for accessibility** (see the criterion below).
3. **Cross-link related terms** with `:term:` (e.g. World Space → Modelspace).
4. **Link the term throughout the book prose** — see the dedicated section
   below; this is a first-class requirement, not an afterthought.

## Link every glossary term occurrence in the prose (Bill, 2026-08-02)

Every occurrence of a glossary term in the book's prose should be a `:term:`
link to its glossary entry — e.g. **every "modelspace" in the text links to the
`Modelspace` entry**, not just the first. Bill has already done a large chunk of
this (as of 2026-08-02: ~52 `:term:` links to `Modelspace` exist, but ~150 raw
"modelspace" word occurrences — so it's a **fill-in-the-gaps** pass, not
from-scratch). Do the same for every term the glossary defines.

- **Syntax** — use the established display form so casing reads naturally:
  `:term:`modelspace <Modelspace>`` (lowercase display, `Modelspace` target),
  `:term:`NDC <Normalized Device Coordinates>``. A bare `:term:`Frame Buffer``
  when the text casing already matches the entry.
- **Method** — per term: `grep` its raw word occurrences, subtract those already
  inside a `:term:` (and the excluded contexts below), and convert the
  remainder.
- **Do NOT link** (leave as raw text): occurrences inside `literalinclude`d code
  or `::` code blocks (that's source, not prose); `doc-region` markers and
  comments; the term inside its **own** glossary definition (self-link);
  and section **headings/titles** (a `:term:` in a heading is awkward and can
  break the toctree label — link the first prose use instead).
- **Judgment on "every instance"** — Bill's stated preference is to link them
  all; if per-paragraph repetition ever reads as noisy, link at least the first
  use in each section, but default to his "all instances" unless it looks
  cluttered (flag any spot where you deviate).

## The source-accessibility criterion (the crux — Bill, 2026-08-02)

**External links must be understandable to the book's audience** — programmers /
students learning graphics, **not** mathematicians. The canonical reference is
often too abstract.

- **Worked example — Cayley graph.** The [Wikipedia
  article](https://en.wikipedia.org/wiki/Cayley_graph) opens: *"a graph that
  encodes the abstract structure of a group"* and dives straight into generating
  sets, group actions, and geometric group theory — impenetrable to a
  non-mathematician, and with no intuition or analogy first. Linking it as-is
  would send a reader somewhere more confusing than the book. **This is the trap
  to avoid.**
- **When the canonical source is too advanced**, in order of preference:
  (a) find a gentler source (a tutorial, a visual explainer, a "for programmers"
  write-up) that matches the reader's level; (b) link the canonical one **with a
  caveat** ("(rigorous / assumes group theory)") *and* a gentler starting point;
  or (c) **omit the external link** rather than mislead — a book definition with
  no link beats a link that loses the reader.
- Prefer sources that lead with intuition/pictures over formal definitions.
- Note per source whether it's introductory vs advanced, so the reader knows
  what they're clicking into.

## Method (suggested)

1. **Sweep every chapter** for terms the book introduces or leans on: candidates
   include *Cayley graph*, *invertible function*, *function composition*,
   *coordinate space* / *camera space*, *orthographic* & *perspective
   projection*, *frustum*, *vertex*, *fragment*, *shader*, *matrix stack*,
   *rotation / rotor*, *geometric algebra*, *dot / wedge / cross product*, *depth
   buffer*, *winding order*, … (enumerate for real during the pass — don't trust
   this list).
2. **Curate** — a term earns an entry if a reader would plausibly look it up, not
   every technical word (decide the bar with Bill; see Q2).
3. **Draft each definition from the book**, cross-link with `:term:`, add the
   vetted external link, and mark the drafts for Bill to refine (book voice is
   his).

## Constraints / gates

- **aspell**: new prose adds words — add real new terms to `book/docs/mvp_dict.pws`
  (bump its `personal_ws-1.1 en <N>` header count to match).
- **`make html`** (in-container) is the real gate — external URLs, `:term:`
  targets, and spelling all get checked there; run it before calling done. I
  can't build the book in-sandbox (`texExpToPng` absent), so the build is Bill's.
- **Book prose is Bill's voice** — deliver definitions as drafts for his review,
  not as final wording.

## Open questions

1. **External-link format in the glossary** — an inline "Further reading:
   <link>" line per entry, a `.. seealso::` block, or footnotes? (Recommend a
   short "Further reading:" line, with an accessibility note where relevant.)
2. **Scope / curation bar** — every technical term, or a curated set of the ones
   a learner would look up? (Recommend curated.)
3. **When no accessible source exists** — omit the link, or link the canonical
   one with a "(technical)" caveat? (Recommend omit-or-caveat per the criterion
   above; confirm the default.)
