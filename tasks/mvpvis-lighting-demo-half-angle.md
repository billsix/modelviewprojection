# New MVP-visualization demo: lighting with half-angle vectors + light source

**Status:** blocked
**Priority:** 7
**Difficulty:** 5
**Started:** 2026-08-27 (William Emerison Six <billsix@gmail.com>)
**Blocked on:** maintainer answers the Open questions below (new demo vs overlay; what the half-angle
vectors show; relationship to demo22 lighting).
**Recheck:** the Open questions below are answered (maintainer-gated; `/recheck-blocked` surfaces it).

## Goal

Maintainer's idea, verbatim: *"Make a MVP visualization demo that shows lighting, with the half angle
vectors, and shows the light source."*

## Context (investigation 2026-08-27)

- The `mvpvisualization/` demos (7 of them, the Cayley-graph engine, GL shell `cayley_gl.py`) are
  covered by active `mvpvisualization-pedagogy-plan.md` — but **none of them show lighting**; the Cayley
  engine has no lighting mechanism, so this is a **new engine capability** (an 8th viz demo or a lighting
  overlay). Reference: `tasks/reference/notable-subsystems.md §2`.
- **The half-vector math already exists in the curriculum** — Blinn-Phong halfway vector at
  `demos/demo23/litjet.frag:47` and `demos/demo23.py:33` — reuse it, don't re-derive.
- Archived `2026/06/14/ports-visible-light-source.md` (the light marker).
- **Overlaps `demo22-light-types-and-flashlight.md` (bullet 6)** — this is the *visualization* side.

## Plan (draft — after questions)

- [ ] Add a new `mvpvisualization/` lighting demo (or overlay), drawing the L/V/N/H vectors and the light
      source, reusing demo23's half-vector math.

## Open questions

1. **New standalone `mvpvisualization/` demo, or an overlay** on an existing one?
2. **"Half angle vectors"** = draw L/V/N/H vectors for Blinn-Phong?
3. **Relationship to bullet 6** (`demo22-light-types-and-flashlight.md`) — is this the *visualization*
   counterpart of demo22's lighting, or independent?
