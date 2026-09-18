# Bake the source into the image (pullable-and-runnable), keep the live-mount override

**Status:** IMPLEMENTED + verified 2026-09-18 (go-ahead given: Q1–4 all yes). `Dockerfile` bakes
the source (`COPY . /mvp` + build-time `-e .`), `.dockerignore` extended, reference doc written.
Offline-export test passed both ways (104 tests offline with no mount; bind-mount shadows the bake).
**Remaining:** propagate the general convention to `dotfiles/.ai-coding-conventions.personal.md`
(held pending the maintainer's OK / after v0.0.3). Staged for the maintainer to commit.
**Priority:** 5
**Difficulty:** 4
**Started:** 2026-09-18 (William Emerison Six <billsix@gmail.com>)
**Sequencing:** done BEFORE cutting `v0.0.3` (so the pushed ghcr image contains source), per the
maintainer.

## BLUF

Bake the project's own source into the image at build time (COPY it to `/mvp`) so a **pulled**
image is runnable standalone (offline: builds the book, runs the demos/tests from the baked
source), while `make shell` and every run target keep **bind-mounting the live repo over `/mvp`**,
so development overrides the baked copy. Done = a pulled/exported image runs with no network and no
mount, AND a mounted `make shell` still reflects live host edits — both proven by the offline-export
test. The design is written up in a new reference doc.

## Judgment / rationale (maintainer's proposal, confirmed sound 2026-09-18)

Today the image bakes **dependencies** but not **source**: `/mvp` is populated only by the
bind-mount (`FILES_TO_MOUNT = -v $(pwd):/mvp/:Z`), and `loadpackages.sh` / `entrypoint.sh` run
`uv pip install --no-deps --no-index -e .` from `/mvp` at runtime. So a pulled image has an empty
`/mvp` and cannot run. Baking the source fixes that, and it composes with the live mount because:

- The editable install always targets the path `/mvp`. Pulled (no mount): `/mvp` = baked source →
  imports resolve there. `make shell` (mount): the bind-mount **shadows** the baked `/mvp` at the
  same path → imports resolve to the live host tree. `loadpackages.sh` re-runs `-e .` on entry, so
  it self-heals for both cases.
- This is the distribution-time completion of the "Self-contained images + live source" convention
  (deps baked at build, own source live at runtime): for a *pushed* image, "own source live" also
  needs a baked fallback so the image runs when nobody mounts a repo over it.

## Context — current state (read 2026-09-18)

- `Dockerfile`: COPYs `entrypoint/*`, `requirements.txt`; builds a `--system-site-packages` venv;
  installs deps (setuptools/wheel/moviepy/requirements minus wxpython); bakes docs-only gacalc
  source at `/opt/gacalc-src` (`ARG GACALC_VERSION`); `ENTRYPOINT ["/entrypoint.sh"]`. **Does NOT
  COPY the mvp source.**
- `entrypoint/shell.sh` → `cd /mvp` + `loadpackages.sh` (runtime editable install) + `exec bash`.
- `entrypoint/entrypoint.sh` (the ENTRYPOINT) → pytest + jupytext + `uv pip install -e .` +
  build the book (HTML/PDF/EPUB) into `/output/modelviewprojection/`.
- `.dockerignore` excludes `.git`, `__pycache__`, `dist/`, `build/`, caches, and the vendored elpa
  tree — but NOT `output/` or `*.tar` (image-export artifacts).
- `Makefile`: every run target threads `FILES_TO_MOUNT` (`-v $(pwd):/mvp/:Z`).

## Plan

- [ ] **Write the reference doc first** (the primary deliverable): `tasks/reference/
      container-source-and-mounts.md` — how deps-baked + source-baked + live-mount-override fit
      together, the `/mvp` shadowing mechanic, the editable-install-at-`/mvp` invariant, the
      pulled-image vs dev-shell paths, and the offline-export verification. Note whether it
      generalizes to the other container-template projects.
- [ ] **Dockerfile: COPY the source to `/mvp`** late (after the dep install, so source changes
      don't bust the cached dep layers), respecting `.dockerignore`. Decide build-time editable
      install (Open Q1).
- [ ] **`.dockerignore`: add `output/` and `*.tar`** (and anything else that shouldn't be baked)
      so the build context / image stay lean and don't carry stale book output or image tars.
- [ ] **Confirm the live-mount override still works** — the bind-mount at `/mvp` must shadow the
      baked copy (it does, same path); `loadpackages.sh` re-installs `-e .` on entry.
- [ ] **Verify via the offline-export test both ways** (per the "Self-contained images + live
      source" convention):
      1. `make image` → `make image-export` → `image-import` → run with `--network=none` and NO
         mount → the baked source builds the book / runs `pytest` offline (pulled-image path).
      2. `make shell` (with mount) → edit a source file on the host → confirm the change is
         reflected in-container (dev-override path).

## Open questions

1. **Build-time editable install?** COPY source is required; additionally running
   `uv pip install -e .` at *build* makes a pulled image import-ready without re-installing on first
   run (the runtime `loadpackages.sh`/`entrypoint.sh` re-install is idempotent and still self-heals
   under a mount). Recommendation: yes, install at build too — cheap, and it makes `docker run
   <image>` work immediately. Either way the runtime install stays.
2. **Does this generalize? Yes — and the contract lives in one place.** The Makefile/Dockerfile
   contract is defined in **`dotfiles/.ai-coding-conventions.personal.md`** (the maintainer's
   personal overlay, mounted as `~/.claude/ai-coding-conventions.personal.md`), in the
   **"### Self-contained images + live source"** section (and the "My project layout" / Makefile /
   Dockerfile / entrypoint contract sections). The shared `runClaudeInContainer` CLAUDE.md has a
   "My project layout" section but **explicitly delegates** the tier-by-tier spec to that personal
   overlay; `runCrushInContainer` carries no conventions mirror. So once this design is proven in
   mvp, the general "bake own source into the image + keep the live-mount override so a pulled image
   runs standalone while dev overrides it" refinement gets added to that one section in
   `dotfiles/.ai-coding-conventions.personal.md` — then it applies to every template project
   (geometricalgebra, etc.), each rolled out separately.
3. **Image-size / secrets check.** Baking source is fine for mvp (small, public). Confirm nothing
   sensitive would be baked (`.dockerignore` covers `.git`; add `output/`, `*.tar`).

## See also

- `~/.claude/reference/` "Self-contained images + live source" (personal conventions) — the
  principle this completes for distributed images.
- `tasks/github-actions-release-ci.md` — the release workflow that pushes the image; this task
  makes that pushed image actually useful when pulled.
- `tasks/reference/book-and-docs-pipeline.md`, `tasks/reference/notable-subsystems.md` — the book
  build the baked image would run.
