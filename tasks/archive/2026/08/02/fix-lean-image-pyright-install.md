# Fix pyright install in lean image builds (`make image BUILD_DOCS=0 …`)

**Status:** DONE 2026-08-02 — replaced `--python $(which python)` with
`--python /venv/bin/python` at **all 4 sites** in the Dockerfile (127
setuptools/wheel, 128 pyright, 149 moviepy, and 178 the requirements install —
one more than the 3 the note flagged, same idiom, same lean-build hazard). This
drops the dependency on `which` entirely, so a trimmed `make image
BUILD_DOCS=0 …` no longer breaks. `/venv` is created at Dockerfile:117, so the
absolute path is valid at every site. **Container verification remains Bill's**
(a lean `make image BUILD_DOCS=0 USE_EMACS=0 USE_JUPYTER=0 USE_X_WINDOWS=0`
then a default-flags `make image`) — can't rebuild the mvp image in-sandbox.
**Created:** 2026-07-30

## Problem

`Dockerfile:128` installs pyright with:

```dockerfile
dnf install -y libatomic && uv pip install pyright --python $(which python); \
```

`which` is not installed explicitly — it only arrives transitively via the
heavy optional feature groups. With the feature flags trimmed
(`make image BUILD_DOCS=0 USE_EMACS=0 …`), `$(which python)` fails and the
image build breaks. Found during the Emacs-vendoring work
(`tasks/archive/2026/06/13/update-emacs-packages-target.md`); recorded in
`tasks/reference/design-decisions.md` › "Tooling, types & gates".

Note the same `--python $(which python)` idiom appears at `Dockerfile:127`
(setuptools/wheel) and `:149` (moviepy) — audit all three, not just pyright's.

## Fix options

- `dnf install -y which` unconditionally near the top (tiny package), or
- replace `$(which python)` with the venv's absolute path
  (`/venv/bin/python`), which is known at that point and drops the dependency
  on `which` entirely — probably the cleaner fix.

## Verification

Nested podman: `make image BUILD_DOCS=0 USE_EMACS=0 USE_JUPYTER=0
USE_X_WINDOWS=0` builds green (add `--cgroups=disabled` transiently per the
standing arrangement), then one default-flags `make image` to confirm no
regression.
