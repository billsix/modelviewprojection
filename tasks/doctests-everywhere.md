# Doctests for as much of the codebase as reasonable

**Status:** **wiring DONE 2026-07-18; coverage still proposed.** Doctests now run as
part of the suite (60 -> 66 tests), the 4 silently-failing ones are fixed, and
`matplotgraphs.py` imports headless. What remains is the actual goal: *writing* doctests
for the modules that have none — which is gated on
[demo-main-guards-and-dedent](demo-main-guards-and-dedent.md) for anything under
`demos/`.
**Created:** 2026-07-18
**Prompted by:** Bill, 2026-07-18 — "I want doctests always run as part of the test
suite… there should be doctests for as much as possible."

## Where things stand (done 2026-07-18)

Doctests **now run as part of the suite**. Before this they were collected by nothing:
`pytest.ini` had no `--doctest-modules` and `testpaths` pointed only at `tests/`, so
**four doctests had been failing silently** since the NumPy 2 scalar-repr change
(`np.float64(-4.0)` where the example expected `-4.0`). Fixed by printing plain floats,
which is version-independent. `matplotgraphs.py` also hardcoded `matplotlib.use("TkAgg")`
and could not even be imported headlessly; it now falls back to `Agg` when there is no
`DISPLAY`.

Suite went 60 -> 66 tests. Verified the wiring actually gates by deliberately breaking a
doctest (it failed) and restoring it (green).

**Only `plotsforbook` has any doctests today — 2 files.** Every other area has zero:
`cayley`, `util`, `framebuffer`, `mathutils.py`, `pyMatrixStack.py`, `mvpvisualization`,
`demos`, `notebooksrc`.

## The allow-list in `pytest.ini` is a workaround, not the design

`testpaths` currently names the importable library modules explicitly. **That list only
exists because `--doctest-modules` IMPORTS whatever it collects, and the runnable scripts
execute at import time:**

- `demos/demo01.py:27` calls `sys.exit()` at module level — this does not fail a test, it
  kills the pytest process with `INTERNALERROR`.
- other `demos/` and `notebooksrc/` files run their render loop on import.
- `mvpvisualization/` and `wxapp*.py` open windows.

### The real fix: `if __name__ == "__main__":` guards

Give every runnable script a main guard (and a clean exit). Then importing one is a
no-op, `testpaths` collapses to `src tests` with **no list at all**, and the suite
automatically picks up doctests anywhere in the tree — including in the demos, which is
where the teaching examples would be most valuable.

**Tracked as its own task: [demo-main-guards-and-dedent](demo-main-guards-and-dedent.md)**
(approved in principle by Bill 2026-07-18). It is not a trivial edit — the demos are the
book's source, so indenting them into a guard changes 129 `literalinclude` excerpts
unless `:dedent:` is added alongside.

Precedent: `tasks/ctc-game-main-guard-and-clean-exit.md` proposes exactly this for the
Code-the-Classics ports. Same change, same reason; worth doing as one sweep or two
consistent ones.

**Sequence matters:** main guards first, then delete the allow-list, then add doctests
broadly. Adding doctests to a demo before it has a main guard does nothing — the module
still can't be collected.

## Then: where doctests actually earn their keep

Ranked by value, not by file count. A doctest is worth writing where it **documents a
contract a reader would otherwise have to infer**; it is not worth writing to inflate
coverage.

1. **`mathutils.py`** — the transform primitives (`translate`, `uniform_scale`, `rotate`,
   `ortho`, `perspective`, the `InvertibleFunction` stack). Highest value in the repo:
   these are the book's core abstractions, and gacalc's equivalents are already
   doctested, so there is a house style to copy.
2. **`pyMatrixStack.py`** — push/pop isolation, and that `modelview` is a *derived*
   product (reading it works, writing it raises). Both are non-obvious and both were
   recently the subject of real bugs (`tasks/archive/2026/07/18/pymatrixstack-bugs.md`).
3. **`cayley/cayleygraph.py`** — `path()` composing edges and auto-inverting
   against-arrow ones is the single most surprising behaviour in the codebase and has no
   executable example.
4. **`framebuffer/softwarerendering.py`** — winding/orientation and the
   point-in-triangle boundary rule (a pixel exactly on an edge counts as both CCW and
   CW). Currently prose-only.
5. **`util/`** — `clipping`, `shading`, `colorutils`: small pure functions, cheap wins.
6. **`demos/`** — only after main guards. Most demo code is a render loop, but the small
   pure helpers in them are good candidates.

**Skip:** anything requiring a GL context, a window, or a real file; anything whose
output is a float formatting accident (see the NumPy 2 breakage above — prefer
`float(...)` or rounding in the example over pasting a raw repr).

## Gates

`make format` clean; `pytest` green headless **and** with a display; and the sanity check
that matters — deliberately break one new doctest and confirm the suite goes red.
