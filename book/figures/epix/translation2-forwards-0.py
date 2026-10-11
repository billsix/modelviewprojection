# %% [markdown]
# # translation2-forwards-0 — paddle2 in its modelspace (step 1)
#
# ePiX replacement for `_static/translation2-forwards-0.svg` (ch06), via `mathutils`.

# %%
from __future__ import annotations

from _transform_sequence import (  # noqa: F401
    BACKGROUND,
    PADDLE2,
    PADDLE2_COLOR,
    PendingFigure,
    identity,
    transform_frame,
)

fig: PendingFigure = transform_frame(
    geometry=PADDLE2,
    color=PADDLE2_COLOR,
    frame_transform=identity(),
    paddle_transform=identity(),
    step=1,
    title_base="Translation",
)

# %%
fig
