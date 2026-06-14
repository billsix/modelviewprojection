# mvpvisualization demos — pedagogy plan (what students should see)

**Status:** proposed — needs go-ahead
**Created:** 2026-06-15

## Goal

For each of the seven Cayley-graph teaching visualizations in
`src/modelviewprojection/mvpvisualization/`, lay out **what would most help a
student see and internalize** the one idea that demo embodies. The Cayley-graph
framing is the constant throughout: **nodes = coordinate spaces, directed edges =
invertible placement functions, "world→camera" = walking the placement arrows
backwards (the inverse), and "toward NDC" = the (non-invertible) projection tail.**
Each demo is supposed to add *exactly one* new idea on top of the previous.

This doc is a design plan, not yet implemented. Everything proposed below is
expressible with the existing engine (`cayley/cayleygraph.py` + `cayleyscene.py`:
`Scene`, `CoordinateFrame`, `Timeline`, `Animation`, `InverseOperations`,
`NonInvertibleTransformation`, the two imgui trees, the focus/anchor mechanism,
and the `StandardObjects` draw helpers). Where a proposal needs a genuinely new
mechanism, it's flagged **[new mechanism]**.

## The throughline (so each demo can lean on the previous)

```
coordinatesystems  → static explorer: graph + focus/anchor, no time
model              → animate ONE placement tree (build frames bottom-up)
pushmatrix         → branching: one parent, many children (push/pop)
modelview2d        → add the camera as a node; world→camera is the INVERSE path (flat 2D)
modelview          → same in full 3D, no projection squash yet
modelvieworthoprojection      → add the projection tail: ortho box → NDC
modelviewperspectiveprojection→ swap the box for a frustum: perspective squash → ortho → NDC
```

A student who watches them in this order should be able to say, by the end:
"placing an object and aiming the camera are the **same** operation run in opposite
directions, and projection is just one more edge that happens not to be
invertible." Every demo below should reinforce that one sentence.

---

## 1. coordinatesystems.py — *the explorer*

**Currently:** static; every space drawn at its full slider-driven transform;
focus buttons (NDC / Paddle1 / Square / Paddle2) re-anchor the view by walking
`path(world, space)` (against the arrows). No camera object, no timeline.

**What students should see:**
- **The active focus path lit up on the graph + in the scene.** When you focus
  "Square", overlay the chain `world → paddle1 → square` — both as a highlighted
  spine in the graph-tree panel *and* as a faint poly-line through the actual
  origins in 3D (world origin → paddle1 origin → square origin). The student
  literally sees "to view *from* the square, I undo these three hops."
- **Per-space axes that the student can toggle**, drawn at each node's origin in
  that node's orientation, so "coordinate system" stops being abstract — paddle1's
  x-axis visibly points along the paddle, the square's is rotated again.
- **A live readout of the composed transform** for the focused space: the ordered
  edge steps (`T(-9,1,0) · R_z(θ₁) · …`) printed in the panel, updating as sliders
  move — connecting the picture to the function composition.
- **"Show inverse" toggle:** when focused on a space, also show the *forward* path
  origin markers vs the *inverse* (anchoring) path, so the duality (place vs. view)
  is visible even though this demo has no camera yet.
- *Why:* this is the only no-time demo, so it should be the place a student
  *pokes* the graph and builds intuition before any animation.

## 2. model.py — *animate one placement tree*

**Currently:** animated build of paddle1 → square(nested) → paddle2, bottom-up
from world; axes bright while an edge interpolates then gray; static perspective;
clickable frame-tree to jump in time. No camera node.

**What students should see:**
- **The "moving frame" made unmistakable.** While an edge animates, draw the
  intermediate coordinate frame *traveling* (a ghost axis sliding/rotating from the
  parent's frame to the child's), not just brightening — so a student sees a
  translate as a *slide* and a rotate as a *turn*, step by step.
- **Step-synced labels.** As each step plays, show its label as a billboard at the
  moving frame (`T(0,0,-5)`, `R_z(30°)`, …) — reuse the new TeX billboard labels
  from the crossproduct work. The tree highlight + the in-scene label should name
  the *same* step.
- **"Build up the composition" caption:** a running line that accumulates the
  composed function as edges complete (`square = paddle1 · T · R · T · R`), so the
  nested square's final placement reads as a product the student watched form.
- **A replay-one-edge control:** click an edge in the tree to scrub just that
  edge's steps back and forth (not only jump-to-start), so a confusing rotate can
  be watched in isolation. **[new mechanism — per-edge scrub]**

## 3. pushmatrix.py — *branching / push-pop*

**Currently:** paddle1 → square_base (geometry-less) → four squares fanned at
0/90/180/270°; square_base keeps a persistent grayed axis marking the fan's pivot;
single placement tree.

**What students should see:**
- **The push/pop story told explicitly.** As each child square builds, show a
  small "stack" widget (or in-scene callout): `push(square_base)` → apply child
  edge → draw → `pop()` back to the grayed pivot axis. The grayed axis is already
  the right anchor; pair it with the word "pop" each time a child finishes so the
  student connects the picture to `fn_stack.push/pop`.
- **All four children share one parent — show it.** Draw the four child edges
  emanating from the *same* grayed `square_base` axis simultaneously (faint), so
  "siblings off one frame" is visual, not just sequential.
- **Side-by-side with the matrix-stack code.** A panel showing the equivalent
  `glPushMatrix / glPopMatrix` (or `fn_stack.push/pop`) lines, highlighting the
  line that corresponds to the current animation step — the demo's whole reason to
  exist is "this fan == push/pop".
- **Contrast toggle:** "what if we *didn't* pop?" — replay the fan accumulating
  transforms (each square placed relative to the previous instead of the base) so
  the student sees the bug push/pop prevents. **[new mechanism — alt choreography]**

## 4. modelview2d.py — *introduce the camera as a node (flat 2D)*

**Currently:** flat ortho head-on; square has no z; camera node translate-only;
`world→camera` inverse animated; `Camera→NDC` a single scale; NDC-zoom toggle.

**What students should see:**
- **The pivotal reveal: place the camera, then run the arrow backwards.** First
  animate the camera being *placed* like any object (forward edge, with its axis),
  then visibly *reverse* that edge and apply the inverse to the whole world — the
  classic "the camera doesn't move, the world moves opposite" moment. The two trees
  (placement vs toward-NDC) should highlight the *same* edge, one forward, one
  inverted.
- **Because it's 2D, exploit the clarity:** keep everything in the plane and make
  the inverse a literal slide of the world under a fixed camera crosshair at
  screen center — no 3D ambiguity to distract from "world→camera = inverse".
- **NDC as a destination, not a toggle:** animate the `Camera→NDC` scale as a
  morph from world units into the [-1,1] square (draw the NDC square the whole
  time), so the student sees the scene *shrink into* clip space rather than a
  binary zoom flip.
- *Why 2D first:* it's the cheapest place to teach the single hardest idea
  (world→camera is the inverse), with no perspective to muddy it.

## 5. modelview.py — *the same idea in full 3D, no squash*

**Currently:** full 3D placement + camera placed as object (axis + NDC cube, no
frustum) + animated 3-step `world→camera` inverse; static perspective; world axis
revealed in timed windows.

**What students should see:**
- **The 3-step inverse, named and slow.** The camera edge is `T · R_y · R_x`; its
  inverse is `R_x⁻¹ · R_y⁻¹ · T⁻¹`. Animate each inverse step applied to the world
  with its label, and show the order *reversing* relative to the forward placement
  (highlight forward steps top-down, inverse steps bottom-up in the trees) — this
  is the demo that should make "inverse = reverse order + invert each" concrete.
- **Keep the camera's own axes/NDC cube on screen** during the unwind so the
  student sees the world rotating into alignment with the camera's frame (the cube
  ending axis-aligned with the view).
- **A "ride the camera" focus** that snaps the orbit to look *down* the camera's
  -z after the unwind, confirming the world is now expressed in camera space.
- *Why:* this is the bridge — same lesson as modelview2d but in 3D, deliberately
  *without* projection so the only new thing is "the inverse is 3 steps now".

## 6. modelvieworthoprojection.py — *add the projection tail (the easy one)*

**Currently:** modelview.py + a hard-coded ortho box (half-size 5, near -0.5,
far -15.5) + a 2-step GPU squash (`T-Center`, `Scale`) with a 10s dwell; editable
virtual camera (px/py/pz, rot); focus buttons.

**What students should see:**
- **The view volume as a real object.** Draw the rectangular prism in world space,
  clip/shade geometry that falls outside it, and then animate the box → NDC cube
  morph so the student sees the box *becoming* clip space (constant cross-section →
  no foreshortening). The 10s dwell is already there to watch it.
- **"Center then scale" shown as two distinct moves:** first translate the box so
  its center sits at the origin, *pause*, then scale to ±1 — two labeled steps, not
  one blur.
- **Editable volume [enhancement]:** expose the box half-size/near/far as sliders
  (today they're hard-coded) so the student can shrink the box and watch geometry
  clip and the NDC mapping rescale — the ortho analogue of the perspective demo's
  frustum sliders.
- *Why ortho before perspective:* it isolates "projection = map a view volume to
  the NDC cube" with the *simplest possible* volume (a box, no squash), so
  perspective later is just "same idea, harder volume".

## 7. modelviewperspectiveprojection.py — *the full stack*

**Currently:** the complete pipeline — placement, 3-step inverse, camera drawn with
its frustum, GPU perspective squash (`Squash X`, `Squash Y`) → ortho (`T-Center`,
`Scale`) → NDC; editable camera + frustum (FOV/aspect/near/far); focus incl.
Camera; both trees.

**What students should see:**
- **The frustum → rectangular-prism squash as the headline.** Draw the frustum,
  then animate it deforming into the ortho box (near face stays, far face shrinks
  in), with the off-axis lines straightening — *this* is where foreshortening comes
  from. Then hand off to the ortho box→NDC morph the student already learned in
  demo 6, so the perspective demo visibly *reuses* the ortho tail.
- **One object tracked all the way through.** Pick the square and draw its outline
  persistently from modelspace → world → camera → frustum-squash → NDC, so a
  student can follow a single thing across every edge of the whole graph in one
  run. **[new mechanism — single-object "trace" overlay]**
- **Frustum sliders with immediate clipping feedback:** as FOV/near/far change,
  recolor what now falls outside the frustum and re-run just the squash, so the
  parameters feel causal.
- **Capstone caption:** the full composed path `modelspace → … → NDC` printed as
  one product, with the non-invertible tail visually distinguished (dashed edges)
  from the invertible placement/inverse edges — closing the course's thesis that
  projection is "just one more edge, the one you can't undo".

---

## Cross-cutting (applies to several, do once in the engine)

- **In-scene step labels via the TeX billboards** (from
  `tasks/.../crossproduct-tex-billboard-labels.md`): every animating step should be
  nameable in the 3D view, not only in the tree. Build it into `cayley_gl` /
  `StandardObjects` so all demos get it.
- **Tree↔scene highlight sync:** the currently-animating step should glow in the
  tree *and* on the moving frame, always the same step. Some of this exists
  (tree highlight); extend it into the scene.
- **Per-edge scrub** (drag a step 0→1) as a shared control — turns every demo into
  something a student can interrogate, not just watch.
- **Consistent "forward vs inverse" coloring** across all demos (placement arrows
  one color, the world→camera inverse another, the non-invertible projection tail
  dashed) so the graph reads the same everywhere.

## Sequencing / suggested order of work

1. Land the shared cross-cutting pieces first (in-scene step labels + tree↔scene
   sync + forward/inverse coloring) — they lift every demo.
2. Then per-demo, cheapest-first: coordinatesystems (focus-path overlay) →
   model (moving frame + labels) → pushmatrix (push/pop widget) → modelview2d
   (camera place-then-reverse) → modelview (named 3-step inverse) →
   ortho (view-volume object + sliders) → perspective (frustum squash + trace).

## Open questions

- Per-demo: keep each visualization *minimal* (one idea) or let the later ones
  accumulate the earlier overlays? (Recommend: minimal, with the shared overlays
  opt-in via a checkbox.)
- Which of the **[new mechanism]** items are worth the engine work vs. nice-to-have.
- Whether to add a short on-screen "what to notice" caption per demo (teacher voice)
  or keep it purely visual.
