# thunderbird.py
# Renders a hand-modeled Thunderbird airplane using indexed vertex
# arrays. The body and glass are loaded from body.cpp and glass.cpp
# (the same C++ data files the SuperBible source links into the demo)
# via the shared _thunderbird_data parser.
# OpenGL SuperBible, Chapter 11
# Python port of ThunderBird.cpp by Richard S. Wright Jr.

import math
import os
import sys

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU

# The shared loader lives one directory up
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _thunderbird_data import load_model  # noqa: E402



PWD = os.path.dirname(os.path.abspath(__file__))

x_rot: float = 0.0
y_rot: float = 0.0
texture_objects = [0, 0]
BODY_TEXTURE, GLASS_TEXTURE = 0, 1
body_list: int = 0
glass_list: int = 0

GL_TEXTURE_MAX_ANISOTROPY_EXT = 0x84FE
GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT = 0x84FF


def draw_body(model: "dict[str, np.ndarray]") -> None:
    fi = model["face_indices"]
    verts = model["vertices"]
    norms = model["normals"]
    texs = model["textures"]
    GL.glBegin(GL.GL_TRIANGLES)
    for face in fi:
        for i in range(3):
            GL.glTexCoord2fv(texs[face[i + 6]])
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
    try:
        f_largest = GL.glGetFloatv(GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT)
        GL.glTexParameterf(GL.GL_TEXTURE_2D,
                           GL_TEXTURE_MAX_ANISOTROPY_EXT, float(f_largest))
    except Exception:
        pass
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
    return tex


def setup_rc() -> None:
    global body_list, glass_list

    f_amb_light = (0.1, 0.1, 0.1, 0.0)
    f_diff_light = (1.0, 1.0, 1.0, 0.0)
    f_spec_light = (0.5, 0.5, 0.5, 0.0)
    light_pos = (-100.0, 100.0, 100.0, 1.0)

    GL.glClearColor(0.0, 0.0, 0.5, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)

    texture_objects[BODY_TEXTURE] = load_texture(os.path.join(PWD, "body.tga"))
    texture_objects[GLASS_TEXTURE] = load_texture(os.path.join(PWD, "glass.tga"))

    GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, f_amb_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, f_amb_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, f_diff_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, f_spec_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_LIGHT0)

    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)

    # Compile body and glass into display lists
    model = load_model(PWD)
    body_list = GL.glGenLists(2)
    glass_list = body_list + 1

    GL.glNewList(body_list, GL.GL_COMPILE)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_objects[BODY_TEXTURE])
    draw_body(model)
    GL.glEndList()

    GL.glNewList(glass_list, GL.GL_COMPILE)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_objects[GLASS_TEXTURE])
    draw_glass(model)
    GL.glEndList()


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
    GL.glCallList(body_list)

    # Glass is transparent
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glColor4f(1.0, 1.0, 1.0, 0.5)
    GL.glCallList(glass_list)
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
    window = glfw.create_window(800, 600, "Thunderbird", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        handle_special_keys(window)
        render_scene()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
