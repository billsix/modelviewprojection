# Create Programming3DComputerGraphics: a copy of this repository's history with the ports removed

**Status:** proposed — needs go-ahead, the answers below, and tasks 1 and 2 finished first (filed 2026-11-23; redesigned 2026-11-24 as a copy)
**Priority:** 7
**Difficulty:** 6
**Created:** 2026-11-23
**Part of:** the maintainer's three-task split (William Emerison Six <billsix@gmail.com>, 2026-11-23): task 1 is
`tasks/archive/2026/11/24/python-port-into-master.md` in `github.com/billsix/OpenGLSuperBibleV4Code` (done), task 2 is
`tasks/extract-code-the-classics-to-own-repo.md` here, this is task 3.
**Depends on:** tasks 1 and 2 done and their repositories pushed (the new repository's history will no longer contain the
ports, so they must already live in their own repositories; this repository keeps them for history).

## BLUF

**Design decision (William Emerison Six <billsix@gmail.com>, 2026-11-24): this is a copy, not a rewrite.** This repository
(`modelviewprojection/modelviewprojection`, GitHub `billsix/modelviewprojection`) is **left exactly as it is**: not renamed, not
cleaned, not rewritten, no longer actively maintained, kept for historical reference, superseded by the new repository. The new
repository is **`Programming3DComputerGraphics`**, directory `/mnt/sda1/Programming3DComputerGraphics` (an empty `git init`, no
remote yet; the maintainer will create `github.com/billsix/Programming3DComputerGraphics` and add it as a remote named `github`).

**The deletion of the ports is part of this task, and it is done by not copying them** (the maintainer's wording, 2026-11-24: "only copying over the non port stuff to the new repo"): there is no separate deletion step, in either repository. Nothing is removed from this repository, and the new one never receives the ports.

The work: 1. copy every commit of this repository into the new one with all port code removed (`git filter-repo`, run on a
fresh clone in a scratch directory, never on this checkout; the result is then pushed or fetched into the new directory).
`src/modelviewprojection/mathutils.py` stays. `src/modelviewprojection/pgzero_gl/` goes with the Code the Classics games if question 2 of
`tasks/extract-code-the-classics-to-own-repo.md` is answered yes (recommended; it is awaiting the maintainer), otherwise it stays. 2. Clean the port references from the new tip with a normal commit.
Done means: the new repository has the same number of commits as this one (less any the maintainer chooses to drop, question 2),
each new commit's tree equals the old commit's tree minus the removed paths (proved by a script), the tags map across, nothing
ported remains in any commit's tree, the tip builds and passes the gates, and this repository's working tree and history are
byte-for-byte unchanged (`git status` clean and `git rev-parse` of every ref equal before and after). The copy command is built
as an ad-hoc script under `tasks/adhoc/copy-history-without-ports/` and, when it has run once and proved itself,
**promoted to a tool in `github.com/billsix/runClaudeInContainer` and `github.com/billsix/runCrushInContainer`** (see Promotion).

## Context (read first)

- **Facts measured 2026-11-23** (checkout at `master`, 2026-11-15 last commit): 1,440 commits on `master`, 1,653 across all
  refs, `.git` 629 MB, not shallow. Refs: `master`, local `doctests`, local and remote `morePorts`, `origin/claudeCode`,
  `github/geometricalgebra`, `origin/geometricalgebra`. Tags: `0.0.02`, `v0.0.3`. Remotes: `github`
  (`git@github.com:billsix/modelviewprojection.git`) and `origin` (the maintainer's self-hosted box).
- **Five port trees exist in history, not two.** File touches under each across all refs: `ports/codetheclassics` 4,876,
  `ports/McNopper` 2,221, `ports/openglsuperbiblev4` 1,407, `ports/openglsuperbiblev7` 1,163, `ports/openglredbook9` 719.
  The McNopper, SuperBible 7 and Red Book 9 ports were already moved out to their own repositories' `python` branches
  (`github.com/billsix/OpenGL`, `github.com/billsix/sb7code`, `github.com/billsix/openglredbook9examples`) and deleted from
  the tip, but they remain in history; "removes any of the code that did a port" means all five. 82 commits touch
  `ports/` today and 23 of those touch nothing else (they become empty after the rewrite).
- **Port-support files outside `ports/`.** At the tip: `tools/ctc_gate_all.sh`, `tools/ctc_verify_game.sh`,
  `tools/ctc_state_trace.py`, `tools/ctc_compare_traces.py`, `tools/ctc_capture_frame.py`, `tools/ctc_profile_update.py`,
  and the reference docs `tasks/reference/superbible-ports-guide.md`, `tasks/reference/gl-and-imgui-gotchas.md`,
  `tasks/reference/code-the-classics-tightening.md`, `tasks/reference/coordinate-spaces-in-code-the-classics.md`,
  `tasks/reference/pgzero-gl-design-for-a-personal-learning-library.md` and the games' part of
  `tasks/reference/tests-and-gates.md`. In history only (already deleted from the tip, verified 2026-11-23):
  `tools/mcnopper/proofs`, `tasks/adhoc/resync-mcnopper-ports/`, `tasks/adhoc/redbook9-fidelity-audit-vs-cpp/`,
  `tasks/adhoc/mcnopper-keyword-arguments/`, `tasks/adhoc/superbible-v4-globals-singleton-and-types/`,
  `tasks/resync-mcnopper-ports-with-upstream.md` and `tasks/reference/ports/`. Question 4.
- **Port references at the current tip that must be edited by a normal commit after the rewrite** (found with `git grep -l
  "ports/"`): `.gitignore`, `CLAUDE.md`, `Makefile` (lines near 221 and 234), `README.md`, `entrypoint/format.sh` (the
  `ruff` and `ty check` lines for `ports/`), `pyproject.toml` (per-file ignores for `ports/**`), `tools/keywordify.py`, and
  `src/modelviewprojection/pgzero_gl/LICENSE` and `__init__.py` (comments naming the games). A rewrite cannot edit what a
  file said; only a new commit can.
- **Consequences of keeping this repository as it is.** Nothing is renamed, so the old GitHub URL, stars, forks, issues, releases,
  Actions history and the book's Pages site (`http://billsix.github.io/modelviewprojection/intro.html`) stay with this repository
  and keep working. The new repository starts with none of them: its Pages URL, CI (`.github/workflows/checks.yml` and
  `release.yml`) and releases are new (question 5; the standing question is `tasks/release-book-github-pages-decision.md`). The Python
  package inside stays named `modelviewprojection`; only the repository name changes.
- **SHA rot only runs one way.** Every commit in the new repository has a new hash, but every old hash stays valid in this
  repository, so docs elsewhere that cite an old hash (for example the Python port's `ba922794` cited from
  `github.com/billsix/OpenGLSuperBibleV4Code` task docs) keep resolving against this repository. Citations inside the new repository
  must be repointed with `git filter-repo`'s `.git/filter-repo/commit-map` (old hash, new hash); where a cited commit was
  removed or emptied, say "see `github.com/billsix/modelviewprojection`".

## What stays at the new tip and what goes (verified 2026-11-24)

The full lists are in the two sibling tasks, so each is written once: the SuperBible v4 table is in
`tasks/python-port-into-master.md` of `github.com/billsix/OpenGLSuperBibleV4Code` ("Which mvp demos stay and which go"), the
Code the Classics table is in `tasks/extract-code-the-classics-to-own-repo.md` here. The result, for this task's removal list:

- **STAYS (curriculum, not ports):** demos `demo19a`–`demo19e`, `demo22`, `demo22a`, `demo22b`, `demo23`, `demo24` with their own
  shaders and textures (`Block4/5/6.tga`, `floor.tga`, `stone.tga`, `grass/wood/orb.tga` and the `.vert`/`.frag` files in their
  directories), `src/modelviewprojection/mathutils.py`, and demos 01–21. `src/modelviewprojection/pgzero_gl/` is undecided: it is
  excluded from the copy (like the ports) if the pgzero question above is answered yes, kept otherwise. None reads
  a file under `ports/`, so deleting the five port trees cannot break them.
- **GOES (not copied):** the five `ports/` trees (including the SuperBible v4 counterparts of the curriculum demos), `tools/ctc_*`,
  `tools/keywordify.py` (moves to the SuperBible repository), `tests/test_ctc_actor_field_collisions.py`.
- **Edited at the new tip:** the files in the list above ("Port references at the current tip"), plus the `pgzero_gl` docstring
  and `LICENSE` that name the games if `pgzero_gl` stays. The new `README.md` drops the link to the book's Pages URL (question 5:
  there are no Pages for the new repository yet) and says the book is built locally.

## Plan (each phase is a staging boundary; the maintainer performs every GitHub action and push)

1. Fresh clone of this repository into a scratch directory (never rewrite this checkout). Record `git rev-list --all --count`, the
   tag list, the ref list, and `git rev-parse` of every ref here, to prove at the end that this repository did not change.
2. Write `tasks/adhoc/copy-history-without-ports/copy.sh`: `git filter-repo --invert-paths` with one `--path` per removed tree (the
   five `ports/` trees, plus whatever question 4 adds), `--prune-empty never` (so a commit that only touched ports stays as an empty
   commit, which is what "every single commit" asks; question 2), and tags kept; then fetch the result into
   `/mnt/sda1/Programming3DComputerGraphics`. Every path is relative; no container paths.
3. Write `.../verify.sh`: for every pair in `commit-map`, check that
   `git diff --quiet <old> <new> -- . ':!ports/<each removed tree>' ...` holds, so the new tree is the old tree minus the removed
   paths; also check commit count, author and date preservation (`git log --format='%an %ae %ad'` equal), tag targets, and that
   `git ls-tree -r` of every new commit contains no removed path. Idempotency: run the copy twice on fresh clones and compare the
   resulting hashes. Last check: the refs recorded in step 1 are unchanged in this repository.
4. Tip commit in the new repository: clean the references listed in Context, run the gates (`make format` and whatever
   `.github/workflows/checks.yml` runs), fix what they report.
5. Repoint SHA citations that sit inside the new repository, using the commit map. (Citations in other repositories keep pointing
   at this one and need no change.)
6. The maintainer, on GitHub: create `billsix/Programming3DComputerGraphics`, add it as the `github` remote of
   `/mnt/sda1/Programming3DComputerGraphics`, push `master` and tags (refs per question 3). Nothing is renamed or archived on GitHub.
7. Final checks: the new clone builds the book and runs the demos from `make shell`; the two extracted repositories' dependency
   pins point at the new repository (task 2, question 2).

## Promotion (marked as the maintainer asked)

After the script has run once and `verify.sh` is green, promote both to `tools/` in `github.com/billsix/runClaudeInContainer`
and `github.com/billsix/runCrushInContainer` (the Crush copy goes under its `tools/` as well), with a docstring and usage
note, as `tools/copy_history_without_paths.sh` (parameters: source clone, list of paths, output directory) and
`tools/verify_history_copy.sh`. Verified 2026-11-23: `git-filter-repo` is already installed in both sandboxes
(`entrypoint/01-install-base.sh` in each), so no package change is needed. Add a line to each sandbox's capability map
(`sandbox-capability-map.md` in the shared reference set) and propose, do not auto-wire, a gate. The ad-hoc copy is then `git
rm`'d in this task's archive commit.

## Open questions

1. Name for the new repository: answered 2026-11-24, `Programming3DComputerGraphics` (William Emerison Six
   <billsix@gmail.com>; local directory `/mnt/sda1/Programming3DComputerGraphics`). This repository is not renamed.
   Related: the maintainer confirmed 2026-11-24 that this task is the "rewriting of history" in the sense of copying only the
   non-port files, with no separate deletion.
2. Answered 2026-11-24 ("go with your recommendations"): keep the 23 commits that touched only ports as empty commits
   (`--prune-empty never`, the new history has the same 1,440 commits), with their messages, so it stays comparable one-to-one
   with this repository.
3. Answered 2026-11-24: carry `master` and both tags only; `doctests`, `morePorts`, `claudeCode` and `geometricalgebra` stay only in
   this repository (the last is a stale copy of a project now in its own repository).
4. Answered 2026-11-24: strip the port code from history (`tools/ctc_*`, the history-only `tools/mcnopper/` and port-only
   `tasks/adhoc/` directories), keep task and reference documents (they record decisions and are small), and list the kept ones
   so nothing dangles.
5. Answered 2026-11-24: no GitHub Pages, no releases, and no GitHub work at all as part of this task (the maintainer has made no
   Pages site and does not want one yet). The standing decision is the existing task `tasks/release-book-github-pages-decision.md`,
   which now also covers the new repository; nothing here depends on it.
6. Answered 2026-11-24: the maintainer creates the bare repository on the self-hosted box later and cannot push yet. The `origin`
   remote of `/mnt/sda1/Programming3DComputerGraphics` is added now, pointing at the path the box's other repositories use; nothing
   is pushed. The `github` remote is added when the maintainer creates the GitHub repository.
7. Answered 2026-11-24 ("go with your recommendations"): add one "superseded, no longer maintained" notice (a paragraph at the top
   of `README.md` and `CLAUDE.md` pointing at `github.com/billsix/Programming3DComputerGraphics`) to this repository; it is the
   only edit this repository gets.
