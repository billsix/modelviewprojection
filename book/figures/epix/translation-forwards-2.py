# %% [markdown]
# # translation-forwards-2 — modelspace frame + paddle slid to world (-9, 2) (step 2)
#
# ePiX replacement for `_static/translation-forwards-2.svg` (ch06). The moved frame and
# the paddle positions are both computed by `mathutils.translate` — the taught code.

# %%
from __future__ import annotations

from _transform_sequence import (  # noqa: F401  (BACKGROUND read by the renderer)
    BACKGROUND,
    E1,
    E2,
    PADDLE1,
    PADDLE1_COLOR,
    PendingFigure,
    transform_frame,
    translate,
)

to_world = translate(b=-9 * E1 + 2 * E2)
fig: PendingFigure = transform_frame(
    geometry=PADDLE1,
    color=PADDLE1_COLOR,
    frame_transform=to_world,
    paddle_transform=to_world,
    step=2,
    title_base="Translation",
)

# %%
fig
