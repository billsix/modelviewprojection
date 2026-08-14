# .extrabashrc: run format.sh once on pwd (/mvp), not per-subdir

**Status:** DONE 2026-08-14 — scope expanded per Bill's clarification: not just fix the exit
hook, but make `format.sh` runnable **both** in the container (`cd /mvp`) and on the host
(`cd <repo>`). Verified green in the container (exit 0) and running end-to-end on the host.
Ready to archive.
**Priority:** 4
**Difficulty:** 1

## Done (2026-08-14)

**Root cause verified first** (per the "test the blocker" rule): from `/mvp/src`,
`format.sh`'s relative `ruff check src` resolves to `src/src` → error; from `/mvp` it's clean.

1. **`entrypoint/dotfiles/.extrabashrc`** — exit hook now `cd /mvp/ && format.sh` (one call from
   the root), replacing the two per-subdir `cd … && format.sh` lines.
2. **`entrypoint/format.sh` made portable** (Bill's in-AND-out-of-container goal): the venv
   activation is guarded (`[ -f /venv/bin/activate ] && source …`, skipped on the host), and the
   `ty check` paths are now **relative** (`ty check src`/`tests`/`ports/...`) like ruff already
   was — so `format.sh` runs identically from the repo root in either place. No `pyproject.toml`
   change was needed (ruff's excludes already cover exclusions).
3. **`src/modelviewprojection/util/shading.py`** — fixed a **pre-existing** ty error (NOT a
   0.0.16 regression — the `tuple(genexpr)` → `tuple[float, ...]` vs `tuple[float, float, float]`
   pattern reproduces under gacalc 0.0.15 too). Unpacked the three coords explicitly so the return
   is a fixed-length 3-tuple; doctests unchanged (2 passed). This was making `format.sh` red on
   every shell exit — likely the bulk of Bill's "issues when I exit the shell".
4. **`src/modelviewprojection/demos/demo22/demo22.py`** — `ruff format` removed 2 stray blank
   lines (pre-existing drift the broken hook never reached; format.sh doing its job).

**Verify:** container `cd /mvp && format.sh` → all ruff+ty green, exit 0. Host `cd <repo> &&
bash entrypoint/format.sh` (no `/venv`) → guard skips cleanly, all 8 ruff steps green, ty paths
resolve (only unresolved-import noise from a minimal venv lacking glfw/PyOpenGL — real host has
them). shading.py doctests pass in-container.

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
