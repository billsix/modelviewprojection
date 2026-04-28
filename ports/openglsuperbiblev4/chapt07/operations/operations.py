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

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402
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
        # Black & white via NSTC luminance weights, draw then read back
        GL.glDrawPixels(image_w, image_h, image_fmt, GL.GL_UNSIGNED_BYTE,
                        image_data)
        GL.glPixelTransferf(GL.GL_RED_SCALE, 0.3)
        GL.glPixelTransferf(GL.GL_GREEN_SCALE, 0.59)
        GL.glPixelTransferf(GL.GL_BLUE_SCALE, 0.11)
        modified = GL.glReadPixels(0, 0, image_w, image_h, GL.GL_LUMINANCE,
                                   GL.GL_UNSIGNED_BYTE)
        GL.glPixelTransferf(GL.GL_RED_SCALE, 1.0)
        GL.glPixelTransferf(GL.GL_GREEN_SCALE, 1.0)
        GL.glPixelTransferf(GL.GL_BLUE_SCALE, 1.0)
    elif i_render_mode == 8:
        invert = np.empty(255, dtype=np.float32)
        invert[0] = 1.0
        for i in range(1, 255):
            invert[i] = 1.0 - (1.0 / 255.0 * float(i))
        GL.glPixelMapfv(GL.GL_PIXEL_MAP_R_TO_R, 255, invert)
        GL.glPixelMapfv(GL.GL_PIXEL_MAP_G_TO_G, 255, invert)
        GL.glPixelMapfv(GL.GL_PIXEL_MAP_B_TO_B, 255, invert)
        GL.glPixelTransferi(GL.GL_MAP_COLOR, GL.GL_TRUE)

    if modified is None:
        GL.glDrawPixels(image_w, image_h, image_fmt, GL.GL_UNSIGNED_BYTE,
                        image_data)
    else:
        GL.glDrawPixels(image_w, image_h, GL.GL_LUMINANCE,
                        GL.GL_UNSIGNED_BYTE, modified)

    # Reset
    GL.glPixelTransferi(GL.GL_MAP_COLOR, GL.GL_FALSE)
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


def imgui_panel() -> None:
    global i_render_mode
    imgui.begin("Operations")
    for label, value in [
        ("Draw Pixels", 1), ("Flip Pixels", 2), ("Zoom Pixels", 3),
        ("Just Red Channel", 4), ("Just Green Channel", 5),
        ("Just Blue Channel", 6), ("Black and White", 7), ("Invert Colors", 8),
    ]:
        if imgui.radio_button(label, i_render_mode == value):
            i_render_mode = value
    imgui.end()


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    
    window_width, window_height = _common.resolve_default_window_size()

    window = glfw.create_window(window_width, window_height, "OpenGL Image Operations", None, None)
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
        imgui_panel()
        imgui.render()
        impl.render(imgui.get_draw_data())

        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
