# Fix the `--system` editable install so `generate_plots_for_book` installs (clean-build SVGs)

**Status:** complete
**Completed:** 2026-07-23 (fix applied to `entrypoint/entrypoint.sh`; verified). Created 2026-07-22.
Found while confirming the book renders after the gacalc-0.0.13 bump
(`tasks/archive/2026/07/22/dual-coefficient-cleanup.md`): a **clean** `make html` failed to
regenerate the book's plot/diagram SVGs.

## Outcome (what shipped)

`entrypoint/entrypoint.sh:18` changed from `-e . --system` to `-e . --python "$(which python)"` (with
a comment), matching `entrypoint/loadpackages.sh` — so the editable install goes into the **active
venv** (which the Dockerfile seeds with setuptools/wheel) instead of `/usr` (no setuptools).
`loadpackages.sh` (used by `shell.sh`/`jupyter.sh`/the `format` target) was **already** correct; only
`entrypoint.sh` (the book build) used `--system`.

**Verified** (in a throwaway copy, current image): the fixed line installs
`modelviewprojection==0.0.2` into the venv, `generate_plots_for_book` resolves to `/venv/bin/...`,
`book/docs/_static/make` exits 0 (it was dying at `generate_plots_for_book: command not found`), and
the plot SVGs (`plot1.svg`, `rotate0-0.svg`, …) regenerate — so a clean `make html` no longer emits
the ~44 `_static/*.svg not readable` warnings. (End-to-end confirmation over a full image rebuild not
re-run; the exact failing step is directly verified.)

The change is a **build-file edit** (uncommitted, Bill commits). The fix reaches the book image only
on the next `make image` (it bakes `entrypoint.sh`).

## Symptom

On a clean tree (`git clean -fdx`), `make html` emits ~44 warnings:
`WARNING: image file not readable: _static/<name>.svg` for the generated plot/diagram SVGs
(`plot1-4.svg`, `translation-forwards-*.svg`, `rotate-sloppy-forwards-*.svg`, `scale-*.svg`,
`incorrectrotate-forwards-*.svg`, `monitor.svg`, `modelspace.svg`, `ndcSpace*.svg`,
`screenspace*.svg`, `disproportionate*.svg`, `viewport.svg`, …). The PNGs (dot/graphviz-generated)
are fine; only the SVGs fail.

## Root cause (verified in the container)

Those SVGs are **generated, not tracked** — `book/docs/_static/Makefile`'s `all` target builds them,
and `rotate0-0.svg` (and the matplotlib plot SVGs) come from the **`generate_plots_for_book`** console
script (`[project.scripts]` in `pyproject.toml` → `modelviewprojection.plotsforbook.generate_plots:main`).

`entrypoint.sh` installs the package with:

```sh
uv pip install --no-deps --no-index --no-build-isolation -e . --system
```

**`--system` targets the system python (`/usr`), which has no `setuptools`** (the venv has it,
83.0.0). So the editable build fails:

```
Call to `setuptools.build_meta.prepare_metadata_for_build_editable` failed
ModuleNotFoundError: No module named 'setuptools'
```

→ `generate_plots_for_book` never installs → `_static/make` dies at
`generate_plots_for_book: command not found` (Error 127) → the plot SVGs are never generated →
Sphinx reports them "not readable". (This is the "loadpackages.sh fails on a missing setuptools build
dep" issue already noted in `CLAUDE.md`.) You normally don't see it because the generated SVGs persist
on disk between incremental builds; only a clean build regenerates them.

## Fix (confirmed)

**Drop `--system`** so the editable install goes into the venv (which has `setuptools`):

```sh
uv pip install --no-deps --no-index --no-build-isolation -e .
```

Verified: with `--system` removed, `generate_plots_for_book` lands in `/venv/bin`, `_static/make`
completes (`rc=0`), every SVG generates, and the clean-build warning count drops **72 → 10** (the
remaining 10 are unrelated — see the texExpToPng and demo01 tasks).

## Scope — check every `--system` editable-install site

- **`entrypoint/entrypoint.sh`** — the book build (the one that bites here).
- **`loadpackages.sh`** / the **`format`** Makefile target path — `CLAUDE.md` says format.sh's `ty`
  step needs the package importable; if it uses the same `--system -e .`, it has the same bug. Grep
  the repo for `--system` on a `uv pip install -e .` and fix each. (Alternative already in use for
  running demos: `PYTHONPATH=/mvp/src`, but the editable install is what registers the console
  scripts, so the book build genuinely needs the install to succeed.)

## Verify

Clean tree, then `make html` (or the containerized book build): `_static/make` exits 0,
`generate_plots_for_book` resolves, no `_static/*.svg not readable` warnings.

## Relationships

- Sibling findings from the same clean-build investigation:
  `tasks/texexptopng-standalone-display-math.md`, `tasks/demo01-import-region-empty.md`.
- Context: `tasks/archive/2026/07/22/dual-coefficient-cleanup.md` (the gacalc-0.0.13 bump whose
  book-render check surfaced this).
