# Tighten bunner (Code the Classics vol 1)

**Status:** DONE 2026-09-05 (Fable session) — all gates green, staged; archived. Play-test audio
(looping river/traffic ambience with distance volume, plus one-shot effects) when convenient.
**Priority:** 3
**Difficulty:** 5
**Part of:** `tasks/archive/2026/09/05/codetheclassics-tighten-games.md` · **Depends on:** the boing depth read · **Next:** `tasks/codetheclassics-tighten-soccer.md`
**Engine family:** vol1-rich (with soccer): the vol1-minimal engine **plus** `surface` 1476, `draw` 1634, `text` 1684 and a richer `Screen`/`_Mixer`. Tighten this engine once; soccer shares it.

## BLUF

Apply `tasks/reference/code-the-classics-tightening.md` to
`ports/codetheclassics/vol1/bunner/bunner.py` (3583 lines). Highest engine-dead ratio in vol1
(~250 lines with zero callers) but **most of the "dead" draw/text surface is only dead because
`DEBUG_SHOW_ROW_BOUNDARIES = False`** (2462) — decide that first. Rich `Row`/`MyActor`
hierarchy with several one-line `super()` constructors and RNG-bearing row constructors.

## Context (read first)

- Shape (HEAD 2026-09-05): banners `_types` 54 … `__init__` 2340; game code from 2445; `__main__`
  at 3507; alias line 52 `_text = audio = gldraw = sys.modules[__name__]`. `update()` takes no `dt`.
- **Heaviest import in vol1:** `game = Game()` 3501 → `Game.__init__` 3192 → `music.play("theme")`
  3200, constructs `Grass(None, 0, 0)` 3209 (Actors → image loads) and consumes `random()`
  (2907) / hedge-mask RNG; **3490–3495 reads `high.txt` from the CWD at import** and 3441 writes it.
- Two `ty: ignore` in the game part: 2478 (`MyActor.draw` widened arity — comment says why, keep
  or fix at the base) and **3217 `scroll_pos` used as float accumulator AND list index — a real
  latent type bug**, annotated "pre-existing"; fix it rather than carry it.

## Analysis

**Engine dead here (zero callers):** the entire `Surface` class 1509–1632 (only referenced by
docstrings), `_MixerSound` 2410–2440 + `_pooled_sound` 2405 + `_Mixer.Sound` 2401,
`_Mixer.find_channel/get_busy`, `Screen.fill/bounds/clear`, `_RectBase` pair properties +
`contains/move/move_ip/inflate/copy/__repr__/_pair/__iter__`, `Image.get_width/get_height/
get_size/get_rect` (**`from_rgba` is live** — `text._render` 1783), `_Loader.clear`,
`Sound.get_volume/fadeout`, `_Music.play_once/get_volume/stop/fadeout`, `Renderer.fill/
filled_rect/polygon/circle/set_clip`, `Actor.distance_to/colliderect/collidepoint/__iter__`,
`audio.available`. **Debug-flag-gated only:** `_Painter.text` 1871 (3320), `_Surface.get_width`
1929 (3316), `draw.rect` 1651 (3311), `Rect(...)` 3312; all other `_Painter`/`_Surface`/`draw`
methods are dead outright.
Used and notable: **`keys.UP/RIGHT/DOWN/LEFT/SPACE`** 2530, 3427, 3453 (the only vol1 game using
`keys` — keep `_Keys` or replace with the GLFW constants); `sounds.*.play(-1)` 3357 (looping!),
`Sound.set_volume` 3361, `Sound.stop` 3364/3372 — **keep the loop path and these methods**;
`getattr(sounds, …)` 3340, 3353; `screen.blit` ×4; `music.set_volume/play` 3198–3201.

**Game classes:** `MyActor` 2466 (adds `children` 2475); `Eagle` 2498, `Bunner` 2540 —
`@dataclass(eq=False)` + `InitVar spawn_pos` (`Bunner.min_y` 2556 set in `__post_init__` →
declare; `input_queue` already `default_factory`); `Mover` 2678 (`dx`), `Car` 2689 (`played`,
`sounds` mutable lists + class consts), `Log` 2712 / `Train` 2718 (one `randint` + `super()`),
`Row` 2727 (`index`, `dx`), `ActiveRow` 2770 (**RNG loop in `__init__`** 2773: `choice` + a
`while` of `randint`s building children), `Hedge` 2820 (single `super()`), `Grass` 2885
(`random()` gate + `generate_hedge_mask` + 12-child loop; `hedge_row_index`/`hedge_mask` set in
branches), `Dirt` 2953 / `Pavement` 3115 (**dead `predecessor` parameter** kept for the uniform
`row_class(self, index, y)` call shape — document, don't delete), `Water` 2977 / `Road` 3038
(compute `dxs` from `predecessor.dx`), `Rail` 3134, `Game` 3191 (`bunner looped_sounds eagle
frame rows scroll_pos`; **`frame` 3206 is write-only, dead**). Row constructors are behaviour
(RNG, children) — convert only where the body is a plain `super()`; the state trace must cover
several rows scrolling in.

**Function-tightening candidates:** **`Grass.next` 2937–2950 and `Dirt.next` 2961–2974 are the
same 5-branch chain** → one helper (module-level; used by both); `Road.next` 3087–3113 nested
`random()` thresholds (2 RNG calls, order-critical — table form only if the call order is kept);
`Pavement.next` 3123–3130, `Rail.next` 3180–3189 → expressions; `classify_hedge_segment`
2846–2879 → conditional expressions; `key_just_pressed` 3381–3401 `result=False; if…` →
expression (note the double `keyboard[key]` read); 3253–3267 `sum([...])` + `min(0.4, …)` → one
expression; `Rail.update` 3141 whole-body `if` → early return; `Row.collide` 2743–2754 → `next(
(…), None)`; `Row.next` base 2739 dead; `Game.update` `return self` 3272 discarded by callers.

**pygame comments in the game part (6):** 2464 (keep "list of child objects … drawn relative to
the parent", drop the attribution), 2478 (`ty: ignore` rationale — keep), 3334 framing / **3339
keep**, 3413 false, 3504 → main-loop banner. Engine comments carrying real rationale (keep the
fact, drop the framing): 1478–1490 (`Surface` = composite offscreen buffer), 1015, 2377–2380,
1078–1084 (images decode immediately because objects exist at import).

## Plan, as scaffolded before the work (the record below is what happened)

Engine: decide the debug flag (Q1), then strip; keep `Sound` loop/`set_volume`/`stop` and
`from_rgba`. Game: dataclass/slots the plain-`super()` classes and `Game` (declare its six),
the two `next()` chains → a shared helper, expressions above, fix `scroll_pos`, header, comments.
Gates: `verify_game.sh`, `state_trace.py` with hops (up/left/right) so rows generate and a car
sound plays, `make format`, the actor-field-collision test. Run the trace from the game's own
directory so `high.txt` resolves the same way in both runs.

## Work record (2026-09-05)

- **Engine:** `splice_vol1_engine.py bunner "Infinite Bunner" - 480x800` (the `-` selects the
  code-indexed keyboard: bunner reads keys by GLFW code, so `keyboard[code]` replaces the name
  table; `keys.UP` etc. became `glfw.KEY_UP`), then bunner-only additions patched in: looping
  buffer voices + per-sound volume + `stop` in the mixer (the river/traffic ambience), a Pillow
  text renderer (`draw_text`), an outline `Renderer.rect` with its own dynamic buffer, and
  `Image.from_rgba` — all for the `DEBUG_SHOW_ROW_BOUNDARIES` overlay, which is KEPT (Q1) as the
  upstream "see what happens when you change this to True" teaching hook. The family `Actor` gained
  read-only `width`/`height` (bunner's `Row.collide` reads them; the splice script carries them
  now — cavern/myriapod still lack them, harmlessly).
- **Found and fixed a latent shim bug:** the old `screen.draw.text(text, pos)` mis-declared its
  second positional parameter (`surf`), so the debug overlay's row-index labels were never drawn
  (verified by capturing the original with the flag forced on: outlines only). The new overlay
  draws them at each row, as the original pygame game does. The debug A/B therefore differs by
  the labels only; the outlines match.
- **Classes:** `MyActor` plain + `__slots__`; its widened `draw(offset_x, offset_y)` override (a
  `ty: ignore` Liskov violation) is now `draw_at(offset_x, offset_y)` and the `GameObject` Protocol
  is `update()` + `draw_at()`; `Eagle`/`Bunner` → `slots=True` (`Bunner.min_y` declared);
  `Mover`/`Car`/`Log`/`Train`/`Row`/`ActiveRow`/`Hedge`/`Grass`/`Dirt`/`Water`/`Road`/`Pavement`/
  `Rail` stay plain with `__slots__` — their constructors COMPUTE the base's inputs (image name from
  `randint`/index, position from `y`, anchor) and consume RNG, so a dataclass base would only add
  sentinel InitVars and re-initialisation (rationale now in the reference doc §1a); **`Game` →
  dataclass** (`bunner: Bunner | None`, dead `frame` dropped, `scroll_pos: float` — the old
  `int` annotation + `ty: ignore` hid a real float accumulator; the one integer use, the menu's
  `// 6 % 4`, gets an `int()` that is a no-op there).
- **Functions:** `Grass.next`/`Dirt.next` (identical 5-branch chains) → one `_next_after_plain_row`
  helper with a `RowFactory` alias (documents why `predecessor` is passed to rows that ignore it);
  `Row.next` base raises `NotImplementedError` (every kind overrides), likewise a base
  `play_sound`; `Row.collide` → `next(…, None)`; `classify_hedge_segment` → early return +
  conditional expressions; `key_just_pressed` → 3 lines; `Rail.update` → early return;
  `Rail.next` unpacks `choice(...)` directly; volume → one `min(0.4, sum(gen) - 0.2)`; `Game.update`
  returns `None`; both `match state:` blocks end in `case _: raise`; `sounds.load(f"…")`;
  `blit(name, x, y)`; f-strings; the mixer no-ops and the Python-3.5 check are gone; `high.txt`
  stays CWD-relative as upstream wrote it.
- **Numbers:** 3583 → 2164 lines (−40%); pygame/pgzero mentions 118 → 2.
- **Gates:** frame 180 AE=0 vs HEAD (the original 3583-line file); 1500-frame input trace
  (start, hop up/right/left, a splat, game over, restart) byte-identical modulo the baseline's
  removed dead `frame` attribute and its derived `left/centerx/centery` properties (the trace
  harness now dumps Actor properties, dict contents and class names — the earlier cavern/myriapod
  traces were re-run under this stronger comparison and are still identical); rows of every kind,
  cars/logs/trains/hedges, and the looping ambience (1393 frames) all appeared; `ty check` clean;
  `make format` ruff clean; 104 tests.

## Open questions — settled by Fable (maintainer had delegated discretion)

1. ~~**`DEBUG_SHOW_ROW_BOUNDARIES`:**~~ KEPT, and its labels now actually draw (see above). Original text: keep the debug feature (then keep `_Painter.text`,
   `_Surface.get_width`, `draw.rect`, `Rect`) or delete the flag and its ~40 lines of
   engine? *(Recommend keeping it — it is the only text/draw use in vol1 and cheap.)*
2. ~~**`scroll_pos` float-vs-index (3217):**~~ FIXED as recommended (`float`, `int()` at the index). Original text: fix the type (an `int(...)` at the index site) rather
   than keep the suppression? *(Recommend fix — behaviour-identical if the value is already
   integral there; the trace proves it.)*
