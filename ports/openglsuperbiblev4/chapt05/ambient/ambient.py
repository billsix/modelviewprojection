# ambient.py
# Same hand-modeled jet as chapt05/jet, but lighting is enabled with
# only an ambient light. The ambient color is editable through an
# ImGui color picker (replaces the C++ original's imgui_impl_glut UI).
# OpenGL SuperBible, Chapter 5
# Python port of Ambient.cpp by Richard S. Wright Jr.

import os
import sys
import time

import glfw
import OpenGL.GL as GL
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer



x_rot: float = 0.0
y_rot: float = 0.0
ambient_light = [1.0, 1.0, 1.0]


def draw_jet() -> None:
    """The hand-modeled jet, faithfully translated. No normals -- the
    lighting in this demo is purely ambient, so the jet looks flat-lit."""
    GL.glBegin(GL.GL_TRIANGLES)

    GL.glColor3ub(0, 255, 0)
    GL.glVertex3f(0.0, 0.0, 60.0)
    GL.glVertex3f(-15.0, 0.0, 30.0)
    GL.glVertex3f(15.0, 0.0, 30.0)

    GL.glVertex3f(15.0, 0.0, 30.0)
    GL.glVertex3f(0.0, 15.0, 30.0)
    GL.glVertex3f(0.0, 0.0, 60.0)

    GL.glVertex3f(0.0, 0.0, 60.0)
    GL.glVertex3f(0.0, 15.0, 30.0)
    GL.glVertex3f(-15.0, 0.0, 30.0)

    GL.glColor3ub(192, 192, 192)
    GL.glVertex3f(-15.0, 0.0, 30.0)
    GL.glVertex3f(0.0, 15.0, 30.0)
    GL.glVertex3f(0.0, 0.0, -56.0)

    GL.glVertex3f(0.0, 0.0, -56.0)
    GL.glVertex3f(0.0, 15.0, 30.0)
    GL.glVertex3f(15.0, 0.0, 30.0)

    GL.glVertex3f(15.0, 0.0, 30.0)
    GL.glVertex3f(-15.0, 0.0, 30.0)
    GL.glVertex3f(0.0, 0.0, -56.0)

    # Wing
    GL.glColor3ub(64, 64, 64)
    GL.glVertex3f(0.0, 2.0, 27.0)
    GL.glVertex3f(-60.0, 2.0, -8.0)
    GL.glVertex3f(60.0, 2.0, -8.0)

    GL.glVertex3f(60.0, 2.0, -8.0)
    GL.glVertex3f(0.0, 7.0, -8.0)
    GL.glVertex3f(0.0, 2.0, 27.0)

    GL.glVertex3f(60.0, 2.0, -8.0)
    GL.glVertex3f(-60.0, 2.0, -8.0)
    GL.glVertex3f(0.0, 7.0, -8.0)

    GL.glVertex3f(0.0, 2.0, 27.0)
    GL.glVertex3f(0.0, 7.0, -8.0)
    GL.glVertex3f(-60.0, 2.0, -8.0)

    # Tail
    GL.glColor3ub(255, 255, 0)
    GL.glVertex3f(-30.0, -0.50, -57.0)
    GL.glVertex3f(30.0, -0.50, -57.0)
    GL.glVertex3f(0.0, -0.50, -40.0)

    GL.glVertex3f(0.0, -0.5, -40.0)
    GL.glVertex3f(30.0, -0.5, -57.0)
    GL.glVertex3f(0.0, 4.0, -57.0)

    GL.glVertex3f(0.0, 4.0, -57.0)
    GL.glVertex3f(-30.0, -0.5, -57.0)
    GL.glVertex3f(0.0, -0.5, -40.0)

    GL.glVertex3f(30.0, -0.5, -57.0)
    GL.glVertex3f(-30.0, -0.5, -57.0)
    GL.glVertex3f(0.0, 4.0, -57.0)

    GL.glColor3ub(255, 0, 0)
    GL.glVertex3f(0.0, 0.5, -40.0)
    GL.glVertex3f(3.0, 0.5, -57.0)
    GL.glVertex3f(0.0, 25.0, -65.0)

    GL.glVertex3f(0.0, 25.0, -65.0)
    GL.glVertex3f(-3.0, 0.5, -57.0)
    GL.glVertex3f(0.0, 0.5, -40.0)

    GL.glVertex3f(3.0, 0.5, -57.0)
    GL.glVertex3f(-3.0, 0.5, -57.0)
    GL.glVertex3f(0.0, 25.0, -65.0)

    GL.glEnd()


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glPushMatrix()
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    draw_jet()
    GL.glPopMatrix()


def imgui_panel() -> None:
    global ambient_light
    imgui.begin("Set Ambient Light")
    _, ambient_light = imgui.color_edit3("ambientLight", ambient_light)
    GL.glLightModelfv(
        GL.GL_LIGHT_MODEL_AMBIENT,
        [ambient_light[0], ambient_light[1], ambient_light[2], 1.0],
    )
    imgui.end()


def setup_rc() -> None:
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glClearColor(0.0, 0.0, 0.5, 1.0)


def change_size(w: int, h: int) -> None:
    n_range = 80.0
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


# Rotation rate while an arrow key is held. Multiplied by frame delta
# so the rotation speed is independent of the render framerate.
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


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    glfw.window_hint(glfw.SAMPLES, 4)

    window = glfw.create_window(800, 600, "Ambient Light Jet", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.swap_interval(1)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

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
