# solar.py
# Sun / Earth / Moon nested coordinate frames with lighting and
# perspective. Earth is in a frame relative to the sun; the moon is in
# a frame relative to the earth.
# OpenGL SuperBible, Chapter 4
# Python port of Solar.cpp by Richard S. Wright Jr.

import os
import sys
import time

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _primitives  # noqa: E402



white_light = (0.2, 0.2, 0.2, 1.0)
source_light = (0.8, 0.8, 0.8, 1.0)
light_pos = (0.0, 0.0, 0.0, 1.0)

f_moon_rot: float = 0.0
f_earth_rot: float = 0.0
# Time-based animation rates (C++ used a 100 ms timer that advanced by
# 15° / 5° per tick = 150°/sec and 50°/sec).
MOON_DEG_PER_SEC: float = 150.0
EARTH_DEG_PER_SEC: float = 50.0
start_time: float = 0.0


# Spheres are identical every frame, so build the vertex bands once at import
# and replay them in render_scene. swap_winding=True emits each latitude band
# as (lat1, lat0): that winds the camera-facing side CCW so glFrontFace(GL_CCW)
# + GL_CULL_FACE keep it. The default (lat0, lat1) order would wind it CW, cull
# the near hemisphere, and light the far one (whose normals point away from the
# sun -> no diffuse).
PLANET_SPHERE = _primitives.build_sphere(15.0, 30, 17, swap_winding=True)
MOON_SPHERE = _primitives.build_sphere(6.0, 30, 17, swap_winding=True)


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glPushMatrix()

    GL.glTranslatef(0.0, 0.0, -300.0)

    # Sun (yellow, no lighting -- it IS the light source)
    GL.glDisable(GL.GL_LIGHTING)
    GL.glColor3ub(255, 255, 0)
    _primitives.draw_mesh(PLANET_SPHERE)
    GL.glEnable(GL.GL_LIGHTING)

    # Place light at the sun's location
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)

    GL.glRotatef(f_earth_rot, 0.0, 1.0, 0.0)

    # Earth
    GL.glColor3ub(0, 0, 255)
    GL.glTranslatef(105.0, 0.0, 0.0)
    _primitives.draw_mesh(PLANET_SPHERE)

    # Moon -- in Earth's frame
    GL.glColor3ub(200, 200, 200)
    GL.glRotatef(f_moon_rot, 0.0, 1.0, 0.0)
    GL.glTranslatef(30.0, 0.0, 0.0)
    _primitives.draw_mesh(MOON_SPHERE)

    GL.glPopMatrix()


def update_animation() -> None:
    global f_earth_rot, f_moon_rot
    elapsed = time.monotonic() - start_time
    f_moon_rot = (elapsed * MOON_DEG_PER_SEC) % 360.0
    f_earth_rot = (elapsed * EARTH_DEG_PER_SEC) % 360.0


def setup_rc() -> None:
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)

    GL.glEnable(GL.GL_LIGHTING)
    GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, white_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, source_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glEnable(GL.GL_LIGHT0)

    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)

    GL.glClearColor(0.0, 0.0, 0.0, 1.0)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    f_aspect = float(w) / float(h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(45.0, f_aspect, 1.0, 425.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def main() -> None:
    global start_time

    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(800, 600, "Earth/Moon/Sun System", None, None)
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

    start_time = time.monotonic()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        update_animation()
        render_scene()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
