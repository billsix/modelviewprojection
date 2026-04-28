# Plan: Visible light source (demo22-style) in all lit SuperBible ports

**Status:** not started — task #40. Recorded 2026-04-28.

**Scope:** SuperBible ports under `/mvp/ports/openglsuperbiblev4/` that use a light source.

## What

Any port that uses an OpenGL light should render a small visible marker (sphere, point sprite, or icon) at the light's world-space position, so the student can see *where* the light is. demo22 already does this and is the reference.

## Why

Bill: "for anything that has a light source, I want it to be visible, like in demo22."

Without a visible marker, students see lighting effects but can't reason about why a particular face is lit or shadowed because they can't see the source. Adds zero pedagogical complexity (the marker is just another sphere) and high pedagogical value.

## How

- Find demo22's light-marker pattern. Likely: a small white sphere drawn at `light_pos` with lighting *disabled* (so it shows full white regardless of orientation) and depth test enabled (so it occludes / is occluded correctly).
- Factor into a helper — probably `draw_light_marker(pos, size=0.5)` in the same shared module that hosts the menubar / camera helpers from #33 / #38.
- Each lit port calls `draw_light_marker(light_pos)` before / after `draw_models()`.

## Scope

Lit demos that need this:
- **chapt05** (lighting chapter — `lights`, `litjet`, `material`, `shadow`, `sphereworld` if they have a light)
- **chapt08** (texturing with lighting — `sphereworld`, `tunnel`)
- **chapt09** (advanced texturing)
- **chapt11** (sphereworld, starrynight)
- **chapt14** (shadowmap)
- **chapt17** (lighting, proctex, fragmentshaders, imageproc) — these have `light_pos` uniforms
- **chapt18** (fboshadowmap, fbodrawbuffers, fboenvmap, hdrbloom)
- **chapt19** (SphereWorld32)

Demos that intentionally hide the light (none come to mind, but if any) keep their current behavior with a comment.

## Coordination

- [demo22-light-radius-imgui.md](demo22-light-radius-imgui.md) (#35) — demo22's light marker should already track the radius slider once that lands.
- [ports-walkaround-camera.md](ports-walkaround-camera.md) (#38) — the walk-around camera makes the visible light marker more useful, since the student can walk around the light and see it from different angles.

## Open questions

- Marker as a small sphere vs. point sprite vs. textured billboard quad? Sphere is simplest; demo22 likely uses a sphere.
- Marker color: pure white vs. tinted toward the light's diffuse color? Pure white reads as "light source" universally; tinted is more honest about the light's color. Ask Bill.
- Size relative to scene scale: hard to pick one default since each demo's scale differs (chapt15 uses ~100-unit scenes, chapt08 uses ~1-unit scenes). Either pass per-demo, or scale relative to scene radius. Defer.
