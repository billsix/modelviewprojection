# sphereworld.py
# Sphereworld with textured ground (grass), spheres (orb), and a torus
# (wood). The chapt09 version is essentially the chapt08 sphereworld;
# the chapter focuses on advanced texturing techniques covered by the
# other chapt09 demos (cubemap, multitexture, etc.).
# OpenGL SuperBible, Chapter 9
# Python port of SphereWorld.cpp by Richard S. Wright Jr.

import math
import os
import random
import sys
import time

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

from modelviewprojection.mathutils import Vector3, plane_equation

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402
import _primitives  # noqa: E402

_window = None  # set in main(); used by the Quit menu item

NUM_SPHERES = 30
sphere_positions = []
camera_x: float = 0.0
camera_y: float = 0.0
camera_z: float = 0.0
camera_yaw: float = 0.0

f_light_pos = (-100.0, 100.0, 50.0, 1.0)
f_no_light = (0.0, 0.0, 0.0, 0.0)
f_low_light = (0.25, 0.25, 0.25, 1.0)
f_bright_light = (1.0, 1.0, 1.0, 1.0)

GROUND_TEXTURE, TORUS_TEXTURE, SPHERE_TEXTURE = 0, 1, 2
texture_files = ["grass.tga", "wood.tga", "orb.tga"]
texture_objects = [0, 0, 0]

shadow_mat = None
y_rot: float = 0.0


def make_planar_shadow_matrix(
    pn: Vector3, pd: float, lp: "tuple[float, float, float, float]"
) -> "np.ndarray":
    a, b, c, d = pn.coeff_e_1, pn.coeff_e_2, pn.coeff_e_3, pd
    dx, dy, dz = -lp[0], -lp[1], -lp[2]
    # CCW plane_equation can land w<0; OpenGL clips before perspective
    # divide and the shadow disappears. Negate to keep w positive.
    # See tasks/archive/2026/05/26/notes-planar-shadow-w-clipping.md.
    s = 1.0 if (a * dx + b * dy + c * dz) > 0.0 else -1.0
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
SPHERE_BIG = _primitives.build_sphere(0.3, 17, 9)
SPHERE_SMALL = _primitives.build_sphere(0.1, 17, 9)
TORUS = _primitives.build_torus(0.35, 0.15, 61, 37)
GROUND = _primitives.build_ground(
    20.0, 1.0, -0.4, tex_step=1.0 / (20.0 * 0.075)
)


def apply_camera_transform() -> None:
    GL.glRotatef(-math.degrees(camera_yaw), 0.0, 1.0, 0.0)
    GL.glTranslatef(-camera_x, -camera_y, -camera_z)


def load_textures() -> None:
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
    for i, fname in enumerate(texture_files):
        img = iio.imread(os.path.join(PWD, fname))
        img = np.flipud(img)
        h, w = img.shape[:2]
        if img.ndim == 3 and img.shape[2] == 4:
            fmt, internal = GL.GL_RGBA, GL.GL_RGBA
        else:
            fmt, internal = GL.GL_RGB, GL.GL_RGB
        img = np.ascontiguousarray(img, dtype=np.uint8)
        texture_objects[i] = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture_objects[i])
        GLU.gluBuild2DMipmaps(
            GL.GL_TEXTURE_2D, internal, w, h, fmt, GL.GL_UNSIGNED_BYTE, img
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
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_objects[GROUND_TEXTURE])
    GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
    GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
    _primitives.draw_mesh(GROUND, textured=True)


def draw_inhabitants(n_shadow: int) -> None:
    if n_shadow == 0:
        GL.glColor4f(1.0, 1.0, 1.0, 1.0)
    else:
        GL.glColor4f(0.0, 0.0, 0.0, 0.6)

    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_objects[SPHERE_TEXTURE])
    for sx, sy, sz in sphere_positions:
        GL.glPushMatrix()
        GL.glTranslatef(sx, sy, sz)
        _primitives.draw_mesh(SPHERE_BIG, textured=True)
        GL.glPopMatrix()

    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.1, -2.5)

    GL.glPushMatrix()
    GL.glRotatef(-y_rot * 2.0, 0.0, 1.0, 0.0)
    GL.glTranslatef(1.0, 0.0, 0.0)
    _primitives.draw_mesh(SPHERE_SMALL, textured=True)
    GL.glPopMatrix()

    if n_shadow == 0:
        GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, f_bright_light)

    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_objects[TORUS_TEXTURE])
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
    apply_camera_transform()
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
    GL.glMultMatrixf(shadow_mat)
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
    global shadow_mat
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

    p1, p2, p3 = (
        Vector3(0.0, -0.4, 0.0),
        Vector3(10.0, -0.4, 0.0),
        Vector3(5.0, -0.4, -5.0),
    )
    pn, pd = plane_equation(p1, p2, p3)
    shadow_mat = make_planar_shadow_matrix(pn, pd, f_light_pos)

    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, f_bright_light)
    GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)

    random.seed(0)
    for _ in range(NUM_SPHERES):
        sx = (random.randint(0, 399) - 200) * 0.1
        sz = (random.randint(0, 399) - 200) * 0.1
        sphere_positions.append((sx, 0.0, sz))

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


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


MOVE_UNITS_PER_SEC: float = 3.0
YAW_RAD_PER_SEC: float = 1.5
TORUS_DEG_PER_SEC: float = 30.0


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
    global y_rot, _window

    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    glfw.window_hint(glfw.STENCIL_BITS, 8)

    window = glfw.create_window(
        800, 600, "OpenGL SphereWorld Demo + Texture Maps", None, None
    )
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
        y_rot = (y_rot + TORUS_DEG_PER_SEC * dt) % 360.0
        render_scene()
        imgui.new_frame()
        imgui_menubar()
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    GL.glDeleteTextures(texture_objects)
    glfw.terminate()


if __name__ == "__main__":
    main()
