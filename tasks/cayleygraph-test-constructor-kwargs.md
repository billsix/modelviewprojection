# Add keyword arguments to constructor calls in the cayleygraph tests (and beyond)

**Status:** done (2026-08-03)
**Priority:** 4
**Difficulty:** 3

## Goal

In `tests/test_cayley_graph.py` (and `tests/test_cayley_scene.py`) there are many constructor
calls with positional arguments where Bill "would love to see keyword arguments so I know what's
what." Investigate, **find all such positional constructor calls**, and rewrite them to use
keyword arguments for readability.

`tests/test_cayley_graph.py` is the example Bill pointed at; use it as the model, then sweep the
cayleygraph tests (and any closely-related test the same constructors appear in).

## Plan

- [x] Read `tests/test_cayley_graph.py` + `tests/test_cayley_scene.py`; identify the constructors
      called positionally (dataclasses / classes from `cayley/`, scene objects, `Vector2`/`Vector3`,
      graph nodes/edges, etc.).
- [x] For each, convert positional args → keyword args (`Foo(x=…, y=…)`), matching the callee's
      parameter names exactly. Skip cases where kwargs would be noise (a single obvious arg, or a
      value type whose positional form is idiomatic — e.g. `Vector2(1, 2)` may be clearer left as
      coords; use judgment and note the calls left positional and why).
- [x] Keep it test-only and behavior-preserving — no production code changes; tests must still pass.
- [x] Verify: `ruff check`/`ruff format` clean, `ty check tests` clean, `pytest` green for the
      touched files.

## Scope / judgment

- The bar is *readability* — kwargs where the positional arg's meaning isn't obvious at the call
  site. Don't blanket-convert every call (a `Vector2(1, 2)` coordinate literal is fine positional);
  focus on multi-arg constructors where "what's what" is unclear (Bill's words).
- Externally-fixed signatures aren't a concern here (these are Bill's own classes).

## Notes

- Origin: Bill (2026-08-03), side note while at work: "look at the tests for cayleygraph, there are
  a lot of constructors where I'd love to see keyword arguments … investigate and find all such
  things, and add keyword arguments."

## What was done (2026-08-03)

Parameter names were read from the callee source
(`src/modelviewprojection/cayley/cayleygraph.py`, `.../cayleyscene.py`), not guessed.

**`tests/test_cayley_graph.py` — 8 constructor calls converted:**

- 8 × `cayleygraph.Edge(...)` → `Edge(src=…, dst=…, steps=[…])`. The two leading
  positional strings were the directed endpoints; which one is the *source* vs
  *destination* (and an edge is directed) was not readable at the call site.
  Sites: `build_graph` (3), `test_no_path_raises` (2), `test_cyclic_graph_rejected`
  (2), `test_enum_node_identifiers` (1).

**`tests/test_cayley_scene.py` — 12 constructor calls converted:**

- 4 × `cayleygraph.Edge(...)` → `src=/dst=/steps=` (in `build_scene`), same reason.
- 4 × `cayleyscene.CoordinateFrame(...)` → `space=/parent=` for the two leading
  positional strings (`geometry=`/`dwell_before=` were already keyword). Which of the
  two strings is the node vs its parent was unclear positionally.
- 1 × `cayleyscene.InverseOperations(...)` → `from_space=/to_space=/group_title=`
  (was three bare positionals — direction + the title string all unlabeled).
- 2 × `cayleyscene.NonInvertibleTransformation(...)` → `group_title=/step_labels=`
  (a title string followed by a list of label strings; labeling makes "what's what"
  explicit).
- 1 × `cayleyscene.CameraControls(...)` → `translate_step=/rot_y_step=/rot_x_step=`
  for the three leading `cam_edge.steps[0..2]` positionals. That `steps[1]` is the
  *rot_y* step and `steps[2]` the *rot_x* step was invisible at the call site;
  `px…rot_x` were already keyword.

**Left positional deliberately:**

- `Vector3(x, y, z)` coordinate literals — idiomatic positional coords; `x=/y=/z=`
  would be noise (matches the task's own guidance and the repo's demo style).
- `cayleygraph.CayleyGraph([...])` — one obvious argument (the list of edges).
- `cayleyscene.Timeline(build_scene())` / `cayleyscene.Animation(build_scene())` —
  one obvious argument (the scene).
- `("T", translate(...))` pairs inside `steps=[...]` — these are `(label, fn)` tuple
  literals, not constructor calls; `Edge` documents and coerces this pair form to
  `Step`. Not touched.
- `cayleyscene.Scene(graph=…, root=…, coordinate_frames=…)` — already all keyword.

## Verification (2026-08-03)

- `ruff format --check tests/test_cayley_graph.py tests/test_cayley_scene.py` → both
  already formatted.
- `ruff check` on both files → All checks passed.
- `pytest tests/test_cayley_graph.py tests/test_cayley_scene.py` → 29 passed.
- `ty`: the two touched files carry only `unresolved-import` diagnostics (pytest /
  numpy), an artifact of this host splitting packages across `/usr` and `/usr/local`
  prefixes (ty resolves only one prefix per run); there are **zero** type errors from
  the kwargs changes. The `invalid-*` diagnostics ty reports are all pre-existing in
  `test_mathutils.py`, which this task did not touch. In the container (single venv)
  `ty check tests` resolves normally.
