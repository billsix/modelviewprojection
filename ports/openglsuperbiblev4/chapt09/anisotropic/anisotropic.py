# anisotropic.py
# Same tunnel as chapt08/tunnel, plus anisotropic filtering. ImGui combo
# replaces the C++ original's right-click menu.
# OpenGL SuperBible, Chapter 9
# Python port of Anisotropic.cpp by Richard S. Wright Jr.

import math
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



PWD = os.path.dirname(os.path.abspath(__file__))
TEXTURE_BRICK, TEXTURE_FLOOR, TEXTURE_CEILING = 0, 1, 2
texture_files = ["brick.tga", "floor.tga", "ceiling.tga"]
textures = [0, 0, 0]
filter_idx: int = 5
anisotropic: bool = False

# Walk-around camera. Initial position puts the camera at the tunnel
# mouth looking down -Z, matching the original z_pos=-60 view.
camera_x: float = 0.0
camera_y: float = 0.0
camera_z: float = 60.0
camera_yaw: float = 0.0


def apply_camera_transform() -> None:
    GL.glRotatef(-math.degrees(camera_yaw), 0.0, 1.0, 0.0)
    GL.glTranslatef(-camera_x, -camera_y, -camera_z)

GL_TEXTURE_MAX_ANISOTROPY_EXT = 0x84FE
GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT = 0x84FF


def load_textures() -> None:
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_DECAL)
    GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
    for i, fname in enumerate(texture_files):
        img = np.flipud(iio.imread(os.path.join(PWD, fname)))
        h, w = img.shape[:2]
        fmt = (GL.GL_RGBA if img.ndim == 3 and img.shape[2] == 4
               else GL.GL_RGB)
        img = np.ascontiguousarray(img, dtype=np.uint8)
        textures[i] = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, textures[i])
        GLU.gluBuild2DMipmaps(GL.GL_TEXTURE_2D, fmt, w, h, fmt,
                              GL.GL_UNSIGNED_BYTE, img)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER,
                           GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER,
                           GL.GL_LINEAR_MIPMAP_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S,
                           GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T,
                           GL.GL_CLAMP_TO_EDGE)


def apply_filter(idx: int, aniso: bool) -> None:
    modes = [GL.GL_NEAREST, GL.GL_LINEAR, GL.GL_NEAREST_MIPMAP_NEAREST,
             GL.GL_NEAREST_MIPMAP_LINEAR, GL.GL_LINEAR_MIPMAP_NEAREST,
             GL.GL_LINEAR_MIPMAP_LINEAR]
    f_max_aniso = 1.0
    try:
        f_max_aniso = GL.glGetFloatv(GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT)
    except Exception:
        pass
    for tex in textures:
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER,
                           modes[idx])
        try:
            if aniso:
                GL.glTexParameterf(GL.GL_TEXTURE_2D,
                                   GL_TEXTURE_MAX_ANISOTROPY_EXT,
                                   float(f_max_aniso))
            else:
                GL.glTexParameterf(GL.GL_TEXTURE_2D,
                                   GL_TEXTURE_MAX_ANISOTROPY_EXT, 1.0)
        except Exception:
            pass


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glPushMatrix()
    apply_camera_transform()
    z = 60.0
    while z >= 0.0:
        GL.glBindTexture(GL.GL_TEXTURE_2D, textures[TEXTURE_FLOOR])
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 0.0); GL.glVertex3f(-10.0, -10.0, z)
        GL.glTexCoord2f(1.0, 0.0); GL.glVertex3f(10.0, -10.0, z)
        GL.glTexCoord2f(1.0, 1.0); GL.glVertex3f(10.0, -10.0, z - 10.0)
        GL.glTexCoord2f(0.0, 1.0); GL.glVertex3f(-10.0, -10.0, z - 10.0)
        GL.glEnd()
        GL.glBindTexture(GL.GL_TEXTURE_2D, textures[TEXTURE_CEILING])
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 1.0); GL.glVertex3f(-10.0, 10.0, z - 10.0)
        GL.glTexCoord2f(1.0, 1.0); GL.glVertex3f(10.0, 10.0, z - 10.0)
        GL.glTexCoord2f(1.0, 0.0); GL.glVertex3f(10.0, 10.0, z)
        GL.glTexCoord2f(0.0, 0.0); GL.glVertex3f(-10.0, 10.0, z)
        GL.glEnd()
        GL.glBindTexture(GL.GL_TEXTURE_2D, textures[TEXTURE_BRICK])
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 0.0); GL.glVertex3f(-10.0, -10.0, z)
        GL.glTexCoord2f(1.0, 0.0); GL.glVertex3f(-10.0, -10.0, z - 10.0)
        GL.glTexCoord2f(1.0, 1.0); GL.glVertex3f(-10.0, 10.0, z - 10.0)
        GL.glTexCoord2f(0.0, 1.0); GL.glVertex3f(-10.0, 10.0, z)
        GL.glEnd()
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
    GL.glEnable(GL.GL_DEPTH_TEST)
    load_textures()


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    # 90 deg FOV (the original) fisheyes hard when the user yaws.
    # 70 deg is the standard first-person-shooter value -- wide enough
    # to feel like walking through a tunnel, narrow enough to keep
    # rotation distortion in check.
    GLU.gluPerspective(70.0, float(w) / float(h), 1.0, 120.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


MOVE_UNITS_PER_SEC: float = 10.0
YAW_RAD_PER_SEC: float = 1.5


def handle_special_keys(window, dt: float) -> None:
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


def imgui_panel() -> None:
    global filter_idx, anisotropic
    imgui.begin("Anisotropic")
    items = ["GL_NEAREST", "GL_LINEAR", "GL_NEAREST_MIPMAP_NEAREST",
             "GL_NEAREST_MIPMAP_LINEAR", "GL_LINEAR_MIPMAP_NEAREST",
             "GL_LINEAR_MIPMAP_LINEAR"]
    f_changed, filter_idx = imgui.combo("Min Filter", filter_idx, items)
    a_changed, anisotropic = imgui.checkbox("Anisotropic", anisotropic)
    if f_changed or a_changed:
        apply_filter(filter_idx, anisotropic)
    imgui.end()


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window = glfw.create_window(800, 600, "Anisotropic Tunnel", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)

    setup_rc()
    apply_filter(filter_idx, anisotropic)
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
