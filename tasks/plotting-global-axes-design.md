# Analyze the `global axes` threading in the matplotlib plot helpers

**Status:** proposed — **analysis only, no code changes without a decision**
**Created:** 2026-07-18
**Requested by:** Bill, 2026-07-18 — "analyze how I do the matplotlib plotting with
threading global axes through. I don't really like the design but I don't know what else
to do"

## The design as it stands

Both repos have an `nbplotutils.py` (mvp `src/modelviewprojection/util/`, gacalc
`src/gacalc/`) built on a **module-level global**:

```python
axes: matplotlib.axes.Axes          # module global

@contextlib.contextmanager
def create_graphs(...):
    global axes
    fig, axes = plt.subplots(...)
    yield axes
    ...

def draw_isoceles_triangle(fn=..., color=...):
    axes.add_patch(triangle)        # reads the global
```

so a notebook cell reads:

```python
with create_graphs():
    draw_isoceles_triangle(fn=f)
```

## What is actually good about it (state this before changing anything)

The call site is **exactly** as short as the teaching content requires. A student sees
"make a graph, draw a triangle on it" and nothing else — no plumbing. That is not an
accident, and any alternative that puts `axes` back into every call has *lost* something
real, not merely traded style.

It also mirrors how matplotlib itself works (`plt.plot` draws on the current axes via
`gca()`), so the notebooks read like ordinary pyplot code.

## What is actually wrong with it

1. **The global is untyped-at-rest and unset until `create_graphs` runs.** gacalc's copy
   asserts `axes is not None, "call inside a create_graphs() block"` in every draw helper
   — nine copies of a runtime check that a parameter would make impossible.
   mvp's copy declares `axes: matplotlib.axes.Axes` with no value, so a call outside a
   block is a `NameError`, not a helpful message.
2. **It is invisible in the signatures.** Nothing in `def draw_isoceles_triangle(fn,
   color)` says it needs an active figure. Discovered while annotating the module
   2026-07-18: every function is now fully typed and *still* does not mention its most
   important input.
3. **Two figures cannot be built at once**, and nested `create_graphs()` blocks silently
   clobber each other.
4. **Two independent copies have already diverged** (mvp's and gacalc's), so the design
   flaw is duplicated too.

## Options to weigh

1. **Explicit parameter — `draw_isoceles_triangle(axes, fn=...)`.** Honest, typed,
   testable, no global. Cost: every notebook call site grows, and the teaching cell stops
   being one short line. **This is the option to price first, because it is the obvious
   one and its only real cost is verbosity in the exact place verbosity hurts most.**
2. **A plotter object — `plot = Plot(); with plot.graphs(): plot.isoceles_triangle(fn=f)`.**
   The axes live on `self`; signatures are honest; multiple plots coexist. Cost: `plot.`
   on every line, and a class where there were free functions.
3. **`contextvars.ContextVar` instead of a bare global.** Keeps the short call site
   *exactly* as-is, fixes nesting and thread-safety, and gives one clean "no active
   figure" error. Does **not** fix the invisible-dependency problem. Cheapest real
   improvement; smallest gain.
4. **Keep the global, but make it honest.** One `_current_axes()` accessor that raises a
   clear error, used by every helper instead of nine scattered asserts; document the
   contract in the module docstring. Cost: nearly nothing. Gain: nearly nothing
   structural.
5. **Do nothing, deliberately** — record *why* the global is right for a teaching
   notebook so the question stops recurring.

## How to decide

- **Count the call sites.** How many notebook/assignment lines would grow under option 1?
  That number is the whole argument. (`notebooksrc/plot2d.py` is the main consumer in mvp;
  gacalc's `notebooks/` has its own.)
- **Write the same cell three ways** (global / explicit / plotter object) and look at
  them side by side as a *student* would. This is a pedagogy decision more than an
  engineering one.
- **Check whether any chapter excerpts these calls.** `util/nbplotutils.py` has **no**
  `doc-region` markers and is not referenced from `book/docs/*.rst`, so the notebooks are
  the only audience — which widens the options considerably.
- **Decide both repos together.** The duplication is already a problem; fixing one and
  not the other makes it worse.

## Gate for any change

Not the test suite — **the rendered pixels**. Render every affected plot before and after
and compare with `PIL.ImageChops.difference(...).getbbox() is None`. Both repos' triangle
helpers were verified this way during the 2026-07-18 dedup, and the harness is reusable.
