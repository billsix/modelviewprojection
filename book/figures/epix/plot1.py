# %% [markdown]
# # plot1 — one paddle in its own space, corners labelled with coordinates (ch02)
#
# ePiX replacement for `_static/plot1.svg`.

# %%
from __future__ import annotations

from _scene2d import (  # noqa: F401
    BACKGROUND,
    PendingFigure,
    Point,
    epix,
    framed_plot_scene,
    plot_markers,
    plot_path,
    plot_text,
)

fig: PendingFigure
with framed_plot_scene(
    x_lo=-1.0,
    x_hi=1.0,
    y_lo=-1.0,
    y_hi=1.0,
    x_interval=0.5,
    y_interval=0.5,
    scale_x=2.4,
    scale_y=2.4,
    decimals=1,
    margin_left_frac=0.36,
    margin_right_frac=0.30,
) as fig:
    c = Point(x=-1.0, y=-0.3)
    d = Point(x=-0.8, y=-0.3)
    a = Point(x=-0.8, y=0.3)
    b = Point(x=-1.0, y=0.3)
    plot_path(points=[c, d, a, b, c])
    plot_markers(points=[c, d, a, b])
    # right-column vertices labelled to the right, left-column to the left.
    plot_text(
        at=a,
        text="A = (-0.8, 0.3)",
        offset=Point(x=6, y=8),
        align=epix.LabelPos.r,
    )
    plot_text(
        at=d,
        text="D = (-0.8, -0.3)",
        offset=Point(x=6, y=-8),
        align=epix.LabelPos.r,
    )
    plot_text(
        at=b,
        text="B = (-1.0, 0.3)",
        offset=Point(x=-6, y=8),
        align=epix.LabelPos.l,
    )
    plot_text(
        at=c,
        text="C = (-1.0, -0.3)",
        offset=Point(x=-6, y=-8),
        align=epix.LabelPos.l,
    )

# %%
fig
