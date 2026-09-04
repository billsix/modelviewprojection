# pgzero_gl — de-abstraction & gacalc options (choose per item)

**Status:** partially decided (maintainer, 2026-09-04) — Group 1 **DONE & archived**
(`tasks/archive/2026/09/04/pgzero-gl-remove-dead-code.md`); Groups 2-3 recommendations accepted (see resolved
Open Questions)
**Priority:** 5
**Difficulty:** 4

## BLUF

`pgzero_gl` is a **personal** OpenGL pygame-zero for the book's demos + 11 Code-the-Classics ports — not a
general library — so it carries pgzero-fidelity code paths **no game uses**, and some `Actor`/game math is
hand-rolled component arithmetic where the callers already speak `gacalc.g2.Vector`. This task is a **menu of
independent, opt-in changes**, each grep-verified, grouped by risk. **Duplication in the games is intentional
pedagogy and is explicitly OUT of scope** — nothing here DRYs the games. Pick the items you want; each is
small and standalone. Full rationale + `file:line` evidence:
`tasks/reference/pgzero-gl-design-for-a-personal-learning-library.md`.

## Context (read first)

- The design study (six parallel readers, 2026-09-03) is the reference doc above — read it for the "why" and
  the per-file evidence. This task is just the "do", as options.
- **Guiding constraint (maintainer, 2026-09-04):** "the point of the class is learning … a lot of duplication
  … helps students remember. I don't mind duplication." So: **keep** the 6-way `sign()`, per-game `draw_text`,
  `play_sound` boilerplate, the two-renderer split, `@dataclass(eq=False)`+`InitVar spawn_pos`. This task
  removes only **dead code** (paths no game runs) and offers **clarity** rewrites (math that reads as GA).
- The transform/matrix slice is deliberately in its own task (`gacalc-transforms-for-rotate-translate.md`) —
  Group 1 below deletes the *dead sprite-rotation* path, which overlaps but is distinct from the still-open
  "should the renderer's `uModel` matrices become gacalc" question.
- Each group is independent; none blocks another. Verify with a plain `make image` (the repo's gate) after any
  code group; per-game behavior is unchanged by design (dead paths / equivalent math).

## Group 1 — delete dead pgzero-fidelity → **DONE (archived `tasks/archive/2026/09/04/pgzero-gl-remove-dead-code.md`)**

**Decision (maintainer, 2026-09-04):** approved, implemented, and verified (net −166 lines; 104 tests pass;
boing/beatstreets render headless on both renderers). The always-dead pure deletions were re-verified across
the book's demos AND the ports (not just the games). Two items the
readers wrongly flagged as dead were **corrected to KEEP** during that re-verification: `_Mixer.find_channel`/
`get_busy` (beatstreets uses them) and `joystick.init()` (all 5 vol2 games call it). The list below is kept for
history; the authoritative, corrected list is in the extracted task. The `_rgba` color collapse (item 5's second
half) and the `input._register` literal-dict (item 7) are **rewrites, not dead-code** — they stay HERE in the
options menu, not in the deletion task.

Each is a pure deletion with no behavior change. High confidence.

1. **Sprite rotation.** Remove `Actor.angle` field + the `angle=` thread into `Actor.draw()` →
   `renderer.draw_image(angle=…)` → the `_rotate_z` compose (actor.py; renderer.py:66,251; renderer_gl1.py).
   No game sets `.angle` (kinetix rotates *vectors* and swaps pre-rendered frames by `.image`). *Note:* leave
   `angle_to` unless the demos also don't use it — verify demos before deleting that one method.
2. **`on_key_down`/`on_key_up` hooks.** Remove `_call_key_hook` + wiring (runner.py:125-126,137-150,212-224);
   keep `keyboard._press/_release` tracking and Esc-to-quit. No game defines either hook.
3. **`Actor(**kwargs)` delegated-anchor constructor.** Drop `**kwargs` + the `_DELEGATED` set + the `else`
   branch (actor.py:110,126-133,57-78); keep `image, pos=None, anchor=None`. No game passes a delegated kwarg.
4. **`geometry._VIRTUALS`** (geometry.py:44-67) — zero references; delete outright.
5. **`draw_image(tint=…)`** — drop the tint param/uniform from the sprite path (renderer.py:223,262;
   renderer_gl1.py:87,103); `uTint` is always `(1,1,1,1)`. While here, **collapse `_rgba`'s 4-way color
   heuristic** (renderer.py:364-376) toward int-RGB(A) — the games pass int tuples, and the float branch was
   the source of a known integer-tint black-screen bug (`_smoketest.py:18`).
6. **Unused joystick pygame-compat** — `get_name`/`get_id`/`get_numaxes`/`get_init`/`init` (joystick.py); never
   called by the 5 joystick games. Optionally collapse `_read_glfw_array` to the pinned-pyGLFW `(pointer,count)`
   case (drop the untriggered plain-sequence branch, joystick.py:83).
7. **`input._register()` → literal key dict** — replace the `getattr(glfw,"KEY_"+…)` reflection loop
   (input.py:30-57) with an explicit dict of the ~25 keys the games name; drop the `k_0..9` aliases and
   `tab`/`backspace`/`r*` modifiers.
8. **Micro-dead:** `text.py` Pillow `textsize` fallback (text.py:128-131, dead since Pillow 8.0); `audio.Sound`
   ignored `maxtime` (audio.py:326,330). **NOT `_Mixer.find_channel`/`get_busy`** — the grep showed beatstreets
   uses them (beatstreets.py:1674,1783,1802); keep. **Not `joystick.init()`** either — all 5 vol2 games call it;
   only the instance `get_init`/`get_name`/`get_id`/`get_numaxes` are dead. (Both are now handled correctly in
   the extracted deletion task.)

## Group 2 — gacalc clarity in Actor (behavior-preserving; makes math read as GA)

No abstraction added — these remove hand-rolled component arithmetic in favor of the ops the callers already use.

9. **`Actor.distance_to`** (actor.py:327-331): `sqrt((tx-mx)**2+(ty-my)**2)` → `(target_pos - self.pos).magnitude()`
   (`self.pos` is already a `Vector`; wrap in `float(...)` to document the boundary). This is exactly what
   avenger/kinetix write for themselves.
10. **Anchor math** (actor.py:150-179): make `_anchor_offset` return a `Vector`, then `_anchor_pos` = `topleft +
    offset` and `_set_pos` = `pos - offset`, unpacking to scalar `left`/`top` once at the `_rect` boundary.

## Group 3 — judgment calls (measure or discuss first; do NOT do blind)

11. **`_offset_cache`** (actor.py:103,145,156-165,237,298,307): 8 touch-points + a 5-site invalidation web
    guarding two dict lookups + two multiplies. It was justified by an audit of the *old* `__getattr__` string-
    ladder cost; now that x/y are plain properties it may be noise. **Re-measure first**; if it doesn't matter,
    delete it (removes all 5 invalidation sites and a `None`-typed field). Correctness-sensitive — don't rush.
12. **eggzy/cavern velocity → `Vector`?** **DECIDED (maintainer, 2026-09-04): preserve the scalar-vs-Vector
    teaching contrast on purpose.** Leave **cavern scalar** (it teaches per-component motion next to kinetix's
    Vector-native style). The only optional tidy is eggzy's one `Vector(dx,dy).normalize()*DASH_SPEED`
    round-trip that immediately decomposes back to `int(v.x),int(v.y)` (eggzy.py:911) — may be cleaned if
    convenient, but not required. No uniform vectorization.

## Explicitly OUT of scope (do not do)

- **DRYing the games** — `sign()`×6, per-game `draw_text`/font tables, `play_sound`/`mixer` boilerplate, the
  `State`-enum skeleton: all intentional repetition for learning. Keep.
- **Merging the two renderers** — the GL 1.x / GL 3.3 split is a deliberate teaching artifact.
- **Turning `geometry.Rect` corner/edge pairs into Vectors** — pygame contract; the games rely on tuple return.
- **The renderer's `uModel` matrices** — matrix-based on purpose (`glUniformMatrix4fv` boundary); that question
  is `tasks/gacalc-transforms-for-rotate-translate.md`, not this task.

## Open questions — RESOLVED (maintainer, 2026-09-04: "I go with your recommendations on all 3")

1. **Which groups/items?** → **Group 1 done & archived** (`tasks/archive/2026/09/04/pgzero-gl-remove-dead-code.md`).
   Groups 2-3 proceed per the recommendations below.
2. **`angle_to` + `_offset_cache` — verify demos / re-measure first?** → **Yes, and done for `angle_to`:** the
   whole-repo grep (demos + ports) shows **zero** `angle_to` callers, so it is now in the deletion task.
   **`_offset_cache` (item 11) still needs its re-measure** before deletion — that measurement is the remaining
   to-do for Group 3; it was NOT extracted (it's a judgment call, not always-dead).
3. **eggzy/cavern vectorization (item 12)?** → **Preserve the scalar-vs-Vector contrast on purpose.** cavern
   stays scalar; only eggzy's `:911` normalize round-trip is an optional tidy. Recorded in item 12 above.

### Remaining actionable work in THIS task (after Group 1 left)

- **Group 2 (items 9-10)** — gacalc clarity in `Actor.distance_to` and the anchor math; behavior-preserving,
  ready when you want them.
- **Group 3 item 11** — re-measure `_offset_cache`, then delete only if it's noise.
- **Group 3 item 12** — optional eggzy `:911` tidy; cavern left scalar by decision.
