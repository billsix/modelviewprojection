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


from mathutils3d import fn_stack


# doc-region-begin function stack examples definitions
def test_fn_stack():
    def identity(x):
        return x

    fn_stack.push(identity)
    assert 1 == fn_stack.modelspace_to_ndc_fn()(1)

    def add_one(x):
        return x + 1

    fn_stack.push(add_one)
    assert 2 == fn_stack.modelspace_to_ndc_fn()(1)  # x + 1 = 2

    def multiply_by_2(x):
        return x * 2

    fn_stack.push(multiply_by_2)  # (x * 2) + 1 = 3
    assert 3 == fn_stack.modelspace_to_ndc_fn()(1)

    def add_5(x):
        return x + 5

    fn_stack.push(add_5)  # ((x + 5) * 2) + 1 = 13
    assert 13 == fn_stack.modelspace_to_ndc_fn()(1)

    fn_stack.pop()
    assert 3 == fn_stack.modelspace_to_ndc_fn()(1)  # (x * 2) + 1 = 3

    fn_stack.pop()
    assert 2 == fn_stack.modelspace_to_ndc_fn()(1)  # x + 1 = 2

    fn_stack.pop()
    assert 1 == fn_stack.modelspace_to_ndc_fn()(1)  # x = 1
    # doc-region-end function stack examples definitions
