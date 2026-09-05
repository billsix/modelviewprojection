# Tighten boing (+ boing_gl1) — the pilot that set the standard

**Status:** DONE — maintainer sign-off 2026-09-05 ("looks great"); depth confirmed as the standard
for the other nine games; `#:` field doc-comments applied the same day (all gates re-run green).
Archived 2026-09-05.
**Priority:** 2
**Difficulty:** 5
**Part of:** `tasks/archive/2026/09/05/codetheclassics-tighten-games.md` (umbrella) · **Next:** `tasks/codetheclassics-tighten-cavern.md`

## BLUF

`ports/codetheclassics/vol1/boing/boing.py` and its fixed-function companion `boing_gl1.py` are
tightened to the shape recorded in `tasks/reference/code-the-classics-tightening.md` §1: demo-style
module-level window + renderer, plain section banners, only the engine boing uses, dataclasses with
`slots=True` and declared fields, two structural Protocols (`Sprite`, `SpriteRenderer`), `match`
blocks that end in `case _: raise`, the BSD-2-Clause header, and no pygame/pgzero framing (67 → 2
mentions; the 2 are the `PGZERO_MAX_FRAMES` harness contract). 1854 → 1270 lines; 1724 → 1170.
Behaviour proven identical three ways (below).

## What the maintainer should look at (the review-worthy judgment calls)

1. **Audio mixer stripped to boing's use** — no fades, no buffer looping, no per-play volume
   (`Sound.play()` takes no args). Not provable by the frame or state harness: **play-test that
   the theme music loops and hit/bounce/score sounds fire.**
2. **`Context` dissolved** into `ASSET_ROOT` (from `__file__`) + a module-level `renderer`; the
   window is created at module level so `require_renderer()` is gone (your call, 2026-09-05).
3. **`images.load()` everywhere, `_Loader.__getattr__` dropped** — the `images.<name>` idiom is
   gone from boing (it was only used via `getattr(sounds, …)`), which is also what made
   `_Loader` slots-safe and generic (`_Loader[T]`).
4. **`Game` is now a dataclass** (`controls` as `InitVar`, bats/ball built in `__post_init__`).
   The old comment argued a generated `__init__` "would add nothing"; the field list at the top
   of the class is what it adds.
5. **Protocols are structural, not subclassed** — tested, see the reference doc §1.6.
6. **Renderer/`Image` shapes untouched** (dead methods removed only) — deferred to
   `tasks/pgzero-gl-dataclasses-investigation.md`.
7. **The upstream "list comprehensions next chapter" teaching comment** on the impact-removal
   loop was replaced by the comprehension itself; the other upstream game-logic comments stay.

## Verification record (2026-09-05)

- `tasks/adhoc/codetheclassics-tighten-games/verify_game.sh`: frame 180 **AE=0** for `boing.py`
  vs HEAD, `boing_gl1.py` vs HEAD, and `boing_gl1.py --against boing.py` (fresh Xvfb each run).
- `tasks/adhoc/codetheclassics-tighten-games/state_trace.py`, 1500 frames, key script
  `5:space:press,6:space:release,400:z:press,412:z:release,900:a:press,915:a:release`:
  **byte-identical** HEAD vs `boing.py` vs `boing_gl1.py`; coverage MENU→PLAY, 72 frames with
  impact sprites, 7 distinct `ai_offset` values, ball speed up to 9, 8 distinct directions,
  scores 0–7 (so the bat-collision, deflection, wall-bounce, scoring and AI paths all ran).
- `make format`: ruff clean, `ty check ports/codetheclassics/vol1` and `vol2` clean; the 36
  diagnostics in `src`/`tests` are the pre-existing gacalc-invariance ones
  (`tasks/ty-0072-strictness-sweep.md`).
- Negative test for the Protocol decision: a copy with `Impact.update` deleted → ty silent with
  `class Impact(Sprite)`, correct error without the subclass (reference doc §1.6).

## Done-state

Maintainer play-tests both files (input, audio) and confirms the depth; then this task archives
(harvest is already in the reference doc) and the other nine games follow the same standard.
