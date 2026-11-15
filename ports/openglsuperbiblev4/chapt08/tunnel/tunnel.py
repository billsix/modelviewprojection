# tunnel.py
# Mipmapping demo: a textured corridor with floor/ceiling/wall textures.
# Arrow keys move forward/back. C++ used a right-click GLUT menu for
# texture filter; replaced with an ImGui combo.
# OpenGL SuperBible, Chapter 8
# Python port of Tunnel.cpp by Richard S. Wright Jr.

import dataclasses
import math
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

TEXTURE_BRICK: int = 0
TEXTURE_FLOOR: int = 1
TEXTURE_CEILING: int = 2
texture_files: list[str] = ["brick.tga", "floor.tga", "ceiling.tga"]
camera_y: float = 0.0


@dataclasses.dataclass
class AppState:
    """The app's mutable state; the one instance is ``state`` below."""

    # glfw window handle; set in main()
    window: typing.Any = None

    textures: list[int] = dataclasses.field(default_factory=lambda: [0, 0, 0])
    filter_idx: int = 5  # 0..5 selects min filter mode

    # Walk-around camera. Initial position puts the camera at the tunnel
    # mouth looking down -Z, matching the original z_pos=-60 view.
    # (camera_y never changes, so it stays a module constant.)
    camera_x: float = 0.0
    camera_z: float = 60.0
    camera_yaw: float = 0.0


state: AppState = AppState()


def apply_camera_transform() -> None:
    GL.glRotatef(-math.degrees(state.camera_yaw), 0.0, 1.0, 0.0)
    GL.glTranslatef(-state.camera_x, -camera_y, -state.camera_z)


def load_textures() -> None:
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_DECAL)
    GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)

    i: int
    fname: str
    for i, fname in enumerate(texture_files):
        img: np.ndarray = iio.imread(os.path.join(PWD, fname))
        img = np.flipud(img)
        img_size: tuple[int, ...] = img.shape[:2]
        fmt: Constant
        internal: Constant
        if img.ndim == 3 and img.shape[2] == 4:
            fmt = GL.GL_RGBA
            internal = GL.GL_RGBA
        else:
            fmt = GL.GL_RGB
            internal = GL.GL_RGB
        img = np.ascontiguousarray(img, dtype=np.uint8)

        state.textures[i] = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, state.textures[i])
        GLU.gluBuild2DMipmaps(
            GL.GL_TEXTURE_2D,
            internal,
            img_size[1],
            img_size[0],
            fmt,
            GL.GL_UNSIGNED_BYTE,
            img,
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D,
            GL.GL_TEXTURE_MIN_FILTER,
            GL.GL_LINEAR_MIPMAP_LINEAR,
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE
        )


def apply_filter(idx: int) -> None:
    modes: list[Constant] = [
        GL.GL_NEAREST,
        GL.GL_LINEAR,
        GL.GL_NEAREST_MIPMAP_NEAREST,
        GL.GL_NEAREST_MIPMAP_LINEAR,
        GL.GL_LINEAR_MIPMAP_NEAREST,
        GL.GL_LINEAR_MIPMAP_LINEAR,
    ]
    tex: int
    for tex in state.textures:
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, modes[idx]
        )


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glPushMatrix()
    apply_camera_transform()

    z: float = 60.0
    while z >= 0.0:
        # Floor
        GL.glBindTexture(GL.GL_TEXTURE_2D, state.textures[TEXTURE_FLOOR])
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 0.0)
        GL.glVertex3f(-10.0, -10.0, z)
        GL.glTexCoord2f(1.0, 0.0)
        GL.glVertex3f(10.0, -10.0, z)
        GL.glTexCoord2f(1.0, 1.0)
        GL.glVertex3f(10.0, -10.0, z - 10.0)
        GL.glTexCoord2f(0.0, 1.0)
        GL.glVertex3f(-10.0, -10.0, z - 10.0)
        GL.glEnd()

        # Ceiling
        GL.glBindTexture(GL.GL_TEXTURE_2D, state.textures[TEXTURE_CEILING])
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 1.0)
        GL.glVertex3f(-10.0, 10.0, z - 10.0)
        GL.glTexCoord2f(1.0, 1.0)
        GL.glVertex3f(10.0, 10.0, z - 10.0)
        GL.glTexCoord2f(1.0, 0.0)
        GL.glVertex3f(10.0, 10.0, z)
        GL.glTexCoord2f(0.0, 0.0)
        GL.glVertex3f(-10.0, 10.0, z)
        GL.glEnd()

        # Left wall
        GL.glBindTexture(GL.GL_TEXTURE_2D, state.textures[TEXTURE_BRICK])
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 0.0)
        GL.glVertex3f(-10.0, -10.0, z)
        GL.glTexCoord2f(1.0, 0.0)
        GL.glVertex3f(-10.0, -10.0, z - 10.0)
        GL.glTexCoord2f(1.0, 1.0)
        GL.glVertex3f(-10.0, 10.0, z - 10.0)
        GL.glTexCoord2f(0.0, 1.0)
        GL.glVertex3f(-10.0, 10.0, z)
        GL.glEnd()

        # Right wall
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 1.0)
        GL.glVertex3f(10.0, 10.0, z)
        GL.glTexCoord2f(1.0, 1.0)
        GL.glVertex3f(10.0, 10.0, z - 10.0)
        GL.glTexCoord2f(1.0, 0.0)
        GL.glVertex3f(10.0, -10.0, z - 10.0)
        GL.glTexCoord2f(0.0, 0.0)
        GL.glVertex3f(10.0, -10.0, z)
        GL.glEnd()

        z -= 10.0

    GL.glPopMatrix()


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    load_textures()


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    # 90 deg FOV (the original) fisheyes hard when the user yaws.
    # 70 deg is the standard first-person-shooter value -- wide enough
    # to feel like walking through a tunnel, narrow enough to keep
    # rotation distortion in check.
    GLU.gluPerspective(70.0, float(w) / float(h), 1.0, 120.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window: typing.Any, w: int, h: int) -> None:
    change_size(w, h)


MOVE_UNITS_PER_SEC: float = 10.0
YAW_RAD_PER_SEC: float = 1.5


def handle_special_keys(window: typing.Any, dt: float) -> None:
    move: float = MOVE_UNITS_PER_SEC * dt
    yaw: float = YAW_RAD_PER_SEC * dt
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        state.camera_x += -move * math.sin(state.camera_yaw)
        state.camera_z += -move * math.cos(state.camera_yaw)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        state.camera_x -= -move * math.sin(state.camera_yaw)
        state.camera_z -= -move * math.cos(state.camera_yaw)
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        state.camera_yaw += yaw
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        state.camera_yaw -= yaw


def on_key(
    window: typing.Any, key: int, _scancode: int, action: int, _mods: int
) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def _move(sign: float) -> None:
    step: float = sign * MOVE_UNITS_PER_SEC / 60.0
    state.camera_x += -step * math.sin(state.camera_yaw)
    state.camera_z += -step * math.cos(state.camera_yaw)


def _yaw(sign: float) -> None:
    state.camera_yaw += sign * YAW_RAD_PER_SEC / 60.0


FILTER_NAMES: list[str] = [
    "GL_NEAREST",
    "GL_LINEAR",
    "GL_NEAREST_MIPMAP_NEAREST",
    "GL_NEAREST_MIPMAP_LINEAR",
    "GL_LINEAR_MIPMAP_NEAREST",
    "GL_LINEAR_MIPMAP_LINEAR",
]


def _set_filter(idx: int) -> None:
    state.filter_idx = idx
    apply_filter(state.filter_idx)


def imgui_menubar() -> None:
    # All controls live in the top menubar. The min-filter combo becomes
    # radio menu items; movement items show their key (hold for continuous
    # walking).
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
    if imgui.begin_menu("Min Filter", True):
        i: int
        name: str
        for i, name in enumerate(FILTER_NAMES):
            _common.menu_action(
                name,
                "",
                lambda v=i: _set_filter(v),
                selected=(state.filter_idx == i),
            )
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _common.menu_action("Forward", "Up", lambda: _move(1.0))
        _common.menu_action("Back", "Down", lambda: _move(-1.0))
        _common.menu_action("Turn Left", "Left", lambda: _yaw(1.0))
        _common.menu_action("Turn Right", "Right", lambda: _yaw(-1.0))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window: typing.Any = glfw.create_window(  # glfw window handle
        800, 600, "Tunnel", None, None
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
    apply_filter(state.filter_idx)
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
