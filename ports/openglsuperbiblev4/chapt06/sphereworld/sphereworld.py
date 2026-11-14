# sphereworld.py
# Sphereworld with multisampling, fog, transparent stencil-tested
# planar shadows, and lighting.
# OpenGL SuperBible, Chapter 6
# Python port of SphereWorld.c by Richard S. Wright Jr.

import dataclasses
import math
import os
import random
import sys
import time
import typing

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from gacalc.g3 import Vector
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

from modelviewprojection.mathutils import plane_equation

PWD: str = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402
import _primitives  # noqa: E402


@dataclasses.dataclass
class AppState:
    """The app's mutable state; the one instance is ``state`` below."""

    # glfw window handle; set in main() for Quit item
    window: typing.Any = None

    sphere_positions: list[tuple[float, float, float]] = dataclasses.field(
        default_factory=list
    )

    camera_x: float = 0.0
    camera_z: float = 0.0
    camera_yaw: float = 0.0

    shadow_mat: np.ndarray | None = None
    y_rot: float = 0.0


state: AppState = AppState()

NUM_SPHERES: int = 30
camera_y: float = 0.0

f_light_pos: tuple[float, float, float, float] = (-100.0, 100.0, 50.0, 1.0)
f_no_light: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
f_low_light: tuple[float, float, float, float] = (0.25, 0.25, 0.25, 1.0)
f_bright_light: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)


def make_planar_shadow_matrix(
    plane_normal: Vector,
    plane_d: float,
    light_pos_4: "tuple[float, float, float, float]",
) -> "np.ndarray":
    a: float = plane_normal.coeff_e_1
    b: float = plane_normal.coeff_e_2
    c: float = plane_normal.coeff_e_3
    d: float = plane_d
    dx: float = -light_pos_4[0]
    dy: float = -light_pos_4[1]
    dz: float = -light_pos_4[2]
    # CCW plane_equation can land w<0; OpenGL clips before perspective
    # divide and the shadow disappears. Negate to keep w positive.
    # See tasks/archive/2026/05/26/notes-planar-shadow-w-clipping.md.
    sign: float = 1.0 if (a * dx + b * dy + c * dz) > 0.0 else -1.0
    return np.array(
        [
            sign * (b * dy + c * dz),
            sign * -a * dy,
            sign * -a * dz,
            0.0,
            sign * -b * dx,
            sign * (a * dx + c * dz),
            sign * -b * dz,
            0.0,
            sign * -c * dx,
            sign * -c * dy,
            sign * (a * dx + b * dy),
            0.0,
            sign * -d * dx,
            sign * -d * dy,
            sign * -d * dz,
            sign * (a * dx + b * dy + c * dz),
        ],
        dtype=np.float32,
    )


# Geometry is identical every frame, so build the vertex bands once at import
# and replay them in draw_inhabitants / render_scene instead of re-running the
# sin/cos loops on every draw. 30 spheres + a torus, each drawn twice per frame
# (the shadow pass), were the bulk of the per-frame CPU cost.
SPHERE_BIG: _primitives.Mesh = _primitives.build_sphere(0.3, 21, 11)
SPHERE_SMALL: _primitives.Mesh = _primitives.build_sphere(0.1, 21, 11)
TORUS: _primitives.Mesh = _primitives.build_torus(0.35, 0.15, 61, 37)
GROUND: _primitives.Mesh = _primitives.build_ground(20.0, 1.0, -0.4)


def apply_camera_transform() -> None:
    GL.glRotatef(-math.degrees(state.camera_yaw), 0.0, 1.0, 0.0)
    GL.glTranslatef(-state.camera_x, -camera_y, -state.camera_z)


def draw_inhabitants(n_shadow: int) -> None:
    if n_shadow != 0:
        # Transparent shadow
        GL.glColor4f(0.0, 0.0, 0.0, 0.5)

    if n_shadow == 0:
        GL.glColor3f(0.0, 1.0, 0.0)

    sx: float
    sy: float
    sz: float
    for sx, sy, sz in state.sphere_positions:
        GL.glPushMatrix()
        GL.glTranslatef(sx, sy, sz)
        _primitives.draw_mesh(SPHERE_BIG)
        GL.glPopMatrix()

    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.1, -2.5)

    if n_shadow == 0:
        GL.glColor3f(0.0, 0.0, 1.0)

    GL.glPushMatrix()
    GL.glRotatef(-state.y_rot * 2.0, 0.0, 1.0, 0.0)
    GL.glTranslatef(1.0, 0.0, 0.0)
    _primitives.draw_mesh(SPHERE_SMALL)
    GL.glPopMatrix()

    if n_shadow == 0:
        GL.glColor3f(1.0, 0.0, 0.0)
        GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, f_bright_light)

    GL.glRotatef(state.y_rot, 0.0, 1.0, 0.0)
    _primitives.draw_mesh(TORUS)
    GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, f_no_light)
    GL.glPopMatrix()


def render_scene() -> None:
    GL.glClear(
        GL.GL_COLOR_BUFFER_BIT
        | GL.GL_DEPTH_BUFFER_BIT
        | GL.GL_STENCIL_BUFFER_BIT
    )

    GL.glPushMatrix()
    apply_camera_transform()
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, f_light_pos)

    # Ground
    GL.glColor3f(0.60, 0.40, 0.10)
    _primitives.draw_mesh(GROUND)

    # Shadows -- transparent and stencil-clipped to draw each pixel only once
    GL.glDisable(GL.GL_DEPTH_TEST)
    GL.glDisable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glEnable(GL.GL_STENCIL_TEST)
    GL.glPushMatrix()
    GL.glMultMatrixf(state.shadow_mat)
    draw_inhabitants(1)
    GL.glPopMatrix()
    GL.glDisable(GL.GL_STENCIL_TEST)
    GL.glDisable(GL.GL_BLEND)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_DEPTH_TEST)

    draw_inhabitants(0)

    GL.glPopMatrix()


def setup_rc() -> None:

    GL.glEnable(GL.GL_MULTISAMPLE)
    GL.glClearColor(*f_low_light)

    # Stencil setup -- writes once per shadow pixel
    GL.glStencilOp(GL.GL_INCR, GL.GL_INCR, GL.GL_INCR)
    GL.glClearStencil(0)
    GL.glStencilFunc(GL.GL_EQUAL, 0x0, 0x01)

    # Fog
    GL.glEnable(GL.GL_FOG)
    GL.glFogfv(GL.GL_FOG_COLOR, f_low_light)
    GL.glFogi(GL.GL_FOG_MODE, GL.GL_LINEAR)
    GL.glFogf(GL.GL_FOG_START, 5.0)
    GL.glFogf(GL.GL_FOG_END, 30.0)
    GL.glHint(GL.GL_FOG_HINT, GL.GL_NICEST)

    GL.glCullFace(GL.GL_BACK)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_DEPTH_TEST)

    GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, f_no_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, f_low_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, f_bright_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, f_bright_light)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_LIGHT0)

    p1: Vector = Vector(0.0, -0.4, 0.0)
    p2: Vector = Vector(10.0, -0.4, 0.0)
    p3: Vector = Vector(5.0, -0.4, -5.0)
    plane: tuple[Vector, float] = plane_equation(p1, p2, p3)
    state.shadow_mat = make_planar_shadow_matrix(
        plane[0], plane[1], f_light_pos
    )

    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)

    random.seed(0)
    for _ in range(NUM_SPHERES):
        sx: float = (random.randint(0, 399) - 200) * 0.1
        sz: float = (random.randint(0, 399) - 200) * 0.1
        state.sphere_positions.append((sx, 0.0, sz))


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    f_aspect: float = float(w) / float(h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(35.0, f_aspect, 1.0, 50.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window: typing.Any, w: int, h: int) -> None:
    change_size(w, h)


MOVE_UNITS_PER_SEC: float = 3.0
YAW_RAD_PER_SEC: float = 1.5
TORUS_DEG_PER_SEC: float = 30.0


def handle_camera_keys(window: typing.Any, dt: float) -> None:
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


# Per-click step for the menubar movement items (the keyboard, held, moves
# continuously via handle_camera_keys; a menu click does one fixed step).
BTN_MOVE_STEP: float = 0.5
BTN_YAW_STEP: float = 0.1


def _walk(direction: int) -> None:
    m: float = BTN_MOVE_STEP * direction
    state.camera_x += -m * math.sin(state.camera_yaw)
    state.camera_z += -m * math.cos(state.camera_yaw)


def _turn(d: float) -> None:
    state.camera_yaw += d


def imgui_menubar() -> None:
    # All controls in the top menubar. Movement items run once per click and
    # show their key in the shortcut column; hold the key for continuous motion.
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
    if imgui.begin_menu("Controls", True):
        _common.menu_action("Forward", "Up", lambda: _walk(1))
        _common.menu_action("Back", "Down", lambda: _walk(-1))
        _common.menu_action("Turn left", "Left", lambda: _turn(BTN_YAW_STEP))
        _common.menu_action("Turn right", "Right", lambda: _turn(-BTN_YAW_STEP))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:

    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    glfw.window_hint(glfw.STENCIL_BITS, 8)
    glfw.window_hint(glfw.SAMPLES, 4)

    window: typing.Any = glfw.create_window(  # glfw window handle
        800, 600, "OpenGL SphereWorld Demo + Lights and Shadow", None, None
    )
    if not window:
        glfw.terminate()
        sys.exit(1)
    state.window = window

    glfw.make_context_current(window)
    glfw.swap_interval(1)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl: GlfwRenderer = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw key
    # callback that doesn't chain, so navigation/Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    setup_rc()
    size: tuple[int, int] = glfw.get_framebuffer_size(window)
    change_size(size[0], size[1])

    last_frame: float = time.monotonic()

    while not glfw.window_should_close(window):
        now: float = time.monotonic()
        dt: float = now - last_frame
        last_frame = now

        glfw.poll_events()
        impl.process_inputs()
        handle_camera_keys(window, dt)
        state.y_rot = (state.y_rot + TORUS_DEG_PER_SEC * dt) % 360.0
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
