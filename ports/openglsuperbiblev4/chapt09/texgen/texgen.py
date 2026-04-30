# texgen.py
# Demonstrates OpenGL automatic texture coordinate generation: object
# linear, eye linear, and sphere mapping.
# OpenGL SuperBible, Chapter 9
# Python port of TexGen.cpp by Richard S. Wright Jr.

import math
import os
import sys

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer



PWD = os.path.dirname(os.path.abspath(__file__))
x_rot: float = 0.0
y_rot: float = 0.0
to_textures = [0, 0]
i_render_mode: int = 3


def draw_torus(major: float, minor: float, n_major: int, n_minor: int) -> None:
    major_step = 2.0 * math.pi / n_major
    minor_step = 2.0 * math.pi / n_minor
    for i in range(n_major):
        a0, a1 = i * major_step, (i + 1) * major_step
        x0, y0 = math.cos(a0), math.sin(a0)
        x1, y1 = math.cos(a1), math.sin(a1)
        GL.glBegin(GL.GL_TRIANGLE_STRIP)
        for j in range(n_minor + 1):
            b = j * minor_step
            cb, sb = math.cos(b), math.sin(b)
            r = minor * cb + major
            z = minor * sb
            GL.glNormal3f(x0 * cb, y0 * cb, sb)
            GL.glVertex3f(x0 * r, y0 * r, z)
            GL.glNormal3f(x1 * cb, y1 * cb, sb)
            GL.glVertex3f(x1 * r, y1 * r, z)
        GL.glEnd()


def apply_mode(mode: int) -> None:
    z_plane = [0.0, 0.0, 1.0, 0.0]
    if mode == 1:
        GL.glTexGeni(GL.GL_S, GL.GL_TEXTURE_GEN_MODE, GL.GL_OBJECT_LINEAR)
        GL.glTexGeni(GL.GL_T, GL.GL_TEXTURE_GEN_MODE, GL.GL_OBJECT_LINEAR)
        GL.glTexGenfv(GL.GL_S, GL.GL_OBJECT_PLANE, z_plane)
        GL.glTexGenfv(GL.GL_T, GL.GL_OBJECT_PLANE, z_plane)
    elif mode == 2:
        GL.glTexGeni(GL.GL_S, GL.GL_TEXTURE_GEN_MODE, GL.GL_EYE_LINEAR)
        GL.glTexGeni(GL.GL_T, GL.GL_TEXTURE_GEN_MODE, GL.GL_EYE_LINEAR)
        GL.glTexGenfv(GL.GL_S, GL.GL_EYE_PLANE, z_plane)
        GL.glTexGenfv(GL.GL_T, GL.GL_EYE_PLANE, z_plane)
    else:
        GL.glTexGeni(GL.GL_S, GL.GL_TEXTURE_GEN_MODE, GL.GL_SPHERE_MAP)
        GL.glTexGeni(GL.GL_T, GL.GL_TEXTURE_GEN_MODE, GL.GL_SPHERE_MAP)


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    # Background quad in 2D ortho space
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glPushMatrix()
    GL.glLoadIdentity()
    GLU.gluOrtho2D(0.0, 1.0, 0.0, 1.0)

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glBindTexture(GL.GL_TEXTURE_2D, to_textures[1])
    GL.glDisable(GL.GL_TEXTURE_GEN_S)
    GL.glDisable(GL.GL_TEXTURE_GEN_T)
    GL.glDepthMask(GL.GL_FALSE)

    GL.glBegin(GL.GL_QUADS)
    GL.glTexCoord2f(0.0, 0.0); GL.glVertex2f(0.0, 0.0)
    GL.glTexCoord2f(1.0, 0.0); GL.glVertex2f(1.0, 0.0)
    GL.glTexCoord2f(1.0, 1.0); GL.glVertex2f(1.0, 1.0)
    GL.glTexCoord2f(0.0, 1.0); GL.glVertex2f(0.0, 1.0)
    GL.glEnd()

    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glPopMatrix()
    GL.glMatrixMode(GL.GL_MODELVIEW)

    GL.glEnable(GL.GL_TEXTURE_GEN_S)
    GL.glEnable(GL.GL_TEXTURE_GEN_T)
    GL.glDepthMask(GL.GL_TRUE)

    if i_render_mode != 3:
        GL.glBindTexture(GL.GL_TEXTURE_2D, to_textures[0])

    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, -2.0)
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    draw_torus(0.35, 0.15, 61, 37)
    GL.glPopMatrix()


def setup_rc() -> None:
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glClearColor(1.0, 1.0, 1.0, 1.0)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_DECAL)

    for i, fname in enumerate(["stripes.tga", "Environment.tga"]):
        img = np.flipud(iio.imread(os.path.join(PWD, fname)))
        h, w = img.shape[:2]
        fmt = (GL.GL_RGBA if img.ndim == 3 and img.shape[2] == 4
               else GL.GL_RGB)
        img = np.ascontiguousarray(img, dtype=np.uint8)
        to_textures[i] = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, to_textures[i])
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, fmt, w, h, 0, fmt,
                        GL.GL_UNSIGNED_BYTE, img)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER,
                           GL.GL_LINEAR)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER,
                           GL.GL_LINEAR)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S,
                           GL.GL_REPEAT)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T,
                           GL.GL_REPEAT)

    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glEnable(GL.GL_TEXTURE_GEN_S)
    GL.glEnable(GL.GL_TEXTURE_GEN_T)
    apply_mode(i_render_mode)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(45.0, float(w) / float(h), 1.0, 225.0)
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


def imgui_panel() -> None:
    global i_render_mode
    imgui.begin("TexGen")
    for label, value in [("Object Linear", 1), ("Eye Linear", 2),
                         ("Sphere Map", 3)]:
        if imgui.radio_button(label, i_render_mode == value):
            i_render_mode = value
            apply_mode(i_render_mode)
    imgui.end()


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window = glfw.create_window(800, 600, "Texture Coordinate Generation",
                                None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        handle_special_keys(window)
        render_scene()
        imgui.new_frame()
        imgui_panel()
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
