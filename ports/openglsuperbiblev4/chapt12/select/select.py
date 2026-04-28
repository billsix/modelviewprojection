# select.py
# Selection plus feedback mode: clicking on the torus or sphere
# selects it, then GL_FEEDBACK is used to compute the screen-space
# bounding rectangle, which is drawn around the object.
# OpenGL SuperBible, Chapter 12
# Python port of Select.cpp by Richard S. Wright Jr.

import math
import os
import sys
from typing import List

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


TORUS, SPHERE = 1, 2
BUFFER_LENGTH = 64
FEED_BUFF_SIZE = 32768

bounding_rect: List[int] = [0, 0, 0, 0]  # top, bottom, left, right
selected_object: int = 0
f_aspect: float = 1.0


def draw_torus(num_major: int, num_minor: int) -> None:
    major_radius = 0.35
    minor_radius = 0.15
    major_step = 2.0 * math.pi / num_major
    minor_step = 2.0 * math.pi / num_minor
    GL.glEnable(GL.GL_NORMALIZE)
    for i in range(num_major):
        a0, a1 = i * major_step, (i + 1) * major_step
        x0, y0 = math.cos(a0), math.sin(a0)
        x1, y1 = math.cos(a1), math.sin(a1)
        GL.glBegin(GL.GL_TRIANGLE_STRIP)
        for j in range(num_minor + 1):
            b = j * minor_step
            cb = math.cos(b)
            r = minor_radius * cb + major_radius
            z = minor_radius * math.sin(b)
            GL.glTexCoord2f(float(i) / num_major, float(j) / num_minor)
            GL.glNormal3f(x0 * cb, y0 * cb, z / minor_radius)
            GL.glVertex3f(x0 * r, y0 * r, z)
            GL.glTexCoord2f(float(i + 1) / num_major,
                            float(j) / num_minor)
            GL.glNormal3f(x1 * cb, y1 * cb, z / minor_radius)
            GL.glVertex3f(x1 * r, y1 * r, z)
        GL.glEnd()
    GL.glDisable(GL.GL_NORMALIZE)


def draw_sphere(radius: float) -> None:
    obj = GLU.gluNewQuadric()
    GLU.gluQuadricNormals(obj, GLU.GLU_SMOOTH)
    GLU.gluSphere(obj, radius, 26, 13)
    GLU.gluDeleteQuadric(obj)


def draw_objects() -> None:
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glPushMatrix()
    GL.glTranslatef(-0.75, 0.0, -2.5)
    GL.glInitNames()
    GL.glPushName(0)

    GL.glColor3f(1.0, 1.0, 0.0)
    GL.glLoadName(TORUS)
    GL.glPassThrough(float(TORUS))
    draw_torus(40, 20)

    GL.glColor3f(0.5, 0.0, 0.0)
    GL.glTranslatef(1.5, 0.0, 0.0)
    GL.glLoadName(SPHERE)
    GL.glPassThrough(float(SPHERE))
    draw_sphere(0.5)

    GL.glPopMatrix()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    draw_objects()

    if selected_object != 0:
        viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glOrtho(viewport[0], viewport[2], viewport[3], viewport[1],
                   -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glDisable(GL.GL_LIGHTING)
        GL.glColor3f(1.0, 0.0, 0.0)
        GL.glBegin(GL.GL_LINE_LOOP)
        GL.glVertex2i(bounding_rect[2], bounding_rect[0])  # left, top
        GL.glVertex2i(bounding_rect[2], bounding_rect[1])  # left, bottom
        GL.glVertex2i(bounding_rect[3], bounding_rect[1])  # right, bottom
        GL.glVertex2i(bounding_rect[3], bounding_rect[0])  # right, top
        GL.glEnd()
        GL.glEnable(GL.GL_LIGHTING)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_MODELVIEW)


def make_selection(n_choice: int) -> None:
    global bounding_rect
    bounding_rect = [999999, -999999, 999999, -999999]  # top, bottom, left, right

    feed_buff = np.zeros(FEED_BUFF_SIZE, dtype=np.float32)
    GL.glFeedbackBuffer(FEED_BUFF_SIZE, GL.GL_2D, feed_buff)
    GL.glRenderMode(GL.GL_FEEDBACK)
    draw_objects()
    size = GL.glRenderMode(GL.GL_RENDER)

    i = 0
    while i < size:
        if feed_buff[i] == GL.GL_PASS_THROUGH_TOKEN:
            if int(feed_buff[i + 1]) == n_choice:
                i += 2
                while i < size and feed_buff[i] != GL.GL_PASS_THROUGH_TOKEN:
                    if feed_buff[i] == GL.GL_POLYGON_TOKEN:
                        i += 1
                        count = int(feed_buff[i])
                        i += 1
                        for _ in range(count):
                            x = int(feed_buff[i])
                            if x > bounding_rect[3]:
                                bounding_rect[3] = x
                            if x < bounding_rect[2]:
                                bounding_rect[2] = x
                            i += 1
                            y = int(feed_buff[i])
                            if y > bounding_rect[1]:
                                bounding_rect[1] = y
                            if y < bounding_rect[0]:
                                bounding_rect[0] = y
                            i += 1
                    else:
                        i += 1
                break
        i += 1


def process_selection(x_pos: float, y_pos: float) -> None:
    global selected_object
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
    GLU.gluPerspective(60.0, f_aspect, 1.0, 425.0)
    draw_objects()
    hits = GL.glRenderMode(GL.GL_RENDER)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glPopMatrix()
    GL.glMatrixMode(GL.GL_MODELVIEW)

    if hits == 1:
        choice = int(select_buff[3])
        make_selection(choice)
        if selected_object == choice:
            selected_object = 0
        else:
            selected_object = choice


def setup_rc() -> None:
    dim_light = (0.1, 0.1, 0.1, 1.0)
    source_light = (0.65, 0.65, 0.65, 1.0)
    light_pos = (0.0, 0.0, 0.0, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, dim_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, source_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glEnable(GL.GL_LIGHT0)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glClearColor(0.60, 0.60, 0.60, 1.0)
    GL.glLineWidth(2.0)


def change_size(w: int, h: int) -> None:
    global f_aspect
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    f_aspect = float(w) / float(h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(60.0, f_aspect, 1.0, 425.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_mouse_button(window, button: int, action: int, _mods: int) -> None:
    if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
        x_pos, y_pos = glfw.get_cursor_pos(window)
        process_selection(x_pos, y_pos)


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window = glfw.create_window(800, 600, "Select an Object", None, None)
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
