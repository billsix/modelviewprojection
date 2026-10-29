# Parameterize bare generic type annotations

**Status:** done (2026-10-29). **Priority:** 5  **Difficulty:** 2

## BLUF

~56 annotations across the demos, `mvpvisualization/`, `cayley/`, `notebooksrc/`,
`pgzero_gl/`, the `ports/openglsuperbiblev4` ports, `tests/`, and `tools/` use a
bare `list`/`tuple`/`dict`/`type` where a parameter belongs; a bare generic
silently degrades its parameters to implicit `Any` (shared Python standard,
"Parameterize generic types"). Give each real parameters. "Done" = every site
parameterized and `make type-check` (ty + `check_local_annotations.py`) green.

## Context (cold-start)

Found by an AST scan for annotations whose value is a generic container left
unsubscripted. Fix policy (maintainer's rule: an explicit `Any` parameter beats
no parameter):

- **Precise where it is clean** — RGB colour constants `tuple[float, float,
  float]`; GL id lists `list[int]`; `frame_good` `list[bool]`; wireframe edges
  `list[tuple[tuple[float, float, float], tuple[float, float, float]]]`; cylinder
  bands/rings `list[tuple[float, ...]]` / `list[list[tuple[float, ...]]]`; demo24
  vertices the exact `(pos, normal, uv)` type `vert()` already returns; `cayley`
  adjacency `Dict[N, list[N]]` / `Dict[N, tuple[N, ...]]`; `factorial`'s callback
  `Callable[..., int]` (the test passes `factorial` to itself, a 2-arg function —
  `Callable[[int], int]` would be wrong).
- **`Any`-parameterized where the literal is genuinely heterogeneous / deeply
  nested** — the demo/port geometry tables (`PLANETS`, `faces`, `triangles`,
  `_JET_TRIS`, `walls`, …) are `list[tuple[Any, ...]]`; `pixels`/`frames`/
  `runpy` globals / trace rows are `list[Any]` / `dict[str, Any]`; the renderer
  selector is `tuple[type[Any], bool]`. Precise nested types here would be long
  and no clearer; `Any` keeps the parameter explicit.

Three `tools`/`notebooksrc` files gain `from typing import Any`.

## Scanner false positives / out-of-scope — NOT changed (with reason)

- `book/docs/_gacalc_src/nbplotutils.py` (5 sites) — this directory is a
  **gitignored build-time copy** of gacalc (`entrypoint/entrypoint.sh` /
  `Makefile` `cp /opt/gacalc-src/*.py`); the real fix lands in gacalc. Not edited.
- `ports/codetheclassics/vol1/cavern/cavern.py:1352,1360` `self.type: Fruit.Type`
  / `types: list[Fruit.Type]` — `Fruit.Type` is a user-defined nested enum, **not**
  `typing.Type`; already correctly parameterized. Not a bare generic.

## Verification

`make type-check` (containerized ty + the local-annotation completeness check).
Annotation-only; no runtime behaviour change. (`make type-check`, not `make
format`, so the gate does not reformat unrelated files as a side effect.)
