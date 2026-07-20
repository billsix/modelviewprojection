# Copyright (c) 2018-2026 William Emerison Six
#
# Regression tests for the gacalc-vector -> immediate-mode-OpenGL unpacking
# contract.  The demos pass vectors straight to GL by unpacking, e.g.
# ``GL.glVertex3f(*paddle1_vector_ndc)`` (demos 05-18), instead of spelling out
# ``v.coeff_e_1, v.coeff_e_2, v.coeff_e_3``.  That relies on gacalc's
# Vector2/Vector3 iterating their coordinates in (e_1, e_2[, e_3]) order with
# exactly the right arity.  If a gacalc upgrade ever changes that order/arity,
# these fail loudly here instead of the demos silently drawing garbage.  Pure
# data -- no display / no real GL needed.

from gacalc.g2 import Vector2
from gacalc.g3 import Vector3


def test_vector2_iterates_as_x_then_y():
    v = Vector2(3.0, 4.0)
    assert tuple(v) == (3.0, 4.0)
    assert list(v) == [3.0, 4.0]
    # glVertex2f wants exactly (x, y)
    assert len(tuple(v)) == 2


def test_vector3_iterates_as_x_then_y_then_z():
    v = Vector3(1.0, 2.0, 5.0)
    assert tuple(v) == (1.0, 2.0, 5.0)
    assert list(v) == [1.0, 2.0, 5.0]
    # glVertex3f wants exactly (x, y, z)
    assert len(tuple(v)) == 3


def test_unpacking_matches_glvertex_positional_args():
    # Mirror the exact call shape the demos use -- ``GL.glVertex?f(*v)`` -- with
    # a stand-in that records its positional args, so the contract is tested the
    # way the demos actually rely on it (no real GL / display required).
    def record_positional_args(*args):
        return args

    assert record_positional_args(*Vector2(7.0, 8.0)) == (7.0, 8.0)
    assert record_positional_args(*Vector3(7.0, 8.0, 9.0)) == (7.0, 8.0, 9.0)
