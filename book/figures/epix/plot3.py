# %% [markdown]
# # plot3 — a paddle whose corners carry a symbolic "+ c" offset (ch05)
#
# ePiX replacement for `_static/plot3.svg`.

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
    margin_left_frac=0.44,
    margin_right_frac=0.34,
) as fig:
    bl = Point(x=-1.0, y=0.2)
    br = Point(x=-0.8, y=0.2)
    tr = Point(x=-0.8, y=0.8)
    tl = Point(x=-1.0, y=0.8)
    plot_path(points=[bl, br, tr, tl, bl])
    plot_markers(points=[bl, br, tr, tl])
    plot_text(
        at=tl,
        text="(-1.0, 0.3) + c",
        offset=Point(x=-6, y=8),
        align=epix.LabelPos.l,
    )
    plot_text(
        at=tr,
        text="(-0.8, 0.3) + c",
        offset=Point(x=6, y=8),
        align=epix.LabelPos.r,
    )
    plot_text(
        at=br,
        text="(-0.8, -0.3) + c",
        offset=Point(x=6, y=-8),
        align=epix.LabelPos.r,
    )
    plot_text(
        at=bl,
        text="(-1.0, -0.3) + c",
        offset=Point(x=-6, y=-8),
        align=epix.LabelPos.l,
    )

# %%
fig
