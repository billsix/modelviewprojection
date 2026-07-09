# Code the Classics: extend type coverage to locals and attributes

**Status:** DONE 2026-07-09 — Bill answered all four questions ("I like
the human readability") and everything actionable landed. Staged,
uncommitted. Ready to archive.

## Outcomes (2026-07-09, Bill's answers -> execution)

1. **Bare locals/attrs sweep ("do them")**: +278 annotations landed via a
   conservative AST annotator (first-binding-only; literal/ctor/known-fn/
   module-constant/same-module-class inference; hardened against
   dataclass fields — a class-level annotation IS a field — Enum members,
   global/nonlocal names, loop vars, tuple unpacks, re-assignments).
   Census: 1039 -> 1317 AnnAssigns across the 10 games. The residue is
   re-assignments (not first bindings — annotating them would be wrong),
   tuple unpacks, and RHS needing per-site game knowledge; the inferable
   tier is exhausted. One upstream oddity found: beatstreets names a
   parameter `str` (shadows the builtin), which blocks annotating in that
   scope.
2. **Shim Any ("do whatever you can deduce")**: ~100 -> 66, the remainder
   sitting on untyped third-party boundaries (GL plumbing, PIL,
   just_playback). actor.py went 30 -> 2; _types.py gained
   PointLike-with-Vector2 and Anchor; screen/draw/geometry APIs typed
   (Color, PointLike, RectLike, Drawable); a typed `_as_xy` normalizer
   replaced blit's untyped pos juggling.
3. **Rect/ZRect per-class typing ("if you can do it, do it")**: done
   WITHOUT the feared 50-line boilerplate — `_RectBase(Generic[_C])` with
   `Rect = _RectBase[int]`, `ZRect = _RectBase[float]`; every coordinate
   property/pair is typed `_C` once. `Rect.top` is an honest int:
   beatstreets' int-wrapped randint reverted to the faithful upstream
   line, and it typechecks.
4. **The 22 ty:ignores ("figure out if you can not ignore them")**: 18
   remained after tonight's earlier work; now **5**, each irreducible and
   documented (the four draw-offset override widenings — upstream's
   design — and soccer's tuple-compare tie quirk). Eliminated via honest
   means: base `update`/`button_down` return-type widening
   (`bool | None`), accepting GravityActor's optional `detect` param
   (`del detect`), asserts on documented invariants, `cast` for the
   CPUCar collision, an explicit unreachable `raise` in myriapod's
   direction table.

Gates: ty all-clean over shim+vol1+vol2, ruff clean, format clean,
60 pytest, 10/10 definitions gate.

**Created:** 2026-07-08

## RESOLUTION of the urgent item (2026-07-08)

Fixed with the codebase's own precedent (cavern's `cast("Player", player)`)
rather than 120 narrowing guards: avenger's and beatstreets' module-level
``game`` globals are now ``game: "Game" = cast("Game", None)`` with the
invariant documented at the declaration ("None ONLY on the title screen,
where nothing touches it"), and the two title-return resets use the same
cast. Runtime behaviour is byte-identical (`cast` is an identity function).
Two follow-on diagnostics the sharper typing surfaced were fixed at their
sites: beatstreets' ``randint(game.boundary.top, ...)`` int-wrapped (a
runtime no-op — shim `Rect` coordinates ARE ints; its properties are typed
``int | float`` only because ZRect shares them — precise per-class property
typing is future shim work for this task), and eggzy's
``game.player.replay_data`` cast under its PLAY-state invariant.
Result: **`ty check vol2` went 120 → 0**; vol1 already clean; the shim's
9 local-only diagnostics are sandbox import noise (glfw/OpenGL/
just_playback aren't installed locally; they resolve in the container).
Authoritative in-container `format.sh` re-run kicked off the same day —
result in session summary.

## Goal (Bill, 2026-07-08)

Add more Python types across the Code-the-Classics tree (pgzero_gl + vol1 +
vol2): function definitions AND local variables.

## URGENT first item: the `game`-global union errors now fail `make format`

**What's red and why.** `make format` runs `entrypoint/format.sh` in the
container; the script's last steps are `ty check` over pgzero_gl/vol1/vol2,
and its exit code is the script's exit code. As of 2026-07-08,
`ty check vol2` reports **~120 errors** (avenger ~45, beatstreets ~74,
eggzy 1) of the form::

    error[unresolved-attribute]: Attribute `player` is not defined on
    `None` in union `Game | None | Any`

**Root cause — a toolchain bump, not a code regression.** Every game
initializes a module-level ``game`` global to ``None`` and only assigns a
real ``Game(...)`` later (in ``update()`` on the first state transition),
while methods everywhere dereference ``game.player`` etc. unguarded. Each
`make image` dnf-installs the *current* Fedora 44 `ty`, and that package
moved to a stricter version some time after the gate was last green — the
new ty sees through the deferred-initialization pattern the old one let
slide. Verified 2026-07-08 via git-stash comparisons that the diagnostics
are byte-identical before/after every one of that day's changes
(dataclasses, formatting, honest-imports, match): nothing regressed; the
checker got smarter.

**Fix (this task's first chunk).** Type the ``game`` global honestly and
make the accesses type-safe. Candidate approaches, to be chosen per the
codebase's teaching style:
- ``game: Game | None = None`` + narrowing at the access sites (the
  *correct* fix, but touches many lines — pairs naturally with this task's
  attribute-annotation sweep);
- a late-bound ``game: Game`` with the None phase eliminated (e.g. create
  the attract-mode ``Game()`` at module init, which most vol1 games already
  effectively do — check why vol1 passes and vol2 doesn't and consider
  making vol2 match vol1's shape);
- last resort: a per-file ty suppression policy (documents the debt without
  paying it).
Until one of these lands, expect `make format` to exit 1 on the vol2 ty
step with these ~120 pre-existing findings.

## Where coverage actually stands (measured 2026-07-08)

The archived task (`tasks/archive/2026/06/29/codetheclassics-types-and-
docstrings.md`) already completed the signature layer: **863 of 864 `def`s
have return annotations** (one straggler in vol1), everything is `ty`-clean,
and `format.sh` enforces `ty check` over the whole tree. So "function
definitions" is a one-line finish. The real remaining work is the
variable layer:

| tree | annotated assignments | bare assignments |
|---|---|---|
| pgzero_gl | 116 | 126 |
| vol1 | 298 | 274 |
| vol2 | 663 | 681 |

≈**1,081 bare local/attribute assignments** (~50% coverage), plus ~100 `Any`
usages concentrated in the shim (audio/actor/screen/text/geometry) and **22
`# ty: ignore` suppressions**.

## Plan

- [ ] Fix the single unannotated `def` in vol1.
- [ ] Per-file pass over the ~1,081 bare assignments: annotate locals and
      `self.` attributes. Prefer annotating the *first* assignment
      (`self.timer: int = 0`), and for actor state prefer class-level
      declarations where the dataclasses task ([[ctc-dataclasses-and-dispatch]])
      would put fields anyway — coordinate the two tasks per game to avoid
      churning the same lines twice (dataclass conversion subsumes attribute
      annotations for converted classes; do dataclasses first in any game
      slated for both).
- [ ] Shrink `Any`: the shim's `Any`-heavy signatures (e.g.
      `Vector2.__init__(x: Any)`, audio/resources lookups) mostly have
      expressible types (`float | Sequence[float] | HasXY` protocols,
      `str`-keyed lookups). Games' `Callable[..., Mover]`-style params
      tighten to `type[Mover]` / precise callables.
- [ ] Revisit the 22 `ty: ignore`s — each is either fixable or gets a
      comment saying why it's permanent (several are documented faithful-port
      method-override variances, e.g. bunner's `MyActor.draw(offset_x,
      offset_y)`; those stay).
- [ ] Gate: `format.sh` (`ruff` on shim, `ty check` tree-wide) stays green;
      behaviour identical (annotations only — no runtime changes; beware
      annotations that *execute*, e.g. avoid evaluating forward refs — the
      files already do `from __future__ import annotations` where needed,
      check per file).

## Notes

- vol1/vol2 remain behaviour-faithful ports: annotations were always the one
  sanctioned change (CLAUDE.md), so unlike the dataclasses/dispatch task this
  needs no rule change.
- Volume: ~1,100 sites is mechanical but large; slice per game (10 chunks +
  shim), each independently gateable.
