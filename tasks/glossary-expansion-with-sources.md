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

## Phase 1 — candidate terms from the whole-book sweep (2026-08-02)

**APPROVED 2026-08-02.** Bill approved the whole *Recommend* set as-is; from
*Borderline* he said **yes** to: Frame/frame-rate/Hertz, Window, Monitor, GLFW,
Non-commutativity of rotations, Z-fighting, OpenGL Core Profile, Standard
perspective matrix; **no** to the rest (Flushing, Clear color, Immediate mode,
Left-handed coordinate system, Premultiplication, Unit vector, rotate_around,
Continuous vs discrete space). *Suggest skip* set: all skipped. Template terms:
**Cayley Graph** + **Camera Space** (Phase 2 below). Existing entries (Frame Buffer, NDC, World
Space, Modelspace, Screen Space, Event Loop) get "Further reading" links too but
aren't relisted. Chapters cited are where the book introduces/leans on the term.

**Recommend — core course abstractions**
- Cayley graph (ch02) · Invertible function (ch02) · Function composition (ch02)
- Inverse of a transformation (ch10) · Coordinate system / space (ch02)
- Change of basis / coordinate conversion (ch02) · Transformation (ch04)
- Affine function (mathhomework1) · Function stack / lambda stack (ch16)

**Recommend — spaces (new)**
- Camera space (ch10) · Clip space (ch19/perspective)

**Recommend — transform primitives**
- Translation (ch04) · Scaling (ch06) · Rotation (ch07) · Identity (ch19)

**Recommend — vectors & geometry**
- Vertex (ch02) · Natural basis / basis vector e_1,e_2,e_3 (ch05/ch14)
- Origin (ch05) · Right-hand rule (ch14) · Vector (Vector2/Vector3) (ch04/ch14)

**Recommend — projection & camera**
- Orthographic projection (ch17) · Perspective projection (ch18) · Frustum (ch18)
- Field of view (ch18) · Near/far plane (ch18) · Aspect ratio (ch18)
- Homogeneous coordinate / w / perspective divide (perspective) · Clipping (ch06)
- View volume / viewable region (ch17) · Virtual camera (ch10)

**Recommend — rasterization, fragments, buffers**
- Pixel (ch01) · Fragment (ch03/ch15) · Depth buffer / Z-buffering (ch15)
- Depth test (ch15) · Stencil buffer (ch15) · Viewport (ch01) · Rasterization (ch20)
- Double buffering / swap buffers (ch01) · Scissor test (ch03)

**Recommend — shaders & modern GL**
- Shader (ch20) · Vertex shader (ch20) · Fragment shader (ch20) · GPU (ch20)
- Fixed-function pipeline (ch20) · Matrix stack (ch19) · Model-view matrix (ch19)
- Projection matrix (ch19)

**Recommend — CS concepts the book teaches**
- First-class functions (miscellany) · Partial application (mathhomework1)
- Black box vs white box (mathhomework1)

**Borderline — your call**
- Frame / frame rate / Hertz (ch01) · Flushing (ch01) · Clear color (ch01/03)
- Window (ch01) · Monitor (ch01) · GLFW (ch01) · Immediate mode (ch02)
- Left-handed coordinate system (ch19) · Premultiplication (ch19)
- Non-commutativity of rotations (ch17) · Z-fighting (perspective)
- Unit vector (ch05) · rotate_around (ch08) · OpenGL Core Profile (ch20/21)
- Continuous vs discrete space (ch02) · Standard perspective matrix (perspective)

**Suggest skip (reason)**
- Keyword arguments (Python feature, not graphics) · OpenGL context (book
  de-emphasizes it) · Group theory / Abstract Algebra (cited as a source, not a
  course term) · theta (notation) · Quad/quadrilateral (basic) · Unit test
  (tooling, not graphics) · MVP pipeline (the book's subject, meta)

## Phase 2 — template approved, full pass underway (2026-08-02)

Bill signed off on the shape (Cayley Graph + Camera Space entries + the ch10
sample link): definition voice, "Further reading:" format, caveat handling, and
`:term:` link syntax all **good as-is**. Also: **videos OK** in Further reading;
glossary switched to **`.. glossary:: :sorted:`** (Sphinx auto-alphabetizes, so
source order no longer matters). Executing the rest in thematic batches
(definitions from the book + vetted accessible source per term), then the
book-wide `:term:`-linking pass. Definitions remain drafts for Bill; `make html`
+ aspell are his gates.

## Phase 2 progress — entries assembled (2026-08-02)

All ~56 approved new entries drafted (5 parallel readers) and assembled into
`glossary.rst`: **69 glossary terms total**, each with a book-voice definition,
`:term:` cross-links, and a vetted "Further reading" source (accessible-first;
caveated where only a technical source exists — songho/scratchapixel/Wikipedia
math pages). Verified: every one of the 206 `:term:` references resolves to a
defined term, no duplicate headers. New proper nouns added to `mvp_dict.pws`
(Scratchapixel, songho, Zucconi, …). Definitions are drafts for Bill's voice;
`make html` + aspell are his gates (can't build in-sandbox).

**(1) + (2) DONE 2026-08-02.**

- **(1)** "Further reading" links added to all 6 pre-existing entries
  (Framebuffer/Event-loop → Wikipedia; the spaces → LearnOpenGL). All 69 terms
  now have a source.
- **(2)** Book-wide `:term:`-linking pass complete (6 parallel readers over
  non-overlapping chapter sets). **714 `:term:` uses across the book now** (206
  glossary cross-links + ~508 in-prose links across 24 chapter/section files;
  ~450 newly added). Verified: **every `:term:` target resolves** to a defined
  glossary term (0 orphans), **0 links in section headings**, and RST hyperlink
  references (`inverse_`, `GLFW_`, `Nintendo_`, …) and `literalinclude`/code
  blocks were left intact. Density judgment applied (conceptual terms linked
  densely; common words like "vertex"/"frame" first-use-per-section).

Definitions are drafts for Bill's voice; **`make html` + aspell are his gates**
(can't build in-sandbox — the aspell run may surface a few more words to add to
`mvp_dict.pws` beyond the ones already whitelisted).

Reader-flagged notes for Bill (not blockers): a source typo `Spaces's` in ch06;
the informal "lambda stack" left unlinked (not a `Function Stack` word-match);
`ortho`→Orthographic Projection is a loose (abbreviated) match; figure captions
were skipped uniformly (linkable later if wanted).

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

## Decisions (Bill, 2026-08-02)

- **List-first, curated by approval.** Sweep the whole book, propose a curated
  candidate term list (term + where introduced + why it belongs) for Bill's
  yes/no; the approved set *is* the curation bar (no separate abstract rule).
- **Template batch.** After approval, do 1–2 terms end-to-end (definition +
  vetted "Further reading" link + prose-linking) and get Bill's sign-off on the
  shape before batching the rest.
- **Link format:** a short **"Further reading: <link>"** line per entry (with an
  accessibility note where relevant) — standard glossary shape.
- **No accessible source:** **still link the canonical source, but with a
  caveat** (e.g. "(technical / assumes group theory)") — don't omit.
- **Link every instance** of a term in the prose (not just first-use), matching
  Bill's existing practice; over-linking is deletable later.
- **Existing 6 entries** (Frame Buffer, NDC, World Space, Modelspace, Screen
  Space, Event Loop) also get "Further reading" links in this pass.
- Definitions are **drafts in Bill's voice for him to refine**, written into
  `glossary.rst`; `make html` + aspell are his gates.
