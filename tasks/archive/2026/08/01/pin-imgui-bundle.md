# Pin imgui-bundle in requirements.txt

**Status:** DONE 2026-08-01 — pinned `imgui-bundle[glfw]==1.92.801` (`requirements.txt:6`).
Verified against the PyPI JSON API that `1.92.801` is a real published release (and is
in fact the current latest, so the pin is both known-good and up-to-date). Exact pin
chosen over a range because the failure this prevents was silent wheel *drift*; loosen
to `>=1.92.801,<...` later if desired. **Final check remains Bill's host `make image` +
one imgui demo launch** (the failure mode is at import/window-setup, so a single launch
confirms it).
**Created:** 2026-07-30

## Why

`requirements.txt:6` is unpinned: `imgui-bundle[glfw]`. A drifted wheel once
broke every imgui demo with `undefined symbol: glfwGetX11Window` (the bundled
glfw lost the X11 symbols imgui_bundle's native lib binds —
`tasks/archive/2026/07/09/crossproduct-tex-billboard-labels.md`; same symbol
family as the `PYGLFW_LIBRARY` dual-lib note in
`tasks/reference/design-decisions.md`). Known-good wheel: **1.92.801**.

## Change

`imgui-bundle[glfw]` → `imgui-bundle[glfw]==1.92.801` (or `>=1.92.801,<next`
if Bill prefers a range). requirements.txt is the single source of truth
(`pyproject.toml` reads it dynamically), so this is the only edit — no
Dockerfile ARG involved, unlike gacalc.

## Gate

Rebuild the image (`make image`) and launch one imgui-using demo
(`mvpvisualization/coordinatesystems.py` or any port) — the failure mode is
at import/window-setup time, so a single launch verifies it. Bill's host run
is the final check.
