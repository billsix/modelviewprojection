# Bring mvp's Makefile/Dockerfile onto the standard container template

**Status:** proposed — needs go-ahead
**Priority:** 4
**Difficulty:** 5
**Created:** 2026-10-12 (William Emerison Six <billsix@gmail.com>)

## BLUF

mvp's `Makefile`/`Dockerfile` have **drifted from the standard container template** that
gacalc and epix-mirror now follow (epix-mirror was "brought onto the standard template"
2026-10-06). This task closes the gaps: add the standard **`make test`** and **`make docs`**
targets, nested-podman support (**`NESTED_PODMAN`/`PODMAN_RUN_FLAGS`**), a lean-image
flag (**`MINIMAL_IMAGE`**), `CONTAINER_CMD` auto-detect, and the `check-*` targets; and
make the doc build **non-interactive** (the current `spellcheck` prereq needs a TTY).
"Done" = a fresh checkout can run `make test` and `make docs` headless (e.g. in CI or a
nested sandbox) without manual `--cgroups=disabled` or an interactive prompt. Surfaced
2026-10-11 during the ePiX figure migration, where every containerized run needed a
hand-added `--cgroups=disabled` and the real `make html` could not be run headless.

## Context — the drift (measured 2026-10-11)

Targets, mvp vs. the template (gacalc):

| | template (gacalc / epix-mirror) | mvp today |
|---|---|---|
| docs | `make docs` | `make html` (non-standard name) |
| tests | `make test` (standalone) | **none** — pytest only runs buried inside `make html`'s `entrypoint.sh` |
| nested podman | `NESTED_PODMAN=1` → `PODMAN_RUN_FLAGS = --cgroups=disabled` on every `run` | **none** — nested runs fail without a hand-added flag |
| lean image | `MINIMAL_IMAGE=1` flips feature flags off | **none** |
| container cmd | `CONTAINER_CMD` auto-detects podman→docker | hardcoded `podman` |
| check targets | `check-format`, `check-generated`, `check-regions` | only `check-regions` |

mvp's current targets: `all check-regions clean format help html image image-export
image-import jupyter shell update-emacs-packages`.

**Two concrete pains this caused during the figure migration:**
1. Every `podman run` for rendering/building had to be issued by hand with
   `--cgroups=disabled` because the Makefile has no `NESTED_PODMAN`/`PODMAN_RUN_FLAGS`.
2. The real build could not be run headless: `make html` → `entrypoint.sh` → `make`
   (Sphinx catch-all) has a **`spellcheck` prerequisite that runs `aspell` interactively**
   (`book/docs/Makefile:20`), which dies "Stdin not a terminal" without a TTY and prompts
   the maintainer per-misspelling with one. A `make docs` should be non-interactive;
   move spellcheck to its own target (e.g. `make spellcheck`) or an `aspell list`-based
   non-interactive check.

## What the build actually is now (so a redesign preserves it)

`make html` (top Makefile) does `podman run -it … $(CONTAINER_NAME)` → the default
`ENTRYPOINT` is `entrypoint/entrypoint.sh`, which runs, in order: `pytest --exitfirst`;
jupytext (3 notebook sources → `.ipynb`); editable install; **`render_epix_figures.py`**
(the book's ePiX figures, added 2026-10-11); copy gacalc docs-source; `check_doc_regions.py`;
then `cd book/docs && make html && make latexpdf && make epub`; copy to `/output`.

So `make html` is really "run the tests, then build all three doc formats." The template
split would be: **`make test`** = just the pytest gate; **`make docs`** = the doc build
(figures + Sphinx html/latexpdf/epub), non-interactive.

## Proposed steps

1. **`PODMAN_RUN_FLAGS`/`NESTED_PODMAN`:** add `PODMAN_RUN_FLAGS ?= $(if $(filter 1,$(NESTED_PODMAN)),--cgroups=disabled)` and append `$(PODMAN_RUN_FLAGS)` to every `podman run`. Copy gacalc's form verbatim.
2. **`CONTAINER_CMD`** auto-detect podman→docker (gacalc's form).
3. **`make test`** — a minimal headless `podman run … --entrypoint /bin/bash … -c 'loadpackages.sh && pytest …'` (like gacalc's `test`), `: image` prereq.
4. **`make docs`** — the doc build, non-interactive; keep `make html` as an alias or retire it. Split `entrypoint.sh` so the test gate and the doc build are separately invokable.
5. **Non-interactive spellcheck** — **DONE 2026-10-12** (Option A): `spellcheck` taken
   off the Sphinx catch-all; `tools/spellcheck.sh` does a headless `aspell list` reusing
   `mvp_dict.pws`. The doc build is now non-interactive. See
   `tasks/archive/2026/10/22/non-interactive-spellcheck.md`. (A top-level containerized `make spellcheck`
   target is still part of this template conformance — not yet added.)
6. **`MINIMAL_IMAGE`** — flip `BUILD_DOCS`/`USE_EMACS`/`USE_JUPYTER`/`USE_X_WINDOWS`/`USE_EPIX` off for a lean test image (gacalc's idiom; mirror into the Dockerfile ARGs).
7. **`check-format`** (= `make format` then `git diff --exit-code`) for CI parity.
8. Update `.github/workflows/*` to call the new `make` targets; update `README`/`CLAUDE.md`.

## Notes / open questions

1. mvp is a private app+book (not published), so the template's `dist`/`upload`/`release`
   targets are **N/A** — skip them (unlike gacalc). Confirm.
2. The interactive spellcheck is long-standing; confirm moving it out of the build path is
   wanted (the maintainer may rely on the per-build prompt). Recommend: `make spellcheck`
   as a separate, opt-in target.
3. Not blocking the ePiX figure migration — that build works once the unrelated
   `shading.py` doctest is fixed (done 2026-10-11). This is pure conformance/ergonomics.
