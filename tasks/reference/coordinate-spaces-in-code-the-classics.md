# Coordinate spaces in the Code-the-Classics games — one flat pixel space, one real projection

**Reference document** (never archived; update in place). Author: William Emerison Six
<billsix@gmail.com>, 2026-09-04. Method: five parallel `file:line`-anchored reads of all 10
games' *game logic* (not the inlined engine), the two surprising findings verified firsthand.

## BLUF

**Nine of the ten Code-the-Classics games live in a single global 2-D pixel space** — the
rich, composed, invertible multi-space model the course teaches (modelspace → world → camera →
NDC, nested spaces, a push/pop `FunctionStack`, `InvertibleFunction` edges, a "Cayley graph" of
spaces) has **essentially no analogue** in them. Where a game scrolls, its "camera" is a
**single additive translation** applied at draw time (`screen = world − camera_offset`) — which
*is* the degenerate, one-edge form of the book's "render through the **inverse** of the camera's
placement," just always a pure translation, never composed, never run backwards. The **one true
exception is `leadingedge`**, the pseudo-3-D racer, which implements a genuine 3-D world →
2-D screen **perspective projection** with a real perspective divide (`x/z`, `y/z`) through a
positioned camera. Two games contain a genuinely *composed* transform reaching screen space
(`myriapod`'s rotate-then-translate segment placement; `leadingedge`'s projection); the rest are
identity or a fixed affine grid overlay. **None** of them uses the course's transform machinery
(`compose`, `inverse`, `translate`, `FunctionStack`) — every transform is hand-inlined and
forward-only.

The teaching value of this doc: it maps each game onto the course's framework so a reader can
see **where the book's abstractions do and don't show up in real game code**, and it is the
evidence base behind two follow-on tasks (`tasks/pgzero-gl-boing-gl14.md` — a GL-1.x vs 3.3
study; and a camera-as-`inverse(translate())` refactor, feasibility task
`tasks/codetheclassics-camera-as-inverse.md`).

## Why this doc exists (the question)

The course (`CLAUDE.md` › Central abstraction) is built on **many coordinate spaces connected by
invertible functions**: nodes are spaces (modelspace, world, camera, NDC, screen, spaces nested
relative to other spaces), edges are `InvertibleFunction`s, and you move between any two by
`compose`-ing the edge functions and `inverse`-ing any edge traversed against its arrow. Camera
placement is the *same* operation as object placement, so the world↔camera edge is reversible —
that reversibility is the pedagogical hinge (demo07–13, ch16, ch19). The question this doc
answers: **do the games use anything like that, or do they collapse to one global pixel space?**

## The coordinate systems that DO exist (even in the "flat" games)

"One global pixel space" describes where **entities are placed**. It does not mean there are no
other coordinate systems — a few are unavoidable, and they matter for the GL-1.x-vs-3.3 study
(`boing_gl1.py`). Per sprite, from bottom to top:

1. **Texture / UV space** — each PNG's own texel grid, sampled `u0,v0 .. u1,v1` in `draw_image`
   (whole image, or a sub-rect for atlases/tilesets). A real per-image coordinate system.
2. **A unit-quad "model space" `[0,1]²`** — every sprite is drawn from one reusable unit quad,
   then `scale(w,h)` + `translate(tx,ty)` map it onto the pixel rectangle. Visible in both
   renderers: 3.3 core `model = _translate(tx,ty) @ _scale(w,h)` (`boing.py:993`); GL 1.x
   `glTranslatef(tx,ty); glScalef(w,h)` + `glVertex2f(0..1)` (`renderer_gl1.py:104-115`). **This
   is OpenGL plumbing, not a space the game reasons in** — the game is pixel space throughout;
   the unit quad is just "hand OpenGL geometry + a transform."
3. **NDC `[-1,1]`** — the space OpenGL genuinely *forces* (it always rasterizes there).
   `ortho_pixels` (3.3, `boing.py:832-840`) / `glOrtho(0,W,H,0,…)` (GL 1.x,
   `renderer_gl1.py:74-76`) is exactly the "convert my pixel space to OpenGL's required NDC"
   edge. So two OpenGL-mandated layers (unit-quad scale, pixel→NDC ortho) sit **under** a game
   that thinks purely in pixels.
4. **Anchor space** — pgzero's per-sprite anchor (center / top-left / a named anchor) placed at
   the entity's position; boing's `blit(name,x,y)` (top-left) vs `draw_sprite(name,cx,cy)`
   (center) are exactly this choice. The anchor placement is a modelspace→world translation.
5. **Placement space** — the global space entities live in: **screen pixels** (single-screen
   games) or **world pixels** (scrollers), top-left origin, y-down.
6. …plus, for scrollers, **world space = pixel space + a camera offset** (below).

The point the doc draws: these spaces exist, but the **edges between them are always the
simplest possible** — a texture UV map, a fixed scale, a translate — applied one-way, never a
rotation (except two games), never a perspective (except leadingedge), never a composed
multi-hop path, never an inverse. A degenerate slice of the course's general graph.

## Per-game summary

| Game | vol | Placement space | Camera / scroll | Grid space | Rotation | Composed transform? | Distinct spaces |
|---|---|---|---|---|---|---|---|
| **boing** | 1 | screen px (identity — pos *is* pixels) | none | none | none | no | **1** |
| **cavern** | 1 | screen px | none | static tile grid, affine `grid*25+{50,0}`, inverted both ways | none | no | 2 |
| **myriapod** | 1 | screen px (player) / grid cells (segments, rocks) | none | tile grid `cell*32+{32,16}`, `pos2cell`/`cell2pos` | **yes — 2×2 matrix**, per segment | **yes** — rotate(in_edge) ∘ cell2pos → screen | **3** |
| **bunner** | 1 | world px (∞ vertical strip) | +additive **scalar** (Y only), `−scroll_pos` | row/lane index `×ROW_HEIGHT(40)` | none | shallow — row→child additive nesting | 4 (grid, world, row-local, screen) |
| **soccer** | 1 | world px (`vpos`, 1000×1400) | +additive **2-D** `vpos−offset`, ball-follow, bounds-clamped | none | none | no | 2 |
| **kinetix** | 2 | screen px | none | brick grid, affine, **inverted at collide** | velocity vector in place (`_turn`, multiball) | no | 2 |
| **eggzy** | 2 | screen px | none | tile grid `×25` (scale only, forward) | none | no | 2 |
| **avenger** | 2 | world px (x wraps `%LEVEL_W`) | +additive **2-D** `world+offset`, +½ parallax | none | none | no | 2 |
| **beatstreets** | 2 | world px (`vpos`) | +additive **2-D** `vpos−scroll` + height→y flatten | none | none | no (height is a scalar flatten, not a 3rd axis) | 2 (+ height scalar) |
| **leadingedge** | 2 | **3-D world** `g3.Vector(x,y,z)`, z = track depth | **real 3-D camera** + **perspective divide** | z→piece index `−int(z/SPACING)` | (sprite art picked by `x/z` angle) | **YES — genuine `world→camera→perspective`** | **≥3 (model/track, camera, screen)** |

## Cameras as the inverse transformation — where the book's hinge appears

This is the most direct correspondence between the course and the games. The book: rendering
applies the **inverse** of the camera's placement to bring world-space into view. The four
scrollers do exactly that, in its simplest form.

- **The move:** placing the camera at `C` in the world is `translate(C)`; drawing needs
  world→screen, which is `translate(C)⁻¹ = translate(−C)` — i.e. **subtract the camera**. So
  every scroller's draw step, `screen = world − camera_offset`, *is* `inverse(translate(C))`
  collapsed to a pure translation.
  - `bunner.py:3305` — `obj.draw(0, -int(self.scroll_pos))` → `MyActor.draw` adds the offset
    (`bunner.py:2478-2487`): `screen_y = world_y − scroll_pos` (Y-only scalar).
  - `soccer.py:2608-2612` — `self.pos = self.vpos − offset`, with `offset` the ball-following,
    bounds-clamped 2-D camera (`soccer.py:3521-3526`).
  - `avenger.py:2887-2897` + `:4058` — `screen = world + offset_x` where
    `offset_x = −(player.x − player_camera_offset_x)` (the minus sign *is* the inverse), plus a
    ½-scaled copy of the same offset for parallax backgrounds (`avenger.py:4049`).
  - `beatstreets.py:3127-3130` + `:5583` — `screen = vpos − scroll_offset`.

- **The games only ever use the inverse direction.** None of the four inverts the offset *the
  other way* (screen→world) — there is no mouse-picking or screen-coordinate reconstruction;
  input is keyboard/pad only, and "is this on screen?" is answered by comparing world
  coordinates against `scroll_pos ± screen extents` (e.g. `bunner.py:3232`, `:2642`;
  `soccer.py:2658`), i.e. the offset used *forward*, not a true inverse. So the games exercise
  exactly one edge of the invertible pair — the camera-placement inverse — and never need the
  forward reconstruction the general machinery would give them for free.

- **Contrast with the course.** The book's camera edge can carry **rotation**, is **composed**
  with other edges (model→world→camera), and is inverted by the general `inverse()` on an
  `InvertibleFunction`. The games' camera is always a **pure translation**, inverted by
  negation, composed with nothing, applied by mutating-then-restoring `x`/`y` (or subtracting a
  `Vector`) inside `Actor.draw`. Same concept — "render through the inverse of the camera's
  placement" — stripped to its degenerate one-edge case. **This is the teachable bridge**, and
  the reason for the feasibility task `tasks/codetheclassics-camera-as-inverse.md` (rewriting
  `screen = world − camera` as an explicit `inverse(translate(camera))`).

## Grid / tile spaces — a real second space, but a fixed affine

Five games carry a discrete grid distinct from pixels, related by a **constant** scale-plus-offset
(never varying, so not a camera): `cavern` (`grid*25+{50,0}`, `cavern.py:2023-2024`/`:2685-2689`),
`myriapod` (`cell*32+{32,16}`, `pos2cell`/`cell2pos`, `myriapod.py:1960-1970`), `kinetix` (brick
grid, `kinetix.py:3627`, **inverted** at collision `:3680-3689`), `eggzy` (`×25`, forward-only,
`eggzy.py:4075-4076`), and `bunner`'s discrete row/lane index (`×ROW_HEIGHT`, `bunner.py:3294`).
These are genuine invertible index↔pixel spaces and several *are* used both ways (`pos2cell` for
collision, `cell2pos` for drawing) — but each is a fixed per-axis affine, not a composed or moving
transform.

## The two genuine composed transforms (the exceptions)

### 1. myriapod — a rotate-then-translate reaching screen space (verified firsthand)

A myriapod Segment is positioned in a **cell-local frame**, rotated into its actual orientation
by a literal 2×2 rotation matrix chosen by the entry edge, then translated to the cell's pixel
centre (`myriapod.py:2592-2604`):

```python
rotation_matrix: list[int] = [
    [1, 0, 0, 1], [0, -1, 1, 0], [-1, 0, 0, -1], [0, 1, -1, 0],
][self.in_edge]
offset_x, offset_y = (
    offset_x * rotation_matrix[0] + offset_y * rotation_matrix[1],
    offset_x * rotation_matrix[2] + offset_y * rotation_matrix[3],
)
self.pos = cell2pos(self.cell_x, self.cell_y, offset_x, offset_y)  # translate to screen
```

That is a real composed transform — **segment-local offset → rotate(in_edge) → cell frame →
translate(cell2pos) → screen pixels** — the one place across the nine flat games that multiplies
a rotation matrix and composes it with a translation to reach the screen.

> **Update (2026-09-04):** the rotate half is now expressed the course's way — the four `in_edge`
> rotations are `offset · e_12^in_edge`, **multiplication by the unit pseudoscalar** `e_12` (the
> exact GA-native 90° rotation; `e_12`'s components are ±1, so no `sin`/`cos`). Byte-identical to
> the old matrix; see `tasks/codetheclassics-myriapod-rotation-via-pseudoscalar.md`. The `cell2pos`
> translate stays hand-rolled (a plain integer offset).

(Note: `kinetix`'s `_turn = plane_rotation(e_1, e_2)` at
`kinetix.py:2674`/`:3367` rotates a *velocity vector in place* for multiball spread — a rotation
*within* the one space, **not** a change of basis into a local frame.)

### 2. leadingedge — a genuine 3-D → 2-D perspective projection (the real exception; verified firsthand)

`leadingedge` is the set's lone true multi-space game. The world is honestly 3-D — cars carry
`pos: g3.Vector(x, y, z)` where **z is distance down the track** (`leadingedge.py:3136-3148`),
and the track is a list of `TrackPiece` storing per-piece **deltas** from the previous piece
(`:3108-3127`). The projection is a textbook perspective divide, not a scanline table
(`leadingedge.py:4221-4245`, verified):

```python
newpoint: g3.Vector = point_v3 - self.camera        # world → camera space (a translation)
if newpoint.z > clipping_plane:                       # near-plane clip
    return ...
point_v2 = g2.Vector(
    (newpoint.x / newpoint.z) + HALF_WIDTH,           # perspective divide X
    (newpoint.y / newpoint.z) + HALF_HEIGHT,          # perspective divide Y
)
return point_v2, w / -newpoint.z, h / -newpoint.z     # sprite size shrinks with depth
```

There is a real positioned camera (`g3.Vector(0, 400, 0)`, follows the player's x/z at a fixed
distance, `:4049-4053`), a near-clip plane (`CLIPPING_PLANE=-0.25`, `:2738`), an implicit
vanishing point at screen centre (the `+HALF_WIDTH/HALF_HEIGHT` recentre), depth-scaled sprites
(`size / -z`), and painter's-algorithm depth sorting in z (no depth buffer, `:4723`/`:4727-4728`).
Road curvature is layered *on top* as a **double-accumulated world-space offset** (`offset_delta`
sums slope, `offset` sums `offset_delta` → a parabolic bend, `:4333-4341`) applied *before*
projection, so the horizontal displacement is itself depth-scaled — the standard pseudo-3-D
curved-road technique over an honest projection.

**Relation to the course:** it matches the *spirit* (distinct spaces — track/model, camera,
screen — joined by a transform; camera placement as a translation of world points, `point −
camera`) but **not the machinery**: it is a single hand-written forward `transform()` closure on
`gacalc.g3.Vector`, never `compose`d, and — critically — **never inverted** (all gameplay stays
in track space so the projection never runs backwards; `:3245`, `:3499-3502`, `:3541`). The
world→camera step (`− self.camera`) is exactly the book's camera-inverse-as-translation and
*could* be written `inverse(translate(self.camera))`; the perspective divide discards z and is
genuinely non-invertible. So leadingedge is where the course's perspective chapters (ch19+) have
a real analogue — and, tellingly, where the ad-hoc version stops short of the invertible,
composable formulation the course generalises to.

## What's absent everywhere (vs the course)

- **No `InvertibleFunction` / `compose` / `inverse`** — every transform is hand-inlined
  arithmetic (a subtraction, an affine, a 2×2 matrix, a divide).
- **No `FunctionStack` / matrix-stack push-pop** — nothing pushes a transform, draws children
  under it, and pops. `bunner`'s row→child nesting (`child_obj.draw(self.x, self.y)`,
  `bunner.py:2483-2484`) is the closest thing: one extra additive level, applied by mutating
  `x`/`y`, not a stack.
- **No composed multi-hop paths and (almost) no inverses** — transforms are one-way. The only
  bidirectional uses are the fixed grid↔pixel affines (`pos2cell`/`cell2pos`, brick-collide),
  not a camera or a general edge.
- **No rotation in placement** except myriapod's segment matrix; `kinetix`'s rotor and various
  direction vectors rotate *within* the one space.

## Teaching takeaway

These ports are, in aggregate, the **flat baseline the course's abstraction generalises from**:
real games that ship in a single 2-D pixel space and reach the screen with the cheapest possible
transforms. The course's value proposition — many spaces, composable invertible edges, a stack —
is exactly what these games *don't* need until the world becomes 3-D. `leadingedge` is where that
tipping point is crossed and a real camera + perspective projection appears — still hand-rolled
and one-way, which is precisely the gap the course's `InvertibleFunction`/Cayley-graph
formulation fills. The camera-as-inverse hinge (ch16/ch19) shows up in degenerate form in every
scroller (`screen = world − camera`), which is why it is the natural place to demonstrate the
book's machinery inside a real game (see the feasibility task).

## Related

- `tasks/reference/pgzero-gl-design-for-a-personal-learning-library.md` — the shim's design and
  per-game usage slices (the engine these games sit on).
- `tasks/pgzero-gl-boing-gl14.md` — the GL 1.x vs 3.3 boing study (uses the model/texture/NDC
  space section above).
- Three feasibility tasks this research spawned, each "build on existing book/gacalc functions,
  study first, byte-identical" (maintainer, 2026-09-04) — outcomes on branch
  `codetheclassics-gl1-and-space-refactors`:
  - `tasks/codetheclassics-camera-as-inverse.md` — **IMPLEMENTED (soccer showcase)**: `screen =
    world − camera` → `inverse(translate(camera))`, frame-180 AE=0. Replication to the other
    scrollers left as a maintainer decision.
  - `tasks/codetheclassics-leadingedge-projection-functions.md` — **IMPLEMENTED**: world→camera →
    `inverse(translate())` in `g3`, perspective divide left hand-rolled, frame-180 AE=0.
  - `tasks/codetheclassics-myriapod-rotation-via-pseudoscalar.md` — **IMPLEMENTED**: the four
    `in_edge` rotations are now `offset · e_12^in_edge` — multiplication by the unit pseudoscalar,
    the exact GA-native 90° rotation (no `sin`/`cos`), frame-180 AE=0. (Supersedes
    `...-myriapod-rotation-as-functions.md`, which wrongly declined a `rotate∘translate` framing
    before the pseudoscalar answer was spotted.)
- `CLAUDE.md` › Central abstraction, pedagogical arc — the course's multi-space model this doc
  contrasts against.
- The 10 game files: `ports/codetheclassics/{vol1,vol2}/<game>/<game>.py`.
