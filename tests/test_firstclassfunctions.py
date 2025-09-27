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
import typing


# doc-region-begin test first class functions
def test_first_class_functions():
    def doubler(x: int) -> int:
        return x * 2

    def add_five_to_result_of(f: typing.Callable[[int], int], x: int) -> int:
        return 5 + f(x)

    assert 11 == add_five_to_result_of(doubler, 3)
    assert 13 == add_five_to_result_of(doubler, 4)
    # doc-region-end test first class functions

# doc-region-begin test factorial no recursion
def test_factorial_no_recursion():
    def factorial(n: int, f: typing.Callable[[int], int]) -> int:
        if n == 1:
            return 1
        else:
            return n * f(n-1, f)

    assert 1 == factorial(1, factorial)
    assert 2 == factorial(2, factorial)
    assert 6 == factorial(3, factorial)
    assert 24 == factorial(4, factorial)
    # doc-region-end test factorial no recursion
