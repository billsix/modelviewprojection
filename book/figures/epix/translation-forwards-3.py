# %% [markdown]
# # translation-forwards-3 — paddle at its world location, axes home (step 2)
#
# ePiX replacement for `_static/translation-forwards-3.svg` (ch06). The paddle is at its
# world position (via `mathutils.translate`); the modelspace marker is back at the origin.

# %%
from __future__ import annotations

from _transform_sequence import (  # noqa: F401  (BACKGROUND read by the renderer)
    BACKGROUND,
    E1,
    E2,
    PADDLE1,
    PADDLE1_COLOR,
    PendingFigure,
    identity,
    transform_frame,
    translate,
)

to_world = translate(b=-9 * E1 + 2 * E2)
fig: PendingFigure = transform_frame(
    geometry=PADDLE1,
    color=PADDLE1_COLOR,
    frame_transform=identity(),
    paddle_transform=to_world,
    step=2,
    title_base="Translation",
)

# %%
fig
