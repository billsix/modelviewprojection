# Bring mvp's Makefile/Dockerfile onto the standard container template

**Status:** done — 2026-10-22 (William Emerison Six <billsix@gmail.com>).
**Priority:** 4
**Difficulty:** 5
**Created:** 2026-10-12 **Updated:** 2026-10-22 (William Emerison Six <billsix@gmail.com>)

## What this was

mvp's `Makefile`/`Dockerfile` had drifted from the standard container template that
gacalc and epix-mirror follow. The drift was first measured 2026-10-11 during the ePiX
figure migration, when every nested `podman run` needed a hand-added `--cgroups=disabled`
and the real doc build could not run headless (an interactive aspell gate).

Most of the drift closed before this task reached its final step: by 2026-10-22 `master`
already had `make test`, `PODMAN_RUN_FLAGS`/`NESTED_PODMAN`, `CONTAINER_CMD` podman→docker
auto-detect, `check-format`, `type-check`, and a non-interactive book build. The original
drift table in git history was measured on a stale branch and was re-measured against
`master` before editing (per the 2026-10-22 decision), so none of that was redone.

## What was done (the three genuine leftovers)

Work commit `6189c16e`:

1. **`MINIMAL_IMAGE`** — the five optional-feature flags (`BUILD_DOCS`, `USE_EMACS`,
   `USE_JUPYTER`, `USE_X_WINDOWS`, `USE_EPIX`) now use the standard idiom
   `?= $(if $(filter 1,$(MINIMAL_IMAGE)),0,1)`: full by default (host or nested), lean
   only on `make image MINIMAL_IMAGE=1`. `USE_SPYDER` stays `?= 0`. The Dockerfile ARGs
   already existed (default 0) and the Makefile already passed each as `--build-arg`, so
   no Dockerfile change was needed. **Verified**: the lean image (3.87 GB) builds nested
   and passes the full `make test` gate (112 passed) — glfw/pyopengl live in the base
   group + `requirements.txt`, and the headless pytest imports/doctests need none of the
   X11/Wayland client libs that `USE_X_WINDOWS=0` drops.

2. **`docs` target name** — `docs` is now the canonical, non-interactive doc build
   (standard template name), writing the book's `version.txt` commit stamp; `html` and
   `book` are aliases of it. `html` dropped its `-it`, which existed only for the old
   interactive aspell gate (spellcheck has been headless since 2026-10-12,
   `tasks/archive/2026/10/22/non-interactive-spellcheck.md`). `release-tarball` keeps
   working through the `book` alias and now also gets the version stamp.

3. **`check-generated`** — **N/A**. mvp has no code generator (no `generate` target, no
   `tools/` generator), so no determinism gate is added. Confirmed, not skipped blindly.

Doc deltas shipped in the same commit: `README.md` quick-start uses `make docs` and notes
`MINIMAL_IMAGE`; `tasks/reference/book-and-docs-pipeline.md` corrected in the three places
that still claimed `-it` was required for an interactive aspell gate.

## Left for the maintainer (optional, non-blocking)

- Several reference docs still mention `make html` in passing (`tests-and-gates.md`,
  `glossary-authoring.md`, `notebook-sphinx-integration.md`, `architecture-overview.md`).
  These are **not wrong** — `make html` still works as an alias — so they were left as-is
  to avoid churn. Repoint them to `make docs` whenever those docs are next touched.
- Historical task-record bullets in `tasks/reference/design-decisions.md` that say
  "make html … resolved" describe past runs and were deliberately **not** rewritten.
