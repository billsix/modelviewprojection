# %% [markdown]
# # modelspace — the paddle's modelspace
#
# The paddle defined in its own modelspace: a rectangle from (-1,-3) to (1,3), its
# four corners labelled a, b, c, d. This is the ePiX replacement for the gnuplot
# figure `_static/modelspace.svg` (ch16). Built with the `epix` Python package.

# %%
from __future__ import annotations

from _scene2d import (
    BACKGROUND,  # noqa: F401  (read by tools/render_epix_figures.py from the globals)
    PendingFigure,
    Point,
    coordinate_axes_scene,
    epix,
    filled_rect,
    point_label,
)

LOW: Point = Point(x=-4.0, y=-4.0)
HIGH: Point = Point(x=4.0, y=4.0)

# The paddle's four modelspace corners.
A: Point = Point(x=1.0, y=3.0)
B: Point = Point(x=-1.0, y=3.0)
C: Point = Point(x=-1.0, y=-3.0)
D: Point = Point(x=1.0, y=-3.0)

fig: PendingFigure
with coordinate_axes_scene(lower_left=LOW, upper_right=HIGH) as fig:
    filled_rect(lower_left=C, upper_right=A, color=epix.white(intensity=1.0))
    point_label(at=A, text="a = (1,3)", offset=Point(x=18, y=6))
    point_label(at=B, text="b = (-1,3)", offset=Point(x=-18, y=6))
    point_label(at=C, text="c = (-1,-3)", offset=Point(x=-18, y=-8))
    point_label(at=D, text="d = (1,-3)", offset=Point(x=18, y=-8))

# %%
fig
