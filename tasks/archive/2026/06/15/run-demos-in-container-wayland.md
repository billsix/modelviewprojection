# Run the GUI demos inside a container (avoid X11 link/display errors; try Wayland)

**Status:** complete
**Completed:** 2026-06-15

Wayland mechanism FOUND, WIRED IN, and the first attempt's crash FIXED
(2026-06-15). Final: `WAYLAND_FLAGS_FOR_CONTAINER` sets `PYGLFW_LIBRARY=/usr/lib64/
libglfw.so.3` (the system DUAL libglfw) + `XDG_SESSION_TYPE=wayland`/`WAYLAND_DISPLAY`/
`XDG_RUNTIME_DIR` mount + conditional `--device /dev/dri`; Dockerfile `USE_X_WINDOWS`
installs `libwayland-egl`+`libwayland-client`+`libxkbcommon`. (First attempt used
`PYGLFW_LIBRARY_VARIANT=wayland`, which crashed imgui_bundle — see corrected ANSWER.)
**Interactive Wayland-in-container CONFIRMED WORKING by Bill on his host (2026-06-15).**
Only the optional headless-CI path (no compositor → Xvfb+llvmpipe / EGL-OSMesa)
remains, if ever wanted.
**Created:** 2026-06-15

## Goal

Make the interactive glfw/imgui_bundle demos (mvpvisualization, mathdemos) actually
**run inside a container** — for headless CI / screenshot validation and for running
on a Wayland host without the X11 grief. Today, trying to run a demo in a (nested)
container fails to get a GL context.

## What we hit (this session, 2026-06-14/15)

1. **`undefined symbol: glfwGetX11Window`** on `from imgui_bundle import imgui` —
   this was **imgui-bundle version drift**, not a container issue: an older bundled
   `libglfw.so.3` lacked X11 native access. **Fixed** by imgui-bundle **1.92.801**
   (its bundled libglfw is dual X11+Wayland — `glfwGetX11Window` is defined). So
   pin/refresh imgui-bundle; this is NOT the blocker below.
2. **No GL context in the nested container:**
   ```
   Authorization required, but no authorization protocol specified
   X11: Failed to open display :0
   GLFW_INIT_FAIL
   ```
   Causes: the nested container has no **xauth** cookie for the host X server, no
   **`/dev/dri`** GPU passthrough, and the lean image (`USE_X_WINDOWS=0`) had no
   **mesa** software-GL drivers. So glfw can't open a window/context at all.

## ANSWER (corrected after a real test, 2026-06-15): point glfw at the SYSTEM DUAL libglfw

First attempt — `PYGLFW_LIBRARY_VARIANT=wayland` — **was WRONG and crashed the demo.**
Why: `_pipeline.py` does `import glfw` (PyPI, line 43) **before** `from imgui_bundle
import imgui` (line 47). The PyPI Wayland libglfw build has soname `libglfw.so.3` but
is **Wayland-only** (no `glfwGetX11Window`). imgui_bundle's native `_imgui_bundle.so`
needs `glfwGetX11Window`; since glfw loads first and registers `libglfw.so.3`,
imgui_bundle binds the Wayland-only lib → `ImportError: undefined symbol:
glfwGetX11Window` (reproduced in a container — exactly the failure Bill hit).

**Correct fix: make the FIRST-loaded `libglfw.so.3` a DUAL (X11+Wayland) build, and
have everything share it.** Fedora's `glfw` rpm ships exactly that at
`/usr/lib64/libglfw.so.3` (verified: exports BOTH `glfwGetX11Window` and
`glfwGetWaylandWindow`). So set **`PYGLFW_LIBRARY=/usr/lib64/libglfw.so.3`**: PyPI
glfw loads the dual lib first, imgui_bundle then binds the same dual lib (has the X11
symbol → no crash), and GLFW selects **Wayland at runtime** from `WAYLAND_DISPLAY`.
Verified in a container: `import glfw; from imgui_bundle import imgui` → OK with the
dual lib. (`LD_PRELOAD=/usr/lib64/libglfw.so.3` also works but is process-wide;
`PYGLFW_LIBRARY` is scoped to glfw and cleaner.)

### Wired into the Makefile (2026-06-15)

`WAYLAND_FLAGS_FOR_CONTAINER` (used by `make shell` / `make jupyter`) now sets:
`XDG_SESSION_TYPE=wayland`, `WAYLAND_DISPLAY`, `XDG_RUNTIME_DIR` (+ socket mount),
**`PYGLFW_LIBRARY=/usr/lib64/libglfw.so.3`**, and a conditional `--device /dev/dri`
(`DRI_DEVICE`). The Dockerfile `USE_X_WINDOWS` block installs `libwayland-egl` +
`libwayland-client` + `libxkbcommon`. So `make image` then `make shell` + run a demo
should open over Wayland. No X server / xauth needed.

(Aside: PyPI `glfw` ships per-backend builds under `glfw/x11/` and `glfw/wayland/`,
chosen by `PYGLFW_LIBRARY_VARIANT` / `XDG_SESSION_TYPE`; but the `wayland` one is
Wayland-only and collides with imgui_bundle's X11 need — hence using the system dual
lib via `PYGLFW_LIBRARY` instead.)

## Other approaches (kept for the headless / no-compositor cases)

1. ~~Force Wayland~~ — **answered above** (PYGLFW_LIBRARY_VARIANT). Needs a real
   compositor reachable, so it's for an interactive Wayland host, NOT headless CI.
2. **Headless Xvfb + software GL (for CI / screenshots).** Run `Xvfb :99` in the
   container, `DISPLAY=:99`, `LIBGL_ALWAYS_SOFTWARE=1`, install `mesa-dri-drivers`
   (llvmpipe/swrast). Lets a demo render to a virtual X display and be screenshotted
   without a real GPU/display. Good for automated "does it render" checks.
3. **EGL surfaceless / OSMesa offscreen.** Render with no display server at all
   (EGL `EGL_PLATFORM=surfaceless` or OSMesa). More invasive — glfw would need an
   EGL/offscreen context path; may require a small headless harness rather than the
   demo's `glfw.create_window`. Best for pure render-to-PNG tests.
4. **Interactive passthrough done right (X11 path).** If staying on X11: mount
   `/tmp/.X11-unix`, pass a valid **xauth** cookie (`-e XAUTHORITY` + mount the
   cookie, or `xhost +local:`), and `--device /dev/dri`. The mvp Makefile's `USE_X`
   block is this; the nested-sandbox failure was the missing xauth + GPU.

## Recommendation (to validate)

- **Interactive on a Wayland host:** approach 1 (force Wayland) — cleanest, no xauth.
- **Headless CI / "did it render" tests:** approach 2 (Xvfb + llvmpipe) or 3 (EGL/
  OSMesa offscreen → glReadPixels → PNG), which is what the billboard smoke-test
  wanted earlier.

## Plan / steps

- [x] Prevent the `glfwGetX11Window` recurrence — solved version-independently by
      pointing glfw at the system **dual** libglfw (`PYGLFW_LIBRARY=/usr/lib64/
      libglfw.so.3`); no imgui-bundle pin needed.
- [x] Approach 1 (Wayland): wired into the Makefile (`WAYLAND_FLAGS_FOR_CONTAINER`)
      + Dockerfile (`libwayland-egl`/`libwayland-client`/`libxkbcommon`), and
      **verified working in-container on Bill's Wayland host (2026-06-15)**.
- [x] Document the working invocation — in the ANSWER section above + the Makefile.
- [ ] *(optional, headless CI only)* Approach 2: a target that runs a demo under
      Xvfb+llvmpipe and screenshots it.
- [ ] *(optional, headless render-to-PNG only)* EGL/OSMesa offscreen path (ties to
      the billboard smoke-test that couldn't get a context).

**Interactive Wayland-in-container is DONE.** The two remaining items are a separate
*headless-CI* goal — only do them if automated, display-less render checks are wanted.

## Open questions

- Does imgui_bundle's GLFW integration respect the Wayland platform hint set via the
  PyPI `glfw` module, or does it init its own glfw separately?
- Hardware GL (`--device /dev/dri`) vs software (llvmpipe) — which for CI?
- Is the goal interactive-in-container, headless-CI, or both? (Changes the choice.)
