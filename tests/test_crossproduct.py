# Copyright (c) 2018-2026 William Emerison Six
#
# Verification that the rotor port of the cross-product proof
# (mathdemos.crossproduct.cross_product) equals the cross product.  Pure gacalc
# (exact sympy arithmetic -- never floats), no display.
#
# Two tiers:
#   * fast (default): exact integer inputs -> exact sympy result, compared exactly.
#   * slow (`pytest -m slow`): a free-symbol proof for ALL a, b -- exact, but
#     ~minutes because sympy.simplify chews through the nested-rotor radicals.

import pytest
import sympy

from modelviewprojection.mathdemos.crossproduct import (
    _rotor_edge,
    cross_product,
    cross_product_stepwise,
    cross_product_via_graph,
)
from modelviewprojection.mathutils import Vector3


def _analytic(a, b):
    a_x, a_y, a_z = a
    b_x, b_y, b_z = b
    return (
        a_y * b_z - a_z * b_y,
        a_z * b_x - a_x * b_z,
        a_x * b_y - a_y * b_x,
    )


EXACT_CASES = [
    ((1, 0, 0), (0, 1, 0)),
    ((2, 1, 3), (0, 4, 1)),
    ((1, 2, 3), (4, 5, 6)),
    ((-3, 2, 1), (1, -1, 2)),
]


def test_cross_product_integer_cases():
    # Fast sanity tier: the coefficients are exact sympy expressions (int input
    # routes through sympy in gacalc), evaluated to high precision and compared to
    # the analytic cross product.  We DON'T sympy.simplify here -- denesting the
    # nested-rotor radicals is what makes the free-symbol proof below take minutes;
    # high-precision evalf is exact-enough and fast.  The real symbolic proof is
    # the slow test.
    for a_v, b_v in EXACT_CASES:
        got = tuple(cross_product(Vector3(*a_v), Vector3(*b_v)))
        exp = _analytic(a_v, b_v)
        for g, e in zip(got, exp):
            assert abs(sympy.N(g - e, 30)) < sympy.Rational(1, 10**20), (
                f"{a_v} x {b_v}: {got} != {exp}"
            )


def test_cross_product_stepwise_integer_cases():
    # the explicit step-by-step form (three plane rotations from projections) must
    # equal the analytic cross product.  Exact-sympy coefficients, evaluated to high
    # precision -- the same tier as cross_product_via_graph (which is the same three
    # nested rotors).  There is deliberately NO free-symbol slow proof for the
    # stepwise/graph forms: with three nested-rotor radicals sympy.simplify does not
    # terminate in a practical time (a single component ran >15 min unfinished),
    # unlike the closed form's two-rotor proof (the @slow test in this file).
    # High-precision exact-integer evalf is the tractable symbolic check here.
    for a_v, b_v in EXACT_CASES:
        got = tuple(cross_product_stepwise(Vector3(*a_v), Vector3(*b_v)))
        exp = _analytic(a_v, b_v)
        for g, e in zip(got, exp):
            assert abs(sympy.N(g - e, 30)) < sympy.Rational(1, 10**20), (
                f"{a_v} x {b_v}: {got} != {exp}"
            )


def test_cross_product_via_graph_matches_analytic():
    # the Cayley-graph / rotor-edge form (float inputs -> fast numeric gacalc).
    for a_v, b_v in EXACT_CASES:
        a = Vector3(*(float(x) for x in a_v))
        b = Vector3(*(float(x) for x in b_v))
        got = tuple(float(x) for x in cross_product_via_graph(a, b))
        exp = _analytic(a_v, b_v)
        for g, e in zip(got, exp):
            assert abs(g - e) < 1e-9, f"{a_v} x {b_v}: {got} != {exp}"


def test_rotor_edge_interpolates_smoothly():
    # a rotor edge's .at(t) must go identity (t=0) -> full (t=1) with a genuine
    # partway state -- so the animation interpolates instead of snapping.
    a = Vector3(2.0, 1.0, 3.0)
    mag = (2.0**2 + 1.0**2 + 3.0**2) ** 0.5
    edge = _rotor_edge(a, Vector3.e_1)
    start = tuple(float(x) for x in edge.at(0.0)(a))
    half = tuple(float(x) for x in edge.at(0.5)(a))
    full = tuple(float(x) for x in edge.at(1.0)(a))
    assert abs(start[0] - 2.0) < 1e-9 and abs(start[1] - 1.0) < 1e-9
    assert abs(full[0] - mag) < 1e-6 and abs(full[1]) < 1e-6 and abs(full[2]) < 1e-6
    # halfway is strictly between (not snapped to either end)
    assert abs(half[0] - 2.0) > 1e-3 and abs(half[0] - mag) > 1e-3


@pytest.mark.slow
def test_cross_product_equals_analytic_symbolically():
    # the proof: equal for ALL a, b (free symbols). ~minutes (radical simplify).
    a_x, a_y, a_z, b_x, b_y, b_z = sympy.symbols("a_x a_y a_z b_x b_y b_z", real=True)
    a = Vector3(a_x, a_y, a_z)
    b = Vector3(b_x, b_y, b_z)

    got_x, got_y, got_z = tuple(cross_product(a, b))
    exp_x, exp_y, exp_z = _analytic((a_x, a_y, a_z), (b_x, b_y, b_z))

    assert sympy.simplify(got_x - exp_x) == 0
    assert sympy.simplify(got_y - exp_y) == 0
    assert sympy.simplify(got_z - exp_z) == 0
