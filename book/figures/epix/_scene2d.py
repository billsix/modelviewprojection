"""Shared 2D scene helpers for the mvp book's ePiX figures.

A labelled coordinate-axes stage plus the small drawing primitives the book's 2D
figures are built from (a filled rectangle, a point marker + label, a vector arrow).
Figures that illustrate a transformation drive mvp's own taught code
(``modelviewprojection.mathutils``) to place their geometry, so the picture is produced
by the exact functions the chapter teaches.

Figure files are jupytext percent notebooks in the style of epix-mirror's
``notebooks/``; ``tools/render_epix_figures.py`` runs each in a fresh process (and skips
these ``_``-prefixed helpers). Modelled on the sibling geometricalgebra repo's
``_scene2d.py``. Every argument is passed by keyword, so a figure reads as a scene
description.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from contextlib import contextmanager

import epix
from epix import Point

# What `epix.figure(...)` yields: a proxy that becomes the rendered `Figure` after the
# `with` block (its `.eepic`/`.png`/`.save` forward to it). epix keeps the class
# private, so the figure files type their `fig` through this alias.
from epix.figure import _Pending as PendingFigure

__all__: list[str] = [
    "BACKGROUND",
    "PendingFigure",
    "Point",
    "epix",
    "coordinate_axes_scene",
    "framed_plot_scene",
    "filled_rect",
    "clipped_rect",
    "point_label",
    "vector",
    "plot_path",
    "plot_markers",
    "plot_text",
    "PLOT_LINE",
    "PLOT_MARKER",
]

# gnuplot-default-ish colours for the static coordinate plots (plot1-4, screenspace,
# ndcSpace, viewport, disproportionate): a violet path and cyan point markers.
PLOT_LINE: epix.Color = epix.rgb(r=0.60, g=0.20, b=0.80)
PLOT_MARKER: epix.Color = epix.rgb(r=0.25, g=0.60, b=0.85)

# The PNGs for the HTML book are flattened onto this so a dark-mode page shows a
# uniform light panel instead of a transparent sheet.
BACKGROUND: str = "#f2f2f2"

UNIT_SCALE_IN: float = 0.5  # inches per unit, kept equal on both axes


def _frame_with_ticks(
    lower_left: Point, upper_right: Point, tick_len: float
) -> None:
    """A gnuplot-style border box with inward tick marks on all four sides and
    numeric labels OUTSIDE the box (on the bottom and left), so a reader reads
    coordinates off the border and nothing the figure draws can occlude them.
    """
    epix.pen(color=epix.black(), width=1.0)
    # The last point repeats the first so the closing (left) edge is an explicit
    # segment: ePiX strokes the polyline segments but NOT the implicit closing edge
    # of a closed Path, so without this the left border is missing.
    epix.Path(
        data=[
            lower_left,
            Point(x=upper_right.x1(), y=lower_left.x2()),
            upper_right,
            Point(x=lower_left.x1(), y=upper_right.x2()),
            lower_left,
        ],
        closed=False,
        filled=False,
    ).draw()
    epix.pen(color=epix.black(), width=0.8)
    epix.font_size(size="normalsize")
    bottom: float = lower_left.x2()
    top: float = upper_right.x2()
    left: float = lower_left.x1()
    right: float = upper_right.x1()
    # x ticks on the bottom and top edges; numbers below the bottom edge.
    for i in range(math.ceil(left), math.floor(right) + 1):
        epix.line(
            tail=Point(x=i, y=bottom), head=Point(x=i, y=bottom + tick_len)
        )
        epix.line(tail=Point(x=i, y=top), head=Point(x=i, y=top - tick_len))
        epix.label(
            at=Point(x=i, y=bottom),
            offset=Point(x=0, y=-11),
            text=f"${i}$",
            align=epix.LabelPos.c,
        )
    # y ticks on the left and right edges; numbers left of the left edge.
    for i in range(math.ceil(bottom), math.floor(top) + 1):
        epix.line(tail=Point(x=left, y=i), head=Point(x=left + tick_len, y=i))
        epix.line(tail=Point(x=right, y=i), head=Point(x=right - tick_len, y=i))
        epix.label(
            at=Point(x=left, y=i),
            offset=Point(x=-13, y=0),
            text=f"${i}$",
            align=epix.LabelPos.c,
        )


@contextmanager
def coordinate_axes_scene(
    lower_left: Point,
    upper_right: Point,
    scale_in: float = UNIT_SCALE_IN,
    title: str = "",
) -> Iterator[PendingFigure]:
    """``epix.figure`` with a gnuplot-style framed grid: a border box with integer
    numeric ticks on all four sides (numbers on the bottom and left), so a reader can
    read coordinates straight off the border. An optional ``title`` is centred above
    the frame.

    ``lower_left``/``upper_right`` are the FRAME (data) extent. The physical size
    follows it at ``scale_in`` inches per unit, so every figure is at the same scale
    whatever its box. The frame + numbers are drawn first; because the labels sit
    OUTSIDE the box, nothing the figure draws inside can occlude them (the lesson from
    the first arrow-axes draft). The figure canvas is expanded past the frame so the
    outside numbers (and the title) are not clipped.
    """
    width: float = upper_right.x1() - lower_left.x1()
    height: float = upper_right.x2() - lower_left.x2()
    # canvas margins past the frame: room for the bottom/left numbers, a little on
    # the right; the top margin grows when there is a title to sit above the frame.
    margin_lb: float = 0.7
    margin_rt: float = 0.35
    margin_top: float = 1.1 if title else margin_rt
    canvas_ll: Point = Point(
        x=lower_left.x1() - margin_lb, y=lower_left.x2() - margin_lb
    )
    canvas_ur: Point = Point(
        x=upper_right.x1() + margin_rt, y=upper_right.x2() + margin_top
    )
    canvas_w: float = canvas_ur.x1() - canvas_ll.x1()
    canvas_h: float = canvas_ur.x2() - canvas_ll.x2()
    size: str = f"{canvas_w * scale_in:.2f}x{canvas_h * scale_in:.2f}in"
    # tick length in data units, scaled so it looks the same across figure sizes
    tick_len: float = 0.06 * max(width, height) / 8.0
    fig: PendingFigure
    with epix.figure(
        lower_left=canvas_ll, upper_right=canvas_ur, size=size
    ) as fig:
        _frame_with_ticks(
            lower_left=lower_left, upper_right=upper_right, tick_len=tick_len
        )
        if title:
            epix.font_size(size="large")
            epix.label(
                at=Point(
                    x=(lower_left.x1() + upper_right.x1()) / 2,
                    y=upper_right.x2(),
                ),
                offset=Point(x=0, y=14),
                text=title,
                align=epix.LabelPos.c,
            )
        yield fig


def filled_rect(
    lower_left: Point,
    upper_right: Point,
    color: epix.Color = epix.white(intensity=1.0),
    edge_width: float = 1.2,
) -> None:
    """A filled, black-edged rectangle spanning ``lower_left`` to ``upper_right``."""
    corners: list[Point] = [
        lower_left,
        Point(x=upper_right.x1(), y=lower_left.x2()),
        upper_right,
        Point(x=lower_left.x1(), y=upper_right.x2()),
    ]
    # Fill first (needs the closed polygon), then stroke the outline as an explicit
    # polyline that returns to the start -- ePiX does not stroke a closed Path's
    # implicit closing edge, so a plain closed Path drops the left side.
    epix.fill(color=color)
    epix.pen(color=epix.black(), width=edge_width)
    epix.Path(data=corners, closed=True, filled=True).draw()
    epix.nofill()
    epix.Path(data=[*corners, lower_left], closed=False, filled=False).draw()


def point_label(
    at: Point,
    text: str,
    offset: Point = Point(x=0, y=8),
    align: epix.LabelPos = epix.LabelPos.c,
) -> None:
    """A small dot at ``at`` with a label offset from it (offset in points)."""
    epix.pen(color=epix.black(), width=1.0)
    epix.dot(at=at)
    epix.label(at=at, offset=offset, text=text, align=align)


def vector(
    tail: Point,
    head: Point,
    text: str = "",
    offset: Point = Point(x=7, y=0),
    color: epix.Color = epix.black(),
    align: epix.LabelPos = epix.LabelPos.r,
) -> None:
    """A coloured arrow ``tail``->``head`` with an optional label (matching colour)."""
    epix.pen(color=color, width=1.8)
    epix.arrow(tail=tail, head=head, scale=0.7)
    if text:
        epix.label_color(color=color)
        epix.label(at=head, offset=offset, text=text, align=align)
        epix.label_color(color=epix.black())


def _ticks(lo: float, hi: float, interval: float, decimals: int) -> list[float]:
    """The tick values at multiples of ``interval`` within [lo, hi] (inclusive)."""
    out: list[float] = []
    n: int = math.ceil(round(lo / interval, 6))
    while n * interval <= hi + 1e-9:
        out.append(round(n * interval, decimals + 1))
        n += 1
    return out


@contextmanager
def framed_plot_scene(
    x_lo: float,
    x_hi: float,
    y_lo: float,
    y_hi: float,
    x_interval: float,
    y_interval: float,
    scale_x: float,
    scale_y: float,
    decimals: int = 0,
    margin_left_frac: float = 0.13,
    margin_right_frac: float = 0.05,
) -> Iterator[PendingFigure]:
    """A gnuplot-style framed plot: a border box over [x_lo,x_hi]x[y_lo,y_hi] with
    numeric ticks + numbers on the bottom and left (interval per axis, formatted to
    ``decimals`` places), inward ticks on the top and right. ``scale_x``/``scale_y``
    are inches per data unit -- unequal values reproduce gnuplot ``set size ratio``
    (the disproportionate figures); equal values reproduce ``ratio -1``. The left/right
    canvas margins are fractions of the width (bump ``margin_left_frac`` when labels sit
    to the left of the frame). The ePiX replacement for the ``_static/gnuplot/*`` family
    (static coordinate diagrams, no transform, so no ``mathutils``)."""
    width: float = x_hi - x_lo
    height: float = y_hi - y_lo
    margin_l: float = width * margin_left_frac
    margin_b: float = height * 0.13
    margin_rt_x: float = width * margin_right_frac
    margin_rt_y: float = height * 0.05
    canvas_w: float = (width + margin_l + margin_rt_x) * scale_x
    canvas_h: float = (height + margin_b + margin_rt_y) * scale_y
    size: str = f"{canvas_w:.2f}x{canvas_h:.2f}in"
    tick_x: float = width * 0.015
    tick_y: float = height * 0.015
    fig: PendingFigure
    with epix.figure(
        lower_left=Point(x=x_lo - margin_l, y=y_lo - margin_b),
        upper_right=Point(x=x_hi + margin_rt_x, y=y_hi + margin_rt_y),
        size=size,
    ) as fig:
        epix.font_size(size="normalsize")
        epix.pen(color=epix.black(), width=1.0)
        # Repeat the first point last so the closing (left) edge draws -- ePiX does
        # not stroke a closed Path's implicit closing edge (see _frame_with_ticks).
        epix.Path(
            data=[
                Point(x=x_lo, y=y_lo),
                Point(x=x_hi, y=y_lo),
                Point(x=x_hi, y=y_hi),
                Point(x=x_lo, y=y_hi),
                Point(x=x_lo, y=y_lo),
            ],
            closed=False,
            filled=False,
        ).draw()
        epix.pen(color=epix.black(), width=0.8)
        for xv in _ticks(
            lo=x_lo, hi=x_hi, interval=x_interval, decimals=decimals
        ):
            epix.line(
                tail=Point(x=xv, y=y_lo), head=Point(x=xv, y=y_lo + tick_y)
            )
            epix.line(
                tail=Point(x=xv, y=y_hi), head=Point(x=xv, y=y_hi - tick_y)
            )
            epix.label(
                at=Point(x=xv, y=y_lo),
                offset=Point(x=0, y=-11),
                text=f"${xv:.{decimals}f}$",
                align=epix.LabelPos.c,
            )
        for yv in _ticks(
            lo=y_lo, hi=y_hi, interval=y_interval, decimals=decimals
        ):
            epix.line(
                tail=Point(x=x_lo, y=yv), head=Point(x=x_lo + tick_x, y=yv)
            )
            epix.line(
                tail=Point(x=x_hi, y=yv), head=Point(x=x_hi - tick_x, y=yv)
            )
            epix.label(
                at=Point(x=x_lo, y=yv),
                offset=Point(x=-13, y=0),
                text=f"${yv:.{decimals}f}$",
                align=epix.LabelPos.c,
            )
        yield fig


def plot_path(points: list[Point], color: epix.Color = PLOT_LINE) -> None:
    """A connected (unclosed) polyline through ``points``."""
    epix.pen(color=color, width=1.4)
    epix.Path(data=points, closed=False, filled=False).draw()


def plot_markers(points: list[Point], color: epix.Color = PLOT_MARKER) -> None:
    """A filled dot at each of ``points`` (gnuplot ``pt 7``)."""
    epix.pen(color=color, width=1.6)
    for p in points:
        epix.dot(at=p)


def plot_text(
    at: Point,
    text: str,
    offset: Point = Point(x=0, y=0),
    align: epix.LabelPos = epix.LabelPos.c,
) -> None:
    """A black text label placed at a data coordinate."""
    epix.label_color(color=epix.black())
    epix.label(at=at, offset=offset, text=text, align=align)


def _clip_seg(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x_lo: float,
    x_hi: float,
    y_lo: float,
    y_hi: float,
) -> tuple[float, float, float, float] | None:
    """Liang-Barsky clip of a segment to [x_lo,x_hi]x[y_lo,y_hi], or None if outside."""
    dx: float = x1 - x0
    dy: float = y1 - y0
    t0: float = 0.0
    t1: float = 1.0
    for p, q in (
        (-dx, x0 - x_lo),
        (dx, x_hi - x0),
        (-dy, y0 - y_lo),
        (dy, y_hi - y0),
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


def clipped_rect(
    lower_left: Point,
    upper_right: Point,
    frame_lower_left: Point,
    frame_upper_right: Point,
    width: float = 1.0,
) -> None:
    """The outline of a rectangle, each edge clipped to the frame box -- so a paddle
    that extends past the monitor/NDC bounds shows only the part on screen (the
    screenspace figures' point). Edges wholly outside are omitted."""
    x0: float = lower_left.x1()
    y0: float = lower_left.x2()
    x1: float = upper_right.x1()
    y1: float = upper_right.x2()
    edges: list[tuple[float, float, float, float]] = [
        (x0, y0, x1, y0),  # bottom
        (x1, y0, x1, y1),  # right
        (x1, y1, x0, y1),  # top
        (x0, y1, x0, y0),  # left
    ]
    epix.pen(color=epix.black(), width=width)
    fx0: float = frame_lower_left.x1()
    fy0: float = frame_lower_left.x2()
    fx1: float = frame_upper_right.x1()
    fy1: float = frame_upper_right.x2()
    for ex0, ey0, ex1, ey1 in edges:
        c: tuple[float, float, float, float] | None = _clip_seg(
            ex0, ey0, ex1, ey1, fx0, fx1, fy0, fy1
        )
        if c is not None:
            epix.line(tail=Point(x=c[0], y=c[1]), head=Point(x=c[2], y=c[3]))
