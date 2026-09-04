#!/usr/bin/env python3
# Copyright (c) 2026 William Emerison Six
#
# Deterministically capture frame N of a pgzero_gl game to a PNG, for the
# frame-identity proof that the inline (step 1) changed no behavior.
#
# It seeds `random` BEFORE the game runs (games don't self-seed, so both the
# original and the inlined copy then take the identical RNG path), and
# monkeypatches glfw.swap_buffers to glReadPixels the back buffer on the Nth
# frame -- a capture tied to the frame COUNT, not wall-clock, so timing jitter
# can't cause a false mismatch. runpy runs the game as __main__ so its
# `if __name__ == "__main__": main()` fires and its asset_root (from __file__)
# resolves.
#
# Usage (headless, PGZERO_MAX_FRAMES must be >= the capture frame):
#   CAPTURE_FRAME=180 CAPTURE_OUT=/tmp/x.png DISPLAY=:99 \
#   PGZERO_MAX_FRAMES=180 python capture_frame.py <game.py>

import os
import random
import runpy
import sys

random.seed(0)

import glfw  # noqa: E402  (must follow the seed; game shares this module)
import OpenGL.GL as GL  # noqa: E402
from PIL import Image  # noqa: E402

_N = int(os.environ["CAPTURE_FRAME"])
_OUT = os.environ["CAPTURE_OUT"]
_count = [0]
_orig_swap = glfw.swap_buffers


def _swap(win: object) -> None:
    _count[0] += 1
    if _count[0] == _N:
        w, h = glfw.get_framebuffer_size(win)
        data = GL.glReadPixels(0, 0, w, h, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE)
        # GL's origin is bottom-left; flip to a normal top-left image.
        Image.frombytes("RGBA", (w, h), bytes(data)).transpose(
            Image.FLIP_TOP_BOTTOM
        ).save(_OUT)
    _orig_swap(win)


glfw.swap_buffers = _swap  # type: ignore[assignment]
runpy.run_path(sys.argv[1], run_name="__main__")
