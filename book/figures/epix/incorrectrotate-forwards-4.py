# %% [markdown]
# # incorrectrotate-forwards-4 — rotate 65 about the origin, grid turned (step 3)
#
# ePiX replacement for `_static/incorrectrotate-forwards-4.svg` (ch06). The paddle is
# rotated about the WRONG centre (the world origin), swinging it away — the mistake the
# figure teaches. All positions come from `mathutils` (translate / rotate / compose).

# %%
from __future__ import annotations

import math

from _transform_sequence import (  # noqa: F401
    BACKGROUND,
    E1,
    E2,
    PADDLE1,
    PADDLE1_COLOR,
    PendingFigure,
    compose,
    identity,
    rotate,
    transform_frame,
    translate,
)

t = translate(b=-9 * E1 + 2 * E2)
r = rotate(math.radians(65))
rt = compose([r, t])  # apply t first, then r (rotation about the world origin)
fig: PendingFigure = transform_frame(
    geometry=PADDLE1,
    color=PADDLE1_COLOR,
    frame_transform=r,
    paddle_transform=rt,
    step=3,
    title_base="Incorrect Rotation, Relative to World Space",
    bound=12.0,
)

# %%
fig
