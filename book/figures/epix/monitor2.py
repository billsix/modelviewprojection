# %% [markdown]
# # monitor2 — a 1920x1200 monitor in pixel coordinates (ch02)
#
# ePiX replacement for `_static/monitor2.svg`.

# %%
from __future__ import annotations

from _scene2d import BACKGROUND, PendingFigure, framed_plot_scene  # noqa: F401

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
    pass

# %%
fig
