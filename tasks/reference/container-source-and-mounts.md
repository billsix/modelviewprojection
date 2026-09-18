# Container image: baked source + live-mount override

**What is true now.** The mvp image bakes BOTH its third-party dependencies AND its own source, so
a **pulled** image runs standalone (builds the book, runs the demos/tests) with no network and no
bind-mount. During development, `make shell` (and every run target) bind-mounts the live host repo
over `/mvp`, which **shadows** the baked source at the same path, so host edits override the baked
copy live. This is the distribution-time completion of the "Self-contained images + live source"
convention (deps baked at build, own source live at runtime): for a *pushed* image, "own source
live" needs a baked fallback so the image still runs when nobody mounts a repo over it.

## How it fits together

- **Dependencies** are installed into `/venv` at image-build time (dnf packages + a
  `--system-site-packages` venv + `requirements.txt`), so they're in committed image layers and the
  image is offline-reproducible. (Unchanged by this design.)
- **Own source** is baked with `COPY . /mvp` near the END of the Dockerfile (after the dnf/pip/TeX
  layers, so a source change rebuilds only the COPY + editable-install layers, not the expensive
  ones). `.dockerignore` keeps `.git`, `output/`, `*.tar`, and caches out of the baked tree.
- A **build-time editable install** (`uv pip install --no-deps --no-index --no-build-isolation -e .`
  from `/mvp`) writes the editable finder into `/venv`, pointing at the path `/mvp`.
- **The `/mvp` invariant is what makes both modes work.** The editable install always targets
  `/mvp`:
  - **Pulled image, no mount:** `/mvp` = the baked source → imports resolve there. `docker run
    <image>` runs the entrypoint (pytest + book build) from the baked source.
  - **`make shell` / run targets:** `FILES_TO_MOUNT` bind-mounts `$(pwd):/mvp/:Z`, which shadows
    the baked `/mvp` → imports resolve to the live host tree. `loadpackages.sh` re-runs the editable
    install on entry (idempotent), so it self-heals for whichever `/mvp` is present.

## Why it's safe / non-surprising

- The bind-mount and the baked copy live at the **same path** (`/mvp`), so the mount cleanly
  shadows the bake — no divergent import paths, no stale-code confusion.
- CI/`make` gates are unaffected: `make format`/`type-check`/`test` bind-mount the live repo, so
  they always run against the working tree, exactly as before.
- The editable finder is in `/venv` (not `/mvp`), so it survives the mount and keeps pointing at
  `/mvp` in both modes.

## Verification — the offline-export test, both ways

1. **Pulled-image path (standalone, offline, no mount):**
   `make image` (lean is fine) →
   `podman run --rm --network=none [--cgroups=disabled] --entrypoint /bin/bash modelviewprojection
   -c 'source /venv/bin/activate && cd /mvp && pytest -q'` → tests pass from the baked source with
   no network and no mount. (Proven 2026-09-18: 104 passed.) For the full pulled-image experience,
   `docker run <image>` runs the entrypoint, which builds the book (needs a `BUILD_DOCS=1` image).
2. **Dev-override path:** `make shell` (or `shell-exec`) with the mount → a host-only file appears
   at `/mvp` in-container, i.e. the mount shadows the bake. (Proven 2026-09-18.)

## Where the general convention lives

The Makefile/Dockerfile *contract* is defined in the maintainer's personal overlay
`dotfiles/.ai-coding-conventions.personal.md`, in the **"Self-contained images + live source"**
section (mounted as `~/.claude/ai-coding-conventions.personal.md`). The shared
`runClaudeInContainer` CLAUDE.md delegates the template spec to that overlay. So the general
"bake own source + keep the live-mount override" refinement belongs in that one section, from which
it governs every container-template project (geometricalgebra, etc.), each rolled out separately.

## See also

- `tasks/bake-source-into-pushed-image.md` — the work record for this change.
- `tasks/github-actions-release-ci.md` — the release workflow that pushes the (now source-bearing)
  image to ghcr.
- `tasks/reference/book-and-docs-pipeline.md` — the book build a pulled image runs.
