"""Shared per-frame keyboard polling for the walk-around camera.

Used by demos 20, 21, 22, 22a, 23, 24, and 19e -- the 3D demos that walk
the camera around the scene with arrow keys + Page Up/Down. Demo 19
introduces this idiom inline (teach-once), and from demo 20 onward the
demos import this helper rather than re-defining the block.

Demos 17 and 18 keep their own input handling because they teach the
InvertibleFunction abstraction. Demos 19a-d are orbit cameras and don't
use this helper.
"""

import math

import glfw


def walk_around_camera(window, camera, move_step: float) -> None:
    """Poll the standard walk-around camera keys and mutate *camera*.

    LEFT/RIGHT yaw, PAGE_UP/PAGE_DOWN pitch, UP/DOWN walk forward/back
    along the camera's heading. *camera* must expose ``x``, ``z``,
    ``rot_y``, and ``rot_x`` floats; *move_step* sets the per-press
    forward distance (yaw and pitch are fixed at 0.03 radians).
    """
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.rot_y -= 0.03
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.rot_y += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_UP) == glfw.PRESS:
        camera.rot_x += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_DOWN) == glfw.PRESS:
        camera.rot_x -= 0.03
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera.x -= move_step * math.sin(camera.rot_y)
        camera.z -= move_step * math.cos(camera.rot_y)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.x += move_step * math.sin(camera.rot_y)
        camera.z += move_step * math.cos(camera.rot_y)
