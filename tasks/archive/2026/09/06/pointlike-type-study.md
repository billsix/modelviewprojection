# Study: does `PointLike` need to exist, or can gacalc's `Vector` (or a tuple) be the one point type?

**Status:** DONE + ARCHIVED 2026-09-06 (Fable, overnight) — decision: keep `PointLike` at the engine boundary; the numbers and rationale are `tasks/reference/point-type-decision.md`. The one real cost found (`Vector.__eq__` via `sympy.simplify`, ~60 µs per differing comparison) is gacalc's — filed there as `tasks/fast-numeric-equality.md`. The whole-game profiler is promoted to `tools/ctc_profile_update.py`; the micro-benchmark stays one-shot in `tasks/adhoc/pointlike-type-study/` (held until the maintainer says "archive").
**Priority:** 5
**Difficulty:** 4

## BLUF

Every tightened Code-the-Classics game defines `PointLike = tuple[float, float] | Vector` and takes
it wherever a position comes in (`Actor.__init__`, `pos` setters, `collidepoint`, `blit`-style
calls, the vol2 `Surface.blit`, `IntRect`/`Rect` helpers). Decide, with measurements, whether that
union should stay, or whether one type should be used everywhere: gacalc's `Vector` (the games'
own arithmetic type), or a plain `tuple[float, float]` (if it is measurably faster on the hot
paths). Deliverable: the decision, the numbers, and the rationale — as a reference doc
(`tasks/reference/point-type-decision.md`) if the finding outlives the change, else in this task.

## Context (read first)

- `tasks/reference/code-the-classics-tightening.md` §1–§1b (the engine shape the games share) and
  §6 (per-game engine flags). `PointLike` is defined in the "rectangles and sprites" engine section
  of each game (e.g. `ports/codetheclassics/vol2/eggzy/eggzy.py`, 18 uses); boing does not have it.
- Why the union exists: upstream pygame code passes positions as tuples (`(400, 400)`, `(x, y)`)
  while the games' physics uses gacalc vectors (`self.vpos + Vector(...)`, `.magnitude()`); the
  engine unpacks (`px, py = pos`) so both work. gacalc vectors are frozen and carry `Coef`
  coordinates that may be sympy expressions; `float(v.x)` appears at float-typed boundaries.
- Related: mvp `CLAUDE.md` ("The games use `gacalc.g2.Vector` DIRECTLY"), `tasks/reference/design-decisions.md`
  › Ports (the frozen-vector migration and its differential trace),
  `tasks/pgzero-gl-renderer-matrix-via-gacalc-perf.md` (an earlier gacalc-vs-numpy perf question in
  the renderer — same measuring discipline), gacalc at `github.com/billsix/geometricalgebra`.

## Questions the study answers

1. **Where do tuples actually flow in?** Census per game: literal tuples at construction sites
   (`Actor("x", (400, 400))`, `Vector(*pos)` copies), tuple-returning helpers (`center`, `topleft`),
   and the places that unpack. How many sites would change under "Vector everywhere" vs "tuple
   everywhere"?
2. **Performance, measured, not assumed.** Micro-benchmarks (`timeit`, in the nested image) of the
   hot operations — construct, unpack, add, compare, `magnitude` — for `Vector` vs `tuple` vs the
   union's unpack; then a whole-game measurement: frames per second of a headless `update()` loop
   (`tools/ctc_state_trace.py`-style driving, without the dump) for the busiest game (beatstreets or
   leadingedge) before and after a trial conversion of one game. gacalc arithmetic goes through
   `Coef` (sympy-capable), so the vector path is expected to be slower per op; the question is
   whether it matters at 60 Hz with a few hundred objects.
3. **Typing and readability.** What does each option do to the annotations (`tuple[float, float]`
   returns vs `Vector`), to the `float(...)` boundary casts, to ty's view of `Coef`, and to the
   course's "the games use gacalc directly" stance? Does one type let `Rect`/`IntRect` and `Actor`
   drop their unpacking?
4. **Decision + plan.** Recommend one of: keep the union (and say why it is cheap); `Vector`
   everywhere (tuples converted at the upstream literal sites); tuple at the engine boundary only.
   If a change is recommended, file it as its own task gated the usual way (frame identity + state
   trace), one game as a pilot.

## Verify

- Numbers reproducible from a saved script under `tasks/adhoc/pointlike-type-study/` (a measuring
  harness is a candidate for `tools/` if it would be re-run).
- Any trial conversion passes `tools/ctc_verify_game.sh` and the state trace before its numbers
  count.
