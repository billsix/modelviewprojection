# pointsprites.py
# Demonstrates point sprites: textured points whose corners are
# automatically generated. C++ used a right-click GLUT menu; replaced
# with an ImGui radio panel.
# OpenGL SuperBible, Chapter 9
# Python port of pointsprites.c by Richard S. Wright Jr.

import dataclasses
import os
import random
import sys
import typing

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer
from OpenGL.constant import Constant

PWD: str = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402


@dataclasses.dataclass
class AppState:
    """The app's mutable state; the one instance is ``state`` below."""

    # glfw window handle; set in main()
    window: typing.Any = None
    small_stars: list[tuple[float, float]] = dataclasses.field(
        default_factory=list
    )
    medium_stars: list[tuple[float, float]] = dataclasses.field(
        default_factory=list
    )
    large_stars: list[tuple[float, float]] = dataclasses.field(
        default_factory=list
    )
    draw_mode: int = 1
    textures: list[int] = dataclasses.field(default_factory=lambda: [0, 0])


state: AppState = AppState()
SCREEN_X: int = 800
SCREEN_Y: int = 600
SMALL_STARS: int = 100
MEDIUM_STARS: int = 40
LARGE_STARS: int = 15


def load_textures() -> None:
    GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
    i: int
    fname: str
    for i, fname in enumerate(["star.tga", "moon.tga"]):
        img: np.ndarray = np.flipud(iio.imread(os.path.join(PWD, fname)))
        img_size: tuple[int, ...] = img.shape[:2]
        if img.ndim == 3 and img.shape[2] == 4:
            fmt: Constant = GL.GL_RGBA
        else:
            fmt = GL.GL_RGB
        img = np.ascontiguousarray(img, dtype=np.uint8)
        state.textures[i] = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, state.textures[i])
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            fmt,
            img_size[1],
            img_size[0],
            0,
            fmt,
            GL.GL_UNSIGNED_BYTE,
            img,
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR
        )


def apply_mode(mode: int) -> None:
    if mode == 1:
        GL.glDisable(GL.GL_BLEND)
        GL.glDisable(GL.GL_LINE_SMOOTH)
        GL.glDisable(GL.GL_POINT_SMOOTH)
        GL.glDisable(GL.GL_TEXTURE_2D)
        try:
            GL.glDisable(GL.GL_POINT_SPRITE)
        except Exception:
            pass
    elif mode == 2:
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glEnable(GL.GL_BLEND)
        GL.glEnable(GL.GL_POINT_SMOOTH)
        GL.glEnable(GL.GL_LINE_SMOOTH)
        GL.glDisable(GL.GL_TEXTURE_2D)
        try:
            GL.glDisable(GL.GL_POINT_SPRITE)
        except Exception:
            pass
    elif mode == 3:
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_COLOR, GL.GL_ONE_MINUS_SRC_COLOR)
        GL.glDisable(GL.GL_LINE_SMOOTH)
        GL.glDisable(GL.GL_POINT_SMOOTH)
        GL.glDisable(GL.GL_POLYGON_SMOOTH)


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glColor3f(1.0, 1.0, 1.0)

    if state.draw_mode == 3:
        GL.glEnable(GL.GL_POINT_SPRITE)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, state.textures[0])
        GL.glEnable(GL.GL_BLEND)

    GL.glPointSize(7.0)
    GL.glBegin(GL.GL_POINTS)
    sx: float
    sy: float
    for sx, sy in state.small_stars:
        GL.glVertex2f(sx, sy)
    GL.glEnd()

    GL.glPointSize(12.0)
    GL.glBegin(GL.GL_POINTS)
    sx: float
    sy: float
    for sx, sy in state.medium_stars:
        GL.glVertex2f(sx, sy)
    GL.glEnd()

    GL.glPointSize(20.0)
    GL.glBegin(GL.GL_POINTS)
    sx: float
    sy: float
    for sx, sy in state.large_stars:
        GL.glVertex2f(sx, sy)
    GL.glEnd()

    GL.glPointSize(120.0)
    if state.draw_mode == 3:
        GL.glDisable(GL.GL_BLEND)
        GL.glBindTexture(GL.GL_TEXTURE_2D, state.textures[1])

    GL.glBegin(GL.GL_POINTS)
    GL.glVertex2f(700.0, 500.0)
    GL.glEnd()

    GL.glDisable(GL.GL_TEXTURE_2D)
    try:
        GL.glDisable(GL.GL_POINT_SPRITE)
    except Exception:
        pass

    # Distant horizon
    GL.glLineWidth(3.5)
    GL.glBegin(GL.GL_LINE_STRIP)
    px: float
    py: float
    for px, py in [
        (0.0, 25.0),
        (50.0, 100.0),
        (100.0, 25.0),
        (225.0, 125.0),
        (300.0, 50.0),
        (375.0, 100.0),
        (460.0, 25.0),
        (525.0, 100.0),
        (600.0, 20.0),
        (675.0, 70.0),
        (750.0, 25.0),
        (800.0, 90.0),
    ]:
        GL.glVertex2f(px, py)
    GL.glEnd()


def setup_rc() -> None:
    random.seed(0)
    for _ in range(SMALL_STARS):
        state.small_stars.append(
            (
                float(random.randint(0, SCREEN_X - 1)),
                float(random.randint(0, SCREEN_Y - 100 - 1)) + 100.0,
            )
        )
    for _ in range(MEDIUM_STARS):
        state.medium_stars.append(
            (
                float(random.randint(0, SCREEN_X * 10 - 1)) / 10.0,
                float(random.randint(0, SCREEN_Y - 100 - 1)) + 100.0,
            )
        )
    for _ in range(LARGE_STARS):
        state.large_stars.append(
            (
                float(random.randint(0, SCREEN_X * 10 - 1)) / 10.0,
                float(random.randint(0, (SCREEN_Y - 100) * 10 - 1)) / 10.0
                + 100.0,
            )
        )
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    load_textures()
    GL.glTexEnvi(GL.GL_POINT_SPRITE, GL.GL_COORD_REPLACE, GL.GL_TRUE)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluOrtho2D(0.0, SCREEN_X, 0.0, SCREEN_Y)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window: typing.Any, w: int, h: int) -> None:
    change_size(w, h)


def on_key(
    window: typing.Any, key: int, _scancode: int, action: int, _mods: int
) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def _set_mode(value: int) -> None:
    state.draw_mode = value
    apply_mode(state.draw_mode)


def imgui_menubar() -> None:
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
    if imgui.begin_menu("Draw mode", True):
        label: str
        value: int
        for label, value in [
            ("Normal Points", 1),
            ("Antialiased Points", 2),
            ("Point Sprites", 3),
        ]:
            _common.menu_action(
                label,
                "",
                lambda v=value: _set_mode(v),
                selected=(state.draw_mode == value),
            )
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window: typing.Any = glfw.create_window(  # glfw window handle
        800, 600, "Point Sprites", None, None
    )
    if not window:
        glfw.terminate()
        sys.exit(1)
    state.window = window
    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl: GlfwRenderer = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw
    # key callback that doesn't chain, so Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    setup_rc()
    apply_mode(state.draw_mode)
    size: tuple[int, int] = glfw.get_framebuffer_size(window)
    change_size(size[0], size[1])

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
