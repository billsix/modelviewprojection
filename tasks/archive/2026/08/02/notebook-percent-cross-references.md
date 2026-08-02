# Percent-notebook ↔ Sphinx cross-references (labelled sections, RST hyperlinks)

**Status:** complete
**Completed:** 2026-08-02
**Created:** 2026-08-02

(Ongoing per-section labelling + inbound `:ref:` links are Bill's manual, as-needed
process — not tracked work. Durable knowledge lives in
`tasks/reference/notebook-sphinx-integration.md`.)

> **Durable "how it works" knowledge now lives in
> `tasks/reference/notebook-sphinx-integration.md`** (the pipeline, the nbsphinx/myst_nb
> handler situation, the label→ref→HTML mechanism, verification). This task is the work
> record.

## Progress / done (2026-08-02)

- **Top-level labels added and verified in generated HTML.** Each notebook now has a
  `(label)=` before its h1: `plot2dlabel`, `framebufferlabel` (pre-existing), `ndclabel`.
  A container `make html` produced `id="plot2dlabel"`, `id="framebufferlabel"`,
  `id="ndclabel"` in the respective pages, RC 0.
- **Orphans fixed (Q2 = "add to toctree").** `framebuffer` and `ndc` added to the
  `index.rst` toctree next to `plot2d`; no more "not included in any toctree" warnings.
- **nbsphinx removal (Q3 = "not yet").** Deferred to `tasks/consider-removing-nbsphinx.md`.
- **Section-level labels + inbound `:ref:` (Q1 = "only what I mark, manually").** Left to
  Bill as an as-needed manual process; the top-level anchors are ready to link against.

The steps/options below are retained for reference; the remaining open items are Q1/Q4/Q5
(all "manual/leave as-is" per Bill).

## Goal (Bill)

In the py:percent-format notebook scripts (`src/modelviewprojection/notebooksrc/*.py`),
be able to **label a section**, then **reference that label from the reStructuredText**
chapters, so the rendered HTML has a **hyperlink** into the notebook.

## TL;DR / assessment — you have already done this, and it works

The mechanism you want is **already in the repo and building correctly**:

- `src/modelviewprojection/notebooksrc/framebuffer.py:16` (a `# %% [markdown]` cell):
  ```python
  # %% [markdown]
  # (framebufferlabel)=
  # # Framebuffer
  ```
- `book/docs/ch01.rst:360` references it:
  ```rst
  ... (we will see the importance of this in :ref:`Framebuffer <framebufferlabel>`).
  ```
- Verified in a full nested-container `make html` (2026-08-02): the build succeeds
  and there is **no "undefined label: framebufferlabel"** warning — the `:ref:`
  resolves and produces the hyperlink.

So "everything looks ok": the pattern is correct and functioning. What's missing is
(a) you've only done it once, and (b) a few setup/robustness gaps below that will bite
as you add more.

## How the mechanism works (research)

- A jupytext **percent** `.py` file's `# %% [markdown]` cell is converted to a notebook
  **markdown cell**. `myst_nb` parses markdown cells as **MyST Markdown**, so MyST's
  target syntax works inside them.
- **`(label)=` on its own line immediately before a heading** creates a cross-reference
  target anchoring that section. This is standard MyST target syntax and needs no extra
  extension when it precedes a **heading**.
- **Reference it from RST** with the normal Sphinx role: `` :ref:`Display text <label>` ``
  (or `` :ref:`label` `` to use the heading text). From MyST/markdown you'd instead write
  `[Display text](#label)` or `` {ref}`Display text <label>` ``.
- Labels are collected **globally** by Sphinx, so a chapter can reference a label defined
  in any notebook regardless of toctree placement (see the orphan caveat below).

## What is set up now (findings, 2026-08-02)

1. **Three percent notebooks** exist: `notebooksrc/{plot2d,framebuffer,ndc}.py`.
   `entrypoint.sh` runs `jupytext --to notebook …` on each into `book/docs/*.ipynb`
   (gitignored) before the build.
2. **`myst_nb` is the active `.ipynb` handler.** The build emits MyST-NB's
   `_build/jupyter_execute/*.svg` execution artifacts, confirming myst_nb (not nbsphinx)
   parses and executes the notebooks. **This is why `(label)=` works** — nbsphinx would
   render the markdown cell with CommonMark and the MyST target would become literal text
   (a broken `:ref:`).
3. **`nbsphinx` is ALSO enabled** (`conf.py` extensions list has both `nbsphinx` and
   `myst_nb`). Normally two extensions both claiming `.ipynb` raise
   *"source_suffix '.ipynb' is already registered"*; here the build tolerates it and
   myst_nb wins, but the coexistence is fragile and confusing — a version bump could
   flip which one handles `.ipynb` and silently break every notebook `:ref:`.
4. **Only `plot2d` is in the toctree** (`book/docs/index.rst`). `framebuffer.ipynb` and
   `ndc.ipynb` are generated and built but **not referenced by any toctree** → they are
   orphaned pages. `framebuffer` is reachable only via the `:ref:` from ch01; `ndc`
   appears unreferenced entirely.
5. **`myst_enable_extensions = ["colon_fence", "dollarmath"]`** — note `attrs_block` /
   `attrs_inline` are **not** enabled, so today you can only anchor **headings**
   (`(label)=` before `#`). Labelling an arbitrary paragraph/figure/span would need
   `attrs_block`.
6. **`myst_heading_anchors` is NOT set**, so there are **no implicit heading anchors**.
   Consequence: the *only* way to make a section referenceable is an explicit `(label)=`
   before it. Set `myst_heading_anchors = 2` (or 3) and every h1/h2(/h3) gets an
   auto-slug you can `:ref:` without hand-writing a label — at the cost that renaming a
   heading silently breaks the link. Explicit `(label)=` is more stable; auto-anchors are
   less typing. (See open question 5.)

## Does it map cleanly? (direct answers to the follow-up, 2026-08-02)

- **Does the label→ref map cleanly?** Yes. `(framebufferlabel)=` → `:ref:`Framebuffer
  <framebufferlabel>`` resolves with no "undefined label" warning in a real build. The
  one explicit label you wrote works end to end.
- **Do the notebook section headings work correctly?** They render correctly, but note:
  - Each notebook has a single ATX h1 (`# # Plot 2D` / `# # Framebuffer` / `# # NDC`),
    then its subsections are **setext** headings (a line of text underlined with
    `---------`). Both ATX and setext render fine in MyST — no bug — just an
    inconsistent style if you care.
  - **Only `framebuffer.py` has a `(label)=`.** `plot2d.py` and `ndc.py` have plenty of
    section headings but **zero labels**, and with `myst_heading_anchors` unset those
    sections are **not referenceable** at all yet. So the headings "work" as headings,
    but they are not yet cross-reference targets.
  - `framebufferlabel` sits before the h1, so the ref lands at the **top of the
    framebuffer page** (a whole-notebook link), which is what you'd want for that case.
- **Does anything actually link to a notebook label?** Exactly **one** place:
  `book/docs/ch01.rst:360`. `plot2d` and `ndc` have **no inbound `:ref:` at all** (and
  `ndc` isn't referenced or in any toctree, so it's fully orphaned). So the feature is
  proven once and otherwise unused.

## Comparison: goal vs. current state

| Goal | Status |
|---|---|
| Label a section in a percent notebook | ✅ done once (`framebufferlabel`), pattern proven |
| Reference it from RST → HTML hyperlink | ✅ done once (ch01 → framebuffer), resolves |
| Do it broadly across notebooks | ⬜ only one label exists so far |
| Label finer-grained than a section header | ⬜ needs `attrs_block` (not enabled) |
| Robust, unambiguous notebook handling | ⚠️ nbsphinx + myst_nb both enabled |
| Notebooks reachable in the book | ⚠️ framebuffer/ndc orphaned (not in toctree) |

## Proposed steps to reach the goal

Nothing here is done yet — awaiting go-ahead (and the open questions below).

1. **Adopt the proven pattern as the convention.** For any section you want linkable,
   put `# (some-label)=` on its own line directly above the `# # Heading` in a
   `# %% [markdown]` cell. Use descriptive kebab/lower labels (`framebuffer-blending`,
   `ndc-clipping`), and keep them globally unique.
2. **Add the labels you actually want**, section by section, in `plot2d.py`,
   `framebuffer.py`, `ndc.py` — then add the `:ref:`Text <label>`` links from the RST
   chapters that should point at them. (Which sections/links: see open question 1.)
3. **Resolve the orphaned notebooks** (open question 2): either add `framebuffer` and
   `ndc` to the `index.rst` toctree (they become navigable pages), or add `:orphan:` at
   the top of each so Sphinx stops warning while they stay reachable only via `:ref:`.
4. **Make notebook handling unambiguous** (open question 3): drop `nbsphinx` from the
   `conf.py` extensions list — `myst_nb` already does everything the book uses, and it's
   the one that makes `(label)=` work. Rebuild to confirm nothing regresses.
5. **(Optional) Enable finer targets** (open question 4): if you want to link to a
   specific paragraph/figure rather than a whole section, add `"attrs_block"` to
   `myst_enable_extensions`, then anchor with `{#label}` block attributes.
6. **Verify:** nested `make html`, grep the build log for `undefined label` and
   `not included in any toctree`, and click each new link in both light/dark HTML.

## Open questions

1. **Scope** — which sections do you want labelled and linked, and from where? Give me
   the list (e.g. "link ch16's NDC discussion to the `ndc` notebook's clipping section"),
   or say "you pick reasonable ones" and I'll propose a set for approval.
2. **Orphaned `framebuffer`/`ndc`** — add them to the `index.rst` toctree (navigable), or
   mark them `:orphan:` (reachable only via `:ref:`)? Recommended: add to the toctree so
   they're discoverable, unless you deliberately want them hidden.
3. **Remove `nbsphinx`?** It's redundant with `myst_nb` and its presence is a latent
   footgun. Recommended: yes, remove it.
4. **Finer-than-section targets?** Do you need to link to specific paragraphs/figures
   (needs `attrs_block`), or are section-header anchors enough? Recommended: headers are
   enough; skip `attrs_block` until a real need appears.
5. **Explicit `(label)=` vs auto heading anchors?** Keep hand-writing `(label)=` (stable,
   explicit, more typing), or set `myst_heading_anchors = 2` so every heading becomes
   referenceable automatically (less typing, but a renamed heading silently breaks refs)?
   Recommended: explicit labels for the handful you actually link, for stability.

## Sources

- MyST cross-referencing (target `(label)=`, `:ref:` / `{ref}` / `[](#label)`):
  https://myst-parser.readthedocs.io/en/latest/syntax/cross-referencing.html
- MyST-NB text/percent notebooks:
  https://myst-nb.readthedocs.io/en/latest/authoring/text-notebooks.html
- Jupytext percent/markdown formats: https://jupytext.org/formats/markdown/
- myst-nb vs nbsphinx (both register `.ipynb`; myst-nb is the successor):
  https://github.com/executablebooks/MyST-NB
