# Programming3DComputerGraphics: a copy of this repository's history without the ports

**Done:** 2026-11-24 (work commit; the archive move follows). Task 3 of a three-task split, the maintainer's plan (William Emerison
Six <billsix@gmail.com>, 2026-11-23): task 1 is `tasks/archive/2026/11/24/python-port-into-master.md` in
`github.com/billsix/OpenGLSuperBibleV4Code`, task 2 is `tasks/archive/2026/11/24/extract-code-the-classics-to-own-repo.md`. Design
decision (2026-11-24): a **copy**, not a rewrite. The maintainer also confirmed that "deleting the ports" means only not copying them.

## What was done

`/mnt/sda1/Programming3DComputerGraphics` (an empty `git init`) now holds all 1,446 commits of this repository's `master` and both tags
(`0.0.02`, `v0.0.3`), with these paths left out of every commit: `ports/` (the Code the Classics and SuperBible v4 trees, the only two
that `master` ever contained), `src/modelviewprojection/pgzero_gl/`, `tools/ctc_*`, `tools/keywordify.py`,
`tests/test_ctc_actor_field_collisions.py`, and the port-only ad-hoc directories (`tasks/adhoc/codetheclassics-tighten-games`,
`superbible-v4-globals-singleton-and-types`, `ctc-*`, `pgzero-gl-*`). The 23 commits that touched only those paths stayed as empty commits
with their messages, so the copy is one-to-one with this repository (`--prune-empty never --prune-degenerate never`). This repository is
unchanged: `git rev-parse master` was `3108efa5` before and after, and no file here was edited by the copy. The copy is `master`
(tip `2f608e28`); the cleanup of the tip is on the branch `tip-cleanup`, for the maintainer to merge.

- **Tip cleanup (a normal commit on `tip-cleanup`).** `CLAUDE.md` and `README.md` say this is the successor of `github.com/billsix/modelviewprojection`
  and point to where the ports went; the `ports/` mentions are gone from `Makefile` (`type-check`), `entrypoint/format.sh`, `pyproject.toml`
  (per-file ignores and their comments) and `.gitignore`; `book/docs/intro.rst` links the new repository; `README.md` no longer links the
  Pages site (there is none yet, question 5). Eight reference docs that describe moved code carry a "Historical copy" banner and are otherwise
  kept (question 4). The five task docs about the SuperBible port moved to `OpenGLSuperBibleV4Code`, and the two extraction task docs became
  done-records, so none of them stays as an open task here. 18 old commit hashes cited in docs were repointed with the commit map.
- **Nothing on GitHub was touched** and nothing was pushed (question 5, question 6). The `origin` remote of the new directory points at the
  self-hosted box's path for `Programming3DComputerGraphics.git`, which the maintainer creates later.
- **This repository got one edit** (question 7): a superseded notice at the top of `README.md` and `CLAUDE.md`.
- **Tools.** The copy and its verifier were built under `tasks/adhoc/copy-history-without-ports/` and promoted, after they had run and
  proved themselves, to `tools/copy_history_without_paths.sh` and `tools/verify_history_copy.py` in `github.com/billsix/runClaudeInContainer`
  and `github.com/billsix/runCrushInContainer` (branch `copy-history-tools` in each; a line in the sandbox capability map). The ad-hoc copies were
  removed in the archive commit.

## Verification

- `verify_history_copy.py`: **1,446 commits checked, 0 failures** (per commit: the tree equals the old tree minus the left-out paths, with the
  same modes and blobs; author and committer name, email and date equal; parents equal to the mapped parents; commit counts equal; both tags
  point at the mapped commits). 9 messages differ only because `git filter-repo` rewrites old hashes quoted in a message. A negative control (the
  same check with `ports` not listed) reported 456 failures, so the verifier does fail when it should.
- Idempotent: a second copy into a fresh repository produced a byte-identical commit map and the same tip hash.
- `git ls-tree -r master` of the copy has no `ports/`, `pgzero_gl` or `ctc_` path. `.git` is 26 MB (this repository's is 632 MB).
- Gates on the cleaned tip, in the container with the default flags: `make check-format` exit 0 (the formatter changed nothing), `make type-check`
  exit 0, `make test` 55 passed.

Not done: nothing was built or run on a real display from the copy (the demos are unchanged), and `make docs` was not run (the book sources
are untouched except the one link in `intro.rst`).

## Owed

- The maintainer creates `github.com/billsix/Programming3DComputerGraphics`, adds it as the `github` remote of `/mnt/sda1/Programming3DComputerGraphics`,
  creates the bare repository on the self-hosted box for `origin`, merges `tip-cleanup` into `master`, and pushes `master` and the tags.
  `git rev-parse master` in the copy must be `2f608e28` before the merge (the tip of the history copy).
- *(optional, recommended)* `requirements.txt` still lists packages only the ports used: `miniaudio` and `OpenEXR` (nothing under `src`, `tests` or
  `tools` imports them). Removing them and re-pinning `constraints.txt` shrinks the image; it was left alone because it changes the image and
  was not asked for.
- *(optional)* Decide on GitHub Pages for the new repository: `tasks/release-book-github-pages-decision.md`.
