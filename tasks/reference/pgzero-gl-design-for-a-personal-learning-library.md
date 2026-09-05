# pgzero_gl — design notes for a personal *learning* library

**What this is:** a durable design study of the `pgzero_gl` shim (`src/modelviewprojection/pgzero_gl/`,
18 files ≈ 3,400 lines) and how the 11 Code-the-Classics ports (`ports/codetheclassics/{vol1,vol2}`,
≈ 16,300 lines) actually use it — read in depth 2026-09-03 by six parallel readers, every claim below
anchored `file:line` and checked against the real game sources. Author: synthesized for
William Emerison Six <billsix@gmail.com>. Project: `github.com/billsix/modelviewprojection`.

**This is a reference doc — it states what is TRUE, not a work plan.** The actionable, choose-one-per-item
options live in the sibling task `tasks/pgzero-gl-de-abstraction-options.md`; the transform/matrix slice has
its own task `tasks/gacalc-transforms-for-rotate-translate.md`. Both cross-link back here.

## BLUF

`pgzero_gl` is a **personal** OpenGL reimplementation of pygame-zero that serves exactly two clients: the
book's own demos and these 11 ports. It is *not* a general library, so it does **not** need to reproduce
pygame-zero's open-world flexibility — and much of its dynamism is fidelity to an upstream nobody here needs
to match. Three findings shape everything:

1. **Duplication in the games is a FEATURE, not a smell (maintainer, 2026-09-04):** "the point of the class
   is learning, and … a lot of duplication … helps students remember. I don't mind duplication." So the
   copy-pasted `sign()`, per-game `draw_text`, and `play_sound` boilerplate **stay**. Nothing in this doc
   recommends DRYing the games. The cleanups are about *dead code* (paths no game exercises) and *clarity*
   (making math read as what it is), never about removing repetition.
2. **The public vector boundary is already right.** `Actor.pos` returns a `gacalc.g2.Vector`, and the games
   already write `self.pos + Vector(...)`, `(a.pos - b.pos).magnitude()` (~157 sites). The gacalc gap is
   *internal*: `Actor`'s own anchor/distance math still speaks tuples in a dialect its callers don't use.
3. **The dead-fidelity pockets are large and grep-verifiable.** Sprite rotation (`Actor.angle`/`angle_to` →
   `renderer.draw_image(angle=…)`), the `on_key_down`/`on_key_up` hook machinery, the `Actor(**kwargs)`
   delegated-anchor constructor, `_VIRTUALS`, and `draw_image(tint=…)` are used by **zero** of the 11 games.

## Context — what pgzero_gl is, and its two renderers

- The shim lets pygame-zero-style game code (`Actor`, `screen.blit`, `keyboard.left`, `music.play`) run on
  OpenGL instead of SDL. `context.py` holds one process-wide `renderer`/`window`/`asset_root` singleton so
  every draw method is stateless; `_types.py` is the leaf that defines `Point`/`PointLike`/`Anchor` and the
  `Drawable`/`RGBASource` protocols, and imports `gacalc.g2.Vector`.
- **Two interchangeable renderers**, chosen in `runner.py:47-51` by the `PGZERO_GL` env var:
  `renderer.Renderer` (GL 3.3 core, default) and `renderer_gl1.Renderer1x` (fixed-function GL 1.x, the
  book's demo19-era teaching artifact). They share only `_rgba` (imported at `renderer_gl1.py:40`) and must
  keep identical method signatures by hand — no ABC/Protocol enforces it; drift only shows under `PGZERO_GL=1`.
  **This duplication is deliberate** (teach fixed-function once, then the modern path) and aligns with the
  repo's "duplication across demos is intended" convention — do not DRY the two renderers together.

## The three categories every finding falls into

Read the file-by-file notes through this lens.

### A. Load-bearing dynamism — KEEP (the games depend on it)

- **Arbitrary `Actor` instance attributes** — `self.vel_y`, `self.timer`, `self.health`, `self.direction_x`…
  set in `__init__` and imperatively later (cavern.py:413-420; eggzy.py:526-707). The *dynamism* is real, but
  the 2026-07-09 audit (actor.py:28-35) already made the attribute set closed/static — these hit the ordinary
  instance `__dict__`, not a `__getattr__` ladder. So the convenience is load-bearing; the open-world
  machinery to support it is already gone. Nothing to do.
- **Mixed per-axis anchors** — `("center","bottom")`, `("center", 60)` (name + literal pixel), pure-pixel
  `(24,60)`, even reassigned at runtime `self.anchor = (175,172)` (avenger.py:1169; eggzy.py:99-103;
  myriapod.py:296). The `_calc` "named-fraction-or-literal per axis" resolution (actor.py:81-86) is genuinely
  exercised and cannot be simplified away.
- **Computed resource names** — the whole animation/sound-variant system is `getattr(images, "robot"+type+dir+frame)`
  and `getattr(sounds, name+str(randint(...)))` (boing.py:399; cavern.py:809). `resources._Loader.__getattr__`
  + its first-touch caching (resources.py:172, a real 148k-lookup perf fix) is load-bearing.
- **`InitVar spawn_pos` dataclass idiom** — every `@dataclass(eq=False)` Actor subclass renames `pos`→`spawn_pos`
  because `pos` is an Actor property (boing.py:62-66; cavern.py:195-209). A recurring shim-interaction cost, but
  correct.
- **The `joystick`/`draw`/`surface`/`mask`/`transform` submodules** — each used by ≥1 game (joystick: 5 vol2
  games; draw: bunner/soccer/eggzy/leadingedge; surface: beatstreets/kinetix/leadingedge; mask: avenger only;
  transform: leadingedge only). None are dead.
- **The audio software mixer + `_MixerSound`** (audio.py; `__init__.py:111-141`) — NOT over-engineered. Both
  are documented fixes for real bugs (a single-device callback mixer replaced a per-voice-stream backend that
  froze; `_MixerSound` restores avenger's per-shot distance-attenuated sounds the old no-op silently dropped).

### B. Dead pgzero-fidelity — safe to trim (grep-verified zero game users)

| Dead thing | Where | Evidence |
|---|---|---|
| **Sprite rotation**: `Actor.angle`, `Actor.angle_to`(*), `renderer.draw_image(angle=…)` rotation path, `renderer._rotate_z` | actor.py:321-325; renderer.py `_rotate_z` :66 + compose :251 | No game sets `.angle`; kinetix rotates *vectors* (`_turn`) and picks pre-rendered rotation *frames* by `.image` |
| **`on_key_down`/`on_key_up` hooks** + `_call_key_hook` introspection | runner.py:125-126,137-150,212-224 | grep `def on_key_*` across 11 games is empty; press/release tracking + Esc-quit ARE used, the hook dispatch is dead |
| **`Actor(**kwargs)` delegated-anchor constructor** + `_DELEGATED` set | actor.py:110,126-133,57-78 | Zero games pass `topleft=`/`center=`/… ; every construction is `Actor("img")`, `Actor("img",(x,y))`, or `Actor("img",pos,anchor=…)` |
| **`geometry._VIRTUALS`** (24-name set) | geometry.py:44-67 | Zero references anywhere — vestige of the old `__getattr__`-dispatched Rect |
| **`draw_image(tint=…)`** sprite tint path + `uTint` always `(1,1,1,1)` | renderer.py:223,262; renderer_gl1.py:87,103 | No caller passes `tint`; the always-white default pairs with `_rgba`'s error-prone float branch (a known black-screen bug, `_smoketest.py:18`) |
| **Unused joystick pygame-compat**: `get_name`/`get_id`/`get_numaxes`/`get_init` (instance) | joystick.py:100,104,139,55/96 | Never called by the 5 joystick games. **NOT `init`** — corrected below |
| **`input._register()` reflects ~2× the keys used** (`k_0..9` aliases, `tab`/`backspace`/`r*`) | input.py:30-57 | The games name ~25 keys; a concrete literal dict would drop the `getattr(glfw,"KEY_"+…)` loop |
| **Dead Pillow `textsize` fallback** | text.py:128-131 | `textbbox` exists since Pillow 8.0; dead on any pinned modern Pillow |
| **`audio.Sound.play(maxtime=…)`** accepted-and-ignored | audio.py:326,330 | `maxtime` documented ignored, zero callers. **`_Mixer.find_channel`/`get_busy` are NOT dead** — see correction below |

(*) **`angle_to` is also dead** — the whole-repo grep (demos + ports, 2026-09-04) found **zero** callers, so it
is in the deletion task alongside the rest of sprite rotation. (It was never a gacalc candidate — g2 has no
angle helper.)

**Corrections from re-verification (2026-09-04) — two reader claims were WRONG; these are KEPT, not deleted:**
- **`_Mixer.find_channel` / `_Mixer.get_busy`** (__init__.py:96-99) — **used by beatstreets**
  (`beatstreets.py:1674` `mixer.find_channel()`, `:1783,:1802` `.get_busy()`). The games-usage reader missed
  beatstreets. Load-bearing; `find_channel` must return an object with a working `get_busy()`.
- **`joystick.init()`** (module-level) — **called by all 5 vol2 games** (`avenger.py:213`, `beatstreets.py:378`,
  `eggzy.py:273`, `kinetix.py:284`, `leadingedge.py:384`). The runtime reader listed `init` as unused; two
  readers disagreed and the grep resolved it in favor of "used." Only the *instance* `get_init`/`get_name`/
  `get_id`/`get_numaxes` are dead.

### C. gacalc `Vector` opportunities — clarity, not abstraction

All in `actor.py` and two games. These make math *read as what it is*; they add no abstraction (they remove
hand-rolled component arithmetic in favor of the same GA ops the callers already use).

- **`Actor.distance_to`** (actor.py:327-331) is `sqrt((tx-mx)**2+(ty-my)**2)` where `self.pos` is *already* a
  `Vector`. It should be `(target_pos - self.pos).magnitude()` — literally the dialect avenger/kinetix already
  write for themselves (avenger.py:517,963). High-confidence clarity win. (Single game caller: eggzy.py:636.)
- **`Actor._anchor_pos`/`_set_pos`/`_anchor_offset`** (actor.py:150-179) express a translation as parallel
  scalar `x`/`y` lines (`return (left+ox, top+oy)`; `left = px-ox; top = py-oy`). If `_anchor_offset` returned
  a `Vector`, these become visible GA: `topleft + offset`, `pos - offset`. The `_rect` still stores scalar
  `left`/`top`, so you unpack once at the boundary. High-confidence.
- **eggzy and cavern are the scalar-game migration candidates** — both handle `vel_x`/`vel_y` independently
  throughout (eggzy.py:526-538,754-758; cavern's `move(dx,dy)` per-pixel loop cavern.py:148-186, no `math`
  import at all). eggzy's one Vector use is `Vector(dx,dy).normalize()*DASH_SPEED` immediately decomposed back
  to `int(v.x),int(v.y)` (eggzy.py:911) — the strongest single migration candidate. **BUT** per the maintainer's
  learning-first stance, migrating a game is a *pedagogical* choice, not a cleanup mandate: kinetix (Vector-native)
  and cavern (scalar) side by side may itself be good teaching. Flagged as an option, not a to-do.
- **myriapod / bunner** are axis-locked, grid-quantized movement (`DX[dir]/DY[dir]` tables) — a Vector rewrite
  is clarity-neutral there. Do NOT force it.

### The one place gacalc does NOT belong

The renderer's `_translate`/`_scale`/`_rotate_z`/`ortho_pixels` (renderer.py:50-89) are hand-rolled 4×4 numpy
matrices at the `glUniformMatrix4fv` boundary — the graphics-engine layer the repo's `CLAUDE.md` deliberately
keeps matrix-based. The GA→matrix question (can a gacalc transform *produce* a `uModel` matrix, or only apply
directly to CPU-side vectors?) is the subject of `tasks/gacalc-transforms-for-rotate-translate.md`; the study
above steers toward **"direct mode for actor/game math, leave the renderer matrices as-is."**

## Duplication is a feature here (the maintainer's stance, made explicit)

The games repeat a lot, and that is **intentional** — the book teaches by repetition so students remember. Do
not read the following as problems to fix:

- **`def sign(x)` copy-pasted in 6 games** (boing/cavern/avenger/beatstreets/eggzy/leadingedge, 36 call sites).
  It also happens to mark the un-vectorized code (option C above), but the *duplication itself* stays.
- **Per-game `draw_text` bitmap-glyph blitters** in 5 games, each with its own font-width table (the tables are
  genuinely per-game; the loop is boilerplate) — keep.
- **`play_sound`/`play_music` + `mixer.quit();mixer.init(...)` boilerplate**, the `@dataclass(eq=False)` +
  `InitVar spawn_pos` + module-level `match state:` skeleton — the universal per-game shape. Keep.

Consolidating any of these into a shared `_ctc_common.py` would trade the ports' faithful-copy pedagogy for DRY
— explicitly declined. **The convention "duplication across the book/demos is deliberate" governs the games; it
does not extend to keeping *dead code* in the shim.** Dead ≠ duplicated: a path no game ever runs teaches
nothing, so category B is still fair game.

## File-by-file quick index (anchors for jumping)

- **actor.py** — the hotspot. Category C (distance/anchor math) + category B (angle, kwargs constructor,
  `_DELEGATED`). Also the `_offset_cache` memoization (103,145,156-165,237,298,307): 8 touch-points + a
  5-site invalidation web guarding two dict lookups + two multiplies, justified by an audit of the *old*
  `__getattr__` cost — **re-measure, then likely delete** (medium confidence, judgment call).
- **geometry.py** — a faithful `pygame.Rect` (`Rect[int]`/`ZRect[float]` via `Generic[_C]`). Corner/edge pairs
  return **tuples** on purpose (pygame contract; games do `rect.center=(x,y)`, `randint(rect.top,rect.bottom)`)
  — NOT gacalc candidates. One deletion: `_VIRTUALS`. `ZRect` is never game-facing (internal to Actor) — could
  drop from `__all__`.
- **renderer.py / renderer_gl1.py** — category B (`tint`, and the `_rgba` 4-way color heuristic → collapse
  toward int-RGB since games pass int tuples). `src=`/atlas sub-rect serves **only eggzy** (eggzy.py:1572) —
  annotate as single-consumer rather than read as a general atlas engine. Matrix helpers stay matrix-based.
- **resources.py** — `_Loader.__getattr__` load-bearing; `Image.__init__` vs `from_rgba` duplicate setup (the
  `__new__` trick) — a shared private initializer is the only minor tidy. No vector content.
- **surface.py** — CPU-composited offscreen buffer (3 games). The alpha-composite (surface.py:100-118) is the
  one non-trivial routine and is correct; leave. Check whether any game passes `fill(rect=…)` sub-region — if
  none, that branch is dead generality.
- **screen.py / draw.py** — thin facades. `_as_xy` (screen.py:44-53) triple-dispatches Rect/Vector/generic; the
  `Vector` branch is load-bearing *because* gacalc `Vector` is not integer-indexable (`pos[0]` fails). `RectLike`
  alias is copy-defined in both screen.py:41 and draw.py:28 — a shared alias in `_types.py` is a tidy.
- **text.py** — 10-way anchor-keyword scan (ptext fidelity); games use a small subset. `_ANCHORS` fraction
  table duplicates `actor._ANCHOR_FRAC` — a shared table would de-dupe the anchor vocabulary (shim-internal, not
  a game). `text.py:165` `pos - (anchor_frac ⊙ size)` is a marginal gacalc candidate (the tuple form is already
  legible).
- **mask.py / transform.py** — points go straight into `int()`/numpy indexing or are width/height pairs; NO
  gacalc benefit. transform's `scale`/`smoothscale` are 91% identical but two 4-line bodies — duplication is
  fine.
- **runner.py / context.py / input.py / joystick.py / audio.py / __init__.py** — category B lives here
  (on_key hooks, key-table reflection, unused joystick *instance* methods, ignored `maxtime`). **NOT
  `_Mixer.find_channel/get_busy` and NOT `joystick.init()`** — both used by the games; see the corrections block.
  context.py is the deliberate global-state singleton — appropriately concrete; the only tidy is deduping the
  asset-root inference computed twice (runner.py:97-99 vs context.py:62-66). `joystick.get_hat → (x,y)` is the
  one vector-shaped construct, but the games index it `[axis_num]` (avenger.py:219; kinetix.py:289) so it MUST
  stay a subscriptable tuple — opportunity-with-a-blocker.

## The gacalc g2 `Vector` surface the games actually need (ground truth)

Verified against `geometricalgebra/src/gacalc/g2.py`+`base.py`: `Vector(x,y)` positional, frozen/immutable,
`__iter__` yields `x,y` (so `*v` and `px,py = v` work), read-only `.x`/`.y`, `+ - neg`, `*scalar`, `/scalar`,
`.magnitude()`/`abs()`, `.magnitude_squared()`, `.normalize()` (raises on zero), `.scalar_product()`→dot as
grade-0 (needs `float(...)` at float boundaries), `^`/`.wedge()`→bivector, `.dual(2)`→`Vector(y,-x)`,
class consts `Vector.e_1`/`Vector.e_2`, and `plane_rotation(Vector.e_1, Vector.e_2)` from `gacalc.transforms`.
**No `.angle()`, no g2 `.cross()`** (cross is g3-only) — so `atan2` stays manual, and `Vector` is **not**
integer-indexable (the `_as_xy`/`get_hat` blockers above).

## Summary table (feeds the task)

| Item | File:line | Category | Confidence | Learning-stance note |
|---|---|---|---|---|
| Delete sprite rotation (`angle`/`draw_image(angle)`/`_rotate_z`) | actor.py:321-325; renderer.py:66,251 | B dead | High | Zero game users; also simplifies the matrix task |
| Delete `on_key_down/up` hook machinery | runner.py:125-224 | B dead | High | Keep press/release + Esc |
| Delete `Actor(**kwargs)`+`_DELEGATED` | actor.py:110,126-133,57-78 | B dead | High | Concrete 3-param `__init__` |
| Delete `geometry._VIRTUALS` | geometry.py:44-67 | B dead | High | Zero refs |
| Drop `draw_image(tint=…)` + collapse `_rgba` to int-RGB | renderer*.py | B dead | High | Fixes a known black-screen footgun |
| Drop unused joystick methods; literal key table | joystick.py; input.py:30-57 | B dead | High | — |
| `distance_to` → `(target-self).magnitude()` | actor.py:327-331 | C clarity | High | Matches games' own dialect |
| Anchor math → Vector translate/subtract | actor.py:150-179 | C clarity | High | Makes the anchor visible |
| Migrate eggzy/cavern velocity to Vector | eggzy.py:526+, cavern.py:148+ | C clarity | Medium | **Optional/pedagogical** — scalar-vs-vector side by side may teach well |
| Re-measure then likely delete `_offset_cache` | actor.py:103,145,156-165,237,298,307 | judgment | Medium | Was justified by the *old* impl |
| Keep all game duplication (`sign`, `draw_text`, `play_sound`) | across games | KEEP | — | Intentional pedagogy |
| Keep the two-renderer duplication, audio mixer, Rect tuples, mixed anchors, computed getattr | — | KEEP | — | Load-bearing / deliberate |

## Related

- **Category B (always-dead code) was removed 2026-09-04** — `tasks/archive/2026/09/04/pgzero-gl-remove-dead-code.md`
  (net −166 lines; verified: 104 tests pass, both renderers draw sprites headless). The corrections above
  (`joystick.init()`, `_Mixer.find_channel`/`get_busy` kept) held.
- `tasks/pgzero-gl-de-abstraction-options.md` — the remaining options (Group 2 gacalc clarity, Group 3
  judgment calls); Group 1 is the removal above.
- `tasks/gacalc-transforms-for-rotate-translate.md` — the renderer-matrix / GA-transform slice.
- Repo `CLAUDE.md` — "duplication across demos is deliberate" and "the graphics engine stays matrix-based".
