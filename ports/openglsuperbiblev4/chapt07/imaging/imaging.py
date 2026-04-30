# imaging.py
# Demonstrates the GL_ARB_imaging subset: convolution kernels (sharpen,
# emboss), color tables (invert), color matrix (brighten, B&W) and
# histograms. The C++ used a right-click GLUT menu; replaced with an
# ImGui panel.
#
# Note: GL_ARB_imaging is deprecated in modern core OpenGL. If the
# driver doesn't expose it, the relevant glConvolutionFilter2D /
# glHistogram / glColorTable calls will fail at runtime.
#
# OpenGL SuperBible, Chapter 7
# Python port of Imaging.cpp by Richard S. Wright Jr.

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
image_data = None
image_w: int = 0
image_h: int = 0
image_fmt = GL.GL_RGB

i_render_mode: int = 1
b_histogram: bool = False

lum_mat = np.array(
    [
        0.30, 0.30, 0.30, 0.0,
        0.59, 0.59, 0.59, 0.0,
        0.11, 0.11, 0.11, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ],
    dtype=np.float32,
)
m_sharpen = np.array(
    [[0.0, -1.0, 0.0], [-1.0, 5.0, -1.0], [0.0, -1.0, 0.0]],
    dtype=np.float32,
)
m_emboss = np.array(
    [[2.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, -1.0]],
    dtype=np.float32,
)


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
    global b_histogram

    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glRasterPos2i(0, 0)
    viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
    GL.glPixelZoom(viewport[2] / image_w, viewport[3] / image_h)

    if b_histogram:
        GL.glMatrixMode(GL.GL_COLOR)
        GL.glLoadMatrixf(lum_mat)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glHistogram(GL.GL_HISTOGRAM, 256, GL.GL_LUMINANCE, GL.GL_FALSE)
        GL.glEnable(GL.GL_HISTOGRAM)

    if i_render_mode == 5:
        GL.glConvolutionFilter2D(
            GL.GL_CONVOLUTION_2D, GL.GL_RGB, 3, 3,
            GL.GL_LUMINANCE, GL.GL_FLOAT, m_sharpen,
        )
        GL.glEnable(GL.GL_CONVOLUTION_2D)
    elif i_render_mode == 4:
        GL.glConvolutionFilter2D(
            GL.GL_CONVOLUTION_2D, GL.GL_RGB, 3, 3,
            GL.GL_LUMINANCE, GL.GL_FLOAT, m_emboss,
        )
        GL.glEnable(GL.GL_CONVOLUTION_2D)
        GL.glMatrixMode(GL.GL_COLOR)
        GL.glLoadMatrixf(lum_mat)
        GL.glMatrixMode(GL.GL_MODELVIEW)
    elif i_render_mode == 3:
        invert_table = np.zeros((256, 3), dtype=np.uint8)
        for i in range(255):
            invert_table[i] = (255 - i, 255 - i, 255 - i)
        GL.glColorTable(GL.GL_COLOR_TABLE, GL.GL_RGB, 256, GL.GL_RGB,
                        GL.GL_UNSIGNED_BYTE, invert_table)
        GL.glEnable(GL.GL_COLOR_TABLE)
    elif i_render_mode == 2:
        GL.glMatrixMode(GL.GL_COLOR)
        GL.glScalef(1.25, 1.25, 1.25)
        GL.glMatrixMode(GL.GL_MODELVIEW)
    # case 1 -- plain copy

    GL.glDrawPixels(image_w, image_h, image_fmt, GL.GL_UNSIGNED_BYTE,
                    image_data)

    if b_histogram:
        histogram = np.zeros(256, dtype=np.int32)
        GL.glGetHistogram(GL.GL_HISTOGRAM, GL.GL_TRUE, GL.GL_LUMINANCE,
                          GL.GL_INT, histogram)
        largest = int(histogram[:255].max()) or 1
        GL.glColor3f(1.0, 1.0, 1.0)
        GL.glBegin(GL.GL_LINE_STRIP)
        for i in range(255):
            GL.glVertex2f(float(i), float(histogram[i]) / largest * 128.0)
        GL.glEnd()
        b_histogram = False
        GL.glDisable(GL.GL_HISTOGRAM)

    GL.glMatrixMode(GL.GL_COLOR)
    GL.glLoadIdentity()
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glDisable(GL.GL_CONVOLUTION_2D)
    GL.glDisable(GL.GL_COLOR_TABLE)


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
    global i_render_mode, b_histogram
    imgui.begin("Imaging")
    for label, value in [
        ("Raw Stretched Image", 1), ("Increase Contrast", 2),
        ("Invert Color", 3), ("Emboss Image", 4), ("Sharpen Image", 5),
    ]:
        if imgui.radio_button(label, i_render_mode == value):
            i_render_mode = value
    imgui.separator()
    if imgui.button("Histogram"):
        b_histogram = True
    imgui.end()


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(600, 600, "OpenGL Imaging subset", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        render_scene()

        imgui.new_frame()
        imgui_panel()
        imgui.render()
        impl.render(imgui.get_draw_data())

        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
