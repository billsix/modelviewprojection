# Attach the book (HTML + PDF + EPUB) as standalone GitHub Release assets

**Status:** approved — ready to implement (William Emerison Six <billsix@gmail.com> approved the
recommendation 2026-09-19: **keep** the source+book tarball AND **add** standalone pdf/epub/html-zip
assets). Not yet started. Rides the release CI in `tasks/github-actions-release-ci.md` (which already
BUILDS all three book forms but ships them only inside the tarball); like that task, the GitHub Release
step can only be fully verified on a real tag push. The GitHub-Pages question is split out to
`tasks/release-book-github-pages-decision.md`.
**Priority:** 5
**Difficulty:** 3

## BLUF

On a tagged release, publish the book's three forms — **HTML (zipped), PDF, and EPUB** — as
**individual downloadable assets** on the GitHub Release, so a reader can grab
`modelviewprojection-<ver>.pdf` or `.epub` (or the HTML site zip) straight from the Releases page.
Today the release workflow already builds all three (`make book`) but bundles them **only inside**
`dist/modelviewprojection-<ver>.tar.gz` (source + `book-output/`), so they are not individually
downloadable. This task adds a make target that stages the three forms as standalone files in `dist/`
and points the Release step at them. Per the project's governing CI principle, all bundling logic is a
`make` target; only the GitHub-API "create Release" step stays in YAML. "Done" = a tagged release shows
`…-html.zip`, `….pdf`, and `….epub` as separate downloads (plus, optionally, the HTML published to
GitHub Pages).

## Context (cold-start — read these first)

- **The book build already exists and runs in CI.** `entrypoint/entrypoint.sh` (run by `make book`)
  builds Sphinx `html` + `latexpdf` + `epub` in `book/docs/`, then copies into
  `output/modelviewprojection/`: the `html/` site, `*.pdf` (from `_build/latex/*pdf`), `*.epub` (from
  `_build/epub/*epub`), and a `.nojekyll`. It also runs the pytest suite + `tools/check_doc_regions.py`
  first as release gates.
- **The release workflow.** `.github/workflows/release.yml` (on `push: tags: v*`) runs
  `make release-tarball` (which depends on `book`), `make image-push`, then `softprops/action-gh-release`
  with `files: dist/*.tar.gz`. So the ONLY attached asset today is the source+book tarball.
- **`make release-tarball`** (in the root `Makefile`) `git archive HEAD` + copies
  `output/modelviewprojection/` → `dist/…/book-output/`, tars to
  `dist/modelviewprojection-<RELEASE_VERSION>.tar.gz`. `RELEASE_VERSION` defaults to
  `git describe --tags --always --dirty`; the workflow passes `${{ github.ref_name }}`.
- **Governing principle** (from `tasks/archive/2026/10/22/github-actions-format-ci.md` / `github-actions-release-ci.md`): CI
  is a THIN wrapper over `make` — every buildable/bundling step is a local `make` target; only registry
  login and Release creation are YAML (they hit GitHub's API). Keep that split.
- **No GitHub Pages deploy today.** `.github/workflows/` has only `checks.yml` + `release.yml`; the
  `.nojekyll` in the output hints Pages was intended, but nothing publishes it. (See open question 3.)
- **Prereq status:** the release CI itself is implemented but **not yet maintainer-tested** (registry
  auth, tag trigger, Release creation) — see `tasks/github-actions-release-ci.md`. This task rides the
  same workflow, so it should be verified in the same test tag push.

## Plan

1. **New make target `release-book-assets`** (root `Makefile`, `.PHONY`, `##`-documented), depends on
   `book` so the artifacts exist. It stages standalone, versioned copies into `$(DIST_DIR)`:
   - PDF: `cp output/modelviewprojection/*.pdf $(DIST_DIR)/modelviewprojection-$(RELEASE_VERSION).pdf`
   - EPUB: `cp output/modelviewprojection/*.epub $(DIST_DIR)/modelviewprojection-$(RELEASE_VERSION).epub`
   - HTML zip: `(cd output/modelviewprojection && zip -r -X - html .nojekyll) > $(DIST_DIR)/modelviewprojection-$(RELEASE_VERSION)-html.zip`
     (or `tar -czf …-html.tar.gz -C output/modelviewprojection html` — pick one; zip is friendlier for a
     Windows reader double-clicking it). Glob the pdf/epub (don't hardcode the Sphinx-chosen basename).
   - Keep it robust: `mkdir -p $(DIST_DIR)`; fail loudly if a form is missing (a glob that matches
     nothing should error, not silently skip — e.g. check the file count).
2. **Wire it into the release.** Either make `release-tarball` also depend on / call
   `release-book-assets`, or add a separate workflow step `make release-book-assets RELEASE_VERSION=…`.
   Prefer a single umbrella target (e.g. `release-artifacts: release-tarball release-book-assets`) the
   workflow calls once, so local `make release-artifacts` reproduces the full asset set.
3. **Update `release.yml`'s Release step** `files:` glob to attach the new assets alongside the tarball:
   ```yaml
   files: |
     dist/*.tar.gz
     dist/*.pdf
     dist/*.epub
     dist/*-html.zip
   ```
   (Decide per open question 1 whether to keep the tarball.)
4. **Gitignore** the new `dist/` artifacts if not already (`dist/` is a build dir; confirm it's ignored).
5. **Verify** (see below).

## Verification

- **Local, offline:** `make release-book-assets RELEASE_VERSION=v0.0.0-test BUILD_DOCS=1` and confirm
  `dist/` gets a `.pdf`, `.epub`, and `-html.zip`, each non-empty, the zip containing `html/index.html`.
  (This exercises everything except the GitHub-API Release step — same limitation as the parent task.)
- **On a real tag** (maintainer, on GitHub): push a throwaway tag, confirm the Release page lists the
  three standalone assets + the tarball, and that the PDF/EPUB open and the HTML zip renders.

## Decisions taken (2026-09-19)

1. **Keep the source+book tarball AND add the three standalone book assets** (approved). `dist/*.tar.gz`
   stays (a reproducible source snapshot); the pdf/epub/html-zip are added so a reader can grab just the
   PDF without extracting a tarball.
2. **HTML delivery in THIS task = a `-html.zip` release asset.** Publishing the HTML to GitHub Pages is a
   separate decision — see `tasks/release-book-github-pages-decision.md` (the maintainer wants to learn
   what Pages is before deciding).

## Open questions (minor)

1. **Asset naming** — `modelviewprojection-<ver>.pdf` / `.epub` / `-html.zip` proposed (matches the
   tarball prefix). Confirm, or prefer a title-cased/hyphenated name. (Low stakes; I'll default to the
   proposed names if unanswered.)

## Related

- `tasks/github-actions-release-ci.md` — the release workflow this extends (Phase 2; needs testing).
- `tasks/archive/2026/10/22/github-actions-format-ci.md` — Phase 1 (check-only CI) + the governing "CI is a thin wrapper"
  principle.
- `tasks/consider-removing-nbsphinx.md` — adjacent book-tooling task (unrelated to release, noted for
  context on the book build).
