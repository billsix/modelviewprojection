# GLXBasics.py
# A pair of cartoon eyeballs that track the mouse pointer. The
# original used GLX directly to set up a context (the chapter is
# about Linux/X11 OpenGL contexts). This port uses GLFW since GLX is
# already abstracted away by the time we're in Python.
#
# OpenGL SuperBible, Chapter 21
# Python port of GLXBasics.c by Nick Haemel

import math
import os
import sys

import glfw
import OpenGL.GL as GL
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit menu item

window_width: int = 400
window_height: int = 200
mouse_x: int = 0
mouse_y: int = 0


def draw_circle() -> None:
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glVertex2f(0.0, 0.0)
    for d in range(0, 361, 10):
        a = d * math.pi / 180.0
        GL.glVertex2f(math.sin(a), math.cos(a))
    GL.glEnd()


def setup_gl_state() -> None:
    aspect = window_width / window_height if window_height else 1.0
    yt, yb = 0.05, -0.05
    xl = yt * aspect
    xr = yb * aspect
    GL.glViewport(0, 0, window_width, window_height)
    GL.glClearColor(0.0, 1.0, 1.0, 1.0)
    GL.glMatrixMode(GL.GL_PROJECTION); GL.glLoadIdentity()
    GL.glFrustum(xl, xr, yb, yt, 0.1, 100.0)
    GL.glMatrixMode(GL.GL_MODELVIEW); GL.glLoadIdentity()


def draw() -> None:
    nle_x = window_width // 2 - int(0.3 * (window_width // 2))
    nle_y = window_height // 2
    nre_x = window_width // 2 + int(0.3 * (window_width // 2))
    nre_y = window_height // 2
    min_len = 0.1 * (window_width // 2)
    lt_mag = max(min_len, math.sqrt((mouse_x - nle_x) ** 2 + (mouse_y - nle_y) ** 2))
    rt_mag = max(min_len, math.sqrt((mouse_x - nre_x) ** 2 + (mouse_y - nre_y) ** 2))
    fLeftX = (mouse_x - nle_x) / lt_mag
    fLeftY = -(mouse_y - nle_y) / lt_mag
    fRightX = (mouse_x - nre_x) / rt_mag
    fRightY = -(mouse_y - nre_y) / rt_mag

    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glMatrixMode(GL.GL_PROJECTION); GL.glLoadIdentity()
    GL.glMatrixMode(GL.GL_MODELVIEW); GL.glLoadIdentity()

    GL.glColor3f(1.0, 1.0, 1.0)
    GL.glScalef(0.20, 0.20, 1.0)
    GL.glTranslatef(-1.5, 0.0, 0.0)
    draw_circle()
    GL.glColor3f(0.0, 0.0, 0.0)
    GL.glScalef(0.40, 0.40, 1.0)
    GL.glTranslatef(fLeftX, fLeftY, 0.0)
    draw_circle()

    GL.glColor3f(1.0, 1.0, 1.0)
    GL.glLoadIdentity()
    GL.glScalef(0.20, 0.20, 1.0)
    GL.glTranslatef(1.5, 0.0, 0.0)
    draw_circle()
    GL.glColor3f(0.0, 0.0, 0.0)
    GL.glScalef(0.40, 0.40, 1.0)
    GL.glTranslatef(fRightX, fRightY, 0.0)
    draw_circle()

    GL.glMatrixMode(GL.GL_MODELVIEW); GL.glLoadIdentity()
    GL.glColor3f(0.5, 0.0, 0.7)
    GL.glScalef(0.20, 0.20, 1.0)
    GL.glTranslatef(0.0, -1.5, 0.0)
    GL.glBegin(GL.GL_TRIANGLES)
    GL.glVertex2f(0.0, 1.0)
    GL.glVertex2f(-0.5, -1.0)
    GL.glVertex2f(0.5, -1.0)
    GL.glEnd()


def on_mouse_pos(_window, x: float, y: float) -> None:
    global mouse_x, mouse_y
    mouse_x, mouse_y = int(x), int(y)


def on_size(_window, w: int, h: int) -> None:
    global window_width, window_height
    window_width, window_height = w, h
    setup_gl_state()


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def imgui_menubar() -> None:
    # This demo has no movement keys (the eyeballs track the mouse), so the
    # menubar only carries File -> Quit.
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action("Quit", "Esc",
                            lambda: glfw.set_window_should_close(_window, True))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    global _window
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window = glfw.create_window(window_width, window_height,
                                "Eyeballs (GLX/Python)", None, None)
    if not window:
        glfw.terminate(); sys.exit(1)
    _window = window
    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_size)

    imgui.create_context()
    impl = GlfwRenderer(window)
    # Set our key/cursor callbacks AFTER GlfwRenderer -- it installs its own
    # glfw callbacks that don't chain, so mouse tracking / Esc must be last.
    glfw.set_cursor_pos_callback(window, on_mouse_pos)
    glfw.set_key_callback(window, on_key)

    setup_gl_state()
    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        draw()
        imgui.new_frame()
        imgui_menubar()
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)
    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
