# Plan: ImGui controls for light position radius in demo22

**Status:** not started — task #35. Recorded 2026-04-28.

**Scope:** `/mvp/src/modelviewprojection/demo22.py` (curriculum-side), *not* the SuperBible ports.

## What

Expose the light-position radius (or whatever parameterizes the light placement around the scene) as an `imgui` slider in demo22, so students can move the light interactively and watch the lighting / shadow update in real time.

## Why

- demo22 is the lighting/planar-shadow/texturing capstone of the curriculum-side demoNN tree. It's also the demo Bill cited as the reference for camera controls, light visibility, and ImGui integration in the SuperBible ports — so it's the touchstone other tasks will copy from.
- A slider for the light radius makes the relationship between light position, surface normal, and shading visible to the student in real time, supporting the lighting chapter's pedagogy.

## How

- Look at how demo22 currently positions the light (likely `light_pos = [x, y, z, w]` somewhere). Identify the parameterization Bill has in mind — radius implies the light orbits the scene at some angle, so probably `(radius, theta, phi)` or `(radius, yaw, pitch)`.
- Add an ImGui collapsing header or floating window with sliders.
- Slider ranges should be reasonable defaults (radius probably 1.0–50.0; angles in degrees).

## Scope

- One file: `demo22.py`.
- Don't refactor the lighting model. Just expose the parameters that already exist.

## Open questions

- Is the radius the only parameter Bill wants, or also angle? "Make the radius adjustable" reads literally — start with one slider, ask before adding more.
- Should the slider also control the visible light marker (see [ports-visible-light-source.md](ports-visible-light-source.md))? demo22 already shows a visible light, so the marker should track the slider automatically — verify in code.
