# bitmaps.py
# Demonstrates glBitmap -- a 16x16 grid of fire bitmaps.
# OpenGL SuperBible, Chapter 7
# Python port of Bitmaps.cpp by Richard S. Wright Jr.

import os
import sys

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


fire = np.array(
    [
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0xC0,
        0x00,
        0x00,
        0x01,
        0xF0,
        0x00,
        0x00,
        0x07,
        0xF0,
        0x0F,
        0x00,
        0x1F,
        0xE0,
        0x1F,
        0x80,
        0x1F,
        0xC0,
        0x0F,
        0xC0,
        0x3F,
        0x80,
        0x07,
        0xE0,
        0x7E,
        0x00,
        0x03,
        0xF0,
        0xFF,
        0x80,
        0x03,
        0xF5,
        0xFF,
        0xE0,
        0x07,
        0xFD,
        0xFF,
        0xF8,
        0x1F,
        0xFC,
        0xFF,
        0xE8,
        0xFF,
        0xE3,
        0xBF,
        0x70,
        0xDE,
        0x80,
        0xB7,
        0x00,
        0x71,
        0x10,
        0x4A,
        0x80,
        0x03,
        0x10,
        0x4E,
        0x40,
        0x02,
        0x88,
        0x8C,
        0x20,
        0x05,
        0x05,
        0x04,
        0x40,
        0x02,
        0x82,
        0x14,
        0x40,
        0x02,
        0x40,
        0x10,
        0x80,
        0x02,
        0x64,
        0x1A,
        0x80,
        0x00,
        0x92,
        0x29,
        0x00,
        0x00,
        0xB0,
        0x48,
        0x00,
        0x00,
        0xC8,
        0x90,
        0x00,
        0x00,
        0x85,
        0x10,
        0x00,
        0x00,
        0x03,
        0x00,
        0x00,
        0x00,
        0x00,
        0x10,
        0x00,
    ],
    dtype=np.uint8,
)


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glColor3f(1.0, 1.0, 1.0)
    for y in range(16):
        GL.glRasterPos2i(0, y * 32)
        for _ in range(16):
            GL.glBitmap(32, 32, 0.0, 0.0, 32.0, 0.0, fire)


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.0, 0.0)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluOrtho2D(0.0, float(w), 0.0, float(h))
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def imgui_menubar() -> None:
    # All controls in the top menubar. This demo has no movement keys, so
    # only File -> Quit is exposed (mirroring the Esc keyboard shortcut).
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action(
            "Quit", "Esc", lambda: glfw.set_window_should_close(_window, True)
        )
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    global _window

    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(512, 512, "OpenGL Bitmaps", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    _window = window

    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw key
    # callback that doesn't chain, so Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
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
