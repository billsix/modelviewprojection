# fogged.py
# Sphereworld with linear fog. Same scene as chapt05/sphereworld plus
# fog parameters in setup_rc.
# OpenGL SuperBible, Chapter 6
# Python port of Fogged.cpp by Richard S. Wright Jr.

import math
import os
import random
import sys
import time

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

from modelviewprojection.mathutils import Vector3, plane_equation

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _primitives  # noqa: E402
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit control button

NUM_SPHERES = 30
sphere_positions = []
camera_x: float = 0.0
camera_y: float = 0.0
camera_z: float = 0.0
camera_yaw: float = 0.0
f_light_pos = (-100.0, 100.0, 50.0, 1.0)
f_no_light = (0.0, 0.0, 0.0, 0.0)
f_low_light = (0.25, 0.25, 0.25, 1.0)
f_bright_light = (1.0, 1.0, 1.0, 1.0)
shadow_mat = None
y_rot: float = 0.0
fog_enabled: bool = True


def make_planar_shadow_matrix(
    plane_normal: Vector3,
    plane_d: float,
    light_pos_4: "tuple[float, float, float, float]",
) -> "np.ndarray":
    a, b, c = plane_normal.coeff_e_1, plane_normal.coeff_e_2, plane_normal.coeff_e_3
    d = plane_d
    dx, dy, dz = -light_pos_4[0], -light_pos_4[1], -light_pos_4[2]
    # CCW plane_equation can land w<0; OpenGL clips before perspective
    # divide and the shadow disappears. Negate to keep w positive.
    # See plans/notes-planar-shadow-w-clipping.md.
    sign = 1.0 if (a * dx + b * dy + c * dz) > 0.0 else -1.0
    return np.array(
        [
            sign * (b * dy + c * dz), sign * -a * dy, sign * -a * dz, 0.0,
            sign * -b * dx, sign * (a * dx + c * dz), sign * -b * dz, 0.0,
            sign * -c * dx, sign * -c * dy, sign * (a * dx + b * dy), 0.0,
            sign * -d * dx, sign * -d * dy, sign * -d * dz,
            sign * (a * dx + b * dy + c * dz),
        ],
        dtype=np.float32,
    )


# Geometry is identical every frame, so build the vertex bands once at import
# and replay them in draw_inhabitants / render_scene instead of re-running the
# sin/cos loops on every draw. 30 spheres + a torus, each drawn twice per frame
# (the shadow pass), were the bulk of the per-frame CPU cost.
SPHERE_BIG = _primitives.build_sphere(0.3, 17, 9)
SPHERE_SMALL = _primitives.build_sphere(0.1, 17, 9)
TORUS = _primitives.build_torus(0.35, 0.15, 61, 37)
GROUND = _primitives.build_ground(20.0, 1.0, -0.4)


def apply_camera_transform() -> None:
    GL.glRotatef(-math.degrees(camera_yaw), 0.0, 1.0, 0.0)
    GL.glTranslatef(-camera_x, -camera_y, -camera_z)


def draw_inhabitants(n_shadow: int) -> None:
    if n_shadow != 0:
        GL.glColor3f(0.0, 0.0, 0.0)

    if n_shadow == 0:
        GL.glColor3f(0.0, 1.0, 0.0)

    for sx, sy, sz in sphere_positions:
        GL.glPushMatrix()
        GL.glTranslatef(sx, sy, sz)
        _primitives.draw_mesh(SPHERE_BIG)
        GL.glPopMatrix()

    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.1, -2.5)
    if n_shadow == 0:
        GL.glColor3f(0.0, 0.0, 1.0)

    GL.glPushMatrix()
    GL.glRotatef(-y_rot * 2.0, 0.0, 1.0, 0.0)
    GL.glTranslatef(1.0, 0.0, 0.0)
    _primitives.draw_mesh(SPHERE_SMALL)
    GL.glPopMatrix()

    if n_shadow == 0:
        GL.glColor3f(1.0, 0.0, 0.0)
        GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, f_bright_light)

    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    _primitives.draw_mesh(TORUS)
    GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, f_no_light)
    GL.glPopMatrix()


def render_scene() -> None:
    if fog_enabled:
        GL.glEnable(GL.GL_FOG)
    else:
        GL.glDisable(GL.GL_FOG)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glPushMatrix()
    apply_camera_transform()
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, f_light_pos)
    GL.glColor3f(0.60, 0.40, 0.10)
    _primitives.draw_mesh(GROUND)

    GL.glDisable(GL.GL_DEPTH_TEST)
    GL.glDisable(GL.GL_LIGHTING)
    GL.glPushMatrix()
    GL.glMultMatrixf(shadow_mat)
    draw_inhabitants(1)
    GL.glPopMatrix()
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_DEPTH_TEST)

    draw_inhabitants(0)
    GL.glPopMatrix()


# Fixed per-frame steps for the Controls buttons. The keyboard walk scales by
# dt (see handle_camera_keys); the buttons apply a constant nudge each held
# frame instead, which keeps the mutator helpers free of timing state.
BTN_MOVE_STEP: float = 0.05
BTN_YAW_STEP: float = 0.025


def _walk(direction: float) -> None:
    """Move forward (+1) or back (-1) along the current heading."""
    global camera_x, camera_z
    step = direction * BTN_MOVE_STEP
    camera_x += -step * math.sin(camera_yaw)
    camera_z += -step * math.cos(camera_yaw)


def _turn(d: float) -> None:
    global camera_yaw
    camera_yaw += d


def _toggle_fog() -> None:
    global fog_enabled
    fog_enabled = not fog_enabled


def imgui_menubar() -> None:
    # All controls live in the top menubar. Fog is a checkable item; movement
    # items show their key (hold the key for continuous walking).
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action("Quit", "Esc",
                            lambda: glfw.set_window_should_close(_window, True))
        imgui.end_menu()
    if imgui.begin_menu("Options", True):
        clicked, _ = imgui.menu_item("Fog", "", fog_enabled, True)
        if clicked:
            _toggle_fog()
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _common.menu_action("Forward", "Up", lambda: _walk(1.0))
        _common.menu_action("Back", "Down", lambda: _walk(-1.0))
        _common.menu_action("Turn Left", "Left", lambda: _turn(BTN_YAW_STEP))
        _common.menu_action("Turn Right", "Right",
                            lambda: _turn(-BTN_YAW_STEP))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def setup_rc() -> None:
    global shadow_mat
    GL.glClearColor(*f_low_light)

    # Fog -- the difference between this demo and chapt05/sphereworld
    GL.glEnable(GL.GL_FOG)
    GL.glFogfv(GL.GL_FOG_COLOR, f_low_light)
    GL.glFogf(GL.GL_FOG_START, 5.0)
    GL.glFogf(GL.GL_FOG_END, 30.0)
    GL.glFogi(GL.GL_FOG_MODE, GL.GL_LINEAR)

    GL.glCullFace(GL.GL_BACK)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_DEPTH_TEST)

    GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, f_no_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, f_low_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, f_bright_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, f_bright_light)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_LIGHT0)

    p1, p2, p3 = (Vector3(0.0, -0.4, 0.0), Vector3(10.0, -0.4, 0.0),
                  Vector3(5.0, -0.4, -5.0))
    plane_normal, plane_d = plane_equation(p1, p2, p3)
    shadow_mat = make_planar_shadow_matrix(plane_normal, plane_d, f_light_pos)

    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)

    random.seed(0)
    for _ in range(NUM_SPHERES):
        sx = (random.randint(0, 399) - 200) * 0.1
        sz = (random.randint(0, 399) - 200) * 0.1
        sphere_positions.append((sx, 0.0, sz))


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


MOVE_UNITS_PER_SEC: float = 3.0
YAW_RAD_PER_SEC: float = 1.5
TORUS_DEG_PER_SEC: float = 30.0


def handle_camera_keys(window, dt: float) -> None:
    global camera_x, camera_z, camera_yaw
    move = MOVE_UNITS_PER_SEC * dt
    yaw = YAW_RAD_PER_SEC * dt
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
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
    global y_rot, _window

    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(
        800, 600, "OpenGL SphereWorld Demo + Fog", None, None
    )
    if not window:
        glfw.terminate()
        sys.exit(1)

    _window = window
    glfw.make_context_current(window)
    glfw.swap_interval(1)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw key
    # callback that doesn't chain, so navigation/Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    last_frame = time.monotonic()

    while not glfw.window_should_close(window):
        now = time.monotonic()
        dt = now - last_frame
        last_frame = now

        glfw.poll_events()
        impl.process_inputs()
        handle_camera_keys(window, dt)
        y_rot = (y_rot + TORUS_DEG_PER_SEC * dt) % 360.0
        render_scene()
        imgui.new_frame()
        imgui_menubar()
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
