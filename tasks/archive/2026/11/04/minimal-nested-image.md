# Lean image for nested-podman builds — what "minimal" means for modelviewprojection

**Done 2026-11-04.** The flag mechanism had already landed on master (commit `6189c16e`, "mvp: finish
Makefile/Dockerfile conformance to the standard template"); this pass measured both image sizes and
recorded the convention in `CLAUDE.md`. Branch `minimal-nested-image`.

## What was delivered

`make image MINIMAL_IMAGE=1` builds a lean export/airgap/CI image; a plain `make image` (host OR
nested) still builds the full one. Measured sizes on 2026-11-04:

| image | size |
| --- | --- |
| full (`make image`) | **6.61 GB** |
| lean (`MINIMAL_IMAGE=1`) | **4.35 GB** |

`CLAUDE.md` › "Dev environment" now carries the one-line rule (what `MINIMAL_IMAGE=1` drops, that
`make test` stays green on the lean image, how to add a flag back, and that `MINIMAL_IMAGE` is build
content independent of `NESTED_PODMAN`).

## Implemented under the CURRENT standard, not this task's original wording — read before merging

This task was filed **2026-09-10**, before the **2026-09-27 rename** of the lean-image idiom from
`NESTED_PODMAN`-keyed to **`MINIMAL_IMAGE`-keyed** (the overload of `NESTED_PODMAN` for build content
silently downgraded the runCrush client; see runClaudeInContainer
`tasks/reference/minimal-nested-images.md`). So two things in the original plan were deliberately
**not** followed, because the later standard supersedes them:

1. **The idiom is `FLAG ?= $(if $(filter 1,$(MINIMAL_IMAGE)),0,1)`, NOT `...$(NESTED_PODMAN)...`.** A
   nested `make image` now builds the **full** image (the inner store is disk-backed, not the RAM
   store the 2026-09-10 BLUF assumed); lean is an explicit opt-in. This is what master already does.
2. **`BUILD_DOCS` and `USE_X_WINDOWS` ARE `MINIMAL_IMAGE`-keyed** (droppable), contrary to this task's
   2026-09-10 finding that they must stay `?= 1`. Master made this call deliberately and documents it
   in the Makefile flag-block comment: the **pytest gate (`make test`) needs none of them** —
   glfw/pyopengl are in the base group + requirements.txt — so a lean image still runs the full test
   gate. The book build (`make html`) and headless-render paths are separate gates you run with the
   flags ON explicitly, satisfying the flag-coverage rule. (If the maintainer wants the lean image to
   also carry the book/headless-render gate by default, that's the one thing to revisit — but the
   documented decision is that the lean image's job is the test/lint gate.)

## Verification

- Built the lean image (a zero-build-arg `podman build`, equivalent to `MINIMAL_IMAGE=1` since every
  Dockerfile optional ARG defaults to 0) → 4.35 GB, exit 0; ePiX install step correctly skipped. Full
  image on disk measured 6.61 GB. Throwaway lean image removed after measuring.
- The flags + `PODMAN_RUN_FLAGS ?= $(if $(filter 1,$(NESTED_PODMAN)),--cgroups=disabled)` are present
  and threaded through every `$(CONTAINER_CMD) run` line on master (confirmed; the 2026-09-10 note
  that a branch lacked `PODMAN_RUN_FLAGS` referred to the then-current `morePorts` branch).

## Related

- runClaudeInContainer `tasks/reference/minimal-nested-images.md` — the standard + the fleet row.
- runClaudeInContainer `tasks/minimal-image-for-nested-podman-standard.md` — the umbrella this was a
  per-project child of.
