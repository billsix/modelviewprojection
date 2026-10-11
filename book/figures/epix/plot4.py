# %% [markdown]
# # plot4 — two paddles carrying symbolic "+ c" and "+ d" offsets (ch05)
#
# ePiX replacement for `_static/plot4.svg`.

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
    margin_right_frac=0.40,
) as fig:
    c_bl = Point(x=-1.0, y=0.2)
    c_br = Point(x=-0.8, y=0.2)
    c_tr = Point(x=-0.8, y=0.8)
    c_tl = Point(x=-1.0, y=0.8)
    d_bl = Point(x=0.8, y=-0.3)
    d_br = Point(x=1.0, y=-0.3)
    d_tr = Point(x=1.0, y=0.3)
    d_tl = Point(x=0.8, y=0.3)
    plot_path(points=[c_bl, c_br, c_tr, c_tl, c_bl])
    plot_path(points=[d_bl, d_br, d_tr, d_tl, d_bl])
    plot_markers(points=[c_bl, c_br, c_tr, c_tl, d_bl, d_br, d_tr, d_tl])
    plot_text(
        at=c_tl,
        text="(-1.0, 0.3) + c",
        offset=Point(x=-6, y=8),
        align=epix.LabelPos.l,
    )
    plot_text(
        at=c_tr,
        text="(-0.8, 0.3) + c",
        offset=Point(x=6, y=8),
        align=epix.LabelPos.r,
    )
    plot_text(
        at=c_br,
        text="(-0.8, -0.3) + c",
        offset=Point(x=6, y=-8),
        align=epix.LabelPos.r,
    )
    plot_text(
        at=c_bl,
        text="(-1.0, -0.3) + c",
        offset=Point(x=-6, y=-8),
        align=epix.LabelPos.l,
    )
    plot_text(
        at=d_tl,
        text="(0.8, 0.3) + d",
        offset=Point(x=-6, y=8),
        align=epix.LabelPos.l,
    )
    plot_text(
        at=d_tr,
        text="(1.0, 0.3) + d",
        offset=Point(x=6, y=8),
        align=epix.LabelPos.r,
    )
    plot_text(
        at=d_br,
        text="(1.0, -0.3) + d",
        offset=Point(x=6, y=-8),
        align=epix.LabelPos.r,
    )
    plot_text(
        at=d_bl,
        text="(0.8, -0.3) + d",
        offset=Point(x=-6, y=-8),
        align=epix.LabelPos.l,
    )

# %%
fig
