# Decision needed: publish the book's HTML to GitHub Pages?

**Status:** needs maintainer decision (a cold-start question for William Emerison Six
<billsix@gmail.com>, who asked to learn what GitHub Pages is before deciding; raised 2026-09-19). Split
out of `tasks/release-standalone-book-assets.md`. No work until you pick an option below.
**Priority:** 6
**Difficulty:** 3 (a small deploy workflow if yes)

## BLUF

The book already builds to HTML in CI. **Question: do you want that HTML published as a live website via
GitHub Pages**, so anyone can read the book online in a browser (no download) at a URL like
`https://billsix.github.io/modelviewprojection/` — updated automatically? Or is shipping the HTML as a
downloadable `.zip` on the Release (the plan in the sibling task) enough? Pick an option at the bottom.

## What GitHub Pages is (plain explanation)

**GitHub Pages is free static-website hosting built into GitHub.** You point it at a folder of HTML/CSS/JS
(here: the book's `output/modelviewprojection/html/`), and GitHub serves it as a public website at
`https://<user>.github.io/<repo>/` — for this repo, `https://billsix.github.io/modelviewprojection/`. It's
how a lot of open-source projects host their docs/books for free. No server to run; GitHub rebuilds and
serves the site whenever a workflow pushes new HTML to it.

- **Cost:** free for public repos.
- **How it'd work here:** a small GitHub Actions step takes the already-built `html/` output and deploys
  it to Pages (via the official `actions/deploy-pages`). The repo already writes a `.nojekyll` marker into
  the HTML output — a hint that publishing to Pages was intended at some point (Pages otherwise runs a
  "Jekyll" step that can mangle files starting with `_`, which Sphinx produces; `.nojekyll` disables that).
- **Two flavors of "when to publish":**
  - **On every push to the default branch** — the online book always reflects the latest committed source
    (good for a living book; the site can drift ahead of the last tagged release).
  - **On tagged release only** — the online book reflects the last released version (more stable, less
    current).
- **Downsides / things to know:** the site is **public** (anyone can read it — fine for an open book);
  it's a separate workflow with its own permissions (`pages: write`, `id-token: write`); and you'd pick
  one source of truth for "the online book" (latest vs released).

## The options

- **(A) Publish to Pages on tagged release.** The online book = the latest released version. Pairs cleanly
  with the release workflow. Recommended if you want a stable public book URL.
- **(B) Publish to Pages on every push to the default branch.** The online book always = latest source.
  Best if you want it to always reflect your newest writing.
- **(C) No Pages — just the downloadable `-html.zip`** on the Release (the sibling task already covers
  this). Simplest; readers download and open locally.
- **(D) Both (B or A) AND the zip.** Online site for browsing + a zip for offline reading.

## What I need from you

**Pick A, B, C, or D.** If A/B/D, I'll add a small Pages deploy workflow (or step) that publishes
`output/modelviewprojection/html/`, keeping the "CI is a thin wrapper over make" principle (the build stays
a make target; only the Pages upload/deploy is the GitHub-specific YAML). If C, this task closes and the
`-html.zip` in the sibling task is the whole HTML story.

## Related

- `tasks/release-standalone-book-assets.md` — the approved standalone-assets work (HTML zip lives there;
  this task decides the online-Pages question).
- `tasks/github-actions-release-ci.md` — the release workflow a Pages deploy would sit alongside.
- The book HTML output that would be published: `output/modelviewprojection/html/` (built by `make book`;
  see `entrypoint/entrypoint.sh`).
