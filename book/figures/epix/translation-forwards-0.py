# %% [markdown]
# # translation-forwards-0 — paddle1 in its modelspace (step 1)
#
# ePiX replacement for `_static/translation-forwards-0.svg` (ch06). Positions come
# from `mathutils.translate` — the taught code.

# %%
from __future__ import annotations

from _transform_sequence import (  # noqa: F401  (BACKGROUND read by the renderer)
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
    title_base="Translation",
)

# %%
fig
