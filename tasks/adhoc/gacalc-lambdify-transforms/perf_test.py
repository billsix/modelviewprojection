#!/usr/bin/env python3
# Copyright (c) 2026 William Emerison Six
#
# Perf + correctness harness behind
# tasks/reference/gacalc-symbolic-transforms-and-lambdify.md.
#
# Question: can the pgzero_gl renderer build its per-sprite GPU matrix (uModel)
# from the maintainer's own gacalc transforms instead of hand-written numpy?
# And can a 90-degree rotation be a NAMED gacalc call instead of raw `* e_12`?
#
# Run in the mvp container (needs gacalc + sympy + numpy):
#   podman run --rm --entrypoint /bin/bash -v "$(pwd)":/mvp:Z \
#     localhost/modelviewprojection:latest -lc \
#     'source /venv/bin/activate; python /mvp/tasks/adhoc/gacalc-lambdify-transforms/perf_test.py'
#
# Findings (measured 2026-09-04, software-GL mvp container; absolute us vary by
# host, the RATIOS are the point):
#   model matrix : hand-built numpy      ~3.9 us/call   (current renderer)
#                  gacalc to_matrix/call ~1669 us/call  (~492x  -- non-starter)
#                  symbolic once+lambdify ~1.5 us/call   (~0.4x -- FASTER)
#   90deg rotate : v * e_12               ~1.1 us/call   (exact, raw)
#                  plane_rotation(pi/2)   ~44 us/call    (~41x -- symbolic rotor
#                                                         in the loop; exact but
#                                                         wants lambdify too)

from __future__ import annotations

import struct
import time

import numpy as np
import sympy

import gacalc.g2 as g2
import gacalc.g3 as g3
from gacalc.g2 import Vector as V2
from gacalc.g3 import Vector as V3
from gacalc.transforms import (
    plane_rotation,
    scale_non_uniform,
    to_matrix,
    translate,
)

N = 20000


def _bits(x: object) -> bytes:
    """Raw IEEE-754 bytes, so we can test bit-for-bit (not just ==)."""
    return struct.pack("<d", float(x))


def _identity() -> np.ndarray:
    return np.identity(4, dtype=np.float32)


def _hand_model(tx: float, ty: float, w: float, h: float) -> np.ndarray:
    """The renderer's current hand-built model matrix: translate @ scale."""
    t = _identity()
    t[0, 3] = tx
    t[1, 3] = ty
    s = _identity()
    s[0, 0] = w
    s[1, 1] = h
    return t @ s


def _bench(label: str, fn) -> float:
    start = time.perf_counter()
    for i in range(N):
        fn(i)
    us = (time.perf_counter() - start) / N * 1e6
    print(f"  {label:<34} {us:8.2f} us/call")
    return us


def model_matrix_study() -> None:
    print("== renderer model matrix (translate + scale, per sprite per frame) ==")

    # (a) gacalc to_matrix called PER draw (probes gacalc Vectors each time).
    def gac_per_call(tx, ty, w, h):
        f = translate(b=V3(tx, ty, 0.0)) @ scale_non_uniform(w, h, 1.0)
        return to_matrix(f, g3.G, backend="numpy")

    # (b) THE TECHNIQUE: derive the matrix symbolically ONCE, lambdify it.
    tx, ty, w, h = sympy.symbols("tx ty w h", real=True)
    f_sym = translate(b=V3(tx, ty, sympy.Integer(0))) @ scale_non_uniform(
        w, h, sympy.Integer(1)
    )
    m_sym = to_matrix(f_sym, g3.G, backend="sympy")
    print("  symbolic matrix from gacalc:\n", np.array(m_sym.tolist()))
    fast = sympy.lambdify((tx, ty, w, h), m_sym, "numpy")

    hand = _hand_model(3.0, 4.0, 10.0, 20.0)
    print(
        "  to_matrix/call == hand:",
        np.allclose(np.asarray(gac_per_call(3.0, 4.0, 10.0, 20.0)), hand),
    )
    print(
        "  lambdify       == hand:",
        np.allclose(np.asarray(fast(3.0, 4.0, 10.0, 20.0)), hand),
    )
    th = _bench("hand-built numpy", lambda i: _hand_model(i % 100, i % 50, 10.0, 20.0))
    tc = _bench("gacalc to_matrix per call", lambda i: gac_per_call(i % 100, i % 50, 10.0, 20.0))
    tl = _bench("symbolic once + lambdify", lambda i: np.asarray(fast(i % 100, i % 50, 10.0, 20.0)))
    print(f"  ratios vs hand: to_matrix/call={tc / th:.0f}x   lambdify={tl / th:.2f}x")


def quarter_turn_study() -> None:
    print("\n== a 90-degree rotation in the e1-e2 plane ==")
    # Named, built once with a SYMBOLIC angle -> exact (cos(pi/2)=0, sin=1).
    quarter_turn = plane_rotation(V2.e_1, V2.e_2)(sympy.pi / 2)
    ok_val = True
    ok_bits = True
    for x, y in [(3, -16), (5, 7), (0, 0), (1, 0), (-9, 13)]:
        v = V2(float(x), float(y))
        r = quarter_turn(v)
        e = v * g2.e_12
        ok_val = ok_val and (float(r.x) == float(e.x) and float(r.y) == float(e.y))
        ok_bits = ok_bits and (_bits(r.x) == _bits(e.x) and _bits(r.y) == _bits(e.y))
    print(f"  quarter_turn == *e_12  (value)   : {ok_val}")
    print(f"  quarter_turn == *e_12  (bit-exact): {ok_bits}  (differs only in sign-of-zero)")
    te = _bench("v * e_12 (raw pseudoscalar)", lambda i: V2(float(i % 100), float(-(i % 50))) * g2.e_12)
    tq = _bench("plane_rotation(pi/2) symbolic rotor", lambda i: quarter_turn(V2(float(i % 100), float(-(i % 50)))))
    print(f"  ratio: symbolic-rotor / *e_12 = {tq / te:.0f}x  (lambdify would remove this)")


if __name__ == "__main__":
    model_matrix_study()
    quarter_turn_study()
