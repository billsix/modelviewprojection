# sphereworld.py
# A first immersive 3D scene: a gridded ground, 50 randomly-placed
# spheres, and a torus orbited by another sphere -- viewed through a
# camera the user can move with arrow keys.
#
# The C++ original used GLFrame for both the camera and the per-actor
# placements. We unfold those into simple state (position+yaw for the
# camera, position only for each sphere) since the demo doesn't actually
# use any of GLFrame's other capabilities.
#
# OpenGL SuperBible, Chapter 4
# Python port of SphereWorld.cpp by Richard S. Wright Jr.

import math
import os
import random
import sys
import time

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _primitives  # noqa: E402



NUM_SPHERES = 50

# 50 sphere positions, generated once at startup
sphere_positions = []

# Camera state: position + yaw (rotation about Y). The C++ GLFrame
# tracks (origin, forward, up); for this demo only origin + yaw is used.
camera_x: float = 0.0
camera_y: float = 0.0
camera_z: float = 0.0
camera_yaw: float = 0.0

y_rot = 0.0  # animation angle for the orbiting sphere/torus group


# The 50 field spheres, the orbiting sphere, and the torus are identical
# every frame -- tessellate once at import, replay the stored vertices.
# This demo renders in wireframe with lighting off (see setup_rc), so the
# torus emits no normals, matching the original hand-written generator.
SPHERE = _primitives.build_sphere(0.1, 13, 26)
TORUS = _primitives.build_torus(0.35, 0.15, 40, 20)


def apply_camera_transform() -> None:
    """Equivalent to GLFrame::ApplyCameraTransform for a camera that has
    only been rotated about Y. Rotate world by -yaw, then translate by
    -position."""
    GL.glRotatef(-math.degrees(camera_yaw), 0.0, 1.0, 0.0)
    GL.glTranslatef(-camera_x, -camera_y, -camera_z)


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.50, 1.0)
    GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)

    random.seed(0)
    for _ in range(NUM_SPHERES):
        # Place between -20 and 20 in 0.1 increments
        sx = ((random.randint(0, 399) - 200) * 0.1)
        sz = ((random.randint(0, 399) - 200) * 0.1)
        sphere_positions.append((sx, 0.0, sz))


def draw_ground() -> None:
    extent = 20.0
    step = 1.0
    y = -0.4

    GL.glBegin(GL.GL_LINES)
    line = -extent
    while line <= extent:
        GL.glVertex3f(line, y, extent)
        GL.glVertex3f(line, y, -extent)
        GL.glVertex3f(extent, y, line)
        GL.glVertex3f(-extent, y, line)
        line += step
    GL.glEnd()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    GL.glPushMatrix()
    apply_camera_transform()

    draw_ground()

    # The 50 random spheres
    for sx, sy, sz in sphere_positions:
        GL.glPushMatrix()
        GL.glTranslatef(sx, sy, sz)
        _primitives.draw_mesh(SPHERE)
        GL.glPopMatrix()

    # Torus orbited by a small sphere, both in front of the camera
    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, -2.5)

    GL.glPushMatrix()
    GL.glRotatef(-y_rot * 2.0, 0.0, 1.0, 0.0)
    GL.glTranslatef(1.0, 0.0, 0.0)
    _primitives.draw_mesh(SPHERE)
    GL.glPopMatrix()

    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    _primitives.draw_mesh(TORUS, normals=False)
    GL.glPopMatrix()

    GL.glPopMatrix()


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    f_aspect = float(w) / float(h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(35.0, f_aspect, 1.0, 50.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


# Movement / rotation rates while a key is held; multiplied by frame
# delta in handle_camera_keys so behavior is independent of framerate.
MOVE_UNITS_PER_SEC: float = 3.0
YAW_RAD_PER_SEC: float = 1.5
TORUS_DEG_PER_SEC: float = 30.0


def handle_camera_keys(window, dt: float) -> None:
    """Replaces GLFrame::MoveForward / RotateLocalY for arrow keys."""
    global camera_x, camera_z, camera_yaw
    move = MOVE_UNITS_PER_SEC * dt
    yaw = YAW_RAD_PER_SEC * dt
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        # Forward in world coords for a camera rotated about +Y by yaw:
        # the default forward (0,0,-1) becomes (-sin yaw, 0, -cos yaw)
        # after the standard right-handed Y-rotation.
        camera_x += -move * math.sin(camera_yaw)
        camera_z += -move * math.cos(camera_yaw)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera_x -= -move * math.sin(camera_yaw)
        camera_z -= -move * math.cos(camera_yaw)
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera_yaw += yaw
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera_yaw -= yaw


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def main() -> None:
    global y_rot

    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(
        800, 600, "OpenGL SphereWorld Demo", None, None
    )
    if not window:
        glfw.terminate()
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.swap_interval(1)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    last_frame = time.monotonic()

    while not glfw.window_should_close(window):
        now = time.monotonic()
        dt = now - last_frame
        last_frame = now

        glfw.poll_events()
        handle_camera_keys(window, dt)
        y_rot = (y_rot + TORUS_DEG_PER_SEC * dt) % 360.0
        render_scene()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
