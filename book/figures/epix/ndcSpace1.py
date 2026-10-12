# %% [markdown]
# # ndcSpace1 — two paddles in 1024x768 pixel space (ch10)
#
# ePiX replacement for `_static/ndcSpace1.svg`.

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
    x_lo=0,
    x_hi=1024,
    y_lo=0,
    y_hi=768,
    x_interval=200,
    y_interval=100,
    scale_x=0.0045,
    scale_y=0.0045,
) as fig:
    filled_rect(lower_left=Point(x=53, y=384), upper_right=Point(x=320, y=704))
    filled_rect(lower_left=Point(x=347, y=384), upper_right=Point(x=826, y=704))

# %%
fig
