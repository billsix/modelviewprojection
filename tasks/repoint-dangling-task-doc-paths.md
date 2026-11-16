# Repoint dangling `tasks/…/*.md` paths across the docs

**Status:** proposed — needs go-ahead
**Priority:** 6
**Difficulty:** 3

## BLUF

As of 2026-11-16, 130 distinct `tasks/<…>.md` paths cited in the repo's text do not resolve. Most
are a task cited by its pre-archive `tasks/<slug>.md` path after it moved to
`tasks/archive/<YYYY>/<MM>/<DD>/`. Done means a re-run of the discovery command below lists only
the paths that are meant not to resolve here: cross-repo citations that name their repo, and
placeholder examples.

## Context

- The rule: a path in a doc is a claim the file exists, and archiving a doc means fixing what
  points at it in the same change. Paths are repo-root-relative. (Sandbox conventions, the
  communication-conventions reference doc in github.com/billsix/runClaudeInContainer.)
- Found by the 2026-11-16 session-end sweep of the pgzero-gl step-3 branch. That branch fixed only
  the two docs it archived itself (commit 6106cadf); everything below predates it.
- Discovery (run from the repo root; 237 files cite at least one `tasks/` path):

  ```sh
  bash -c 'git grep -ohE "tasks/[A-Za-z0-9_./-]+\.md" | sort -u | while read p; do [ -e "$p" ] || echo "$p"; done'
  ```

## The three groups (snapshot 2026-11-16)

1. **75: archived in this repo.** The basename matches exactly one file under `tasks/archive/`
   (none matched more than one), e.g. `tasks/pgzero-gl-de-abstraction-options.md` →
   `tasks/archive/2026/09/08/pgzero-gl-de-abstraction-options.md`. Repoint them mechanically:
   - Match on the full old path, with a guard so an `archive/…` prefix is not doubled.
   - Re-check any basename that later matches more than one archive file by hand.
2. **About 50: another repo's docs.** These cite gacalc (`tasks/add-quarter-turn-to-g2.md`,
   `tasks/archive/2026/07/22/precise-dual-typing.md`, …) or the sandbox repo
   (`tasks/reference/nested-podman-design.md`, `tasks/reference/python-coding-standard.md`,
   `tasks/add-shell-exec-target.md`, …).
   - Where the citing line or paragraph already names the repo (github.com/billsix/geometricalgebra,
     github.com/billsix/runClaudeInContainer), leave it.
   - Otherwise add the repo URL, and the archived path if that task was archived over there.
   - Read the GitHub URL from each repo's `github` remote, not from the directory name.
3. **A handful: placeholders and typos.** `tasks/x.md`, `tasks/reference/x.md`, `tasks/foo.md` and
   `tasks/.../typed-product-helper-functions.md` are examples or elisions, so leave them.
   - `tasks/tasks/reference/x.md` is the helm double-prefix example, which is deliberate.
   - Check each one in context before deciding.

## Decisions

- **Scope covers the live docs and the archived task docs** (William Emerison Six
  <billsix@gmail.com>, 2026-11-16). Live means `CLAUDE.md`, `README.md`, `tasks/*.md` and
  `tasks/reference/`. A path fix doesn't change what a done-record says, and most of the dangling
  paths are in archived docs.

## Scripts

Save the discovery command and the repointing codemod under
`tasks/adhoc/repoint-dangling-task-doc-paths/` (`discover.sh`, the worklog in `data/`). `git rm`
them at archive time.
