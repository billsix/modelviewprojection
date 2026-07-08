# Block.py
# OpenGL SuperBible, Chapter 1
# Demonstrates an assortment of basic 3D concepts
# Python port of Block.cpp by Richard S. Wright Jr.
#
# Press SPACE to advance through 6 stages:
#   0  wireframe cube
#   1  wireframe cube with hidden-line removal (manual)
#   2  solid uniform-colored cube (looks 2D / goofy)
#   3  same cube with lighting
#   4  cube with lighting + planar shadow on the floor
#   5  textured cube with planar shadow on the textured floor

import os
import sys

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

from modelviewprojection.mathutils import Vector3, plane_equation

STAGE_LABELS = (
    "0  Wireframe cube",
    "1  Wireframe cube + hidden-line removal",
    "2  Solid uniform-colored cube",
    "3  Solid cube + lighting",
    "4  Lit cube + planar shadow",
    "5  Textured cube + textured floor + shadow",
)


# Keep track of effects step
n_step: int = 0

# Lighting data
light_ambient = (0.2, 0.2, 0.2, 1.0)
light_diffuse = (0.7, 0.7, 0.7, 1.0)
light_specular = (0.9, 0.9, 0.9, 1.0)
material_color = (0.8, 0.0, 0.0, 1.0)
v_light_pos = (-80.0, 120.0, 100.0, 0.0)

# Three points defining the ground plane (used to derive the plane
# equation for the planar-shadow projection)
ground = [
    Vector3(0.0, -25.0, 0.0),
    Vector3(10.0, -25.0, 0.0),
    Vector3(10.0, -25.0, -10.0),
]

textures = [0, 0, 0, 0]
window_width: int = 800
window_height: int = 600

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

_window = None  # set in main(); used by the Controls buttons


# ---------------------------------------------------------------------------
# Planar shadow matrix
#
# Inline here because the demo uses fixed-function `glMultMatrixf` and
# pyMatrixStack's planar_shadow (Tier-1 task #3) hasn't landed yet. The
# plane-equation helper, however, now lives in mathutils.py (Tier-1
# task #5) and is imported above.
# ---------------------------------------------------------------------------


def make_planar_shadow_matrix(
    plane_normal: Vector3,
    plane_d: float,
    light_pos: "tuple[float, float, float, float]",
) -> "np.ndarray":
    """4x4 column-major shadow projection matrix that "squishes"
    geometry onto the plane along rays from light_pos. Mirrors
    m3dMakePlanarShadowMatrix in math3d.cpp. Note that this matrix
    is rank 3 (not invertible) -- it is the pedagogical example of a
    transform that is NOT a Cayley graph edge.

    Negation note: the bottom-right entry below is the w of every
    transformed vertex (rows 0-2 of column 3 are 0). Two homogeneous
    points (p, w) and (-p, -w) represent the same 3D point after
    perspective divide -- but OpenGL clips on w *before* the divide,
    discarding everything with w<0. SuperBible's plane equation uses
    CW winding so w lands positive; mvp's plane_equation uses CCW so
    w lands negative and the shadow gets clipped away. We negate the
    whole matrix when needed to keep w positive."""
    a, b, c = (
        plane_normal.coeff_e_1,
        plane_normal.coeff_e_2,
        plane_normal.coeff_e_3,
    )
    d = plane_d
    dx, dy, dz = -light_pos[0], -light_pos[1], -light_pos[2]
    sign = 1.0 if (a * dx + b * dy + c * dz) > 0.0 else -1.0
    return np.array(
        [
            # column 0
            sign * (b * dy + c * dz),
            sign * -a * dy,
            sign * -a * dz,
            0.0,
            # column 1
            sign * -b * dx,
            sign * (a * dx + c * dz),
            sign * -b * dz,
            0.0,
            # column 2
            sign * -c * dx,
            sign * -c * dy,
            sign * (a * dx + b * dy),
            0.0,
            # column 3
            sign * -d * dx,
            sign * -d * dy,
            sign * -d * dz,
            sign * (a * dx + b * dy + c * dz),
        ],
        dtype=np.float32,
    )


# ---------------------------------------------------------------------------
# Inline replacements for glutSolidCube / glutWireCube
# ---------------------------------------------------------------------------


def draw_solid_cube(size: float) -> None:
    s = size / 2.0
    GL.glBegin(GL.GL_QUADS)
    # +Z
    GL.glNormal3f(0.0, 0.0, 1.0)
    GL.glVertex3f(-s, -s, s)
    GL.glVertex3f(s, -s, s)
    GL.glVertex3f(s, s, s)
    GL.glVertex3f(-s, s, s)
    # -Z
    GL.glNormal3f(0.0, 0.0, -1.0)
    GL.glVertex3f(s, -s, -s)
    GL.glVertex3f(-s, -s, -s)
    GL.glVertex3f(-s, s, -s)
    GL.glVertex3f(s, s, -s)
    # +X
    GL.glNormal3f(1.0, 0.0, 0.0)
    GL.glVertex3f(s, -s, s)
    GL.glVertex3f(s, -s, -s)
    GL.glVertex3f(s, s, -s)
    GL.glVertex3f(s, s, s)
    # -X
    GL.glNormal3f(-1.0, 0.0, 0.0)
    GL.glVertex3f(-s, -s, -s)
    GL.glVertex3f(-s, -s, s)
    GL.glVertex3f(-s, s, s)
    GL.glVertex3f(-s, s, -s)
    # +Y
    GL.glNormal3f(0.0, 1.0, 0.0)
    GL.glVertex3f(-s, s, s)
    GL.glVertex3f(s, s, s)
    GL.glVertex3f(s, s, -s)
    GL.glVertex3f(-s, s, -s)
    # -Y
    GL.glNormal3f(0.0, -1.0, 0.0)
    GL.glVertex3f(-s, -s, -s)
    GL.glVertex3f(s, -s, -s)
    GL.glVertex3f(s, -s, s)
    GL.glVertex3f(-s, -s, s)
    GL.glEnd()


def draw_wire_cube(size: float) -> None:
    s = size / 2.0
    edges = [
        # Bottom face
        ((-s, -s, -s), (s, -s, -s)),
        ((s, -s, -s), (s, -s, s)),
        ((s, -s, s), (-s, -s, s)),
        ((-s, -s, s), (-s, -s, -s)),
        # Top face
        ((-s, s, -s), (s, s, -s)),
        ((s, s, -s), (s, s, s)),
        ((s, s, s), (-s, s, s)),
        ((-s, s, s), (-s, s, -s)),
        # Verticals
        ((-s, -s, -s), (-s, s, -s)),
        ((s, -s, -s), (s, s, -s)),
        ((s, -s, s), (s, s, s)),
        ((-s, -s, s), (-s, s, s)),
    ]
    GL.glBegin(GL.GL_LINES)
    for p1, p2 in edges:
        GL.glVertex3f(*p1)
        GL.glVertex3f(*p2)
    GL.glEnd()


# ---------------------------------------------------------------------------
# Texture loading (replaces gltLoadTGA)
# ---------------------------------------------------------------------------


def load_tga_texture(path: str) -> int:
    img = iio.imread(path)
    if img.ndim == 2:
        img = np.stack([img, img, img], axis=-1)
    # OpenGL expects bottom-up; imageio returns top-down
    img = np.flipud(img)
    h, w = img.shape[:2]
    channels = img.shape[2] if img.ndim == 3 else 1
    img = np.ascontiguousarray(img, dtype=np.uint8)

    tex = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
    fmt = GL.GL_RGBA if channels == 4 else GL.GL_RGB
    internal = GL.GL_RGBA8 if channels == 4 else GL.GL_RGB8
    GL.glTexImage2D(
        GL.GL_TEXTURE_2D, 0, internal, w, h, 0, fmt, GL.GL_UNSIGNED_BYTE, img
    )
    return tex


# ---------------------------------------------------------------------------
# Scene rendering
# ---------------------------------------------------------------------------


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glShadeModel(GL.GL_SMOOTH)
    GL.glEnable(GL.GL_NORMALIZE)

    GL.glPushMatrix()

    # Draw the ground plane (textured at step 5, blue otherwise)
    GL.glDisable(GL.GL_LIGHTING)
    if n_step == 5:
        GL.glColor3ub(255, 255, 255)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, textures[0])
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 0.0)
        GL.glVertex3f(-100.0, -25.3, -100.0)
        GL.glTexCoord2f(0.0, 1.0)
        GL.glVertex3f(-100.0, -25.3, 100.0)
        GL.glTexCoord2f(1.0, 1.0)
        GL.glVertex3f(100.0, -25.3, 100.0)
        GL.glTexCoord2f(1.0, 0.0)
        GL.glVertex3f(100.0, -25.3, -100.0)
        GL.glEnd()
    else:
        GL.glColor3f(0.0, 0.0, 0.90)
        GL.glBegin(GL.GL_QUADS)
        GL.glVertex3f(-100.0, -25.3, -100.0)
        GL.glVertex3f(-100.0, -25.3, 100.0)
        GL.glVertex3f(100.0, -25.3, 100.0)
        GL.glVertex3f(100.0, -25.3, -100.0)
        GL.glEnd()

    GL.glColor3f(1.0, 0.0, 0.0)

    if n_step > 2:
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDepthFunc(GL.GL_LEQUAL)
        GL.glEnable(GL.GL_COLOR_MATERIAL)

        GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, light_ambient)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, light_diffuse)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, light_specular)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_LIGHT0)
        GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, light_specular)
        GL.glMaterialfv(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE, material_color)
        GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)

    # Move the cube slightly forward and to the left
    GL.glTranslatef(-10.0, 0.0, 10.0)

    if n_step == 0:
        # Wireframe cube
        draw_wire_cube(50.0)
    elif n_step == 1:
        # Wireframe cube with hidden-line removal simulated by drawing
        # only the front three faces' edges
        GL.glBegin(GL.GL_LINES)
        # Front face (before rotation)
        GL.glVertex3f(25.0, 25.0, 25.0)
        GL.glVertex3f(25.0, -25.0, 25.0)
        GL.glVertex3f(25.0, -25.0, 25.0)
        GL.glVertex3f(-25.0, -25.0, 25.0)
        GL.glVertex3f(-25.0, -25.0, 25.0)
        GL.glVertex3f(-25.0, 25.0, 25.0)
        GL.glVertex3f(-25.0, 25.0, 25.0)
        GL.glVertex3f(25.0, 25.0, 25.0)
        GL.glEnd()
        GL.glBegin(GL.GL_LINES)
        # Top face
        GL.glVertex3f(25.0, 25.0, 25.0)
        GL.glVertex3f(25.0, 25.0, -25.0)
        GL.glVertex3f(25.0, 25.0, -25.0)
        GL.glVertex3f(-25.0, 25.0, -25.0)
        GL.glVertex3f(-25.0, 25.0, -25.0)
        GL.glVertex3f(-25.0, 25.0, 25.0)
        GL.glVertex3f(-25.0, 25.0, 25.0)
        GL.glVertex3f(25.0, 25.0, 25.0)
        GL.glEnd()
        GL.glBegin(GL.GL_LINES)
        # Last two segments
        GL.glVertex3f(25.0, 25.0, -25.0)
        GL.glVertex3f(25.0, -25.0, -25.0)
        GL.glVertex3f(25.0, -25.0, -25.0)
        GL.glVertex3f(25.0, -25.0, 25.0)
        GL.glEnd()
    elif n_step == 2:
        draw_solid_cube(50.0)
    elif n_step == 3:
        draw_solid_cube(50.0)
    elif n_step == 4:
        # Lit cube + planar shadow
        cube_transform = GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX)  # noqa: F841
        draw_solid_cube(50.0)
        GL.glPopMatrix()

        GL.glDisable(GL.GL_LIGHTING)
        GL.glPushMatrix()

        plane_normal, plane_d = plane_equation(ground[0], ground[1], ground[2])
        shadow_mat = make_planar_shadow_matrix(
            plane_normal, plane_d, v_light_pos
        )
        GL.glMultMatrixf(shadow_mat)

        GL.glTranslatef(-10.0, 0.0, 10.0)
        GL.glColor3f(0.0, 0.0, 0.0)
        draw_solid_cube(50.0)
    elif n_step == 5:
        # Textured cube + planar shadow on textured floor
        GL.glColor3ub(255, 255, 255)

        # Front face
        GL.glBindTexture(GL.GL_TEXTURE_2D, textures[1])
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(1.0, 1.0)
        GL.glVertex3f(25.0, 25.0, 25.0)
        GL.glTexCoord2f(1.0, 0.0)
        GL.glVertex3f(25.0, -25.0, 25.0)
        GL.glTexCoord2f(0.0, 0.0)
        GL.glVertex3f(-25.0, -25.0, 25.0)
        GL.glTexCoord2f(0.0, 1.0)
        GL.glVertex3f(-25.0, 25.0, 25.0)
        GL.glEnd()

        # Top face
        GL.glBindTexture(GL.GL_TEXTURE_2D, textures[2])
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 0.0)
        GL.glVertex3f(25.0, 25.0, 25.0)
        GL.glTexCoord2f(1.0, 0.0)
        GL.glVertex3f(25.0, 25.0, -25.0)
        GL.glTexCoord2f(1.0, 1.0)
        GL.glVertex3f(-25.0, 25.0, -25.0)
        GL.glTexCoord2f(0.0, 1.0)
        GL.glVertex3f(-25.0, 25.0, 25.0)
        GL.glEnd()

        # Right face
        GL.glBindTexture(GL.GL_TEXTURE_2D, textures[3])
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(1.0, 1.0)
        GL.glVertex3f(25.0, 25.0, -25.0)
        GL.glTexCoord2f(1.0, 0.0)
        GL.glVertex3f(25.0, -25.0, -25.0)
        GL.glTexCoord2f(0.0, 0.0)
        GL.glVertex3f(25.0, -25.0, 25.0)
        GL.glTexCoord2f(0.0, 1.0)
        GL.glVertex3f(25.0, 25.0, 25.0)
        GL.glEnd()

        GL.glPopMatrix()
        GL.glDisable(GL.GL_LIGHTING)
        GL.glDisable(GL.GL_TEXTURE_2D)

        GL.glPushMatrix()
        plane_normal, plane_d = plane_equation(ground[0], ground[1], ground[2])
        shadow_mat = make_planar_shadow_matrix(
            plane_normal, plane_d, v_light_pos
        )
        GL.glMultMatrixf(shadow_mat)

        GL.glTranslatef(-10.0, 0.0, 10.0)
        GL.glColor3f(0.0, 0.0, 0.0)
        draw_solid_cube(50.0)

    GL.glPopMatrix()


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)

    textures[0] = load_tga_texture(os.path.join(PWD, "floor.tga"))
    textures[1] = load_tga_texture(os.path.join(PWD, "Block4.tga"))
    textures[2] = load_tga_texture(os.path.join(PWD, "Block5.tga"))
    textures[3] = load_tga_texture(os.path.join(PWD, "Block6.tga"))


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1

    if w <= h:
        win_h = 100.0 * float(h) / float(w)
        win_w = 100.0
    else:
        win_w = 100.0 * float(w) / float(h)
        win_h = 100.0

    GL.glViewport(0, 0, w, h)

    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GL.glOrtho(-100.0, win_w, -100.0, win_h, -200.0, 200.0)

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()

    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, v_light_pos)

    GL.glRotatef(30.0, 1.0, 0.0, 0.0)
    GL.glRotatef(330.0, 0.0, 1.0, 0.0)


def on_framebuffer_size(_window, w: int, h: int) -> None:
    global window_width, window_height
    window_width, window_height = w, h
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    global n_step
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)
    elif key == glfw.KEY_SPACE and action == glfw.PRESS:
        n_step += 1
        if n_step > 5:
            n_step = 0


def _set_step(i: int) -> None:
    global n_step
    n_step = i


def imgui_menubar() -> None:
    """Top menubar. The Demo menu's radio items select the stage (SPACE
    still cycles through them as an accelerator)."""
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action(
            "Quit", "Esc", lambda: glfw.set_window_should_close(_window, True)
        )
        imgui.end_menu()
    if imgui.begin_menu("Demo", True):
        for i, label in enumerate(STAGE_LABELS):
            _common.menu_action(
                label,
                "SPACE" if i == 0 else "",
                lambda i=i: _set_step(i),
                selected=(n_step == i),
            )
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    global _window
    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(800, 600, "3D Effects Demo", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    _window = window

    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw key
    # callback that doesn't chain, so SPACE/Esc must be registered last.
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
    GL.glDeleteTextures(textures)
    glfw.terminate()


if __name__ == "__main__":
    main()
