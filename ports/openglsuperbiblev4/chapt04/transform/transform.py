# transform.py
# Demonstrates manual matrix math: builds a rotation matrix on the CPU
# (m3dRotationMatrix44) and transforms each torus vertex by hand
# (m3dTransformVector3) before sending to glVertex3fv. The companion
# demo (transformgl.py) uses glLoadMatrixf to let OpenGL do the work.
# OpenGL SuperBible, Chapter 4
# Python port of Transform.cpp by Richard S. Wright Jr.

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
    """Replacement for m3dRotationMatrix44(angle, x, y, z). Builds a 4x4
    column-major rotation matrix about an arbitrary unit axis (x, y, z)
    by `angle_rad` radians. Uses Rodrigues' formula expanded into the
    standard 4x4 form."""
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    one_c = 1.0 - c

    mag = math.sqrt(x * x + y * y + z * z)
    if mag != 0.0:
        x, y, z = x / mag, y / mag, z / mag

    m = np.array(
        [
            # column 0
            (one_c * x * x) + c,
            (one_c * x * y) + (z * s),
            (one_c * x * z) - (y * s),
            0.0,
            # column 1
            (one_c * x * y) - (z * s),
            (one_c * y * y) + c,
            (one_c * y * z) + (x * s),
            0.0,
            # column 2
            (one_c * x * z) + (y * s),
            (one_c * y * z) - (x * s),
            (one_c * z * z) + c,
            0.0,
            # column 3
            0.0, 0.0, 0.0, 1.0,
        ],
        dtype=np.float32,
    )
    return m


def transform_vector3(
    v: "tuple[float, float, float]", m: "np.ndarray"
) -> "tuple[float, float, float]":
    """Replacement for m3dTransformVector3 -- multiply a 3-vector
    (treating w=1) by a 4x4 column-major matrix. Returns a 3-tuple."""
    out_x = m[0] * v[0] + m[4] * v[1] + m[8] * v[2] + m[12]
    out_y = m[1] * v[0] + m[5] * v[1] + m[9] * v[2] + m[13]
    out_z = m[2] * v[0] + m[6] * v[1] + m[10] * v[2] + m[14]
    return (out_x, out_y, out_z)


def draw_torus(m_transform: "np.ndarray") -> None:
    """Draw a torus by hand-transforming each vertex through m_transform
    on the CPU before sending to glVertex3fv."""
    major_radius = 0.35
    minor_radius = 0.15
    num_major = 40
    num_minor = 20
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

            GL.glVertex3fv(transform_vector3((x0 * r, y0 * r, z), m_transform))
            GL.glVertex3fv(transform_vector3((x1 * r, y1 * r, z), m_transform))
        GL.glEnd()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    transformation_matrix = rotation_matrix_about_axis(
        math.radians(y_rot), 0.0, 1.0, 0.0
    )
    # Translation in the last column of a column-major 4x4
    transformation_matrix[12] = 0.0
    transformation_matrix[13] = 0.0
    transformation_matrix[14] = -2.5

    draw_torus(transformation_matrix)


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
        800, 600, "Manual Transformations Demo", None, None
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
