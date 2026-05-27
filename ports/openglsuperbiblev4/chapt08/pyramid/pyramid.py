# pyramid.py
# Demonstrates simple 2D texture mapping. A textured pyramid with
# ImGui controls for texture environment mode and filtering.
# OpenGL SuperBible, Chapter 8
# Python port of Pyramid.cpp by Richard S. Wright Jr.

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

from modelviewprojection.mathutils import Vector3D, find_normal



PWD = os.path.dirname(os.path.abspath(__file__))

x_rot: float = 0.0
y_rot: float = 0.0
extra_radius: float = 0.0
texture_id: int = 0

env_mode_idx: int = 0  # 0=Modulate, 1=Replace
min_filter_idx: int = 0  # 0=Linear, 1=Nearest
mag_filter_idx: int = 0  # 0=Linear, 1=Nearest


def load_texture() -> None:
    global texture_id
    img = iio.imread(os.path.join(PWD, "stone.tga"))
    img = np.flipud(img)
    h, w = img.shape[:2]
    fmt = (GL.GL_RGBA if img.ndim == 3 and img.shape[2] == 4 else GL.GL_RGB)
    internal = GL.GL_RGBA8 if fmt == GL.GL_RGBA else GL.GL_RGB8
    img = np.ascontiguousarray(img, dtype=np.uint8)

    GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
    texture_id = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id)
    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, internal, w, h, 0, fmt,
                    GL.GL_UNSIGNED_BYTE, img)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)


def render_scene() -> None:
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S,
                       GL.GL_CLAMP_TO_EDGE)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T,
                       GL.GL_CLAMP_TO_EDGE)
    GL.glEnable(GL.GL_TEXTURE_2D)

    corners = [
        Vector3D(0.0, 0.80, 0.0),     # 0 top
        Vector3D(-0.5, 0.0, -0.50),   # 1 back-left
        Vector3D(0.5, 0.0, -0.50),    # 2 back-right
        Vector3D(0.5, 0.0, 0.5),      # 3 front-right
        Vector3D(-0.5, 0.0, 0.5),     # 4 front-left
    ]

    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glPushMatrix()
    GL.glTranslatef(0.0, -0.25, -4.0 - extra_radius)
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)

    GL.glColor3f(1.0, 1.0, 1.0)
    GL.glBegin(GL.GL_TRIANGLES)

    # Bottom -- two triangles, normal points down
    GL.glNormal3f(0.0, -1.0, 0.0)
    GL.glTexCoord2f(1.0, 1.0); GL.glVertex3f(*corners[2])
    GL.glTexCoord2f(0.0, 0.0); GL.glVertex3f(*corners[4])
    GL.glTexCoord2f(0.0, 1.0); GL.glVertex3f(*corners[1])
    GL.glTexCoord2f(1.0, 1.0); GL.glVertex3f(*corners[2])
    GL.glTexCoord2f(1.0, 0.0); GL.glVertex3f(*corners[3])
    GL.glTexCoord2f(0.0, 0.0); GL.glVertex3f(*corners[4])

    # Front, left, back, right faces -- normal computed via mathutils
    for tri in [
        (corners[0], corners[4], corners[3]),
        (corners[0], corners[1], corners[4]),
        (corners[0], corners[2], corners[1]),
        (corners[0], corners[3], corners[2]),
    ]:
        n = find_normal(*tri)
        GL.glNormal3f(n.x, n.y, n.z)
        GL.glTexCoord2f(0.5, 1.0); GL.glVertex3f(*tri[0])
        GL.glTexCoord2f(0.0, 0.0); GL.glVertex3f(*tri[1])
        GL.glTexCoord2f(1.0, 0.0); GL.glVertex3f(*tri[2])

    GL.glEnd()
    GL.glPopMatrix()


def setup_rc() -> None:
    white_light = (0.05, 0.05, 0.05, 1.0)
    source_light = (0.25, 0.25, 0.25, 1.0)
    light_pos = (-10.0, 5.0, 5.0, 1.0)

    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, white_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, source_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, source_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glEnable(GL.GL_LIGHT0)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    load_texture()


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(35.0, float(w) / float(h), 1.0, 40.0)
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


def imgui_panel() -> None:
    global env_mode_idx, min_filter_idx, mag_filter_idx, extra_radius

    imgui.begin("Set Ambient Light")

    env_modes = ["Modulate", "Replace"]
    changed, env_mode_idx = imgui.combo("Texture Env Mode", env_mode_idx,
                                        env_modes)
    if changed:
        modes = [GL.GL_MODULATE, GL.GL_REPLACE]
        GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE,
                     modes[env_mode_idx])

    filters = ["Linear", "Nearest"]
    changed, min_filter_idx = imgui.combo("Min Filter", min_filter_idx,
                                          filters)
    if changed:
        f = [GL.GL_LINEAR, GL.GL_NEAREST]
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER,
                           f[min_filter_idx])

    changed, mag_filter_idx = imgui.combo("Mag Filter", mag_filter_idx,
                                          filters)
    if changed:
        f = [GL.GL_LINEAR, GL.GL_NEAREST]
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER,
                           f[mag_filter_idx])

    _, extra_radius = imgui.slider_float("Extra Camera Radius", extra_radius,
                                         -4.0, 100.0)

    imgui.end()


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    glfw.window_hint(glfw.SAMPLES, 4)

    window = glfw.create_window(800, 600, "Textured Pyramid", None, None)
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

    glfw.swap_interval(1)
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
        imgui_panel()
        imgui.render()
        impl.render(imgui.get_draw_data())

        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
