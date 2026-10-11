"""Shared scene for the book's transformation step-sequence figures (ch06).

The ePiX replacement for the matplotlib families `_static/<name>-<n>.svg`:
`translation-forwards`, `translation2-forwards`, `scale`, and the rotation families.
Each frame shows a paddle as four labelled points over a unit grid, with the modelspace
frame (blue x-axis, magenta y-axis, highlighted origin bands) and the paddle positions
BOTH computed by driving mvp's OWN taught code -- `modelviewprojection.mathutils`
(`translate` / `scale_non_uniform` / `rotate` composed on `gacalc` `Vector2`s) -- so the
picture is produced by the exact functions the chapter teaches.

The modelspace frame is drawn as the transform applied to the basis: the x-axis is
`axes_transform(0) -> axes_transform(e_1)`, the y-axis `-> axes_transform(e_2)`, and the
origin bands are at `axes_transform(0)`. That one rule reproduces every family -- a
translation slides the frame, a scale stretches its basis axes, a rotation turns them.

The forwards story across the three referenced frames of each family:
  step 1  -- paddle in its modelspace, frame at the world origin (identity);
  step 2  -- the modelspace frame + paddle under the transform (basis axes show it);
  step 3  -- the paddle at its world position, world unit axes back at the origin.

Run by `tools/render_epix_figures.py` (each frame file in a fresh process). Every
argument is passed by keyword.
"""

from __future__ import annotations

from _scene2d import (
    BACKGROUND,  # noqa: F401  (read by tools/render_epix_figures.py from the globals)
    PendingFigure,
    Point,
    coordinate_axes_scene,
    epix,
)
from gacalc.g2 import Vector2
from gacalc.transforms import InvertibleFunction

from modelviewprojection.mathutils import (
    compose,
    rotate,
    scale_non_uniform,
    translate,
)

__all__: list[str] = [
    "BACKGROUND",
    "PendingFigure",
    "PADDLE1",
    "PADDLE2",
    "PADDLE1_COLOR",
    "PADDLE2_COLOR",
    "E1",
    "E2",
    "ORIGIN_VEC",
    "compose",
    "identity",
    "rotate",
    "scale_non_uniform",
    "translate",
    "transform_frame",
]

E1: Vector2 = Vector2.e_1
E2: Vector2 = Vector2.e_2
ORIGIN_VEC: Vector2 = 0 * E1 + 0 * E2

#: the paddle shape (c, d, a, b corners), shared by paddle1 and paddle2.
_CORNERS: list[tuple[Vector2, str]] = [
    (-1 * E1 + -3 * E2, "c"),
    (1 * E1 + -3 * E2, "d"),
    (1 * E1 + 3 * E2, "a"),
    (-1 * E1 + 3 * E2, "b"),
]
PADDLE1: list[tuple[Vector2, str]] = _CORNERS
PADDLE2: list[tuple[Vector2, str]] = _CORNERS

PADDLE1_COLOR: epix.Color = epix.rgb(r=0.578, g=0.0, b=1.0)  # purple
PADDLE2_COLOR: epix.Color = epix.rgb(r=1.0, g=0.0, b=0.0)  # red

GRID: epix.Color = epix.rgb(r=0.72, g=0.76, b=0.92)
BAND: epix.Color = epix.rgb(r=0.80, g=0.84, b=0.95)
X_AXIS: epix.Color = epix.rgb(r=0.0, g=0.0, b=1.0)  # modelspace x, blue
Y_AXIS: epix.Color = epix.rgb(r=1.0, g=0.0, b=1.0)  # modelspace y, magenta


def identity() -> InvertibleFunction[Vector2]:
    """The identity transform, built from the taught code (a zero translation)."""
    return translate(b=ORIGIN_VEC)


def _pt(v: Vector2) -> Point:
    """A `gacalc` `Vector2` as an `epix.Point` (coords may be sympy; coerce to float)."""
    return Point(x=float(v.x), y=float(v.y))


def _clip(
    x0: float, y0: float, x1: float, y1: float, bound: float
) -> tuple[float, float, float, float] | None:
    """Liang-Barsky clip of the segment to the box [-bound, bound]^2, or None if it
    misses the box entirely. Lets a transformed (e.g. rotated) gridline be drawn only
    where it crosses the frame, exactly as the matplotlib axes clip it."""
    dx: float = x1 - x0
    dy: float = y1 - y0
    t0: float = 0.0
    t1: float = 1.0
    for p, q in (
        (-dx, x0 + bound),
        (dx, bound - x0),
        (-dy, y0 + bound),
        (dy, bound - y0),
    ):
        if p == 0.0:
            if q < 0.0:
                return None
        else:
            r: float = q / p
            if p < 0.0:
                if r > t1:
                    return None
                t0 = max(t0, r)
            else:
                if r < t0:
                    return None
                t1 = min(t1, r)
    return (x0 + t0 * dx, y0 + t0 * dy, x0 + t1 * dx, y0 + t1 * dy)


def _seg(a: Vector2, b: Vector2, bound: float) -> None:
    """Draw the segment a->b clipped to the frame (endpoints already in world coords)."""
    pa: Point = _pt(a)
    pb: Point = _pt(b)
    clipped: tuple[float, float, float, float] | None = _clip(
        pa.x1(), pa.x2(), pb.x1(), pb.x2(), bound
    )
    if clipped is not None:
        epix.line(
            tail=Point(x=clipped[0], y=clipped[1]),
            head=Point(x=clipped[2], y=clipped[3]),
        )


def _draw_grid(
    frame_transform: InvertibleFunction[Vector2], bound: float
) -> None:
    """The unit grid, drawn under `frame_transform` and clipped to the frame -- so a
    translation leaves it standard (integer grid maps to itself), a scale spaces it
    out, a rotation turns the whole grid, matching the matplotlib originals."""
    ext: int = (
        int(bound * 1.8) + 2
    )  # wide enough that a rotation still fills the frame
    epix.pen(color=GRID, width=0.5)
    i: int = -ext
    while i <= ext:
        _seg(
            frame_transform(i * E1 + -ext * E2),
            frame_transform(i * E1 + ext * E2),
            bound,
        )
        _seg(
            frame_transform(-ext * E1 + i * E2),
            frame_transform(ext * E1 + i * E2),
            bound,
        )
        i += 1


def _draw_modelspace_frame(
    frame_transform: InvertibleFunction[Vector2], bound: float
) -> None:
    """The modelspace frame under `frame_transform`: the thick origin bands are the
    transformed modelspace axis-lines (x=0, y=0), and the blue/magenta unit axes are
    `0 -> e_1` and `0 -> e_2` transformed."""
    ext: int = int(bound * 1.8) + 2
    epix.pen(color=BAND, width=5.0)
    _seg(
        frame_transform(0 * E1 + -ext * E2),
        frame_transform(0 * E1 + ext * E2),
        bound,
    )
    _seg(
        frame_transform(-ext * E1 + 0 * E2),
        frame_transform(ext * E1 + 0 * E2),
        bound,
    )
    epix.pen(color=X_AXIS, width=1.6)
    _seg(frame_transform(ORIGIN_VEC), frame_transform(E1), bound)
    epix.pen(color=Y_AXIS, width=1.6)
    _seg(frame_transform(ORIGIN_VEC), frame_transform(E2), bound)


def _draw_geometry(
    geometry: list[tuple[Vector2, str]],
    color: epix.Color,
    transform: InvertibleFunction[Vector2],
) -> None:
    """The paddle points placed by `transform` (the taught code), each labelled."""
    epix.pen(color=color, width=1.2)
    epix.label_color(color=color)
    for corner, name in geometry:
        at: Point = _pt(transform(corner))
        epix.dot(at=at)
        epix.label(
            at=at,
            offset=Point(x=0, y=10),
            text=f"${name}$",
            align=epix.LabelPos.c,
        )
    epix.label_color(color=epix.black())


def transform_frame(
    geometry: list[tuple[Vector2, str]],
    color: epix.Color,
    frame_transform: InvertibleFunction[Vector2],
    paddle_transform: InvertibleFunction[Vector2],
    step: int,
    title_base: str,
    bound: float = 10.0,
    scale_in: float = 0.3,
) -> PendingFigure:
    """One frame of a transformation sequence. The grid, origin bands and modelspace
    unit axes are all drawn under `frame_transform` (the step's own function -- identity
    in the "settled" frames, the transform itself in the frame that shows it acting);
    the paddle is placed by `paddle_transform` (the accumulated transform so far). Both
    are built from `mathutils`, so the whole picture comes out of the taught code."""
    low: Point = Point(x=-bound, y=-bound)
    high: Point = Point(x=bound, y=bound)
    fig: PendingFigure
    with coordinate_axes_scene(
        lower_left=low,
        upper_right=high,
        scale_in=scale_in,
        title=f"{title_base}, step {step}",
    ) as fig:
        _draw_grid(frame_transform=frame_transform, bound=bound)
        _draw_modelspace_frame(frame_transform=frame_transform, bound=bound)
        _draw_geometry(
            geometry=geometry, color=color, transform=paddle_transform
        )
    return fig
