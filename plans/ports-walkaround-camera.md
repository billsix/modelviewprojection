# Plan: Walk-around camera (demo22-style) for all 3D SuperBible ports

**Status:** not started — task #38. Recorded 2026-04-28.

**Scope:** SuperBible ports under `/mvp/ports/openglsuperbiblev4/` that place a camera in 3D space.

## What

Any SuperBible port with a 3D camera should support walk-around movement (FPS-style: WASD or equivalent + yaw control or mouse-look). The default should NOT be orbit / rotate-around-target *unless* there's a stated reason.

## Why

Bill: "for anything that has 3D space, I want movement in 3D like demo22. I want to be able to walk around. I never want to just rotate around something, unless you tell me a reason why."

Many SuperBible originals chose orbit/dolly camera because the C++ demos were short — they wanted to show off a single object. But for students walking through the textbook, a walk-around camera makes spatial relationships (light position, shadow direction, surface normals) tangible.

## How

**Reference:** demo22's camera in `/mvp/src/modelviewprojection/demo22.py`. Read it, document the model (likely yaw + position triple, no roll, no pitch above some clamp), then replace the per-demo cameras in the ports with the same model.

Per-demo translation:
- Replace `camera_pos` + `camera_yaw` triples already in many ports (chapt15+) with a shared `Camera` class (or module-level functions) imported from a common helper.
- The view-matrix setup (the `gluLookAt` call or equivalent) becomes uniform across ports.

## Scope

Demos that need a walk-around camera:
- All chapt05–chapt09 ports with 3D scenes
- chapt11/sphereworld, starrynight (already FPS-camera-style — confirm they match demo22)
- chapt12 ports (planets, moons, select)
- chapt13 (occquery)
- chapt14 (shadowmap)
- chapt15–17 shader demos (currently X/Y/Z + Shift to translate camera, no yaw — definitely orbit-ish)
- chapt18 FBO/HDR demos
- chapt19/SphereWorld32

Demos that *legitimately* don't need walk-around (must justify in a comment per Bill's instruction):
- 2D demos (chapt02/glrect, chapt02/bounce, chapt03 primitives, chapt19/GLRect, chapt21/fonts)
- Demos showing a single object front-and-center where rotation IS the demo (chapt10 NURBS demos? — verify case-by-case)

## Coordination

- [ports-keyboard-standardization.md](ports-keyboard-standardization.md) (#37) — assigns the keys.
- [ports-sphereworld-camera-fix.md](ports-sphereworld-camera-fix.md) (#39) — specific instance.

Do this task first (define camera model), then keyboard-standardization (bind keys), then sphereworld fix (apply pattern).

## Open questions

- Strict FPS (no pitch) vs. free-look (pitch + yaw)? demo22 likely is one or the other; copy whatever it does.
- Mouse-look vs. keyboard-look (Q/E for yaw, etc.)? Mouse capture has cross-platform quirks (Wayland especially) — keyboard-look is safer for the curriculum but mouse is more comfortable. Ask Bill.
