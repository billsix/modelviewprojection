# The Code the Classics games, moved into their own repository

**Done:** 2026-11-24 (work commit; the archive move follows). Task 2 of a three-task split, the maintainer's plan (William
Emerison Six <billsix@gmail.com>, 2026-11-23): task 1 is `tasks/archive/2026/11/24/python-port-into-master.md` in
`github.com/billsix/OpenGLSuperBibleV4Code`, task 3 is `tasks/copy-history-without-ports.md` in
`github.com/billsix/modelviewprojection`. The maintainer answered the five open questions (2026-11-24); the answers are below.

## What was done

`ports/codetheclassics/` (ten games, 11 files, 140 MB) and the shared package `pgzero_gl` moved from
`github.com/billsix/modelviewprojection` into this repository (`github.com/billsix/CodeTheClassics`, a new repository; the GitHub
remote is the maintainer's to add and push). The repository is `vol1/`, `vol2/`, `pgzero_gl/`, `tools/`, `tests/`, `tasks/reference/`,
a container, and the games' `LICENSE` and `README.md`. Nothing was deleted from the course repository; task 3 copies its history
without these paths.

- **History came with it** (question 5: yes). `git filter-repo` on a fresh clone kept `ports/codetheclassics/`, `src/modelviewprojection/pgzero_gl/`,
  `tools/ctc_*` and `tests/test_ctc_actor_field_collisions.py`, renamed to the layout above. 50 commits; authorship and dates kept;
  the clone's `v0.0.3` tag was dropped. That history is `master`; the work is on the branch `container-docs-and-gates`.
- **`pgzero_gl` moved with the games** (question 2: yes). The games needed nothing else from the course (measured with `git grep`: only
  `pgzero_gl.{resources,audio,gl}`, no `mathutils`) and nothing else in the course used `pgzero_gl`. 53 import sites in 11 files were
  rewritten from `modelviewprojection.pgzero_gl` to `pgzero_gl` by `tasks/adhoc/extract-code-the-classics-to-own-repo/repoint_pgzero_gl.py`
  (idempotent: second run, zero changes; removed in the archive commit). The only dependency outside the repository is `gacalc==0.1.1`.
- **Assets committed** (question 3: "commit them"). 4,555 asset files, none over 20 MB. The README keeps the licence flag.
- **Upstream links** (question 4). The maintainer said to cite the book page and the Debian tarball only, on my claim that no
  official volume 2 repository was found. That claim was wrong: both `github.com/raspberrypipress/Code-the-Classics-Vol1` and `Vol2`
  answer HTTP 200 (checked 2026-11-24), and the maintainer's own README already named them. The README cites both repositories, the
  vol 1 book page, and the Debian tarballs named in `LICENSE`.
- **Container and gates.** One `Dockerfile` (Fedora 45): `entrypoint/01-install-base.sh` (a C++ compiler and Python headers, because
  `miniaudio` has no wheel for the newest Python and builds from source), `02-install-graphics.sh` (Mesa, Xvfb, Wayland, ALSA and
  PulseAudio client libraries), `03-install-python.sh` (`/venv` from `requirements.txt` and the `uv pip compile`d `constraints.txt`).
  `Makefile`: `image`, `shell`, `shell-exec`, `run GAME=vol1/boing`, `list`, `check`, `format`, `update-pins`. `pyproject.toml` holds the
  ruff, `ty` and pytest settings. New tools: `check_imports.py`, `run_game.sh`, `run_games_xvfb.sh`. The `ctc_*` gates were re-pointed
  (image `codetheclassics`, mount `/ctc`, paths without `ports/codetheclassics/`) and gained `BASELINE_SRC`.
- **Docs.** Five reference docs copied and re-pathed into `tasks/reference/` (`code-the-classics-tightening`,
  `coordinate-spaces-in-code-the-classics`, `pgzero-gl-design-for-a-personal-learning-library`, `gacalc-transforms-in-the-renderer`,
  `point-type-decision`) and one new, `gates-and-verification.md`. No open task about the games existed in the course repository.
  `LICENSE` was copied with its two path references corrected.

## Verification (container, 2026-11-24)

- `make format`: ruff idempotent and `ty` clean on `vol1`, `vol2`, `pgzero_gl`. `make check`: 15 of 15 modules import, 11 tests pass.
- `tools/run_games_xvfb.sh`: all 11 game files run 120 frames headless under Xvfb and exit 0.
- **Behaviour preserved across the move:** `REF=master BASELINE_SRC=<course repository src> tools/ctc_gate_all.sh` passed both gates on all 11
  game files: frame 180 pixel-identical (the baseline, the extracted `master` using `modelviewprojection.pgzero_gl`, run beside the working
  tree using `pgzero_gl`), and the 300-frame scripted-input state traces equal.

Not verified: audio and gamepad (never gated), a real display, and `make run` on Wayland (this sandbox has none).

## Owed

- The maintainer creates `github.com/billsix/CodeTheClassics`, adds it as the `github` remote, merges `container-docs-and-gates` into
  `master`, and pushes. Before the repository goes public, confirm asset redistribution with Raspberry Pi Press (flagged in the README).
- Task 3 does not copy `ports/codetheclassics/`, `pgzero_gl` or `tools/ctc_*` into `Programming3DComputerGraphics`.
