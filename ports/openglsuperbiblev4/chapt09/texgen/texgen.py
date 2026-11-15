# texgen.py
# Demonstrates OpenGL automatic texture coordinate generation: object
# linear, eye linear, and sphere mapping.
# OpenGL SuperBible, Chapter 9
# Python port of TexGen.cpp by Richard S. Wright Jr.

import dataclasses
import os
import sys
import time
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
import _primitives  # noqa: E402


@dataclasses.dataclass
class AppState:
    """The app's mutable state; the one instance is ``state`` below."""

    # glfw window handle; set in main()
    window: typing.Any = None
    x_rot: float = 0.0
    y_rot: float = 0.0
    to_textures: list[int] = dataclasses.field(default_factory=lambda: [0, 0])
    i_render_mode: int = 3


state: AppState = AppState()


# Torus the texgen modes are demonstrated on -- texgen generates its
# texcoords, so none are stored; tessellate once at import.
TORUS: _primitives.Mesh = _primitives.build_torus(0.35, 0.15, 61, 37)


def apply_mode(mode: int) -> None:
    z_plane: list[float] = [0.0, 0.0, 1.0, 0.0]
    if mode == 1:
        GL.glTexGeni(GL.GL_S, GL.GL_TEXTURE_GEN_MODE, GL.GL_OBJECT_LINEAR)
        GL.glTexGeni(GL.GL_T, GL.GL_TEXTURE_GEN_MODE, GL.GL_OBJECT_LINEAR)
        GL.glTexGenfv(GL.GL_S, GL.GL_OBJECT_PLANE, z_plane)
        GL.glTexGenfv(GL.GL_T, GL.GL_OBJECT_PLANE, z_plane)
    elif mode == 2:
        GL.glTexGeni(GL.GL_S, GL.GL_TEXTURE_GEN_MODE, GL.GL_EYE_LINEAR)
        GL.glTexGeni(GL.GL_T, GL.GL_TEXTURE_GEN_MODE, GL.GL_EYE_LINEAR)
        GL.glTexGenfv(GL.GL_S, GL.GL_EYE_PLANE, z_plane)
        GL.glTexGenfv(GL.GL_T, GL.GL_EYE_PLANE, z_plane)
    else:
        GL.glTexGeni(GL.GL_S, GL.GL_TEXTURE_GEN_MODE, GL.GL_SPHERE_MAP)
        GL.glTexGeni(GL.GL_T, GL.GL_TEXTURE_GEN_MODE, GL.GL_SPHERE_MAP)


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    # Background quad in 2D ortho space
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glPushMatrix()
    GL.glLoadIdentity()
    GLU.gluOrtho2D(0.0, 1.0, 0.0, 1.0)

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glBindTexture(GL.GL_TEXTURE_2D, state.to_textures[1])
    GL.glDisable(GL.GL_TEXTURE_GEN_S)
    GL.glDisable(GL.GL_TEXTURE_GEN_T)
    GL.glDepthMask(GL.GL_FALSE)

    GL.glBegin(GL.GL_QUADS)
    GL.glTexCoord2f(0.0, 0.0)
    GL.glVertex2f(0.0, 0.0)
    GL.glTexCoord2f(1.0, 0.0)
    GL.glVertex2f(1.0, 0.0)
    GL.glTexCoord2f(1.0, 1.0)
    GL.glVertex2f(1.0, 1.0)
    GL.glTexCoord2f(0.0, 1.0)
    GL.glVertex2f(0.0, 1.0)
    GL.glEnd()

    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glPopMatrix()
    GL.glMatrixMode(GL.GL_MODELVIEW)

    GL.glEnable(GL.GL_TEXTURE_GEN_S)
    GL.glEnable(GL.GL_TEXTURE_GEN_T)
    GL.glDepthMask(GL.GL_TRUE)

    if state.i_render_mode != 3:
        GL.glBindTexture(GL.GL_TEXTURE_2D, state.to_textures[0])

    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, -2.0)
    GL.glRotatef(state.x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(state.y_rot, 0.0, 1.0, 0.0)
    _primitives.draw_mesh(TORUS)
    GL.glPopMatrix()

    # Turn texgen off for the imgui menubar (re-enabled each frame above), so
    # the menubar quad isn't given generated texture coords.
    GL.glDisable(GL.GL_TEXTURE_GEN_S)
    GL.glDisable(GL.GL_TEXTURE_GEN_T)


def setup_rc() -> None:
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glClearColor(1.0, 1.0, 1.0, 1.0)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_DECAL)

    i: int
    fname: str
    for i, fname in enumerate(["stripes.tga", "Environment.tga"]):
        img: np.ndarray = np.flipud(iio.imread(os.path.join(PWD, fname)))
        img_size: tuple[int, ...] = img.shape[:2]
        fmt: Constant = (
            GL.GL_RGBA if img.ndim == 3 and img.shape[2] == 4 else GL.GL_RGB
        )
        img = np.ascontiguousarray(img, dtype=np.uint8)
        state.to_textures[i] = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, state.to_textures[i])
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
        GL.glTexParameterf(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR
        )
        GL.glTexParameterf(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR
        )
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)

    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glEnable(GL.GL_TEXTURE_GEN_S)
    GL.glEnable(GL.GL_TEXTURE_GEN_T)
    apply_mode(state.i_render_mode)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(45.0, float(w) / float(h), 1.0, 225.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window: typing.Any, w: int, h: int) -> None:
    change_size(w, h)


ROT_DEG_PER_SEC: float = 90.0


def handle_special_keys(window: typing.Any, dt: float) -> None:
    step: float = ROT_DEG_PER_SEC * dt
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        state.x_rot -= step
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        state.x_rot += step
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        state.y_rot -= step
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        state.y_rot += step


def on_key(
    window: typing.Any, key: int, _scancode: int, action: int, _mods: int
) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def _nudge_x(d: float) -> None:
    state.x_rot += d


def _nudge_y(d: float) -> None:
    state.y_rot += d


def _set_mode(value: int) -> None:
    state.i_render_mode = value
    apply_mode(state.i_render_mode)


def imgui_menubar() -> None:
    # All controls live in the top menubar. Movement items run once per click
    # and show their key in the shortcut column (discovery); hold the key for
    # continuous rotation.
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
    if imgui.begin_menu("Render Mode", True):
        label: str
        value: int
        for label, value in [
            ("Object Linear", 1),
            ("Eye Linear", 2),
            ("Sphere Map", 3),
        ]:
            _common.menu_action(
                label,
                "",
                lambda v=value: _set_mode(v),
                selected=(state.i_render_mode == value),
            )
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _common.menu_action("Rotate Up", "Up", lambda: _nudge_x(-2.0))
        _common.menu_action("Rotate Down", "Down", lambda: _nudge_x(2.0))
        _common.menu_action("Rotate Left", "Left", lambda: _nudge_y(-2.0))
        _common.menu_action("Rotate Right", "Right", lambda: _nudge_y(2.0))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window: typing.Any = glfw.create_window(  # glfw window handle
        800, 600, "Texture Coordinate Generation", None, None
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

    setup_rc()
    size: tuple[int, int] = glfw.get_framebuffer_size(window)
    change_size(size[0], size[1])

    glfw.swap_interval(1)
    last_frame: float = time.monotonic()

    while not glfw.window_should_close(window):
        now: float = time.monotonic()
        dt: float = now - last_frame
        last_frame = now

        glfw.poll_events()
        impl.process_inputs()
        handle_special_keys(window, dt)
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
