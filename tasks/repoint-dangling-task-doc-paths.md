# Repoint dangling `tasks/…/*.md` paths across the docs

**Done:** 2026-11-16. **Created:** 2026-11-16 by the session-end sweep of the pgzero-gl step-3
branch (William Emerison Six <billsix@gmail.com>).

Of the 130 distinct `tasks/<…>.md` paths in tracked text that did not resolve, 148 citations in 97
files were fixed. The 53 paths still dangling are all meant to: each cites another repo's doc and
names that repo, cites a doc that was deleted, or is a placeholder example. The edits are comment
and prose changes only. `make check-format`, `make type-check` and `make test` (66 passed) were
green afterwards.

## Decision

- **Scope covered the live docs and the archived task docs** (William Emerison Six
  <billsix@gmail.com>, 2026-11-16). Live means `CLAUDE.md`, `README.md`, `tasks/*.md` and
  `tasks/reference/`. A path fix doesn't change what a done-record says, and most of the dangling
  paths were in archived docs.
- **Code comments were in scope too:** `Makefile`, `.github/workflows/checks.yml`,
  `requirements.txt`, `softwarerendering.py` and three `tools/` scripts each cited a task by its
  pre-archive path.

## What was done

1. **This repo's archived tasks (120 citations, 82 files):** `repoint.py` rewrote each citation
   whose basename matched exactly one file under `tasks/archive/`.
   - It skipped any citation preceded by another path component, and the `data/keep.txt` sites.
   - A second run changed nothing.
   - The 21 sites it flagged as naming another repo were read in context. All were mvp's own tasks;
     the flags came from slugs containing "gacalc".
2. **Other repos' docs (28 hand-reviewed edits):** `locate_cross_repo.py` found where each
   remaining path lives in the sibling checkouts, and `cross_repo_edits.py` applied an explicit
   list.
   - Where the other repo had since archived the task, the path was repointed to that repo's
     archive path.
   - Where the citation named the repo only as "gacalc", by a directory path (`/geometricalgebra/…`,
     `spimulator/tasks/…`) or by a wrong URL (`github.com/billsix/texExpToPng`), the GitHub URL was
     added or corrected.
   - A citation that already named its repo by the exact GitHub repo name (geometricalgebra,
     runClaudeInContainer) was left alone.
   - The two `../tasks/…` relative links in
     `tasks/archive/2026/06/01/ports-render-options-to-imgui.md` became repo-root-relative code
     spans.
3. **Left dangling on purpose (53 paths):**
   - Citations of another repo's current doc that name the repo, e.g. runClaudeInContainer
     `tasks/reference/python-coding-standard.md`, github.com/billsix/geometricalgebra
     `tasks/reference/gl-toolkit.md`.
   - Deleted docs, cited as history: `tasks/codebase-overview.md` (retired 2026-07-30),
     `tasks/backport-labels-fixes-from-mvm.md` (deleted 2026-07-08),
     `tasks/archive/2026/10/14/ports-controls-in-menubar-step-1-superbiblev4.md` (removed by the
     maintainer 2026-10-18, commit 877371ac) and `tasks/texexptopng-standalone-display-math.md`
     (in neither repo's history).
   - Proposed names in a plan table: `tasks/archive/2026/09/14/trim-claude-md.md` proposed
     `tasks/reference/assignments.md` and a mvp `tasks/reference/python-coding-standard.md`.
   - `tasks/reference/chapt18-advanced-buffers.md` is tracked in github.com/billsix/OpenGLSuperbibleV4Code,
     which the citation names. The maintainer added that checkout's `github` remote on 2026-11-16.
     It spells the repo with a lowercase "b", so the four mvp citations spelled
     `OpenGLSuperBibleV4Code` were corrected to match.
   - Examples: `helm.el`'s `tasks/foo.md`, `tasks/reference/x.md` and `tasks/tasks/reference/x.md`.
4. **One edit reverted:** `tools/check_local_annotations.py` is vendored from
   github.com/billsix/runClaudeInContainer, so its stale `tasks/annotate-all-local-variables.md`
   citation was left alone here. The canonical already cites the archived path (since 2026-11-15);
   mvp's copy is an older version.
   - Re-copying it is filed as runClaudeInContainer
     `tasks/recopy-check-local-annotations-to-vendored-copies.md`, together with the stale copies
     in methodfinder, spimulator and impo.

## Scripts

All under `tasks/adhoc/repoint-dangling-task-doc-paths/`:
- `discover.sh` lists the dangling paths. It excludes this doc and its own directory, which quote
  dangling paths on purpose.
- `repoint.py` (`report` or `apply`) handles group 1.
- `locate_cross_repo.py` builds the sibling-repo report.
- `cross_repo_edits.py` holds the group-2 edit list.
- `data/` holds the snapshots: `dangling-before.txt`, `dangling-after-group1.txt`,
  `dangling-after.txt`, `report.txt`, `cross-repo-report.txt` and `keep.txt`.

All of them are one-shot: they get `git rm`'d in the archive commit.
