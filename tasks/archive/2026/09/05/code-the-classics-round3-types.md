# Code the Classics — round 3: add more types

**Status:** DONE + ARCHIVED 2026-09-05 (as subsumed — every game's types concern was covered by the tightening pass; see the umbrella's completion record).
"add more types" is absorbed into that umbrella's per-game tightening pass (concern 2, tighter
functions + precise types). This doc stays for its prior-rounds context and is archived as subsumed
when the games it would cover are done. Not an independent actionable task.
**Priority:** 7
**Difficulty:** 4
**Started:** 2026-08-27 (William Emerison Six <billsix@gmail.com>)
**Recheck:** the Open questions below are answered (maintainer-gated; `/recheck-blocked` surfaces it).

## Goal

Maintainer's idea, verbatim: *"Code the classics - add in more types."*

Continue adding types to the Code the Classics games — this would be a **round 3**, after two
already-completed modernization/typing rounds.

## Context (investigation 2026-08-27)

- **Two modernization/typing rounds are already done and archived** — cite them for what's covered:
  `2026/07/09/ctc-more-types.md`, `2026/06/29/codetheclassics-types-and-docstrings.md`,
  `2026/07/09/ctc-modernization-round2.md`, plus `ctc-dataclasses-and-dispatch`,
  `ctc-match-and-modern-python`, `port-codetheclassics-vol1/vol2`.
- Reference: `tasks/reference/notable-subsystems.md §4a` (the 10 games, the `pgzero_gl` shim;
  byte-faithfulness was retired 2026-07-08, so modernization is sanctioned).

## Plan (draft — after questions)

- [ ] Identify what rounds 1–2 left untyped; add the remaining types to the named games.

## Open questions

1. **Which games / which remaining types** — this is round 3; what did rounds 1–2 leave?
2. **"Types"** — more type *annotations*, or new dataclass / game-object *types*?
