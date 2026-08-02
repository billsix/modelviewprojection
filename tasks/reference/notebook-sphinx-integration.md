# How the percent-format notebooks integrate with the Sphinx book

**What this is:** durable reference for how the `notebooksrc/*.py` Jupyter notebooks flow
into the book, how they're executed and rendered, and — the part that's easy to get wrong —
how to make a **labelled section** in a notebook that other chapters can **hyperlink to**.
Read this before touching the notebook pipeline, adding a notebook cross-reference, or
changing the Sphinx notebook extensions.

Related tasks: `tasks/notebook-percent-cross-references.md` (the label/toctree work),
`tasks/consider-removing-nbsphinx.md` (the nbsphinx cleanup, deferred).

## The pipeline, end to end

1. **Sources** are jupytext **percent-format** Python files:
   `src/modelviewprojection/notebooksrc/{plot2d,framebuffer,ndc}.py`. They use `# %%` for
   code cells and `# %% [markdown]` for markdown cells. They're editable as plain scripts
   (Spyder) or as notebooks (JupyterLab, via the jupytext viewer).
2. **`entrypoint.sh` converts each to `.ipynb`** with `jupytext --to notebook … --output
   book/docs/<name>.ipynb` **before** the Sphinx build. The generated `.ipynb` are
   **gitignored build artifacts** — never edit or commit them; edit the percent `.py`.
   (Some are also written to `notebooks/` and `assignments/demo02/` for non-book use.)
3. **Sphinx executes and renders the `.ipynb`.** Execution output lands in
   `_build/jupyter_execute/*.svg` etc. (a MyST-NB artifact — see the handler note below).
   `nb_execution_timeout = 600` (conf.py).
4. **Inclusion in the book:** each notebook is a page listed in the `index.rst` toctree
   (`plot2d`, `framebuffer`, `ndc`). A notebook that is generated but **not** in a toctree
   builds an orphaned page and warns "document isn't included in any toctree".

## Which extension renders `.ipynb`: myst_nb, NOT nbsphinx (and both are enabled)

`conf.py`'s `extensions` list contains **both `nbsphinx` and `myst_nb`**. This matters:

- Both extensions register `.ipynb` as a source suffix. Normally that raises
  *"source_suffix '.ipynb' is already registered"*; here the build tolerates it and
  **`myst_nb` is the one actually handling notebooks** (confirmed by the
  `_build/jupyter_execute/` output, which is a MyST-NB artifact).
- **This is load-bearing for cross-references.** The `(label)=` target syntax below is
  **MyST** syntax. `myst_nb` parses markdown cells as MyST, so it works. **`nbsphinx` would
  parse the same cell as CommonMark**, turning `(label)=` into literal text and making every
  notebook `:ref:` an "undefined label". So the feature only works *because* myst_nb wins.
- **The footgun:** having both enabled is fragile — a version bump or an import-order change
  could flip which extension claims `.ipynb`, silently breaking every notebook link. The
  intended end state is to **remove `nbsphinx`** (myst_nb supersedes it for everything this
  book uses). Deferred deliberately; tracked in `tasks/consider-removing-nbsphinx.md`. Until
  then, know that myst_nb must remain the handler.

## Cross-referencing: labelled section → RST → HTML hyperlink

This is the mechanism to link a chapter to a place inside a notebook.

**1. Put a MyST target before a heading, in a markdown cell of the percent file:**

```python
# %% [markdown]
# (framebufferlabel)=
# # Framebuffer
```

`# (label)=` on its own line, immediately above the `# # Heading`. jupytext turns the cell
into markdown `(label)=` + heading; myst_nb makes it a cross-reference target anchoring that
section. In the generated HTML this becomes an `id="framebufferlabel"` anchor.

**2. Reference it from reStructuredText** with the normal Sphinx role:

```rst
... see :ref:`Framebuffer <framebufferlabel>` for details.
```

`` :ref:`Display text <label>` `` sets the link text; `` :ref:`label` `` uses the heading
text. Labels are collected **globally**, so any chapter can reference any notebook's label
regardless of toctree placement. From MyST/markdown you'd instead write `[text](#label)` or
`` {ref}`text <label>` ``.

### Top-level label convention

Each notebook has a **top-level `(label)=` before its h1**, named `<notebook>label`:
`framebufferlabel` (framebuffer), `plot2dlabel` (plot2d), `ndclabel` (ndc). A ref to one of
these lands at the top of that notebook's page — the clean "link to the whole notebook"
case. Section-level labels (finer than the h1) are added **manually, per section**, only
where a chapter actually links in.

### Constraints to know before adding labels

- **No implicit heading anchors.** `myst_heading_anchors` is **unset** in conf.py, so the
  *only* way to make a section referenceable is an explicit `(label)=`. (Setting
  `myst_heading_anchors = 2` would auto-anchor every h1/h2 by slug, at the cost that
  renaming a heading silently breaks refs. We chose explicit labels for stability.)
- **Targets attach to headings.** `(label)=` before a heading works with base MyST. To
  anchor a non-heading (a specific paragraph/figure), you'd need the `attrs_block` MyST
  extension added to `myst_enable_extensions` (currently only `colon_fence`, `dollarmath`).
  Not enabled — add it only if a real need appears.
- **Heading style:** notebooks use an ATX h1 (`# # Title`) then setext subsections (text
  underlined with `---------`). Both render fine in MyST; the mix is cosmetic.

## Verifying a notebook cross-reference

Build the book in the container and check the HTML, not just the exit code:

- `make html` (or the nested-container equivalent) — see the project's container docs.
- Grep the build log for `undefined label` and `not included in any toctree` (both should be
  empty for a healthy notebook link).
- Grep the generated page for the anchor: `grep 'id="framebufferlabel"'
  _build/html/framebuffer.html` — the `id` must be present for the hyperlink to land.
- Open the page in both light and dark furo themes and click the link.

## Current inbound references (as of 2026-08-02)

- `book/docs/ch01.rst` → `:ref:`Framebuffer <framebufferlabel>`` (the one existing link).
- `plot2d` / `ndc` now carry top-level labels (`plot2dlabel`, `ndclabel`) and are in the
  toctree, ready to be linked as chapters need them. Adding those `:ref:` links is a manual,
  as-needed process.
