# %% [markdown]
# # rotate-sloppy-forwards-3 — paddle slid to (-9,2) (step 2)
#
# ePiX replacement for `_static/rotate-sloppy-forwards-3.svg` (ch06). The correct
# result (rotate the paddle about its own centre) reached the sloppy way: translate out,
# rotate, translate back. All positions come from `mathutils` (translate / rotate / compose).

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
tb = translate(b=9 * E1 + -2 * E2)
r = rotate(math.radians(45))
fig: PendingFigure = transform_frame(
    geometry=PADDLE1,
    color=PADDLE1_COLOR,
    frame_transform=identity(),
    paddle_transform=t,
    step=2,
    title_base="Correct but Sloppy Rotation, Relative to World Space",
    bound=12.0,
)

# %%
fig
