# The mvp book's figures, math images & notebooks

**Reference document** — how every image and executed notebook in the book
comes to exist: the four figure toolchains, the custom `inlinetex` Sphinx
extension, and the jupytext notebook pipeline. Not a task; update in place.
Last updated 2026-10-12 (the math plots moved from gnuplot + matplotlib to
**ePiX**; see `tasks/replace-book-figures-with-epix.md`).

Sibling of `tasks/reference/book-and-docs-pipeline.md`, which owns the Sphinx
build sequence and the doc-region `literalinclude` mechanism. This doc owns
everything that produces a PNG/SVG/notebook the chapters embed.

Open future work on these images: `tasks/dark-mode-images.md` — making the generated
figures render correctly in furo's dark mode (they currently show as white boxes; direction
decided = best-fidelity dual light/dark assets, implementation deferred).

---

## 1. The four toolchains

The `.tex` labels and the `.dot` graphs are driven by `book/docs/_static/Makefile`
(invoked as `cd _static/ && make` by `book/docs/Makefile` before — and its PNG copy
step after — every Sphinx target). The ePiX figures are driven **separately**, by
`tools/render_epix_figures.py` run from `entrypoint.sh` before Sphinx (not by the
`_static/Makefile`). `inlinetex` runs during the Sphinx build itself.

| Source | Tool | Output |
|---|---|---|
| `_static/*.tex` (~35 Cayley edge labels: `p1ToW.tex`, `wToNDC.tex`, …) | `texExpToPng --size 300` | `_static/*.png` |
| `_static/*.dot` (~26 Cayley graphs: `demo02.dot` … `demo18-8.dot`) | graphviz `dot -Tpng` | `_static/*.png` |
| `book/figures/epix/*.py` (35: the coordinate/space plots + the transform-step frames) | ePiX, via `tools/render_epix_figures.py` | `_static/epix/<name>.{pdf,png}` |
| `.. inlinetex::` / `:itex:` in the `.rst` | `book/docs/_ext/inlinetex.py` → texExpToPng | `_static/inlinetex/<sha1>.png` — generated during the **Sphinx run**, not by make |

Mechanics worth knowing before touching any of it:

- **The ePiX figures are a separate pipeline** (added 2026-10-11, replacing the
  gnuplot plots and the `generate_plots.py` matplotlib frames — see
  `tasks/replace-book-figures-with-epix.md`). Each figure is one jupytext-percent
  `.py` under `book/figures/epix/`, **one figure per file** (the renderer runs each
  in a fresh interpreter because `libepix` keeps global drawing state), every
  argument keyword-only. `render_epix_figures.py` writes `<name>.pdf` (via `elaps
  --pdf`) and `<name>.png` (flattened onto a solid background so dark-mode HTML
  pages don't show a transparent sheet) into `_static/epix/`. Chapters reference
  `.. figure:: _static/epix/<name>.*` — the wildcard resolves to the PDF for the
  `latex` builder and the PNG for `html`; there is **no SVG** in this path. The
  transform figures (`translation*`, `scale*`, `*rotate*`, `modelspace`) **drive
  mvp's own taught code** — they import `modelviewprojection.mathutils` over gacalc
  `Vector`/`InvertibleFunction`s, so the renderer runs *after* the editable install
  in `entrypoint.sh`; the 13 static coordinate plots use no `mathutils`. The build
  is gated by `USE_EPIX` (a Dockerfile LATE layer pinning `EPIX_COMMIT`, matching
  the gacalc pin); with `USE_EPIX=0` the renderer exits 2 with a message rather than
  failing cryptically. Shared scene helpers: `_scene2d.py` (framed plots, clipped
  rects, markers) and `_transform_sequence.py` (`transform_frame`).
- **The ePiX outputs are not tracked** (`_static/epix/` is gitignored — the pdf+png
  are build artifacts). As with the old generated SVGs, they persist on disk across
  incremental builds, so **a clean build is the only honest test** (below).
- **`/usr/local/bin/texExpToPng` is an explicit make prerequisite** of the
  `.tex → .png` rule, deliberately: a `BUILD_DOCS=0` image fails there with a
  clear message instead of at the first invocation.
- **The `%.png` copy runs twice** in `book/docs/Makefile` (before Sphinx and
  after, into `_build/html/_static/`) because some PNGs materialize after
  Sphinx has already copied `_static`. Belt and braces — leave it.
- **Bill's rule: each demo gets its own `.dot` copy** even when two chapters'
  diagrams are currently identical (`demo12.dot`/`demo13.dot` were created as
  copies of `demo11`'s so each chapter's diagram is independently editable).
  Don't "helpfully" de-duplicate them.
  (`tasks/archive/2026/05/26/ch13-fixes.md`)
- **What is deliberately OUTSIDE the inlinetex path:** the `.dot`-embedded
  node-label equations — graphviz references those PNGs by filename inside
  `<IMG SRC=…/>` HTML labels, so they stay on the `_static/Makefile` `.tex`
  pattern rule at size 300.

### Clean builds are the real test (a generated figure can silently vanish)

`entrypoint.sh` installs the package with `--python "$(which python)"`. This flag is
load-bearing: the earlier `--system` form targeted `/usr` (no setuptools) → the
editable build failed → downstream figure generation never ran → "not readable"
warnings — but only on a **clean** tree, because previously-generated figures
persist on disk. The editable install now also makes `modelviewprojection.mathutils`
importable for `render_epix_figures.py`, so the same failure class would silently
blank the transform figures. Smoke-test after `git clean -fdx` (or in a fresh
container), not incrementally. (Historical: the original symptom was the retired
`generate_plots_for_book` console script failing → `_static/make` exit 127 → ~44
warnings, clean-build count 72 → 10 when fixed, 2026-07-23 —
`tasks/archive/2026/07/23/fix-editable-install-system-flag.md`.)

## 2. The `inlinetex` extension (`book/docs/_ext/inlinetex.py`)

A custom Sphinx **directive and inline role** that renders LaTeX through
texExpToPng into PNGs. Reachable because `conf.py` does
`sys.path.insert(0, os.path.abspath("./_ext"))`.

**Why it exists at all:** EPUB output renders stock `.. math::` / `:math:`
incorrectly — that is the original reason for the whole texExpToPng path.
The 2026-05-10 migration removed **every** stock math usage (43 blocks + 84
inline roles), so the standing convention is: **never author `:math:` or
`.. math::` in this book** — they'd render through a path the book no longer
uses everywhere (mathjax stays enabled for HTML, but PDF/EPUB consistency is
the point). Use `.. inlinetex::` / the inline role.
(`tasks/archive/2026/05/10/sphinx-inline-tex-extension.md`,
`sphinx-math-to-inlinetex.md`)

- **Content-addressed cache:** filename = `sha1(whitespace-normalized latex +
  "|size=N")[:12]`; the on-disk PNG in `_static/inlinetex/` (gitignored) *is*
  the cache; identical expressions dedupe; the only invalidation is deleting
  the directory. Normalization means `.rst` re-indentation doesn't bust it.
- **`inlinetex_default_size = 150` in `conf.py`** (extension default is 300 —
  too large at body-text scale). **Changing this value changes every hash**
  and orphans every cached PNG.
- **The docutils NUL trap:** an inline role taking raw LaTeX must call
  `utils.unescape(text, restore_backslashes=True)` — docutils replaces
  backslashes with NUL during inline parsing, so `\times` otherwise arrives as
  `\x00times`, texExpToPng errors, and Sphinx marks the node
  `class="problematic"` with no useful cause. Generic Sphinx-extension trap.
- **Graceful degradation is a silent failure:** with texExpToPng missing from
  PATH, the directive logs a warning and emits the raw LaTeX as a literal
  block — the build **succeeds** and ships a book full of LaTeX source.
- **Figure-vs-image:** passing `:caption:`/`:figclass:` wraps the image in a
  figure node, so `.. figure::` call sites swap 1:1.
- **Directive-body indentation rules** (both produce a bare
  "texExpToPng failed (exit 1)", not an RST error): docutils dedents a body by
  its *minimum* indent, so an under-indented continuation line demotes the
  option lines (`:class:`/`:align:`) into the LaTeX itself; and a trailing
  `.. //` comment block still indented gets swallowed into the body.
  (`tasks/archive/2026/07/23/perspective-inlinetex-malformed-directives.md`)
- **Wrapping heuristics for newly-authored math** (from the migration): single
  line → `$…$`; `\begin{split}` → `equation*`; `&`-aligned multi-line →
  `align*`; other multi-line → `\[…\]`.
- **The pinned texExpToPng SHA matters:** the current pin carries
  `\documentclass[varwidth]{standalone}` + `xcolor` in its preamble — without
  varwidth, the book's display math (`\[…\]`, `align*` in ch04/ch06/ch14)
  fails. Those two preamble features cleared 25 of 27 inlinetex failures when
  the pin was bumped; bump deliberately (see `CLAUDE.md` › dependency sync).
- texExpToPng leaks `formula.{aux,dvi,tex}` into its working directory —
  hidden only by `.gitignore`.

## 3. The notebook pipeline

- **Every `.ipynb` in the repo is a build artifact** (gitignored;
  `notebooks/` holds only `.keep`). `entrypoint.sh` converts the jupytext
  py:percent sources in `src/modelviewprojection/notebooksrc/` before each
  build — and the destinations are *not* uniform:
  - `plot2d.py` → `assignments/demo02/plot2d.ipynb` + `book/docs/` (not
    `notebooks/`)
  - `framebuffer.py` → `notebooks/` + `book/docs/`
  - `ndc.py` → `notebooks/` + `book/docs/`
- **The notebooks are first-class toctree pages**, not figures: `index.rst`
  lists `framebuffer` and `ndc` **between ch02 and ch03**, and `plot2d` at the
  end. On a fresh checkout they don't exist, so a host-side `sphinx-build`
  reports missing toctree documents — build in the container.
- **A fourth py:percent file is NOT generated and NOT in `notebooksrc/`:**
  `assignments/demo02/vec1.py` is a hand-maintained jupytext source with 11
  doc-region markers, `literalinclude`d by `mathhomework1.rst`. It sits next
  to a *generated* notebook from a different source — don't confuse the two.
- **`util/nbplotutils.py` is not a demo helper** despite its location — its
  sole consumer is `notebooksrc/plot2d.py`. It guards
  `set_matplotlib_formats("svg")` behind `if get_ipython() is not None`
  precisely so it imports headless (which lets `--doctest-modules` collect
  `util/` without a Jupyter kernel).
- **PDF landmines from executed notebooks:** moviepy's tqdm progress bar
  emits U+2588 `█` into cell output and used to kill pdflatex — `ndc.py`
  passes `logger=None` to `write_videofile`; any new notebook using a
  progress-bar library needs the same. The recursive variant: a `█` inside a
  *source comment* also reaches LaTeX (jupytext puts comments in code cells).
  Keep notebook sources ASCII-only. (lualatex now absorbs most of this, but
  the convention stands; `tasks/archive/2026/05/10/HANDOFF-2026-05-10.md`,
  `2026/07/08/finish-pdf-epub-build.md`)
- The Dockerfile's `USE_JUPYTER` block makes py:percent files open as
  notebooks on a single click and disables the news prompt — both must stay
  **inside** the `if [ "$USE_JUPYTER" = "1" ]` guard (the flag defaults 0 in
  the Dockerfile, so an unguarded call breaks a lean build). Since JupyterLab
  4.1 a user *can* re-enable a disabled plugin unless `jupyter labextension
  lock` is used — deliberately skipped for a single-user container.
  (`tasks/archive/2026/07/29/…`; the `--level=user` gotcha is in `CLAUDE.md`)

## 4. `conf.py` reading guide — what's live, what's dead

- **Live:** `furo` theme; `autodoc`+`napoleon`; `nbsphinx` + `myst_nb`;
  `sphinxcontrib.bibtex` (`references.bib`); `mathjax` (HTML only);
  `inlinetex`; `sphinx.ext.imgconverter` with an inkscape svg→pdf converter —
  now that ePiX supplies PDFs directly (and the math-plot SVGs are gone), the
  converter serves only the remaining committed SVG art (`Maththing.svg`, the CC
  images); keep it — don't remove it blindly on the strength of the ePiX migration;
  `latex_engine = "lualatex"`, `latex_use_xindy = False` (rationale in the
  pipeline doc).
- **Dead config that will mislead you:** `imgmath_image_format` /
  `imgmath_font_size` / `imgmath_latex_preamble` are set but
  **`sphinx.ext.imgmath` is not in `extensions`**; `templates_path`
  names a `_templates/` that doesn't exist; `requirements.txt` still pins
  `sphinx_rtd_theme` though the theme is furo.
- Small standing items: `book/docs/mvp_dict.pws` is the aspell dictionary
  (pipeline doc §1); `glossary.rst` has three placeholder entries (World
  Space, Modelspace defined as themselves); `references.bib`'s key
  `AbstractAlegbra` is misspelled and cite sites depend on the misspelling.
