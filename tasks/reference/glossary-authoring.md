# Authoring & maintaining the book glossary

**What this is:** the durable conventions for writing glossary entries and linking terms
in the book — definition voice, the external-source accessibility criterion, the
`:term:`-linking rules, and the glossary mechanics. Read this before adding or editing a
glossary term, or doing another prose-linking pass. Harvested from the 2026-08-02
whole-book glossary expansion (work record:
`tasks/archive/2026/08/02/glossary-expansion-with-sources.md`).

The glossary lives in `book/docs/glossary.rst` as a `.. glossary:: :sorted:` block (Sphinx
auto-alphabetizes, so source order doesn't matter). As of 2026-08-02 it has 69 terms.

## Each entry has three parts

1. **A definition derived from the book itself**, written in the course's own
   voice/notation — the paddle-scene, Cayley-graph, invertible-function vocabulary — the way
   the chapter that introduces the term explains it. Match the existing entries' style
   (Frame Buffer / NDC / World Space / Modelspace / Screen Space / Event Loop). Definitions
   are **Bill's voice**; AI drafts are drafts until he refines them.
2. **A "Further reading:" line** — one external link (Wikipedia/tutorial/video), vetted by
   the accessibility criterion below, with an accessibility note where relevant.
3. **`:term:` cross-links** to related glossary terms (e.g. World Space → Modelspace).

## The source-accessibility criterion (the crux)

**External links must be understandable to the book's audience — programmers/students
learning graphics, NOT mathematicians.** The canonical reference is often too abstract.

- **Worked example / the trap: Cayley graph.** The
  [Wikipedia article](https://en.wikipedia.org/wiki/Cayley_graph) opens *"a graph that
  encodes the abstract structure of a group"* and dives into generating sets, group actions,
  and geometric group theory — impenetrable to a non-mathematician, no intuition first.
  Linking it as-is sends the reader somewhere *more* confusing than the book.
- **When the canonical source is too advanced**, in order of preference:
  1. find a gentler source (a tutorial, a visual explainer, a "for programmers" write-up);
  2. link the canonical one **with a caveat** ("(rigorous / assumes group theory)") *and* a
     gentler starting point;
  3. **omit the external link** rather than mislead — a book definition with no link beats a
     link that loses the reader.
- Prefer sources that lead with intuition/pictures over formal definitions. Note per source
  whether it's introductory or advanced. Videos are acceptable.
- Sources used in the 2026 pass, caveated where only a technical one existed: LearnOpenGL,
  Math is Fun, songho, Scratchapixel, Alan Zucconi, MDN, Wikipedia (math pages caveated).

## Linking terms in the prose (`:term:`)

**Every occurrence of a glossary term in the prose should be a `:term:` link** to its entry
— not just the first use. (Bill's stated preference; over-linking is deletable later.)

- **Syntax** — use the display form so casing reads naturally:
  `` :term:`modelspace <Modelspace>` `` (lowercase display, `Modelspace` target),
  `` :term:`NDC <Normalized Device Coordinates>` ``. A bare `` :term:`Frame Buffer` `` when
  the text casing already matches the entry title.
- **Method, per term:** `grep` the raw word occurrences, subtract those already inside a
  `:term:` (and the excluded contexts below), convert the rest.
- **Do NOT link** (leave as raw text):
  - occurrences inside `literalinclude`d code or `::` code blocks (that's source, not prose);
  - `doc-region` markers and comments;
  - the term inside its **own** glossary definition (self-link);
  - section **headings/titles** — a `:term:` in a heading is awkward and can break the
    toctree label; link the first prose use instead.
- **Density judgment:** conceptual terms (Cayley graph, invertible function) can be linked
  densely; common words (vertex, frame) read better linked first-use-per-section. Default to
  "all instances" unless it looks cluttered; flag any spot where you deviate.
- Also distinct from `:term:`: RST hyperlink references like `inverse_`, `GLFW_`,
  `Nintendo_` are external-URL links, not glossary links — leave them intact.

## What earns an entry

A term earns an entry if a reader would plausibly look it up — not every technical word. The
curation bar is *by approval*: sweep the book, propose a candidate list (term + where the
book introduces it + why it belongs), and the approved set is the bar. (Skipped in 2026:
Python-feature words like keyword arguments, tooling like unit test, meta terms like "the
MVP pipeline", notation like theta.)

## Gates

- **`make html` in the container is the real gate** — external URLs, `:term:` targets, and
  spelling are all checked there. Can't build in-sandbox (`texExpToPng` absent), so the
  build is Bill's.
- **aspell:** new prose adds words — add real new terms/proper nouns to
  `book/docs/mvp_dict.pws` (bump its `personal_ws-1.1 en <N>` header count). Enumerate the
  additions non-interactively with `aspell --personal=./mvp_dict.pws list < file`.
- **Book prose is Bill's voice** — deliver definitions as drafts for his review, not final
  wording. (Pending review of the 69 drafted definitions is tracked in
  `tasks/glossary-definitions-voice-review.md`.)
