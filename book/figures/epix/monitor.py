# %% [markdown]
# # monitor — a 1024x768 monitor in pixel coordinates (ch02)
#
# ePiX replacement for `_static/monitor.svg`. A static pixel-space frame; no transform.

# %%
from __future__ import annotations

from _scene2d import BACKGROUND, PendingFigure, framed_plot_scene  # noqa: F401

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
    pass

# %%
fig
