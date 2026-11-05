# Upgrade the container base from Fedora 44 to Fedora 45

**Status:** in progress
**Priority:** 3
**Difficulty:** 6

## BLUF

Bump `Dockerfile` from `registry.fedoraproject.org/fedora:44` to `fedora:45` and
get the image building green nested on the 45 base. "Done" = the fedora-45 base
builds the image (at least `MINIMAL_IMAGE=1`, which runs the pytest gate), with
any full-image (`BUILD_DOCS`/`USE_JUPYTER`/`USE_EPIX`) gaps documented.

## Context (read first)

Part of a fleet-wide Fedora 44 → 45 bump (William Emerison Six
<billsix@gmail.com>, 2026-11-05). Fedora 45 ships **Python 3.15** (was 3.14),
GCC 16.2, clang/LLVM 23. This is the heaviest image in the fleet: full `make
image` (~6.6 GB) installs the Python/OpenGL stack, a TeX Live + Sphinx docs
toolchain, builds **texExpToPng** and **ePiX** from source, and bakes JupyterLab.

Primary risk: the PyPI deps (requirements.txt, installed via uv minus wxpython;
numpy/glfw/pyopengl/pillow/sympy/matplotlib come from dnf `python3-*` via the
`--system-site-packages` venv) resolving under **Python 3.15** — a package
without a 3.15 wheel may fail. Secondary: the two from-source C builds under LLVM
23, and the gacalc `==0.0.20` pin / ePiX commit pin.

## Plan / build strategy (discretion)

1. `Dockerfile`: `fedora:44` → `fedora:45`.
2. **Build `make image MINIMAL_IMAGE=1` first** — fastest path that still
   exercises the fedora-45 base + the core Python stack under 3.15 and runs the
   pytest gate; this is the real test of whether the base bump works.
3. Then attempt the **full** `make image`. If it fails only on an upstream
   Python-3.15 wheel/package-availability gap (not fixable cleanly tonight),
   document it here and leave the minimal image as the verified result.
4. Fix any in-scope toolchain breakage minimally; log decisions here.
5. Stage by path; archive.

## Notes / findings

(appended as the build runs)
