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

Plans: [`ports-imgui-menubar.md`](archive/2026/04/28/ports-imgui-menubar.md), [`ports-window-size-1920x1080.md`](archive/2026/04/28/ports-window-size-1920x1080.md) (archived). Detail in those files.

Result: `/mvp/ports/openglsuperbiblev4/_common.py` exists with `resolve_default_window_size`, `init_imgui`, `WindowState`, `toggle_fullscreen`, `draw_menubar`. 92 ports migrated by script, 1 hand-written reference (`chapt15/shaders.py`), 7 stubs skipped. All 100 files compile clean. Bill verified menubar+fullscreen on `chapt15/shaders.py` and the imgui panel on `chapt01/Block.py`.

Three migration bugs hit and fixed in pass: line-concatenation regex, `impl.shutdown()` placement (placed inside `if not window:` initially, then over-corrected, then placed correctly), multi-line `from ... import (...)` block split. See [`ports-imgui-menubar.md`](archive/2026/04/28/ports-imgui-menubar.md#bugs-hit-during-the-bulk-migration-resolved) for detail.

### Phase 2 — camera (3D ports only) — NEXT (first attempt rolled back)

**First attempt 2026-04-29 was reverted via `git reset` after the bulk migration broke ~10 demos.** Postmortem at [`postmortem-phase2-attempt-1.md`](archive/2026/04/28/postmortem-phase2-attempt-1.md) — read it before re-attempting. Key takeaways: the canary on `chapt08/sphereworld` worked end-to-end (Bill confirmed), but the bulk-migration regex partially-replaced function bodies and left orphan references that compiled clean but failed at runtime. Use libcst or hand-migrate per pattern group next time, and grep for stale references after any pass.

Tasks: **#38 (walk-around camera), then #39 (sphereworld) immediately after.**
(Detail for both folded in below from the archived `ports-walkaround-camera.md`
and `ports-sphereworld-camera-fix.md` satellites, 2026-06-14.)

- Read demo22's camera in `/mvp/src/modelviewprojection/demo22.py` and document the model.
- Add `Camera` class (or module-level functions) to `_common.py`:
  - `Camera.update(window, dt)` — read keys, mutate position/yaw.
  - `Camera.apply()` — call the equivalent of `gluLookAt` with current state.
- Migrate 3D ports to use the new Camera. Replace each port's per-demo `camera_x/y/z/yaw` triples and inline view-matrix setup.
- **#39 immediately after #38** because sphereworld is the most camera-heavy scene; if the new Camera doesn't feel right there, the design needs revision and it's better to find out early. Sphereworld is also Bill's stated wishlist demo (`demo24` modernization), so the camera shape decided here will eventually echo to the curriculum side.

**Why second:** Phase 1 already gave us imgui setup; Phase 2 adds the camera model that Phase 3's keyboard task binds to.

#### #38 — Walk-around camera (demo22-style) for all 3D ports
**Status:** not started (recorded 2026-04-28).
**Why:** Bill — "for anything that has 3D space, I want movement in 3D like
demo22. I want to be able to walk around. I never want to just rotate around
something, unless you tell me a reason why." Many SuperBible originals chose
orbit/dolly because the C++ demos were short showpieces; for students walking the
textbook, walk-around makes spatial relationships (light position, shadow
direction, normals) tangible.
**Reference:** demo22's camera (`/mvp/src/modelviewprojection/demo22.py`) — read
it, document the model (likely yaw + position triple, no roll, pitch clamped or
absent), then replace per-demo cameras in the ports with the same model. The
`gluLookAt`-equivalent view setup becomes uniform across ports.
**Scope — need walk-around:** all chapt05–chapt09 3D scenes; chapt11/sphereworld
+ starrynight (already FPS-ish — confirm they match demo22); chapt12 (planets,
moons, select); chapt13 (occquery); chapt14 (shadowmap); chapt15–17 shader demos
(currently X/Y/Z + Shift to translate, no yaw — orbit-ish); chapt18 FBO/HDR;
chapt19/SphereWorld32.
**Legitimately don't need walk-around (justify in a per-demo comment, per Bill):**
2D demos (chapt02/glrect, chapt02/bounce, chapt03 primitives, chapt19/GLRect,
chapt21/fonts); single-object demos where rotation IS the demo (chapt10 NURBS? —
verify case by case).
**Open Qs:** strict FPS (no pitch) vs free-look (pitch+yaw) — copy whatever
demo22 does; mouse-look vs keyboard-look (mouse capture has Wayland quirks;
keyboard-look safer for curriculum but mouse more comfortable) — ask Bill.

#### #39 — Sphereworld camera fix (canary for #38's design)
**Status:** not started (recorded 2026-04-28).
**Why:** the specific instance Bill flagged by name — "for the sphereworld demos,
movement is not right. Look at demo22, and use similar camera controls."
Sphereworld is the biggest scene (random sphere field + ground), so camera quality
is most visible; it appears 3× in the tree; and it's Bill's wishlist `demo24`
modernization, so the camera shape decided here should match the eventual
curriculum version.
**Files (3):** `chapt08/sphereworld/sphereworld.py`,
`chapt11/sphereworld/sphereworld.py`, `chapt19/SphereWorld32/SphereWorld32.py`.
**How:** do #38 first (defines the camera model). Pick `chapt08/sphereworld` as
the reference fix (oldest chapter, minimal extras); replace its
`camera_x`/`camera_z`/`camera_yaw` controls with the common Camera helper; then
propagate to chapt11 (keep its display lists) and chapt19/SphereWorld32 (keep its
FSAA + planar shadow). No new C++ source to read — all three exist already.
**Open Qs:** chapt19/SphereWorld32 already uses keyboard yaw (Left/Right yaw,
Up/Down forward/back) — closest to demo22 of the three; confirm by reading both.
Height-clamped (FPS-on-ground) vs free-fly — spheres rest on a ground plane so
FPS-on-ground feels right, but verify against demo22.

**Out of scope this phase:** demos that don't have a 3D camera (chapt02/glrect, chapt03 primitives, chapt19/GLRect, chapt21/fonts, etc.) and demos where rotation is the demo (some chapt10 NURBS — verify case by case with a per-demo justification comment as Bill requested).

### Phase 3 — polish (additive, lower blast radius)

Tasks: **#37 (keyboard), then #36 (CLI→ImGui), then #40 (visible light).**
(Detail folded in below from the archived `ports-keyboard-standardization.md`,
`ports-replace-cli-with-imgui.md`, and `ports-visible-light-source.md` satellites,
2026-06-14.)

#### #37 first within Phase 3 — keyboard standardization
**Status:** not started (recorded 2026-04-28).
By this point the menubar (#33) and camera (#38) both exist. Decide one keymap
(matching demo22). Per-demo toggles move into menubar entries, freeing keys. Add a
Help → Controls entry to the menubar that displays the active bindings.
**Why:** Bill — "check for standardization of keyboard controls. Movement in 3D
space should be consistent." Currently each chapter chose its own (X/Y/Z+Shift for
movement in chapt15+ shaders; arrow keys for pan in chapt12; WASD-ish elsewhere;
R/L/U/D for rotation; assorted single-letter toggles B/V/F/P/M).
**Reference:** demo22's controls (`/mvp/src/modelviewprojection/demo22.py`) — read
first, don't guess. **Likely convention (verify against demo22):** W/A/S/D
forward/left/back/right; Q/E or mouse for yaw; Space/Shift up/down (or disallow
vertical for floor-bound demos); Esc to quit (already universal); demo-specific
toggles move into the ImGui menubar (#33), so the keyboard reserves only what must
be a key.
**Scope:** every port with movement/camera keys; non-3D-camera demos
(chapt02/glrect, chapt03 primitives, chapt19/GLRect, chapt21/fonts) only need
Esc-to-quit; menubar shows active bindings in a Help/Controls menu.
**Open Qs:** WASD vs arrows vs both (pick one canonical, other as alias);
chapt17/imageproc `P`-then-`1..5` pass count → ImGui slider, freeing `P`; demo22's
*exact* controls — read first.

#### #36 second within Phase 3 — replace CLI args with ImGui controls
**Status:** not started (recorded 2026-04-28).
Smaller scope — only ports that currently take CLI args. Needs #33's menubar in
place to host the ImGui controls.
**Why:** students shouldn't read help output or pass flags to see different demo
states — every option visible/toggleable in the running window. Demos should be
runnable with no flags and configured live.
**How:** `grep -rn "argparse\|sys.argv\|getopt" /mvp/ports/openglsuperbiblev4/` to
find CLI-driven ports; for each, replace CLI parsing with default values + ImGui
sliders/checkboxes/radio buttons in the main loop; surface them via the #33
menubar (menu items or a "Controls" floating window the menubar toggles).
**Scope:** only ports that take CLI args (most are already self-contained); any
future port follows the convention. Lands with / in known order after the menubar
task (same ImGui setup).
**Open Q:** ports legitimately needing a CLI arg (e.g. a data-file path) → ImGui
file dialog or a menu "Open…" item, but most load assets from a fixed path, so
unlikely.

#### #40 last within Phase 3 — visible light source (demo22-style)
**Status:** not started (recorded 2026-04-28).
Add `draw_light_marker(pos, size=0.5)` to `_common.py`. Migrate lit ports to call
it. Purely additive — won't break a demo if left alone, so safe to do last.
**Why:** Bill — "for anything that has a light source, I want it to be visible,
like in demo22." Without a marker students see lighting effects but can't reason
about which face is lit/shadowed. Zero pedagogical complexity (just another
sphere), high value.
**How:** find demo22's light-marker pattern — likely a small white sphere drawn at
`light_pos` with lighting *disabled* (full white regardless of orientation) and
depth test enabled (occludes correctly). Factor into `draw_light_marker(pos,
size)` in the shared module; each lit port calls it before/after `draw_models()`.
**Scope — lit demos:** chapt05 (lights, litjet, material, shadow, sphereworld if
lit), chapt08 (sphereworld, tunnel), chapt09 (advanced texturing), chapt11
(sphereworld, starrynight), chapt14 (shadowmap), chapt17 (lighting, proctex,
fragmentshaders, imageproc — have `light_pos` uniforms), chapt18 (fboshadowmap,
fbodrawbuffers, fboenvmap, hdrbloom), chapt19 (SphereWorld32). Any demo that
intentionally hides the light keeps current behavior with a comment.
**Coordination:** demo22's own marker should track the radius slider once #35
([`demo22-light-radius-imgui.md`](demo22-light-radius-imgui.md)) lands; the
walk-around camera (#38) makes the marker more useful (walk around the light).
**Open Qs:** marker as sphere vs point sprite vs billboard (sphere simplest;
demo22 likely sphere); pure white vs tinted toward diffuse color (ask Bill); size
relative to scene scale (chapt15 ~100-unit vs chapt08 ~1-unit) — pass per-demo or
scale by scene radius; defer.

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
