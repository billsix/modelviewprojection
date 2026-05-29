# imaging.py
# Demonstrates image processing: convolution kernels (sharpen, emboss),
# color tables (invert), color matrix (brighten, B&W), and histograms.
# The C++ original used the GL_ARB_imaging subset (glConvolutionFilter2D,
# glHistogram, glColorTable, glMatrixMode(GL_COLOR)) which is deprecated
# and not exposed by Mesa or most modern drivers. This port does the
# math CPU-side with numpy and ships the finished pixels to the GPU via
# glDrawPixels, so the visual output matches the textbook regardless of
# what extensions the driver advertises.
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
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit control button
image_data: np.ndarray
image_w: int = 0
image_h: int = 0
image_fmt = GL.GL_RGB

MODE_RAW, MODE_CONTRAST, MODE_INVERT, MODE_EMBOSS, MODE_SHARPEN = 1, 2, 3, 4, 5
i_render_mode: int = MODE_RAW
b_histogram: bool = False

# Luminance weights (Rec. 601). In the C++ this was a 4x4 GL_COLOR
# matrix; here it's just a dot-product against (R, G, B).
LUM_WEIGHTS = np.array([0.30, 0.59, 0.11], dtype=np.float32)

KERNEL_SHARPEN = np.array(
    [[0.0, -1.0, 0.0], [-1.0, 5.0, -1.0], [0.0, -1.0, 0.0]],
    dtype=np.float32,
)
KERNEL_EMBOSS = np.array(
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


def convolve3x3(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """3x3 convolution per channel, edge-padded. Returns uint8 clipped
    0..255. Same result as the deprecated glConvolutionFilter2D."""
    h, w = image.shape[:2]
    padded = np.pad(image, ((1, 1), (1, 1), (0, 0)), mode="edge")
    out = np.zeros(image.shape, dtype=np.float32)
    for i in range(3):
        for j in range(3):
            out += kernel[i, j] * padded[i:i + h, j:j + w].astype(np.float32)
    return np.clip(out, 0, 255).astype(np.uint8)


def to_luminance(image: np.ndarray) -> np.ndarray:
    """Collapse RGB to luminance, expanded back to 3 channels so the
    rest of the pipeline doesn't have to special-case grayscale."""
    lum = image[:, :, :3].astype(np.float32) @ LUM_WEIGHTS
    lum = np.clip(lum, 0, 255).astype(np.uint8)
    return np.stack([lum, lum, lum], axis=-1)


def process_image(mode: int) -> np.ndarray:
    """The CPU equivalent of the GL_ARB_imaging pipeline for each
    radio-button mode."""
    if mode == MODE_RAW:
        return image_data
    if mode == MODE_CONTRAST:
        # C++: glScalef(1.25, 1.25, 1.25) on the GL_COLOR matrix.
        return np.clip(image_data.astype(np.float32) * 1.25, 0, 255).astype(np.uint8)
    if mode == MODE_INVERT:
        # C++: glColorTable inverting every entry.
        out = image_data.copy()
        out[:, :, :3] = 255 - out[:, :, :3]
        return out
    if mode == MODE_EMBOSS:
        # C++ applied the emboss kernel AND the luminance color matrix.
        return to_luminance(convolve3x3(image_data, KERNEL_EMBOSS))
    if mode == MODE_SHARPEN:
        return convolve3x3(image_data, KERNEL_SHARPEN)
    return image_data


def compute_histogram(image: np.ndarray) -> np.ndarray:
    """256-bin luminance histogram. C++ used glHistogram + glGetHistogram
    on the luminance-converted draw."""
    lum = (image[:, :, :3].astype(np.float32) @ LUM_WEIGHTS).astype(np.uint8)
    counts, _ = np.histogram(lum, bins=256, range=(0, 256))
    return counts.astype(np.int32)


def render_scene() -> None:
    global b_histogram

    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glRasterPos2i(0, 0)
    viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
    GL.glPixelZoom(viewport[2] / image_w, viewport[3] / image_h)

    processed = process_image(i_render_mode)
    processed = np.ascontiguousarray(processed)
    GL.glDrawPixels(image_w, image_h, image_fmt, GL.GL_UNSIGNED_BYTE,
                    processed)

    if b_histogram:
        # Scale histogram x-extent to the window so it stays readable
        # at any window size; y-extent is fixed at 25% of window height.
        GL.glPixelZoom(1.0, 1.0)
        hist = compute_histogram(processed)
        largest = int(hist[:255].max()) or 1
        win_w, win_h = float(viewport[2]), float(viewport[3])
        GL.glColor3f(1.0, 1.0, 0.0)
        GL.glLineWidth(2.0)
        GL.glBegin(GL.GL_LINE_STRIP)
        for i in range(256):
            x = (i / 255.0) * win_w
            y = (float(hist[i]) / largest) * (win_h * 0.25)
            GL.glVertex2f(x, y)
        GL.glEnd()
        GL.glLineWidth(1.0)


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
    global b_histogram
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action("Quit", "Esc",
                            lambda: glfw.set_window_should_close(_window, True))
        imgui.end_menu()
    if imgui.begin_menu("Imaging", True):
        for label, value in [
            ("Raw Stretched Image", MODE_RAW),
            ("Increase Contrast", MODE_CONTRAST),
            ("Invert Color", MODE_INVERT),
            ("Emboss Image", MODE_EMBOSS),
            ("Sharpen Image", MODE_SHARPEN),
        ]:
            _common.menu_action(label, "", lambda v=value: _set_mode(v),
                                selected=(i_render_mode == value))
        imgui.separator()
        _, b_histogram = imgui.menu_item("Histogram", "", b_histogram, True)
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    global _window
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(600, 600, "OpenGL Imaging subset", None, None)
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
