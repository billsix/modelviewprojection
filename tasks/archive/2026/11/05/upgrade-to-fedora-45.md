# Upgrade the container base from Fedora 44 to Fedora 45 (done)

Done 2026-11-05 (William Emerison Six <billsix@gmail.com>). Part of a fleet-wide
Fedora 44 → 45 bump.

## What changed

- `Dockerfile`: `registry.fedoraproject.org/fedora:44` → `fedora:45`.
- `requirements.txt`: two dependency bumps to get cp315 (Python 3.15) wheels
  instead of failing source builds (maintainer pre-authorized bumping versions
  to whatever works; versions recorded here for tracking):
  - `imgui-bundle[glfw]==1.92.801` → **`==1.93.0`** — 1.93.0 is the first
    imgui-bundle release that ships a CPython-3.15 (`cp315`) Linux wheel; 1.92.x
    had none, so pip/uv tried to source-build its C++/nanobind extension and
    failed (nanobind API mismatch `ndarray_handle*` → `nb_internals*`).
  - added **`Pillow==13.0.0`** — pillow is a transitive dep (via moviepy/imageio);
    the resolver otherwise selected `pillow-11.3.0`, which has no cp315 wheel and
    fails its source build. 13.0.0 (the resolved version, pinned exactly) has a
    cp315 wheel. (uv still *probes* 11.3.0 during backtracking and logs a build
    error, then falls back to the pinned 13.0.0 — non-fatal; final install is
    pillow 13.0.0.)

## Result — both images green nested on fedora:45 / Python 3.15

- `make image MINIMAL_IMAGE=1` + `make test`: **112 passed** (pytest/doctests).
- `make image` (full, 6.6 GB): builds the Python/OpenGL stack + the TeX-Live docs
  toolchain + texExpToPng + **ePiX** from source + JupyterLab. Verified the image
  has `PIL 13.0.0` and `imgui_bundle 1.93.0`.

No source-code changes were needed — only the two dependency-pin bumps above.

## Note for the maintainer

The `imgui-bundle` bump 1.92.801 → 1.93.0 can shift the imgui API the GUI demos
use (menubar/controls conventions per CLAUDE.md). The headless build + pytest
pass, but the **interactive imgui / SuperBible demos were not play-tested on a
display** (that's your call). If 1.93.0 changed anything the demos rely on, it
would surface only on-display.
