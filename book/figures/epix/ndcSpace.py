# %% [markdown]
# # ndcSpace — two paddles in normalized device coordinates (ch10)
#
# ePiX replacement for `_static/ndcSpace.svg`.

# %%
from __future__ import annotations

from _scene2d import (  # noqa: F401
    BACKGROUND,
    PendingFigure,
    Point,
    filled_rect,
    framed_plot_scene,
)

fig: PendingFigure
with framed_plot_scene(
    x_lo=-1.0,
    x_hi=1.0,
    y_lo=-1.0,
    y_hi=1.0,
    x_interval=0.5,
    y_interval=0.5,
    scale_x=2.2,
    scale_y=2.2,
    decimals=1,
) as fig:
    filled_rect(
        lower_left=Point(x=-0.895, y=0.0), upper_right=Point(x=-0.375, y=0.833)
    )
    filled_rect(
        lower_left=Point(x=-0.322, y=0.0), upper_right=Point(x=0.614, y=0.833)
    )

# %%
fig
