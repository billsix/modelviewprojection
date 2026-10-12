# %% [markdown]
# # screenspace — two paddles in screen (pixel) space, clipped to the monitor (ch02)
#
# ePiX replacement for `_static/screenspace.svg`. The paddles extend past the top/right
# of the 1024x768 monitor, so only the on-screen part shows.

# %%
from __future__ import annotations

from _scene2d import (  # noqa: F401
    BACKGROUND,
    PendingFigure,
    Point,
    clipped_rect,
    framed_plot_scene,
)

FLL = Point(x=0, y=0)
FUR = Point(x=1024, y=768)
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
    clipped_rect(
        lower_left=Point(x=100, y=600),
        upper_right=Point(x=600, y=1100),
        frame_lower_left=FLL,
        frame_upper_right=FUR,
    )
    clipped_rect(
        lower_left=Point(x=650, y=600),
        upper_right=Point(x=1550, y=1100),
        frame_lower_left=FLL,
        frame_upper_right=FUR,
    )

# %%
fig
