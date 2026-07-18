# Investigate: does the book's plotting code teach transforms the way the GL code does?

**Status:** **INVESTIGATED 2026-07-19 — the premise was wrong; recommendation is a
small, local change.** See "Findings" below. No code changed yet.
**Created:** 2026-07-18
**Requested by:** Bill, 2026-07-18 — "investigate what makes more sense to a student"

## The question

The matplotlib plotting code (`src/modelviewprojection/plotsforbook/plotutils/`) builds
2-D transforms by **piping a function over the point data**. The OpenGL side of the same
book teaches transforms very differently — a matrix stack, composed
`InvertibleFunction`s, `Vector2`/`Vector3` values. **Are we teaching one idea in two
unrelated vocabularies?** If so, which one should the plots use?

This task is to *investigate and recommend*, not to rewrite. The current design may well
be the right one for its chapter — Bill's note: "maybe that's good for students to
understand."

## What the plotting code does today

`mpltransformations.py` is built on one primitive:

```python
def map_matplotlib_data(f, *points_on_axis):
    return zip(*map(f, zip(*points_on_axis)))
```

matplotlib wants **parallel arrays** (`xs`, `ys`), but a transform is naturally
point-at-a-time. So `map_matplotlib_data` zips the axes into points, maps `f` over them,
and unzips back into axes. Each transform is then a curried function returning a
function over `(xs, ys)`:

```python
def scale(scale_x, scale_y):
    return lambda xs, ys: map_matplotlib_data(
        lambda point: (point[0] * scale_x, point[1] * scale_y), xs, ys)
```

Composition at the call site is **nested application with re-splatting**, because each
stage returns a tuple of axes that the next stage must take as separate arguments
(`matplotgraphs.py:66`):

```python
mplt.translate(2, 2)(
    *mplt.scale(math.sqrt(8), math.sqrt(8))(
        *mplt.rotate(math.radians(45.0))(xs, ys)))
```

## Why it is worth questioning

- **Reading order is inside-out.** The `*`-splat between stages makes it hard to see that
  this is "rotate, then scale, then translate" — the order a student is being taught.
- **It is a different vocabulary from the rest of the book.** Elsewhere the same idea is
  `compose([...])` over `InvertibleFunction`s, or a `pyMatrixStack` push/pop, over
  `Vector2` values. A student meeting both may not realize they are the same concept.
- **The axes/points impedance mismatch is incidental** — it exists because matplotlib
  takes parallel arrays, not because transforms work that way. Right now that plumbing is
  visible in every call.
- **No inverses, no interpolation.** The GL side gets `inverse()` and `at(t)` free from
  `InvertibleFunction`; these plot transforms are one-directional plain callables.

**The counter-argument, which the investigation must take seriously:** function-piping is
*explicitly* what some chapters teach — first-class functions, currying, composition —
and seeing a transform as a plain function applied to points may be exactly the right
first exposure, *before* matrices are introduced. Making the plots match the GL code
could rob an early chapter of its point. **Check which chapters include this code and
what the surrounding prose claims** before recommending anything.

## Findings (2026-07-19)

Two measurements overturn the framing this task was written with.

### 1. The book never shows this code. It is build tooling, not teaching material.

- **0** references to `mpltransformations` / `plotsforbook` / `generate_plots` anywhere in
  `book/docs/*.rst`.
- **0** `doc-region` markers in any of the four plotting modules.
- The book consumes only the *output*: `.. figure:: _static/plot1.svg`, produced by the
  `generate_plots_for_book` entry point that `book/docs/_static/Makefile` runs.

**This kills the main argument for keeping the design as-is.** The task assumed the prose
might teach "a transform is a function", making the function-piping style pedagogically
load-bearing. It does not, because a student never sees this source. The design should be
judged purely on maintainability, and its only audience is whoever edits the plot
generator.

### 2. The ugly pattern is ONE expression, not a pervasive style.

Of **51** uses of `mplt.translate` / `rotate` / `scale`:

- **50** pass transforms as a **list** -- `procedures=[mplt.translate(-9.0, 2.0)]` --
  which `create_graphs` composes via `accumulate_transformation`. That is already
  list-based composition, and it reads fine.
- **1** uses the nested-splat form, in `matplotgraphs.py:65-71`:

  ```python
  transformed_xs, transformed_ys = list(
      mplt.translate(2, 2)(
          *mplt.scale(math.sqrt(8), math.sqrt(8))(
              *mplt.rotate(math.radians(45.0))(xs, ys))))
  ```

So there is no pervasive design problem to fix -- there is one call site that does not
use the composition idiom the rest of the file already uses.

## Recommendation

**Do not rewrite the model.** Neither the `InvertibleFunction`/`Vector2` migration nor a
plotter-object redesign is justified: the code is not read by students, 50 of 51 call
sites already compose via a list, and the module works.

**Do add a small `compose` to `mpltransformations` and use it at the one site**, so the
transforms read in the order they are written instead of inside-out:

```python
def compose(*transforms):
    """Apply `transforms` right-to-left, like function composition."""
    def composed(xs, ys):
        for transform in reversed(transforms):
            xs, ys = transform(xs, ys)
        return xs, ys
    return composed
```

```python
to_rotated_scaled_translated = mplt.compose(
    mplt.translate(2, 2),
    mplt.scale(math.sqrt(8), math.sqrt(8)),
    mplt.rotate(math.radians(45.0)),
)
transformed_xs, transformed_ys = to_rotated_scaled_translated(xs, ys)
```

Cost: ~8 new lines, one call site changed. Gate: the generated figures must be
pixel-identical (`generate_plots_for_book` emits 170 SVGs).

**Then annotate the module** -- it is the last deferred piece of the annotation sweep
(5 functions), and `compose` settles what the types should be.

## What to investigate

1. **Which chapters excerpt this code, and what do they say it demonstrates?** Grep
   `book/docs/*.rst` for `literalinclude` of `plotsforbook`/`mpltransformations`. If the
   prose teaches "a transform is a function," that is decisive and the answer may be
   "leave it, but document why."
2. **Where does it sit in the arc?** If the plots come *before* matrices are introduced,
   function-piping is pedagogically prior and should probably stay. If they come after,
   consistency with the GL vocabulary is more defensible.
3. **Would `InvertibleFunction` + `Vector2` work here?** gacalc vectors are already used
   throughout the GL demos. Sketch what `matplotgraphs.py:66` would look like as
   `compose([translate(...), uniform_scale(...), rotate(...)])` applied to a list of
   `Vector2` — including how the axes/points conversion gets hidden (probably one
   `to_axes(points)` helper at the matplotlib boundary, instead of splatting at every
   stage).
4. **Cheaper middle grounds**, if a full rewrite is not warranted:
   - keep the model, add a `compose`/pipeline helper so the call site reads in
     application order instead of inside-out;
   - keep the model, fix only the `*`-splat by having each stage take and return one
     value;
   - keep everything, add a comment in the module explaining the deliberate difference
     from the GL side and pointing at the chapter that motivates it.
5. **Cost:** how many call sites (`matplotgraphs.py`, `generate_plots.py`,
   `nbplotutils.py`), how many book excerpts, and would any rendered figure change?
   A plot that changes pixels is a book change, not a refactor.

## Deliverable

A recommendation with the chapter evidence attached: keep / adjust-lightly / rewrite, and
if changing, what the call sites and the excerpted code would look like. **No code
changes until Bill picks an option.**

## Related

- `tasks/apply-python-coding-standard.md` — the naming pass already touched these files
  (`mapMatplotlibData` -> `map_matplotlib_data`, `scaleX`/`scaleY` -> `scale_x`/`scale_y`).
- `tasks/doctests-everywhere.md` — `mpltransformations.py` holds 2 of the repo's only
  doctests; any rewrite must keep them meaningful.
