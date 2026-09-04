# pgzero_gl — remove the always-dead pgzero-fidelity code

**Status:** DONE — implemented & verified 2026-09-04 (see Result below)
**Priority:** 3
**Difficulty:** 3

## Result (2026-09-04)

All nine deletions applied (net **−166 lines**: 26 insertions, 192 deletions across 9 shim files), plus the
now-unused `angle`/`anchor` params removed from both renderers' `draw_image` and two stale `on_key_down` doc
mentions fixed in `input.py`. The two reader-flagged-but-actually-live items were **kept** (`joystick.init()`,
`_Mixer.find_channel`/`get_busy`). One test (`tests/test_ctc_actor_field_collisions.py`) hardcoded `angle` in
the expected Actor property set — updated to drop it (the whole point of the deletion). Verified in the nested
container (image built `BUILD_DOCS=0 USE_EMACS=0 USE_JUPYTER=0 USE_X_WINDOWS=1` — the deletion can't touch the
trimmed paths):

- **ruff** check + format clean/idempotent; **ty** no real errors (only host-env unresolved-imports).
- **pytest: 104 passed** (`make test`).
- **Headless game runs** (Xvfb + Mesa llvmpipe): boing GL 3.3 core rc=0 (mean 0.127, 11,467 colours), boing
  GL 1.x fixed-func rc=0 (mean 0.127), beatstreets GL 3.3 rc=0 (mean 0.0625, exercised the kept
  `find_channel`/`get_busy` + joystick + surface). Sprites render untinted — the `tint` removal is
  behavior-preserving on both renderers.

Rationale + the verified-dead evidence live in
`tasks/reference/pgzero-gl-design-for-a-personal-learning-library.md`.

## BLUF

Delete the pgzero-fidelity code paths in `src/modelviewprojection/pgzero_gl/` that **no book demo and no
Code-the-Classics port uses** — verified 2026-09-04 by grepping the whole repo (demos + all 11 ports), not
just the games. Nine pure deletions, each behavior-preserving (a path nothing runs). **Two things the design
study wrongly flagged as dead are corrected here to KEEP** — the verification caught them. Duplication in the
games is intentional pedagogy and is untouched; this task removes only *dead* code, never *duplicated* code.
Rationale + full per-file evidence: `tasks/reference/pgzero-gl-design-for-a-personal-learning-library.md`.
This is the extraction of Group 1 from `tasks/pgzero-gl-de-abstraction-options.md`.

## Context (read first)

- The six-reader design study (2026-09-03) surfaced these as "zero game users." The readers only checked the
  11 ports; per the maintainer's approved Q2 decision, this task **re-grepped the book's own demos too**
  (`src/modelviewprojection/demos/`, `assignments/`) before calling anything always-dead. The grep results are
  recorded inline below so a cold reader can re-run and trust them.
- **Verification gate:** after the deletions, a plain `make image` (the repo's default gate) must pass, and the
  ports + a couple of demos must still run. Behavior is unchanged by construction (dead paths / removed
  no-op params), so no game/demo output changes.
- **Do the deletions as one reviewable change per numbered item** (or a few grouped commits), so any surprise
  localizes. Each item names its exact `file:line` sites.

## The deletions (all grep-verified dead across demos + ports, 2026-09-04)

1. **Sprite rotation — the whole `angle` path.** No demo/port ever sets `Actor.angle` (the only `.angle`
   assignments in the repo are `wxapp.py:79,276`, an unrelated wxPython GL-canvas shader uniform). Remove:
   - `Actor.angle` field + property and the `angle=` argument threaded through `Actor.draw()` (actor.py).
   - `renderer.draw_image(angle=…)` rotation branch + `renderer._rotate_z` (renderer.py:66 and the compose at
     :251); the GL-1.x twin in `renderer_gl1.py`.
   - **`Actor.angle_to`** (actor.py:321-325) — grep-verified **zero** callers anywhere (demos + ports). The
     study's "keep unless demos use it" caveat is resolved: they don't. Delete it. (It was never a gacalc
     candidate — g2 has no angle helper.)
2. **`on_key_down`/`on_key_up` hook machinery.** grep `def on_key_down|def on_key_up` across the repo = empty.
   Remove `_call_key_hook` + the hook wiring (runner.py:125-126,137-150,212-224). **Keep** the
   `keyboard._press/_release` tracking and the Esc-to-quit handling (those are used).
3. **`Actor(**kwargs)` delegated-anchor constructor.** No demo/port passes `topleft=`/`center=`/… to `Actor`.
   Drop `**kwargs` + the `_DELEGATED` set + the `else` branch (actor.py:110,126-133,57-78); keep the concrete
   `image, pos=None, anchor=None` signature.
4. **`geometry._VIRTUALS`** (geometry.py:44-67) — the only reference in the whole package is its own
   definition. Delete outright.
5. **`draw_image(tint=…)` sprite tint path.** grep `tint=` across the repo = zero callers; `uTint` is always
   `(1,1,1,1)`. Remove the `tint` param + the `uTint` set from the sprite draw path in both renderers
   (renderer.py:223,262; renderer_gl1.py:87,103). *(Leave the `uUseTex`/flat-fill uniforms — only the sprite
   tint is dead. The `_rgba` color-heuristic collapse is a separate behavior-narrowing rewrite, NOT part of
   this dead-code task — it stays in the options task.)*
6. **Unused joystick *instance* methods:** `get_name`, `get_id`, `get_numaxes`, `get_init` (joystick.py) —
   grep-verified zero callers. **KEEP `joystick.init()`** — the correction below.
7. **`audio.Sound(maxtime=…)`** accepted-and-ignored param (audio.py:326,330) — zero callers; drop the dead
   param.
8. **`text.py` Pillow `textsize` fallback** (text.py:128-131) — dead since Pillow 8.0 (`textbbox` always
   present on any pinned modern Pillow). Remove the fallback branch.

## Corrections — the study flagged these as dead; verification says KEEP (do NOT delete)

- **`_Mixer.find_channel` / `_Mixer.get_busy`** (__init__.py:96-99) — **USED by beatstreets**
  (`beatstreets.py:1674` `mixer.find_channel()`, `:1783,:1802` `.get_busy()`). The games-usage reader missed
  beatstreets. Keep both — and note `find_channel` must return an object whose `get_busy()` works (verify
  beatstreets' scooter-sound loop still behaves after any nearby edits).
- **`joystick.init()`** (module-level) — **called by all 5 vol2 games** (`avenger.py:213`, `beatstreets.py:378`,
  `eggzy.py:273`, `kinetix.py:284`, `leadingedge.py:384`, each `joystick.init()  # Not necessary in Pygame
  2.0.0 onwards`). The runtime reader wrongly listed `init` as unused; two readers disagreed and the grep
  resolved it. Keep `joystick.init()`; only the *instance* `get_init` is dead (item 6).

## Verification recipe (bake these greps; re-run to trust)

```sh
SHIM=src/modelviewprojection/pgzero_gl
grep -rnE "def on_key_down|def on_key_up" --include=*.py . | grep -v "$SHIM"   # empty
grep -rnE "\.angle_to\b|\.angle\s*=" --include=*.py . | grep -v "$SHIM"        # only wxapp.py (unrelated)
grep -rnE "Actor\([^)]*(topleft|center|midtop)\s*=" --include=*.py .|grep -v "$SHIM"  # empty
grep -rnE "tint\s*=|maxtime\s*=" --include=*.py . | grep -v "$SHIM"            # empty
grep -rn "_VIRTUALS" --include=*.py .                                          # only geometry.py:44 def
grep -rnE "joystick\.init\(|find_channel|get_busy" --include=*.py . | grep -v "$SHIM"  # KEEP: games use these
```

Then: `make image` (repo gate) → run boing + one vol2 game (e.g. beatstreets, to exercise `find_channel`/
`get_busy`) + a joystick game → confirm no regression.

## Out of scope (lives in the options task, not here)

- The `_rgba` 4-way→int-RGB color collapse (behavior-narrowing rewrite).
- `input._register()` → literal key dict (rewrite, not dead-code removal).
- All gacalc-clarity rewrites (`distance_to`, anchor math) and the `_offset_cache` re-measure.
- Any game duplication — intentional pedagogy, never touched.

## Open questions

None — the plan is approved and the dead set is grep-verified. If a deletion turns out to have a caller the
grep missed, stop and re-scope rather than forcing it.
