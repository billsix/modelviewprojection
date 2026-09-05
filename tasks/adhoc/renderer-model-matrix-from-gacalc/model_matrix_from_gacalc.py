#!/usr/bin/env python3
# Copyright (c) 2026 William Emerison Six
#
# Codemod for tasks/renderer-model-matrix-from-gacalc.md: in each Code-the-
# Classics game engine (the OpenGL 3.3 ones -- boing_gl1's fixed-function path
# has no matrix to build), define the sprite model matrix and the orthographic
# projection with gacalc's transforms instead of hand-built numpy.
#
#   _translate(x, y) / _scale(sx, sy)   -> removed
#   ortho_pixels(width, height)         -> to_matrix(translate @ scale_non_uniform)
#   (new) MatrixTemplate + MODEL         -> the model matrix compiled ONCE over
#                                          sympy symbols; MODEL.fill(tx, ty, w, h)
#   _translate(x=a, y=b) @ _scale(sx=c, sy=d)  ->  MODEL.fill(a, b, c, d)
#
# The three helper functions are located with `ast` and must match the text
# every engine shares (asserted -- an unfamiliar body aborts the file untouched);
# the imports are merged into the existing gacalc lines. Idempotent: a file
# that already has MatrixTemplate is left alone. Run from the repo root:
#   python tasks/adhoc/renderer-model-matrix-from-gacalc/model_matrix_from_gacalc.py <game.py>...
# then `ruff check --fix` + `ruff format` the files.

import ast
import re
import sys
from pathlib import Path

EXPECTED = {
    "_translate": '''def _translate(x: float, y: float) -> NDArray[np.float32]:
    """Return a 4x4 translation by ``(x, y)`` pixels."""
    m: NDArray[np.float32] = _identity()
    m[0, 3] = x
    m[1, 3] = y
    return m
''',
    "_scale": '''def _scale(sx: float, sy: float) -> NDArray[np.float32]:
    """Return a 4x4 non-uniform scale by ``(sx, sy)``."""
    m: NDArray[np.float32] = _identity()
    m[0, 0] = sx
    m[1, 1] = sy
    return m
''',
    "ortho_pixels": '''def ortho_pixels(width: float, height: float) -> NDArray[np.float32]:
    """Map pixel space (0,0)=top-left .. (width,height)=bottom-right to NDC."""
    m: NDArray[np.float32] = _identity()
    m[0, 0] = 2.0 / width
    m[0, 3] = -1.0
    m[1, 1] = -2.0 / height
    m[1, 3] = 1.0
    m[2, 2] = -1.0
    return m
''',
}

NEW_BLOCK = '''# The sprite's model matrix (scale the unit quad to w x h, then move it to
# (tx, ty) pixels) and the orthographic projection are DEFINED with gacalc's
# transforms -- the course's own math -- and converted to the GL 4x4 by
# ``to_matrix``, which puts the translation in the last column (column vectors,
# premultiply; the ``GL_TRUE`` on upload transposes into GL's layout). The model
# matrix is needed per sprite per frame, so it is converted ONCE, at import,
# over sympy symbols, into a template that a draw fills by poking four numbers:
# 0.47 microseconds a sprite, against 3.19 for two numpy matrices and a matmul
# (tasks/reference/gacalc-transforms-in-the-renderer.md).


@dataclass(slots=True, frozen=True)
class MatrixTemplate:
    """A 4x4 matrix with a few varying entries: its constant part, and the
    (row, column, parameter) of each entry that is a parameter -- read off a
    gacalc transform built over sympy symbols. Build one with
    :meth:`MatrixTemplate.compile`.
    """

    #: the matrix with every parameter entry zeroed
    constants: NDArray[np.float32]
    #: (row, column, index into fill()'s arguments) per parameter entry
    slots: tuple[tuple[int, int, int], ...]

    @classmethod
    def compile(
        cls, fn: InvertibleFunction[g3.Vector], params: Sequence[sympy.Symbol]
    ) -> MatrixTemplate:
        """The template of ``fn``, a gacalc transform over the symbols ``params``."""
        m = to_matrix(fn, g3.Vector, backend="sympy")
        assert isinstance(m, sympy.Matrix)
        constants: NDArray[np.float32] = np.array(
            [
                [0.0 if m[i, j].free_symbols else float(m[i, j]) for j in range(4)]
                for i in range(4)
            ],
            dtype=np.float32,
        )
        slots = tuple(
            (i, j, params.index(m[i, j]))
            for i in range(4)
            for j in range(4)
            if m[i, j].free_symbols
        )
        return cls(constants, slots)

    def fill(self, *params: float) -> NDArray[np.float32]:
        """The matrix for these parameter values."""
        m: NDArray[np.float32] = self.constants.copy()
        for row, col, k in self.slots:
            m[row, col] = params[k]
        return m


_TX, _TY, _W, _H = sympy.symbols("tx ty w h")
#: The model matrix: scale the unit quad to (w, h), then translate to (tx, ty);
#: ``MODEL.fill(tx, ty, w, h)``
MODEL: MatrixTemplate = MatrixTemplate.compile(
    translate(b=_TX * g3.Vector.e_1 + _TY * g3.Vector.e_2)
    @ scale_non_uniform(_W, _H, 1),
    (_TX, _TY, _W, _H),
)


def ortho_pixels(width: float, height: float) -> NDArray[np.float32]:
    """Map pixel space (0,0)=top-left .. (width,height)=bottom-right to NDC:
    scale to a 2 x 2 box (y flipped, z into the clip range), then move its
    corner to (-1, 1). Built once per renderer.
    """
    return np.asarray(
        to_matrix(
            translate(b=-1 * g3.Vector.e_1 + 1 * g3.Vector.e_2)
            @ scale_non_uniform(2.0 / width, -2.0 / height, -1),
            g3.Vector,
        ),
        dtype=np.float32,
    )
'''

CALL = re.compile(r"_translate\(x=(\w+), y=(\w+)\) @ _scale\(\s*sx=([^,]+), sy=([^)]+?)\s*\)")
NEEDED = {"InvertibleFunction", "scale_non_uniform", "to_matrix", "translate"}


def convert(src: str) -> str | None:
    if "class MatrixTemplate" in src:
        return None
    tree = ast.parse(src)
    lines = src.splitlines(keepends=True)
    fns = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in EXPECTED}
    assert set(fns) == set(EXPECTED), sorted(fns)
    for name, node in fns.items():
        got = "".join(lines[node.lineno - 1 : node.end_lineno])
        assert got == EXPECTED[name], f"{name} differs from the shared text:\n{got}"
    t, s, o = fns["_translate"], fns["_scale"], fns["ortho_pixels"]
    assert t.end_lineno < s.lineno < o.lineno, "helpers not in the expected order"
    # replace the span from _translate's first line to ortho_pixels' last line
    out = "".join(lines[: t.lineno - 1]) + NEW_BLOCK + "".join(lines[o.end_lineno :])
    sites = out.count("_translate(x=")  # 1 in boing (draw_image only), 3 with region/filled_rect
    out, n = CALL.subn(r"MODEL.fill(\1, \2, \3, \4)", out)
    assert 1 <= n == sites, f"rewrote {n} of {sites} model-matrix call sites"
    assert "_translate(" not in out and "_scale(" not in out
    # imports: sympy, g3, and the gacalc.transforms names (merged with an existing line)
    if "\nimport sympy\n" not in out:
        out = out.replace("\nimport numpy as np\n", "\nimport numpy as np\nimport sympy\n", 1)
    g2line = re.search(r"^from gacalc\.g2 import [^\n]+\n", out, re.M)
    assert g2line, "no `from gacalc.g2 import` line to anchor the gacalc imports on"
    if "\nimport gacalc.g3 as g3\n" not in out:
        out = out[: g2line.start()] + "import gacalc.g3 as g3\n" + out[g2line.start() :]
    m = re.search(r"^from gacalc\.transforms import ([^\n]+)\n", out, re.M)
    if m:
        names = sorted(NEEDED | {x.strip() for x in m.group(1).split(",")})
        out = out[: m.start()] + "from gacalc.transforms import " + ", ".join(names) + "\n" + out[m.end() :]
    else:
        g2line = re.search(r"^from gacalc\.g2 import [^\n]+\n", out, re.M)
        assert g2line
        out = out[: g2line.end()] + "from gacalc.transforms import " + ", ".join(sorted(NEEDED)) + "\n" + out[g2line.end() :]
    # MatrixTemplate.compile is annotated with Sequence; the vol1 engines don't import it
    c = re.search(r"^from collections\.abc import ([^\n]+)\n", out, re.M)
    assert c, "no collections.abc import line"
    cnames = sorted({x.strip() for x in c.group(1).split(",")} | {"Sequence"})
    out = out[: c.start()] + "from collections.abc import " + ", ".join(cnames) + "\n" + out[c.end() :]
    assert "import sympy" in out and "gacalc.g3 as g3" in out
    return out


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        p = Path(arg)
        new = convert(p.read_text())
        if new is not None:
            p.write_text(new)
        print(f"{p}: {'converted' if new is not None else 'already converted'}")
