# Code the Classics: express leadingedge's world→camera as inverse(translate()), and name its spaces

**Status:** IMPLEMENTED 2026-09-04 (branch `codetheclassics-gl1-and-space-refactors`) — the world→camera step is now `inverse(translate(b=self.camera))` on `g3`; the perspective divide stays hand-rolled (correctly — non-invertible). Feasibility byte-identical; frame-180 AE=0; ruff+ty clean.
**Priority:** 5
**Difficulty:** 4

## Implementation record (2026-09-04, while maintainer away — for review)

- **Feasibility PROVEN byte-identical:** in the mvp container, `inverse(translate(b=camera))(v)`
  equals `v - camera` **bit-for-bit** on `g3.Vector` (packed IEEE-754 doubles compared) across
  several 3-D points; `f` is an `InvertibleFunction`. Confirmed gacalc's `translate`/`inverse`
  work on 3-D vectors (the task's Open-Q1 feasibility check).
- **Change (minimal, one hop):** `ports/codetheclassics/vol2/leadingedge/leadingedge.py` — added
  `from gacalc.transforms import InvertibleFunction, inverse, translate`; in `Game.draw`, built
  `world_to_camera = inverse(translate(b=self.camera))` once per frame (captured by the
  `transform` closure); `transform` now does `newpoint = world_to_camera(point_v3)` (was `point_v3
  - self.camera`). The **perspective divide (`x/z`, `y/z`) is left exactly as-is** — it discards
  depth and is not invertible, so it stays a hand-rolled projection (the course's own perspective
  is a projection too, not an `InvertibleFunction`). Chose scope option (a)+(b): the swap **plus**
  a comment naming the spaces/edge; left the divide alone.
- **Verification:** frame-180 differential trace (original HEAD vs converted, mvp container +
  Xvfb, the `update(dt)` game) — **AE = 0** (byte-identical, 69 171 colors both). `ruff` + `ty`
  clean. Update path untouched.
- **Open for maintainer:** book-sequencing chapter for the comment (referenced ch16/ch19+
  generically); whether to also add the one-line pointer to mvp's full-frustum `perspective`
  (Open-Q2 — left out for now to keep the game self-contained).

## BLUF

`leadingedge` is the **only** game with a real 3-D → 2-D **perspective projection**. Study the
feasibility of expressing its **world→camera** step (`point − self.camera`) as the course's own
**`inverse(translate(self.camera))`** on a `g3.Vector` — the book's camera-inverse hinge, now on a
*genuine 3-D camera* — and of **naming the spaces** (track/model → camera → screen) in comments
mapped to the Cayley graph, **without** forcing the non-invertible perspective divide into an
`InvertibleFunction`. **Build on existing book/gacalc functions (`translate`, `inverse`, and
mvp's `perspective`/`ortho` for reference) — do NOT invent new machinery** (maintainer,
2026-09-04). Feasibility-first; behaviour-faithful so **byte-identical**; discuss before
implementing.

## Context (read first)

- **The verified projection** (`leadingedge.py:4230-4245`, read firsthand 2026-09-04):

  ```python
  newpoint = point_v3 - self.camera                 # world → camera space (a TRANSLATION)
  if newpoint.z > clipping_plane: return ...          # near-plane clip
  point_v2 = g2.Vector((newpoint.x / newpoint.z) + HALF_WIDTH,   # perspective divide
                       (newpoint.y / newpoint.z) + HALF_HEIGHT)
  return point_v2, w / -newpoint.z, h / -newpoint.z   # sprite size shrinks with depth
  ```

  The world is honestly 3-D (`Car.pos: g3.Vector(x,y,z)`, z = track depth, `:3136-3148`); the
  camera is a positioned `g3.Vector(0,400,0)` that follows the player (`:4049-4053`).
- **Two clean, separable pieces:**
  1. **`newpoint = point − self.camera` IS `inverse(translate(self.camera))(point)`** — the exact
     book move (camera placement inverted to bring world into camera space), now on a real 3-D
     camera. This part is trivially expressible with `gacalc.transforms`.
  2. **The perspective divide (`x/z`, `y/z`) discards z → not invertible → it must STAY a
     hand-rolled function.** That is *correct*, and consistent with the course: the book's own
     perspective/NDC step (`cs_to_ndc_space_fn`, `perspective`) is a projection, not a general
     `InvertibleFunction` either. Do not try to make it one.
- **The teaching payoff:** leadingedge is where the course's perspective chapters (`CLAUDE.md` ›
  pedagogical arc, demo19/ch19+) have a *real* analogue in a game — and where the ad-hoc version
  stops exactly at the invertible/composable boundary the course generalises past. Naming the
  spaces here (even where the transform stays hand-rolled) is high pedagogical value at zero
  behaviour cost.
- **Fidelity + harness:** behaviour-faithful; verify with the frame-180 byte-identical harness in
  `tasks/adhoc/pgzero-gl-inline/`. Note `leadingedge` is the one `update(dt)` game (its trace
  driver passes `_dt`).

## Design principle (settled — maintainer, 2026-09-04)

Using the book's **taught** math abstractions here is **consistent** with the ports' "library, not
framework" / "clearer code over abstractions" philosophy — not an exception to it. That principle
targets **framework-style inversion of control** (PyGame Zero's runner owning the loop, calling
*up* into the game) and depending on **pgzero-the-framework** — NOT the book's own math.
`translate`/`inverse` (and `perspective`/`cs_to_ndc_space_fn` for reference) are library functions
the game calls *down* into, and the maintainer *teaches* them, so a game (and a book section) that
uses them is coherent with the curriculum. The abstraction **gradient** runs from `boing_gl1.py`
(zero abstractions, rawest fixed-function GL) to this game (a real 3-D projection) — all still
"library, not framework." Two real constraints remain: **(1) book sequencing** — a section
referencing this code must come *after* the perspective chapter (ch19+); **(2) don't reintroduce
the pgzero framework.** Import from **`gacalc.transforms`** (decided).

## Feasibility questions to resolve BEFORE any edit

1. **Does `gacalc.transforms.translate` / `inverse` accept a 3-D `g3.Vector`?** The book uses them
   in both `g2` and `g3` (demos 16+), so almost certainly yes — but **verify** before relying on
   it (import, build `inverse(translate(cam))`, apply to a `g3.Vector`, check the result equals
   `point − cam`).
2. **Type & rounding parity.** `inverse(translate(cam))(point)` returns `Coef` components; the
   divide needs `float()`. Confirm `float(newpoint.x)/float(newpoint.z)` reproduces the current
   arithmetic bit-for-bit (it should — same subtraction, same divide) via the trace.
3. **Scope of the "name the spaces" comments.** Deciding how much Cayley-graph vocabulary to add
   (track/model space → world → camera → screen) without over-annotating game code.

## Open questions

1. **Scope:** (a) just swap the world→camera step to `inverse(translate(self.camera))` (tiny,
   behaviour-identical), or (b) that *plus* comments naming the spaces/edges mapped to the book's
   graph, leaving the divide hand-rolled? *(Recommend both — the small swap makes the
   camera-inverse explicit, and the comments are where most of the teaching value is; the
   perspective divide stays as-is, correctly.)*
2. **Reference the book's `perspective()`?** Should a comment relate the game's simple `f=1`
   divide to mvp's full-frustum `perspective`/`cs_to_ndc_space_fn` (a "this is the same idea, one
   focal length" pointer), or keep the game self-contained? *(Recommend a one-line pointer, not a
   rewrite — the game's divide is deliberately simpler.)*
3. **Book sequencing:** a section referencing this code must come *after* the perspective chapter
   (ch19+). Which chapter is the earliest appropriate anchor? *(Your call — you teach the math.)*
   *(The "is this an exception?" question is settled — see "Design principle": it's consistent, not
   an exception.)*

## Related

- `tasks/reference/coordinate-spaces-in-code-the-classics.md` › "leadingedge — a genuine 3-D → 2-D
  perspective projection" — the evidence base (the set's one true multi-space game).
- `tasks/archive/2026/09/05/codetheclassics-camera-as-inverse.md` — the 2-D camera-inverse case (this is its 3-D
  cousin, on a real camera).
- `tasks/archive/2026/09/05/codetheclassics-myriapod-rotation-as-functions.md` — the 2-D rotate case.
- `CLAUDE.md` › pedagogical arc (demo19/ch19 perspective) — the course chapters this game mirrors.
- `tasks/adhoc/pgzero-gl-inline/` — the byte-identical trace harness (`update(dt)` variant).
