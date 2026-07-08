# vbo.py
# Same Thunderbird as chapt11/thundergl, but the body and glass are
# uploaded to GL_ARRAY_BUFFER VBOs once at setup and drawn via
# glDrawElements (with parallel index buffers). The C++ original used
# the CVBOMesh helper class; here we expand the mesh into per-vertex
# arrays (one position, one normal, one texcoord per index) so it can
# be drawn with a flat index list.
# OpenGL SuperBible, Chapter 11
# Python port of thundergl.cpp + body.cpp + glass.cpp using VBOs.

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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import _common  # noqa: E402
from _thunderbird_data import load_model  # noqa: E402

PWD = os.path.dirname(os.path.abspath(__file__))

_window = None  # set in main(); used by the Quit menu item

x_rot: float = 0.0
y_rot: float = 0.0

texture_objects = [0, 0, 0]
BODY_TEXTURE, GLASS_TEXTURE, CUBE_MAP = 0, 1, 2
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

# VBO state
body_vbos = {"vert": 0, "norm": 0, "tex": 0, "count": 0}
glass_vbos = {"vert": 0, "norm": 0, "tex": 0, "count": 0}


def expand_mesh(
    face_indices: np.ndarray,
    vertices: np.ndarray,
    normals: np.ndarray,
    textures: np.ndarray,
) -> "tuple[np.ndarray, np.ndarray, np.ndarray]":
    """The C++ data has separate index streams for verts/normals/texs;
    GL VBOs need one parallel stream per attribute. Expand the
    `face_indices` table (3 vertices x 9 indices each) into per-vertex
    flat arrays."""
    n_faces = face_indices.shape[0]
    n_verts = n_faces * 3
    out_v = np.empty((n_verts, 3), dtype=np.float32)
    out_n = np.empty((n_verts, 3), dtype=np.float32)
    out_t = np.empty((n_verts, 2), dtype=np.float32)
    k = 0
    for face in face_indices:
        for i in range(3):
            out_v[k] = vertices[face[i]]
            out_n[k] = normals[face[i + 3]]
            out_t[k] = textures[face[i + 6]]
            k += 1
    return out_v, out_n, out_t


def make_vbos(
    verts: np.ndarray, norms: np.ndarray, texs: np.ndarray
) -> "dict[str, int]":
    vbo_v = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo_v)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, verts.nbytes, verts, GL.GL_STATIC_DRAW)

    vbo_n = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo_n)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, norms.nbytes, norms, GL.GL_STATIC_DRAW)

    vbo_t = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo_t)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, texs.nbytes, texs, GL.GL_STATIC_DRAW)

    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    return {"vert": vbo_v, "norm": vbo_n, "tex": vbo_t, "count": verts.shape[0]}


def draw_vbos(vbos: "dict[str, int]") -> None:
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbos["vert"])
    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    GL.glVertexPointer(3, GL.GL_FLOAT, 0, None)

    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbos["norm"])
    GL.glEnableClientState(GL.GL_NORMAL_ARRAY)
    GL.glNormalPointer(GL.GL_FLOAT, 0, None)

    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbos["tex"])
    GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
    GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, None)

    GL.glDrawArrays(GL.GL_TRIANGLES, 0, vbos["count"])

    GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
    GL.glDisableClientState(GL.GL_NORMAL_ARRAY)
    GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)


def load_cube_map() -> int:
    """Load the 6 pos_x/neg_x/... TGA files into a single cube-map
    texture used by draw_sky_box()."""
    tex = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, tex)
    for p in [
        (GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR),
        (GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR),
        (GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE),
        (GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE),
        (GL.GL_TEXTURE_WRAP_R, GL.GL_CLAMP_TO_EDGE),
    ]:
        GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, p[0], p[1])
    for i, fname in enumerate(cube_faces):
        img = np.flipud(iio.imread(os.path.join(PWD, fname)))
        h, w = img.shape[:2]
        fmt = GL.GL_RGBA if img.ndim == 3 and img.shape[2] == 4 else GL.GL_RGB
        img = np.ascontiguousarray(img, dtype=np.uint8)
        GL.glTexImage2D(
            cube_targets[i], 0, fmt, w, h, 0, fmt, GL.GL_UNSIGNED_BYTE, img
        )
    return tex


def draw_sky_box() -> None:
    """50x50x50 cube around the camera, textured directly from the
    cube map (no texgen).  Same approach as chapt11/thundergl --
    background that surrounds the scene.  Drawn before the plane so
    the plane writes on top of it.  Uses TU0 with TEXTURE_CUBE_MAP
    since this demo doesn't use multi-texturing for reflection."""
    e = 50.0
    faces = [
        # -X
        ((-1, -1, 1), (-e, -e, e)),
        ((-1, -1, -1), (-e, -e, -e)),
        ((-1, 1, -1), (-e, e, -e)),
        ((-1, 1, 1), (-e, e, e)),
        # +X
        ((1, -1, -1), (e, -e, -e)),
        ((1, -1, 1), (e, -e, e)),
        ((1, 1, 1), (e, e, e)),
        ((1, 1, -1), (e, e, -e)),
        # -Z
        ((-1, -1, -1), (-e, -e, -e)),
        ((1, -1, -1), (e, -e, -e)),
        ((1, 1, -1), (e, e, -e)),
        ((-1, 1, -1), (-e, e, -e)),
        # +Z
        ((1, -1, 1), (e, -e, e)),
        ((-1, -1, 1), (-e, -e, e)),
        ((-1, 1, 1), (-e, e, e)),
        ((1, 1, 1), (e, e, e)),
        # +Y
        ((-1, 1, 1), (-e, e, e)),
        ((-1, 1, -1), (-e, e, -e)),
        ((1, 1, -1), (e, e, -e)),
        ((1, 1, 1), (e, e, e)),
        # -Y
        ((-1, -1, -1), (-e, -e, -e)),
        ((-1, -1, 1), (-e, -e, e)),
        ((1, -1, 1), (e, -e, e)),
        ((1, -1, -1), (e, -e, -e)),
    ]
    GL.glBegin(GL.GL_QUADS)
    for tc, v in faces:
        GL.glTexCoord3f(*tc)
        GL.glVertex3f(*v)
    GL.glEnd()


def load_texture(path: str) -> int:
    img = np.flipud(iio.imread(path))
    h, w = img.shape[:2]
    fmt = GL.GL_RGBA if img.ndim == 3 and img.shape[2] == 4 else GL.GL_RGB
    img = np.ascontiguousarray(img, dtype=np.uint8)
    tex = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
    GL.glTexImage2D(
        GL.GL_TEXTURE_2D, 0, fmt, w, h, 0, fmt, GL.GL_UNSIGNED_BYTE, img
    )
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    return tex


def setup_rc() -> None:
    global body_vbos, glass_vbos
    f_amb = (0.1, 0.1, 0.1, 0.0)
    f_diff = (1.0, 1.0, 1.0, 0.0)
    f_spec = (0.5, 0.5, 0.5, 0.0)
    light_pos = (-100.0, 100.0, 100.0, 1.0)

    GL.glClearColor(0.0, 0.0, 0.5, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)

    texture_objects[BODY_TEXTURE] = load_texture(os.path.join(PWD, "body.tga"))
    texture_objects[GLASS_TEXTURE] = load_texture(
        os.path.join(PWD, "glass.tga")
    )
    texture_objects[CUBE_MAP] = load_cube_map()

    GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, f_amb)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, f_amb)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, f_diff)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, f_spec)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    # Keep specular highlights from being dimmed by the body/glass
    # texture colors (matches the C++ SetupRC).
    GL.glLightModeli(
        GL.GL_LIGHT_MODEL_COLOR_CONTROL, GL.GL_SEPARATE_SPECULAR_COLOR
    )
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

    model = load_model(PWD)
    bv, bn, bt = expand_mesh(
        model["face_indices"],
        model["vertices"],
        model["normals"],
        model["textures"],
    )
    gv, gn, gt = expand_mesh(
        model["face_indices_glass"],
        model["vertices_glass"],
        model["normals_glass"],
        model["textures_glass"],
    )

    body_vbos = make_vbos(bv, bn, bt)
    glass_vbos = make_vbos(gv, gn, gt)


def render_scene() -> None:
    f_scale = 0.01
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    # Sky box first, in world space (before the plane's translate/rotate).
    # Bind the cube map on TU0, disable lighting/depth so the background
    # just paints, then turn 2D back on for the plane.
    GL.glDisable(GL.GL_TEXTURE_2D)
    GL.glEnable(GL.GL_TEXTURE_CUBE_MAP)
    GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, texture_objects[CUBE_MAP])
    GL.glDisable(GL.GL_LIGHTING)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_DECAL)
    GL.glColor4f(1.0, 1.0, 1.0, 1.0)
    draw_sky_box()
    GL.glDisable(GL.GL_TEXTURE_CUBE_MAP)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
    GL.glEnable(GL.GL_TEXTURE_2D)

    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, -3.0)
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    # body.cpp and glass.cpp use different native coordinate systems:
    # body needs -90 X to be drawn upright, glass is already upright
    # and needs a small translate to sit on top of the cockpit.  User
    # rotations above apply to both as a rigid body; per-mesh fixups
    # are local to each draw block.

    GL.glPushMatrix()
    GL.glRotatef(-90.0, 1.0, 0.0, 0.0)
    GL.glScalef(f_scale, f_scale, f_scale)
    GL.glColor4f(1.0, 1.0, 1.0, 1.0)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_objects[BODY_TEXTURE])
    draw_vbos(body_vbos)
    GL.glPopMatrix()

    GL.glTranslatef(0.0, 0.132, 0.555)
    GL.glScalef(f_scale, f_scale, f_scale)
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glColor4f(1.0, 1.0, 1.0, 0.5)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_objects[GLASS_TEXTURE])
    GL.glFrontFace(GL.GL_CW)
    draw_vbos(glass_vbos)
    GL.glFrontFace(GL.GL_CCW)
    draw_vbos(glass_vbos)
    GL.glDisable(GL.GL_BLEND)

    GL.glPopMatrix()
    GL.glDisable(GL.GL_TEXTURE_2D)


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


# Per-click step for the menubar rotation items (the keyboard, held, rotates
# continuously via handle_special_keys; a menu click does one fixed step).
BTN_ROT_STEP: float = 5.0


def _rot_x(d: float) -> None:
    global x_rot
    x_rot += d


def _rot_y(d: float) -> None:
    global y_rot
    y_rot += d


def imgui_menubar() -> None:
    # All controls in the top menubar. Rotation items run once per click and
    # show their key in the shortcut column; hold the key for continuous spin.
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action(
            "Quit", "Esc", lambda: glfw.set_window_should_close(_window, True)
        )
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _common.menu_action("Rotate up", "Up", lambda: _rot_x(-BTN_ROT_STEP))
        _common.menu_action("Rotate down", "Down", lambda: _rot_x(BTN_ROT_STEP))
        _common.menu_action(
            "Rotate left", "Left", lambda: _rot_y(-BTN_ROT_STEP)
        )
        _common.menu_action(
            "Rotate right", "Right", lambda: _rot_y(BTN_ROT_STEP)
        )
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    global _window
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window = glfw.create_window(
        800, 600, "OpenGL ThunderBird w/ VBOs", None, None
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
