# fscreen.py
# Same bouncing square as GLRect, but in a borderless full-screen
# window. The C++ version used Win32 DEVMODE / ChangeDisplaySettings;
# this port uses GLFW's primary monitor on the create_window call.
# Press Esc to leave full screen / quit.
#
# OpenGL SuperBible, Chapter 19
# Python port of FScreen.cpp by Richard S. Wright Jr.

import os
import sys

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


x1: float = 100.0
y1: float = 150.0
rsize: int = 50
xstep: float = 1.0
ystep: float = 1.0
window_width: float = 250.0
window_height: float = 250.0


def change_size(w: int, h: int) -> None:
    global window_width, window_height
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glLoadIdentity()
    if w <= h:
        window_height = 250.0 * h / w
        window_width = 250.0
    else:
        window_width = 250.0 * w / h
        window_height = 250.0
    GLU.gluOrtho2D(0.0, window_width, 0.0, window_height)


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def render_scene() -> None:
    global x1, y1, xstep, ystep
    if x1 > window_width - rsize or x1 < 0:
        xstep = -xstep
    if y1 > window_height - rsize or y1 < 0:
        ystep = -ystep
    if x1 > window_width - rsize:
        x1 = window_width - rsize - 1
    if y1 > window_height - rsize:
        y1 = window_height - rsize - 1
    x1 += xstep
    y1 += ystep
    GL.glClearColor(0.0, 0.0, 1.0, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glColor3f(1.0, 0.0, 0.0)
    GL.glRectf(x1, y1, x1 + rsize, y1 + rsize)


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    monitor = glfw.get_primary_monitor()
    mode = glfw.get_video_mode(monitor)
    
    window_width, window_height = _common.resolve_default_window_size()
    window = glfw.create_window(mode.size.width, mode.size.height,
                                "Full Screen Demo", monitor, None)
    if not window:
        glfw.terminate(); sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    impl = _common.init_imgui(window)
    win_state = _common.WindowState()
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
