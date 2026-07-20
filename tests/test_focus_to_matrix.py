# Copyright (c) 2018-2026 William Emerison Six
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Regression for the mvpViz focus crash (tasks/mvpviz-focus-failure.md).

gacalc's ``magnitude()`` goes through ``sympy.sqrt``, so rotor-based rotations
(``rotate_z``) hand back sympy-typed coefficients even for purely numeric input.
``cayleyscene.to_matrix`` must coerce to ``float64`` -- otherwise ``np.array``
infers ``dtype=object`` and ``np.linalg.inv`` (the perspective/ortho focus path)
fails with a dtype cast error.
"""

import numpy as np
from gacalc.g3 import Vector3
from gacalc.transforms import translate

from modelviewprojection.cayley import cayleygraph, cayleyscene
from modelviewprojection.mathutils import rotate_z


def _v(x: float, y: float, z: float) -> Vector3:
    return Vector3(coeff_e_1=x, coeff_e_2=y, coeff_e_3=z)


def _focus_matrix() -> np.ndarray:
    # mirror a focus path: an edge with a translate + a rotor-based rotation,
    # walked against the arrow (world -> paddle1), then realized as a matrix.
    edge: cayleygraph.Edge[str] = cayleygraph.Edge(
        src="paddle1",
        dst="world",
        steps=[("T", translate(_v(0.5, 0.3, 0.0))), ("R_z", rotate_z(0.7))],
    )
    graph: cayleygraph.CayleyGraph = cayleygraph.CayleyGraph([edge])
    return cayleyscene.to_matrix(graph.path("world", "paddle1").function())


def test_to_matrix_is_float64_through_a_rotation() -> None:
    assert _focus_matrix().dtype == np.float64


def test_focus_matrix_is_invertible() -> None:
    # the perspective / ortho focus path inverts this matrix (np.linalg.inv);
    # an object-dtype matrix would raise a UFuncTypeError here.
    np.linalg.inv(_focus_matrix())
