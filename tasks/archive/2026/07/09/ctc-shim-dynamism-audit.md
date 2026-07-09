# CTC: audit the shim's dynamism against the 10 games' real uses; make the basics static

**Status:** DONE 2026-07-09, archived (Bill: "yes it's done").
The one open thread — leadingedge's clunky engine audio + freeze —
is deliberately split out and lives on in
`tasks/leadingedge-audio-clunk-and-freeze.md` (confirmed present).
**Created:** 2026-07-09 (Bill)

## Design revisit + follow-up pass (2026-07-09, all landed)

- **Trimmed the 12 unused rect delegations** (right, topleft, topright,
  bottomleft, bottomright, midtop, midbottom, midleft, midright, size,
  w, h — zero call sites in the audit); kept `angle` (core pgzero draw
  API, one float) and the used 13. Actor now has 14 properties, matching
  the shim's subset charter.
- **New guard test** `tests/test_ctc_actor_field_collisions.py`:
  AST-scans every Actor-rooted dataclass against Actor's property names
  (both scanned, no imports/GL) — makes the spawn_pos rule mechanical.
- **Dataclass design verdict**: the InitVar + __post_init__ pattern
  survives unchanged; kept-manual classes stay manual (kinetix Ball's
  reason got STRONGER: x/y fields would now collide with properties);
  Actor stays a plain class (its state is derived, not field-like); no
  __slots__ (post-init attrs like Door.opening need __dict__; the 84x
  win came from deleting __setattr__, not layout).
- **`Actor.pos` returns a gacalc Vector2**; setter unchanged (unpacks).
  Anchor offset is memoized (invalidated by anchor/image/width/height
  setters). Games: avenger's pos-indexing -> .x/.y, radar_pos unpacks,
  and 14 `Vector2(*a.pos)` wrap-dances collapsed to direct algebra —
  `self.pos = self.pos + self.velocity`, `player_vec = game.player.pos
  - self.pos`. Position-pair annotations on ctors/InitVars widened to
  `tuple[float, float] | Vector2` (cavern/myriapod import gacalc now).
- **Bench** (ns, container): a.x read 292 -> 115 (was ~700 pre-audit);
  a.x write 786 -> 398; pos read 295 -> 188 (now building a Vector2!);
  plain-data write 10; delegated read 25.
- eggzy/cavern per-axis velocities re-examined: stay scalar (per-axis
  physics IS the algorithm) — closes the follow-up's open question.
- Gates: ty all-clean, ruff clean, mvp pytest 64 (incl. the 2 guard
  tests), 10/10 definitions gate, Vector2-pos contract suite.



## Second Vector2 survey round (2026-07-09, Bill: "do everything you recommend")

- ~11 offset-arithmetic-in-tuple sites converted to vector expressions
  (kinetix shadows/bullets `self.pos ± Vector2(...)`, avenger
  carried-human + thrust sprite, boing impact, cavern robot fire).
- **soccer's camera offset is a Vector2 end to end**: the
  split-into-scalars/rebuild dance is gone — `MyActor.draw(offset)`,
  `self.pos = self.vpos - offset`, `screen.blit("pitch", -offset)`.
  (avenger/bunner offsets deliberately stay scalar: genuinely 1-D
  scroll designs.)
- `Actor.distance_to` now measures via `(self.pos - Vector2(...)).magnitude()`.
- Position annotations widened where vectors now flow (kinetix Bullet).
- **Unrelated pre-existing bug fixed en route**: pyGLFW returns joystick
  state as a `(ctypes_pointer, count)` tuple; the shim's `list()` of it
  yielded `[pointer, count]` and the pointer leaked into the d-pad
  bit-math (avenger crash with a controller attached). New
  `_read_glfw_array` helper unpacks it (axes/buttons/hats); verified
  against real ctypes shapes.
- Also this round (boot-pass catches): avenger `hit_test` param unpack;
  eggzy `save_replays` unpack — the latter was SILENT replay data loss
  (the write is inside a swallow-all except).
- Gates: ty all-clean, ruff clean, 64 pytest, 10/10 definitions gate.
- **Second pre-existing gap fixed (Bill's boot pass)**: the `mixer`
  stand-in's `Sound` stub had no `set_volume` and played nothing —
  avenger's distance-attenuated sounds (every quiet enemy laser) were
  silently dropped into its print-and-continue handler. `mixer.Sound`
  is now a real wrapper over the pooled audio backend: one decoded
  `audio.Sound` per file (lru by path — a naive instance-per-call would
  leak miniaudio streams, per audio.py's no-finalizer warning), with
  the wrapper's volume applied PER PLAY to that play's voice
  (`audio.Sound.play(volume=...)` grew the override), preserving
  pygame's per-instance-volume semantics leak-free. Contract-tested
  against avenger's real assets in-container.

## Audio round (2026-07-09, from Bill's leadingedge session: clunky acceleration + a freeze)

Root cause for both: the shim's ``fadeout``/``fade_ms`` were fake — an
immediate ``stop()`` and an ignored parameter. leadingedge crossfades
between **40 looping engine samples** as speed changes
(``old.fadeout(150)`` + ``new.play(loops=-1, fade_ms=100)`` per band
change), so every band transition was a hard cut (the clunk), and a
speed hovering at a band boundary flapped stop()/play() on live
miniaudio streams every few frames — rapid stream stop/start storms,
the prime suspect for the freeze — **DISPROVEN 2026-07-09: both
symptoms persist after the fade engine** (Bill's retest). The follow-up
investigation lives in `tasks/leadingedge-audio-clunk-and-freeze.md`
(compare against git history / upstream, per Bill); the fade engine
stays (correct pygame semantics regardless).

Fix: a real fade engine in audio.py — a ~50 Hz daemon thread ramping
voice volumes; ``fade_ms`` ramps a play up from silence,
``Sound.fadeout(ms)``/``music.fadeout(s)`` ramp to silence then stop
ONCE at ramp end. Transitions now touch only ``set_volume`` on
already-playing voices — zero stop/play churn. Stale-ramp hygiene:
plays/stops/music-restarts cancel pending jobs on their voice.
Unit-tested (ramp down+stop, ramp up, cancel); ty/ruff/defs gates green.

Known remaining best-effort gap (graceful, logged not fixed):
``mixer.find_channel()`` returns None, so beatstreets' scooterboy
engine channel is silently absent (the game guards for it).

## Runtime results (all 10 games, ~5 min of play; dumps kept in .instrumentation/)

- **3.87M + 680k (kinetix) Actor dynamic-dispatch events**; peak
  47.5k/sec (bunner), 29.7k/sec (avenger).
- Reads (2.5M): **x + y = 93%**; then pos, and only 8 of the 20
  delegated rect names (left/top/center/width/bottom/height/centerx/
  centery). `angle`/`anchor` never read. **ZERO open-world reads**
  (getattr-MISS count: 0 across every game).
- Writes (1.6M): x/y/pos/image = 74%; the other 26% (415k) spread over
  ~165 plain data-attribute names (timer, vpos, vel_y, anim_frame, ...)
  — ordinary subclass state paying the full string ladder.
- keyboard.getattr ~95k total but only ~360/sec — not hot. keys trivial.
- resources.images __getattr__: 149k trips (leadingedge fonts/billboards
  per frame — same ~200 names re-resolved forever).

## The rewrite (landed with this task)

- **Actor: `__getattr__`/`__setattr__` DELETED.** The six magic names
  and all 20 rect delegations are real static properties (all 20 kept
  for pygame API parity; as descriptors the unused ones cost nothing).
  Subclass data attributes now hit the instance dict natively.
- **resources: first-touch caching** — `__getattr__` binds the loaded
  resource as a real instance attribute, so repeat `images.font048`
  accesses never re-enter the dynamic path.
- **keyboard/keys: kept dynamic** (data: not hot; names genuinely open).
- Instrumentation module + all hooks removed.
- **Microbenchmark (container, 100k reps):** plain data write
  844 → 10 ns (**84x**), delegated read 484 → 27 ns (**18x**),
  x write 1287 → 786 ns, pos read 741 → 295 ns.
- **The typed surface caught 20 real latencies immediately**: soccer's
  kickoff wiring (`peer`/`mark`/`lead`) was assigned cross-object and
  never declared — now explicit class annotations; `Actor.image` is now
  `-> str` (the games always use name strings), which also fixed
  `self.image + "_shadow"` (beatstreets), `+= "f"` (kinetix), and
  `getattr(images, self.image)` (eggzy) diagnostics.
- Gates: ty **All checks passed** over pgzero_gl+vol1+vol2 (with real
  gacalc 0.0.8), ruff clean, mvp pytest 62, 10 games compile, Actor
  behavioral contract suite (anchors, rect delegation, image swap
  keeping pos, gacalc-vector pos, AttributeError on unknown reads).

### Post-rewrite incident (2026-07-09, caught by Bill's boot pass)

cavern and avenger crashed AT CLASS DEFINITION: dataclasses treats any
class attribute as a field default, so the new `pos` PROPERTY on Actor
became the "default" for every subclass's `pos: InitVar` field ->
"non-default argument follows default argument". Fix: the InitVar is a
constructor argument, not the attribute -- renamed to `spawn_pos` in all
16 dataclasses (7 games), with a comment at each explaining why; no
keyword callers existed (`pos=` only reaches Actor's own __init__).
Gate hole closed: `py_compile` doesn't EXECUTE class bodies, so the
gates now include a **definitions gate** -- run every game module with
`pgzero_gl.runner.go` stubbed to a no-op (executes all module-level
code and class definitions headless, skips the window):
`runpy.run_path(game, run_name="__main__")` after
`pgzero_gl.go = pgzero_gl.runner.go = lambda *a, **k: None`.
All 10 games pass it; ty + ruff re-verified clean after the rename.

Answer to Bill's original "why so much dynamism": upstream pgzero is
built for beginners — open-world attributes so nothing needs declaring.
The games' attribute surface is closed; the machinery was pure overhead
here. (Note for the record: my nested sandbox image still had gacalc
0.0.7 during gating — ~200 phantom `Vector2.x` ty errors until the gate
container pip-installed 0.0.8. Bill's rebuilt host image is fine.)

## Instrumentation (in place, marked DEV-INSTRUMENTATION — remove with this task)

- `pgzero_gl/_instrument.py` + one-line `record()` hooks in
  `actor.py` (`__getattr__`, `__getattr__` miss, `__setattr__`,
  `__setattr__` open-world FALLTHROUGH), `input.py` (keyboard/keys
  `__getattr__`), `resources.py` (images/sounds `__getattr__`).
- On interpreter exit each game writes
  `ports/codetheclassics/.instrumentation/<game>-<ts>.tsv`
  (kind, attr, count, count/sec; dir gitignored) and prints
  `[shim-dynamism-audit] wrote ...` to stderr. Quit normally (window
  close / crash both fine; SIGKILL loses the dump).
- **Play-session prerequisite: gacalc 0.0.8 must be released and the
  mvp image rebuilt first** — kinetix now imports `plane_rotation`,
  which is not in the venv's 0.0.7.
- Bill: play all 10 games — menus, gameplay, deaths, level transitions.
  Multiple sessions fine (files are timestamped). Then hand back to
  Claude for analysis.

## Static AST scan results (2026-07-09, .instrumentation/static-scan.tsv)

Across the 9 Actor-using games (leadingedge subclasses nothing):

- Of Actor's 6 magic names, games use **x, y, pos, image** everywhere,
  `anchor` in 2 games — `angle` NOWHERE.
- Of the 20 `_DELEGATED` rect names, games use only **6**: `bottom`,
  `center`, `centerx`, `centery`, `top`, `left`, `width` — 14 delegations
  have zero static call sites.
- **~220 distinct open-world attribute names** on Actor subclasses
  (plain data fields + methods; runtime run will separate and weight
  them) — every one of those writes walks the full string ladder to the
  FALLTHROUGH branch today. This is the smoking gun for the hypothesis:
  the games' attribute surface is closed and enumerable.


## Goal (Bill)

Determine why there is so much dynamism in the Python objects — the
PyGame Zero shim (`pgzero_gl/`) especially — and determine, based off
the uses of the 10 games, whether it's actually needed. If it's not,
rewrite it so basic stuff is NOT dynamic dispatch (which it does
excessively today). Afterwards (separate pass, below), take a second
look at turning more x/y-based stuff into 2D GA vectors.

## Where the dynamism lives (inventory, 2026-07-09)

- **`actor.py` (the big one — 18 dynamic-dispatch sites).** `Actor`
  routes EVERY attribute read through `__getattr__` and every write
  through `__setattr__`: string-compares for `x`/`y`/`pos`/`angle`/
  `image`/`anchor`, then a `_DELEGATED` set of ~20 rect attributes
  forwarded via `getattr`/`setattr` to the underlying `ZRect`, then a
  fallthrough. Every `self.x += ...` in every game, every frame, walks
  this ladder — and the games' own dataclass fields on Actor subclasses
  also pass through it on every assignment (including in `__init__`).
  This is why so much of the shim is typed `Any` (~15 in actor.py alone;
  the docstring says so explicitly) — `__getattr__` erases the type
  surface, which also degrades what ty can check in all 10 games.
- **`geometry.py` Rect/ZRect**: mostly REAL properties (static
  descriptors — fine), but `_set_pair` goes through
  `setattr(self, name, ...)` with string attribute names, and the
  `_VIRTUALS` set exists to support Actor's delegation.
- **`input.py` keyboard/keys**: `__getattr__` mapping attribute names to
  key constants (e.g. `keyboard.left`).
- **`resources.py` images/sounds**: `__getattr__` mapping attribute
  names to files on disk (`images.blank`, `sounds.jump0`).
- **`context.py`, `surface.py`**: one-off dynamic lookups.

Hypothesis: pgzero upstream is designed for *teaching children* — the
dynamic attribute magic exists so `alien.x = 42` and `images.alien`
"just work" with zero declarations, and so arbitrary user attributes can
be set on actors. Our 10 games are a CLOSED, known corpus: every
attribute they touch is enumerable, so the open-world machinery is very
likely unneeded — but that's exactly what the instrumentation should
prove rather than assume.

## Methodology (Bill's protocol): run, play, instrument

1. **Instrument** (Claude): wrap `Actor.__getattr__`/`__setattr__` (and
   the input/resources `__getattr__`s) with counters keyed by attribute
   name — per game, per frame — plus a "fallthrough" bucket for
   anything reaching the generic paths that isn't in the known lists
   (that bucket is the "do the games need open-world attributes?"
   answer). Cheap enough to leave on while playing; dump the table on
   exit (atexit → a per-game file under a gitignored scratch dir).
   A static AST cross-check (every attribute name the games access on
   Actor-typed objects) complements the runtime numbers.
2. **Run + play**: Claude runs the games (needs display — Bill plays
   each of the 10 long enough to hit gameplay, deaths, level
   transitions, menus). Runtime tells us frequency (what's hot); the
   AST scan tells us totality (what exists at all).
3. **Decide from the data**, attribute by attribute:
   - names the games use that map to fixed concepts (`x`, `y`, `pos`,
     `angle`, `image`, `anchor`, the used subset of the rect
     delegations) → **real static properties** on Actor (descriptors
     resolve in C, no string ladder), plus `__slots__` where possible;
     `__getattr__`/`__setattr__` removed or reduced to an assertion
     shim during transition.
   - the fallthrough bucket: if (as suspected) the games set plain data
     attributes on subclasses, those become declared dataclass fields
     (most already are, post ctc-dataclasses) — then nothing needs the
     open-world path at all.
   - `images.*` / `sounds.*` / `keyboard.*`: name→resource lookup is
     inherently string-keyed; keep `__getattr__` there unless the audit
     shows a small closed set worth pre-declaring. These are not
     per-frame-hot (resources cache; keyboard is per-poll) — decide on
     evidence, not principle.
4. **Rewrite** the proven-static parts; gates: format.sh (ruff + ty —
   expect ty coverage to IMPROVE as `Any` shrinks; this overlaps the
   open `ctc-more-types` question about the shim's ~100 `Any`s),
   pytest, 10-game compile, and a before/after of the same
   instrumentation run to show the ladders are gone. Perf note: this
   compounds with gacalc's dispatch work (geometricalgebra
   `tasks/generated-dispatch-fast-paths.md`) — attribute routing is the
   shim-side half of the per-frame overhead story.

## Follow-up pass (after the de-dynamism work): more x/y pairs -> 2D vectors

Revisit the 2026-07-09 x/y→Vector2 survey with the new shape in hand.
That survey converted three (boing ball `dir`, kinetix `brick_collide`,
soccer position predicates) and declined the rest — but two of the
"declined" reasons may change once Actor is static:

- **Actor itself**: if `x`/`y`/`pos` become real properties, Actor can
  store its anchor position AS a `gacalc.g2.Vector2` internally (the
  ZRect keeps collision duty), making `actor.pos` vector-in/vector-out
  and eliminating the games' `Vector2(*self.pos)` unwrap/rewrap dance
  (avenger's `self.pos = tuple(Vector2(*self.pos) + self.velocity)`
  becomes `self.pos += self.velocity` again — honestly this time).
- **eggzy/cavern per-axis velocities**: still expected to stay scalar
  (per-axis physics is the algorithm), but re-examine with the
  instrumentation data in hand.
- Re-run the CTC benchmark mix after both passes; it doubles as the 2D
  metrics corpus for the gacalc fast-path task.
