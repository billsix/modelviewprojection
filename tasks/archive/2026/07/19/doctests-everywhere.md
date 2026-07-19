# Doctests for as much of the codebase as reasonable

**Status:** **COMPLETE 2026-07-19 — archived.** Doctests now run as part of the suite
(wiring done 2026-07-18) AND coverage is written for every library module where a doctest
can assert something.

**Coverage landed (this session):** `mathutils.py` (all 12 functions, incl. the 5
book-facing ones via split doc-regions), `util/shading.py` + `util/colorutils.py`,
`cayley/cayleygraph.py` (`node_label`, `CayleyGraph` acyclicity) + `cayley/cayleyscene.py`
(`interp`, `to_matrix`), `framebuffer/softwarerendering.py` (the orientation predicates),
`matrix_stack.py` (`get_current_matrix`, `push_matrix`). Suite 60 -> 96.

**Deliberately NOT doctested, and why:** the GUI / OpenGL / plotting / callback code
(`mvpvisualization/`, `demos/`, `wxapp*`, the `nbplotutils` draw helpers, `clipping`,
`axes`, `cameracontrols`, `windowing`) opens windows or draws and returns nothing to
assert -- a doctest there would be theater, not a test.

**Spun off, not part of this:** the `pytest.ini` allow-list is a permanent, small, and
adequate workaround (the follow-up to remove it is CLOSED as not-needed, see
`tasks/archive/2026/07/19/demo-main-guards-and-dedent.md`); and the anti-parallel naming
fix became `tasks/archive/2026/07/19/is-parallel-ga-semantics.md`.
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

**Correction, 2026-07-19: the allow-list does NOT block this task, and the follow-up
task that existed to remove it is closed as not-needed**
(`tasks/archive/2026/07/19/demo-main-guards-and-dedent.md`).

The allow-list already names **every library area in the repo** — `tests`, `cayley/`,
`framebuffer/`, `plotsforbook/`, `util/`, `mathutils.py`, `matrix_stack.py`. Doctests can
be written for 100% of the library right now with no restructuring. The only excluded
files are runnable scripts (`demos/`, `mvpvisualization/`) and jupytext notebooks
(`notebooksrc/`) — where a doctest has nothing to assert anyway, since they are flat
scripts that open a window and run a render loop, not callables returning values.

So the remaining work here is purely **writing doctests**, starting with the zero-coverage
library modules: `mathutils.py`, `util/`, `cayley/`, `framebuffer/`, `matrix_stack.py`.
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


## `mathutils.py` — DONE 2026-07-19 (7 functions), and the split-region plan for the other 5

**Landed:** doctests for `cosine`, `sine`, `abs_sin` (none had a docstring at all) and
appended to the existing docstrings of `find_normal`, `plane_equation`,
`distance_to_plane`, plus a new `push_transformation` docstring. **Container suite 67 ->
74**, `ty` unchanged at 11, ruff clean, nothing over 80 columns.

They teach distinctions rather than just asserting values: `cosine` vs `sine` (unsigned vs
**signed** — swapping arguments negates it), `sine` vs `abs_sin` (3D has no single turn
direction to take a sign from), `find_normal`'s winding flip as the front/back-face test,
and why `plane_equation`'s `d` is `-3.0` for the plane at `z == 3`.

### Book impact: none — and the line-number question is a non-issue by design

The seven functions appear in **no** book `doc-region`, so no chapter gained a line of
code.

An earlier draft of this section flagged that `mathutils.py` includes use `:linenos:` +
`:lineno-match:`, and that adding 175 lines shifted the displayed numbers of later
listings (`define ortho` 259 -> 395, `define perspective` 304 -> 440, and so on). **That
was raised as a problem and it is not one.** Sphinx derives those numbers from the region
markers **at build time**, so they simply render correctly against the new file. Measured:
**174 `:lineno-match:`, zero `:lineno-start:`, zero `:lines:`** — nothing in the book is
pinned to a hardcoded line range, which is the whole point of selecting by marker. Bill,
2026-07-19: *"the whole point of using those is that when code changes, sphinx will use
the new line numbers."*

The rule is now recorded in `CLAUDE.md` ("The book includes code by MARKER, not by line
number"). **The check before editing a source file is "is this text inside a published
region?" — not "did the line numbers move?"**

### The remaining 5, using split region markers (Bill, 2026-07-19)

The five book-visible functions — `rotate_around`, `ortho`, `perspective`,
`cs_to_ndc_space_fn`, `FunctionStack` — would put their docstring *inside* the listing
students read. Bill: *"look at how I deal with the regions to make sure students don't
have to read unnecessary stuff. I sometimes use multiple region markers."*

**The mechanism, confirmed by reading `demos/demo03.py`:** a `doc-region-begin` and its
`doc-region-end` are **independent text anchors and need not share a name** —
`doc-region-begin square viewport` is closed by `doc-region-end set to gray`. So a
construct can be carved into several published pieces, and the parts between them are
simply never included.

**Proposed shape** (feasibility-tested in a scratch file: the docstring still binds as
`__doc__`, doctest still collects it, and both blocks render with correct line numbers):

```python
# doc-region-begin define ortho
def ortho(left: float, right: float) -> float:
    # doc-region-end ortho signature
    """Map camera space onto NDC.

    >>> ortho(0.0, 2.0)          # doctests live here, NOT in the book
    1.0
    """
    # doc-region-begin ortho body
    return (left + right) / 2.0
    # doc-region-end define ortho
```

The chapter then carries **two** adjacent `literalinclude`s — signature, then body —
skipping the docstring entirely. Precedent exists: **25 back-to-back literalinclude pairs
with no prose between them** already appear in the book.

**Costs / caveats, inline:**
- Each of the 5 becomes **two** code blocks in the chapter instead of one, with a visible
  line-number gap where the docstring was skipped. That gap is arguably a *feature* (it
  signals something was omitted) but it is a visual change to ch16/ch17/ch18.
- A comment line sits between `def` and the docstring. Harmless (comments are not
  statements, `__doc__` is unaffected — tested) but slightly odd to read in source.
- `FunctionStack` is a **class** with methods, so it needs a decision about whether each
  method gets the same treatment or only the class-level docstring is skipped.

**Not implemented — needs a go-ahead on the shape**, since it edits 5 listings across
three chapters.
