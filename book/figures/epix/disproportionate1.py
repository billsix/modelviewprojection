# %% [markdown]
# # disproportionate1 — two paddles drawn with a tall (ratio 2) aspect (ch08)
#
# ePiX replacement for `_static/disproportionate1.svg`. Same paddles as plot2, with an
# unequal x/y scale, to show how a disproportionate viewport distorts them.

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
    scale_x=1.7,
    scale_y=3.4,
    decimals=1,
    margin_left_frac=0.36,
    margin_right_frac=0.32,
) as fig:
    c = Point(x=-1.0, y=-0.3)
    d = Point(x=-0.8, y=-0.3)
    a = Point(x=-0.8, y=0.3)
    b = Point(x=-1.0, y=0.3)
    g = Point(x=0.8, y=-0.3)
    h = Point(x=1.0, y=-0.3)
    e = Point(x=1.0, y=0.3)
    f = Point(x=0.8, y=0.3)
    plot_path(points=[c, d, a, b, c])
    plot_path(points=[g, h, e, f, g])
    plot_markers(points=[c, d, a, b, g, h, e, f])
    plot_text(
        at=a, text="(-0.8, 0.3)", offset=Point(x=6, y=8), align=epix.LabelPos.r
    )
    plot_text(
        at=d,
        text="(-0.8, -0.3)",
        offset=Point(x=6, y=-8),
        align=epix.LabelPos.r,
    )
    plot_text(
        at=b, text="(-1.0, 0.3)", offset=Point(x=-6, y=8), align=epix.LabelPos.l
    )
    plot_text(
        at=c,
        text="(-1.0, -0.3)",
        offset=Point(x=-6, y=-8),
        align=epix.LabelPos.l,
    )
    plot_text(
        at=e, text="(1.0, 0.3)", offset=Point(x=6, y=8), align=epix.LabelPos.r
    )
    plot_text(
        at=h, text="(1.0, -0.3)", offset=Point(x=6, y=-8), align=epix.LabelPos.r
    )
    plot_text(
        at=f, text="(0.8, 0.3)", offset=Point(x=-6, y=8), align=epix.LabelPos.l
    )
    plot_text(
        at=g,
        text="(0.8, -0.3)",
        offset=Point(x=-6, y=-8),
        align=epix.LabelPos.l,
    )

# %%
fig
