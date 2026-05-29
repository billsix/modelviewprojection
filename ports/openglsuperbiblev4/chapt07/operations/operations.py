# operations.py
# Demonstrates per-channel pixel transfer operations: flip, zoom,
# isolated R/G/B channels, B&W conversion, color inversion. C++ used a
# right-click GLUT menu; replaced here with an ImGui radio panel.
# OpenGL SuperBible, Chapter 7
# Python port of Operations.cpp by Richard S. Wright Jr.

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

_window = None  # set in main(); used by the Quit control button
image_data = None
image_w: int = 0
image_h: int = 0
image_fmt = GL.GL_RGB

i_render_mode: int = 1


def load_image() -> None:
    global image_data, image_w, image_h, image_fmt
    img = iio.imread(os.path.join(PWD, "horse.tga"))
    img = np.flipud(img)
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
    GL.glRasterPos2i(0, 0)

    modified = None
    modified_fmt = image_fmt

    if i_render_mode == 2:
        # Flip
        GL.glPixelZoom(-1.0, -1.0)
        GL.glRasterPos2i(image_w, image_h)
    elif i_render_mode == 3:
        # Zoom
        viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
        GL.glPixelZoom(viewport[2] / image_w, viewport[3] / image_h)
    elif i_render_mode == 4:
        GL.glPixelTransferf(GL.GL_RED_SCALE, 1.0)
        GL.glPixelTransferf(GL.GL_GREEN_SCALE, 0.0)
        GL.glPixelTransferf(GL.GL_BLUE_SCALE, 0.0)
    elif i_render_mode == 5:
        GL.glPixelTransferf(GL.GL_RED_SCALE, 0.0)
        GL.glPixelTransferf(GL.GL_GREEN_SCALE, 1.0)
        GL.glPixelTransferf(GL.GL_BLUE_SCALE, 0.0)
    elif i_render_mode == 6:
        GL.glPixelTransferf(GL.GL_RED_SCALE, 0.0)
        GL.glPixelTransferf(GL.GL_GREEN_SCALE, 0.0)
        GL.glPixelTransferf(GL.GL_BLUE_SCALE, 1.0)
    elif i_render_mode == 7:
        # Black & white. C++ did this via glPixelTransfer scale + a
        # GL_LUMINANCE readback round-trip; same math (Rec. 601 weights)
        # in numpy, no driver dependency.
        weights = np.array([0.30, 0.59, 0.11], dtype=np.float32)
        lum = image_data[:, :, :3].astype(np.float32) @ weights
        modified = np.ascontiguousarray(np.clip(lum, 0, 255).astype(np.uint8))
        modified_fmt = GL.GL_LUMINANCE
    elif i_render_mode == 8:
        # C++ used glPixelMapfv with 255 entries to invert via lookup.
        # Mesa segfaults on the non-power-of-2 size, and the array was
        # one short for a full 0..255 mapping anyway. Plain numpy.
        modified = np.ascontiguousarray(255 - image_data[:, :, :3])
        modified_fmt = GL.GL_RGB

    if modified is None:
        GL.glDrawPixels(image_w, image_h, image_fmt, GL.GL_UNSIGNED_BYTE,
                        image_data)
    else:
        GL.glDrawPixels(image_w, image_h, modified_fmt,
                        GL.GL_UNSIGNED_BYTE, modified)

    # Reset
    GL.glPixelTransferf(GL.GL_RED_SCALE, 1.0)
    GL.glPixelTransferf(GL.GL_GREEN_SCALE, 1.0)
    GL.glPixelTransferf(GL.GL_BLUE_SCALE, 1.0)
    GL.glPixelZoom(1.0, 1.0)


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.0, 0.0)
    GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
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


def _set_mode(value: int) -> None:
    global i_render_mode
    i_render_mode = value


def imgui_menubar() -> None:
    # All controls live in the top menubar (no keyboard nav besides Esc,
    # which the File -> Quit item covers).
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action("Quit", "Esc",
                            lambda: glfw.set_window_should_close(_window, True))
        imgui.end_menu()
    if imgui.begin_menu("Operations", True):
        for label, value in [
            ("Draw Pixels", 1), ("Flip Pixels", 2), ("Zoom Pixels", 3),
            ("Just Red Channel", 4), ("Just Green Channel", 5),
            ("Just Blue Channel", 6), ("Black and White", 7),
            ("Invert Colors", 8),
        ]:
            _common.menu_action(label, "", lambda v=value: _set_mode(v),
                                selected=(i_render_mode == value))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    global _window
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(800, 600, "OpenGL Image Operations", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)

    _window = window
    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw
    # key callback that doesn't chain, so Esc must be registered last.
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
