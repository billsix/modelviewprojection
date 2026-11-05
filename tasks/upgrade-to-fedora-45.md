# Upgrade the container base from Fedora 44 to Fedora 45

**Status:** blocked
**Blocked on:** maintainer decision on two Python-3.15 dependency pins (below).
**Recheck:** after bumping imgui-bundle to a cp315-wheel release and resolving
the pillow `<12` cap, run `make image MINIMAL_IMAGE=1` nested — green = cleared.
**Priority:** 3
**Difficulty:** 6

## BLUF

The base is bumped to `fedora:45` (committed), but the image build is **blocked**
by two upstream Python-3.15 wheel gaps in pinned/transitive deps that fail their
source builds. Resolving them requires dependency-pin changes that can shift the
imgui demo API and must be re-verified on a display — a maintainer call, not an
overnight auto-fix. Everything else about the bump is ready.

## What was done

- `Dockerfile`: `registry.fedoraproject.org/fedora:44` → `fedora:45` (committed).

## The blocker (Fedora 45 ships Python 3.15; measured 2026-11-05, `MINIMAL_IMAGE=1`)

The `grep -v wxpython /requirements.txt | uv pip install …` step fails. Two deps
have no cp315 wheel and fail to build from source under Python 3.15:

1. **imgui-bundle==1.92.801** (pinned, line `imgui-bundle[glfw]==1.92.801`). No
   cp315 wheel, so pip/uv build it from source (a large C++/nanobind compile),
   which fails with a real nanobind API mismatch:
   `cannot convert 'nanobind::detail::ndarray_handle*' to
   'nanobind::detail::nb_internals*'` — the vendored bindings in 1.92.801 don't
   compile against the nanobind pulled under 3.15.
   → **Fix (maintainer):** bump the `imgui-bundle` pin to a release that ships
   cp315 wheels. This can change the imgui API the demos use (menubar/controls
   conventions), so the imgui/SuperBible demos need an on-display re-verify.

2. **pillow** (transitive, via `ImageIO` → `pillow>=8.3.2`). Something in the
   graph caps **pillow<12**, so the resolver selects `pillow-11.3.0`, which has
   no cp315 wheel → source build → fails. The dnf `python3-pillow` is **12.3.0**
   (cp315-native) but is *too new* for the `<12` cap, so `--system-site-packages`
   can't satisfy it either.
   → **Fix (maintainer):** find and loosen/bump the dep that caps `pillow<12`
   (likely an older imageio/moviepy/matplotlib pin), so the resolver can take the
   system 12.3.0 or a cp315-wheel pillow.

## Investigated and rejected (to save the maintainer the detour)

- **Switching the requirements install `uv` → `pip install -r /dev/stdin`**
  (matching the sibling multivariate-math repo, so the dnf natives satisfy via
  `--system-site-packages`): helps in principle and correctly uses Fedora's
  Wayland-patched pyopengl, but does **not** clear either blocker — imgui-bundle
  still source-builds and fails, and the `pillow<12` cap still forces a 11.3.0
  source build (system 12.3.0 is too new). Reverted so the committed diff is just
  the base bump; the real fix is the two pin changes above.

## Note

Sibling Python repo **multivariate-math** upgraded to fedora:45 cleanly — it has
no imgui-bundle and no `pillow<12` cap, so this blocker is specific to mvp's
imgui/imageio dependency set, not a general Python-3.15 problem.
