#!/usr/bin/env python
# Copyright (c) 2026 William Emerison Six
#
# Prove that a GL script in this repo actually rasterizes something -- a demo,
# a visualization, or an assignment. Run it after editing one of those files,
# via tools/verify_render.sh, which supplies the container and the X display.
# Promoted from tasks/adhoc/assignments-review/ on 2026-09-09, where it gated
# the assignment re-syncs -- record in
# tasks/archive/2026/09/09/assignments-1-and-2-review.md
#
# Why this exists rather than a screenshot: `import -window root` against the
# sandbox's Xvfb captures BLACK for these programs, because nothing maps their
# GLFW window onto the root. So instead of photographing the screen, this reads
# the back buffer with glReadPixels just before each swap -- which is also
# stronger evidence, since it cannot be fooled by a window manager.
#
# A demo here is a flat script that opens a window and runs its own loop at
# module level, so there is nothing to import and call. It is driven with
# runpy, and two glfw functions are wrapped:
#
#   * swap_buffers        -- read the back buffer, then swap as usual.
#   * window_should_close -- true after N frames, so the script's own loop
#                            ends on its own, with no timeout and no nonzero
#                            exit code to interpret.
#
# --hold names keys to hold down for the whole run, so a keyboard-driven
# behaviour (a camera move) can be exercised with nobody at the keyboard.

"""Render gate for a GL script: drive N frames, report what was drawn.

    python render_probe.py <script.py> [frames] [--png OUT] [--hold KEY,KEY]
                           [--allow-blank]

``--hold`` takes glfw key names without the ``KEY_`` prefix: ``RIGHT``,
``LEFT_SHIFT``, ``UP``.  ``--allow-blank`` accepts a single-colour frame, which
is the CORRECT state for an assignment whose exercise hole is what makes the
scene appear (``assignments/assignment2-screenspace.py`` draws nothing until a
student writes its NDC-to-screen mapping).
"""

import argparse
import pathlib
import runpy
import sys

import glfw
import OpenGL.GL as GL
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("script")
parser.add_argument("frames", nargs="?", type=int, default=10)
parser.add_argument("--png", default=None, help="write frame 0 here")
parser.add_argument("--hold", default="", help="comma-separated glfw keys")
parser.add_argument(
    "--allow-blank",
    action="store_true",
    help="a single-colour frame is a pass (unsolved-assignment case)",
)
args = parser.parse_args()

held: set[int] = {
    getattr(glfw, f"KEY_{name.strip().upper()}")
    for name in args.hold.split(",")
    if name.strip()
}
if held:
    glfw.get_key = lambda window, key: (
        glfw.PRESS if key in held else glfw.RELEASE
    )
# a controller plugged into the host would otherwise perturb a scripted run
glfw.get_joystick_axes = lambda joy: []

_real_swap = glfw.swap_buffers
state: dict = {"frames": 0, "image": None}


def _probing_swap(window):
    state["frames"] += 1
    if state["frames"] == 1:
        width, height = glfw.get_framebuffer_size(window)
        raw = GL.glReadPixels(
            0, 0, width, height, GL.GL_RGB, GL.GL_UNSIGNED_BYTE
        )
        state["image"] = Image.frombytes(
            "RGB", (width, height), bytes(raw)
        ).transpose(Image.FLIP_TOP_BOTTOM)
    return _real_swap(window)


glfw.swap_buffers = _probing_swap
glfw.window_should_close = lambda window: state["frames"] >= args.frames

globals_after: dict = runpy.run_path(args.script, run_name="__main__")

print(f"{args.script}: {state['frames']} frame(s)")

image: Image.Image | None = state["image"]
if image is None:
    print("FAIL: no frame was ever swapped -- nothing rendered")
    sys.exit(1)

colors = sorted(image.getcolors(maxcolors=1 << 20) or [], reverse=True)
print(f"  {image.size[0]}x{image.size[1]}, {len(colors)} distinct colours")
for count, color in colors[:6]:
    print(f"    {color}  {count}")

if args.png:
    pathlib.Path(args.png).parent.mkdir(parents=True, exist_ok=True)
    image.save(args.png)
    print(f"  wrote {args.png}")

camera = globals_after.get("camera")
if camera is not None:
    # 2D demos carry a g2 camera with no z and no rotation, so report what this
    # one actually has rather than assuming demo18's shape
    coords = ", ".join(f"{float(c):.2f}" for c in camera.position_ws)
    angles = " ".join(
        f"{name}={getattr(camera, name):.4f}"
        for name in ("rot_y", "rot_x")
        if hasattr(camera, name)
    )
    print(f"  camera: ({coords}) {angles}".rstrip())

# A scene that drew nothing is one flat clear colour; the paddle demos draw at
# least their two paddles over the background.
if len(colors) < 2 and not args.allow_blank:
    print(
        "FAIL: frame is a single flat colour -- the scene drew nothing.\n"
        "      (If this is an assignment whose exercise hole is what makes\n"
        "      the scene appear, that is correct: pass --allow-blank.)"
    )
    sys.exit(1)

print("PASS")
