# imageload.py
# Loads a TGA image and draws it via glDrawPixels.
# OpenGL SuperBible, Chapter 7
# Python port of ImageLoad.cpp by Richard S. Wright Jr.

import os
import sys

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit menu item
image_data = None
image_w: int = 0
image_h: int = 0
image_fmt = GL.GL_RGB


def load_image() -> None:
    global image_data, image_w, image_h, image_fmt
    img = iio.imread(os.path.join(PWD, "Fire.tga"))
    img = np.flipud(img)  # OpenGL bottom-up
    image_h, image_w = img.shape[:2]
    if img.ndim == 3 and img.shape[2] == 4:
        image_fmt = GL.GL_RGBA
    elif img.ndim == 3 and img.shape[2] == 3:
        image_fmt = GL.GL_RGB
    else:
        image_fmt = GL.GL_LUMINANCE
    image_data = np.ascontiguousarray(img, dtype=np.uint8)


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
    GL.glRasterPos2i(0, 0)
    GL.glDrawPixels(
        image_w, image_h, image_fmt, GL.GL_UNSIGNED_BYTE, image_data
    )


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.0, 0.0)
    load_image()


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

    window = glfw.create_window(512, 512, "OpenGL Image Loading", None, None)
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
