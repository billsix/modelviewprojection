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

from pytest import approx

from mathutils import InvertibleFunction, compose, inverse
from mathutils1d import Vector1D, translate, uniform_scale


def test___add__():
    result = Vector1D(x=1.0) + Vector1D(x=3.0)
    assert result == Vector1D(x=approx(4.0))


def test___sub__():
    result = Vector1D(x=5.0) - Vector1D(x=1.0)
    assert result == Vector1D(x=approx(4.0))


def test___mul__():
    result = Vector1D(x=2.0) * 4.0
    assert result == Vector1D(x=approx(8.0))


def test___rmul__():
    result = 4.0 * Vector1D(x=2.0)
    assert result == Vector1D(x=approx(8.0))


def test___neg__():
    result = -Vector1D(x=2.0)
    assert result == Vector1D(x=approx(-2.0))


# doc-region-begin translate test
def test_translate():
    t: InvertibleFunction[Vector1D] = translate(Vector1D(x=2.0))
    assert t(Vector1D(x=0.0)) == Vector1D(x=approx(2.0))
    assert t(Vector1D(x=1.0)) == Vector1D(x=approx(3.0))
    assert t(Vector1D(x=0.0)) == Vector1D(x=approx(2.0))

    t_inv: InvertibleFunction[Vector1D] = inverse(t)
    assert t_inv(t(Vector1D(x=0.0))) == Vector1D(x=approx(0.0))
    assert t_inv(t(Vector1D(x=1.0))) == Vector1D(x=approx(1.0))


# doc-region-end translate test


def test_mx_plus_b():
    m = 5.0
    b = 2.0
    t: InvertibleFunction[Vector1D] = translate(Vector1D(b))
    scale: InvertibleFunction[Vector1D] = uniform_scale(m)

    fn: InvertibleFunction[Vector1D] = compose(t, scale)
    fn_inv: InvertibleFunction[Vector1D] = inverse(fn)

    assert fn(Vector1D(x=0.0)) == Vector1D(x=approx(2.0))
    assert fn_inv(Vector1D(x=2.0)) == Vector1D(x=approx(0.0))

    assert fn(Vector1D(x=1.0)) == Vector1D(x=approx(7.0))
    assert fn_inv(Vector1D(x=7.0)) == Vector1D(x=approx(1.0))

    assert fn(Vector1D(x=2.0)) == Vector1D(x=approx(12.0))
    assert fn_inv(Vector1D(x=12.0)) == Vector1D(x=approx(2.0))


def test_uniform_scale():
    s: InvertibleFunction[Vector1D] = uniform_scale(4.0)

    result = s(Vector1D(x=2.0))
    assert result == Vector1D(x=approx(8.0))
    assert inverse(s)(result) == Vector1D(x=approx(2.0))
