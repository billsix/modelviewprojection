# Copyright (c) 2017-2026 William Emerison Six
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import contextlib
import enum
import math
import typing

import numpy as np


class MatrixStack(enum.Enum):
    model = 1
    view = 2
    projection = 3
    modelview = 4
    modelviewprojection = 5


__modelStack__: list[np.ndarray] = [
    np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )
]

__viewStack__: list[np.ndarray] = [
    np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )
]

__projectionStack__: list[np.ndarray] = [
    np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )
]


def get_current_matrix(matrix_stack: MatrixStack) -> np.ndarray:
    # A chain of `if`s with no `else` fell off the end and returned None for
    # any unhandled member -- while the signature promises an ndarray, and
    # every caller indexes the result immediately. The `case _` makes that
    # unreachable branch loud instead of silent.
    match matrix_stack:
        case MatrixStack.model:
            return __modelStack__[-1]
        case MatrixStack.view:
            return __viewStack__[-1]
        case MatrixStack.projection:
            return __projectionStack__[-1]
        case MatrixStack.modelview:
            return np.matmul(
                __viewStack__[-1],
                __modelStack__[-1],
            )
        case MatrixStack.modelviewprojection:
            return np.matmul(
                __projectionStack__[-1],
                np.matmul(
                    __viewStack__[-1],
                    __modelStack__[-1],
                ),
            )
        case _:
            raise ValueError(
                f"get_current_matrix: unhandled MatrixStack member "
                f"{matrix_stack!r}"
            )


def _not_a_stack(operation: str, matrix_stack: MatrixStack) -> ValueError:
    # `modelview` and `modelviewprojection` are products COMPUTED on demand by
    # get_current_matrix, not stored stacks -- so storing into them, pushing
    # them, and popping them are all meaningless. These used to be silent
    # `pass` branches (with a TODO), which meant a caller writing to a derived
    # stack got no effect and no error.
    return ValueError(
        f"{operation}: {matrix_stack.name} is a product derived from the "
        f"model / view / projection stacks, not a stack of its own. "
        f"Operate on those stacks individually."
    )


def set_current_matrix(matrix_stack: MatrixStack, m: np.ndarray) -> None:
    match matrix_stack:
        case MatrixStack.model:
            __modelStack__[-1] = m
        case MatrixStack.view:
            __viewStack__[-1] = m
        case MatrixStack.projection:
            __projectionStack__[-1] = m
        case MatrixStack.modelview | MatrixStack.modelviewprojection:
            raise _not_a_stack("set_current_matrix", matrix_stack)
        case _:
            raise ValueError(
                f"set_current_matrix: unhandled MatrixStack member "
                f"{matrix_stack!r}"
            )


def _push_matrix(matrix_stack: MatrixStack) -> None:
    def top_copy() -> np.ndarray:
        return np.copy(get_current_matrix(matrix_stack))

    match matrix_stack:
        case MatrixStack.model:
            __modelStack__.append(top_copy())
        case MatrixStack.view:
            __viewStack__.append(top_copy())
        case MatrixStack.projection:
            __projectionStack__.append(top_copy())
        case MatrixStack.modelview | MatrixStack.modelviewprojection:
            raise _not_a_stack("push_matrix", matrix_stack)
        case _:
            raise ValueError(
                f"push_matrix: unhandled MatrixStack member {matrix_stack!r}"
            )


def _pop_matrix(matrix_stack: MatrixStack) -> None:
    match matrix_stack:
        case MatrixStack.model:
            __modelStack__.pop()
        case MatrixStack.view:
            __viewStack__.pop()
        case MatrixStack.projection:
            __projectionStack__.pop()
        case MatrixStack.modelview | MatrixStack.modelviewprojection:
            raise _not_a_stack("pop_matrix", matrix_stack)
        case _:
            raise ValueError(
                f"pop_matrix: unhandled MatrixStack member {matrix_stack!r}"
            )


@contextlib.contextmanager
def push_matrix(m: MatrixStack) -> typing.Iterator[MatrixStack]:
    """Instead of manually pushing and poping the matrix stack,
    this allows using the "with" keyword."""
    matrix_stack = m
    try:
        _push_matrix(matrix_stack)
        yield matrix_stack
    finally:
        _pop_matrix(matrix_stack)


def set_to_identity_matrix(m: MatrixStack) -> None:
    set_current_matrix(
        m,
        np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=np.float32,
        ),
    )


def rotate_x(matrix_stack: MatrixStack, rads: float) -> None:
    """Using a normal linear algebra notation, which
    is row-major, 1-based indexes, the following
    matrix multiplication shows how to add a rotation
    to a matrix, along the position X axis.

    M(1,1) M(1,2) M(1,3) M(1,4)     1   0    0    0
    M(2,1) M(2,2) M(2,3) M(2,4) *   0   cos  -sin 0
    M(3,1) M(3,2) M(3,3) M(3,4)     0   sin  cos  0
    M(4,1) M(4,2) M(4,3) M(4,4)     0   0    0    1

      =

    Rather than keeping both matricies, we can reduce
    them to one by matrix multiplication

    M(1,1)  M(1,2)*cos+M(1,3)*sin  M(1,2)*-sin+M(1,3)*cos  M(1,4)
    M(2,1)  M(2,2)*cos+M(2,3)*sin  M(2,2)*-sin+M(2,3)*cos  M(2,4)
    M(3,1)  M(3,2)*cos+M(3,3)*sin  M(3,2)*-sin+M(3,3)*cos  M(3,4)
    M(4,1)  M(4,2)*cos+M(4,3)*sin  M(4,2)*-sin+M(4,3)*cos  M(4,4)
    """

    m = get_current_matrix(matrix_stack)
    copy_of_m = np.copy(m)

    c = math.cos(rads)
    s = math.sin(rads)

    m[0, 1] = copy_of_m[0, 1] * c + copy_of_m[0, 2] * s
    m[1, 1] = copy_of_m[1, 1] * c + copy_of_m[1, 2] * s
    m[2, 1] = copy_of_m[2, 1] * c + copy_of_m[2, 2] * s
    m[3, 1] = copy_of_m[3, 1] * c + copy_of_m[3, 2] * s

    m[0, 2] = copy_of_m[0, 1] * -s + copy_of_m[0, 2] * c
    m[1, 2] = copy_of_m[1, 1] * -s + copy_of_m[1, 2] * c
    m[2, 2] = copy_of_m[2, 1] * -s + copy_of_m[2, 2] * c
    m[3, 2] = copy_of_m[3, 1] * -s + copy_of_m[3, 2] * c


def rotate_y(matrix_stack: MatrixStack, rads: float) -> None:
    """Using a normal linear algebra notation, which
    is row-major, 1-based indexes, the following
    matrix multiplication shows how to add a rotation
    to a matrix, along the position Y axis.

    M(1,1) M(1,2) M(1,3) M(1,4)     cos  0    sin  0
    M(2,1) M(2,2) M(2,3) M(2,4) *   0    1    0    0
    M(3,1) M(3,2) M(3,3) M(3,4)     -sin 0    cos  0
    M(4,1) M(4,2) M(4,3) M(4,4)     0    0    0    1

    =

    Rather than keeping both matricies, we can reduce
    them to one by matrix multiplication

    M(1,1)*cos+M(1,3)*-sin    M(1,2)     M(1,1)*sin+M(1,3)*cos     M(1,4)
    M(2,1)*cos+M(2,3)*-sin    M(2,2)     M(2,1)*sin+M(2,3)*cos     M(2,4)
    M(3,1)*cos+M(3,3)*-sin    M(3,2)     M(3,1)*sin+M(3,3)*cos     M(3,4)
    M(4,1)*cos+M(4,3)*-sin    M(4,2)     M(4,1)*sin+M(4,3)*cos     M(4,4)
    """
    m = get_current_matrix(matrix_stack)
    copy_of_m = np.copy(m)

    c = math.cos(rads)
    s = math.sin(rads)

    m[0, 0] = copy_of_m[0, 0] * c + copy_of_m[0, 2] * -s
    m[1, 0] = copy_of_m[1, 0] * c + copy_of_m[1, 2] * -s
    m[2, 0] = copy_of_m[2, 0] * c + copy_of_m[2, 2] * -s
    m[3, 0] = copy_of_m[3, 0] * c + copy_of_m[3, 2] * -s

    m[0, 2] = copy_of_m[0, 0] * s + copy_of_m[0, 2] * c
    m[1, 2] = copy_of_m[1, 0] * s + copy_of_m[1, 2] * c
    m[2, 2] = copy_of_m[2, 0] * s + copy_of_m[2, 2] * c
    m[3, 2] = copy_of_m[3, 0] * s + copy_of_m[3, 2] * c


def rotate_z(matrix_stack: MatrixStack, rads: float) -> None:
    """Using a normal linear algebra notation, which
    is row-major, 1-based indexes, the following
    matrix multiplication shows how to add a rotation
    to a matrix, along the position Z axis.

    M(1,1) M(1,2) M(1,3) M(1,4)     cos -sin 0    0
    M(2,1) M(2,2) M(2,3) M(2,4) *   sin cos  0    0
    M(3,1) M(3,2) M(3,3) M(3,4)     0   0    1    0
    M(4,1) M(4,2) M(4,3) M(4,4)     0   0    0    1

      =

    Rather than keeping both matricies, we can reduce
    them to one by matrix multiplication

    M(1,1)*cos+M(1,2)*sin    M(1,1)*-sin+M(1,2)*cos M(1,3) M(1,4)
    M(2,1)*cos+M(2,2)*sin    M(2,1)*-sin+M(2,2)*cos M(2,3) M(2,4)
    M(3,1)*cos+M(3,2)*sin    M(3,1)*-sin+M(3,2)*cos M(3,3) M(3,4)
    M(4,1)*cos+M(4,2)*sin    M(4,1)*-sin+M(4,2)*cos M(4,3) M(4,4)
    """
    m = get_current_matrix(matrix_stack)
    copy_of_m = np.copy(m)

    c = math.cos(rads)
    s = math.sin(rads)

    m[0, 0] = copy_of_m[0, 0] * c + copy_of_m[0, 1] * s
    m[1, 0] = copy_of_m[1, 0] * c + copy_of_m[1, 1] * s
    m[2, 0] = copy_of_m[2, 0] * c + copy_of_m[2, 1] * s
    m[3, 0] = copy_of_m[3, 0] * c + copy_of_m[3, 1] * s

    m[0, 1] = copy_of_m[0, 0] * -s + copy_of_m[0, 1] * c
    m[1, 1] = copy_of_m[1, 0] * -s + copy_of_m[1, 1] * c
    m[2, 1] = copy_of_m[2, 0] * -s + copy_of_m[2, 1] * c
    m[3, 1] = copy_of_m[3, 0] * -s + copy_of_m[3, 1] * c


def translate(matrix_stack: MatrixStack, x: float, y: float, z: float) -> None:
    """Using a normal linear algebra notation, which
    is row-major, 1-based indexes, the following
    matrix multiplication shows how to add a translation
    to a matrix.

    M(1,1) M(1,2) M(1,3) M(1,4)     1 0 0 x
    M(2,1) M(2,2) M(2,3) M(2,4) *   0 1 0 y
    M(3,1) M(3,2) M(3,3) M(3,4)     0 0 1 z
    M(4,1) M(4,2) M(4,3) M(4,4)     0 0 0 1

      =

    Rather than keeping both matricies, we can reduce
    them to one by matrix multiplication

    M(1,1) M(1,2) M(1,3) (M(1,1)*x + M(1,2)*y + M(1,3)*z + M(1,4)*w)
    M(2,1) M(2,2) M(2,3) (M(2,1)*x + M(2,2)*y + M(2,3)*z + M(2,4)*w)
    M(3,1) M(3,2) M(3,3) (M(3,1)*x + M(3,2)*y + M(3,3)*z + M(3,4)*w)
    M(4,1) M(4,2) M(4,3) (M(4,1)*x + M(4,2)*y + M(4,3)*z + M(4,4)*w)
    """
    m = get_current_matrix(matrix_stack)

    m[0, 3] = m[0, 0] * x + m[0, 1] * y + m[0, 2] * z + m[0, 3]
    m[1, 3] = m[1, 0] * x + m[1, 1] * y + m[1, 2] * z + m[1, 3]
    m[2, 3] = m[2, 0] * x + m[2, 1] * y + m[2, 2] * z + m[2, 3]
    m[3, 3] = m[3, 0] * x + m[3, 1] * y + m[3, 2] * z + m[3, 3]


def scale(matrix_stack: MatrixStack, x: float, y: float, z: float) -> None:
    """Using a normal linear algebra notation, which
    is row-major, 1-based indexes, the following
    matrix multiplication shows how to add a translation
    to a matrix.

    M(1,1) M(1,2) M(1,3) M(1,4)     x 0 0 0
    M(2,1) M(2,2) M(2,3) M(2,4) *   0 y 0 0
    M(3,1) M(3,2) M(3,3) M(3,4)     0 0 z 0
    M(4,1) M(4,2) M(4,3) M(4,4)     0 0 0 1

      =

    Rather than keeping both matricies, we can reduce
    them to one by matrix multiplication

    M(1,1)*x  M(1,2)*y  M(1,3)*z  M(1,4)
    M(2,1)*x  M(2,2)*y  M(2,3)*z  M(2,4)
    M(3,1)*x  M(3,2)*y  M(3,3)*z  M(3,4)
    M(4,1)*x  M(4,2)*y  M(4,3)*z  M(4,4)
    """
    m = get_current_matrix(matrix_stack)

    m[0, 0] = m[0, 0] * x
    m[1, 0] = m[1, 0] * x
    m[2, 0] = m[2, 0] * x
    m[3, 0] = m[3, 0] * x

    m[0, 1] = m[0, 1] * y
    m[1, 1] = m[1, 1] * y
    m[2, 1] = m[2, 1] * y
    m[3, 1] = m[3, 1] * y

    m[0, 2] = m[0, 2] * z
    m[1, 2] = m[1, 2] * z
    m[2, 2] = m[2, 2] * z
    m[3, 2] = m[3, 2] * z


def multiply(matrix_stack: MatrixStack, rhs: np.ndarray) -> None:
    """Matrix multiply"""
    m = get_current_matrix(matrix_stack)
    m[0:4, 0:4] = np.matmul(m.copy(), rhs)


def ortho(
    left: float,
    right: float,
    bottom: float,
    top: float,
    near: float,
    far: float,
) -> None:
    """ortho projection, like a blueprint diagram for a house.
    depth down the z axis does not affect x and y position
    in screen space.

    http://www.songho.ca/opengl/gl_projectionmatrix.html
    """
    dx = right - left
    dy = top - bottom
    dz = far - near

    rx = -(right + left) / (right - left)
    ry = -(top + bottom) / (top - bottom)
    rz = -(far + near) / (far - near)

    # fmt: off
    __projectionStack__[-1] = np.array(
        [
            [2.0 / dx, 0.0,      0.0,       rx],
            [0.0,      2.0 / dy, 0.0,       ry],
            [0.0,      0.0,      -2.0 / dz, rz],
            [0.0,      0.0,      0.0,       1.0],
        ],
        dtype=np.float32,
    )
    # fmt: on


def perspective(
    field_of_view: float, aspect_ratio: float, near_z: float, far_z: float
) -> None:
    """perspective projection, where things further away look smaller
    by shrinking their x and y coordinates.

    Camera is at 0,0,0, facing down the negative z axis.

    near_z and far_z are expressed in positive numbers, which is odd,
    because the camera space coordinates will be from -near_z to -far_z
    on the z axis.

    http://www.songho.ca/opengl/gl_projectionmatrix.html
    """
    top = near_z * math.tan(math.radians(field_of_view) / 2.0)
    right = top * aspect_ratio

    # m34 is a constant, inlining it would make the line > 80 chars
    m34 = -2 * (far_z * near_z) / (far_z - near_z)
    # fmt: off
    # The rows are hand-aligned into matrix columns and run a few chars past 80.
    # In a book about matrices that layout IS the documentation, so these keep
    # their alignment (hence the `fmt: off` above) and opt out of E501 rather
    # than being reflowed into an unreadable stack.
    __projectionStack__[-1] = np.array(
        [
            [near_z / right, 0.0,          0.0,                                  0.0],  # noqa: E501
            [0.0,            near_z / top, 0.0,                                  0.0],  # noqa: E501
            [0.0,            0.0,          -(far_z + near_z) / (far_z - near_z), m34],  # noqa: E501
            [0.0,            0.0,          -1.0,                                 0.0],  # noqa: E501
        ],
        dtype=np.float32,
    )
    # fmt: on
