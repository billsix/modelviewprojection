# Tightening the Code-the-Classics games — the standard, the findings, the traps

**What this is:** the durable record of *how* the inlined Code-the-Classics games are tightened
(dataclasses + `__post_init__`, tighter functions, Protocols, the pygame-comment strip) and *why*
each choice was made — established on the **boing pilot** (`boing.py` + its `boing_gl1.py`
companion, 2026-09-05, a Fable session) and meant to be applied to the other nine games. Read it
before touching any game under `ports/codetheclassics/`. Work tracking lives in the umbrella task
`tasks/archive/2026/09/05/codetheclassics-tighten-games.md`; this doc states what is true. Project:
`github.com/billsix/modelviewprojection`.

**Status of the standard:** set by the boing pilot and **confirmed by the maintainer 2026-09-05**
(William Emerison Six <billsix@gmail.com>: "looks great"); it applies to the other nine games. Every rule
below that came from a maintainer instruction says so.

## 1. The shape of a tightened game (what boing looks like now)

Read `ports/codetheclassics/vol1/boing/boing.py` top to bottom; this is the target shape.

1. **Header + docstring.** BSD-2-Clause with dual copyright, read from
   `ports/codetheclassics/LICENSE` (vol 1: © 2019 Eben Upton <eben@raspberrypi.org>; vol 2:
   © 2024 Eben Upton <eben@raspberrypi.com> — note **2024**, not the 2020 an earlier task guessed);
   the inlined engine © 2026 William Emerison Six. This is the header pass the licensing task
   (`tasks/codetheclassics-licensing-after-shim-inline.md`) decided; it is folded into each game's
   tightening pass rather than run separately. The module docstring names the game, the pipeline,
   and the read-top-to-bottom layout — no "pgzero_gl inlined" framing.
2. **Plain section banners.** `# ===== engine: audio =====`, `# ===== engine: images and sounds
   =====`, `# ===== engine: renderer (OpenGL 3.3 core) =====`, `# ===== window and GL context
   =====`, `# ===== engine: sprite drawing =====`, `# ===== engine: keyboard =====`, `# ===== game
   code =====`, `# ===== main loop =====`. The old `# ===== pgzero_gl/<module>.py =====` banners
   are gone (decision: replace now, not at step 3 — they named a library the file no longer is).
   Each section opens with a comment saying what it does *for this game*; real rationale is kept
   (the one-device software mixer and why, lazy texture upload because game objects exist before
   the GL context, Pillow `convert("RGBA")` for palette transparency) and only the "this
   reimplements pygame" framing is dropped.
3. **Demo-style ordering, no `__main__` guard (maintainer, 2026-09-05).** Engine definitions →
   **window + GL context + renderer created at module level** (`renderer: SpriteRenderer =
   Renderer(WIDTH, HEIGHT)`; a failure raises and ends the program) → game code → the loop at the
   bottom. Exactly the demos' shape (`demos/demo07.py:38-47` creates its window at the top). The
   maintainer's question that settled it: *"is there any reason it would need to be checked if it
   existed every time?"* — no: the old `require_renderer()` guard existed only because the game
   objects were built at import while the window was created later under `if __name__ ==
   "__main__"`, a leftover of the framework era. Consequences: importing the file opens a window
   (nothing live depended on import-without-window — `_smoketest.py` was written for the shared
   shim and already cannot reach an inlined game's renderer), and the harnesses run the file as
   `__main__` (see §5). **Import guard (maintainer, 2026-09-05):** the window section opens with
   `if __name__ != "__main__": sys.exit(...)`, so a tool that imports the file to inspect it stops
   before any window, GL context or sound device is acquired (everything above that line is
   definitions plus lazy loaders). Note the demos themselves do NOT carry such a guard — they open
   their window at import — so this is a games-only convention for now.
4. **Only what this game uses.** boing dropped: `Context` (dissolved into `ASSET_ROOT` from
   `__file__` plus the module-level `renderer`), the `Drawable`/`RGBASource` protocols and the
   `Point`/`PointLike`/`Anchor`/`Color*` aliases, `Image.from_rgba/get_width/get_height`,
   `_Loader.__getattr__/values/clear`, `Sound.stop/set_volume/get_volume/fadeout` and the
   `loops`/`fade_ms`/`volume` play args, `_Music.play_once/get_volume/fadeout`, the mixer's fade
   ramps and buffer looping (`_Voice.fade_*`, `looping`, `start_fadeout` — boing never fades and
   only the music loops, which the stream generator does), `available()`, the renderer's flat
   colour methods (`fill/filled_rect/rect/line/polygon/circle/set_clip/_draw_prim/_rgba`) and the
   primitives VAO/VBO, `draw_image(src=…)`, the `_Keys` class and the `k_*`/modifier key table
   (the key table is now the seven keys boing reads), `_Mixer` and the `mixer.quit()/init()`
   boilerplate, the `_text = audio = sys.modules[__name__]` alias, the dead `sign()`.
   1854 → 1270 lines (−31%); `boing_gl1.py` 1724 → 1170.
5. **Dataclasses.** Engine state objects are `@dataclass(slots=True)` (`_Voice`, `_Engine`,
   `Sound`, `_Music`, `_Loader[T]`, `Keyboard`); game objects keep `eq=False` (identity
   semantics) and add `slots=True`. **Every attribute is a declared field** — that is what
   `slots=True` demands: `Bat.move_func` (was set in `__post_init__` undeclared) and `Bat.x/y`
   are `field(init=False)`; constructor-only inputs are `InitVar` (`Game.controls`,
   `Bat.move_func_init`); derived setup lives in `__post_init__` (`Game` builds its bats and
   ball there — the shape the maintainer asked for). `_Loader` became a PEP 695 generic
   (`class _Loader[T]`) so `images.load("ball")` is typed `Image` and `sounds.load(…)` is
   `Sound`. Traps: `__getattr__` + `setattr` caching is slots-incompatible (boing replaced the
   attribute idiom with `load()` outright); a class whose `__init__` consumes RNG or has a
   side effect must keep its statement order exactly when converted (see §4).
6. **Protocols, structural — copied per file, never extracted (maintainer, 2026-09-05).**
   `Sprite` (`x`, `y`, `image`, `update()`) is what the game loop needs of a bat, the ball, or an
   impact; `Game.sprites() -> list[Sprite]` is the one list update and draw both iterate.
   `SpriteRenderer` (`begin_frame`, `draw_image`) is the interface the 3.3 `Renderer` and the
   1.x `Renderer1x` both satisfy — it is the same text in both files, and only the concrete
   class differs, which is the point of the `diff boing.py boing_gl1.py` study. **Do NOT declare
   conformance by subclassing the Protocol.** Tested 2026-09-05 with `ty` on a copy of boing
   with `Impact.update` deleted: with `class Impact(Sprite)` ty reported **nothing** (the class
   inherits the protocol's `...` stub, so it structurally still "has" `update`); without the
   subclass ty reported exactly the right thing at the use site — *"protocol member `update` is
   not defined on type `Impact`"* at `Game.sprites`. So conformance is verified where an instance
   flows into the protocol-typed slot (`sprites()`'s return, the `renderer: SpriteRenderer`
   assignment), and the docstrings say so. Instances are typed at the level their users need:
   `bats: list[Bat]` (callers read `.score`/`.timer`), `ball: Ball` (`.out()`), `renderer:
   SpriteRenderer` (only the two methods).
7. **`match` always ends in `case _: raise` (maintainer, 2026-09-05).** Both `match state:`
   blocks end with `case _: raise ValueError(f"unhandled game state {state!r}")`, and a
   deliberately-empty arm is written out (`case State.PLAY: pass  # nothing drawn over the game
   while playing`) so every enum member is visibly handled. A missed case crashes loudly instead
   of falling through.
8. **Tighter functions.** Early-return control functions (`p1_controls`), conditional
   expressions for `x = default; if …: x = …` shapes, `[i for i in impacts if i.time < 10]` for
   the reversed-delete loop, f-strings, `sounds.load(f"{name}{randint(…)}")` instead of
   `getattr(sounds, …)`, `space_pressed = keyboard.space and not space_down`. The upstream
   teaching comments on the *game logic* (the ball physics essay, the AI weighting) stay
   verbatim; only pygame-framed comments were rewritten, keeping their rationale.
9. **Field documentation — comments, in Sphinx's `#:` form (recommendation).** The maintainer
   asked (2026-09-05) whether Python has a standard way to attach a description to a dataclass
   field instead of a comment. Researched: `dataclasses.field(metadata=…)` exists but the docs
   say it "is not used at all by Data Classes, and is provided as a third-party extension
   mechanism" (a read-only mapping for libraries like marshmallow/SQLAlchemy to hang machine
   data on — not prose; no editor, Sphinx or checker shows it); PEP 727 (`Annotated[T,
   Doc("…")]`) was **withdrawn** after a mostly negative reception, and `typing_extensions.Doc`
   survives only for backwards compatibility with no tooling behind it. The standard that *is*
   read by tooling is Sphinx autodoc's attribute doc-comment: `#: description` on the line(s)
   above the field (or a string literal right after it). The engine already uses it
   (`_Voice.pos`). **Decision (maintainer, 2026-09-05): keep field descriptions as comments and
   spell them `#:`** so they double as documentation; reserve `field(metadata=)` for machine-read
   data. Applied to boing/boing_gl1 (every dataclass field with a description, engine and game);
   every game does the same. Sources: https://docs.python.org/3/library/dataclasses.html,
   https://peps.python.org/pep-0727/, https://github.com/python/typing_extensions/issues/443.

### 1a. The Actor hierarchy (settled on cavern, 2026-09-05)

`Actor` stays a **plain class with `__slots__`**, not a dataclass: its setup is ordered (load the
image, size the rect, then place the anchor) and a dataclass base would push its `InitVar`s into
every subclass's generated `__init__` and `__post_init__` signature. Intermediate classes with
behaviour-only constructors (`CollideActor`, `GravityActor`) are plain and slotted; a constructor
that consumes RNG in a branch (`Fruit`) stays plain with a comment saying why; the leaf game
classes are `@dataclass(eq=False, slots=True)` with **every attribute declared** (attributes an
old `reset()` used to invent become `field(init=False)`). Zero-arg `super()` inside a slotted
dataclass works on the container's Python 3.14 (it raised before 3.14 — verified). A base
`update(detect=True)` whose overrides ignore `detect` becomes `update()` + `fall(detect)`, so no
override carries a dead parameter. A `GameObject` Protocol (`update`, `draw`) types the per-frame
object lists. `Game.player` is honestly `Player | None` (the menu's attract mode has none) with
`assert … is not None` at the two play-only sites, instead of a `cast` lie.

**Why not make Actor and every subclass a dataclass? (maintainer's question, 2026-09-05,
settled on bunner.)** It is possible, but most constructors in these hierarchies are *computations
of the base class's inputs*, not field lists: `Row(base_image, index, y)` derives the image name,
position and anchor from its own arguments; `Car(dx, pos)` picks its image with `randint`; `Rock`
picks its anchor from a flag. A dataclass base passes its `InitVar`s straight through from the
caller, so each such subclass would need sentinel defaults on the base's `InitVar`s and then redo
the image and position in its own `__post_init__` after the base already ran — more machinery than
the hand-written `__init__` it replaces, and RNG-order-sensitive. The line drawn: **a leaf that is a
bag of fields plus derived setup is a dataclass; a class whose constructor computes the base's
inputs stays a plain slotted class.** The maintainer can overrule this per game.

**The vol1-rich additions (bunner, 2026-09-05).** The splice script's `-` keyboard mode gives a
code-indexed `keyboard[code]` (no name table) for games that read keys by GLFW code; bunner then
patches in looping/volume/stop sounds, a Pillow `draw_text`, an outline `Renderer.rect`, and
`Image.from_rgba`. **Shim bug found:** the old `screen.draw.text(text, pos)` took its second
positional argument as `surf`, so positional `pos` was silently dropped and text landed at (0, 0)
— bunner's debug row labels had never been drawn. Fixed in the tightened file; check the other
games that call `screen.draw.text` positionally (soccer, beatstreets, leadingedge) for the same.

### 1b. GL-resource classes: a dataclass of state built by a factory (maintainer, 2026-09-05)

A hand-rolled `__init__` that computes a dozen attributes from one or two inputs (compile and
link a program, query its uniforms, upload a quad) is split in two: the **factory** is the
computation phase and the **dataclass** is the resulting state, every field declared. Related
variables get their own named dataclass so the top level stays short: `Uniforms` (seven
locations, was `u_*`), `GLBuffer` (a VAO + its VBO). `Renderer` is
`@dataclass(slots=True, eq=False)` — `eq=False` because GL handles compared by value are
meaningless; not frozen because `fb_width`/`fb_height` change every frame — and
`Renderer.create(width, height)` does the GL calls in exactly the old order, then constructs.
`Image` is a dataclass of `rgba` plus the lazy `_tex`, `width`/`height` are properties, and
`Image.load(path)` / `Image.from_rgba(arr)` are its factories (vol2: `Surface.create(...)`,
`Mask.from_image(...)`). The fixed-function `Renderer1x` gets its own `create`, so `boing.py` and
`boing_gl1.py` share the same window line. Done by the idempotent codemod
`tasks/adhoc/codetheclassics-tighten-games/renderer_dataclasses.py` (re-running it on a converted
file is a no-op), verified frame-identical on all six games. This is also the answer to §1a's
"constructors that compute the base's inputs": the computation moves to a factory. Applying that
to the Actor hierarchies (bunner's rows, myriapod's `Rock`) is a candidate follow-up, not done.

**The factories are `@classmethod`s on their classes (2026-09-06,
`tasks/archive/2026/09/06/ctc-factory-classmethods.md`).** The maintainer asked how to signal
"use the factory, not the constructor"; Python has no private constructors, and the standard
signal is the classmethod alternative constructor (`dict.fromkeys`, `datetime.fromtimestamp`,
`Path.home()`): the entry point lives on the type, autocomplete shows it, and the class docstring
says "build one with `X.create(...)`; the constructor takes already-made GL objects" — which stays
public on purpose (tests, or another backend, may pass their own). Rejected: `init=False` + a
hand-written `__init__` (what the factory split left behind), a sentinel `InitVar` checked in
`__post_init__` (enforcement theatre; breaks `dataclasses.replace`), underscore-prefixing the
class (it is the annotation type everywhere). Private helpers (`_link_program`, `_make_buffer`)
and transformations (`scale_image`) stay free functions.

## 2. Deliberately NOT changed in boing (and why)

- ~~`Image` and `Renderer`/`Renderer1x` keep their hand-rolled `__init__`s.~~ **Superseded
  2026-09-05:** the maintainer decided the shape — see §1b below — and it is applied everywhere.
- **The shader keeps its flat-colour branch** (`uUseTex`/`uTint`) even though boing only draws
  untinted sprites — so boing's renderer stays the same program the richer games run. A comment
  says so. Cutting it is a renderer decision, not a tightening one.
- **`PGZERO_MAX_FRAMES`** keeps its name: it is the headless harness's contract, an identifier.
- **`x`/`y` scalars on the sprites** (not a `Vector` position): the step-2 decision for boing; the
  scalar-vs-Vector contrast across games is deliberate teaching (see
  `tasks/reference/pgzero-gl-design-for-a-personal-learning-library.md`).
- **The three-step ball deflection** (`Vector(-x, y)` → deflect → clamp → normalize) stays as
  three rebindings with their teaching comments; merging them buys nothing legible.

## 3. The engine-family finding — tighten the engine once per family, then splice

The 2026-09-05 read of all ten games (three parallel readers, `file:line`-anchored) found the
inlined engines are **byte-identical within families**, differing only in the game name in a
handful of doc lines and in the one `_text = audio = … = sys.modules[__name__]` alias line:

| family | games | engine sections carried |
|---|---|---|
| vol1-minimal | cavern ≡ myriapod (lines 1–1936 identical) | `_types geometry context audio resources renderer screen actor input __init__` |
| vol1-rich | bunner, soccer | + `surface draw text` (bunner: richer `Screen`/`_Mixer`) |
| vol2 | eggzy ≡ beatstreets ≡ leadingedge (identical modulo a 1–3 line offset); kinetix, avenger the same set with `mask transform joystick` | + `mask transform joystick`, `_MixerSound` |

Consequence for method: **the engine half of a family is produced by a script, from boing's**:
`tasks/adhoc/codetheclassics-tighten-games/splice_vol1_engine.py <name> <Title> <keys>` builds the
vol1-minimal engine (boing's tightened engine + a float `Rect` dataclass + the slotted `Actor`),
parameterised only by the game name, window title and the key names the game reads; cavern was
built that way (2026-09-05) and myriapod reuses it. Hand-tighten only the game halves. The family
engine carries the UNION of its games' needs (e.g. `Actor.anchor`'s setter is myriapod's, not
cavern's) — that union is exactly what step 3 will find shared. This
also matters for step 3 of `tasks/pgzero-gl-inline-strip-reextract.md` (re-extract the shared
library): what is "genuinely shared in the same shape" is already visible per family.

Two per-game exceptions the reader census found and the splice must respect: **leadingedge is the
only game that uses `Sound.play(loops=…, fade_ms=…)`, `Sound.fadeout/set_volume`** (so the mixer's
fade/loop paths that boing dropped must stay there), and **avenger is the only game that built
`mixer.Sound(...)`** — it did so only for a per-play volume, so `_MixerSound` was dropped there
(2026-09-05) in favour of `Sound.play(volume=…)`. bunner is the only vol1 game using `Sound.play(-1)`,
`set_volume`, `stop` and the `keys.*` constants.

**vol2 (2026-09-05, kinetix):** `splice_vol2_engine.py <name> <Title> <keys|-> <WxH> <flags>` builds
the vol1 family engine plus flag-selected sections: `surface` (a `Surface` dataclass SUBCLASS of
`Image` with CPU `fill`/`blit`/`set_alpha` and a dirty re-upload, built by `Surface.create`),
`joystick` (`Joystick` dataclass over the GLFW id, `joystick_count()`), `clip` (`Renderer.set_clip`).
avenger (2026-09-05) added `sound` (the full mixer sound API: loops, fade-in/out, per-play
`volume=`, `stop`, `_Music.fadeout`), `mask` (`Mask` + `Mask.from_image`) and `lines`
(`Renderer.line` with its own `prim` buffer); `set_clip` takes floats. eggzy added `collide` (a
`RectLike` edge Protocol, `Rect.colliderect`, the whole-pixel mutable `IntRect`, `Actor.colliderect`/
`distance_to`/`centerx`/`centery`), `fill`, `rect` (filled + outline) and `region`
(`draw_image_region`, one tile of a tileset). leadingedge added `polygon` (`Renderer.polygon`,
fan or loop on the `prim` buffer), `scale` (`scale_image`, nearest-neighbour) and `text`
(`draw_system_text`, the Pillow debug text), and the key table learned `lctrl`/`lshift` aliases. The trace comparator `compare_traces.py` replaces the `sed` normalisations:
it compares dumps structurally, ignoring named keys and collapsing named classes.

## 4. Traps found by the analysis (cross-cutting; per-game detail is in each step-task)

- **RNG-order-bearing constructors.** Several `__init__`s consume `random` in a branch-dependent
  order (cavern `Fruit`, myriapod `FlyingEnemy`/`Rock` — `Rock` also plays a sound while
  constructing; avenger `Enemy` — five RNG calls interleaved with `match`; leadingedge `CPUCar`;
  kinetix `Barrel` reads global game state before `choice()`). Converting these to
  `@dataclass` + `__post_init__` must keep the statement order exactly, or leave them alone and
  say why. The state trace (§5) is the proof either way.
- **`Game()` runs at import** in most games, often consuming RNG (cavern `next_level` →
  `shuffle`; leadingedge builds the whole attract-mode race; bunner loads images and reads
  `high.txt` from the CWD). Any reordering of that constructor is behaviour-visible; the harnesses
  seed before import, so they catch it.
- **Undeclared attributes block `slots=True`.** Existing `@dataclass(eq=False)` game classes set
  attributes outside `__post_init__` (cavern `Player.reset()` sets six; eggzy `Player` four;
  kinetix `Bat.shadow`/`portal_animation_active`; beatstreets `Attack.flying_kick`; avenger
  `Player.thrust_sound`). Declare them as fields (with `field(init=False)`/defaults) before
  adding `slots=True`, or the first assignment raises `AttributeError`.
- **`_Loader.__getattr__`'s first-touch `setattr` caching** is slots-incompatible and is what the
  `images.<name>` attribute idiom rides on (leadingedge ×24, beatstreets, kinetix, avenger use
  it; the vol1 games mostly go through `screen.blit(name)`/`getattr`). Either keep `_Loader`
  un-slotted or switch the game to `load()` (boing did the latter).
- **Dead-only-because-of-a-debug-flag code.** bunner's `screen.draw.text`, `screen.surface`,
  `gldraw.rect` and `Rect` are referenced only under `DEBUG_SHOW_ROW_BOUNDARIES = False`;
  soccer's `screen.draw.text` only under `DEBUG_SHOW_COSTS`. Deleting the engine behind them
  silently deletes a debug feature — decide, don't discover.
- **`mixer.find_channel()` returns `None` on purpose** (a known graceful gap), so beatstreets'
  whole scooter-engine channel path (`EnemyScooterboy`, ~130 lines) is dead at runtime.
- **`update(dt)` arity:** leadingedge is the only game whose `update` takes a delta; its loop
  passes `_dt`.
- **`# ty: ignore` suppressions in the game halves** exist (soccer/bunner/avenger
  `invalid-method-override` on widened `draw()`; bunner `scroll_pos`; eggzy `:4241`; beatstreets
  ×5) — a tightening pass should try to remove the *cause*, not carry them forward.

## 5. Verification — the harnesses (promoted to `tools/` on 2026-09-05 when the umbrella archived)

- **`tools/ctc_verify_game.sh <game.py> [frame] [ref]`** — frame-N pixel identity of the working tree vs a
  committed baseline (`git show <ref>:<game>` written beside the game so assets resolve),
  baseline captured twice (determinism check) then the working file, compared with ImageMagick
  `AE`. `--against <other.py>` compares two working-tree files (boing vs boing_gl1). Reuses the
  step-1 `capture_frame.py`. Covers **the no-input attract mode only**.
- **`tools/ctc_state_trace.py <game.py> <frames> <keyscript> [skip]`** — the input-path complement: seeds
  `random`, stubs `miniaudio` (its device open can block headless), runs the file as `__main__`
  with `glfw.window_should_close` patched to `True` (window + renderer get built, zero frames run),
  then drives `update()` for N frames while scripting key presses, dumping a canonical
  snapshot of `state`/`num_players`/`game` (sorted union of dataclass fields, `__dict__` and
  `__slots__`, enums by name, vectors by coordinates, callables by name) after every frame. Diff
  the dumps for baseline vs working tree. Since 2026-09-05 (bunner) the dump also includes every
  public **property** of an object (an Actor's `x`/`y`/`pos`/`image` live behind properties, so
  earlier dumps compared only declared attributes), dict/set contents, and the class name — when a
  tightening drops a derived property (bunner's `left`/`centerx`/`centery`) or a dead attribute,
  strip those keys from the baseline dump with `sed` before diffing, and say so in the record.
  Since eggzy/leadingedge the harness puts the game's directory first on `sys.path` (games find
  their data files there), passes `1/60` to an `update` that takes a delta, dumps g3 vectors with
  their z, and takes a fourth argument of attribute names to leave out (`track` for leadingedge's
  3000 pieces); a game that prints to stdout pollutes its dump — keep only lines starting with a
  frame number (`grep -E '^[0-9]+ '`).
- **`tools/ctc_compare_traces.py base.txt cur.txt [--ignore k,…] [--opaque Class,…]`** — the
  structural comparator (replaced the `sed` normalisations from kinetix on): parses each frame's
  dict, drops the named keys anywhere in the tree, collapses objects of the named classes to their
  class name, and reports the first differing path. Typical ignores: the rect-derived keys when an
  int `Rect` became `IntRect` (`x,y,w,h,right,bottom,center*,mid*,size,class`), attributes newly
  declared as dataclass fields (they appear from frame 0), and `Image`/`Surface`/`Sound` opaque.
  Strip the title-screen `'game': None` from the baseline first when the tightened game leaves
  `game` unbound until the first start.
  Needs `DISPLAY` (the sandbox's Xvfb). Pick a key script
  that actually reaches the code you changed — boing's first script never made a bat hit the
  ball (0 impacts); the second one covered MENU→PLAY, 72 impact frames, 7 AI offsets, ball speed
  to 9, scores to 7.
- boing's record: frame 180 AE=0 for `boing.py` vs HEAD, `boing_gl1.py` vs HEAD, and
  `boing_gl1.py` vs `boing.py`; 1500-frame input trace byte-identical across all three; ruff +
  `ty check ports/codetheclassics/vol1` clean (`make format` was red at the time on 36 gacalc-
  invariance diagnostics in `src`/`tests`; green since the gacalc 0.0.19 pin, 2026-09-06 —
  `tasks/archive/2026/09/06/ty-0072-strictness-sweep.md`).
- **What the harnesses cannot prove:** audio (the mixer paths boing dropped) and real-hardware
  GL. Those need the maintainer's play-test, as with steps 1–2.
- **Environment lore:** the sandbox's Xvfb wedges after several captures (`CAPTURE-FAIL` with a
  SIGKILLed container) — restart it (`pkill -x Xvfb; Xvfb :99 …`) and rerun; nested shell quoting
  silently emptied a key script once (pass scripts via a mounted file, not nested `-c` strings).

## 6. Outcome (2026-09-05) — numbers, deviations, and what step 3 inherits

| game | lines before | after | change | pygame/pgzero mentions left |
|---|---|---|---|---|
| boing | 1854 | 1367 | −26% | 2 |
| boing_gl1 | 1724 | 1222 | −29% | 2 |
| cavern | 2971 | 2010 | −32% | 2 |
| myriapod | 3081 | 2119 | −31% | 2 |
| bunner | 3583 | 2248 | −37% | 2 |
| soccer | 3886 | 2620 | −33% | 2 |
| kinetix | 4124 | 2653 | −36% | 2 |
| avenger | 4456 | 2989 | −33% | 2 |
| eggzy | 4727 | 3326 | −30% | 4 |
| leadingedge | 5151 | 3784 | −27% | 2 |
| beatstreets | 6022 | 4749 | −21% | 3 |
| **all eleven files** | **41579** | **29087** | **−30%** | (the `PGZERO_MAX_FRAMES` env var, plus the int-Rect rationale in eggzy/beatstreets) |

**Per-game engine flags** (the vol2 splice's, the map of what each game actually uses — step 3's
"genuinely shared in the same shape" question starts here): kinetix `surface,joystick,clip`;
avenger `joystick,clip,sound,mask,lines`; eggzy `joystick,collide,fill,rect,region`; leadingedge
`joystick,surface,sound,fill,polygon,scale,text`; beatstreets
`joystick,surface,region,rect,lines,circle,text`. vol1: cavern ≡ myriapod (minimal); bunner and
soccer add `rect`, Pillow text, looping/volume sounds, code-indexed keys. Every game: the mixer,
`images`/`sounds` loaders, the renderer's `begin_frame`/`draw_image`, `blit`, `Actor`, keyboard.

**Deliberate deviations from the pre-tightening HEAD (all shim bugs, none in game logic; the maintainer
play-tested all ten games 2026-09-05, "seem good to go"):** leadingedge's and
beatstreets' fades (the shim's `set_alpha` scaled pixel alpha in place; `fill` after it reset the
surface to opaque, or the scaling compounded frame to frame) now fill-then-scale each frame, i.e.
the fade upstream's pygame produces; bunner's debug labels draw (the old
`screen.draw.text(text, pos)` took `pos` as a surface). Everything else is pixel- and
state-identical; the records name what each trace did and did not reach (audio and the gamepad are
never covered — play-test).

**Traps the pass hit, for whoever edits these files next:** a dataclass field named `pos`/`anchor`
shadows the Actor property (the repo test `tests/test_ctc_actor_field_collisions.py` catches it —
use `spawn_pos`/`spawn_anchor` InitVars); gacalc vectors are rejected as dataclass defaults
(`default_factory`); `slots=True` on a leaf whose base has no `__slots__` is pointless (slot the
whole chain, or don't); a `match` on an enum with a `case _: raise` turns a silently-ignored state
into a crash — write the deliberate `pass` arms; `Game`'s `player`-less attract-mode game exists
only in leadingedge; the loop-carried `prev_*` pattern in leadingedge's draw is a dataclass in
disguise (`TrackPieceScreen`).

## Related

- `tasks/archive/2026/09/05/codetheclassics-tighten-games.md` — the umbrella (per-game checklist, decisions log, completion record).
- `tasks/archive/2026/09/05/codetheclassics-tighten-boing.md` — the pilot's work record (archived after sign-off).
- `tasks/reference/library-not-framework-authorship-style.md` — why demo style is the target.
- `tasks/reference/pgzero-gl-design-for-a-personal-learning-library.md` — the shim's design and
  the per-game usage slices (still the map for "what does this game use").
- `tasks/archive/2026/09/05/pgzero-gl-dataclasses-investigation.md` — the `Image`/`Renderer` shape question.
