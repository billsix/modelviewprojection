# %% [markdown]
# # translation2-forwards-2 — paddle2 frame + paddle slid to world (9, -4) (step 2)
#
# ePiX replacement for `_static/translation2-forwards-2.svg` (ch06), via `mathutils`.

# %%
from __future__ import annotations

from _transform_sequence import (  # noqa: F401
    BACKGROUND,
    E1,
    E2,
    PADDLE2,
    PADDLE2_COLOR,
    PendingFigure,
    transform_frame,
    translate,
)

to_world = translate(b=9 * E1 + -4 * E2)
fig: PendingFigure = transform_frame(
    geometry=PADDLE2,
    color=PADDLE2_COLOR,
    frame_transform=to_world,
    paddle_transform=to_world,
    step=2,
    title_base="Translation",
)

# %%
fig
