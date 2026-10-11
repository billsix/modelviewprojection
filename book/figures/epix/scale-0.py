# %% [markdown]
# # scale-0 — paddle1 in its modelspace (step 1)
#
# ePiX replacement for `_static/scale-0.svg` (ch06), via `mathutils.scale_non_uniform`.

# %%
from __future__ import annotations

from _transform_sequence import (  # noqa: F401
    BACKGROUND,
    PADDLE1,
    PADDLE1_COLOR,
    PendingFigure,
    identity,
    transform_frame,
)

fig: PendingFigure = transform_frame(
    geometry=PADDLE1,
    color=PADDLE1_COLOR,
    frame_transform=identity(),
    paddle_transform=identity(),
    step=1,
    title_base="Scale Relative to World Space",
)

# %%
fig
