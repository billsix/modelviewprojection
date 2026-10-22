# GitHub Actions: format-check CI (phase 1), then releases (phase 2), then other repos

**Status:** in progress — **Phase 1 COMPLETE** (`make check-format` + `checks.yml`; the
Actions run is **confirmed green on GitHub**, 2026-09-18). Phase 2 (releases) is implemented in
`tasks/github-actions-release-ci.md` and awaits the maintainer's test; a `make release` tag target
(ported from geometricalgebra) was added to cut it. Cross-project replication done for
geometricalgebra.
**Priority:** 5
**Difficulty:** 4
**Started:** 2026-08-27 (William Emerison Six <billsix@gmail.com>)
**Phase 1 implemented:** 2026-09-17; **confirmed green on GitHub:** 2026-09-18 (William Emerison Six
<billsix@gmail.com>).

## Phase 1 landed (2026-09-17)

- **`make check-format`** (Makefile) = run `make format` (ruff `--fix`/`ruff format`, + `ty check` —
  fails on any ty error), then `git diff --exit-code` to fail if the code was not already formatted.
  All logic is in the make target, per the governing principle.
- **`.github/workflows/checks.yml`** = two check-only jobs on push + pull_request (`ubuntu-latest`):
  `format` (`make check-format`) and `type` (`make type-check`) — both `checkout` → `make <target>`,
  nothing else in YAML. Added the `type` job 2026-09-18 (maintainer: format AND type on every commit,
  not just release). Neither job commits or reformats the repo (the formatter runs in the disposable
  runner and the job fails on a `git diff`).
- **Runner environment (Open Q1, resolved):** `ubuntu-latest` (ships Docker); the image is built
  in-workflow from the committed Dockerfile (self-contained, no registry needed for phase 1), built
  lean (the format/ty check needs no docs/emacs/jupyter/X). `CONTAINER_CMD` already auto-detects
  podman→docker (`Makefile:11`), so the identical target runs in CI and on the maintainer's host.
- **Verified locally** (nested podman, the acceptance test per the principle): a clean tree →
  `make check-format` exit 0 (ruff unchanged, ty green, empty diff); a deliberately unformatted line
  → exit nonzero (ruff reformatted it, `git diff --exit-code` caught it). The gate bites.
- **Not verifiable locally — the one caveat:** the sandbox has podman, not docker, so the
  docker-on-the-runner path (BuildKit `--mount=type=cache`, `:Z` mount labels as a no-op on
  non-SELinux Ubuntu) is exercised only when CI first runs. If the first run fails on a
  docker-specific detail, that is the thing to fix — the make target itself is proven.

*(Was `**Status:** blocked` until 2026-09-08. Re-filed: `blocked` is for a concrete, **testable**
gate outside our control, with a `Recheck:` someone can run — a decision the maintainer owes is the
`proposed — needs go-ahead` state. `/recheck-blocked` had nothing to run for this one.)*

## Goal

Maintainer's idea, verbatim: *"Add a task to investigate GitHub actions, can we run them locally? If so,
as a first pass, I want a github action that will pass if the code is formatted correctly. It can do this
via running make format, to see if there is a git diff, and if there is a diff, then failure happens. As
part of this task, make a line item that when the previous part is finished, create a new task, that will
handle more than just formatting. For instance, on tagged releases, I would like to be able to see if I
can push to a registry for containers, ideally on GitHub itself. And, to have it make a release tarball,
which has the source, and the generated artifacts, such as the three forms of the book. When this is
done, I want a reminder to do this on other projects as well, such as geometricalgebra."*

This is a **phased** task — the structure below is deliberate.

## Governing design principle — CI is a THIN WRAPPER over the make/Dockerfile system

**Every workflow does as little as possible: `checkout` → `make <target>`. All real work lives in
the Makefile + Dockerfile so it runs identically on a laptop and in CI** — no build/test/release
logic in YAML. This is the whole point of the task: what CI does must be reproducible locally with
the same command, not a GitHub-only path that drifts from what the maintainer runs by hand.

Consequences that shape every phase:

- **If a workflow needs a step, add it as a `make` target first**, then have the workflow call it.
  The format-check is not "run `make format` then a YAML `git diff` step" but a single make target
  (e.g. `make check-format` = `make format` + `git diff --exit-code`) so the exact CI behaviour is
  one command locally. Same for phase 2: image push and the release-tarball build are `make`
  targets the workflow invokes, not inline `docker push`/`tar` in YAML.
- **`CONTAINER_CMD` auto-detects podman→docker** (`$(shell command -v podman >/dev/null 2>&1 &&
  echo podman || echo docker)`) so the identical `make` target runs on a GitHub runner (Docker) and
  on the maintainer's host (podman). No podman-vs-docker branching in the workflow.
- **Local runnability is the acceptance test**, not just "the Action is green": because the
  workflow does nothing but call a `make` target, the maintainer reproduces exactly what CI does by
  running that same target on his host (nested podman drives the container). There is no need to
  simulate the GitHub runner locally — the make/Dockerfile system *is* the local path. If a thing
  can only be done in GitHub's environment, that's a smell to flag, not design around.
- This mirrors the shared container-template convention (make drives the container; scripts run
  both in-container and on the host from the repo root) and the imps `*-upstream-container-ci`
  tasks, where the workflow just calls `make appimage` and the Makefile drives everything.

## Context (investigation 2026-08-27)

- **There is NO CI today** — `.github/` does not exist (`tasks/reference/tests-and-gates.md:14-18`;
  confirmed on disk). `make format` is the only standing gate, portable host + container.
- Nested podman is available in the sandbox and on the maintainer's host, so every `make` target a
  workflow calls runs locally with the identical command — which is the whole local-reproducibility
  story (no GitHub-runner simulator needed).
- The three book forms (HTML/PDF/EPUB) exist (archived `2026/07/08/finish-pdf-epub-build.md`); image
  export/import targets exist (`Makefile:211-215`, archived `2026/06/13/fix-image-export-import-gaps.md`).
- **Personal convention:** the agent stages, the maintainer commits — so any `.github/workflows/*.yml`
  would be created and staged, not committed, by the agent.

## Plan (phased — line items are explicit per the maintainer's ask)

- [x] **Phase 1 (this task):** added the **`make check-format`** target (= `make format` +
      `git diff --exit-code`) and `.github/workflows/checks.yml` (just `checkout` →
      `make check-format`). The diff-fail logic lives in the Makefile, per the governing principle,
      so the maintainer runs the exact CI check locally with one command. Verified both paths.
- [x] **Document the principle (end of Phase 1):** the "CI is a thin wrapper over the
      make/Dockerfile system" principle is now a concise rule in `CLAUDE.md` (the "Continuous
      integration" section), pointing here for the roadmap and rationale.
- [ ] **Line item → spawn a NEW task (Phase 2)** once Phase 1 lands: on **tagged releases**, push a
      container image to a registry (**ghcr.io** — "ideally on GitHub itself") **and** build a release
      tarball bundling the source + the **three book forms (HTML/PDF/EPUB)** — each as a `make` target
      the workflow calls (e.g. `make image-push`, `make release-tarball`), not inline YAML.
- [ ] **Cross-project reminder:** after Phase 2, replicate this on other projects, e.g.
      `geometricalgebra` (and note it belongs on the shared container template generally).

## Open questions

1. **Format action's runner environment** — mvp's `make format` needs the container (or the portable
   host path with editable install + gacalc generated). Which runner environment should the Action
   use? (This is the one place the runner matters; the governing principle keeps everything else in
   make targets.)
2. **Registry** confirmed as **ghcr.io**?
