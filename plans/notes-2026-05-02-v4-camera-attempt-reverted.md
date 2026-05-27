# Note: v4 ports walk-around camera attempt — reverted 2026-05-02

**Status:** all changes thrown away by Bill via `git checkout`.  This
note records what I did so the next attempt can avoid the same
mistakes.

## What I attempted

Three combined plans across `/mvp/ports/openglsuperbiblev4/`:

1. **`ports-imgui-menubar.md`** — confirmed by audit that the prior
   "done" status was wrong: 0 of 102 ports actually imported `_common`,
   despite the plan claiming a 92-file migration had landed.  So I
   re-ran the foundation: every non-stub port got
   `import _common`, `_common.init_imgui`, `_common.WindowState`,
   `_common.draw_menubar` (File→Quit, View→Fullscreen), and
   `glfw.create_window(*_common.resolve_default_window_size(), …)`.

2. **`ports-walkaround-camera.md`** — replaced three patterns with
   `_common.Camera`:
   - **Pattern A** (chapt03/04/05/06/08/09/10/11): `x_rot`/`y_rot`
     globals + `glRotatef(x_rot, …) / glRotatef(y_rot, …)` in
     `render_scene` + `handle_special_keys`.
   - **Pattern B** (chapt13/14/15/16/17/18): `camera_pos = [X, Y, Z, 1]`
     + `gluLookAt(camera_pos[0..2], 0,0,0, 0,1,0)` + KEY_X/Y/Z bindings.
   - **Pattern C** (chapt04/05/06/08/09/11 sphereworld + chapt19):
     `camera_x/y/z/yaw` + `apply_camera_transform` + `handle_camera_keys`.

3. **`ports-keyboard-standardization.md`** — implicit byproduct: every
   migrated port used `_common.update_camera()` (WASD walk, QE up/down,
   arrows look, mouse drag, scroll).

49 ports got a `_common.Camera`.  91 got the menubar foundation.
All 102 files compiled.

## What went wrong

### Bug 1 — regex deleted main()

The Phase B regex used `(?:\s+[^\n]*\n)+` to match the body of
`handle_special_keys` / `handle_camera_keys` for deletion.  Because
`\s` matches `\n`, the regex was greedy across blank lines and ate
the rest of the file — including each demo's `def main()` and
`if __name__ == "__main__"` block.  This affected 33 files.

I misdiagnosed it as "42 ports are incomplete" because they no
longer had a `main()`.  Bill caught the misdiagnosis ("they may
not have a main method, but they are all runnable") — only after
that did I check `git diff master` and see the regex had silently
stripped main loops.

I then restored the 33 files from `master` and rewrote the migration
to use `ast.parse` + `node.lineno` / `node.end_lineno` for function
deletion (which can't gobble more than the targeted body).  The
recovery was clean: 101 of 102 files had `main()` after that
(the one without is `_thunderbird_data.py`, a data-only module).

### Bug 2 — the camera itself didn't work as Bill expected

After the recovery, the migration completed and all files compiled.
Bill ran them and reported the camera didn't work as expected.  He
threw the changes away rather than continue debugging.

I don't have the exact failure description, so the reasons below are
my best guesses about what likely went wrong.  **Verify each one
before re-attempting** — don't re-implement assuming these are facts.

#### Likely causes

1. **Object-rotation semantics ≠ walk-around semantics.**
   Many demos (chapt05/jet, chapt05/litjet, chapt05/shinyjet,
   chapt03/star, etc.) rotated the *object* in front of a fixed
   camera with `glRotatef(x_rot, ...) / glRotatef(y_rot, ...)`.
   Replacing that with a walk-around camera means the user has to
   walk around the object instead of spinning it.  For "show me all
   sides of this jet" that's a *worse* control scheme — the original
   intent was orbital, and walk-around requires the user to fly
   physical loops.  My script didn't distinguish "rotation that's
   really orbital framing" from "rotation that's really camera
   movement."  This is the most likely visible failure.

2. **`move_speed` wrong for the scene scale.**
   I used `move_speed=1.0` as the default, `0.1` for sphereworld,
   `5.0` for the chapt13+ shader demos.  But scene scales vary
   wildly — e.g. chapt05/jet is in tens-of-units, chapt06/multisample
   is in hundreds, the chapt03 primitives are in NDC-ish (±1).  WASD
   that walks 1 unit per frame is either glacial (large worlds) or
   teleporting through the scene (small worlds).  No single speed
   works.

3. **`apply_camera` placement broke `change_size`-based view setup.**
   The original `change_size` often set up the modelview matrix once
   (`glMatrixMode(GL_MODELVIEW); glLoadIdentity(); glTranslatef(0, 0, -K)`)
   and let `render_scene` push/pop on top of that.  My migration
   inserted `glLoadIdentity(); _common.apply_camera(camera, [])` at
   the top of `render_scene`, wiping the change_size translation
   each frame.  For demos where the camera is at origin and the
   `glTranslatef(0, 0, -K)` was the only thing positioning the
   scene, the scene now sits at the camera position and you see
   nothing.  Initial `Camera(position=[0, 0, K])` was supposed to
   compensate, but only when the K value was extracted from the
   `glTranslatef`; for some demos the `glTranslatef` lived
   elsewhere and the regex missed it.

4. **2D demos turned 3D.**
   chapt03/star, chapt03/triangle, chapt03/lines, etc., used
   `glOrtho` for projection — they're effectively 2D.  Adding a
   walk-around camera to them doesn't make sense; users would see
   the wireframe drift sideways with no perspective change.  My
   x_rot/y_rot detector matched these even though they shouldn't
   have been migrated.

5. **gluLookAt-with-origin-focus lost framing on the first key press.**
   For chapt13–18 shader demos, the original gluLookAt always
   pointed at origin from `camera_pos`.  I computed initial
   `rot_y = atan2(X, Z), rot_x = asin(-Y/r)` so the *initial* frame
   matched.  But the moment the user presses W/S, the camera walks
   along its forward direction — it doesn't keep tracking origin.
   For demos meant to "study this thing in the middle" that's a
   regression.

#### Plausible mitigations (for next attempt)

- **Don't migrate object-rotation demos (`x_rot`/`y_rot`) at all.**
   Keep their UP/DOWN/LEFT/RIGHT object-tumble behaviour.  Walk-around
   only fits demos that already use `gluLookAt` (true cameras) or have
   a navigable scene like sphereworld.  Smaller blast radius, fewer
   surprises.

- **Make `move_speed` per-demo.**  Read it from the existing
   `glTranslatef(0, 0, -K)` value — `move_speed = K / 50` or similar
   gives "walk forward 50 frames to cross the scene", which feels
   right at any scale.

- **Add an "Orbit" mode on `_common.Camera`.**  When `focus_index >= 0`
   the camera already orbits; expose this via the imgui Camera panel
   and *default* the chapt05 jets and chapt03 primitives to orbit
   mode with the scene as the focus object.  That preserves the
   original "tumble the object" feel while letting curious users
   switch to walk-around.

- **Hand-migrate 3 representative demos first** (one Pattern A,
   one Pattern B, one sphereworld) and ask Bill to verify visually
   before scaling.  Don't bulk-migrate 49 files only to discover
   the model is wrong.

## Files that were modified during the attempt

All under `/mvp/ports/openglsuperbiblev4/`.  Bill reverted via
`git checkout` so the working tree is back to `master` for these
files.  The plan files (`ports-imgui-menubar.md`,
`ports-walkaround-camera.md`, `ports-keyboard-standardization.md`,
`ports-sphereworld-camera-fix.md`, `ports-replace-cli-with-imgui.md`)
were also reverted to their pre-attempt state ("not started").

The migration scripts are still under `/tmp/` for reference if a
future attempt wants to study them — but the regex bug in
`migrate_v4_phaseB.py` (`(?:\s+[^\n]*\n)+` greedy across blanks) is
why the AST-based `migrate_v4_combined.py` was written.  Use the AST
approach if anything from `/tmp/` is reused.

## Lessons

- **Trust but verify "done" plans.**  The menubar plan claimed 92
  files were migrated; the audit showed 0.  Always grep-confirm a
  plan's claims before treating it as a foundation.
- **Don't use regex to delete code blocks.**  Use AST.  Function
  bodies in particular are too easy to over-match because blank
  lines count as whitespace.
- **Hand-migrate before scaling.**  A 49-file bulk migration that
  fails on visual semantics costs a full session to recover from;
  3 hand-migrations + a verification ride costs ~30 min and
  surfaces semantic mismatches before the script generalizes them
  across the tree.
- **Don't conflate "object rotation" with "camera movement".**
  They look syntactically similar (`glRotatef` calls) but are
  pedagogically opposite.  The walk-around-camera plan should
  have specified which demos genuinely have a *camera* (vs.
  object tumble) before any migration started.
