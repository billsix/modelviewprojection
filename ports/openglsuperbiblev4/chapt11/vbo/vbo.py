# vbo.py
# Same Thunderbird as chapt11/thundergl, but the body and glass are
# uploaded to GL_ARRAY_BUFFER VBOs once at setup and drawn via
# glDrawElements (with parallel index buffers). The C++ original used
# the CVBOMesh helper class; here we expand the mesh into per-vertex
# arrays (one position, one normal, one texcoord per index) so it can
# be drawn with a flat index list.
# OpenGL SuperBible, Chapter 11
# Python port of thundergl.cpp + body.cpp + glass.cpp using VBOs.

import math
import os
import sys

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _thunderbird_data import load_model  # noqa: E402

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402
x_rot: float = 0.0
y_rot: float = 0.0

texture_objects = [0, 0]
BODY_TEXTURE, GLASS_TEXTURE = 0, 1

# VBO state
body_vbos = {"vert": 0, "norm": 0, "tex": 0, "count": 0}
glass_vbos = {"vert": 0, "norm": 0, "tex": 0, "count": 0}


def expand_mesh(face_indices, vertices, normals, textures):
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


def make_vbos(verts: np.ndarray, norms: np.ndarray,
              texs: np.ndarray) -> dict:
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
    return {"vert": vbo_v, "norm": vbo_n, "tex": vbo_t,
            "count": verts.shape[0]}


def draw_vbos(vbos: dict) -> None:
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


def load_texture(path: str) -> int:
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
        os.path.join(PWD, "glass.tga"))

    GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, f_amb)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, f_amb)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, f_diff)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, f_spec)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_LIGHT0)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)

    model = load_model(PWD)
    bv, bn, bt = expand_mesh(
        model["face_indices"], model["vertices"],
        model["normals"], model["textures"])
    gv, gn, gt = expand_mesh(
        model["face_indices_glass"], model["vertices_glass"],
        model["normals_glass"], model["textures_glass"])

    body_vbos = make_vbos(bv, bn, bt)
    glass_vbos = make_vbos(gv, gn, gt)


def render_scene() -> None:
    f_scale = 0.01
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glEnable(GL.GL_TEXTURE_2D)

    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, -3.0)
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    GL.glScalef(f_scale, f_scale, f_scale)

    GL.glColor4f(1.0, 1.0, 1.0, 1.0)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_objects[BODY_TEXTURE])
    draw_vbos(body_vbos)

    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glColor4f(1.0, 1.0, 1.0, 0.5)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_objects[GLASS_TEXTURE])
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


def handle_special_keys(window) -> None:
    global x_rot, y_rot
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        x_rot -= 5.0
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        x_rot += 5.0
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        y_rot -= 5.0
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        y_rot += 5.0


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    
    window_width, window_height = _common.resolve_default_window_size()
    window = glfw.create_window(window_width, window_height,
                                "OpenGL ThunderBird w/ VBOs",
                                None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    impl = _common.init_imgui(window)
    win_state = _common.WindowState()

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        handle_special_keys(window)
        render_scene()
        
        imgui.new_frame()
        _common.draw_menubar(window, win_state)
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()

    glfw.terminate()


if __name__ == "__main__":
    main()
