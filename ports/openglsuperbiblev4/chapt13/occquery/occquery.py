# occquery.py
# Occlusion queries: a cube of 27 spheres is wrapped in bounding cubes;
# at draw time only the spheres whose bounding box passed depth testing
# in the previous frame are rendered. The render options (occlusion
# detection, bounding volumes, help overlay) live on an imgui panel;
# arrows and x/y/z (and SHIFT) fly the camera.
#
# Note: the C++ original used glutSolidTetrahedron/Octahedron/etc. for
# alternate bounding volumes; this port keeps just the box variant for
# simplicity.
#
# OpenGL SuperBible, Chapter 13
# Python port of occquery.cpp by Benjamin Lipchak

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


@dataclasses.dataclass
class AppState:
    """The app's mutable state; the one instance is ``state`` below."""

    window: typing.Any = None  # glfw window handle; set in main()
    window_width: int = 1024
    window_height: int = 768

    show_menu: bool = True
    occlusion_detection: bool = True
    show_bounding_volume: bool = False
    query_ids: np.ndarray = dataclasses.field(
        default_factory=lambda: np.zeros(27, dtype=np.uint32)
    )

    camera_pos: list[float] = dataclasses.field(
        default_factory=lambda: [200.0, 300.0, 400.0, 1.0]
    )
    texture_id: int = 0


state: AppState = AppState()

ambient_light: tuple[float, float, float, float] = (0.4, 0.4, 0.4, 1.0)
diffuse_light: tuple[float, float, float, float] = (0.9, 0.9, 0.9, 1.0)
light_pos: tuple[float, float, float, float] = (100.0, 300.0, 100.0, 1.0)

camera_zoom: float = 0.6


def draw_solid_cube(size: float) -> None:
    s: float = size / 2.0
    GL.glBegin(GL.GL_QUADS)
    nx: int
    ny: int
    nz: int
    vs: list[tuple[float, float, float]]
    for nx, ny, nz, vs in [
        (0, 0, 1, [(-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s)]),
        (0, 0, -1, [(s, -s, -s), (-s, -s, -s), (-s, s, -s), (s, s, -s)]),
        (1, 0, 0, [(s, -s, s), (s, -s, -s), (s, s, -s), (s, s, s)]),
        (-1, 0, 0, [(-s, -s, -s), (-s, -s, s), (-s, s, s), (-s, s, -s)]),
        (0, 1, 0, [(-s, s, s), (s, s, s), (s, s, -s), (-s, s, -s)]),
        (0, -1, 0, [(-s, -s, -s), (s, -s, -s), (s, -s, s), (-s, -s, s)]),
    ]:
        GL.glNormal3f(nx, ny, nz)
        v: tuple[float, float, float]
        for v in vs:
            GL.glVertex3f(*v)
    GL.glEnd()


def draw_solid_sphere(radius: float, slices: int, stacks: int) -> None:
    i: int
    for i in range(stacks):
        lat0: float = math.pi * (-0.5 + float(i) / stacks)
        lat1: float = math.pi * (-0.5 + float(i + 1) / stacks)
        s0: float = math.sin(lat0)
        c0: float = math.cos(lat0)
        s1: float = math.sin(lat1)
        c1: float = math.cos(lat1)
        GL.glBegin(GL.GL_QUAD_STRIP)
        j: int
        for j in range(slices + 1):
            lng: float = 2.0 * math.pi * float(j) / slices
            cl: float = math.cos(lng)
            sl: float = math.sin(lng)
            GL.glNormal3f(cl * c0, sl * c0, s0)
            GL.glVertex3f(radius * cl * c0, radius * sl * c0, radius * s0)
            GL.glNormal3f(cl * c1, sl * c1, s1)
            GL.glVertex3f(radius * cl * c1, radius * sl * c1, radius * s1)
        GL.glEnd()


def draw_occluder() -> None:
    GL.glColor3f(0.5, 0.25, 0.0)
    axis: int
    d: float
    for axis in range(3):
        GL.glPushMatrix()
        if axis == 0:
            GL.glScalef(30.0, 30.0, 1.0)
            for d in (50.0, -50.0):
                GL.glPushMatrix()
                GL.glTranslatef(0.0, 0.0, d)
                draw_solid_cube(10.0)
                GL.glPopMatrix()
        elif axis == 1:
            GL.glScalef(1.0, 30.0, 30.0)
            for d in (50.0, -50.0):
                GL.glPushMatrix()
                GL.glTranslatef(d, 0.0, 0.0)
                draw_solid_cube(10.0)
                GL.glPopMatrix()
        else:
            GL.glScalef(30.0, 1.0, 30.0)
            for d in (50.0, -50.0):
                GL.glPushMatrix()
                GL.glTranslatef(0.0, d, 0.0)
                draw_solid_cube(10.0)
                GL.glPopMatrix()
        GL.glPopMatrix()


def draw_sphere_at(idx: int) -> None:
    occluded: bool = False
    if state.occlusion_detection:
        passing: int = GL.glGetQueryObjectiv(
            state.query_ids[idx], GL.GL_QUERY_RESULT
        )
        if passing == 0:
            occluded = True
    if not occluded:
        draw_solid_sphere(50.0, 100, 100)


def draw_models() -> None:
    draw_occluder()

    if state.occlusion_detection or state.show_bounding_volume:
        GL.glShadeModel(GL.GL_FLAT)
        if not state.show_bounding_volume:
            GL.glDisable(GL.GL_LIGHTING)
            GL.glDisable(GL.GL_COLOR_MATERIAL)
            GL.glDisable(GL.GL_NORMALIZE)
            GL.glDepthMask(GL.GL_FALSE)
            GL.glColorMask(False, False, False, False)
        r: int
        g: int
        b: int
        for r in range(3):
            for g in range(3):
                for b in range(3):
                    if state.show_bounding_volume:
                        GL.glColor3f(r * 0.5, g * 0.5, b * 0.5)
                    GL.glPushMatrix()
                    GL.glTranslatef(
                        100.0 * r - 100.0, 100.0 * g - 100.0, 100.0 * b - 100.0
                    )
                    GL.glBeginQuery(
                        GL.GL_SAMPLES_PASSED,
                        int(state.query_ids[r * 9 + g * 3 + b]),
                    )
                    draw_solid_cube(100.0)
                    GL.glEndQuery(GL.GL_SAMPLES_PASSED)
                    GL.glPopMatrix()
        GL.glShadeModel(GL.GL_SMOOTH)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glEnable(GL.GL_NORMALIZE)
        GL.glColorMask(True, True, True, True)
        GL.glDepthMask(GL.GL_TRUE)

    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glEnable(GL.GL_TEXTURE_GEN_S)
    GL.glEnable(GL.GL_TEXTURE_GEN_T)

    for r in range(3):
        for g in range(3):
            for b in range(3):
                GL.glColor3f(r * 0.5, g * 0.5, b * 0.5)
                GL.glPushMatrix()
                GL.glTranslatef(
                    100.0 * r - 100.0, 100.0 * g - 100.0, 100.0 * b - 100.0
                )
                draw_sphere_at(r * 9 + g * 3 + b)
                GL.glPopMatrix()

    GL.glDisable(GL.GL_TEXTURE_2D)
    GL.glDisable(GL.GL_TEXTURE_GEN_S)
    GL.glDisable(GL.GL_TEXTURE_GEN_T)


def render_scene() -> None:
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    if state.window_width > state.window_height:
        ar: float = float(state.window_width) / float(state.window_height)
        GL.glFrustum(
            -ar * camera_zoom,
            ar * camera_zoom,
            -camera_zoom,
            camera_zoom,
            1.0,
            1000.0,
        )
    else:
        ar = float(state.window_height) / float(state.window_width)
        GL.glFrustum(
            -camera_zoom,
            camera_zoom,
            -ar * camera_zoom,
            ar * camera_zoom,
            1.0,
            1000.0,
        )

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GLU.gluLookAt(
        state.camera_pos[0],
        state.camera_pos[1],
        state.camera_pos[2],
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
    )
    GL.glViewport(0, 0, state.window_width, state.window_height)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    draw_models()


def _nudge_cam(axis: int, d: float) -> None:
    state.camera_pos[axis] += d


def imgui_menubar() -> None:
    # All controls live in the top menubar. Movement items run once per click
    # and show their key in the shortcut column (discovery); hold the key for
    # continuous motion.
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
    if imgui.begin_menu("Render options", True):
        occlusion_item: tuple[bool, bool] = imgui.menu_item(
            "Occlusion detection", "", state.occlusion_detection, True
        )
        if occlusion_item[0]:
            state.occlusion_detection = occlusion_item[1]
        bounding_item: tuple[bool, bool] = imgui.menu_item(
            "Show bounding volumes", "", state.show_bounding_volume, True
        )
        if bounding_item[0]:
            state.show_bounding_volume = bounding_item[1]
        help_item: tuple[bool, bool] = imgui.menu_item(
            "Show help overlay", "", state.show_menu, True
        )
        if help_item[0]:
            state.show_menu = help_item[1]
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _common.menu_action("Camera +X", "Left", lambda: _nudge_cam(0, 5.0))
        _common.menu_action("Camera -X", "Right", lambda: _nudge_cam(0, -5.0))
        _common.menu_action("Camera +Y", "Up", lambda: _nudge_cam(1, 5.0))
        _common.menu_action("Camera -Y", "Down", lambda: _nudge_cam(1, -5.0))
        _common.menu_action("Camera +Z", "Z", lambda: _nudge_cam(2, 5.0))
        _common.menu_action("Camera -Z", "Shift+Z", lambda: _nudge_cam(2, -5.0))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def setup_rc() -> None:
    state.query_ids = np.array(GL.glGenQueries(27), dtype=np.uint32)

    GL.glClearColor(0.3, 0.3, 0.3, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glDepthFunc(GL.GL_LESS)

    # Screen-door stipple pattern
    mask: np.ndarray = np.zeros(32, dtype=np.uint32)
    i: int
    for i in range(0, 32, 2):
        mask[i] = 0xAAAAAAAA
        mask[i + 1] = 0x55555555
    GL.glPolygonStipple(mask.view(np.uint8))

    GL.glShadeModel(GL.GL_SMOOTH)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glEnable(GL.GL_NORMALIZE)
    GL.glEnable(GL.GL_LIGHT0)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, ambient_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, diffuse_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)

    GL.glTexGeni(GL.GL_S, GL.GL_TEXTURE_GEN_MODE, GL.GL_OBJECT_LINEAR)
    GL.glTexGeni(GL.GL_T, GL.GL_TEXTURE_GEN_MODE, GL.GL_OBJECT_LINEAR)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)

    img: np.ndarray = np.flipud(iio.imread(os.path.join(PWD, "logo.tga")))
    shape: tuple[int, ...] = img.shape[:2]
    fmt: Constant = (
        GL.GL_RGBA if img.ndim == 3 and img.shape[2] == 4 else GL.GL_RGB
    )
    img = np.ascontiguousarray(img, dtype=np.uint8)
    state.texture_id = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, state.texture_id)
    # Bind FIRST, then set the params on this texture.  The C++ wrote
    # to texture 0 (no glGenTextures, no glBindTexture) so its param
    # order didn't matter; we have a real texture name now and the
    # params need to land on it.  Without these, min-filter defaults
    # to GL_NEAREST_MIPMAP_LINEAR -- since we don't upload mipmaps,
    # the texture is incomplete and Mesa samples black.
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    GL.glTexImage2D(
        GL.GL_TEXTURE_2D,
        0,
        fmt,
        shape[1],
        shape[0],
        0,
        fmt,
        GL.GL_UNSIGNED_BYTE,
        img,
    )

    GL.glTexGenfv(
        GL.GL_S,
        GL.GL_OBJECT_PLANE,
        np.array([1.0 / 50.0, 0.0, 0.0, -0.5], dtype=np.float32),
    )
    GL.glTexGenfv(
        GL.GL_T,
        GL.GL_OBJECT_PLANE,
        np.array([0.0, 1.0 / 50.0, 0.0, -0.5], dtype=np.float32),
    )


def change_size(w: int, h: int) -> None:
    state.window_width = w
    state.window_height = h


def on_framebuffer_size(_window: typing.Any, w: int, h: int) -> None:
    change_size(w, h)


def on_key(
    window: typing.Any, key: int, _scancode: int, action: int, mods: int
) -> None:
    # Render-option toggles (O/S/M) moved to the imgui panel; keys here
    # are navigation only.
    # Movement keys fire on PRESS or REPEAT so holding the key keeps
    # moving, matching GLUT glutSpecialFunc's auto-repeat behavior.
    is_movement: bool = key in (
        glfw.KEY_LEFT,
        glfw.KEY_RIGHT,
        glfw.KEY_UP,
        glfw.KEY_DOWN,
        glfw.KEY_X,
        glfw.KEY_Y,
        glfw.KEY_Z,
    )
    if action == glfw.PRESS:
        pass
    elif action == glfw.REPEAT and is_movement:
        pass
    else:
        return

    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)
    # Arrow keys -- matches C++ SpecialKeys.  LEFT/RIGHT moves X (note
    # the C++ inverts: LEFT increases, RIGHT decreases); UP/DOWN moves Y.
    elif key == glfw.KEY_LEFT:
        state.camera_pos[0] += 5.0
    elif key == glfw.KEY_RIGHT:
        state.camera_pos[0] -= 5.0
    elif key == glfw.KEY_UP:
        state.camera_pos[1] += 5.0
    elif key == glfw.KEY_DOWN:
        state.camera_pos[1] -= 5.0
    # x/y/z letter keys -- shift inverts direction.  Matches the
    # ProcessMenu callbacks in the C++ original.
    elif key == glfw.KEY_X:
        state.camera_pos[0] += -5.0 if (mods & glfw.MOD_SHIFT) else 5.0
    elif key == glfw.KEY_Y:
        state.camera_pos[1] += -5.0 if (mods & glfw.MOD_SHIFT) else 5.0
    elif key == glfw.KEY_Z:
        state.camera_pos[2] += -5.0 if (mods & glfw.MOD_SHIFT) else 5.0


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 5)
    window: typing.Any = glfw.create_window(
        state.window_width,
        state.window_height,
        "Occlusion Query Demo",
        None,
        None,
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
    # callback that doesn't chain, so navigation/Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    setup_rc()
    size: tuple[int, int] = glfw.get_framebuffer_size(window)
    change_size(size[0], size[1])

    # FPS reporter.  C++ updates every 100 frames, but at Python
    # immediate-mode rates (a handful of fps with 540k triangles), 100
    # frames takes 20+ seconds and feels frozen.  Report on a 1-second
    # wall-clock cadence instead so the user sees the number quickly.
    frames: int = 0
    frame_timer: float = time.monotonic()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        render_scene()
        imgui.new_frame()
        imgui_menubar()
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

        frames += 1
        now: float = time.monotonic()
        if now - frame_timer >= 1.0:
            fps: float = frames / (now - frame_timer)
            label: str = "with" if state.occlusion_detection else "without"
            glfw.set_window_title(
                window,
                f"Draw scene {label} occlusion detection {fps:.1f} fps",
            )
            frames = 0
            frame_timer = now

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
