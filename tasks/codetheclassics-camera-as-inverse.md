# Code the Classics: express the scroller cameras as inverse(translate(camera))

**Status:** SHOWCASE IMPLEMENTED on soccer 2026-09-04 (branch `codetheclassics-gl1-and-space-refactors`) — feasibility proven byte-identical, soccer converted, frame-180 AE=0, ruff+ty clean. Replication to bunner/avenger/beatstreets NOT done (a separate decision — see record).
**Priority:** 4
**Difficulty:** 4

## Implementation record (2026-09-04, while maintainer away — for review)

- **Feasibility PROVEN byte-identical (not just assumed):** in the mvp container,
  `inverse(translate(b=offset))(v)` equals `v - offset` **bit-for-bit** (compared the packed
  IEEE-754 doubles) across several vectors, including zeros and level-boundary values; `f` is an
  `InvertibleFunction`, `f(v)` a `Vector`. So the refactor is arithmetic-preserving.
- **Showcase = soccer** (`ports/codetheclassics/vol1/soccer/soccer.py`). Added
  `from gacalc.transforms import InvertibleFunction, inverse, translate`; in `Game.draw`, after
  the clamped `offset` is built, `world_to_screen = inverse(translate(b=offset))`; `MyActor.draw`
  now takes that function and does `self.pos = world_to_screen(self.vpos)` (was `self.vpos -
  offset`); the pitch blit and the active-player arrow route through it too.
- **Scope decision (flag if you disagree):** converted only the **real render path** (actors,
  pitch, arrow). Left the **`DEBUG_*` overlays** on raw `vpos - offset` — they are flag-gated (off
  by default), so the frame trace cannot verify them; converting them would be unverified change
  with no showcase value. A comment at the debug block notes they're the same value.
- **Verification:** frame-180 differential trace, original (HEAD) vs converted, in the mvp
  container under Xvfb — **AE = 0** (byte-identical, 39 182 colors both). `ruff` + `ty` clean.
  (Update path untouched, so seeded simulation state is identical; only the draw math changed, and
  identically.)
- **Open for maintainer:** (1) whether to replicate to the other three scrollers — `beatstreets`
  is easy (Vector `vpos`), `bunner`/`avenger` need the scalar→Vector care noted below;
  (2) the book-sequencing chapter for the code comment (I referenced ch16/ch19 generically).

## BLUF

Study the feasibility of rewriting the four scrolling games' ad-hoc world→screen step —
`screen = world − camera_offset` — as the course's own **`inverse(translate(camera_offset))`**,
so the ports *demonstrate the book's central hinge* ("render through the **inverse** of the
camera's placement") in real game code. **Build on the existing `gacalc.transforms` /
`mathutils` functions — `translate`, `inverse`, `InvertibleFunction` — do NOT invent new
machinery** (maintainer, 2026-09-04). This is a study + a discussion, not an approved change:
the games are behaviour-faithful ports, so any rewrite must be **byte-identical** (proven by the
frame-trace harness), and the abstraction-vs-clarity trade-off is a maintainer call.

Applies to the **four scrollers only** — `bunner`, `soccer`, `avenger`, `beatstreets`. The five
single-screen games have no camera; `leadingedge`'s genuine 3-D camera is its own task
(`tasks/codetheclassics-leadingedge-projection-functions.md`).

## Context (read first)

- **Evidence base:** `tasks/reference/coordinate-spaces-in-code-the-classics.md` › "Cameras as
  the inverse transformation." It documents, with `file:line`, that every scroller's draw step is
  a single additive translation that *is* `inverse(translate(C))` collapsed to a subtraction:
  - `soccer.py:2608-2612` — `self.pos = self.vpos − offset` (2-D `Vector`, ball-follow,
    bounds-clamped at `:3521-3526`). **Cleanest fit** — positions are already `gacalc` Vectors.
  - `beatstreets.py:3127-3130` — `screen = vpos − scroll_offset` (2-D `Vector`, horizontal).
  - `bunner.py:2478-2487` + `:3305` — `screen_y = world_y − scroll_pos` (scalar, **Y-only**,
    `int(scroll_pos)`).
  - `avenger.py:2887-2897` + `:4058` — `screen = world + offset_x`, `offset_x = −(player.x −
    camera_offset_x)`, plus a **½-scaled parallax** copy (`:4049`) = a second `translate(C/2)`.
- **The course's machinery to build on** (`CLAUDE.md` › Central abstraction): `translate(b)` and
  `inverse(f)` come from **`gacalc.transforms`**; `inverse(translate(C))` is definitionally
  `translate(−C)`, so it produces `world − C` — mathematically identical to what the games do
  today. The games already depend on `gacalc` (they use `gacalc.g2.Vector` directly), so
  `from gacalc.transforms import translate, inverse` adds no new dependency.
- **Fidelity rule** (`CLAUDE.md` › Code-the-Classics): behaviour-faithful — structure may change,
  behaviour may not. The proven net is the **frame-180 byte-identical harness** built in
  `tasks/adhoc/pgzero-gl-inline/` (seeded RNG + `PGZERO_MAX_FRAMES` + `glReadPixels` compare).

## Design principle (settled — maintainer, 2026-09-04)

Using the book's **taught** math abstractions here is **consistent** with the ports' "library, not
framework" / "clearer code over abstractions" philosophy — not an exception to it. That principle
targets **framework-style inversion of control** (PyGame Zero's runner owning the loop, calling
*up* into the game) and depending on **pgzero-the-framework** — NOT the book's own math.
`InvertibleFunction`/`translate`/`inverse`/`compose` are library functions the game calls *down*
into, and the maintainer *teaches* them, so a game (and a book section) that uses them is coherent
with the curriculum. The abstraction **gradient** is exactly this: `boing_gl1.py` uses **zero**
abstractions (rawest, fixed-function GL, an early teaching point); richer games use more of the
taught abstractions — all still "library, not framework." Two real constraints remain: **(1) book
sequencing** — a book section referencing this code must come *after* the chapter teaching the
abstraction; **(2) don't reintroduce the pgzero framework.** Import from **`gacalc.transforms`**
(decided) — the ports already depend on gacalc and stay off course-layer code.

## Feasibility questions to resolve BEFORE any edit

1. **Type & rounding parity.** `translate`/`inverse` operate on `gacalc` Vectors and return
   `Coef` (`float | Expr`); the blit boundary needs `float()`. `soccer`/`beatstreets` already
   store `Vector` `vpos` (clean). `bunner` uses a **scalar `int(scroll_pos)`** and `avenger` uses
   **`int` `offset_x`/`top`** — routing these through a `Vector` translate must reproduce the
   *exact* int truncation at the pixel boundary. **Prove byte-identical, per game, with the
   trace** — do not assume float vs int math coincides.
2. **Where the `InvertibleFunction` is built and applied.** Construct `f =
   inverse(translate(camera))` **once per frame**, apply `f(world_pos)` per object inside
   `Actor.draw`. Confirm the per-object cost is negligible (it is — one Vector add).
3. **soccer's clamp** is computed *before* the offset is used (`max/min` to level bounds,
   `:3521-3524`) → it produces the offset vector, which `translate` then consumes; no conflict.
   Verify.
4. **avenger's parallax** = drawing backgrounds at `offset // 2`. Expressed as a *second*
   `inverse(translate(camera / 2))`. This shows the pattern scales to multiple camera edges —
   confirm the `// 2` integer halving is reproduced exactly.
5. **Import source (open question 2).** `gacalc.transforms` (keeps the ports depending only on
   gacalc, off the course layer) vs `modelviewprojection.mathutils` (the book's exact bindings,
   but couples ports to course code). Both are "existing code" per the maintainer's guidance.

## Approach sketch (only after go-ahead)

- Pick ONE showcase game (recommend `soccer` — Vector-native, cleanest), rewrite its draw offset
  as `inverse(translate(offset))`, add a comment naming the world↔screen edge and pointing at the
  book chapter, and **prove frame-180 byte-identical** + maintainer play-test.
- Then decide (a fresh decision) whether to replicate to `beatstreets` (easy, Vector), `bunner`
  and `avenger` (need the scalar→Vector care of feasibility Q1).
- Reuse the existing trace harness; save any codemod under `tasks/adhoc/` per convention.

## Open questions

1. **Scope:** one **showcase** first (recommend `soccer`), proven byte-identical, then a separate
   decision on the other three — or all four scrollers at once? *(Recommend: showcase first — one
   clean, verified example beats four parallel half-migrations.)*
2. **Book sequencing:** a book section referencing this game code must come *after* the chapter
   teaching `translate`/`inverse`/the camera-as-inverse hinge (ch16/ch19). Which chapter is the
   earliest appropriate anchor for the cross-reference? *(Your call — you teach the math; I'll
   point the code comment at whatever chapter you name.)*

(Import source and the "is this an exception?" question are **settled** — see "Design principle":
`gacalc.transforms`, and it's consistent with the philosophy, not an exception.)

## Related

- `tasks/reference/coordinate-spaces-in-code-the-classics.md` — the finding (evidence base).
- `tasks/codetheclassics-myriapod-rotation-as-functions.md` — the sibling "rotation as functions"
  concern (the 2-D rotate case; this is the 2-D translate case).
- `tasks/codetheclassics-leadingedge-projection-functions.md` — the 3-D camera/projection case.
- `tasks/adhoc/pgzero-gl-inline/` — the byte-identical frame-trace harness to verify with.
