# Lean image for nested-podman builds — what "minimal" means for modelviewprojection

**Status:** proposed — research done 2026-09-10 (survey of the Dockerfile + Makefile from the
runClaudeInContainer sandbox); **implementation needs go-ahead**. One of the per-project children of
runClaudeInContainer `tasks/minimal-image-for-nested-podman-standard.md` (the convention: every optional-feature build flag defaults to its lean value when
`NESTED_PODMAN=1`); the fleet-wide findings table is runClaudeInContainer `tasks/reference/minimal-nested-images.md`. Created 2026-09-10 at the maintainer's
request (William Emerison Six <billsix@gmail.com>: "go through all of my projects with CLAUDE.md …
research what a minimal nested podman container would be for them").
**Priority:** 3
**Difficulty:** 3

## BLUF

Make `make image` inside a sandbox (which exports `NESTED_PODMAN=1`) build a lean image that fits
the nested RAM store and still runs this project's gate, while a host `make image` stays
byte-identical — via the idiom `FLAG ?= $(if $(filter 1,$(NESTED_PODMAN)),0,1)` on each optional-feature flag (the `PODMAN_RUN_FLAGS`
pattern applied to build flags; reference implementation: runCrushInContainer `client/Makefile`,
`FULL_TOOLCHAIN`). Done = the flags below carry the nested-aware default, a nested `make image`
builds and passes the gate, both image sizes are measured and recorded here and in `CLAUDE.md`.

## Context — read first

- runClaudeInContainer `tasks/reference/minimal-nested-images.md` — the standard, the idiom, the rules (a project's *gates* and *product build deps* are never
  trimmed; only editors, docs toolchains, notebooks, GUI extras), and every project's row.
- This repo's `Dockerfile`, `Makefile` (flag block + `image` target), `entrypoint/*install*.sh`.
- The flag-coverage rule (cross-project `CLAUDE.md` › "Verification gates in nested containers"): a
  lean build verifies nothing about the layers it skips — when a change touches what a skipped layer
  consumes, build with that flag ON.

## Findings (2026-09-10)

**What the image installs today.** Flags `BUILD_DOCS` (1: TeX, sphinx, inkscape, ImageMagick, gnuplot, graphviz, mathjax + texExpToPng built from a pinned clone), `USE_EMACS` (1), `USE_JUPYTER` (1: jupyter/jupyterlab/ffmpeg/moviepy), `USE_X_WINDOWS` (1: mesa-dri-drivers + X/Wayland client libs), `USE_SPYDER` (0). Unconditional: the GL/Python runtime (glfw, pyopengl, numpy, sympy, wxpython, pytest, ruff, ty, uv) + venv + pyright. **Also found: this checkout's Makefile has no `PODMAN_RUN_FLAGS` line at all** (the 2026-08-29 rollout record says mvp was converted — the branch checked here is `morePorts`; verify on master).

**What "minimal" is here.** Nested default: `USE_EMACS=0`, `USE_JUPYTER=0`. **Keep `USE_X_WINDOWS=1`** — it installs `mesa-dri-drivers`, which is what makes the headless Xvfb-in-sandbox rendering of the demos work (CLAUDE.md's verified recipe); and **keep `BUILD_DOCS=1`** — `make html` is the book gate and the doc-region checker runs in-container; a lean image that can't build the book would silently pass book-breaking edits (flag-coverage rule).

**Notes.** Emacs here also pulls `python3-lsp-server` for its LSP config — that goes with it. The 'do not change the Dockerfile for mvp' instruction (2026-07-18) was about adding xvfb to the image; flipping defaults in the Makefile touches no Dockerfile line — but confirm before touching the Dockerfile at all.

## Plan

- [ ] Makefile: `USE_EMACS` and `USE_JUPYTER` get the nested-aware default; `BUILD_DOCS` and `USE_X_WINDOWS` keep `?= 1` with a comment naming the two verification paths they serve.
- [ ] Restore/confirm `PODMAN_RUN_FLAGS ?= $(if $(filter 1,$(NESTED_PODMAN)),--cgroups=disabled)` threaded into the `run` lines on whichever branch lacks it.
- [ ] Measure both images (the full one is large: TeX + jupyter + wx); `CLAUDE.md` 'Dev environment' + the nested-podman paragraph under 'How to resolve drift'.
- [ ] Record both sizes (host full vs nested lean) here and in `CLAUDE.md`; add the standard's one-line
      rule to `CLAUDE.md` ("nested = lean image automatically; `FLAG=1` overrides").

## Open questions

None — the standard's decisions (dnf-only, gates never trimmed) were the maintainer's on 2026-09-10;
anything project-specific to decide is flagged inline above.
