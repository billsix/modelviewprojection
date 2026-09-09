# Copyright (c) 2026 William Emerison Six
#
# Headless render gate for a GL script in this repo (a demo, or an assignment).
#
# A demo here is a flat script that opens a window and runs its own loop at
# module level, so there is nothing to import and call -- which is why this
# drives it with runpy and wraps glfw instead.  Two things are faked:
#
#   * glfw.swap_buffers  -- wrapped so the BACK BUFFER is read back with
#     glReadPixels just before each swap.  That is the evidence: it proves the
#     script rasterized geometry, and unlike an X screenshot it does not depend
#     on a window manager mapping the window onto the root.  (`import -window
#     root` against the sandbox's Xvfb captures black here, which is why this
#     exists.)
#   * glfw.window_should_close -- made true after N frames, so the script's own
#     `while not glfw.window_should_close(window)` loop terminates on its own
#     rather than needing a timeout and a nonzero exit code.
#
# Optionally holds a set of keys down for the whole run, so a keyboard-driven
# behaviour (a camera move) can be exercised without a human at the keyboard.
#
# Run it through ./verify.sh, which supplies the container and the X display.
#
#   python render_probe.py <script.py> [frames] [--png OUT] [--hold KEY,KEY]
#   --hold names are glfw key constants without the KEY_ prefix: RIGHT,
#   LEFT_SHIFT, UP, ...

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

# A scene that drew nothing is one flat clear colour; the paddle demos draw at
# least the two paddles over the background.
if len(colors) < 2:
    print("FAIL: frame is a single flat colour -- the scene drew nothing")
    sys.exit(1)

camera = globals_after.get("camera")
if camera is not None:
    position = camera.position_ws
    print(
        f"  camera: ({float(position.x):.2f}, {float(position.y):.2f}, "
        f"{float(position.z):.2f}) rot_y={camera.rot_y:.4f} "
        f"rot_x={camera.rot_x:.4f}"
    )

print("PASS")
