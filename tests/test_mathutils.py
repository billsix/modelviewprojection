# Copyright (c) 2018-2025 William Emerison Six
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


from __future__ import annotations  # to appease Python 3.7-3.9

import math
from typing import Callable

from pytest import approx

from mathutils import (
    Vertex2D,
    compose,
    inverse,
    rotate,
    rotate_90_degrees,
    scale,
    translate,
    uniform_scale,
)


def test___add__():
    result = Vertex2D(x=1.0, y=2.0) + Vertex2D(x=3.0, y=4.0)
    assert result == Vertex2D(x=approx(4.0), y=approx(6.0))


def test___sub__():
    result = Vertex2D(x=5.0, y=8.0) - Vertex2D(x=1.0, y=2.0)
    assert result == Vertex2D(x=approx(4.0), y=approx(6.0))


def test___mul__():
    result = Vertex2D(x=2.0, y=3.0) * 4.0
    assert result == Vertex2D(x=approx(8.0), y=approx(12.0))


def test___rmul__():
    result = 4.0 * Vertex2D(x=2.0, y=3.0)
    assert result == Vertex2D(x=approx(8.0), y=approx(12.0))


def test___neg__():
    result = -Vertex2D(x=2.0, y=3.0)
    assert result == Vertex2D(x=approx(-2.0), y=approx(-3.0))


def test_translate():
    t: Callable[Vertex2D, Vertex2D] = translate(Vertex2D(x=2.0, y=3.0))
    assert t(Vertex2D(x=0.0, y=0.0)) == Vertex2D(x=approx(2.0), y=approx(3.0))
    assert t(Vertex2D(x=1.0, y=0.0)) == Vertex2D(x=approx(3.0), y=approx(3.0))
    assert t(Vertex2D(x=0.0, y=1.0)) == Vertex2D(x=approx(2.0), y=approx(4.0))

    t_inv: Callable[Vertex2D, Vertex2D] = inverse(t)
    assert t_inv(t(Vertex2D(x=0.0, y=0.0))) == Vertex2D(
        x=approx(0.0), y=approx(0.0)
    )
    assert t_inv(t(Vertex2D(x=1.0, y=0.0))) == Vertex2D(
        x=approx(1.0), y=approx(0.0)
    )
    assert t_inv(t(Vertex2D(x=0.0, y=1.0))) == Vertex2D(
        x=approx(0.0), y=approx(1.0)
    )


def test_compose():
    t: Callable[Vertex2D, Vertex2D] = translate(Vertex2D(x=2.0, y=3.0))
    t_inv: Callable[Vertex2D, Vertex2D] = inverse(t)

    assert compose(t_inv, t)(Vertex2D(x=0.0, y=0.0)) == Vertex2D(
        x=approx(0.0), y=approx(0.0)
    )
    id: Callable[Vertex2D, Vertex2D] = compose(t_inv, t)
    assert id(Vertex2D(x=1.0, y=0.0)) == Vertex2D(x=approx(1.0), y=approx(0.0))
    assert id(Vertex2D(x=0.0, y=1.0)) == Vertex2D(x=approx(0.0), y=approx(1.0))


def test_uniform_scale():
    s: Callable[Vertex2D, Vertex2D] = uniform_scale(4.0)

    result = s(Vertex2D(x=2.0, y=3.0))
    assert result == Vertex2D(x=approx(8.0), y=approx(12.0))
    assert inverse(s)(result) == Vertex2D(x=approx(2.0), y=approx(3.0))


def test_scale():
    s: Callable[Vertex2D, Vertex2D] = scale(scale_x=2.0, scale_y=3.0)

    result = s(Vertex2D(x=5.0, y=6.0))
    assert result == Vertex2D(x=approx(10.0), y=approx(18.0))
    assert inverse(s)(result) == Vertex2D(x=approx(5.0), y=approx(6.0))


def test_rotate_90():
    r: Callable[Vertex2D, Vertex2D] = rotate_90_degrees()

    result = r(Vertex2D(x=5.0, y=6.0))
    assert result == Vertex2D(x=approx(-6.0), y=approx(5.0))
    assert inverse(r)(result) == Vertex2D(x=approx(5.0), y=approx(6.0))


def test_rotate():
    r: Callable[Vertex2D, Vertex2D] = rotate(math.radians(53.130102))

    result = r(Vertex2D(x=5.0, y=0.0))
    assert result == Vertex2D(approx(3.0), approx(4.0))
    assert inverse(r)(result) == Vertex2D(x=approx(5.0), y=approx(0.0))
