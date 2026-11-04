# Attach the book (HTML + PDF + EPUB) as standalone GitHub Release assets

**Done 2026-11-04** (William Emerison Six <billsix@gmail.com> approved the direction 2026-09-19:
keep the source+book tarball AND add standalone pdf/epub/html-zip assets). Implemented on branch
`release-book-assets`.

## What was done

On a tagged release the book's three forms — zipped HTML site, PDF, and EPUB — now ship as
individual downloadable assets on the GitHub Release, alongside the existing source+book tarball,
so a reader can grab just the PDF without extracting the tarball.

- **`make release-book-assets`** (root `Makefile`, `.PHONY`, `##`-documented, depends on `book`)
  stages standalone versioned copies into `$(DIST_DIR)`:
  `modelviewprojection-<ver>.pdf`, `modelviewprojection-<ver>.epub`,
  `modelviewprojection-<ver>-html.zip` (the `html/` site + `.nojekyll`). It fails loudly if any
  form is missing rather than shipping a partial set.
- **`make release-artifacts`** = `release-tarball` + `release-book-assets` — the single umbrella
  target the workflow calls; running it locally reproduces exactly what a tag attaches.
- **`.github/workflows/release.yml`** now runs `make release-artifacts` (was `release-tarball`) and
  the Create-Release step's `files:` attaches `dist/*.tar.gz`, `dist/*.pdf`, `dist/*.epub`,
  `dist/*-html.zip`. Per the governing "CI is a thin wrapper over make" principle, all bundling is
  in make; only the GitHub-API Release step stays in YAML.

## The one non-obvious thing (kept so it isn't re-discovered)

**The book PDF is named explicitly as `$(CONTAINER_NAME).pdf` — NOT a `*.pdf` glob.** The book build
(`entrypoint/entrypoint.sh`) flattens `output/modelviewprojection/` to hold the `html/` site, the
single book `.epub`, the `.nojekyll`, the book PDF `modelviewprojection.pdf` (Sphinx names the latex
target after the project), AND ~40 descriptively-named figure PDFs (`plot1.pdf`, `scale-0.pdf`, …).
So `output/.../*.pdf` matches far more than the book. The EPUB is globbed (exactly one). The task
doc's original plan said "glob the pdf" — that was written before the figure PDFs were in `output/`;
the glob would have been wrong.

## Decisions

- Keep the source+book tarball AND add the three standalone assets (approved 2026-09-19).
- HTML delivery here = a `-html.zip` asset; publishing HTML to GitHub Pages is the separate
  `tasks/release-book-github-pages-decision.md`.
- Asset naming: defaulted to the proposed `modelviewprojection-<ver>.{pdf,epub,-html.zip}` (matches
  the tarball prefix) — the one minor open question, which the task said to default on if unanswered.

## Verification

- **Local staging — PASS.** Ran the recipe body against the already-built `output/`: `dist/` got a
  non-empty `.pdf` (8.3 MB), `.epub` (16 MB), and `-html.zip` (17.5 MB) whose listing contains
  `html/index.html` and `.nojekyll`. `make -n release-book-assets` expands the recipe correctly and
  `make help` lists both new targets. This exercises everything except the GitHub-API Release step.
- **Remaining (maintainer, GitHub-gated):** the real-tag Release attachment can only be exercised on
  an actual tag push — the same limitation as, and tested together with,
  `tasks/github-actions-release-ci.md` (release CI, still awaiting the maintainer's first tag test).

## Related

- `tasks/github-actions-release-ci.md` — the release workflow this extends (needs the maintainer's
  tag-push test; this task's real-tag verification rides it).
- `tasks/release-book-github-pages-decision.md` — the split-out GitHub Pages question.
