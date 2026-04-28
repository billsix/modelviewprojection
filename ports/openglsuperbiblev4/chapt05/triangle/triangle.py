# triangle.py
# A flat-shaded RGB triangle, demonstrating Gouraud (per-vertex)
# color interpolation when GL_SMOOTH is enabled.
# OpenGL SuperBible, Chapter 5
# Python port of Triangle.cpp by Richard S. Wright Jr.

import os
import sys

import glfw
import OpenGL.GL as GL
from imgui_bundle import imgui

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glShadeModel(GL.GL_SMOOTH)

    GL.glBegin(GL.GL_TRIANGLES)
    GL.glColor3ub(255, 0, 0)
    GL.glVertex3f(0.0, 200.0, 0.0)
    GL.glColor3ub(0, 255, 0)
    GL.glVertex3f(200.0, -70.0, 0.0)
    GL.glColor3ub(0, 0, 255)
    GL.glVertex3f(-200.0, -70.0, 0.0)
    GL.glEnd()


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glLoadIdentity()
    if w <= h:
        win_h = 250.0 * h / w
        win_w = 250.0
    else:
        win_w = 250.0 * w / h
        win_h = 250.0
    GL.glOrtho(-win_w, win_w, -win_h, win_h, 1.0, -1.0)


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    
    window_width, window_height = _common.resolve_default_window_size()

    window = glfw.create_window(window_width, window_height, "RGB Triangle", None, None)
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

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        render_scene()
        
        imgui.new_frame()
        _common.draw_menubar(window, win_state)
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()

    glfw.terminate()


if __name__ == "__main__":
    main()
