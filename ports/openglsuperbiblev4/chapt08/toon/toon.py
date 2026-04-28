# toon.py
# Cell/toon shading via a 1D texture indexed by light dot normal.
# OpenGL SuperBible, Chapter 8
# Python port of Toon.cpp by Richard S. Wright Jr.

import math
import os
import sys
import time

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


v_light_dir = np.array([-1.0, 1.0, 1.0], dtype=np.float32)
y_rot: float = 0.0


def invert_matrix44(m) -> "np.ndarray":
    """Replacement for m3dInvertMatrix44. m is a flat 16-element
    column-major numpy array. Returns the inverse, also column-major."""
    mat = m.reshape((4, 4)).T  # convert column-major flat to row-major 4x4
    inv = np.linalg.inv(mat)
    return inv.T.flatten().astype(np.float32)


def transform_vector3(v, m) -> tuple:
    """m is a flat 16-element column-major matrix; v is a 3-vector,
    treated as (x, y, z, 1) when applying the rotation portion (the
    translation is subtracted by the caller)."""
    out = np.empty(3, dtype=np.float32)
    out[0] = m[0]*v[0] + m[4]*v[1] + m[8]*v[2]
    out[1] = m[1]*v[0] + m[5]*v[1] + m[9]*v[2]
    out[2] = m[2]*v[0] + m[6]*v[1] + m[10]*v[2]
    return out


def normalize3(v):
    n = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
    if n != 0.0:
        return v / n
    return v


def toon_draw_torus(major_radius: float, minor_radius: float,
                    num_major: int, num_minor: int,
                    light_dir) -> None:
    # Get current modelview, invert to bring the light into object space
    model = np.array(GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX),
                     dtype=np.float32).flatten()
    inverted = invert_matrix44(model)
    new_light = transform_vector3(light_dir, inverted)
    new_light[0] -= inverted[12]
    new_light[1] -= inverted[13]
    new_light[2] -= inverted[14]
    new_light = normalize3(new_light)

    major_step = 2.0 * math.pi / num_major
    minor_step = 2.0 * math.pi / num_minor

    for i in range(num_major):
        a0 = i * major_step
        a1 = a0 + major_step
        x0, y0 = math.cos(a0), math.sin(a0)
        x1, y1 = math.cos(a1), math.sin(a1)

        GL.glBegin(GL.GL_TRIANGLE_STRIP)
        for j in range(num_minor + 1):
            b = j * minor_step
            cb = math.cos(b)
            r = minor_radius * cb + major_radius
            z = minor_radius * math.sin(b)

            n0 = np.array([x0 * cb, y0 * cb, z / minor_radius],
                          dtype=np.float32)
            n0 = normalize3(n0)
            GL.glTexCoord1f(float(np.dot(new_light, n0)))
            GL.glVertex3f(x0 * r, y0 * r, z)

            n1 = np.array([x1 * cb, y1 * cb, z / minor_radius],
                          dtype=np.float32)
            n1 = normalize3(n1)
            GL.glTexCoord1f(float(np.dot(new_light, n1)))
            GL.glVertex3f(x1 * r, y1 * r, z)
        GL.glEnd()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, -2.5)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    toon_draw_torus(0.35, 0.15, 50, 25, v_light_dir)
    GL.glPopMatrix()


def setup_rc() -> None:
    # 1D toon texture: 4 shades of green
    toon_table = np.array(
        [[0, 32, 0], [0, 64, 0], [0, 127, 0], [0, 127, 0]],
        dtype=np.uint8,
    )
    GL.glClearColor(0.0, 0.0, 0.5, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_DECAL)
    GL.glTexParameteri(GL.GL_TEXTURE_1D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_1D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_1D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP)
    GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
    GL.glTexImage1D(GL.GL_TEXTURE_1D, 0, GL.GL_RGB, 4, 0, GL.GL_RGB,
                    GL.GL_UNSIGNED_BYTE, toon_table)
    GL.glEnable(GL.GL_TEXTURE_1D)


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


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


TICK_INTERVAL: float = 33.0 / 1000.0


def tick() -> None:
    global y_rot
    y_rot += 0.5


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    
    window_width, window_height = _common.resolve_default_window_size()

    window = glfw.create_window(window_width, window_height, "Toon/Cell Shading Demo", None, None)
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

    last_tick = time.monotonic()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        now = time.monotonic()
        if now - last_tick >= TICK_INTERVAL:
            tick()
            last_tick = now
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
