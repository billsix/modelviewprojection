# The engine's point type: keep `PointLike = tuple[float, float] | Vector` at the boundary

**Decided 2026-09-06 (Fable, executing `tasks/archive/2026/09/06/pointlike-type-study.md` with the
maintainer's delegated discretion; William Emerison Six <billsix@gmail.com> may overrule).** Project:
`github.com/billsix/modelviewprojection`; the vector type is gacalc's `g2.Vector`
(`github.com/billsix/geometricalgebra`). Numbers from `tasks/adhoc/pointlike-type-study/bench_point_types.py`
and `tools/ctc_profile_update.py` (promoted from the study's `bench_game_update.py`), in the project image (gacalc 0.0.19, Python 3.14), 2026-09-06.

## The decision

Every Code-the-Classics game keeps `PointLike = tuple[float, float] | Vector` **only at the engine's
input boundary** — `Actor(image, pos, anchor)`, the `pos` setter, `collidepoint`, `Rect`/`IntRect`
helpers, `Surface.blit` — where it unpacks once (`px, py = pos`). Inside the engine and the games'
physics the type is `Vector`; tuple-returning helpers (`center`, `topleft`) stay tuples. Neither
"Vector everywhere" nor "tuple everywhere" is adopted.

## Why (the three questions the study asked)

**1. Where tuples flow in.** They are upstream's literal form: `Actor("x", (400, 400))`,
`pos=(1000, 400)` — beatstreets' stage table alone has 120 such literals, avenger/kinetix a couple,
the rest none; every game's engine has 2–3 `Vector(*pos)` copies and 1–5 unpack sites. "Vector
everywhere" would wrap every upstream literal in `Vector(...)` (noise in the ported text, the thing the
ports keep faithful) and the engine would still copy; "tuple everywhere" would strip the games'
arithmetic type at the boundary and put `(v.x, v.y)` at every call that already holds a vector.

**2. Performance, measured.** Per-operation (best of 5 × 200k, µs):

| operation | `Vector` | tuple | ratio |
|---|---|---|---|
| construct | 0.148 | 0.005 | 30× |
| unpack `a, b = p` | 0.089 | 0.008 | 11× |
| add / subtract | 0.28 | 0.047 | 6× |
| scale by float | 0.416 | 0.037 | 11× |
| `float(v.x)` | 0.023 | 0.016 | 1.4× |
| magnitude | 0.141 | 0.053 (`hypot`) | 2.7× |
| the `PointLike` boundary unpack | 0.133 | 0.048 | 2.8× |
| `Actor.pos = p` (anchor → rect) | 0.174 | 0.088 | 2.0× |
| **equality `==`** | **48.1** | 0.018 | **2685×** |

Whole game, 900 scripted frames of `update()` under cProfile: beatstreets 192 µs/frame, leadingedge
219, eggzy 214 — **about 1% of the 16.7 ms frame budget**, so the vector-vs-tuple ratios above are
irrelevant to frame rate: the boundary unpack costs 0.05–0.13 µs and a game does at most a few
thousand vector ops per frame (leadingedge: 9k `__sub__` calls in 900 frames; gacalc is 15 ms of
197). The one thing that matters is **`Vector.__eq__`**: gacalc's generated equality is `a == b or
sympy.simplify(sympify(a) - sympify(b)) == 0` per coefficient, so two vectors that *differ* pay
`sympy.simplify` (~60 µs). beatstreets compares `target != self.vpos` per fighter per frame: 1189
comparisons = 71 ms of its 173 ms. Still only 0.4% of the budget today, but it is the wrong place
for the cost and it is gacalc's to fix — filed as `tasks/fast-numeric-equality.md` in the gacalc repo
(short-circuit when both coefficients are plain numbers). Not a reason to change the point type: the
comparison is between two `Vector`s regardless.

**3. Typing and readability.** The union costs nothing in annotations (`PointLike` reads as "a
point, however you have it"); the `float(v.x)` casts at float-typed boundaries stay (gacalc's
coordinates are `Coef`, which admits sympy, and ty is right to insist); `Rect`/`IntRect` and
`Actor` keep their one unpack. The course's "the games use gacalc directly" stance is untouched:
all arithmetic is on `Vector`.

## When to revisit

- If a profile ever shows the boundary unpack or `Vector(*pos)` copies near the top — it will not at
  60 Hz with hundreds of objects; re-measure with `tools/ctc_profile_update.py <game> <frames> <keys>`.
- After gacalc's fast numeric equality ships, beatstreets' `==`/`!=` on vectors becomes free; nothing
  in the games needs to change for it.
