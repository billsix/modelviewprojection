# GLRect.py
# Bouncing red square — the original is a Win32 (no MFC, no GLUT)
# OpenGL "hello world" demonstrating raw window-procedure context
# creation. The Python port uses GLFW for the same role.
#
# OpenGL SuperBible, Chapter 19
# Python port of GLRect.cpp by Richard S. Wright Jr.

import dataclasses
import os
import sys
import typing

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

PWD: str = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

rsize: int = 50


@dataclasses.dataclass
class AppState:
    """The app's mutable state; the one instance is ``state`` below."""

    window: typing.Any = None  # glfw window handle; set in main()

    x1: float = 100.0
    y1: float = 150.0
    xstep: float = 1.0
    ystep: float = 1.0
    window_width: float = 250.0
    window_height: float = 250.0


state: AppState = AppState()


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glLoadIdentity()
    if w <= h:
        state.window_height = 250.0 * h / w
        state.window_width = 250.0
    else:
        state.window_width = 250.0 * w / h
        state.window_height = 250.0
    GLU.gluOrtho2D(0.0, state.window_width, 0.0, state.window_height)


def on_framebuffer_size(_window: typing.Any, w: int, h: int) -> None:
    change_size(w, h)


def idle() -> None:
    if state.x1 > state.window_width - rsize or state.x1 < 0:
        state.xstep = -state.xstep
    if state.y1 > state.window_height - rsize or state.y1 < 0:
        state.ystep = -state.ystep
    if state.x1 > state.window_width - rsize:
        state.x1 = state.window_width - rsize - 1
    if state.y1 > state.window_height - rsize:
        state.y1 = state.window_height - rsize - 1
    state.x1 += state.xstep
    state.y1 += state.ystep


def render_scene() -> None:
    GL.glClearColor(0.0, 0.0, 1.0, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glColor3f(1.0, 0.0, 0.0)
    GL.glRectf(state.x1, state.y1, state.x1 + rsize, state.y1 + rsize)


def on_key(
    window: typing.Any, key: int, _scancode: int, action: int, _mods: int
) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def imgui_menubar() -> None:
    # This demo has no movement keys (the square bounces on its own), so the
    # menubar only carries File -> Quit.
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action(
            "Quit",
            "Esc",
            lambda: glfw.set_window_should_close(state.window, True),
        )
        imgui.end_menu()
    _common.draw_view_menu(state.window)
    imgui.end_main_menu_bar()


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window: typing.Any = glfw.create_window(  # glfw window handle
        250, 250, "GLRect", None, None
    )
    if not window:
        glfw.terminate()
        sys.exit(1)
    state.window = window
    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl: GlfwRenderer = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw key
    # callback that doesn't chain, so Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    size: tuple[int, int] = glfw.get_framebuffer_size(window)
    change_size(size[0], size[1])
    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        idle()
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
