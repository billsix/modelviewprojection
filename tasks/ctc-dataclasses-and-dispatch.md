# Code the Classics: dataclasses where feasible + dynamic-dispatch audit

**Status:** proposed — needs go-ahead
**Created:** 2026-07-08

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
