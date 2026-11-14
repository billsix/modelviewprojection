# sphereworld.py
# Sphereworld with textured ground (grass), spheres (orb), and a torus
# (wood). Same shadow + lighting approach as chapt06/sphereworld.
# OpenGL SuperBible, Chapter 8
# Python port of SphereWorld.cpp by Richard S. Wright Jr.

import dataclasses
import math
import os
import random
import sys
import time
import typing

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from gacalc.g3 import Vector
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer
from OpenGL.constant import Constant

from modelviewprojection.mathutils import plane_equation

PWD: str = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402
import _primitives  # noqa: E402

NUM_SPHERES: int = 30


@dataclasses.dataclass
class AppState:
    """The app's mutable state; the one instance is ``state`` below."""

    sphere_positions: list[tuple[float, float, float]] = dataclasses.field(
        default_factory=list
    )

    # Walk-around camera (demo22-style), replacing the old yaw-only
    # camera_x/y/z/yaw globals. Params tuned for this ~6-unit ground scene: a
    # low eye height, a slight downward tilt, and gentle move/scroll speeds.
    camera: _common.Camera = dataclasses.field(
        default_factory=lambda: _common.Camera(
            position=[0.0, 0.5, 6.0],
            rot_x=math.radians(-5.0),
            move_speed=0.2,
            scroll_speed=0.5,
            focus_radius=4.0,
        )
    )
    win_state: _common.WindowState = dataclasses.field(
        default_factory=_common.WindowState
    )

    texture_objects: list[int] = dataclasses.field(
        default_factory=lambda: [0, 0, 0]
    )

    shadow_mat: np.ndarray | None = None
    y_rot: float = 0.0


state: AppState = AppState()


def torus_orbiter_position() -> tuple[float, float, float]:
    # The small sphere orbits the central torus at radius 1 (see
    # draw_inhabitants); expose its live world position so the camera's
    # focus mode can track it while it moves.
    angle: float = math.radians(-state.y_rot * 2.0)
    return (math.cos(angle), 0.1, -2.5 - math.sin(angle))


scene_objects: list[_common.SceneObject] = [
    _common.SceneObject("Torus (center)", lambda: (0.0, 0.1, -2.5)),
    _common.SceneObject("Torus orbiter", torus_orbiter_position),
    _common.SceneObject("Ground center", lambda: (0.0, -0.4, 0.0)),
]

f_light_pos: tuple[float, float, float, float] = (-100.0, 100.0, 50.0, 1.0)
f_no_light: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
f_low_light: tuple[float, float, float, float] = (0.25, 0.25, 0.25, 1.0)
f_bright_light: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)

GROUND_TEXTURE: int = 0
TORUS_TEXTURE: int = 1
SPHERE_TEXTURE: int = 2
texture_files: list[str] = ["grass.tga", "wood.tga", "orb.tga"]


def make_planar_shadow_matrix(
    pn: Vector, pd: float, lp: "tuple[float, float, float, float]"
) -> "np.ndarray":
    a: float = pn.coeff_e_1
    b: float = pn.coeff_e_2
    c: float = pn.coeff_e_3
    d: float = pd
    dx: float = -lp[0]
    dy: float = -lp[1]
    dz: float = -lp[2]
    # CCW plane_equation can land w<0; OpenGL clips before perspective
    # divide and the shadow disappears. Negate to keep w positive.
    # See tasks/archive/2026/05/26/notes-planar-shadow-w-clipping.md.
    s: float = 1.0 if (a * dx + b * dy + c * dz) > 0.0 else -1.0
    return np.array(
        [
            s * (b * dy + c * dz),
            s * -a * dy,
            s * -a * dz,
            0.0,
            s * -b * dx,
            s * (a * dx + c * dz),
            s * -b * dz,
            0.0,
            s * -c * dx,
            s * -c * dy,
            s * (a * dx + b * dy),
            0.0,
            s * -d * dx,
            s * -d * dy,
            s * -d * dz,
            s * (a * dx + b * dy + c * dz),
        ],
        dtype=np.float32,
    )


# Geometry is identical every frame, so build the vertex bands once at import
# and replay them (textured) in draw_inhabitants / draw_ground instead of
# re-running the sin/cos loops on every draw.
SPHERE_BIG: _primitives.Mesh = _primitives.build_sphere(0.3, 21, 11)
SPHERE_SMALL: _primitives.Mesh = _primitives.build_sphere(0.1, 21, 11)
TORUS: _primitives.Mesh = _primitives.build_torus(0.35, 0.15, 61, 37)
GROUND: _primitives.Mesh = _primitives.build_ground(
    20.0, 1.0, -0.4, tex_step=1.0 / (20.0 * 0.075)
)


def load_textures() -> None:
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
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
        state.texture_objects[i] = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, state.texture_objects[i])
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


def draw_ground() -> None:
    # The texture binding + wrap mode stay in the per-frame path; only the
    # grid geometry is precomputed (GROUND).
    GL.glBindTexture(GL.GL_TEXTURE_2D, state.texture_objects[GROUND_TEXTURE])
    GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
    GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
    _primitives.draw_mesh(GROUND, textured=True)


def draw_inhabitants(n_shadow: int) -> None:
    if n_shadow == 0:
        GL.glColor4f(1.0, 1.0, 1.0, 1.0)
    else:
        GL.glColor4f(0.0, 0.0, 0.0, 0.6)

    GL.glBindTexture(GL.GL_TEXTURE_2D, state.texture_objects[SPHERE_TEXTURE])
    sx: float
    sy: float
    sz: float
    for sx, sy, sz in state.sphere_positions:
        GL.glPushMatrix()
        GL.glTranslatef(sx, sy, sz)
        _primitives.draw_mesh(SPHERE_BIG, textured=True)
        GL.glPopMatrix()

    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.1, -2.5)

    GL.glPushMatrix()
    GL.glRotatef(-state.y_rot * 2.0, 0.0, 1.0, 0.0)
    GL.glTranslatef(1.0, 0.0, 0.0)
    _primitives.draw_mesh(SPHERE_SMALL, textured=True)
    GL.glPopMatrix()

    if n_shadow == 0:
        GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, f_bright_light)

    GL.glRotatef(state.y_rot, 0.0, 1.0, 0.0)
    GL.glBindTexture(GL.GL_TEXTURE_2D, state.texture_objects[TORUS_TEXTURE])
    _primitives.draw_mesh(TORUS, textured=True)
    GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, f_no_light)
    GL.glPopMatrix()


def render_scene() -> None:
    GL.glClear(
        GL.GL_COLOR_BUFFER_BIT
        | GL.GL_DEPTH_BUFFER_BIT
        | GL.GL_STENCIL_BUFFER_BIT
    )

    GL.glPushMatrix()
    _common.apply_camera(state.camera, scene_objects)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, f_light_pos)

    GL.glColor3f(1.0, 1.0, 1.0)
    draw_ground()

    GL.glDisable(GL.GL_DEPTH_TEST)
    GL.glDisable(GL.GL_LIGHTING)
    GL.glDisable(GL.GL_TEXTURE_2D)
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
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glEnable(GL.GL_DEPTH_TEST)

    draw_inhabitants(0)
    GL.glPopMatrix()


def setup_rc() -> None:
    GL.glClearColor(*f_low_light)
    GL.glStencilOp(GL.GL_INCR, GL.GL_INCR, GL.GL_INCR)
    GL.glClearStencil(0)
    GL.glStencilFunc(GL.GL_EQUAL, 0x0, 0x01)

    GL.glCullFace(GL.GL_BACK)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glEnable(GL.GL_MULTISAMPLE)

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
    GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, f_bright_light)
    GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)

    random.seed(0)
    for _ in range(NUM_SPHERES):
        sx: float = (random.randint(0, 399) - 200) * 0.1
        sz: float = (random.randint(0, 399) - 200) * 0.1
        state.sphere_positions.append((sx, 0.0, sz))

    load_textures()


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(35.0, float(w) / float(h), 1.0, 50.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window: typing.Any, w: int, h: int) -> None:
    change_size(w, h)


TORUS_DEG_PER_SEC: float = 30.0


def on_key(
    window: typing.Any, key: int, _scancode: int, action: int, _mods: int
) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def main() -> None:

    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    glfw.window_hint(glfw.STENCIL_BITS, 8)

    window: typing.Any = glfw.create_window(  # glfw window handle
        800, 600, "OpenGL SphereWorld Demo + Texture Maps", None, None
    )
    if not window:
        glfw.terminate()
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.swap_interval(1)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl: GlfwRenderer = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw key
    # callback that doesn't chain, so navigation/Esc must be registered last.
    glfw.set_key_callback(window, on_key)
    # Chain the camera's scroll handler off imgui's (installed by GlfwRenderer).
    _common.bind_camera_inputs(window, state.camera)

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
        _common.update_camera(window, state.camera, scene_objects)
        state.y_rot = (state.y_rot + TORUS_DEG_PER_SEC * dt) % 360.0
        render_scene()
        imgui.new_frame()
        _common.draw_menubar(
            window,
            state.win_state,
            controls=lambda: _common.draw_camera_controls(
                state.camera, scene_objects
            ),
        )
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    GL.glDeleteTextures(state.texture_objects)
    glfw.terminate()


if __name__ == "__main__":
    main()
