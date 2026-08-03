# .extrabashrc: run format.sh once on pwd (/mvp), not per-subdir

**Status:** proposed — needs go-ahead (small, well-specified)
**Priority:** 4
**Difficulty:** 1

## Goal

Make the shell-exit auto-format work **outside the container**. Right now
`entrypoint/dotfiles/.extrabashrc` (the exit hook) does:

```bash
cd /mvp/src/ && format.sh
cd /mvp/tests/ && format.sh
```

Bill wants it to instead call `format.sh` **once from the project root (`/mvp`, the pwd)**,
with **no `cd` into a subdir and no directory-name argument** — relying on `pyproject.toml`
to exclude what shouldn't be formatted.

## Why (Bill, 2026-08-03)

- Works outside the container: no hard-coded `/mvp/src` etc.
- Fixes the "issues when I exit the shell." **Likely root cause:** `format.sh` uses *relative*
  paths internally (`ruff check src`, per CLAUDE.md "the `cd` must be in the `bash -c` itself"),
  so `cd /mvp/src && format.sh` makes its internal `ruff check src` resolve to `src/src` and
  fail. Running `format.sh` once from `/mvp` lets `ruff check src`/`tests` resolve correctly, and
  `pyproject.toml`'s excludes cover the rest.

## Plan

- [ ] Change the exit hook to `cd /mvp && format.sh` (single call from the root), removing the
      two per-subdir `cd … && format.sh` lines.
- [ ] Confirm `format.sh` formats src + tests (+ tools?) from `/mvp` via its relative paths /
      `pyproject.toml` config, and that nothing that should be excluded gets touched.
- [ ] Sanity-check it also works when the shell exits with a non-zero format result (the
      exit-status-propagation shape — `format.sh` should still report all red; see CLAUDE.md
      "A multi-step check script must propagate every step's failure").

## Notes

- Origin: Bill (2026-08-03), side note while at work. `.extrabashrc` is the dotfile hook, NOT
  the off-limits vendored `.emacs.d/elpa/` tree.
