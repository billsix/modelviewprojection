# Archive this repository, and publish a copy of every commit with the ports removed

**Status:** proposed — needs go-ahead, the answers below, and tasks 1 and 2 finished first (filed 2026-11-23)
**Priority:** 7
**Difficulty:** 6
**Created:** 2026-11-23
**Part of:** the maintainer's three-task split (William Emerison Six <billsix@gmail.com>, 2026-11-23): task 1 is
`tasks/python-port-into-master.md` in `github.com/billsix/OpenGLSuperBibleV4Code`, task 2 is
`tasks/extract-code-the-classics-to-own-repo.md` here, this is task 3.
**Depends on:** tasks 1 and 2 done and their repositories pushed (this task deletes the only other copy of the ports'
working tree from the new history; the archived repository keeps the old one).

## BLUF

1. Rename the GitHub repository `billsix/modelviewprojection` to `billsix/modelviewprojection-archived` (the maintainer does
   this on GitHub). 2. Create a new repository and push to it a rewritten copy of every commit with all port code removed
(`git filter-repo`, from a fresh clone). Compatibility libraries stay (`src/modelviewprojection/pgzero_gl/`,
`src/modelviewprojection/mathutils.py`), and the extracted repositories may depend on `modelviewprojection` and `gacalc`.
3. Clean the port references from the new tip. Done means: the new repository has the same number of commits as the old
one (less any the maintainer chooses to drop, question 2), each new commit's tree equals the old commit's tree minus the
removed paths (proved by a script), the tags map across, nothing ported remains in any commit's tree, and the tip
builds and passes this repository's gates. The rewrite command is built as an ad-hoc script under
`tasks/adhoc/rewrite-history-without-ports/` and, when it has run once and proved itself, **promoted to a tool in
`github.com/billsix/runClaudeInContainer` and `github.com/billsix/runCrushInContainer`** (see Promotion).

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
- **GitHub effects the maintainer should know before renaming:** the old URL redirects to the renamed repository until
  another repository takes the name (the new repository will, if it reuses `modelviewprojection`: question 1). Stars,
  watchers, forks, issues, releases and Actions history stay with the archived repository. `README.md` links the book at
  `http://billsix.github.io/modelviewprojection/intro.html` (GitHub Pages); `tasks/release-book-github-pages-decision.md`
  is the standing question of whether Pages is used at all. CI is `.github/workflows/checks.yml` and `release.yml`.
- **SHA rot.** Every commit hash changes. Docs here and in other repositories cite old hashes (for example the Python
  port's `ba922794` cited from `github.com/billsix/OpenGLSuperBibleV4Code` task docs). The maintainer's convention is to
  repoint a dead SHA to its replacement or drop it. `git filter-repo` writes `.git/filter-repo/commit-map` (old hash,
  new hash); use it to repoint citations, and where a cited commit was removed or emptied, say "see
  `modelviewprojection-archived`".

## What stays at the new tip and what goes (verified 2026-11-24)

The full lists are in the two sibling tasks, so each is written once: the SuperBible v4 table is in
`tasks/python-port-into-master.md` of `github.com/billsix/OpenGLSuperBibleV4Code` ("Which mvp demos stay and which go"), the
Code the Classics table is in `tasks/extract-code-the-classics-to-own-repo.md` here. The result, for this task's removal list:

- **STAYS (curriculum, not ports):** demos `demo19a`–`demo19e`, `demo22`, `demo22a`, `demo22b`, `demo23`, `demo24` with their own
  shaders and textures (`Block4/5/6.tga`, `floor.tga`, `stone.tga`, `grass/wood/orb.tga` and the `.vert`/`.frag` files in their
  directories), `src/modelviewprojection/pgzero_gl/`, `src/modelviewprojection/mathutils.py`, and demos 01–21. None reads
  a file under `ports/`, so deleting the five port trees cannot break them.
- **GOES:** the five `ports/` trees (including the SuperBible v4 counterparts of the curriculum demos), `tools/ctc_*`,
  `tools/keywordify.py` (moves to the SuperBible repository), `tests/test_ctc_actor_field_collisions.py`.
- **Edited at the tip:** the files in the list above ("Port references at the current tip"), plus the `pgzero_gl` docstring
  and `LICENSE` that name the games.

## Plan (each phase is a staging boundary; the maintainer performs every GitHub action and push)

1. Fresh clone of the current repository into a scratch directory (never rewrite the working checkout). Record
   `git rev-list --all --count`, the tag list, and the ref list.
2. Write `tasks/adhoc/rewrite-history-without-ports/rewrite.sh`: `git filter-repo --invert-paths` with one `--path` per
   removed tree (the five `ports/` trees, plus whatever question 4 adds), `--prune-empty never` (so a commit that only
   touched ports stays as an empty commit, which is what "every single commit" asks; question 2), and tags kept.
   Every path is relative; no container paths.
3. Write `.../verify.sh`: for every pair in `commit-map`, check that
   `git diff --quiet <old> <new> -- . ':!ports/<each removed tree>' ...` holds, so the new tree is the old tree minus the
   removed paths; also check commit count, author and date preservation (`git log --format='%an %ae %ad'` equal), tag
   targets, and that `git ls-tree -r` of every new commit contains no removed path. Idempotency: run the rewrite twice on
   fresh clones and compare the resulting hashes.
4. Tip commit in the rewritten clone: clean the references listed in Context, run this repository's gates (`make format`
   and whatever `.github/workflows/checks.yml` runs), fix what they report.
5. Repoint SHA citations in docs that cite old hashes (here and in `github.com/billsix/OpenGLSuperBibleV4Code`,
   `github.com/billsix/sb7code`, `github.com/billsix/OpenGL`, `github.com/billsix/openglredbook9examples`, and the new
   Code the Classics repository), using the commit map.
6. The maintainer, on GitHub: rename the old repository to `modelviewprojection-archived`; create the new one; add it as the
   `github` remote of a clone; push `master` and tags (refs per question 3). Locally: rename the old remote to `archived`.
7. Final checks: the new clone builds the book and runs the demos from `make shell`; the two extracted repositories'
   dependency pins point at the new repository.

## Promotion (marked as the maintainer asked)

After the script has run once and `verify.sh` is green, promote both to `tools/` in `github.com/billsix/runClaudeInContainer`
and `github.com/billsix/runCrushInContainer` (the Crush copy goes under its `tools/` as well), with a docstring and usage
note, as `tools/rewrite_history_without_paths.sh` (parameters: source clone, list of paths, output directory) and
`tools/verify_history_rewrite.sh`. Verified 2026-11-23: `git-filter-repo` is already installed in both sandboxes
(`entrypoint/01-install-base.sh` in each), so no package change is needed. Add a line to each sandbox's capability map
(`sandbox-capability-map.md` in the shared reference set) and propose, do not auto-wire, a gate. The ad-hoc copy is then `git
rm`'d in this task's archive commit.

## Open questions

1. Name for the new repository: reuse `modelviewprojection` (links, `pip` pins and the Pages URL keep working once the
   old repository is renamed) or a new name? Recommend: reuse it.
2. "Every single commit": keep the 23 commits that touched only ports as empty commits (`--prune-empty never`, the new
   history has the same 1,440 commits) or let `filter-repo` drop them (cleaner, 1,417)? Recommend: keep them, with their
   messages, so the history stays comparable one-to-one with the archive.
3. Which refs to carry? Recommend: `master` and both tags only; `doctests`, `morePorts`, `claudeCode` and
   `geometricalgebra` stay in the archive (the last is a stale copy of a project now in its own repository).
4. Port-support files outside `ports/` (tools and ad-hoc scripts and task docs named in Context): strip them from history
   too, or keep them? Recommend: strip the code (`tools/ctc_*`, and the history-only `tools/mcnopper/` and port-only `tasks/adhoc/` dirs),
   keep task and reference documents (they record decisions and are small), and list them so nothing dangles.
5. GitHub Pages and releases: the book's Pages URL is tied to the repository name; should Pages be re-enabled on the new
   repository (the standing question in `tasks/release-book-github-pages-decision.md`), and should the tagged releases be
   recreated there? Recommend: decide Pages first; recreate releases only if people download them.
6. The self-hosted `origin` remote: create a matching bare repository for the new history and rename the old one, or leave
   `origin` alone? Recommend: mirror the same rename there so `origin` and `github` agree.
