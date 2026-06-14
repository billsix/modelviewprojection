# Plan: Standardize keyboard controls across SuperBible ports

**Status:** not started — task #37. Recorded 2026-04-28.

**Scope:** SuperBible ports under `/mvp/ports/openglsuperbiblev4/` only.

## What

Audit `/mvp/ports/openglsuperbiblev4/` for inconsistent key bindings and pick one convention to apply across all ports. Currently each chapter chose its own based on the original C++:
- Some use **X / Y / Z + Shift** for ±movement (chapt15+ shader demos)
- Some use **arrow keys** for camera pan (chapt12 ports)
- Some use **WASD-like** mappings
- Some use **R / L / U / D** for rotation
- Various single-letter toggles (B, V, F, P, M, etc.) for demo-specific options

## Why

Inconsistency forces students to relearn controls every chapter. Bill flagged this directly: "check for standardization of keyboard controls. Movement in 3D space should be consistent."

## How

**Reference:** demo22's camera controls in `/mvp/src/modelviewprojection/demo22.py` are the target. Read those first, document the convention, then apply.

Likely convention (verify against demo22 before locking in):
- **W/A/S/D** for forward/left/back/right walk
- **Q/E** or **mouse** for yaw/look
- **Space / Shift** for up/down (or maybe disallow vertical for floor-bound demos)
- **Esc** to quit (already universal in this session's ports)
- **Demo-specific toggles** (light visibility, blur passes, etc.) move into the ImGui menubar from [ports-imgui-menubar.md](ports-imgui-menubar.md), so the keyboard reserves only what needs to be a key.

## Scope

- Touch every port with movement/camera keys.
- Demos that don't have a 3D camera (chapt02/glrect, chapt03 primitives, chapt19/GLRect, chapt21/fonts, etc.) only need Esc-to-quit.
- The ImGui menubar should display the active key binding in a "Help" or "Controls" menu so the student can confirm.

## Coordination

This task overlaps with:
- [ports-walkaround-camera.md](ports-walkaround-camera.md) (#38) — defines the camera *behavior*; this task defines the *keys* that drive it.
- [ports-sphereworld-camera-fix.md](ports-sphereworld-camera-fix.md) (#39) — specific instance.

Do walkaround-camera first (define the model), then keyboard-standardization (assign keys to it), then per-demo migration.

## Open questions

- WASD vs. arrow keys vs. both? Pick one canonical and the other as alias.
- For demos like chapt17/imageproc that previously used `P` then `1..5` to set number of passes — those move to ImGui sliders, freeing `P` for "pause" or similar in other demos.
- demo22's existing controls — what *exactly* are they? Read first, don't guess.
