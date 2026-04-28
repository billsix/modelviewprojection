# Plan: SuperBible ports UX pass — phased execution order

**Status:** Phase 1 (#33 + #34) ✅ **done 2026-04-28**. Phases 2–3 not started. Umbrella plan covering the eight UX tasks (#33–#40) added 2026-04-28, plus how to schedule them.

## Why this exists

The eight UX tasks Bill added on 2026-04-28 aren't independent. Several share helper code (a common `_common.py` module under `/mvp/ports/openglsuperbiblev4/`), and several have hard dependencies (e.g., the keyboard-standardization task assigns keys to a camera model that the walk-around-camera task hasn't defined yet). Doing them in arbitrary order means re-touching the same files multiple times. This file is the agreed-upon ordering.

## Dependency map

```
#33 menubar ─┬─→ #36 CLI→ImGui          (CLI controls live in menus / windows)
             ├─→ #37 keyboard           (frees keys; surfaces bindings in Help menu)
             └─→ #34 fullscreen toggle  (fullscreen entry IS in the menubar)

#34 window size ── (mostly mechanical, pairs naturally with #33 since same setup function)

#38 walkaround camera ─┬─→ #37 keyboard       (#37 binds keys to #38's camera model)
                        └─→ #39 sphereworld    (#39 applies #38's helper to 3 files)

#40 visible light ── (independent additive)
#35 demo22 slider ── (curriculum side, isolated)
#3, #4 pyMatrixStack ── (curriculum side, no port dependency)
```

Cross-project surface: the only soft dependency is "demo22 must remain the camera + visible-light reference." It already does.

## Phased execution order

### Phase 1 — shared helper module (foundation) ✅ done 2026-04-28

Tasks: **#33 (menubar) + #34 (window size), paired.**

Plans: [`ports-imgui-menubar.md`](ports-imgui-menubar.md), [`ports-window-size-1920x1080.md`](ports-window-size-1920x1080.md). Detail in those files.

Result: `/mvp/ports/openglsuperbiblev4/_common.py` exists with `resolve_default_window_size`, `init_imgui`, `WindowState`, `toggle_fullscreen`, `draw_menubar`. 92 ports migrated by script, 1 hand-written reference (`chapt15/shaders.py`), 7 stubs skipped. All 100 files compile clean. Bill verified menubar+fullscreen on `chapt15/shaders.py` and the imgui panel on `chapt01/Block.py`.

Three migration bugs hit and fixed in pass: line-concatenation regex, `impl.shutdown()` placement (placed inside `if not window:` initially, then over-corrected, then placed correctly), multi-line `from ... import (...)` block split. See [`ports-imgui-menubar.md`](ports-imgui-menubar.md#bugs-hit-during-the-bulk-migration-resolved) for detail.

### Phase 2 — camera (3D ports only) — NEXT (first attempt rolled back)

**First attempt 2026-04-29 was reverted via `git reset` after the bulk migration broke ~10 demos.** Postmortem at [`postmortem-phase2-attempt-1.md`](postmortem-phase2-attempt-1.md) — read it before re-attempting. Key takeaways: the canary on `chapt08/sphereworld` worked end-to-end (Bill confirmed), but the bulk-migration regex partially-replaced function bodies and left orphan references that compiled clean but failed at runtime. Use libcst or hand-migrate per pattern group next time, and grep for stale references after any pass.

Tasks: **#38 (walk-around camera), then #39 (sphereworld) immediately after.**

Plans: [`ports-walkaround-camera.md`](ports-walkaround-camera.md), [`ports-sphereworld-camera-fix.md`](ports-sphereworld-camera-fix.md).

- Read demo22's camera in `/mvp/src/modelviewprojection/demo22.py` and document the model.
- Add `Camera` class (or module-level functions) to `_common.py`:
  - `Camera.update(window, dt)` — read keys, mutate position/yaw.
  - `Camera.apply()` — call the equivalent of `gluLookAt` with current state.
- Migrate 3D ports to use the new Camera. Replace each port's per-demo `camera_x/y/z/yaw` triples and inline view-matrix setup.
- **#39 immediately after #38** because sphereworld is the most camera-heavy scene; if the new Camera doesn't feel right there, the design needs revision and it's better to find out early. Sphereworld is also Bill's stated wishlist demo (`demo24` modernization), so the camera shape decided here will eventually echo to the curriculum side.

**Why second:** Phase 1 already gave us imgui setup; Phase 2 adds the camera model that Phase 3's keyboard task binds to.

**Out of scope this phase:** demos that don't have a 3D camera (chapt02/glrect, chapt03 primitives, chapt19/GLRect, chapt21/fonts, etc.) and demos where rotation is the demo (some chapt10 NURBS — verify case by case with a per-demo justification comment as Bill requested).

### Phase 3 — polish (additive, lower blast radius)

Tasks: **#37 (keyboard), then #36 (CLI→ImGui), then #40 (visible light).**

Plans: [`ports-keyboard-standardization.md`](ports-keyboard-standardization.md), [`ports-replace-cli-with-imgui.md`](ports-replace-cli-with-imgui.md), [`ports-visible-light-source.md`](ports-visible-light-source.md).

#### #37 first within Phase 3
By this point the menubar (#33) and camera (#38) both exist. Decide one keymap (matching demo22). Per-demo toggles move into menubar entries, freeing keys. Add a Help → Controls entry to the menubar that displays the active bindings.

#### #36 second within Phase 3
Smaller scope — only ports that currently take CLI args. Needs #33's menubar in place to host the ImGui controls.

#### #40 last within Phase 3
Add `draw_light_marker(pos, size)` to `_common.py`. Migrate lit ports (chapt05, chapt08–09, chapt11, chapt14, chapt17, chapt18, chapt19/SphereWorld32) to call it. Purely additive — won't break a demo if I leave it alone, so safe to do last.

### Independent / pick whenever

- **#35 demo22 light radius slider** ([`demo22-light-radius-imgui.md`](demo22-light-radius-imgui.md)) — one file, one sitting, no dependency on the port pass.
- **#3 planar_shadow / #4 rotate_around_axis** ([`planar-shadow-matrix.md`](planar-shadow-matrix.md), [`rotate-around-axis.md`](rotate-around-axis.md)) — curriculum-side `pyMatrixStack`. No port dependency. Do these when a curriculum demo actually needs them (`chapt01/block` already has inline copies of the shadow math; nothing else blocks).

## Smoke-test approach (used in Phase 1, repeat for Phases 2–3)

Phase 1 was approached as: hand-write the helper + migrate ONE small demo (`chapt15/shaders.py`) as a proof-of-concept, get Bill to verify, then write a migration script for the other ~95. Worked well — caught the GLFW_DECORATED-vs-set_window_monitor design issue early before the bulk migration.

Same approach is recommended for Phase 2: hand-write the Camera helper + migrate one canary demo first (probably `chapt08/sphereworld` since Bill flagged sphereworld camera quality specifically) before propagating to the other ~50 3D ports.

## Order summary (one-liner per task)

1. ✅ **#33 + #34** — shared `_common.py` (menubar + window size + fullscreen toggle), applied to every port
2. **#38** — walk-around Camera helper in `_common.py`, applied to 3D ports
3. **#39** — sphereworld camera fix (canary for #38's design)
4. **#37** — keyboard standardization (binds keys to #38's camera, surfaces in #33's menu)
5. **#36** — replace CLI args with ImGui (lives in #33's menu/windows)
6. **#40** — visible light marker (independent additive, safe last)
7. **#35, #3, #4** — independent, do when convenient

## Resolved open questions (Phase 1)

- Helper module location: `/mvp/ports/openglsuperbiblev4/_common.py` (sibling-of-chapter-dirs, one level above `chapt11/_thunderbird_data.py`).
- Fullscreen default: windowed-by-default at 1920×1080, View menu toggles to fullscreen on demand.

## Open questions before starting Phase 2

- demo22's exact camera model: read it first, don't guess. (#38 plan is written assuming I'll read demo22 before implementing, not as a substitute for that.)
- Where does the new `Camera` class live? Same `_common.py`, or a separate `_camera.py` if the helper is getting large?
- Mouse-look vs. keyboard-look: cross-platform mouse capture has Wayland quirks. Pick one before implementing.
