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
from imgui_bundle import imgui

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


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


def draw_solid_sphere(radius: float, slices: int, stacks: int) -> None:
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        sin0, cos0 = math.sin(lat0), math.cos(lat0)
        sin1, cos1 = math.sin(lat1), math.cos(lat1)
        GL.glBegin(GL.GL_QUAD_STRIP)
        for j in range(slices + 1):
            lng = 2.0 * math.pi * float(j) / slices
            cl, sl = math.cos(lng), math.sin(lng)
            GL.glNormal3f(cl * cos0, sl * cos0, sin0)
            GL.glVertex3f(radius * cl * cos0, radius * sl * cos0, radius * sin0)
            GL.glNormal3f(cl * cos1, sl * cos1, sin1)
            GL.glVertex3f(radius * cl * cos1, radius * sl * cos1, radius * sin1)
        GL.glEnd()


def draw_torus(major_radius: float, minor_radius: float, num_major: int, num_minor: int) -> None:
    major_step = 2.0 * math.pi / num_major
    minor_step = 2.0 * math.pi / num_minor

    for i in range(num_major):
        a0 = i * major_step
        a1 = a0 + major_step
        x0 = math.cos(a0)
        y0 = math.sin(a0)
        x1 = math.cos(a1)
        y1 = math.sin(a1)

        GL.glBegin(GL.GL_TRIANGLE_STRIP)
        for j in range(num_minor + 1):
            b = j * minor_step
            c = math.cos(b)
            r = minor_radius * c + major_radius
            z = minor_radius * math.sin(b)
            GL.glVertex3f(x0 * r, y0 * r, z)
            GL.glVertex3f(x1 * r, y1 * r, z)
        GL.glEnd()


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
    global y_rot
    y_rot += 0.5

    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    GL.glPushMatrix()
    apply_camera_transform()

    draw_ground()

    # The 50 random spheres
    for sx, sy, sz in sphere_positions:
        GL.glPushMatrix()
        GL.glTranslatef(sx, sy, sz)
        draw_solid_sphere(0.1, 13, 26)
        GL.glPopMatrix()

    # Torus orbited by a small sphere, both in front of the camera
    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, -2.5)

    GL.glPushMatrix()
    GL.glRotatef(-y_rot * 2.0, 0.0, 1.0, 0.0)
    GL.glTranslatef(1.0, 0.0, 0.0)
    draw_solid_sphere(0.1, 13, 26)
    GL.glPopMatrix()

    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    draw_torus(0.35, 0.15, 40, 20)
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


def handle_camera_keys(window) -> None:
    """Replaces GLFrame::MoveForward / RotateLocalY for arrow keys."""
    global camera_x, camera_z, camera_yaw
    move_step = 0.1
    rot_step = 0.1
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        # forward in world coords after rotating by yaw about Y. Default
        # forward is (0,0,-1); after glRotatef(yaw_deg, 0,1,0) on the
        # column vector this becomes (sin(yaw), 0, -cos(yaw)).
        camera_x += move_step * math.sin(camera_yaw)
        camera_z += -move_step * math.cos(camera_yaw)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera_x -= move_step * math.sin(camera_yaw)
        camera_z -= -move_step * math.cos(camera_yaw)
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera_yaw += rot_step
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera_yaw -= rot_step


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


TICK_INTERVAL: float = 33.0 / 1000.0


def main() -> None:
    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    
    window_width, window_height = _common.resolve_default_window_size()

    window = glfw.create_window(
        window_width, window_height, "OpenGL SphereWorld Demo", None, None
    )
    if not window:
        glfw.terminate()
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    impl = _common.init_imgui(window)
    win_state = _common.WindowState()

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    last_tick = time.monotonic()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        handle_camera_keys(window)

        now = time.monotonic()
        if now - last_tick >= TICK_INTERVAL:
            render_scene()
            last_tick = now

        
        imgui.new_frame()
        _common.draw_menubar(window, win_state)
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()

    glfw.terminate()


if __name__ == "__main__":
    main()
