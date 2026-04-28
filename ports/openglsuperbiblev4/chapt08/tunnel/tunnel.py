# tunnel.py
# Mipmapping demo: a textured corridor with floor/ceiling/wall textures.
# Arrow keys move forward/back. C++ used a right-click GLUT menu for
# texture filter; replaced with an ImGui combo.
# OpenGL SuperBible, Chapter 8
# Python port of Tunnel.cpp by Richard S. Wright Jr.

import os
import sys

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


PWD = os.path.dirname(os.path.abspath(__file__))
TEXTURE_BRICK, TEXTURE_FLOOR, TEXTURE_CEILING = 0, 1, 2
texture_files = ["brick.tga", "floor.tga", "ceiling.tga"]
textures = [0, 0, 0]
z_pos: float = -60.0
filter_idx = 5  # 0..5 selects min filter mode


def load_textures() -> None:
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_DECAL)
    GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)

    for i, fname in enumerate(texture_files):
        img = iio.imread(os.path.join(PWD, fname))
        img = np.flipud(img)
        h, w = img.shape[:2]
        if img.ndim == 3 and img.shape[2] == 4:
            fmt, internal = GL.GL_RGBA, GL.GL_RGBA
        else:
            fmt, internal = GL.GL_RGB, GL.GL_RGB
        img = np.ascontiguousarray(img, dtype=np.uint8)

        textures[i] = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, textures[i])
        GLU.gluBuild2DMipmaps(GL.GL_TEXTURE_2D, internal, w, h, fmt,
                              GL.GL_UNSIGNED_BYTE, img)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER,
                           GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER,
                           GL.GL_LINEAR_MIPMAP_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S,
                           GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T,
                           GL.GL_CLAMP_TO_EDGE)


def apply_filter(idx: int) -> None:
    modes = [
        GL.GL_NEAREST, GL.GL_LINEAR,
        GL.GL_NEAREST_MIPMAP_NEAREST, GL.GL_NEAREST_MIPMAP_LINEAR,
        GL.GL_LINEAR_MIPMAP_NEAREST, GL.GL_LINEAR_MIPMAP_LINEAR,
    ]
    for tex in textures:
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER,
                           modes[idx])


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, z_pos)

    z = 60.0
    while z >= 0.0:
        # Floor
        GL.glBindTexture(GL.GL_TEXTURE_2D, textures[TEXTURE_FLOOR])
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 0.0); GL.glVertex3f(-10.0, -10.0, z)
        GL.glTexCoord2f(1.0, 0.0); GL.glVertex3f(10.0, -10.0, z)
        GL.glTexCoord2f(1.0, 1.0); GL.glVertex3f(10.0, -10.0, z - 10.0)
        GL.glTexCoord2f(0.0, 1.0); GL.glVertex3f(-10.0, -10.0, z - 10.0)
        GL.glEnd()

        # Ceiling
        GL.glBindTexture(GL.GL_TEXTURE_2D, textures[TEXTURE_CEILING])
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 1.0); GL.glVertex3f(-10.0, 10.0, z - 10.0)
        GL.glTexCoord2f(1.0, 1.0); GL.glVertex3f(10.0, 10.0, z - 10.0)
        GL.glTexCoord2f(1.0, 0.0); GL.glVertex3f(10.0, 10.0, z)
        GL.glTexCoord2f(0.0, 0.0); GL.glVertex3f(-10.0, 10.0, z)
        GL.glEnd()

        # Left wall
        GL.glBindTexture(GL.GL_TEXTURE_2D, textures[TEXTURE_BRICK])
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 0.0); GL.glVertex3f(-10.0, -10.0, z)
        GL.glTexCoord2f(1.0, 0.0); GL.glVertex3f(-10.0, -10.0, z - 10.0)
        GL.glTexCoord2f(1.0, 1.0); GL.glVertex3f(-10.0, 10.0, z - 10.0)
        GL.glTexCoord2f(0.0, 1.0); GL.glVertex3f(-10.0, 10.0, z)
        GL.glEnd()

        # Right wall
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 1.0); GL.glVertex3f(10.0, 10.0, z)
        GL.glTexCoord2f(1.0, 1.0); GL.glVertex3f(10.0, 10.0, z - 10.0)
        GL.glTexCoord2f(1.0, 0.0); GL.glVertex3f(10.0, -10.0, z - 10.0)
        GL.glTexCoord2f(0.0, 0.0); GL.glVertex3f(10.0, -10.0, z)
        GL.glEnd()

        z -= 10.0

    GL.glPopMatrix()


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    load_textures()


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(90.0, float(w) / float(h), 1.0, 120.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def handle_special_keys(window) -> None:
    global z_pos
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        z_pos += 1.0
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        z_pos -= 1.0


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def imgui_panel() -> None:
    global filter_idx
    imgui.begin("Tunnel")
    items = ["GL_NEAREST", "GL_LINEAR", "GL_NEAREST_MIPMAP_NEAREST",
             "GL_NEAREST_MIPMAP_LINEAR", "GL_LINEAR_MIPMAP_NEAREST",
             "GL_LINEAR_MIPMAP_LINEAR"]
    changed, filter_idx = imgui.combo("Min Filter", filter_idx, items)
    if changed:
        apply_filter(filter_idx)
    imgui.end()


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(800, 600, "Tunnel", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)

    setup_rc()
    apply_filter(filter_idx)
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
