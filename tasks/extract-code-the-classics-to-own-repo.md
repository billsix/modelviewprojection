# Move the Code the Classics ports into a new CodeTheClassics repository

**Status:** proposed — needs go-ahead, the new repository, and the answers below (filed 2026-11-23)
**Priority:** 6
**Difficulty:** 5
**Created:** 2026-11-23
**Part of:** a three-task split, the maintainer's plan (William Emerison Six <billsix@gmail.com>, 2026-11-23): task 1 is
`tasks/python-port-into-master.md` in `github.com/billsix/OpenGLSuperBibleV4Code`, this is task 2, and task 3 is
`tasks/rewrite-history-without-ports.md` here. Task 3 must not start until tasks 1 and 2 are done.
**Depends on:** the maintainer adding the GitHub remote. The directory `/mnt/sda1/CodeTheClassics` exists with an empty
`git init` and no remote (2026-11-24); the maintainer will create `github.com/billsix/CodeTheClassics` and add it as a remote
named `github`. The name in question 1 is therefore settled.

## BLUF

`ports/codetheclassics/` here (ten games, 140 MB: vol1 `boing` `bunner` `cavern` `myriapod` `soccer`, vol2 `avenger`
`beatstreets` `eggzy` `kinetix` `leadingedge`) is a Python and OpenGL 3.3 translation of Raspberry Pi Press's *Code the
Classics* games from PyGame Zero. Move it into a new repository that holds the code for both volumes, with links to the
upstream sources, and has `modelviewprojection` and `gacalc` as dependencies rather than carrying their code. Done means:
a fresh clone of the new repository runs every game from its own container (`make shell`), the licence notices are intact,
the games' reference docs and open tasks have moved, and nothing here has been deleted yet (task 3 deletes).

## Context (read first)

- **This is not the same shape as the SuperBible and Red Book moves.** Those added a `python` branch beside an upstream's
  C or C++ (`github.com/billsix/sb7code`, `github.com/billsix/openglredbook9examples`, `github.com/billsix/OpenGL`,
  and task 1). Code the Classics has no C twin: the originals are Python (PyGame Zero) and are not in this repository, so
  the new repository is a standalone one whose `README.md` links the upstream rather than a branch of it. Upstream
  sources: volume 1 is `github.com/Wireframe-Magazine/Code-the-Classics` (found on the publisher's announcement; both
  upstream URLs below are unverified until opened); volume 2 has no repository I could confirm (a personal
  `github.com/russeg/Code-the-Classics-Vol2` exists but is not official); the licence file here names the Debian source
  tarballs `code-the-classics_0.3.tar.xz` and `code-the-classics-2_0.1.tar.xz` on `archive.raspberrypi.org`. The books'
  pages are at `magazine.raspberrypi.com/books/code-the-classics1` and `magpi.raspberrypi.com/books/code-the-classics-vol-ii`.
- **Layout today:** `ports/codetheclassics/{vol1,vol2}/<game>/<game>.py`, one file per game with its own `images/`, `sounds/`
  and `music/` (vol2 adds tilemaps), plus `LICENSE` and `README.md` (run, verify, layout, licensing). Each game file is
  readable top to bottom: its own engine (renderer, `Actor`, `Rect`, keyboard, loop) inlined, then the game. The standard
  they were tightened to is `tasks/reference/code-the-classics-tightening.md`; the coordinate model is
  `tasks/reference/coordinate-spaces-in-code-the-classics.md`.
- **Dependencies on this repository:** the games import the shared package `modelviewprojection.pgzero_gl`
  (`audio` 11 files, `resources` 11, `gl` 10; LGPL-2.1, `src/modelviewprojection/pgzero_gl/`), `modelviewprojection.mathutils`
  (13 call sites across the ports) and `gacalc` (`g2`, `g3`, `transforms`; `github.com/billsix/geometricalgebra`).
  `pgzero_gl` is a compatibility library that stays in `modelviewprojection` (the maintainer's decision), so the new
  repository depends on it. Design notes: `tasks/reference/pgzero-gl-design-for-a-personal-learning-library.md`.
- **Licences:** the game code is BSD-2-Clause, copyright Eben Upton (2019 vol 1, 2024 vol 2), derived from the Debian
  packaging; the inlined engine in each game file is BSD-2-Clause, copyright William Emerison Six; `pgzero_gl` is
  LGPL-2.1. `ports/codetheclassics/LICENSE` carries all of it; copy it verbatim. The `images/`, `sounds/` and `music/`
  files are upstream's; this repository's licence file speaks only about code, so redistributing the assets is the same kind
  of question the maintainer decided for the SuperBible 7 media pack (committed deliberately, flagged as a possible
  licensing concern; `tasks/archive/2026/10/19/pythonize-and-containerize-port.md` in `github.com/billsix/sb7code`).
  Question 3.
- **Verification tooling to move:** `tools/ctc_verify_game.sh` (frame N pixel-identical to a baseline commit),
  `tools/ctc_state_trace.py`, `tools/ctc_compare_traces.py`, `tools/ctc_capture_frame.py`, `tools/ctc_profile_update.py`,
  `tools/ctc_gate_all.sh`, and the gate section in `tasks/reference/tests-and-gates.md`. They assume this repository's image
  and a baseline `HEAD`; they need re-pointing.
- **This repository's gates mention the games** (`entrypoint/format.sh`: `ruff` and `ty check ports/codetheclassics/vol1`
  and `vol2`; `Makefile` lines for the same; `pyproject.toml` per-file ruff ignores for `ports/codetheclassics/**`;
  `README.md`, `CLAUDE.md`, `.gitignore`). Cleaning those is task 3's tip commit, but list them here so nothing is missed.
- **Container:** this repository's `Dockerfile` and `Makefile` are the template (the container-per-project layout in the
  maintainer's conventions); the games need glfw, PyOpenGL, numpy, imageio, a display (X11 or Wayland), and audio.

## What stays in mvp and what goes after this port (verified 2026-11-24; task 3 does the deleting)

No remaining mvp demo, test (apart from the one listed) or book page imports from `ports/codetheclassics/` or reads its assets
(`git grep` over `src`, `tests`, `book/docs`, `notebooks`, `assignments`).

| Path | After the move |
|---|---|
| `src/modelviewprojection/pgzero_gl/` (`audio.py`, `gl.py`, `resources.py`, `LICENSE`, `py.typed`) | **STAYS** (maintainer's decision); the new repository depends on it. Its docstring and `LICENSE` name the games and need rewording at task 3's tip commit. No in-tree consumer remains once the games leave. |
| `src/modelviewprojection/mathutils.py` | **STAYS** (the demos' own module; 13 game call sites move out) |
| `ports/codetheclassics/` (10 games, their `images/`, `sounds/`, `music/`, `LICENSE`, `README.md`) | **GOES** |
| `tools/ctc_gate_all.sh`, `ctc_verify_game.sh`, `ctc_state_trace.py`, `ctc_compare_traces.py`, `ctc_capture_frame.py`, `ctc_profile_update.py` | **GO** (copied to the new repository and re-pointed) |
| `tests/test_ctc_actor_field_collisions.py` (reads `ports/codetheclassics`) | **GOES**; copy it to the new repository |
| `tasks/reference/code-the-classics-tightening.md`, `coordinate-spaces-in-code-the-classics.md`, `pgzero-gl-design-for-a-personal-learning-library.md`, the games' part of `tests-and-gates.md` | copied; mvp keeps the `pgzero_gl` design doc (it describes a library that stays) |
| gate and config lines naming the games (`entrypoint/format.sh`, `Makefile`, `pyproject.toml`, `.gitignore`, `README.md`, `CLAUDE.md`) | **edited** at task 3's tip commit |

## Plan (each phase is a staging boundary)

1. The maintainer creates the repository; add it as a remote named `github` (not `origin`).
2. Copy `ports/codetheclassics/` to the new repository's root as `vol1/` and `vol2/`; carry `LICENSE` and `README.md`;
   rewrite the README to name the two upstreams with links and to say these are translations to GLFW and OpenGL 3.3.
3. Container (`Dockerfile`, `Makefile`: `image`, `shell`, `shell-exec`, `run GAME=vol1/boing`, `check`, `format`,
   `type-check`), `pyproject.toml` with the ruff and `ty` settings that apply to the games, and a dependency on
   `modelviewprojection` and `gacalc` pinned by URL and commit (question 2).
4. Move the verification tools and re-point them; run the frame gate on at least `boing` and `eggzy`.
5. Docs: copy `code-the-classics-tightening.md`, `coordinate-spaces-in-code-the-classics.md` and the games' parts of
   `tests-and-gates.md` into `tasks/reference/` of the new repository, rewritten to read against it alone; move the open
   tasks about the games (none are open today; scan `tasks/` for `ctc-` and `codetheclassics-` at the time).
6. Gates: format, type-check, import every game with `PGZERO_MAX_FRAMES=120` under Xvfb.
7. Stage and leave the commit to the maintainer. Do not delete anything here; task 3 does.

## Open questions

1. Repository name: answered 2026-11-24, `CodeTheClassics` (William Emerison Six <billsix@gmail.com>; local directory
   `/mnt/sda1/CodeTheClassics`, GitHub remote to be added).
2. How does the new repository get `modelviewprojection`? It is not on PyPI (it installs editable from a checkout). Options:
   (a) `pip install git+https://github.com/billsix/modelviewprojection@<commit>` in the image; (b) a git submodule;
   (c) clone it in the Dockerfile. Recommend (a), pinned to a commit of the rewritten repository (task 3), which means
   task 3 should finish first or the pin must be updated afterwards.
3. Assets: commit the 140 MB of upstream images, sounds and music (as the mvp tree does today), or fetch them from the
   Debian source tarballs at image build time, as sb7code does with its media pack? Recommend: fetch at build time and
   commit nothing, unless the maintainer wants to ship them (the licence question above).
4. Volume 2's upstream repository link: is there an official one, or should the README cite the book page and the Debian
   tarball only?
5. Should the new repository's history carry the history of these games (4,876 file touches under `ports/codetheclassics` across all refs, 2026-11-23) (via `git filter-repo --path
   ports/codetheclassics --path-rename ports/codetheclassics/:`), as in question 1 of task 1? Recommend: yes.
