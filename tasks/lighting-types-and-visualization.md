# Lighting: light types in demo22, a half-angle visualization, and the ports' light markers

**Status:** proposed — needs go-ahead. **Merged 2026-09-08** from three tasks the maintainer filed
on 2026-08-27 (`demo22-light-types-and-flashlight`, `mvpvis-lighting-demo-half-angle`,
`port-sb4-directional-far-light`), each of which had already asked in its own Open questions
whether it was the same effort as the others. Their factual halves were answered by
`tasks/reference/lighting-and-shading.md` (written the same day, after them); what remained in all
three was one scope conversation, which is what this task is. The originals are archived at
`tasks/archive/2026/09/08/`.
**Priority:** 6
**Difficulty:** 5

## BLUF

Three strands of one subject — **how a light is modelled and how it is made visible** — across the
three places mvp teaches lighting:

- **A.** demo22 today has exactly one light type (directional). Add the others a student should
  meet: a **positional** light and a **spotlight** ("flashlight"), so the curriculum shows the
  distinction rather than asserting it.
- **B.** The `mvpvisualization/` Cayley demos have **no lighting at all**. A lighting
  visualization drawing the L / V / N / H vectors would be an 8th viz demo (or an overlay) — the
  half-angle idea made visible.
- **C.** The SuperBible ports have **no light marker of any kind**, and if one is added, a
  *directional* light must not get a positional sphere — it has no position. This is the
  convention half of `ports-ux-pass.md` Phase 3 #40.

Done = the maintainer's answers below are recorded, and each strand is either implemented or split
back out as its own scoped task with the answers baked in.

## Correction carried in from the merge (read this before planning C)

All three source tasks stated, as established fact, that
`tasks/archive/2026/06/14/ports-visible-light-source.md` "added the visible light marker across lit
ports". **It did not.** That file is archived with `**Status:** not started` — it is one of five
2026-06-14 satellites archived because their content was *folded into* the `ports-ux-pass.md`
umbrella, not because they were done, and `ports-ux-pass.md` Phase 3 still lists #40 as not
started. Verified 2026-09-08: `grep -rn light_marker ports/` returns nothing, and
`ports/openglsuperbiblev4/_common.py` has no `draw_light_marker`.

So strand C is **not** "refine an existing marker convention" — the marker does not exist yet.
`tasks/reference/lighting-and-shading.md` (§"What this de-blocks") repeated the same wrong claim and
is corrected in the same pass as this merge.

**What *does* exist** is demo22's own marker — a cone + bulb built by `_build_marker_cone` /
`_build_marker_sphere` (`src/modelviewprojection/demos/demo22/demo22.py:1049`, `:1076`) and placed
at `light_dir * light_radius` (`:1483-1489`). That is the reference implementation to copy from,
and it is *the* reason the ports' marker was specified as "demo22-style".

## Context — the facts, already verified (don't re-derive)

From `tasks/reference/lighting-and-shading.md`, which anchors every claim at `file:line`:

- **Fixed-function light type is read off the `w` of the light position.** `w = 0.0` → directional
  (a direction, no position, no attenuation); `w = 1.0` → positional; positional + `GL_SPOT_*` →
  spotlight. This is the whole basis of strand C's convention.
- **The "directional light far away" SB4 demo is `ports/openglsuperbiblev4/chapt05/shadow/shadow.py:41`**
  (`light_pos = (-75.0, 150.0, -50.0, 0.0)`). This answered the original task's Q1; only the
  visual-convention question was left.
- **The flashlight reference is `chapt05/spot/spot.py:29`** — `light_pos = (0, 0, 75, 1.0)` plus
  `GL_SPOT_DIRECTION` (`:121`) and a spot cutoff. chapt05 is SB4's lighting chapter.
- **demo22 is directional-only today** — `demos/demo22/demo22.py:1112` ("constant directional
  light"), `:1132` ("Lw==0 for a directional light") — with Lambert shading, a shadow map, and the
  marker above. Its azimuth/elevation/radius imgui sliders already exist
  (`:1396-1404`; that was task #35, closed 2026-09-08 as already implemented).
- **demo23 already has the half-angle math** — Blinn-Phong via the half-vector,
  `demos/demo23/litjet.frag:47`, with `l = normalize(lightDirWS)` (`:41`) and
  `n = normalize(v_normal_ws)` (`:40`). Strand B reuses this rather than deriving it.
- **The Cayley engine has no lighting mechanism** — a grep for `glLight`/Lambert/diffuse/specular/
  Blinn across `src/modelviewprojection/cayley/` and `mvpvisualization/` returns nothing. So strand
  B is a net-new engine capability, not an extension.

Adjacent and deliberately *not* merged in: **`axis-cylinder-cone-lighting.md`** (deferred, P8) —
lighting the cylinder+cone axis *arrows* in the viz demos. It is a different deliverable (the
gizmo, not a lesson about light), but its Option 2 builds exactly the lit-shader pipeline for
`mvpvisualization/` that strand B would need, so **whichever of the two is done first should build
that pipeline for both**.

## The three strands, as work

### A — demo22 light types + flashlight
Add a positional light and a spotlight alongside the existing directional one, reusing demo22's
marker and slider panel. The marker convention from strand C applies here first, since demo22 is
where the ports copy from: a directional light's marker means "direction", a positional light's
means "place".

### B — a lighting visualization in `mvpvisualization/`
Draw L (to light), V (to eye), N (surface normal) and H (the half-vector) at a point on a surface,
plus the light source itself, with the shading recomputed as the light or eye moves. Reuse
demo23's half-vector math. Needs the lit-axis/lit-shader pipeline (see the `axis-cylinder-cone-lighting`
note above) — the Cayley engine has nothing to build on.

### C — the ports' light markers, with the directional carve-out
Add `draw_light_marker(pos, size)` to `ports/openglsuperbiblev4/_common.py` (this is `ports-ux-pass.md`
Phase 3 #40, still unstarted) and migrate the lit ports, with the rule that a **`w = 0.0`
directional** light gets whatever the maintainer picks for "a direction from infinity" — *not* a
sphere at a fabricated position. `ports-ux-pass.md` sequences #40 last within Phase 3 because it is
purely additive; that ordering still holds.

## Open questions (the reason this is one task and not three)

1. **Scope of A** — demonstrate all three light *types* in demo22 (directional / positional /
   spot), or add only the flashlight to the existing directional one? *(Recommend all three: the
   `w` distinction is the lesson, and demo22 is the lighting capstone.)*
2. **B: new demo or overlay** — an 8th standalone `mvpvisualization/` demo, or a lighting overlay
   toggled on an existing one? *(Recommend standalone: the viz demos each teach exactly one idea,
   and lighting is not the Cayley-graph idea the others share.)*
3. **B ↔ A relationship** — is the visualization the *companion* to demo22's lighting (same light
   model, shown two ways), or an independent demo with its own scene? *(Recommend companion —
   it costs nothing and the cross-reference teaches.)*
4. **C: the directional marker convention** — an arrow from off-scene / an at-infinity indicator,
   or simply no marker plus a label? *(Recommend an arrow: "no marker" loses the very information
   the marker exists to give, while a sphere would state a position the light does not have.)*
5. **C: which ports get markers** — every lit port (the chapt05/06/08/09/11/14/17/18/19 family
   listed in `ports-ux-pass.md` #40), or only the lighting chapter (chapt05) where it is the
   lesson? *(Recommend all lit ports: it is additive and the reason it was asked for is that a
   student cannot reason about shading without seeing the source.)*
6. **Ordering against `axis-cylinder-cone-lighting`** — build the `mvpvisualization/` lit-shader
   pipeline once, as part of whichever of the two runs first? *(Recommend yes, and do the axis
   lighting first: it is smaller, already scoped, and its Option 1 is a 15-minute fixed-function
   win that proves the shading before the shader work.)*

## Related

- `tasks/reference/lighting-and-shading.md` — the inventory this task rests on (and the doc whose
  §"What this de-blocks" is corrected by the merge).
- `tasks/ports-ux-pass.md` — Phase 3 #40 is strand C; #38/#39 (the camera) come first in that
  umbrella.
- `tasks/axis-cylinder-cone-lighting.md` — the viz demos' axis-arrow lighting; shares strand B's
  shader pipeline.
- `tasks/archive/2026/09/08/demo22-light-radius-imgui.md` — demo22's light sliders (already
  implemented; closed 2026-09-08).
- `tasks/archive/2026/06/14/ports-visible-light-source.md` — #40's original satellite, archived
  **unstarted**; see the Correction above.
