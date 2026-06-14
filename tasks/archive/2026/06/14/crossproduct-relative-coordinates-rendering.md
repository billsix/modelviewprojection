# Cross-product demo relative-coordinate plane rendering

**Status:** complete
**Completed:** 2026-06-14

Resolved 2026-06-14 (fresh-eyes pass). The forward-phase relative-coordinate
graph-paper plane and its basis vectors now render correctly. Root causes and
fixes, all in `src/modelviewprojection/mathdemos/crossproduct.py`
(`main()` -> `draw_scene`):

1. **Ground frame** — each forward relative ground/basis is drawn at the uniform
   transform `o = coords @ edge_M(r_phase, t) @ edge_M(r_phase_inv, 1.0)`: it
   starts tilted in the relative frame (shown immediately, distinct from the world
   grid) and rotates onto the world axis-plane as the phase animates.
2. **Basis double-transform** — `draw_relative_basis` was projecting the input
   vector into world space and then drawing it *under* `o` (already rotated),
   rotating it twice. Fixed to draw the two in-plane MODEL-space unit axes under
   `o` (like the original's `draw_axis`); `o`'s in-plane axes already ARE the
   projected-input + its 90deg.
3. **Prior-rotation special cases** — phases 2/3 baked in the prior rotors
   (`@ r_z`, `@ r_y @ r_z`), over-rotating the plane/basis out of their axis-plane.
   Removed: all three phases use the same `coords @ r_phase(t) @ r_phase_inv(1)`
   form. The original's interleaved `do_*`/`draw_*` order means `draw_second` never
   sees `R_z` and `draw_third` never sees `R_y`/`R_z`.
4. **Phase-3 plane leaking into the next phase** — the teardown relied on a fragile
   `ratio > 0.9999` flag-clear plus coincidence-masking (phases 1/2 end on the
   xy/zx planes which the world ground hides; phase 3 ends on the bare yz plane with
   no world ground, so any residue showed). Each forward block is now gated on its
   step window (`not reached(<next step>)`), so it disappears deterministically when
   the next phase begins.

Verified numerically (rotor matrices vs the original's atan2 rotations match;
basis vectors unit and in-plane) and visually by Bill.

---

Original handoff notes preserved below for history.

**Status (at handoff): NOT WORKING — needs fresh eyes (handoff 2026-06-14).** Bill (the author)
is frustrated after many failed iterations. The relative-coordinate **graph-paper
plane** (and its basis vectors) for the FORWARD phases (rotate_z, rotate_y,
rotate_x) is still not drawn correctly. Bill asked to reset context and re-approach
with fresh eyes. **Do not trust the prior assistant's mental model below — it kept
being wrong. Start by STUDYING THE ORIGINAL and the UNDO phases, which Bill says
are correct.**

File: `src/modelviewprojection/mathdemos/crossproduct.py`, inside `main()` ->
`draw_scene`. Relevant pieces:
- `draw_relative_ground(model_M, *, xy/yz/zx)` — draws the graph paper (lighter
  color `_REL_GROUND`, with `glPolygonOffset` to win the depth tie).
- `draw_relative_basis(model_M, prior_M, drop, src, c_red, c_green)` — draws the
  in-plane unit basis (red = src projected onto the plane; green = 90deg = normal x
  red).
- The forward blocks: `if g.draw_first_relative_coordinates:` (rotate_z, x-y),
  `draw_second` (rotate_y, z-x), `draw_third` (rotate_x, y-z).  These are the ones
  Bill keeps rejecting.
- The UNDO blocks (Bill says THESE LOOK RIGHT — copy their approach): inside
  `if reached(StepNumber.rotate_x/y/z):`, the
  `if g.draw_undo_rotate_x/y/z_relative_coordinates and not reached(show_plane):`
  branches call `draw_ground(plane)` + `relative_axes()` at the **current
  accumulated `model_M`** (the full scene rotation).

## The reference that is CORRECT (per Bill)

1. The **undo phases** in THIS file (the `draw_undo_rotate_*` branches): they draw
   `draw_ground(plane)` + `relative_axes()` at the live `model_M` (the scene's full
   rotation), so the plane is rotated to match the rotated scene.
2. The **ORIGINAL demo** this was ported from:
   `/billopt/multivariate-math/multivariate-math/src/crossproduct/crossproduct.py`
   (+ `renderer.py`).  Look at its `draw_first/second/third_relative_coordinates`
   render blocks and `do_draw_axis`/`do_draw_ground` in renderer.py.  NOTE the
   original has a bug worth understanding: `draw_third` compares
   `g.step_number == StepNumber.show_triangle.value` (enum == int -> always False),
   so its `ratio` is always 1.0.  The original draws the relative frame at
   `model_M @ rotate_<axis>(+angle)` (the inverse of the forward rotate), i.e. the
   scene frame BEFORE the current phase's rotation.

## Bill's complaints, in order (PRESERVE — do not delete)

1. "when I select 'draw relative coordinates', I'd expect immediately, even though
   the transformation hasn't started, the relative graph paper and axes shown. Then
   during the animation shown, and only upon starting the next phase disappear.
   Currently they only show up during the animation, not before the stage begins."
2. "I guess I'm fine with it disappearing at the end though."
3. "the relative coordinates are supposed to show where the vectors will end up at
   the end of the frame! not be animated and move with the other data!"
4. "Look at the original demo... It uses the colors of the unit vectors. It projects
   the input vectors, or derived vectors, to the plane that is about to be rotated,
   makes them unit length."
5. "on the first one, vector a gets projected to the xy plane. That looks good. But
   the second vector, that is green, should be that projection rotated by 90 degrees
   in the xy plane! Not whatever it currently is."
6. "the color of these normalized vectors should match the reference frame. If we
   are rotating on the plane that has blue and red for the unit vectors, the
   relative vectors should be blue and red, not one being green. Now make those
   vectors rotate with the animation, and also draw out the whole ground plane, as
   was done in the original animation."
7. "on the first phase or two, the graph paper isn't showing up until the animation
   starts. on later phases, it's shown at the same time as the relative coordinate
   vectors."
8. "you are not drawing the relative plane correctly. ... You draw the ground
   rotated [in the last/undo phases], so that it matches with the rotated vectors.
   You should do that for the first few phases as well. The way you just did it,
   it's showing the 'new' coordinate system as the plane as it is in world space.
   learn from what you do on the last few phases, and modify the first 3 rotations
   to draw the ground the same way."
9. "still not working. holy smokes. you are not drawing the relative plane
   correctly." (current)

## What the prior assistant tried (all rejected) — so DON'T just repeat these

- Static destination frame (full rotors at(1)) — rejected ("animated/wrong").
- Projecting the vectors onto the world coordinate plane, normalized — colors/90deg
  wrong, then "world space" wrong.
- Basis: red = source projected onto plane (unit), green = normal x red (90deg).
  Bill liked the BASIS VECTORS at one point ("looking good"), colors per plane
  (x-y: red+green, z-x: red+blue, y-z: green+blue). The PLANE is the problem.
- Most recent attempt: draw ground+basis at `O_full = coords @ R_phase.at(t) @
  R_prior` (the full forward scene rotation), projecting the INPUT vector onto the
  standard plane in that frame. Verified coplanar (basis lies in ground plane) and
  math checks pass — but Bill says it's STILL not drawing the relative plane
  correctly. So either O_full is the wrong frame, or the plane/normal/projection is
  wrong, or the grid orientation is off.

## Suggested fresh approach

1. **Actually read and trace the ORIGINAL's `draw_first/second/third_relative_
   coordinates` render math line by line** (multivariate-math path above), including
   what `model_M` is at each point and the `+angle` extra rotate.  Replicate THAT
   transform exactly for the forward phases here, rather than reinventing.
2. Cross-check against the UNDO branches in this file (they're agreed-correct):
   match how they pick the model matrix and which plane/axes they draw.
3. The likely crux: WHICH frame the relative plane lives in (world rotation plane vs
   the scene's rotated coordinate plane), and that for phases 2-3 the prior rotation
   (R_z, then R_y) must be included so the grid is rotated to match the scene — but
   the projected/aligned vector (a', b'') lives in a WORLD coordinate plane, which
   created a tension the prior assistant never resolved. Resolve that tension by
   following the original exactly, not by reasoning from scratch.
4. It is DISPLAY-ONLY: Bill verifies visually. Make a hypothesis, implement, ask
   Bill to look. Don't over-spin headless verifications.

## Env / RAM note (2026-06-14)

Bill flagged high RAM. The prior assistant removed the `gacalc` and
`tex-expression-to-png` podman images and a stuck container; only
`modelviewprojection` (5.83 GB) and `fedora:44` remain.  Verify changes in the
`modelviewprojection` container (nested podman works here):
`podman run --rm --entrypoint /bin/bash -v "$(pwd)":/mvp/:Z modelviewprojection -c
'source /venv/bin/activate; cd /mvp; uv pip install --no-deps --no-index
--no-build-isolation -e . --python $(which python); <cmd>'`.  Don't rebuild images
you don't need.

## Also queued (separate, not this bug)

`tasks/crossproduct-tex-billboard-labels.md` — TeX billboard vector labels via
texExpToPng; decisions locked, runtime-conditional generation; texExpToPng already
has new `--bg/--fg` flags (staged in /billopt/texExpToPng). Not started.
