#!/usr/bin/env python3
# Copyright (c) 2026 William Emerison Six
#
# Benchmark for tasks/pgzero-gl-renderer-matrix-via-gacalc-perf.md: the cost of
# building a sprite's 4x4 model matrix (translate by (tx, ty), then scale by
# (w, h) -- the games' `_translate(tx, ty) @ _scale(w, h)`) five ways:
#
#   hand-built numpy   -- what the games do today (two 4x4s and a matmul)
#   template fill      -- copy one identity and poke the four numbers in
#   to_matrix per call -- gacalc's transform -> matrix bridge, called per sprite
#   gacalc, lambdified -- to_matrix ONCE with sympy symbols, then a compiled
#                         numpy function of (tx, ty, w, h) per sprite
#   gacalc, compiled   -- to_matrix ONCE with sympy symbols, read off WHICH
#                         entries are which symbol, then template-fill per sprite
#
# The last two keep gacalc as the definition of the transform while paying the
# probe-the-basis cost once, not per draw. All five are checked equal first.
# Run in the project container:
#   python tasks/adhoc/pgzero-gl-renderer-matrix-via-gacalc-perf/bench_model_matrix.py

import timeit

import numpy as np
import sympy
from gacalc import g3
from gacalc.transforms import scale_non_uniform, to_matrix, translate
from numpy.typing import NDArray

N = 20_000
tx, ty, w, h = 123.0, 45.0, 32.0, 48.0


def _identity() -> NDArray[np.float32]:
    return np.identity(4, dtype=np.float32)


def _translate(x: float, y: float) -> NDArray[np.float32]:
    m = _identity(); m[0, 3] = x; m[1, 3] = y  # noqa: E702
    return m


def _scale(sx: float, sy: float) -> NDArray[np.float32]:
    m = _identity(); m[0, 0] = sx; m[1, 1] = sy  # noqa: E702
    return m


def hand_built(tx: float, ty: float, w: float, h: float) -> NDArray[np.float32]:
    return _translate(tx, ty) @ _scale(w, h)


_TEMPLATE = _identity()


def template_fill(tx: float, ty: float, w: float, h: float) -> NDArray[np.float32]:
    m = _TEMPLATE.copy()
    m[0, 0] = w; m[1, 1] = h; m[0, 3] = tx; m[1, 3] = ty  # noqa: E702
    return m


def to_matrix_per_call(tx: float, ty: float, w: float, h: float) -> NDArray[np.float32]:
    return to_matrix(
        translate(b=tx * g3.Vector.e_1 + ty * g3.Vector.e_2)
        @ scale_non_uniform(w, h, 1),
        g3.Vector,
    )


# --- gacalc once, symbolically ------------------------------------------------
STX, STY, SW, SH = sympy.symbols("tx ty w h")
M_SYM = to_matrix(
    translate(b=STX * g3.Vector.e_1 + STY * g3.Vector.e_2) @ scale_non_uniform(SW, SH, 1),
    g3.Vector,
    backend="sympy",
)
_lambdified = sympy.lambdify((STX, STY, SW, SH), M_SYM, "numpy")


def gacalc_lambdified(tx: float, ty: float, w: float, h: float) -> NDArray[np.float32]:
    return np.asarray(_lambdified(tx, ty, w, h), dtype=np.float32)


# which (row, col) holds which parameter, read off the symbolic matrix once
_CONST = np.array([[float(e) if not e.free_symbols else 0.0 for e in M_SYM.row(i)] for i in range(4)], dtype=np.float32)
_SLOTS: list[tuple[int, int, int]] = [
    (i, j, [STX, STY, SW, SH].index(M_SYM[i, j]))
    for i in range(4) for j in range(4) if M_SYM[i, j].free_symbols
]


def gacalc_compiled(tx: float, ty: float, w: float, h: float) -> NDArray[np.float32]:
    m = _CONST.copy()
    args = (tx, ty, w, h)
    for i, j, k in _SLOTS:
        m[i, j] = args[k]
    return m


BUILDERS = [
    ("hand-built numpy (today)", hand_built),
    ("template fill", template_fill),
    ("to_matrix per call", to_matrix_per_call),
    ("gacalc once, lambdified", gacalc_lambdified),
    ("gacalc once, compiled fill", gacalc_compiled),
]
ref = hand_built(tx, ty, w, h)
for name, fn in BUILDERS:
    assert np.allclose(fn(tx, ty, w, h), ref), name
print("symbolic model matrix from gacalc:"); sympy.pprint(M_SYM)  # noqa: E702
print(f"\n{'builder':30} {'µs/call':>9} {'vs hand-built':>14}")
base = None
for name, fn in BUILDERS:
    n = N // 100 if fn is to_matrix_per_call else N
    us = min(timeit.repeat(lambda: fn(tx, ty, w, h), number=n, repeat=5)) / n * 1e6
    base = base or us
    print(f"{name:30} {us:9.2f} {us / base:13.1f}x")
