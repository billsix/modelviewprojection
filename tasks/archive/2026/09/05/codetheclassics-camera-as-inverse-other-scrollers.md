# Replicate camera-as-inverse to the other scrollers (bunner, avenger, beatstreets)

**Status:** DONE 2026-09-04 (branch `codetheclassics-gl1-and-space-refactors`) — **beatstreets converted** (byte-identical); **bunner and avenger deliberately LEFT RAW** — their structure is a genuine poor fit for the camera-as-inverse abstraction (details below). soccer + beatstreets are the two clean showcases. Maintainer can override if uniformity is wanted (would need restructuring).
**Priority:** 4
**Difficulty:** 4

## Decision (2026-09-04, while maintainer away — for review)

Did **beatstreets** (clean, byte-identical). **Declined bunner and avenger** — not laziness, real
structural mismatches (same "clearer code over abstractions" call as the myriapod rotate framing):

- **bunner — `draw(offset_x, offset_y)` is DUAL-ROLE.** `Game.draw` passes the camera scroll
  `(0, -int(scroll_pos))` (`bunner.py:3305`), but the row→child nesting **reuses the same
  signature** to pass the parent's screen position — `child_obj.draw(self.x, self.y)`
  (`bunner.py:2484`). One `world_to_screen` `InvertibleFunction` can't cleanly replace that
  parameter without **conflating** the camera scroll with the parent→child translate (two
  different transforms sharing one signature). It also mutates `Actor.x/y` **in place**
  (`self.x += offset_x`, then restores) rather than assigning `self.pos`, so soccer's
  `self.pos = world_to_screen(vpos)` shape doesn't transfer. Forcing it would be less clear.
- **avenger — the "camera" isn't a translate of a camera placement.** The y-offset is a
  **derived, clamped** value: `top = max(-int(self.player.y / 4), -100)` (`avenger.py:4041`) —
  `player.y / 4`, not `-camera_y`. So `inverse(translate(b=camera))` would **misrepresent** the
  math (there is no camera position whose inverse is this). Plus a ½-scaled parallax second offset
  (`:4049`) and an x-wrap (`% LEVEL_WIDTH`). A poor fit; leaving it raw is honest.

**Recommendation:** keep bunner/avenger raw. If you want all four scrollers uniform for pedagogy,
each needs a small restructure (bunner: split the dual-role param; avenger: separate the true
camera-x from the derived parallax-y) — say the word and I'll do it, but I don't think it earns its
keep by your stated principles.

## BLUF

Replicate the **camera-as-inverse** pattern proven on soccer (`15bfd77a`) to the other three
scrolling games: build `world_to_screen = inverse(translate(b=camera))` from `gacalc.transforms`
and route the world→screen step through it instead of an ad-hoc `world ± offset`. Each conversion
must stay **byte-identical** (frame-180 differential trace, mvp container + Xvfb). The three differ
in difficulty, so each is verified independently:

- **beatstreets** — easy: `vpos` is a `gacalc` `Vector`, drawn as `vpos - scroll_offset` (exactly
  soccer's shape).
- **bunner** — care needed: the scroll is a **scalar Y-only** `scroll_pos`, applied as
  `world + (0, -scroll_pos)` via a mutate/restore in `MyActor.draw`, **plus** a row→child nesting
  level (`child.draw(self.x, self.y)`).
- **avenger** — care needed: the offset is **int** `offset_x`/`top`, applied as `world + offset`,
  **plus** a ½-scaled parallax copy and an x-wrap (`% LEVEL_WIDTH`).

## Context (read first)

- **The pattern to copy** — soccer (`ports/codetheclassics/vol1/soccer/soccer.py`, commit
  `15bfd77a`): `from gacalc.transforms import InvertibleFunction, inverse, translate`; in
  `Game.draw`, `world_to_screen = inverse(translate(b=offset))`; `MyActor.draw(world_to_screen)`
  does `self.pos = world_to_screen(self.vpos)`. Proven byte-identical (AE=0). Feasibility already
  established: `inverse(translate(b))(v) == v - b` bit-for-bit on `g2`/`g3` Vectors.
- **Per-game sites** are documented in `tasks/reference/coordinate-spaces-in-code-the-classics.md`
  › "Cameras as the inverse transformation":
  - `beatstreets.py:3127-3130` `self.pos = (vpos.x - offset.x, vpos.y - offset.y - height)` — note
    the extra `- height_above_ground` (the beat-em-up depth flatten), which is **not** part of the
    camera; keep it outside `world_to_screen`.
  - `bunner.py:2478-2487` `MyActor.draw` mutate/restore; `:3305` `obj.draw(0, -int(scroll_pos))`.
  - `avenger.py:2887-2897` `MyActor.draw(offset_x, offset_y)`; `:4058` `offset_x = -(player.x -
    camera_offset_x)`; `:4049` parallax `//2`.
- **Fidelity rule + harness:** behaviour-faithful; frame-180 differential trace per game.

## Per-game plan

1. **beatstreets** — like soccer. `world_to_screen = inverse(translate(b=scroll_offset))`;
   `self.pos = world_to_screen(self.vpos)` **then** subtract the `height_above_ground` on the y
   (the depth flatten stays a separate step; the shadow keeps omitting it). Convert the background
   tiles' `- scroll_offset` too. Keep the painter's-algorithm sort on `vpos.y` untouched.
2. **beatstreets scope:** like soccer, convert the real render path; leave any flag-gated debug on
   raw subtraction if present.
3. **bunner** — the scalar scroll is conceptually a camera at `(0, scroll_pos)`; render is its
   inverse. Build `world_to_screen = inverse(translate(b=Vector(0, int(scroll_pos))))` and apply
   `world_to_screen(Vector(obj.x, obj.y))`. **Watch the int() rounding** (bunner uses
   `int(scroll_pos)`) and the **row→child nesting** — decide whether the nesting composes through
   the same function or stays a separate additive step (it may be cleaner to leave the child
   nesting as-is and only convert the top-level world→screen). Verify byte-identical.
4. **avenger** — the offset is already the negated camera (`offset_x = -(player.x - …)`), applied
   by addition, so `screen = world + offset` = `translate(b=offset)(world)` (NOT its inverse). To
   express it as the course's *camera* inverse, use `world_to_screen =
   inverse(translate(b=Vector(player.x - camera_offset_x, -top)))` (the camera placement, whose
   inverse gives the current `+offset`) — **verify the signs against the frame trace.** The ½
   parallax is a *second* `world_to_screen` on a halved camera; the x-wrap stays as-is. This is the
   fiddliest — if the signs/parallax make it uglier than it's worth, note that and leave avenger on
   the raw form (soccer + beatstreets already demonstrate the pattern).

## Verification (per game)

- Frame-180 differential trace, original (HEAD) vs converted, mvp container + Xvfb — **AE = 0**.
- `ruff` + `ty` clean.
- Maintainer play-test (input/audio/gameplay the trace can't cover).

## Status table (fill in)

| Game | difficulty | converted | trace AE=0 | notes |
|---|---|---|---|---|
| beatstreets | easy | ✅ | ✅ | `world_to_screen` built in the core `ScrollHeightActor.draw` (offset stays threaded through the many subclass draws — less churn than changing 5 signatures); height flatten kept out of the camera as `- Vector(0, height)` so pos stays a Vector (ty-clean). ruff+ty clean, AE=0 |
| bunner | medium | ❌ left raw | n/a | dual-role `draw(offset_x, offset_y)` (camera scroll AND row→child nesting share the signature) + in-place `x/y` mutation — poor fit; see Decision |
| avenger | fiddly | ❌ left raw | n/a | "camera" y is derived/clamped (`player.y/4`), not a camera placement; + parallax + x-wrap — `inverse(translate)` would misrepresent it; see Decision |

## Related

- `tasks/archive/2026/09/05/codetheclassics-camera-as-inverse.md` — the soccer showcase (the pattern + feasibility).
- `tasks/reference/coordinate-spaces-in-code-the-classics.md` — the per-game camera sites.
