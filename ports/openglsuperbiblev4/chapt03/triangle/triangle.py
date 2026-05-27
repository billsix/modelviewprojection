# triangle.py
# Demonstrates triangle fans, backface culling, and depth testing.
# The C++ original used a GLUT right-click menu; replaced here with an
# ImGui control panel.
# OpenGL SuperBible, Chapter 3
# Python port of Triangle.cpp by Richard S. Wright Jr.

import math
import os
import sys
import time

import glfw
import OpenGL.GL as GL
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer



# C++ original used a truncated 3.1415; that, combined with `angle <
# 2*GL_PI` in the fan loop, dropped the closing vertex and left an open
# seam in the cone. Use math.pi and an inclusive vertex count so all
# triangles get drawn.
NUM_SEGMENTS: int = 16

x_rot: float = 0.0
y_rot: float = 0.0

i_cull: bool = False
i_outline: bool = False
i_depth: bool = False


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    if i_cull:
        GL.glEnable(GL.GL_CULL_FACE)
    else:
        GL.glDisable(GL.GL_CULL_FACE)

    if i_depth:
        GL.glEnable(GL.GL_DEPTH_TEST)
    else:
        GL.glDisable(GL.GL_DEPTH_TEST)

    # C++ original used GL_BACK so back faces would render as lines, but
    # in modern fixed-function pipelines back faces are either culled or
    # depth-discarded by the front, so GL_BACK is a visible no-op.
    # GL_FRONT_AND_BACK makes the toggle actually do something visible.
    if i_outline:
        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
    else:
        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)

    GL.glPushMatrix()
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)

    # Top of cone as a triangle fan. Loop NUM_SEGMENTS+1 times so the
    # last vertex closes the fan back to the first base vertex.
    pivot = 1
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glVertex3f(0.0, 0.0, 75.0)  # apex
    for i in range(NUM_SEGMENTS + 1):
        angle = 2.0 * math.pi * i / NUM_SEGMENTS
        x = 50.0 * math.sin(angle)
        y = 50.0 * math.cos(angle)
        if pivot % 2 == 0:
            GL.glColor3f(0.0, 1.0, 0.0)
        else:
            GL.glColor3f(1.0, 0.0, 0.0)
        pivot += 1
        GL.glVertex2f(x, y)
    GL.glEnd()

    # Bottom cap
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glVertex2f(0.0, 0.0)
    for i in range(NUM_SEGMENTS + 1):
        angle = 2.0 * math.pi * i / NUM_SEGMENTS
        x = 50.0 * math.sin(angle)
        y = 50.0 * math.cos(angle)
        if pivot % 2 == 0:
            GL.glColor3f(0.0, 1.0, 0.0)
        else:
            GL.glColor3f(1.0, 0.0, 0.0)
        pivot += 1
        GL.glVertex2f(x, y)
    GL.glEnd()

    GL.glPopMatrix()


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glColor3f(0.0, 1.0, 0.0)
    GL.glShadeModel(GL.GL_FLAT)
    # Triangle fans wind clockwise here, so flip the front-face convention
    GL.glFrontFace(GL.GL_CW)


def change_size(w: int, h: int) -> None:
    n_range = 100.0
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    if w <= h:
        GL.glOrtho(-n_range, n_range, -n_range * h / w, n_range * h / w,
                   -n_range, n_range)
    else:
        GL.glOrtho(-n_range * w / h, n_range * w / h, -n_range, n_range,
                   -n_range, n_range)
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
    global i_depth, i_cull, i_outline
    imgui.begin("Triangle")
    _, i_depth = imgui.checkbox("Depth test", i_depth)
    _, i_cull = imgui.checkbox("Cull backface", i_cull)
    _, i_outline = imgui.checkbox("Outline back", i_outline)
    imgui.end()


def main() -> None:
    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(
        800, 600, "Triangle Culling Example", None, None
    )
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
