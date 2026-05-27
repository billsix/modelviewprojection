# thundergl.py
# The Thunderbird with a cube-map environment reflection applied to
# the body (chrome-like). Uses two texture units: unit 0 for the body
# decal, unit 1 for the cube-map reflection via texgen.
# OpenGL SuperBible, Chapter 11
# Python port of thundergl.cpp by Richard S. Wright Jr.

import math
import os
import sys
import time

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _thunderbird_data import load_model  # noqa: E402



PWD = os.path.dirname(os.path.abspath(__file__))
x_rot: float = 0.0
y_rot: float = 0.0

CUBE_MAP, BODY_TEXTURE, GLASS_TEXTURE = 0, 1, 2
texture_objects = [0, 0, 0]
cube_faces = ["pos_x.tga", "neg_x.tga", "pos_y.tga", "neg_y.tga",
              "pos_z.tga", "neg_z.tga"]
cube_targets = [
    GL.GL_TEXTURE_CUBE_MAP_POSITIVE_X, GL.GL_TEXTURE_CUBE_MAP_NEGATIVE_X,
    GL.GL_TEXTURE_CUBE_MAP_POSITIVE_Y, GL.GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
    GL.GL_TEXTURE_CUBE_MAP_POSITIVE_Z, GL.GL_TEXTURE_CUBE_MAP_NEGATIVE_Z,
]


def draw_body(model: "dict[str, np.ndarray]") -> None:
    fi = model["face_indices"]
    verts = model["vertices"]
    norms = model["normals"]
    texs = model["textures"]
    GL.glBegin(GL.GL_TRIANGLES)
    for face in fi:
        for i in range(3):
            GL.glMultiTexCoord2fv(GL.GL_TEXTURE0, texs[face[i + 6]])
            GL.glNormal3fv(norms[face[i + 3]])
            GL.glVertex3fv(verts[face[i]])
    GL.glEnd()


def draw_glass(model: "dict[str, np.ndarray]") -> None:
    fi = model["face_indices_glass"]
    verts = model["vertices_glass"]
    norms = model["normals_glass"]
    texs = model["textures_glass"]
    GL.glBegin(GL.GL_TRIANGLES)
    for face in fi:
        for i in range(3):
            GL.glTexCoord2fv(texs[face[i + 6]])
            GL.glNormal3fv(norms[face[i + 3]])
            GL.glVertex3fv(verts[face[i]])
    GL.glEnd()


def load_2d_texture(path: str) -> int:
    img = np.flipud(iio.imread(path))
    h, w = img.shape[:2]
    fmt = (GL.GL_RGBA if img.ndim == 3 and img.shape[2] == 4
           else GL.GL_RGB)
    img = np.ascontiguousarray(img, dtype=np.uint8)
    tex = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, fmt, w, h, 0, fmt,
                    GL.GL_UNSIGNED_BYTE, img)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    return tex


def draw_sky_box() -> None:
    """50x50x50 cube around the camera, textured directly from the
    cube map (no texgen) so the user sees the environment as the
    background.  The C++ samples TU1 with manual 3D texcoords
    matching each vertex's direction from origin."""
    e = 50.0
    # (texcoord, vertex) for each of 24 quad vertices, six faces.
    faces = [
        # -X
        ((-1, -1,  1), (-e, -e,  e)), ((-1, -1, -1), (-e, -e, -e)),
        ((-1,  1, -1), (-e,  e, -e)), ((-1,  1,  1), (-e,  e,  e)),
        # +X
        (( 1, -1, -1), ( e, -e, -e)), (( 1, -1,  1), ( e, -e,  e)),
        (( 1,  1,  1), ( e,  e,  e)), (( 1,  1, -1), ( e,  e, -e)),
        # -Z
        ((-1, -1, -1), (-e, -e, -e)), (( 1, -1, -1), ( e, -e, -e)),
        (( 1,  1, -1), ( e,  e, -e)), ((-1,  1, -1), (-e,  e, -e)),
        # +Z
        (( 1, -1,  1), ( e, -e,  e)), ((-1, -1,  1), (-e, -e,  e)),
        ((-1,  1,  1), (-e,  e,  e)), (( 1,  1,  1), ( e,  e,  e)),
        # +Y
        ((-1,  1,  1), (-e,  e,  e)), ((-1,  1, -1), (-e,  e, -e)),
        (( 1,  1, -1), ( e,  e, -e)), (( 1,  1,  1), ( e,  e,  e)),
        # -Y
        ((-1, -1, -1), (-e, -e, -e)), ((-1, -1,  1), (-e, -e,  e)),
        (( 1, -1,  1), ( e, -e,  e)), (( 1, -1, -1), ( e, -e, -e)),
    ]
    GL.glBegin(GL.GL_QUADS)
    for tc, v in faces:
        GL.glMultiTexCoord3f(GL.GL_TEXTURE1, *tc)
        GL.glVertex3f(*v)
    GL.glEnd()


def load_cube_map() -> int:
    tex = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, tex)
    for p in [(GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR),
              (GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR),
              (GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE),
              (GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE),
              (GL.GL_TEXTURE_WRAP_R, GL.GL_CLAMP_TO_EDGE)]:
        GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, p[0], p[1])
    for i, fname in enumerate(cube_faces):
        img = np.flipud(iio.imread(os.path.join(PWD, fname)))
        h, w = img.shape[:2]
        fmt = (GL.GL_RGBA if img.ndim == 3 and img.shape[2] == 4
               else GL.GL_RGB)
        img = np.ascontiguousarray(img, dtype=np.uint8)
        GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_GENERATE_MIPMAP,
                           GL.GL_TRUE)
        GL.glTexImage2D(cube_targets[i], 0, fmt, w, h, 0, fmt,
                        GL.GL_UNSIGNED_BYTE, img)
    return tex


def setup_rc() -> None:
    f_amb = (0.1, 0.1, 0.1, 0.0)
    f_diff = (1.0, 1.0, 1.0, 0.0)
    f_spec = (0.5, 0.5, 0.5, 0.0)
    light_pos = (-100.0, 100.0, 100.0, 1.0)

    GL.glClearColor(0.0, 0.0, 0.5, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glEnable(GL.GL_CULL_FACE)

    texture_objects[CUBE_MAP] = load_cube_map()
    texture_objects[BODY_TEXTURE] = load_2d_texture(
        os.path.join(PWD, "body.tga"))
    texture_objects[GLASS_TEXTURE] = load_2d_texture(
        os.path.join(PWD, "glass.tga"))

    GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, f_amb)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, f_amb)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, f_diff)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, f_spec)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    # Keep specular highlights from being dimmed by the body/glass
    # texture colors (matches the C++ SetupRC).
    GL.glLightModeli(GL.GL_LIGHT_MODEL_COLOR_CONTROL,
                     GL.GL_SEPARATE_SPECULAR_COLOR)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_LIGHT0)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    # Default material specular is black -- the C++ sets it to the
    # diffuse-light value so highlights actually appear.
    GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, f_diff)
    GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)

    # render_scene does glScalef(0.01) which also scales normals; without
    # rescaling, dot(N, L) collapses to ~1% and the plane is nearly black.
    # The C++ pre-scaled the geometry; here it's faster to keep glScalef
    # and just enable RESCALE_NORMAL.
    GL.glEnable(GL.GL_RESCALE_NORMAL)


def render_scene() -> None:
    f_scale = 0.01
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    # Sky box first, in world space (before the plane's translate/rotate).
    # Uses TU1 directly with manual texcoords; TU0's 2D off, TU1's texgen
    # off, env mode = DECAL so lighting doesn't tint it.
    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glDisable(GL.GL_TEXTURE_2D)
    GL.glActiveTexture(GL.GL_TEXTURE1)
    GL.glEnable(GL.GL_TEXTURE_CUBE_MAP)
    GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, texture_objects[CUBE_MAP])
    GL.glDisable(GL.GL_TEXTURE_GEN_S)
    GL.glDisable(GL.GL_TEXTURE_GEN_T)
    GL.glDisable(GL.GL_TEXTURE_GEN_R)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_DECAL)
    draw_sky_box()

    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, -3.0)
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    # body.cpp and glass.cpp use different native coordinate systems:
    # body needs -90 X to be drawn upright, glass is already upright
    # and needs a small translate to sit on top of the cockpit.  User
    # rotations above apply to both as a rigid body; per-mesh fixups
    # are local to each draw block.

    model = load_model(PWD)

    # Body: TU0 = body decal, TU1 = cube map reflection (texgen)
    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_objects[BODY_TEXTURE])
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_DECAL)

    GL.glActiveTexture(GL.GL_TEXTURE1)
    GL.glEnable(GL.GL_TEXTURE_CUBE_MAP)
    GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, texture_objects[CUBE_MAP])
    GL.glTexGeni(GL.GL_S, GL.GL_TEXTURE_GEN_MODE, GL.GL_REFLECTION_MAP)
    GL.glTexGeni(GL.GL_T, GL.GL_TEXTURE_GEN_MODE, GL.GL_REFLECTION_MAP)
    GL.glTexGeni(GL.GL_R, GL.GL_TEXTURE_GEN_MODE, GL.GL_REFLECTION_MAP)
    GL.glEnable(GL.GL_TEXTURE_GEN_S)
    GL.glEnable(GL.GL_TEXTURE_GEN_T)
    GL.glEnable(GL.GL_TEXTURE_GEN_R)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)

    GL.glPushMatrix()
    GL.glRotatef(-90.0, 1.0, 0.0, 0.0)
    GL.glScalef(f_scale, f_scale, f_scale)
    GL.glColor4f(1.0, 1.0, 1.0, 1.0)
    draw_body(model)
    GL.glPopMatrix()

    # Disable second unit for the glass
    GL.glDisable(GL.GL_TEXTURE_GEN_S)
    GL.glDisable(GL.GL_TEXTURE_GEN_T)
    GL.glDisable(GL.GL_TEXTURE_GEN_R)
    GL.glDisable(GL.GL_TEXTURE_CUBE_MAP)

    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_objects[GLASS_TEXTURE])
    GL.glTranslatef(0.0, 0.132, 0.555)
    GL.glScalef(f_scale, f_scale, f_scale)
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glColor4f(1.0, 1.0, 1.0, 0.5)
    GL.glFrontFace(GL.GL_CW)
    draw_glass(model)
    GL.glFrontFace(GL.GL_CCW)
    draw_glass(model)
    GL.glDisable(GL.GL_BLEND)

    GL.glPopMatrix()


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(35.0, float(w) / float(h), 1.0, 1000.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


ROT_DEG_PER_SEC: float = 90.0


def handle_special_keys(window, dt: float) -> None:
    global x_rot, y_rot
    step = ROT_DEG_PER_SEC * dt
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        x_rot -= step
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        x_rot += step
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        y_rot -= step
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        y_rot += step


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window = glfw.create_window(800, 600,
                                "Thunderbird w/ Cube Map Reflection",
                                None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    glfw.make_context_current(window)
    glfw.swap_interval(1)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    last_frame = time.monotonic()

    while not glfw.window_should_close(window):
        now = time.monotonic()
        dt = now - last_frame
        last_frame = now

        glfw.poll_events()
        handle_special_keys(window, dt)
        render_scene()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
