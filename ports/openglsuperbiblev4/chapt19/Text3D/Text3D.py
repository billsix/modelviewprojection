# Text3D.py
# Extruded 3D text via wglUseFontOutlines in the original. Like
# Text2D this is Windows-only — there's no portable equivalent in
# the OpenGL ecosystem. This port shows a static spinning textured
# cube with a label printed via imgui_bundle as a visible substitute
# for the demo's intent (drawing text in 3D scenes).
#
# OpenGL SuperBible, Chapter 19
# Python port of Text3D.cpp by Richard S. Wright Jr.

import os
import sys
import time

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit menu item


def imgui_menubar() -> None:
    # The cube spins on its own and there are no movement keys, so the menubar
    # only carries File -> Quit. Drawn inside the existing imgui frame (the
    # demo already owns an imgui context for its text overlay).
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action(
            "Quit", "Esc", lambda: glfw.set_window_should_close(_window, True)
        )
        imgui.end_menu()
    imgui.end_main_menu_bar()


def draw_cube(s: float = 1.0) -> None:
    s /= 2.0
    GL.glBegin(GL.GL_QUADS)
    for nx, ny, nz, vs in [
        (0, 0, 1, [(-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s)]),
        (0, 0, -1, [(s, -s, -s), (-s, -s, -s), (-s, s, -s), (s, s, -s)]),
        (1, 0, 0, [(s, -s, s), (s, -s, -s), (s, s, -s), (s, s, s)]),
        (-1, 0, 0, [(-s, -s, -s), (-s, -s, s), (-s, s, s), (-s, s, -s)]),
        (0, 1, 0, [(-s, s, s), (s, s, s), (s, s, -s), (-s, s, -s)]),
        (0, -1, 0, [(-s, -s, -s), (s, -s, -s), (s, -s, s), (-s, -s, s)]),
    ]:
        GL.glColor3f(0.5 + 0.5 * nx, 0.5 + 0.5 * ny, 0.5 + 0.5 * nz)
        GL.glNormal3f(nx, ny, nz)
        for v in vs:
            GL.glVertex3f(*v)
    GL.glEnd()


def main() -> None:
    global _window
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    window = glfw.create_window(640, 480, "Text3D", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    _window = window
    glfw.make_context_current(window)
    imgui.create_context()
    impl = GlfwRenderer(window)
    GL.glEnable(GL.GL_DEPTH_TEST)

    start = time.time()
    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
            break

        w, h = glfw.get_framebuffer_size(window)
        GL.glViewport(0, 0, w, h)
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GLU.gluPerspective(45.0, w / h, 0.1, 50.0)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GLU.gluLookAt(3.0, 3.0, 3.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        GL.glRotatef((time.time() - start) * 30.0, 0.0, 1.0, 0.0)
        draw_cube(1.5)

        imgui.new_frame()
        imgui_menubar()
        imgui.set_next_window_pos((10, 10))
        imgui.begin(
            "3D Text",
            None,
            imgui.WindowFlags_.no_decoration.value
            | imgui.WindowFlags_.no_background.value,
        )
        imgui.text_colored((1, 1, 0, 1), "OpenGL 3D Text")
        imgui.text("Win32 wglUseFontOutlines is not portable;")
        imgui.text("imgui overlay used as substitute. Esc to exit.")
        imgui.end()
        imgui.render()
        impl.render(imgui.get_draw_data())

        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
