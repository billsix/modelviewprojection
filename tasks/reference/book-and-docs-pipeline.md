# The mvp book & docs pipeline

**Reference document** — how the Sphinx book is built and how it pulls code (including gacalc's) via doc-region literalinclude. Not a task; update in place. Last updated 2026-07-21.

---

mvp *is* a book. The Sphinx pipeline under `book/docs/` is the primary deliverable; the Python package in `src/modelviewprojection/` exists largely to be *quoted* by that book. Breaking the book build, or silently emptying a code listing, is the highest-severity class of regression in this repo. This document is the map of that subsystem.

## 1. The Sphinx book build

### Where it runs and what produces it

The whole book builds **inside the Fedora-44 container** (`Dockerfile` → `registry.fedoraproject.org/fedora:44`). The image's `ENTRYPOINT` is `/entrypoint.sh` (`Dockerfile:195`). The top-level `Makefile`'s **`html` target is the book build** (`Makefile:185`): it writes `book/docs/version.txt` on the host (`git rev-parse HEAD`), then `podman run`s the image with **no `--entrypoint` override**, so the container's default `ENTRYPOINT ["/entrypoint.sh"]` fires. Despite the target name, `entrypoint.sh` builds **all three formats** — HTML, LaTeX-PDF, and EPUB — every time; there is no separate `latexpdf` or `epub` make target.

### The entrypoint build sequence (`entrypoint/entrypoint.sh`)

In order, inside the container:

1. Activate `/venv` (`source /venv/bin/activate`), `cd /mvp`.
2. `pytest --exitfirst --disable-warnings || exit` — **the test suite gates the book build**. A failing test aborts before any docs are produced.
3. **Regenerate the jupytext notebooks** — `plot2d`, `framebuffer`, `ndc` are converted from their `.py` sources in `src/modelviewprojection/notebooksrc/` into `.ipynb`, written to **both** `notebooks/`/`assignments/` **and** `book/docs/` (so nbsphinx/myst-nb can execute+embed them). These `.ipynb` are build artifacts (gitignored — `.gitignore:39`).
4. `uv pip install --no-deps --no-index --no-build-isolation -e . --system` — editable install of the package.
5. **Populate the docs-only gacalc source** into `book/docs/_gacalc_src/` (see §3).
6. `python tools/check_doc_regions.py || exit` — **the anchor checker gates the build** (see §2). Runs *after* `_gacalc_src` is populated, because some anchors resolve against gacalc's files.
7. `cd /mvp/book/docs && make html && make latexpdf && make epub`.
8. Copy artifacts to the bind-mounted output tree and `touch .nojekyll` (see below).

### Output location

`entrypoint.sh` copies into `/output/modelviewprojection/` (`entrypoint.sh:37-45`), which the Makefile bind-mounts from the host `./output/` (`Makefile:34`, `-v ./output/:/output/:Z`):

- `_build/html/` → `/output/modelviewprojection/html/`
- `_build/latex/*pdf` → the PDF
- `_build/epub/*epub` → the EPUB
- `touch /output/modelviewprojection/.nojekyll` — stops GitHub Pages' Jekyll from mangling Sphinx's underscore-prefixed dirs (`_static`, `_images`).

`make clean` just does `rm -rf output/*` (`Makefile:94`).

### The interactive aspell spellcheck gotcha ⚠️

`book/docs/Makefile` has a **catch-all rule that makes *every* Sphinx target depend on `spellcheck`**:

```make
%: Makefile spellcheck
	cd _static/ && make
	@$(SPHINXBUILD) -M $@ …
```

`spellcheck` (`book/docs/Makefile:19`) runs `aspell --personal=./mvp_dict.pws check <file>` over every `*.rst`. **`aspell check` is interactive** — on an unknown word it opens a full-screen prompt and *waits for a keystroke*. This is why the top-level `html` target runs the container with **`-it`** (`Makefile:188`): without a TTY, aspell has no terminal to drive and the build **hangs forever** (or dies) at spellcheck, before Sphinx ever runs. Any new automation that invokes `make html`/the book build must allocate a TTY, or must feed aspell clean input.

The custom dictionary is **`book/docs/mvp_dict.pws`** (`PERSONAL_DICT` in the docs Makefile) — an aspell personal wordlist (`personal_ws-1.1 en 278`, ~278 project-specific terms: `APIs`, `BackColor`, GA/math jargon, etc.). **When the book introduces a new proper noun or coined term, add it here**, or the spellcheck gate stops on it. The `cd _static/ && make` step (before and after the Sphinx call) builds/copies the book's generated `.png` plots into the HTML `_static`.

## 2. The doc-region `literalinclude` mechanism

The book does **not** paste code inline. Chapters quote live source with Sphinx `literalinclude` + named region markers, so the printed listings can never drift from the code that actually runs.

### How a slice is pulled

Source files carry paired comment markers:

```python
# doc-region-begin <name>
...code...
# doc-region-end <name>
```

A chapter `.rst` selects between them (real example, `book/docs/ch16.rst:51`):

```rst
.. literalinclude:: ../../src/modelviewprojection/demos/demo14.py
   :language: python
   :start-after: doc-region-begin draw paddle 1
   :end-before: doc-region-end draw paddle 1
   :lineno-match:
```

`:start-after:`/`:end-before:` name the markers; the lines *between* them are rendered (the marker comment lines themselves are excluded). `:lineno-match:` makes the displayed line numbers equal the real line numbers in the source file (so a reader can open the file and land on the same line). Markers live in **hand-written** modules as ordinary comments (`src/modelviewprojection/mathutils.py`, the demos, `tests/test_mathutils.py`) and, for gacalc, are baked into its generated files (§3).

**Split signature vs. body.** A single `begin` marker can be closed by several differently-named `end` markers, letting one region be sliced into signature-only and body-only pieces. From `mathutils.py:108`:

```python
# doc-region-begin define rotate around
def rotate_around(angle_in_radians: float, center: Vector2) -> InvertibleFunction[Vector2]:
    # doc-region-end rotate around signature
    """..docstring.."""
    # doc-region-begin rotate around body
    return compose([translate(center), rotate(angle_in_radians), translate(-center)])
    # doc-region-end define rotate around
```

So the book can show the `def` line (`start-after: define rotate around` / `end-before: rotate around signature`) without the docstring, then the body separately.

### The prefix-collision hazard ⚠️

**Sphinx matches the first line *containing* the anchor text — not an exact-line match.** Two consequences, both silent:

- If a name is a **prefix** of another name in the same file (`define rotate` vs `define rotate around`), a query for the shorter can match the longer's marker line and pull the wrong region.
- If a name is **duplicated**, the query always grabs the *first* occurrence.

This is also why gacalc's own marker naming is descriptive-and-prefix-free with a load-bearing trailing keyword (`... signature`/`... body`/`... method`).

### The silent-empty-listing failure — why the checker exists

If an anchor **doesn't resolve** (marker renamed/deleted/typo'd, or the target file moved), Sphinx emits at most a warning and **renders an empty code block** — the caption and surrounding prose survive, the code just vanishes. A broken listing ships looking fine. `tools/check_doc_regions.py` makes both failure modes **loud (exit 1)**:

- `_unresolved_anchor_errors()` — walks every `book/docs/**/*.rst`, finds each `literalinclude` with a `:start-after:`/`:end-before:` doc-region option, resolves the target path relative to the `.rst`, and asserts the `doc-region-begin <name>` / `doc-region-end <name>` string is present in the target (mirroring Sphinx's *containing-line* match). Missing target file or missing marker → error.
- `_name_collision_errors()` — walks every `*.py` in the repo *except* under `book/docs/`, and for begin- and end-markers **separately** flags (a) exact-duplicate names and (b) any name that is a **prefix** of another in the same file.

It is invoked two ways, both in the container: by `entrypoint.sh:29` as a **build gate** (before `make html`), and standalone via **`make check-regions`** (`Makefile:150`) — which populates `_gacalc_src` first (mirroring the entrypoint) then runs the checker, because some anchors resolve against gacalc's files that only exist inside the image. The checker's own module docstring notes a *third* check (region content vs a lockfile, for cross-repo drift) is planned but unwired, pending a marker-ID scheme (`tasks/dangling-book-code-includes.md`).

## 3. The gacalc integration for docs

mvp depends on gacalc **twice, for two different reasons**, and the two must stay in lockstep.

**(a) The runtime WHEEL.** `requirements.txt:3` pins `gacalc==0.0.11`. This is the ordinary runtime dependency — `pip`-installed into `/venv`, imported by the package (`from gacalc.g2 import Vector2`, etc.). `pyproject.toml` reads dependencies dynamically from `requirements.txt` (`[tool.setuptools.dynamic]`).

**(b) The docs-only SOURCE sdist.** The book `literalinclude`s **gacalc's own source** (its `functions.py`, `transforms.py`, `g2.py`, `g3.py`) to teach GA concepts — e.g. `book/docs/ch06.rst` quotes `_gacalc_src/functions.py` for `InvertibleFunction`, ch05/ch14 quote `g2.py`/`g3.py`/`transforms.py`. To do that, gacalc's real source must be *on disk inside the book tree*. The `Dockerfile` (`ARG GACALC_VERSION=0.0.11`, lines 179-193):

1. Fetches the gacalc **sdist** from the PyPI JSON API for exactly `${GACALC_VERSION}`.
2. Extracts it and copies `src/gacalc/*.py` into the image at **`/opt/gacalc-src/`**.
3. `entrypoint.sh:23-24` (and `make check-regions`) then copies `/opt/gacalc-src/*.py` → **`book/docs/_gacalc_src/`** at build time.

`_gacalc_src/` is **gitignored** (`.gitignore:183`), docs-only, never on `sys.path`, never imported. It exists purely as literalinclude fodder.

**Why the sdist, not a git clone.** gacalc's `g1.py`/`g2.py`/`g3.py`/`scalar.py` are *code-generated and gitignored in gacalc's own repo* — a git clone would contain no generated modules (you'd have to run gacalc's generator). The **sdist has the generated modules, with their doc-region markers, baked in** (gacalc bakes them into the sdist/wheel at build time). So pulling the sdist gets ready-to-quote source with zero code generation and zero toolchain here.

**The lockstep rule.** `ARG GACALC_VERSION` (`Dockerfile:179`) **must equal** the `gacalc==` pin in `requirements.txt`. The same version drives both the runtime wheel and the docs source, so *the book never documents a gacalc version the code doesn't run*. Bump both together (`Dockerfile:179`'s comment states this explicitly). `GACALC_VERSION` is declared as a *late* `ARG` (not up top with the feature-flag ARGs) deliberately, so a version bump only rebuilds that cheap final layer, not the expensive TeX/dnf install above it.

## 4. The container build/run flow

**Image (`make image`).** Fedora-44 + podman, with the standard dnf-cache mount idiom. Feature flags are build args, defaulting to `1` in the `Makefile` (`BUILD_DOCS ?= 1`, `USE_EMACS ?= 1`, `USE_JUPYTER ?= 1`, `USE_X_WINDOWS ?= 1`; `USE_SPYDER ?= 0`) and `0` in the `Dockerfile`. **`BUILD_DOCS=1` is what installs the entire book toolchain** — Sphinx, furo, nbsphinx, myst-nb, texlive (+lualatex/fontspec/gnu-freefont), aspell/aspell-en, graphviz, inkscape, ImageMagick, and a source build of `tex-expression-to-png` (the `inlinetex` extension, pinned to a git SHA). Building the book with `BUILD_DOCS=0` produces an image that cannot build the book.

**Sphinx config highlights (`book/docs/conf.py`).** Theme `furo`; extensions include `autodoc` + `napoleon` (docstrings become API pages — `api.rst`), `nbsphinx` + `myst_nb` (the regenerated notebooks), `sphinxcontrib.bibtex` (`references.bib`), `mathjax`, and the custom `inlinetex`. **PDF uses `latex_engine = "lualatex"`** (not pdflatex) because Unicode from autodoc'd gacalc docstrings (e.g. `|A| = √(A~ * A)`, the U+221A radical) would otherwise abort the PDF build; `latex_use_xindy = False` keeps `makeindex` (the image ships it; xindy would drag in clisp).

**Run sequence** — see §1. Summary: pytest gate → regenerate notebooks → editable install → populate `_gacalc_src` → `check_doc_regions.py` gate → html+pdf+epub → copy to `/output`.

**`make check-regions`** (`Makefile:150`) is the standalone anchor validator; it runs in the container, populates `_gacalc_src` from `/opt/gacalc-src` first (because gacalc anchors resolve there), then runs the checker. The html build runs the same check via `entrypoint.sh`, so `check-regions` is *not* wired as an html prerequisite.

**Related non-book targets.** `make format` (container ruff+ty via `loadpackages.sh && format.sh`), `make shell` (interactive), `make jupyter` (JupyterLab on 8888). `format.sh` runs every step and exits nonzero if *any* failed (so one pass reports all the red).

**Running nested** (inside the sandbox): every inner `podman run` needs `--cgroups=disabled` (the sandbox's `/sys/fs/cgroup` is read-only). Add it transiently to the target's `podman run`. The book build itself is headless (no GUI); the xvfb/`DISPLAY` recipe is only relevant for the OpenGL *demo* targets (`make shell` + running a `demos/*.py`), not for `make html`. Note the html/shell/jupyter targets carry `-it` — needed for the aspell gate (§1) and for interactive shells; a fully non-interactive nested html build will hang at spellcheck unless aspell input is clean.

## 5. Gotchas & how it fails

- **Silent empty listing.** A renamed/deleted/misspelled doc-region marker, or a moved target file, makes Sphinx render an **empty** code block with the caption and prose intact — the build "succeeds" and the bug is invisible in the PDF. `tools/check_doc_regions.py` is the only thing that catches this; it runs as a build gate (`entrypoint.sh:29`) and via `make check-regions`. **After renaming any marker or moving any quoted file, run `make check-regions`.**
- **Prefix / duplicate anchor.** Sphinx matches the first line *containing* the anchor, so `foo` matches `foo bar`'s line and pulls the wrong region; a duplicated name always grabs the first. Both are silent; the checker's `_name_collision_errors()` flags them. Keep marker names descriptive and prefix-free (trailing `signature`/`body`/`method`/`setter` keywords disambiguate).
- **gacalc version mismatch.** If `Dockerfile`'s `ARG GACALC_VERSION` and `requirements.txt`'s `gacalc==` pin diverge, the book quotes one gacalc version while the code imports another — the listings can show code that doesn't match runtime behavior. Bump both together. A gacalc release that isn't yet on PyPI will fail the Dockerfile's sdist fetch (it hits the live PyPI JSON API).
- **`_gacalc_src/` missing.** It's gitignored and only materializes inside the container (from `/opt/gacalc-src`). On a bare host checkout it doesn't exist, so gacalc-quoting anchors won't resolve and a host-side `check_doc_regions.py` will report them as unresolved — run the check in-container (`make check-regions`), which populates it first.
- **Spellcheck hang.** `book/docs/Makefile`'s catch-all makes every Sphinx target depend on the **interactive** `aspell check`. Without a TTY the build hangs/dies before Sphinx runs — hence `-it` on the `html` target. An unknown word not in `book/docs/mvp_dict.pws` stops the build on that word; add new proper nouns/coined terms to the dictionary.
- **`BUILD_DOCS=0` image can't build the book.** All of Sphinx/TeX/aspell is gated behind that flag. It defaults to `1` in the Makefile; trimming it to speed an image build produces an image where `make html` fails.
- **pytest gates the book.** `entrypoint.sh:6` runs `pytest --exitfirst` before building; a failing test aborts the entire book build (no docs produced). Doctests count — `mathutils.py`'s docstring examples run as tests and are also quoted into the book.
