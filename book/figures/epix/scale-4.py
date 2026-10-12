# %% [markdown]
# # scale-4 — paddle scaled, world unit axes back at origin (step 3)
#
# ePiX replacement for `_static/scale-4.svg` (ch06), via `mathutils.scale_non_uniform`.

# %%
from __future__ import annotations

from _transform_sequence import (  # noqa: F401
    BACKGROUND,
    PADDLE1,
    PADDLE1_COLOR,
    PendingFigure,
    identity,
    scale_non_uniform,
    transform_frame,
)

s = scale_non_uniform(2.0, 3.0)
fig: PendingFigure = transform_frame(
    geometry=PADDLE1,
    color=PADDLE1_COLOR,
    frame_transform=identity(),
    paddle_transform=s,
    step=3,
    title_base="Scale Relative to World Space",
)

# %%
fig
