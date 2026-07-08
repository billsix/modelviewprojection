# multitexture.py
# Two texture units active at once: a tarnish color map on unit 0 and
# a cube-map reflection on unit 1, modulated together.
# OpenGL SuperBible, Chapter 9
# Python port of Multitexture.cpp by Richard S. Wright Jr.

import math
import os
import sys
import time

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
import _primitives  # noqa: E402

_window = None  # set in main(); used by the Quit menu item

camera_x: float = 0.0
camera_y: float = 0.0
camera_z: float = 0.0
camera_yaw: float = 0.0

CUBE_MAP, COLOR_MAP = 0, 1
texture_objects = [0, 0]
cube_faces = [
    "pos_x.tga",
    "neg_x.tga",
    "pos_y.tga",
    "neg_y.tga",
    "pos_z.tga",
    "neg_z.tga",
]
cube_targets = [
    GL.GL_TEXTURE_CUBE_MAP_POSITIVE_X,
    GL.GL_TEXTURE_CUBE_MAP_NEGATIVE_X,
    GL.GL_TEXTURE_CUBE_MAP_POSITIVE_Y,
    GL.GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
    GL.GL_TEXTURE_CUBE_MAP_POSITIVE_Z,
    GL.GL_TEXTURE_CUBE_MAP_NEGATIVE_Z,
]


def load_image(fname: str) -> "tuple[np.ndarray, int, int, int]":
    img = np.flipud(iio.imread(os.path.join(PWD, fname)))
    h, w = img.shape[:2]
    fmt = GL.GL_RGBA if img.ndim == 3 and img.shape[2] == 4 else GL.GL_RGB
    return np.ascontiguousarray(img, dtype=np.uint8), w, h, fmt


# Sphere with a tarnish color-map on unit 0. Its texcoords go on TEXTURE0
# via glMultiTexCoord2f, so draw_mesh (which emits glTexCoord2f) doesn't
# fit -- a slim local replay of the precomputed mesh handles it. The trig
# still runs only once, at import.
SPHERE = _primitives.build_sphere(0.75, 41, 41)


def draw_sphere_multitex() -> None:
    mode, bands = SPHERE
    for band in bands:
        GL.glBegin(mode)
        for v in band:
            GL.glNormal3f(v[0], v[1], v[2])
            GL.glMultiTexCoord2f(GL.GL_TEXTURE0, v[3], v[4])
            GL.glVertex3f(v[5], v[6], v[7])
        GL.glEnd()


def draw_skybox() -> None:
    e = 15.0
    # Six faces, all with explicit cube-map coords on TEXTURE1
    faces = [
        # -X
        [
            (-1.0, -1.0, 1.0, -e, -e, e),
            (-1.0, -1.0, -1.0, -e, -e, -e),
            (-1.0, 1.0, -1.0, -e, e, -e),
            (-1.0, 1.0, 1.0, -e, e, e),
        ],
        # +X
        [
            (1.0, -1.0, -1.0, e, -e, -e),
            (1.0, -1.0, 1.0, e, -e, e),
            (1.0, 1.0, 1.0, e, e, e),
            (1.0, 1.0, -1.0, e, e, -e),
        ],
        # -Z
        [
            (-1.0, -1.0, -1.0, -e, -e, -e),
            (1.0, -1.0, -1.0, e, -e, -e),
            (1.0, 1.0, -1.0, e, e, -e),
            (-1.0, 1.0, -1.0, -e, e, -e),
        ],
        # +Z
        [
            (1.0, -1.0, 1.0, e, -e, e),
            (-1.0, -1.0, 1.0, -e, -e, e),
            (-1.0, 1.0, 1.0, -e, e, e),
            (1.0, 1.0, 1.0, e, e, e),
        ],
        # +Y
        [
            (-1.0, 1.0, 1.0, -e, e, e),
            (-1.0, 1.0, -1.0, -e, e, -e),
            (1.0, 1.0, -1.0, e, e, -e),
            (1.0, 1.0, 1.0, e, e, e),
        ],
        # -Y
        [
            (-1.0, -1.0, -1.0, -e, -e, -e),
            (-1.0, -1.0, 1.0, -e, -e, e),
            (1.0, -1.0, 1.0, e, -e, e),
            (1.0, -1.0, -1.0, e, -e, -e),
        ],
    ]
    GL.glBegin(GL.GL_QUADS)
    for face in faces:
        for tx, ty, tz, vx, vy, vz in face:
            GL.glMultiTexCoord3f(GL.GL_TEXTURE1, tx, ty, tz)
            GL.glVertex3f(vx, vy, vz)
    GL.glEnd()


def setup_rc() -> None:
    GL.glCullFace(GL.GL_BACK)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_DEPTH_TEST)

    texture_objects[0] = GL.glGenTextures(1)
    texture_objects[1] = GL.glGenTextures(1)

    # Cube map
    GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, texture_objects[CUBE_MAP])
    for p in [
        (GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR),
        (GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR),
        (GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE),
        (GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE),
        (GL.GL_TEXTURE_WRAP_R, GL.GL_CLAMP_TO_EDGE),
    ]:
        GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, p[0], p[1])
    for i, fname in enumerate(cube_faces):
        img, w, h, fmt = load_image(fname)
        GL.glTexParameteri(
            GL.GL_TEXTURE_CUBE_MAP, GL.GL_GENERATE_MIPMAP, GL.GL_TRUE
        )
        GL.glTexImage2D(
            cube_targets[i], 0, fmt, w, h, 0, fmt, GL.GL_UNSIGNED_BYTE, img
        )

    # Color map
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_objects[COLOR_MAP])
    for p in [
        (GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR),
        (GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR),
        (GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE),
        (GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE),
    ]:
        GL.glTexParameteri(GL.GL_TEXTURE_2D, p[0], p[1])
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_GENERATE_MIPMAP, GL.GL_TRUE)
    img, w, h, fmt = load_image("tarnish.tga")
    GL.glTexImage2D(
        GL.GL_TEXTURE_2D, 0, fmt, w, h, 0, fmt, GL.GL_UNSIGNED_BYTE, img
    )

    # Texture units
    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_objects[COLOR_MAP])
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_DECAL)

    GL.glActiveTexture(GL.GL_TEXTURE1)
    GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, texture_objects[CUBE_MAP])
    GL.glTexGeni(GL.GL_S, GL.GL_TEXTURE_GEN_MODE, GL.GL_REFLECTION_MAP)
    GL.glTexGeni(GL.GL_T, GL.GL_TEXTURE_GEN_MODE, GL.GL_REFLECTION_MAP)
    GL.glTexGeni(GL.GL_R, GL.GL_TEXTURE_GEN_MODE, GL.GL_REFLECTION_MAP)
    GL.glEnable(GL.GL_TEXTURE_CUBE_MAP)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)


def apply_camera_transform() -> None:
    GL.glRotatef(-math.degrees(camera_yaw), 0.0, 1.0, 0.0)
    GL.glTranslatef(-camera_x, -camera_y, -camera_z)


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    GL.glPushMatrix()
    apply_camera_transform()

    # Skybox -- only TEXTURE1 active. Re-assert the cube map each frame
    # (setup_rc enabled it once, but we disable it before imgui draws below,
    # so it must be turned back on here).
    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glDisable(GL.GL_TEXTURE_2D)
    GL.glActiveTexture(GL.GL_TEXTURE1)
    GL.glEnable(GL.GL_TEXTURE_CUBE_MAP)
    GL.glDisable(GL.GL_TEXTURE_GEN_S)
    GL.glDisable(GL.GL_TEXTURE_GEN_T)
    GL.glDisable(GL.GL_TEXTURE_GEN_R)
    draw_skybox()

    # Sphere -- both texture units active
    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glActiveTexture(GL.GL_TEXTURE1)
    GL.glEnable(GL.GL_TEXTURE_GEN_S)
    GL.glEnable(GL.GL_TEXTURE_GEN_T)
    GL.glEnable(GL.GL_TEXTURE_GEN_R)

    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, -3.0)

    # Inverse-rotate TEXTURE1's texture matrix so reflections track the camera.
    # GL_TEXTURE is per-unit; TEXTURE1 is the active unit here, so this only
    # touches the cube map's matrix.
    GL.glMatrixMode(GL.GL_TEXTURE)
    GL.glPushMatrix()
    GL.glRotatef(math.degrees(camera_yaw), 0.0, 1.0, 0.0)

    draw_sphere_multitex()

    GL.glPopMatrix()
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glPopMatrix()

    GL.glPopMatrix()

    # Leave a clean single-unit texture state for the imgui menubar, which is
    # drawn next via the fixed-function GL2 backend on whatever unit is active.
    # Without this, render_scene leaves TEXTURE1 active with the cube map +
    # texgen on, so imgui binds its font to TEXTURE1 and corrupts the demo's
    # multitexturing on the following frames.
    GL.glActiveTexture(GL.GL_TEXTURE1)
    GL.glDisable(GL.GL_TEXTURE_CUBE_MAP)
    GL.glDisable(GL.GL_TEXTURE_GEN_S)
    GL.glDisable(GL.GL_TEXTURE_GEN_T)
    GL.glDisable(GL.GL_TEXTURE_GEN_R)
    GL.glActiveTexture(GL.GL_TEXTURE0)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(35.0, float(w) / float(h), 1.0, 2000.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


MOVE_UNITS_PER_SEC: float = 3.0
YAW_RAD_PER_SEC: float = 1.5


def handle_camera_keys(window, dt: float) -> None:
    global camera_x, camera_z, camera_yaw
    move = MOVE_UNITS_PER_SEC * dt
    yaw = YAW_RAD_PER_SEC * dt
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera_x += -move * math.sin(camera_yaw)
        camera_z += -move * math.cos(camera_yaw)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera_x -= -move * math.sin(camera_yaw)
        camera_z -= -move * math.cos(camera_yaw)
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera_yaw += yaw
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera_yaw -= yaw


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


# Per-click step for the menubar movement items (the keyboard, held, moves
# continuously via handle_camera_keys; a menu click does one fixed step).
BTN_MOVE_STEP: float = 0.5
BTN_YAW_STEP: float = 0.1


def _walk(direction: int) -> None:
    global camera_x, camera_z
    m = BTN_MOVE_STEP * direction
    camera_x += -m * math.sin(camera_yaw)
    camera_z += -m * math.cos(camera_yaw)


def _turn(d: float) -> None:
    global camera_yaw
    camera_yaw += d


def imgui_menubar() -> None:
    # All controls in the top menubar. Movement items run once per click and
    # show their key in the shortcut column; hold the key for continuous motion.
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action(
            "Quit", "Esc", lambda: glfw.set_window_should_close(_window, True)
        )
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _common.menu_action("Forward", "Up", lambda: _walk(1))
        _common.menu_action("Back", "Down", lambda: _walk(-1))
        _common.menu_action("Turn left", "Left", lambda: _turn(BTN_YAW_STEP))
        _common.menu_action("Turn right", "Right", lambda: _turn(-BTN_YAW_STEP))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    global _window

    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window = glfw.create_window(800, 600, "OpenGL Multitexture", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    _window = window
    glfw.make_context_current(window)
    glfw.swap_interval(1)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw key
    # callback that doesn't chain, so navigation/Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    last_frame = time.monotonic()

    while not glfw.window_should_close(window):
        now = time.monotonic()
        dt = now - last_frame
        last_frame = now

        glfw.poll_events()
        impl.process_inputs()
        handle_camera_keys(window, dt)
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
