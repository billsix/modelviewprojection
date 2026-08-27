# GitHub Actions: format-check CI (phase 1), then releases (phase 2), then other repos

**Status:** blocked
**Priority:** 5
**Difficulty:** 4
**Started:** 2026-08-27 (William Emerison Six <billsix@gmail.com>)
**Blocked on:** maintainer answers the Open questions below (local-run via `act`; runner environment;
registry = ghcr.io).
**Recheck:** the Open questions below are answered (maintainer-gated; `/recheck-blocked` surfaces it).

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

## Context (investigation 2026-08-27)

- **There is NO CI today** — `.github/` does not exist (`tasks/reference/tests-and-gates.md:14-18`;
  confirmed on disk). `make format` is the only standing gate, portable host + container.
- Nested podman is available in the sandbox, so GitHub Actions can be run locally via `act`/`nektos`.
- The three book forms (HTML/PDF/EPUB) exist (archived `2026/07/08/finish-pdf-epub-build.md`); image
  export/import targets exist (`Makefile:211-215`, archived `2026/06/13/fix-image-export-import-gaps.md`).
- **Personal convention:** the agent stages, the maintainer commits — so any `.github/workflows/*.yml`
  would be created and staged, not committed, by the agent.

## Plan (phased — line items are explicit per the maintainer's ask)

- [ ] **Phase 1 (this task):** investigate running Actions locally (`act` under nested podman); add a
      **format-check** GitHub Action = run `make format`, fail if `git diff` is non-empty.
- [ ] **Line item → spawn a NEW task (Phase 2)** once Phase 1 lands: on **tagged releases**, push a
      container image to a registry (**ghcr.io** — "ideally on GitHub itself") **and** build a release
      tarball bundling the source + the **three book forms (HTML/PDF/EPUB)**.
- [ ] **Cross-project reminder:** after Phase 2, replicate this on other projects, e.g.
      `geometricalgebra` (and note it belongs on the shared container template generally).

## Open questions

1. **Run locally via `act`** under the sandbox's nested podman — acceptable as the "can we run them
   locally?" answer?
2. **Format action's runner environment** — mvp's `make format` needs the container (or the portable
   host path with editable install + gacalc generated). Which runner environment should the Action use?
3. **Registry** confirmed as **ghcr.io**?
