#!/usr/bin/env python3
"""Parameterize the repo's bare generic annotations (list/tuple/dict/type).

One-shot codemod for tasks/parameterize-bare-generic-annotations.md. Each edit is
an exact-literal replacement with an asserted occurrence count, so a drifted line
fails loudly instead of silently mis-editing; demo24's 12 uniform vertices use a
regex. Idempotent: a second run finds the (now-parameterized) originals absent and
reports zero changes. Paths are resolved relative to the repo root, not hardcoded.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO: Path = Path(__file__).resolve().parents[3]

VERT: str = (
    "tuple[tuple[float, float, float], "
    "tuple[float, float, float], tuple[float, float]]"
)
EDGE: str = "list[tuple[tuple[float, float, float], tuple[float, float, float]]]"
BAND: str = "list[tuple[float, ...]]"
RINGS: str = "list[list[tuple[float, ...]]]"
COLOR: str = "tuple[float, float, float]"

# file -> list of (old, new, expected_count). Order matters where one old string
# is a prefix of another (bands before band, "= []" before "= [").
EDITS: dict[str, list[tuple[str, str, int]]] = {
    "src/modelviewprojection/demos/demo19d.py": [
        ("PLANETS: list = [", "PLANETS: list[tuple[Any, ...]] = [", 1),
    ],
    "src/modelviewprojection/demos/demo22/demo22.py": [
        ("LIGHT_MARKER_CONE_COLOR: tuple = (", f"LIGHT_MARKER_CONE_COLOR: {COLOR} = (", 1),
        ("LIGHT_MARKER_BULB_COLOR: tuple = (", f"LIGHT_MARKER_BULB_COLOR: {COLOR} = (", 1),
        ("faces: list = [", "faces: list[tuple[Any, ...]] = [", 1),
        ("faces_to_draw: list = [", "faces_to_draw: list[tuple[Any, ...]] = [", 1),
    ],
    "src/modelviewprojection/demos/demo22a/demo22a.py": [
        ("LIGHT_MARKER_CONE_COLOR: tuple = (", f"LIGHT_MARKER_CONE_COLOR: {COLOR} = (", 1),
        ("LIGHT_MARKER_BULB_COLOR: tuple = (", f"LIGHT_MARKER_BULB_COLOR: {COLOR} = (", 1),
        ("triangles: list = [", "triangles: list[tuple[Any, ...]] = [", 1),
    ],
    "src/modelviewprojection/demos/demo23/demo23.py": [
        ("_JET_TRIS: list = [", "_JET_TRIS: list[tuple[Any, ...]] = [", 1),
        ("LIGHT_MARKER_CONE_COLOR: tuple = (", f"LIGHT_MARKER_CONE_COLOR: {COLOR} = (", 1),
        ("LIGHT_MARKER_BULB_COLOR: tuple = (", f"LIGHT_MARKER_BULB_COLOR: {COLOR} = (", 1),
    ],
    "src/modelviewprojection/demos/demo22b/demo22b.py": [
        ("LIGHT_MARKER_CONE_COLOR: tuple = (", f"LIGHT_MARKER_CONE_COLOR: {COLOR} = (", 1),
        ("LIGHT_MARKER_BULB_COLOR: tuple = (", f"LIGHT_MARKER_BULB_COLOR: {COLOR} = (", 1),
        ("faces_to_draw: list = [", "faces_to_draw: list[tuple[Any, ...]] = [", 1),
    ],
    "src/modelviewprojection/demos/demo22b/export_scene.py": [
        ("faces: list = [", "faces: list[tuple[Any, ...]] = [", 1),
    ],
    "src/modelviewprojection/mvpvisualization/_pipeline.py": [
        ("edges: list = []", f"edges: {EDGE} = []", 1),
        ("edges: list = [", f"edges: {EDGE} = [", 1),
        ("edges: list,", f"edges: {EDGE},", 1),
    ],
    "src/modelviewprojection/mvpvisualization/cayley_gl.py": [
        ("verts: list = []", "verts: list[float] = []", 1),
    ],
    "src/modelviewprojection/notebooksrc/ndc.py": [
        ("import warnings\n", "import warnings\nfrom typing import Any\n", 1),
        ("frames: list = []", "frames: list[Any] = []", 1),
    ],
    "src/modelviewprojection/cayley/cayleygraph.py": [
        # adjacency values are (neighbor, edge, walked_forward) = (N, Edge, bool);
        # only `directed` holds bare dst nodes (N).
        ("adj: typing.Dict[N, list] = {}", "adj: typing.Dict[N, list[tuple[N, Edge, bool]]] = {}", 1),
        (
            "self._adj: typing.Dict[N, tuple] = {k: tuple(v) for k, v in adj.items()}",
            "self._adj: typing.Dict[N, tuple[tuple[N, Edge, bool], ...]] = {k: tuple(v) for k, v in adj.items()}",
            1,
        ),
        ("directed: typing.Dict[N, list] = {}", "directed: typing.Dict[N, list[N]] = {}", 1),
    ],
    "src/modelviewprojection/pgzero_gl/runner.py": [
        (
            "def _select_renderer() -> tuple[type, bool]:",
            "def _select_renderer() -> tuple[type[Any], bool]:",
            1,
        ),
    ],
    "ports/openglsuperbiblev4/chapt05/spot/spot.py": [
        ("bands: list = []", f"bands: {RINGS} = []", 1),
        ("band: list = []", f"band: {BAND} = []", 1),
        (
            "band: list = [(0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0)]",
            f"band: {BAND} = [(0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0)]",
            1,
        ),
    ],
    "ports/openglsuperbiblev4/chapt10/axes3d/axes3d.py": [
        (") -> list:", f") -> {RINGS}:", 1),
        ("rings: list = []", f"rings: {RINGS} = []", 1),
        (
            "band: list = [(0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0)]",
            f"band: {BAND} = [(0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0)]",
            1,
        ),
        (
            "CYLINDER_RINGS: list = _build_cylinder_rings(",
            f"CYLINDER_RINGS: {RINGS} = _build_cylinder_rings(",
            1,
        ),
    ],
    "ports/openglsuperbiblev4/chapt17/bumpmap/bumpmap.py": [
        ("faces: list = [", "faces: list[tuple[Any, ...]] = [", 1),
    ],
    "ports/openglsuperbiblev4/chapt18/fbodrawbuffers/fbodrawbuffers.py": [
        ("walls: list = [", "walls: list[tuple[Any, ...]] = [", 1),
    ],
    "ports/openglsuperbiblev4/chapt18/fboenvmap/fboenvmap.py": [
        ("walls: list = [", "walls: list[tuple[Any, ...]] = [", 1),
    ],
    "ports/openglsuperbiblev4/chapt18/hdrbloom/hdrbloom.py": [
        ("texture_id: list = [0] * 7", "texture_id: list[int] = [0] * 7", 1),
        ("framebuffer_id: list = [0] * 5", "framebuffer_id: list[int] = [0] * 5", 1),
    ],
    "ports/openglsuperbiblev4/chapt18/pixbufobj/pixbufobj.py": [
        ("pixels: list = [", "pixels: list[Any] = [", 1),
        ("frame_good: list = [False, False, False]", "frame_good: list[bool] = [False, False, False]", 1),
        ("pbo_ids: list = []", "pbo_ids: list[int] = []", 1),
    ],
    "ports/openglsuperbiblev4/chapt19/SphereWorld32/SphereWorld32.py": [
        ("sphere_positions: list = []", "sphere_positions: list[tuple[float, float]] = []", 1),
    ],
    "tests/test_firstclassfunctions.py": [
        (
            "def factorial(n: int, f: typing.Callable) -> int:",
            # f is factorial itself (called `f(n - 1, f)`), a 2-arg function
            "def factorial(n: int, f: typing.Callable[..., int]) -> int:",
            1,
        ),
    ],
    "tools/ctc_compare_traces.py": [
        ("from pathlib import Path\n", "from pathlib import Path\nfrom typing import Any\n", 1),
        ("def load(path: str) -> list:", "def load(path: str) -> list[Any]:", 1),
    ],
    "tools/render_probe.py": [
        ("import sys\n", "import sys\nfrom typing import Any\n", 1),
        (
            'state: dict = {"frames": 0, "swaps": 0, "image": None}',
            'state: dict[str, Any] = {"frames": 0, "swaps": 0, "image": None}',
            1,
        ),
        (
            'globals_after: dict = runpy.run_path(args.script, run_name="__main__")',
            'globals_after: dict[str, Any] = runpy.run_path(args.script, run_name="__main__")',
            1,
        ),
    ],
}

# demo24: 12 uniform (pos, normal, uv) vertices p00/p10/p01/p11.
DEMO24: str = "src/modelviewprojection/demos/demo24/demo24.py"
DEMO24_RE: re.Pattern[str] = re.compile(r"(p[01][01]): tuple =")

# Files whose new annotations use bare `Any` but only `import typing` (no direct
# `Any` binding) -- give each `from typing import Any` after any __future__ import.
IMPORT_ANY: list[str] = [
    "src/modelviewprojection/demos/demo19d.py",
    "src/modelviewprojection/demos/demo22/demo22.py",
    "src/modelviewprojection/demos/demo22a/demo22a.py",
    "src/modelviewprojection/demos/demo23/demo23.py",
    "src/modelviewprojection/demos/demo22b/demo22b.py",
    "ports/openglsuperbiblev4/chapt17/bumpmap/bumpmap.py",
    "ports/openglsuperbiblev4/chapt18/fbodrawbuffers/fbodrawbuffers.py",
    "ports/openglsuperbiblev4/chapt18/fboenvmap/fboenvmap.py",
    "ports/openglsuperbiblev4/chapt18/pixbufobj/pixbufobj.py",
]


def main() -> None:
    total: int = 0
    for rel, edits in EDITS.items():
        path: Path = REPO / rel
        text: str = path.read_text()
        for old, new, count in edits:
            found: int = text.count(old)
            if found != count:
                raise SystemExit(f"{rel}: expected {count}x {old!r}, found {found}")
            text = text.replace(old, new)
            total += count
        path.write_text(text)

    d24: Path = REPO / DEMO24
    d24_text: str = d24.read_text()
    d24_new: str
    n24: int
    d24_new, n24 = DEMO24_RE.subn(rf"\1: {VERT} =", d24_text)
    if n24 != 12:
        raise SystemExit(f"{DEMO24}: expected 12 vertex annotations, found {n24}")
    d24.write_text(d24_new)
    total += n24

    for rel in IMPORT_ANY:
        p = REPO / rel
        lines: list[str] = p.read_text().splitlines(keepends=True)
        if any("from typing import Any" in ln for ln in lines):
            continue
        future: int | None = max(
            (i for i, ln in enumerate(lines) if ln.startswith("from __future__")),
            default=None,
        )
        idx: int = (
            future + 1
            if future is not None
            else next(i for i, ln in enumerate(lines) if ln.startswith(("import ", "from ")))
        )
        lines.insert(idx, "from typing import Any\n")
        p.write_text("".join(lines))
        total += 1

    print(f"applied {total} edits across {len(EDITS) + 1} files")


if __name__ == "__main__":
    main()
