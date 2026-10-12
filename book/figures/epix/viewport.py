# %% [markdown]
# # viewport — the NDC square mapped into a 1920x1200 viewport (ch10)
#
# ePiX replacement for `_static/viewport.svg`. The white box is the viewport; the corner
# labels are the NDC coordinates that map to each corner.

# %%
from __future__ import annotations

from _scene2d import (  # noqa: F401
    BACKGROUND,
    PendingFigure,
    Point,
    epix,
    filled_rect,
    framed_plot_scene,
    plot_text,
)

fig: PendingFigure
with framed_plot_scene(
    x_lo=0,
    x_hi=1920,
    y_lo=0,
    y_hi=1200,
    x_interval=500,
    y_interval=200,
    scale_x=0.0024,
    scale_y=0.0024,
) as fig:
    filled_rect(lower_left=Point(x=360, y=0), upper_right=Point(x=1560, y=1200))
    plot_text(at=Point(x=360, y=50), text="$(-1,-1)$", align=epix.LabelPos.l)
    plot_text(at=Point(x=1400, y=50), text="$(1,-1)$", align=epix.LabelPos.l)
    plot_text(at=Point(x=360, y=1150), text="$(-1,1)$", align=epix.LabelPos.l)
    plot_text(at=Point(x=1400, y=1150), text="$(1,1)$", align=epix.LabelPos.l)

# %%
fig
