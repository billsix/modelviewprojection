# Pin imgui-bundle in requirements.txt

**Status:** not started
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
