# planets.py
# OpenGL selection mode (glRenderMode(GL_SELECT) + glPushName) demo.
# Click on a planet and the window title changes to identify it.
# OpenGL SuperBible, Chapter 12
# Python port of Planets.c by Richard S. Wright Jr.

import os
import sys

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


SUN, MERCURY, VENUS, EARTH, MARS = 1, 2, 3, 4, 5
PLANET_NAMES = {SUN: "Sun", MERCURY: "Mercury", VENUS: "Venus",
                EARTH: "Earth", MARS: "Mars"}
BUFFER_LENGTH = 64


def draw_sphere(radius: float) -> None:
    obj = GLU.gluNewQuadric()
    GLU.gluQuadricNormals(obj, GLU.GLU_SMOOTH)
    GLU.gluSphere(obj, radius, 26, 13)
    GLU.gluDeleteQuadric(obj)


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, -300.0)

    GL.glInitNames()
    GL.glPushName(0)

    GL.glColor3f(1.0, 1.0, 0.0)
    GL.glLoadName(SUN)
    draw_sphere(15.0)

    for color, distance, radius, name in [
        ((0.5, 0.0, 0.0), 24.0, 2.0, MERCURY),
        ((0.5, 0.5, 1.0), 60.0, 4.0, VENUS),
        ((0.0, 0.0, 1.0), 100.0, 8.0, EARTH),
        ((1.0, 0.0, 0.0), 150.0, 4.0, MARS),
    ]:
        GL.glColor3f(*color)
        GL.glPushMatrix()
        GL.glTranslatef(distance, 0.0, 0.0)
        GL.glLoadName(name)
        draw_sphere(radius)
        GL.glPopMatrix()

    GL.glPopMatrix()


def process_selection(window, x_pos: float, y_pos: float) -> None:
    select_buff = np.zeros(BUFFER_LENGTH, dtype=np.uint32)
    GL.glSelectBuffer(BUFFER_LENGTH, select_buff)
    viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)

    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glPushMatrix()
    GL.glRenderMode(GL.GL_SELECT)
    GL.glLoadIdentity()
    GLU.gluPickMatrix(
        x_pos, viewport[3] - y_pos + viewport[1], 2, 2, viewport,
    )
    f_aspect = float(viewport[2]) / float(viewport[3])
    GLU.gluPerspective(45.0, f_aspect, 1.0, 425.0)

    render_scene()

    hits = GL.glRenderMode(GL.GL_RENDER)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glPopMatrix()
    GL.glMatrixMode(GL.GL_MODELVIEW)

    if hits == 1:
        # In the selection buffer the format per hit is:
        # [name_count, z_min, z_max, name0, name1, ...]
        planet_id = int(select_buff[3])
        name = PLANET_NAMES.get(planet_id, "?")
        glfw.set_window_title(window, f"You clicked on {name}!")
    else:
        glfw.set_window_title(window, "Nothing was clicked on!")


def setup_rc() -> None:
    dim_light = (0.1, 0.1, 0.1, 1.0)
    source_light = (0.65, 0.65, 0.65, 1.0)
    light_pos = (0.0, 0.0, 0.0, 1.0)

    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, dim_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, source_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glEnable(GL.GL_LIGHT0)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glClearColor(0.60, 0.60, 0.60, 1.0)


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


def on_mouse_button(window, button: int, action: int, _mods: int) -> None:
    if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
        x_pos, y_pos = glfw.get_cursor_pos(window)
        process_selection(window, x_pos, y_pos)


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window = glfw.create_window(800, 600, "Pick a Planet", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_mouse_button_callback(window, on_mouse_button)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        render_scene()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
