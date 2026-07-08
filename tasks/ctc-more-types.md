# Code the Classics: extend type coverage to locals and attributes

**Status:** proposed — needs go-ahead
**Created:** 2026-07-08

## Goal (Bill, 2026-07-08)

Add more Python types across the Code-the-Classics tree (pgzero_gl + vol1 +
vol2): function definitions AND local variables.

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
