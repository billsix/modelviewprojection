# Plan: Fix sphereworld camera controls to match demo22

**Status:** not started — task #39. Recorded 2026-04-28.

**Scope:** the sphereworld ports under `/mvp/ports/openglsuperbiblev4/`. Specifically:
- `chapt08/sphereworld/sphereworld.py`
- `chapt11/sphereworld/sphereworld.py`
- `chapt19/SphereWorld32/SphereWorld32.py`

## What

The sphereworld ports' camera controls don't feel right to Bill. Replace with demo22-style walk-around camera.

## Why

This is the specific instance Bill flagged by name: "for the sphereworld demos, movement is not right. Look at demo22, and use similar camera controls."

Tracking it as its own task (vs. rolling into [ports-walkaround-camera.md](ports-walkaround-camera.md) #38) because:
- Sphereworld is the biggest scene in the curriculum (random sphere field + ground plane). Camera quality is most visible here.
- It appears 3 times in the ports tree, so a per-demo fix needs 3 edits — likely the right order is to fix one as the reference, then propagate.
- It's also Bill's stated wishlist demo to modernize as `demo24` or later (see auto-memory `project_superbible_ports.md`) — so the camera shape decided here should match what he wants for the curriculum-side modernized version eventually.

## How

1. Do [ports-walkaround-camera.md](ports-walkaround-camera.md) first — defines the camera model.
2. Pick `chapt08/sphereworld/sphereworld.py` as the reference fix (oldest chapter, minimal extras).
3. Replace its `camera_x` / `camera_z` / `camera_yaw` controls with the common Camera helper.
4. Propagate to chapt11/sphereworld and chapt19/SphereWorld32, keeping each chapter's added features (chapt11's display lists, chapt19's FSAA + planar shadow).

## Scope

3 files. No new C++ source to read — all three already exist in the tree.

## Open questions

- The chapt19/SphereWorld32 port currently uses keyboard yaw (Left/Right arrows for yaw, Up/Down for forward/back). That's the closest to demo22 of the three — confirm by reading both before changing.
- Should the camera be height-clamped (FPS-on-ground) or free-fly (Y-up traversal)? Sphereworld's spheres rest on a ground plane, so FPS-on-ground feels right — but verify with demo22.
