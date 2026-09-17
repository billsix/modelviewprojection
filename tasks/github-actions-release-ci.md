# GitHub Actions Phase 2: release automation on tagged releases

**Status:** in progress — implemented autonomously 2026-09-17 (maintainer away, commit permission
granted); **NEEDS THE MAINTAINER TO TEST** (registry auth, tag trigger, GitHub Release creation,
and the full book build cannot be exercised in the sandbox — see "What is verified vs. needs
testing").
**Priority:** 5
**Difficulty:** 5
**Started:** 2026-09-17 (William Emerison Six <billsix@gmail.com>) — spawned from
`tasks/github-actions-format-ci.md` (Phase 1) on its completion, per that task's plan.

## BLUF

On a tagged release, CI publishes two artifacts: a **container image** pushed to a registry
(ghcr.io) and a **release tarball** bundling the source + the three built book forms
(HTML/PDF/EPUB), attached to a GitHub Release. Per the governing principle (see the Phase 1 task),
every buildable step is a `make` target that runs locally; only the irreducibly GitHub-specific
steps (registry login, creating the Release) live in the workflow YAML.

## Governing principle (inherited from Phase 1)

CI is a thin wrapper over the make/Dockerfile system: `checkout` → `make <target>`, all
build/bundle logic in make targets, `CONTAINER_CMD` auto-detecting podman→docker. The ONE
acknowledged exception here: **logging in to the registry and creating a GitHub Release talk to
GitHub's API and cannot be a local `make` target** — those two steps are YAML. Everything else
(build the image, build the book, make the tarball, tag + push the image) is a make target.

## What was implemented (2026-09-17)

Makefile targets (all container-driven, `CONTAINER_CMD`-portable):

- **`make book`** — non-interactive book build (the existing `html` target uses `-it`, unusable in
  CI). Runs the image's default entrypoint, which builds HTML + PDF + EPUB into
  `output/modelviewprojection/` (it also runs the test suite first — an intentional release gate).
- **`make release-tarball`** — depends on `book`; bundles `git archive HEAD` (tracked source) plus
  `output/modelviewprojection/` into `dist/modelviewprojection-<version>.tar.gz` via a staging dir,
  so the tarball has both the source and the built book under one prefix. `RELEASE_VERSION` defaults
  to `git describe --tags --always --dirty`.
- **`make image-push`** — tags the built image `$(IMAGE_REF):$(RELEASE_VERSION)` and `:latest`
  (`IMAGE_REF` defaults to `ghcr.io/billsix/modelviewprojection`) and pushes both. Requires the
  caller to already be logged in to the registry (the workflow does that).

Workflow `.github/workflows/release.yml`:

- Triggers on `push:` of tags matching `v*`.
- `permissions: contents: write` (create the Release) + `packages: write` (push to ghcr).
- Steps: checkout (full history, for `git describe`) → `docker login ghcr.io` with the built-in
  `GITHUB_TOKEN` → `make release-tarball` (builds the BUILD_DOCS=1 image + book + tarball) →
  `make image-push` → attach `dist/*.tar.gz` to a GitHub Release.

## What is verified vs. needs testing

**Verified locally (sandbox, podman):**
- The `release-tarball` bundling mechanics (git archive + output staging + tar) — tested against a
  stub `output/` (the tar is well-formed, contains source + book-output under the version prefix).
- Makefile parses; `make help` lists the new targets; YAML parses.

**NEEDS THE MAINTAINER TO TEST (could not be done in the sandbox):**
1. **The full book build** (`make book`) end to end — needs a `BUILD_DOCS=1` image (heavy TeX
   Live) and a long `latexpdf`/`epub` run; not built here to avoid a 20+ min TeX install. The
   entrypoint that produces the three forms is unchanged, so `make book` = the proven manual build,
   just non-interactive.
2. **`make image-push`** — needs registry credentials; not runnable in the sandbox (no ghcr auth).
3. **The `release.yml` trigger + registry login + GitHub Release creation** — only exercised by
   pushing a real `v*` tag to the GitHub remote. Docker-runner specifics (BuildKit cache mounts,
   `:Z` labels as a no-op on Ubuntu) also first-run only, same caveat as Phase 1.

## Decisions made autonomously (for maintainer review)

- **Registry = `ghcr.io/billsix/modelviewprojection`** (Open Q3 of the Phase 1 task: "ideally on
  GitHub itself"). Overridable via `IMAGE_REF=`. Change if you want a different registry/name.
- **Release tarball layout:** `modelviewprojection-<version>/` containing the tracked source
  (`git archive`) plus `book-output/` (= `output/modelviewprojection/`, the HTML dir + PDF +
  EPUB). Chose `git archive` for source so only tracked files ship (no `output/`, tars, venvs).
- **`GITHUB_TOKEN`** (the workflow's built-in token) for the ghcr login, not a PAT — it has
  `packages: write` on the repo's own package. Switch to a PAT only if pushing elsewhere.
- **GitHub Release creation stays in YAML** (`softprops/action-gh-release`) — it's a GitHub-API
  action with no local `make` equivalent; this is the acknowledged exception to the thin-wrapper
  principle, noted above.
- **The book build runs the test suite first** (the entrypoint does), so a release can't be cut
  from failing tests. Kept as-is.

## Open questions (for the maintainer)

1. **Registry/name** — `ghcr.io/billsix/modelviewprojection` OK, or a different registry/image
   name?
2. **Release trigger** — tags matching `v*` (e.g. `v1.2.3`). Confirm the tag scheme, or narrow to
   `v[0-9]*`.
3. **Should the release also run the format/type gates first** (reuse Phase 1's `check-format` /
   `type-check`), or is the entrypoint's built-in pytest enough of a gate for a release?

## See also

- `tasks/github-actions-format-ci.md` — Phase 1 (format-check) + the governing principle.
- `github.com/billsix/geometricalgebra` › `tasks/github-actions-ci.md` — the sibling replication
  (a PyPI-published library, so its Phase 2 is PyPI-first).
