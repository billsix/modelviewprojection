# mvp — lighting & shading inventory

**Reference document** — what lighting/shading each demo actually implements, so the lighting-task
family can cite verified facts instead of re-deriving them. Not a task; update in place. Created
2026-08-27 (William Emerison Six <billsix@gmail.com>) from a direct read (all `file:line` verified at
their real paths). Companion to `tasks/reference/notable-subsystems.md` and `superbible-ports-guide.md`.

## Two lighting worlds (verified distinct)

### 1. Curriculum demos — GL 3.3 core, shader-based, share `util/shading.py`
`src/modelviewprojection/util/shading.py` holds the shared lighting/geometry helpers (`_face_normal`,
light-direction) used by the lighting-era demos.
- **demo22** (`src/modelviewprojection/demos/demo22/demo22.py`) — a **directional light + Lambert**
  shading, plus a shadow-map and a visible light marker. The curriculum's Lambert demo.
- **demo23** (`src/modelviewprojection/demos/demo23/`) — Lambert **+ Blinn-Phong specular via the
  half-vector**: `litjet.frag:47` ("Blinn-Phong: use the half-vector between view and light"),
  `l = normalize(lightDirWS)` (`:41`), `n = normalize(v_normal_ws)` (`:40`). This is the demo to reuse
  for any half-angle-vector visualization.

### 2. SuperBible v4 ports — fixed-function `glLight*`, classify by the light-position `w`-component
The SB4 ports (`ports/openglsuperbiblev4/`) use fixed-function lighting; **chapt05 is the lighting
chapter**. The light *type* is read off the 4th component of the light position:
- **DIRECTIONAL (w = 0.0 — "infinitely far away"):** `chapt05/shadow/shadow.py:41`
  `light_pos = (-75.0, 150.0, -50.0, 0.0)`. **This is the concrete answer to "which SB4 demo does a
  directional light far away"** (`tasks/lighting-types-and-visualization.md`, strand C).
- **SPOTLIGHT (positional w = 1.0 + a cone):** `chapt05/spot/spot.py:29`
  `light_pos = (0.0, 0.0, 75.0, 1.0)` + `GL_SPOT_DIRECTION` (`:121`) + a spot cutoff. This is the
  "flashlight" primitive (`tasks/lighting-types-and-visualization.md`, strand A).
- **POSITIONAL (w = 1.0):** the lit-object ports — litjet, shinyjet, the sphereworlds (chapt05/06/08/…)
  — all use a `w = 1.0` light position.
- **AMBIENT-only:** `chapt05/ambient/`.

> **Correction (2026-09-08): the SB4 ports have NO light marker.** An earlier revision of this doc
> said the positional ports "got the visible-light-source marker in archived
> `2026/06/14/ports-visible-light-source.md`". They did not: that task is archived with
> `**Status:** not started` — one of five 2026-06-14 satellites archived because their content was
> *folded into* the `tasks/ports-ux-pass.md` umbrella, where it is still Phase 3 item #40, unstarted.
> Verified 2026-09-08: `grep -rn light_marker ports/` returns nothing and
> `ports/openglsuperbiblev4/_common.py` has no `draw_light_marker`. **The marker that does exist is
> demo22's** — a cone + bulb (`src/modelviewprojection/demos/demo22/demo22.py:1049`, `:1076`, placed
> at `:1483`), which is what "demo22-style marker" refers to and what the ports would copy.

### 3. `mvpvisualization` / Cayley engine — NO lighting at all (verified)
Grep for `glLight`/Lambert/diffuse/specular/Blinn across `src/modelviewprojection/cayley/` and
`mvpvisualization/` returns nothing — the Cayley engine has **no lighting mechanism**. So any lighting in
a `mvpvisualization` demo (`tasks/lighting-types-and-visualization.md`, strand B) is a **net-new engine
capability**, not an extension of existing code (reuse demo23's half-vector math for the shading itself).
`tasks/axis-cylinder-cone-lighting.md` Option 2 would build the same lit-shader pipeline for the axis
arrows — whichever runs first should build it for both.

## The rule to remember

**Fixed-function light type = the `w` of the light position:** `w = 0.0` → directional (a direction, no
position, no attenuation); `w = 1.0` → positional (has a place; add `GL_SPOT_*` → spotlight). This is why
a directional light should NOT get a positional sphere marker — it has no position — which is the
distinction strand C of `tasks/lighting-types-and-visualization.md` is about.

## What this de-blocks (the facts those tasks were asking for)

The three tasks below were merged into **`tasks/lighting-types-and-visualization.md`** on
2026-09-08 (originals archived at `tasks/archive/2026/09/08/`), precisely because this doc had
answered their factual halves and only one scope conversation was left across all three:

- **directional-far-light (now strand C)** — the demo is **`chapt05/shadow`** (w=0); only the
  marker convention (arrow-from-infinity vs sphere) remains a maintainer aesthetic call — and note
  the marker itself is still unbuilt (see the Correction above).
- **light types + flashlight (now strand A)** — "flashlight" = a spotlight; the reference impl is
  `chapt05/spot` (positional + `GL_SPOT_DIRECTION` + cutoff). demo22 is directional-only today.
- **half-angle visualization (now strand B)** — confirmed net-new (Cayley has no lighting); reuse
  `demo23/litjet.frag:47` half-vector math.

## Cross-links

- `tasks/reference/superbible-ports-guide.md` (the port tree), `notable-subsystems.md` (demo inventory).
- `tasks/lighting-types-and-visualization.md` — the one open lighting task, which cites this doc for
  its factual half; `tasks/ports-ux-pass.md` Phase 3 #40 is where the ports' marker is sequenced.
- `tasks/axis-cylinder-cone-lighting.md` — lighting the viz demos' axis arrows (deferred); shares
  the lit-shader pipeline with strand B.
