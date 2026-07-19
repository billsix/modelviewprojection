# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.


import contextlib
import contextvars
import math
from collections.abc import Generator, Iterator, Sequence

import matplotlib
import matplotlib.axes
import matplotlib.figure
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
from IPython import get_ipython
from IPython.display import display
from matplotlib.patches import Polygon
from matplotlib_inline.backend_inline import set_matplotlib_formats

from modelviewprojection.mathutils import (
    InvertibleFunction,
    Vector2,
    cosine,
    identity,
    sine,
)

# the inline SVG backend only makes sense inside an IPython/Jupyter session;
# guarding it lets this module import headless instead of raising.
if get_ipython() is not None:
    set_matplotlib_formats("svg")

extra_lines_multiplier = 3

zero = Vector2.zero()


def _xy(vertices: Sequence[Vector2]) -> np.ndarray:
    """(N, 2) float array of the vertices' 2D coordinates, for matplotlib.

    gacalc vectors iterate their coefficient values, so ``list(v) == [x, y]``;
    those values are sympy ``Float``s (rotations go through ``sympy.sqrt``), so
    cast to ``float`` -- otherwise numpy builds an object array matplotlib can't
    render.
    """
    return np.array([list(v) for v in vertices], dtype=float)


def generategridlines(
    graph_bounds: tuple[int, int], interval: int = 1
) -> Iterator[tuple[list[Vector2], int]]:
    for x in range(
        -graph_bounds[0] * extra_lines_multiplier,
        graph_bounds[0] * extra_lines_multiplier,
        interval,
    ):
        thickness = 4 if np.isclose(x, 0.0) else 1
        yield (
            [
                x * Vector2.e_1
                + (-graph_bounds[1] * extra_lines_multiplier) * Vector2.e_2,
                x * Vector2.e_1
                + (graph_bounds[1] * extra_lines_multiplier) * Vector2.e_2,
            ],
            thickness,
        )

    for y in range(
        -graph_bounds[1] * extra_lines_multiplier,
        graph_bounds[1] * extra_lines_multiplier,
        interval,
    ):
        thickness = 4 if np.isclose(y, 0.0) else 1
        yield (
            [
                (-graph_bounds[0] * extra_lines_multiplier) * Vector2.e_1
                + y * Vector2.e_2,
                (graph_bounds[0] * extra_lines_multiplier) * Vector2.e_1
                + y * Vector2.e_2,
            ],
            thickness,
        )


#: The axes established by the enclosing ``create_graphs()`` block.
#:
#: A :class:`contextvars.ContextVar` rather than a plain module global for two
#: reasons.  ``set()`` returns a token and ``reset(token)`` restores the
#: *previous* value, so nested ``create_graphs()`` blocks no longer clobber each
#: other (a bare global left the outer block with ``None``).  And an unset
#: ContextVar raises at the point of use, which is how ``_current_axes()`` can
#: report the real mistake instead of an ``AttributeError`` further downstream.
_axes: contextvars.ContextVar[matplotlib.axes.Axes] = contextvars.ContextVar(
    "axes"
)


def _current_axes() -> matplotlib.axes.Axes:
    """The axes of the enclosing ``create_graphs()`` block.

    Raises :class:`RuntimeError` naming the actual mistake if there is no such
    block -- this replaced scattered ``assert axes is not None`` checks.
    """
    try:
        return _axes.get()
    except LookupError:
        raise RuntimeError(
            "no active figure -- call this inside a "
            "`with create_graphs():` block"
        ) from None


@contextlib.contextmanager
def create_graphs(
    graph_bounds: tuple[int, int] = (3, 3),
    title: str | None = None,
    filename: str | None = None,
) -> Generator[matplotlib.axes.Axes, None, matplotlib.figure.Figure]:
    fig: matplotlib.figure.Figure
    fig, axes = plt.subplots(figsize=graph_bounds)
    token = _axes.set(axes)
    axes.set_xlim((-graph_bounds[0], graph_bounds[0]))
    axes.set_ylim((-graph_bounds[1], graph_bounds[1]))

    plt.tight_layout()

    try:
        yield axes
    finally:
        _axes.reset(token)

    fig.patch.set_edgecolor("black")
    fig.patch.set_linewidth(2)

    # make sure the x and y axis are equally proportional in screen space
    plt.gca().set_aspect("equal", adjustable="box")
    axes.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(1))
    axes.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(1))
    fig.canvas.draw()
    display(fig)
    plt.close()

    return fig


# the shared no-op default for create_basis (B008: don't call in defaults;
# identity() is stateless, so one module-level instance serves every call)
_IDENTITY = identity()


def create_basis(
    fn: InvertibleFunction = _IDENTITY,
    graph_bounds: tuple[int, int] = (10, 10),
    gridline_interval: int = 1,
    xcolor: tuple[float, float, float] = (0.0, 0.0, 1.0),
    ycolor: tuple[float, float, float] = (1.0, 0.0, 1.0),
) -> None:
    # plot transformed basis
    for vecs, thickness in generategridlines(
        graph_bounds, interval=gridline_interval
    ):
        plt.plot(
            [fn(vec).coeff_e_1 for vec in vecs],
            [fn(vec).coeff_e_2 for vec in vecs],
            "-",
            lw=thickness,
            color=(0.1, 0.2, 0.5),
            alpha=0.3,
        )


def create_unit_circle(
    fn: InvertibleFunction = _IDENTITY,
) -> None:
    def generate_circle() -> Iterator[list[Vector2]]:
        theta_increment: float = 0.01
        scale_radius: float = 1.0

        for theta in np.arange(0.0, 2 * math.pi, theta_increment):
            yield (
                [
                    scale_radius * math.cos(theta) * Vector2.e_1
                    + math.sin(theta) * Vector2.e_2,
                    scale_radius
                    * (
                        math.cos(theta + theta_increment) * Vector2.e_1
                        + math.sin(theta + theta_increment) * Vector2.e_2
                    ),
                ]
            )

    # plot transformed basis
    for vecs in generate_circle():
        plt.plot(
            [fn(vec).coeff_e_1 for vec in vecs],
            [fn(vec).coeff_e_2 for vec in vecs],
            "-",
            lw=1,
            color=(0.0, 0.0, 0.0),
            alpha=0.5,
        )


def create_x_and_y(
    fn: InvertibleFunction = _IDENTITY,
    xcolor: tuple[float, float, float] = (0.0, 0.0, 1.0),
    ycolor: tuple[float, float, float] = (1.0, 0.0, 1.0),
) -> None:
    # x axis
    x_axis = [zero, Vector2.e_1]
    plt.plot(
        [fn(vec).coeff_e_1 for vec in x_axis],
        [fn(vec).coeff_e_2 for vec in x_axis],
        "-",
        lw=1.0,
        color=xcolor,
    )

    # y axis
    y_axis = [zero, Vector2.e_2]
    plt.plot(
        [fn(vec).coeff_e_1 for vec in y_axis],
        [fn(vec).coeff_e_2 for vec in y_axis],
        "-",
        lw=1.0,
        color=ycolor,
    )


def _draw_labelled_triangle(
    vertices_in_model_space: Sequence[Vector2],
    labels: Sequence[str],
    fn: InvertibleFunction = _IDENTITY,
    color: tuple[float, float, float] = (0.0, 0.0, 1.0),
    label_offset_x_sign: float = 1.0,
) -> None:
    """Draw a filled, vertex-labelled triangle under the transform ``fn``.

    The three ``draw_*_triangle`` helpers below were 53-line near-duplicates
    (91-92% identical); only the two non-origin vertices, the label strings, and
    which way the labels are nudged in x ever differed.
    """
    axes = _current_axes()
    x_prime_direction_world_space = fn(Vector2.e_1) - fn(zero)
    x_world_space = Vector2.e_1
    y_prime_direction_world_space = fn(Vector2.e_2) - fn(zero)
    angle_radians = math.atan2(
        sine(x_world_space, x_prime_direction_world_space),
        cosine(x_world_space, x_prime_direction_world_space),
    )
    label_offset = (
        0 * x_prime_direction_world_space + 0.20 * y_prime_direction_world_space
    )

    vertices = [fn(v) for v in vertices_in_model_space]

    triangle = Polygon(
        _xy(vertices),
        closed=True,
        facecolor="lightblue",
        edgecolor="black",
    )
    axes.add_patch(triangle)

    vertices_as_np = np.array(_xy(vertices))
    # Plot dots at the vertices
    axes.scatter(
        vertices_as_np[:, 0], vertices_as_np[:, 1], color="red", s=5, zorder=5
    )  # zorder ensures dots are on top

    # Label each vertex
    for i, label in enumerate(labels):
        # Use plt.annotate to place the label near the point
        plt.annotate(
            label,
            xy=(vertices_as_np[i, 0], vertices_as_np[i, 1]),
            xytext=(
                vertices_as_np[i, 0]
                + label_offset_x_sign * label_offset.coeff_e_1,
                vertices_as_np[i, 1] + label_offset.coeff_e_2,
            ),
            rotation=math.degrees(angle_radians),
            rotation_mode="anchor",
            zorder=6,
        )


def draw_isoceles_triangle(
    fn: InvertibleFunction = _IDENTITY,
    color: tuple[float, float, float] = (0.0, 0.0, 1.0),
) -> None:
    """An isoceles triangle with vertices labelled A, B, C."""
    _draw_labelled_triangle(
        [zero, Vector2.e_1, 0.5 * Vector2.e_1 + Vector2.e_2],
        ["A", "B", "C"],
        fn,
        color,
    )


def draw_second_right_triangle(
    fn: InvertibleFunction = _IDENTITY,
    color: tuple[float, float, float] = (0.0, 0.0, 1.0),
) -> None:
    """A right triangle in the second quadrant, labelled by coordinate."""
    _draw_labelled_triangle(
        [zero, -4 * Vector2.e_1, -4 * Vector2.e_1 + 3 * Vector2.e_2],
        ["(0,0)", "(-4,0)", "(-4,3)"],
        fn,
        color,
        label_offset_x_sign=-1.0,
    )


def draw_right_triangle(
    fn: InvertibleFunction = _IDENTITY,
    color: tuple[float, float, float] = (0.0, 0.0, 1.0),
) -> None:
    """A 3-4-5 right triangle in the first quadrant, labelled by coordinate."""
    _draw_labelled_triangle(
        [zero, 3 * Vector2.e_1, 3 * Vector2.e_1 + 4 * Vector2.e_2],
        ["(0,0)", "(3,0)", "(3,4)"],
        fn,
        color,
    )


#         # Annotate with a 45-degree rotation
# ax.annotate('Rotated Annotation', xy=(0.5, 0.5), xytext=(0.7, 0.3),
#             arrowprops=dict(facecolor='black', shrink=0.05),
#             rotation=45)


def draw_ndc(
    fn: InvertibleFunction = _IDENTITY,
    color: tuple[float, float, float] = (0.0, 0.0, 1.0),
) -> None:
    axes = _current_axes()
    x_prime_direction_world_space = fn(Vector2.e_1) - fn(zero)
    x_world_space = Vector2.e_1
    y_prime_direction_world_space = fn(Vector2.e_2) - fn(zero)
    angle_radians = math.atan2(
        sine(x_world_space, x_prime_direction_world_space),
        cosine(x_world_space, x_prime_direction_world_space),
    )
    label_offset = (
        0 * x_prime_direction_world_space + 0.20 * y_prime_direction_world_space
    )

    vertices = [
        fn(v)
        for v in [
            -1 * Vector2.e_1 + -1 * Vector2.e_2,
            1 * Vector2.e_1 + -1 * Vector2.e_2,
            1 * Vector2.e_1 + 1 * Vector2.e_2,
            -1 * Vector2.e_1 + 1 * Vector2.e_2,
        ]
    ]

    square = Polygon(
        _xy(vertices),
        closed=True,
        fc="none",
        edgecolor="black",
    )
    axes.add_patch(square)

    vertices_as_np = np.array(_xy(vertices))
    # Plot dots at the vertices
    axes.scatter(
        vertices_as_np[:, 0], vertices_as_np[:, 1], color="red", s=5, zorder=5
    )  # zorder ensures dots are on top

    # Label each vertex
    labels = ["(-1,-1)", "(1,-1)", "(1,1)", "(-1,1)"]
    for i, label in enumerate(labels):
        # Use plt.annotate to place the label near the point
        plt.annotate(
            label,
            xy=(vertices_as_np[i, 0], vertices_as_np[i, 1]),
            xytext=(
                vertices_as_np[i, 0] + label_offset.coeff_e_1,
                vertices_as_np[i, 1] + label_offset.coeff_e_2,
            ),
            rotation=math.degrees(angle_radians),
            rotation_mode="anchor",
            zorder=6,
        )


def draw_screen(
    width: int,
    height: int,
    fn: InvertibleFunction = _IDENTITY,
    color: tuple[float, float, float] = (0.0, 0.0, 1.0),
) -> None:
    axes = _current_axes()
    d_width = 2.0 / width
    d_height = 2.0 / height
    for x in range(width):
        for y in range(height):
            vertices = [
                fn(v)
                for v in [
                    (-1.0 + d_width * x) * Vector2.e_1
                    + (-1.0 + d_height * y) * Vector2.e_2,
                    (-1.0 + d_width * (x + 1)) * Vector2.e_1
                    + (-1.0 + d_height * y) * Vector2.e_2,
                    (-1.0 + d_width * (x + 1)) * Vector2.e_1
                    + (-1.0 + d_height * (y + 1)) * Vector2.e_2,
                    (-1.0 + d_width * (x)) * Vector2.e_1
                    + (-1.0 + d_height * (y + 1)) * Vector2.e_2,
                ]
            ]

            square = Polygon(
                _xy(vertices),
                closed=True,
                fc="none",
                edgecolor="black",
            )
            axes.add_patch(square)
