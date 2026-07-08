# shadow.py
# Demonstrates planar shadows: the lit jet drops a darkened copy of
# itself onto a green ground plane via a shadow projection matrix.
# Uses mathutils.plane_equation to derive the plane, and an inline
# planar-shadow matrix builder (will move to pyMatrixStack with
# Tier-1 task #3).
# OpenGL SuperBible, Chapter 5
# Python port of Shadow.cpp by Richard S. Wright Jr.

import os
import sys
import time

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

from modelviewprojection.mathutils import (
    Vector3,
    find_normal,
    plane_equation,
)

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402
import _primitives  # noqa: E402

_window = None  # set in main(); used by the Quit menu item


x_rot: float = 0.0
y_rot: float = 0.0

ambient_light = (0.3, 0.3, 0.3, 1.0)
diffuse_light = (0.7, 0.7, 0.7, 1.0)
specular = (1.0, 1.0, 1.0, 1.0)
light_pos = (-75.0, 150.0, -50.0, 0.0)
specref = (1.0, 1.0, 1.0, 1.0)

shadow_mat = None  # built in setup_rc -- 4x4 column-major np array

# Yellow light-source marker sphere, redrawn each frame at the light
# position -- tessellate once at import.
SPHERE_LIGHT = _primitives.build_sphere(5.0, 10, 10)


def make_planar_shadow_matrix(
    plane_normal: Vector3,
    plane_d: float,
    light_pos_4: "tuple[float, float, float, float]",
) -> "np.ndarray":
    """4x4 column-major shadow projection matrix. Same formula as
    chapt01/block; will move to pyMatrixStack with Tier-1 task #3.

    The bottom-right entry below is the w of every transformed vertex
    (rows 0-2 of column 3 are 0). With mvp's CCW plane_equation that w
    can land negative, and OpenGL clips negative-w vertices *before*
    perspective divide -- the shadow silently disappears. Negate the
    whole matrix when needed to keep w positive. See
    tasks/archive/2026/05/26/notes-planar-shadow-w-clipping.md."""
    a, b, c = (
        plane_normal.coeff_e_1,
        plane_normal.coeff_e_2,
        plane_normal.coeff_e_3,
    )
    d = plane_d
    dx = -light_pos_4[0]
    dy = -light_pos_4[1]
    dz = -light_pos_4[2]
    sign = 1.0 if (a * dx + b * dy + c * dz) > 0.0 else -1.0
    return np.array(
        [
            sign * (b * dy + c * dz),
            sign * -a * dy,
            sign * -a * dz,
            0.0,
            sign * -b * dx,
            sign * (a * dx + c * dz),
            sign * -b * dz,
            0.0,
            sign * -c * dx,
            sign * -c * dy,
            sign * (a * dx + b * dy),
            0.0,
            sign * -d * dx,
            sign * -d * dy,
            sign * -d * dz,
            sign * (a * dx + b * dy + c * dz),
        ],
        dtype=np.float32,
    )


def _emit_face(p1: Vector3, p2: Vector3, p3: Vector3) -> None:
    n = find_normal(p1, p2, p3)
    GL.glNormal3f(n.coeff_e_1, n.coeff_e_2, n.coeff_e_3)
    GL.glVertex3f(p1.coeff_e_1, p1.coeff_e_2, p1.coeff_e_3)
    GL.glVertex3f(p2.coeff_e_1, p2.coeff_e_2, p2.coeff_e_3)
    GL.glVertex3f(p3.coeff_e_1, p3.coeff_e_2, p3.coeff_e_3)


def draw_jet(n_shadow: int) -> None:
    if n_shadow == 0:
        GL.glColor3ub(128, 128, 128)
    else:
        GL.glColor3ub(0, 0, 0)

    GL.glBegin(GL.GL_TRIANGLES)

    GL.glNormal3f(0.0, -1.0, 0.0)
    GL.glVertex3f(0.0, 0.0, 60.0)
    GL.glVertex3f(-15.0, 0.0, 30.0)
    GL.glVertex3f(15.0, 0.0, 30.0)

    _emit_face(
        Vector3(15.0, 0.0, 30.0),
        Vector3(0.0, 15.0, 30.0),
        Vector3(0.0, 0.0, 60.0),
    )
    _emit_face(
        Vector3(0.0, 0.0, 60.0),
        Vector3(0.0, 15.0, 30.0),
        Vector3(-15.0, 0.0, 30.0),
    )

    _emit_face(
        Vector3(-15.0, 0.0, 30.0),
        Vector3(0.0, 15.0, 30.0),
        Vector3(0.0, 0.0, -56.0),
    )
    _emit_face(
        Vector3(0.0, 0.0, -56.0),
        Vector3(0.0, 15.0, 30.0),
        Vector3(15.0, 0.0, 30.0),
    )

    GL.glNormal3f(0.0, -1.0, 0.0)
    GL.glVertex3f(15.0, 0.0, 30.0)
    GL.glVertex3f(-15.0, 0.0, 30.0)
    GL.glVertex3f(0.0, 0.0, -56.0)

    _emit_face(
        Vector3(0.0, 2.0, 27.0),
        Vector3(-60.0, 2.0, -8.0),
        Vector3(60.0, 2.0, -8.0),
    )
    _emit_face(
        Vector3(60.0, 2.0, -8.0),
        Vector3(0.0, 7.0, -8.0),
        Vector3(0.0, 2.0, 27.0),
    )
    _emit_face(
        Vector3(60.0, 2.0, -8.0),
        Vector3(-60.0, 2.0, -8.0),
        Vector3(0.0, 7.0, -8.0),
    )
    _emit_face(
        Vector3(0.0, 2.0, 27.0),
        Vector3(0.0, 7.0, -8.0),
        Vector3(-60.0, 2.0, -8.0),
    )

    GL.glNormal3f(0.0, -1.0, 0.0)
    GL.glVertex3f(-30.0, -0.50, -57.0)
    GL.glVertex3f(30.0, -0.50, -57.0)
    GL.glVertex3f(0.0, -0.50, -40.0)

    _emit_face(
        Vector3(0.0, -0.5, -40.0),
        Vector3(30.0, -0.5, -57.0),
        Vector3(0.0, 4.0, -57.0),
    )
    _emit_face(
        Vector3(0.0, 4.0, -57.0),
        Vector3(-30.0, -0.5, -57.0),
        Vector3(0.0, -0.5, -40.0),
    )
    _emit_face(
        Vector3(30.0, -0.5, -57.0),
        Vector3(-30.0, -0.5, -57.0),
        Vector3(0.0, 4.0, -57.0),
    )

    _emit_face(
        Vector3(0.0, 0.5, -40.0),
        Vector3(3.0, 0.5, -57.0),
        Vector3(0.0, 25.0, -65.0),
    )
    _emit_face(
        Vector3(0.0, 25.0, -65.0),
        Vector3(-3.0, 0.5, -57.0),
        Vector3(0.0, 0.5, -40.0),
    )
    _emit_face(
        Vector3(3.0, 0.5, -57.0),
        Vector3(-3.0, 0.5, -57.0),
        Vector3(0.0, 25.0, -65.0),
    )

    GL.glEnd()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    # Ground -- darker green at the back, lighter at the front, gives an
    # illusion of depth on a flat quad
    GL.glBegin(GL.GL_QUADS)
    GL.glColor3ub(0, 32, 0)
    GL.glVertex3f(400.0, -150.0, -200.0)
    GL.glVertex3f(-400.0, -150.0, -200.0)
    GL.glColor3ub(0, 255, 0)
    GL.glVertex3f(-400.0, -150.0, 200.0)
    GL.glVertex3f(400.0, -150.0, 200.0)
    GL.glEnd()

    GL.glPushMatrix()

    GL.glEnable(GL.GL_LIGHTING)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    draw_jet(0)
    GL.glPopMatrix()

    # Shadow pass: same jet, projected onto the ground
    GL.glDisable(GL.GL_DEPTH_TEST)
    GL.glDisable(GL.GL_LIGHTING)
    GL.glPushMatrix()
    GL.glMultMatrixf(shadow_mat)
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    draw_jet(1)
    GL.glPopMatrix()

    # Light source visualization (yellow sphere where the light is)
    GL.glPushMatrix()
    GL.glTranslatef(light_pos[0], light_pos[1], light_pos[2])
    GL.glColor3ub(255, 255, 0)
    _primitives.draw_mesh(SPHERE_LIGHT)
    GL.glPopMatrix()

    GL.glEnable(GL.GL_DEPTH_TEST)


def setup_rc() -> None:
    global shadow_mat

    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)

    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, ambient_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, diffuse_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, specular)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glEnable(GL.GL_LIGHT0)

    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, specref)
    GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)

    GL.glClearColor(0.0, 0.0, 1.0, 1.0)

    # Three points on the ground plane
    p1 = Vector3(-30.0, -149.0, -20.0)
    p2 = Vector3(-30.0, -149.0, 20.0)
    p3 = Vector3(40.0, -149.0, 20.0)
    plane_normal, plane_d = plane_equation(p1, p2, p3)
    shadow_mat = make_planar_shadow_matrix(plane_normal, plane_d, light_pos)

    GL.glEnable(GL.GL_NORMALIZE)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    f_aspect = float(w) / float(h)
    GLU.gluPerspective(60.0, f_aspect, 200.0, 500.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GL.glTranslatef(0.0, 0.0, -400.0)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


# Rotation rate while an arrow key is held. Multiplied by frame delta
# so the rotation speed is independent of the render framerate.
ROT_DEG_PER_SEC: float = 90.0


def handle_special_keys(window, dt: float) -> None:
    global x_rot, y_rot
    step = ROT_DEG_PER_SEC * dt
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        x_rot -= step
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        x_rot += step
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        y_rot -= step
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        y_rot += step


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


# Per-click step for the menubar rotate items (the keyboard, held, rotates
# continuously via handle_special_keys; a menu click does one fixed step).
BTN_ROT_STEP: float = 5.0


def _rotate(dx: float, dy: float) -> None:
    global x_rot, y_rot
    x_rot += dx
    y_rot += dy


def imgui_menubar() -> None:
    # All controls in the top menubar. Rotate items run once per click and show
    # their key in the shortcut column; hold the key for continuous rotation.
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action(
            "Quit", "Esc", lambda: glfw.set_window_should_close(_window, True)
        )
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _common.menu_action(
            "Rotate up", "Up", lambda: _rotate(-BTN_ROT_STEP, 0)
        )
        _common.menu_action(
            "Rotate down", "Down", lambda: _rotate(BTN_ROT_STEP, 0)
        )
        _common.menu_action(
            "Rotate left", "Left", lambda: _rotate(0, -BTN_ROT_STEP)
        )
        _common.menu_action(
            "Rotate right", "Right", lambda: _rotate(0, BTN_ROT_STEP)
        )
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    global _window

    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(800, 600, "Shadow", None, None)
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
        handle_special_keys(window, dt)
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
