# %% [markdown]
# # scale-2 — modelspace basis scaled by (2, 3), paddle scaled (step 2)
#
# ePiX replacement for `_static/scale-2.svg` (ch06). The modelspace basis axes stretch
# to (2,0) and (0,3) and the paddle scales, all via `mathutils.scale_non_uniform`.

# %%
from __future__ import annotations

from _transform_sequence import (  # noqa: F401
    BACKGROUND,
    PADDLE1,
    PADDLE1_COLOR,
    PendingFigure,
    scale_non_uniform,
    transform_frame,
)

s = scale_non_uniform(2.0, 3.0)
fig: PendingFigure = transform_frame(
    geometry=PADDLE1,
    color=PADDLE1_COLOR,
    frame_transform=s,
    paddle_transform=s,
    step=2,
    title_base="Scale Relative to World Space",
)

# %%
fig
