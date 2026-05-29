# font.py
# The original uses glXUseXFont + glCallLists to render a fixed
# bitmap string with X11 fonts. That path is X-server-side and not
# portable to non-X platforms. This port renders the same demo
# (a single string on a green background) using imgui_bundle.
#
# OpenGL SuperBible, Chapter 21
# Python port of font.c by Nick Haemel

import os
import sys

import glfw
import OpenGL.GL as GL
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit menu item


def imgui_menubar() -> None:
    # This demo only displays static text, so the menubar only carries
    # File -> Quit. Drawn inside the existing imgui frame (the demo already
    # owns an imgui context for its text rendering).
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
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    window = glfw.create_window(500, 60, "Fonts", None, None)
    if not window:
        glfw.terminate(); sys.exit(1)
    _window = window
    glfw.make_context_current(window)
    imgui.create_context()
    impl = GlfwRenderer(window)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
            break
        GL.glClearColor(0.0, 1.0, 0.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        imgui.new_frame()
        imgui_menubar()
        size = glfw.get_framebuffer_size(window)
        flags = (imgui.WindowFlags_.no_decoration.value
                 | imgui.WindowFlags_.no_background.value
                 | imgui.WindowFlags_.no_inputs.value)
        imgui.set_next_window_pos((0, 0))
        imgui.set_next_window_size((size[0], size[1]))
        imgui.begin("text", None, flags)
        imgui.set_window_font_scale(2.5)
        imgui.text_colored((0, 0, 0, 1), "GLX Fonts")
        imgui.end()
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
