# motionblur.py
# Motion blur via the accumulation buffer. Each frame draws the
# revolving sphere 10 times at slightly different rotations and blends
# them together.
#
# Note: GL_ACCUM is deprecated and not all drivers expose it via the
# default GLFW context. If glAccum raises an error, this demo simply
# won't run -- the technique itself is what's pedagogically interesting.
#
# OpenGL SuperBible, Chapter 6
# Python port of MotionBlur.cpp by Richard S. Wright Jr.

import os
import sys

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _primitives  # noqa: E402
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit menu item


f_light_pos = (-100.0, 100.0, 50.0, 1.0)
f_no_light = (0.0, 0.0, 0.0, 0.0)
f_low_light = (0.25, 0.25, 0.25, 1.0)
f_bright_light = (1.0, 1.0, 1.0, 1.0)

y_rot = 45.0


# The revolving sphere is the same every frame (drawn 10x per frame for
# the accumulation-buffer blur) -- tessellate once at import, replay each pass.
SPHERE = _primitives.build_sphere(0.1, 17, 9)


def draw_ground() -> None:
    extent = 20.0
    step = 0.5
    bounce = 0
    GL.glShadeModel(GL.GL_FLAT)
    strip = -extent
    while strip <= extent:
        GL.glBegin(GL.GL_TRIANGLE_STRIP)
        run = extent
        while run >= -extent:
            color = 1.0 if bounce % 2 == 0 else 0.0
            GL.glColor4f(color, color, color, 0.5)
            GL.glVertex3f(strip, 0.0, run)
            GL.glVertex3f(strip + step, 0.0, run)
            bounce += 1
            run -= step
        GL.glEnd()
        strip += step
    GL.glShadeModel(GL.GL_SMOOTH)


def draw_geometry() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glPushMatrix()
    draw_ground()

    GL.glColor3f(1.0, 0.0, 0.0)
    GL.glTranslatef(0.0, 0.5, -3.5)
    GL.glRotatef(-(y_rot * 2.0), 0.0, 1.0, 0.0)
    GL.glTranslatef(1.0, 0.0, 0.0)
    _primitives.draw_mesh(SPHERE)
    GL.glPopMatrix()


def render_scene() -> None:
    global y_rot
    f_passes = 10.0
    y_rot = 35.0

    f_pass = 0.0
    while f_pass < f_passes:
        y_rot += 0.75
        draw_geometry()
        if f_pass == 0.0:
            GL.glAccum(GL.GL_LOAD, 0.5)
        else:
            GL.glAccum(GL.GL_ACCUM, 0.5 * (1.0 / f_passes))
        f_pass += 1.0

    GL.glAccum(GL.GL_RETURN, 1.0)


def setup_rc() -> None:
    GL.glClearColor(*f_low_light)
    GL.glCullFace(GL.GL_BACK)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_DEPTH_TEST)

    GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, f_no_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, f_low_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, f_bright_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, f_bright_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, f_light_pos)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_LIGHT0)

    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(35.0, float(w) / float(h), 1.0, 50.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GL.glTranslatef(0.0, -0.4, 0.0)


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def imgui_menubar() -> None:
    # All controls in the top menubar. This demo has no movement keys, so the
    # bar carries only File -> Quit (mirrors Esc).
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action("Quit", "Esc",
                            lambda: glfw.set_window_should_close(_window, True))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def main() -> None:
    global _window

    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    # Request an accumulation buffer (GLUT_ACCUM in the original)
    glfw.window_hint(glfw.ACCUM_RED_BITS, 16)
    glfw.window_hint(glfw.ACCUM_GREEN_BITS, 16)
    glfw.window_hint(glfw.ACCUM_BLUE_BITS, 16)
    glfw.window_hint(glfw.ACCUM_ALPHA_BITS, 16)

    window = glfw.create_window(
        800, 600, "Motion Blur with the Accumulation Buffer", None, None
    )
    if not window:
        glfw.terminate()
        sys.exit(1)
    _window = window

    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw key
    # callback that doesn't chain, so navigation/Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        render_scene()
        imgui.new_frame()
        imgui_menubar()
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
