#!/usr/bin/env python3
# Copyright (c) 2026 William Emerison Six
#
# Micro-benchmarks for tasks/pointlike-type-study.md: the per-operation cost of
# the three ways a Code-the-Classics game could carry a 2-D point -- a gacalc
# g2 Vector (the games' arithmetic type), a plain (x, y) tuple, and the
# engine's current `PointLike = tuple | Vector` boundary (unpack whatever came
# in). Prints a table of microseconds per operation (best of 5 repeats of
# `timeit`, N calls each). Run in the project container:
#   python tasks/adhoc/pointlike-type-study/bench_point_types.py

import math
import timeit

from gacalc.g2 import Vector

N = 200_000
setup = "from __main__ import Vector, math, v, w, t, u, unpack_point, set_pos_actor_style"
v, w = Vector(3.0, 4.0), Vector(1.5, -2.0)
t, u = (3.0, 4.0), (1.5, -2.0)


def unpack_point(p):  # noqa: ANN001 -- the engine's PointLike boundary
    px, py = p
    return float(px), float(py)


def set_pos_actor_style(p, w=32.0, h=48.0):  # noqa: ANN001 -- Actor._set_pos: anchor -> rect
    px, py = p
    return float(px) - w * 0.5, float(py) - h * 0.5


CASES = [
    ("construct", "Vector(3.0, 4.0)", "(3.0, 4.0)"),
    ("copy from the other kind", "Vector(*t)", "(v.x, v.y)"),
    ("unpack  a, b = p", "a, b = v", "a, b = t"),
    ("add", "v + w", "(t[0] + u[0], t[1] + u[1])"),
    ("subtract", "v - w", "(t[0] - u[0], t[1] - u[1])"),
    ("scale by float", "v * 2.5", "(t[0] * 2.5, t[1] * 2.5)"),
    ("equality", "v == w", "t == u"),
    ("x coordinate as float", "float(v.x)", "float(t[0])"),
    ("magnitude", "v.magnitude()", "math.hypot(t[0], t[1])"),
    ("PointLike boundary unpack", "unpack_point(v)", "unpack_point(t)"),
    ("Actor.pos = p (anchor->rect)", "set_pos_actor_style(v)", "set_pos_actor_style(t)"),
]


def best(stmt: str) -> float:
    return min(timeit.repeat(stmt, setup=setup, number=N, repeat=5)) / N * 1e6


print(f"{'operation':32} {'Vector µs':>10} {'tuple µs':>10} {'ratio':>7}")
for name, sv, st in CASES:
    a, b = best(sv), best(st)
    print(f"{name:32} {a:10.3f} {b:10.3f} {a / b:7.1f}x")
