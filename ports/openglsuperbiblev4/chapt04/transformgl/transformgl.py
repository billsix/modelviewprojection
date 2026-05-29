# transformgl.py
# Companion to transform.py: builds the same rotation matrix on the CPU
# but uses glLoadMatrixf to let OpenGL transform vertices on the GPU,
# rather than transforming each vertex by hand before sending it.
# Reads cleaner and runs faster -- the point of the demo.
# OpenGL SuperBible, Chapter 4
# Python port of Transformgl.c by Richard S. Wright Jr.

import math
import os
import sys
import time

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit menu item

y_rot: float = 0.0


def rotation_matrix_about_axis(angle_rad: float, x: float, y: float, z: float) -> "np.ndarray":
    """Same as in transform.py -- 4x4 column-major rotation matrix."""
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    one_c = 1.0 - c

    mag = math.sqrt(x * x + y * y + z * z)
    if mag != 0.0:
        x, y, z = x / mag, y / mag, z / mag

    return np.array(
        [
            (one_c * x * x) + c,
            (one_c * x * y) + (z * s),
            (one_c * x * z) - (y * s),
            0.0,
            (one_c * x * y) - (z * s),
            (one_c * y * y) + c,
            (one_c * y * z) + (x * s),
            0.0,
            (one_c * x * z) + (y * s),
            (one_c * y * z) - (x * s),
            (one_c * z * z) + c,
            0.0,
            0.0, 0.0, 0.0, 1.0,
        ],
        dtype=np.float32,
    )


def draw_torus(major_radius: float, minor_radius: float, num_major: int, num_minor: int) -> None:
    """Replacement for gltDrawTorus -- standard parametric torus."""
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


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    transformation_matrix = rotation_matrix_about_axis(
        math.radians(y_rot), 0.0, 1.0, 0.0
    )
    transformation_matrix[12] = 0.0
    transformation_matrix[13] = 0.0
    transformation_matrix[14] = -2.5

    GL.glLoadMatrixf(transformation_matrix)
    draw_torus(0.35, 0.15, 40, 20)


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.50, 1.0)
    GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)


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


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def imgui_menubar() -> None:
    # All controls in the top menubar. This demo is animation-only, so the
    # only control is File -> Quit (Esc).
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action("Quit", "Esc",
                            lambda: glfw.set_window_should_close(_window, True))
        imgui.end_menu()
    imgui.end_main_menu_bar()


TORUS_DEG_PER_SEC: float = 30.0


def main() -> None:
    global y_rot, _window

    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(
        800, 600, "OpenGL Transformations Demo", None, None
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
    # callback that doesn't chain, so Esc must be registered last.
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
