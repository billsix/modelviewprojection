# Code the Classics: dataclasses where feasible + dynamic-dispatch audit

**Status:** implementation COMPLETE 2026-07-08 — all 10 games converted +
dispatch-audited; per-game ty gates all show zero new diagnostics (vol1
fully clean; avenger/beatstreets/eggzy carry pre-existing `game`-union
noise under the strict local ty, byte-identical before/after — verified via
git stash). Remaining: Bill's on-display batch boot of the games (boing
already verified), and a final in-container `format.sh` ty run.
**Created:** 2026-07-08

## Progress + pattern rules (established on boing, refined on bunner)

- [x] **CLAUDE.md rule updated** ("behaviour-faithful, structure may modernize").
- [x] **vol1/boing** — Impact/Ball/Bat → `@dataclass(eq=False)` with
      InitVar + `__post_init__` for the `super().__init__(image, pos)` call;
      Game stays plain (all fields derived from `controls`). Display-verified
      by Bill. Dispatch audit: nothing vestigial.
- [x] **vol1/bunner** — Bunner + Eagle converted (stateful leaves); the four
      framework bases (MyActor/Mover/Row/ActiveRow) and the
      RNG-in-`__init__` classes (Car/Log/Train/Hedge/Grass/Water/Road/Rail/
      Dirt/Pavement) + Game keep explicit `__init__` (see rules below).
      Dispatch audit: all overrides load-bearing via `game.rows`; tightened
      `child_type: Callable[..., Mover]` →
      `Callable[[int, tuple[float, float]], Mover]` (NOT `type[Mover]` —
      subclass constructors take (dx, pos), not Mover's (dx, image, pos)).
- [x] **vol1/cavern** — Orb/Bolt/Pop/Player/Robot converted (Robot's
      `randint` speed moved to `__post_init__`, same RNG sequence);
      CollideActor/GravityActor kept (bases), Fruit kept (choice-table init
      IS the logic), Game kept. ty clean.
- [x] **vol1/myriapod** — Explosion/Player/Bullet/Segment converted
      (Segment: all-assignment 5-param constructor, the cleanest win yet);
      FlyingEnemy kept (super-pos depends on RNG `side`), Rock kept
      (branching RNG + sound side effect in init), Game kept. ty clean.
- [x] **vol1/soccer** — Difficulty (pure 4-field record, cleanest win)/
      Goal/Ball/Team converted (Ball uses `field(default_factory=...)` for
      its Vector2 and shadow-MyActor defaults); MyActor kept (base), Player
      kept (computed kickoff position + compared by identity against
      `game.kickoff_player`), Controls kept (branching key-bindings init),
      Game kept (sound side effects). ty clean; **vol1 COMPLETE (5/5)**.
- [x] **vol2/avenger** — Bullet/Player/Human converted (Player: 13 declared
      fields incl. factory-made Vector2/blip/thrust-sprite; nested Timer
      IntEnum + Vector2 class constants as ClassVar; thrust-sound try/except
      in post_init); Laser kept (computed super-args), Enemy kept (type-
      branching + RNG init), Controls ABC family kept (base init chain),
      WrapActor/Radar/Game kept. NOTE: local pip ty shows 45 pre-existing
      `game`-union diagnostics in this file — identical before/after the
      conversion (verified via git stash); the container's ty is clean.
- [x] **vol2/kinetix** — Bullet/Impact/Bat converted (Bat's shadow created
      in post_init since it reads self.x/y set by super); Barrel kept
      (weighted-RNG powerup table reads live game state), **Ball kept for a
      subtle ordering reason**: its x/y params intentionally overwrite
      Actor's x/y AFTER super().__init__ — a dataclass would assign the
      fields first and super would clobber them. Controls family kept.
      ty clean before and after.
- [x] **vol2/eggzy** — Gem (round-robin `next_type` as ClassVar, mutation in
      post_init)/Door/Player (15 declared fields)/GhostPlayer converted;
      Enemy kept (lookup-table-derived init), Animation/CollideActor/
      GravityActor kept (bases), DashTrail kept (trivial arg-bundle).
- [x] **vol2/leadingedge** — first **dataclass-base + plain-subclass** wins:
      Scenery, TrackPiece, Car are pure records converted to dataclasses
      while their subclasses (StartGantry/Billboard/Lamps, CPUCar/PlayerCar)
      keep explicit `__init__` calling the generated one — the inverse of
      the boing pattern, allowed by rule 3.
- [x] **vol2/beatstreets** — Attack (the 18-parameter JSON-driven record;
      `flyingkick` json name kept via InitVar → `flying_kick` attr) and
      Stage converted (Stage's shared-mutable-default `[]` args replaced by
      default_factory — strictly safer). Fighter/Weapon/Powerup ABC families
      and their leaves kept: the leaves' whole substance is one big kwargs
      super() call (arg-bundles), and Stick/Chain roll randint durability.

## Dispatch-audit conclusion (Bill's question: why so much, is it needed?)

Across all 10 games the dispatch falls into four buckets:
1. **Heterogeneous update/draw loops — necessary.** Every Game.update walks
   a mixed list (`bunner.rows` holds 8 Row types; cavern's five object
   lists; beatstreets' fighters+weapons+powerups) calling `update()`/
   `draw()` virtually. The alternative is isinstance ladders per type.
2. **Rule-encoding subclass families — necessary, it IS the design.**
   bunner's Row API (`next/check_collision/push/play_sound/allow_movement`)
   makes each row type a different game rule; same for Weapon/Powerup/
   Controls (keyboard vs joystick vs AI at runtime).
3. **`getattr(sounds/images, name+n)` — not class dispatch at all**, it's
   pgzero's resource-lookup API; copy-pasted per game, centralizable into a
   shim helper but not removable.
4. **Actual surplus — small and cosmetic:** a handful of arg-bundle
   subclasses (LampLeft/LampRight, TrackPieceStartLine, DashTrail,
   Stick/Chain) that could be factory calls or data rows, and the loose
   `Callable[...]` types (one fixed in bunner). Nothing architectural.

Verdict: the dispatch is deliberate curriculum, not pgzero leftovers —
vol2 even graduates from vol1's convention-based overriding to real
ABC/@abstractmethod, and eggzy's GravityActor carries an upstream comment
*acknowledging* the inheritance drawback vs component systems. pgzero
itself only requires module-level update()/draw(); everything class-shaped
above that is the books teaching OOP game architecture on purpose.

**Pattern rules for the remaining games:**
1. `@dataclass(eq=False)` ALWAYS — generated `__eq__` would swap identity
   semantics for field equality and set `__hash__ = None`.
2. Constructor-only inputs → `InitVar`; `super().__init__(image, pos)` in
   `__post_init__`; mutable defaults via `field(default_factory=...)`;
   class constants → `ClassVar` (stays out of `__init__`/instance state).
3. **Never dataclass a class whose subclasses are (or its base is) also a
   dataclass** — inherited InitVars/fields merge into subclass `__init__`
   signatures and break positional call sites. Convert stateful LEAVES over
   plain bases only; framework bases keep explicit `__init__`.
4. Keep explicit `__init__` when: super-args are computed (image names from
   `randint` — also preserves RNG call order), init logic is the interesting
   part, or all attrs derive from one parameter (a generated `__init__`
   would be all-`field(init=False)` ceremony). Leave a one-line comment on
   deliberate keeps only where the reason isn't obvious.
5. Upstream teaching comments move intact onto the fields they describe.

**Per-chunk gate:** py_compile + `ty check vol1/<game>` clean + a stub-Actor
harness when the pattern does something new; Bill boots each converted game
on-display (batched is fine).

## Goal (Bill, 2026-07-08)

Across **vol1 and vol2** (all 10 games): convert classes to `@dataclass`
wherever feasible, and **audit the dynamic dispatch** — Bill suspects some of
it is leftover from learning from Pygame Zero rather than something the code
actually needs. Look at how each class is *used* and decide.

## RULE CHANGE this task implies

CLAUDE.md's Code-the-Classics section says the games are **faithful ports —
"no behaviour changes, no restructuring, no ruff"**. This task deliberately
relaxes the *restructuring* half (dataclasses, dispatch cleanup) while keeping
**behaviour identical**. When this lands, update CLAUDE.md's rule to say the
games may be structurally modernized but must stay behaviour-faithful (the
shim `pgzero_gl/` was always fair game).

## Survey findings (2026-07-08, pre-work)

~138 classes across the 10 games; **zero dataclasses today**.

The "dynamic" constructs fall into distinct buckets — they should be judged
separately:

1. **`getattr(sounds, name + str(n))` / `getattr(images, ...)`** — upstream
   Pygame Zero's resource-lookup idiom (name-composed attribute access),
   present in every game (boing 381, cavern 662, bunner 772/785, soccer 967,
   myriapod 831, avenger 1307/1316/1329, kinetix 875/1103, leadingedge
   228/230/347/505). This is *the shim's public API* (`sounds`/`images`
   attribute objects), not class dispatch — removing it means changing the
   shim API, e.g. adding `sounds.play(name, count)` / dict-style lookup.
   Probably KEEP the shim API but a helper could centralize the
   `name+randint` composition (it's copy-pasted in every game).
2. **Actor inheritance trees with overridden `update()`/`draw()`** — e.g.
   bunner's `MyActor → Mover → Car/Log/Train` and `Row → ActiveRow →
   Water/Road` plus `Grass/Dirt/Pavement/Rail`; avenger's `WrapActor →
   Bullet/Laser/Player/Enemy/Human`. These ARE used polymorphically — the
   game loops iterate heterogeneous lists (`for obj in self.rows +
   [self.bunner, self.eagle]: obj.update()`), so this virtual dispatch is
   load-bearing. Audit question per class: is every override actually reached
   via a base-typed reference, or do some subclasses exist only to hold a
   different constructor (→ dataclass field defaults could replace them)?
3. **Classes/functions passed as values** — bunner's `Row.__init__(child_type:
   Callable[..., Mover], ...)` (class-as-factory), boing's
   `move_func`/`controls` callables (human vs AI paddle). Deliberate upstream
   design and genuinely polymorphic; keep, but type them precisely
   (`type[Mover]` instead of `Callable[..., Mover]`).
4. **`Controls` ABC (avenger, others in vol2)** — keyboard vs joystick
   implementations selected at runtime; real dispatch, keep.

## Dataclass feasibility notes

- Best candidates: classes whose `__init__` is pure field assignment —
  the `Game` classes' state blocks, plain records, and Actor subclasses that
  only stash constants. `@dataclass` with methods is fine (dataclasses don't
  preclude behaviour).
- **Friction:** most Actor subclasses *compute* arguments before
  `super().__init__(image, pos)` (e.g. `Car.__init__` builds the image name
  from `randint`), and `Actor`/`pgzero_gl` base classes are not dataclasses.
  Options per class: keep a custom `__init__`; or `@dataclass` +
  `__post_init__` calling `super().__init__(...)`. Do NOT contort a class
  into a dataclass when the __init__ logic is the interesting part —
  "feasible" means it gets *simpler*.
- `slots=True` where it works (these run 60 fps loops); `kw_only`/defaults to
  replace trivial subclasses where bucket-2 audit says the subclass carries
  no behaviour.

## Plan

- [ ] Per game (10 passes, one commit-sized chunk each): classify every class
      into bucket 1–4 / dataclass-candidate; convert; note each dispatch site
      kept-and-why or removed.
- [ ] Keep behaviour byte-identical: same RNG call order (careful — moving
      `randint` calls into field defaults changes seeding order), same
      update/draw order.
- [ ] Gate: `entrypoint/format.sh`'s `ty check` over pgzero_gl+vol1+vol2
      stays green; each game boots and plays (Bill's on-display check).
- [ ] Update CLAUDE.md's faithful-port rule per above.

## Open questions

- Bucket 1: is a `sounds.play_random(name, count)`-style shim helper wanted,
  or is `getattr` fine as the pgzero idiom? (It's also a teaching artifact.)
- How aggressive on collapsing no-behaviour subclasses (bucket 2) — replace
  with dataclass field values, or keep the class-per-thing structure for
  readability?
