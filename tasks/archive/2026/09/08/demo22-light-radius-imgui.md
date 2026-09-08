# Plan: ImGui controls for light position radius in demo22

**Status:** **DONE — closed 2026-09-08 as already implemented.** The work exists in
`src/modelviewprojection/demos/demo22/demo22.py`; nobody recorded it against this task, so it sat
at "not started" while the feature shipped. Verified 2026-09-08:

- `:1396-1404` — three imgui sliders in the light panel: `"Azimuth (deg)"` (0–360),
  `"Elevation (deg)"` (5–89), and `"Radius (marker only)"` (10–150), driving the module-level
  `light_az_deg` / `light_el_deg` / `light_radius` (`:176-177`, `:1111`).
- `:1407-1410` — the light direction and the shadow are recomputed **every frame** from the
  slider values, so moving a slider reshapes the Lambert shading and the floor shadow live.
- **The open question below is answered by the code:** the visible marker *does* track the
  slider — `:1483-1489` places the cone+bulb at `light_dir * light_radius` and orients it from
  `light_az_deg`/`light_el_deg`. And the answer to "radius only, or angle too?" turned out to be
  *both*: azimuth and elevation are the pedagogically useful pair (they change the shading),
  while radius is marker-only, which the slider label says out loud.

Recorded 2026-04-28 as task #35. **Priority:** 6 · **Difficulty:** 3

**Scope:** `src/modelviewprojection/demos/demo22/demo22.py` (curriculum-side), *not* the
SuperBible ports. (The original path in this doc, `src/modelviewprojection/demo22.py`, predates
the 2026-06-03 restructure that moved the demos into `demos/`.)

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
- Should the slider also control the visible light marker (see the visible-light-source task, #40, now folded into [ports-ux-pass.md](ports-ux-pass.md) Phase 3)? demo22 already shows a visible light, so the marker should track the slider automatically — verify in code.
