# spot.py
# Demonstrates a spotlight illuminating a sphere. The C++ original used
# a GLUT right-click menu to switch between flat/smooth shading and
# three tessellation levels; replaced here with an ImGui panel.
# OpenGL SuperBible, Chapter 5
# Python port of Spot.cpp by Richard S. Wright Jr.

import math
import os
import sys

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


x_rot: float = 0.0
y_rot: float = 0.0

light_pos = (0.0, 0.0, 75.0, 1.0)
specular = (1.0, 1.0, 1.0, 1.0)
specref = (1.0, 1.0, 1.0, 1.0)
ambient_light = (0.5, 0.5, 0.5, 1.0)
spot_dir = (0.0, 0.0, -1.0)

MODE_FLAT = 1
MODE_SMOOTH = 2
MODE_VERYLOW = 3
MODE_MEDIUM = 4
MODE_VERYHIGH = 5

i_shade: int = MODE_FLAT
i_tess: int = MODE_VERYLOW


def draw_solid_sphere(radius: float, slices: int, stacks: int) -> None:
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        sin0, cos0 = math.sin(lat0), math.cos(lat0)
        sin1, cos1 = math.sin(lat1), math.cos(lat1)
        GL.glBegin(GL.GL_QUAD_STRIP)
        for j in range(slices + 1):
            lng = 2.0 * math.pi * float(j) / slices
            cl, sl = math.cos(lng), math.sin(lng)
            GL.glNormal3f(cl * cos0, sl * cos0, sin0)
            GL.glVertex3f(radius * cl * cos0, radius * sl * cos0, radius * sin0)
            GL.glNormal3f(cl * cos1, sl * cos1, sin1)
            GL.glVertex3f(radius * cl * cos1, radius * sl * cos1, radius * sin1)
        GL.glEnd()


def draw_solid_cone(base: float, height: float, slices: int, stacks: int) -> None:
    """Replacement for glutSolidCone -- cone with apex at +Z."""
    # Body of the cone
    for i in range(stacks):
        z0 = float(i) / stacks * height
        z1 = float(i + 1) / stacks * height
        r0 = base * (1.0 - float(i) / stacks)
        r1 = base * (1.0 - float(i + 1) / stacks)
        GL.glBegin(GL.GL_QUAD_STRIP)
        for j in range(slices + 1):
            lng = 2.0 * math.pi * float(j) / slices
            cl, sl = math.cos(lng), math.sin(lng)
            # Approximate normal: side of a cone, pointing outward
            slope = base / height if height != 0 else 0.0
            nx = cl
            ny = sl
            nz = slope
            mag = math.sqrt(nx * nx + ny * ny + nz * nz)
            GL.glNormal3f(nx / mag, ny / mag, nz / mag)
            GL.glVertex3f(r0 * cl, r0 * sl, z0)
            GL.glVertex3f(r1 * cl, r1 * sl, z1)
        GL.glEnd()
    # Base disk (facing -Z)
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glNormal3f(0.0, 0.0, -1.0)
    GL.glVertex3f(0.0, 0.0, 0.0)
    for j in range(slices + 1):
        lng = 2.0 * math.pi * float(j) / slices
        GL.glVertex3f(base * math.cos(lng), -base * math.sin(lng), 0.0)
    GL.glEnd()


def render_scene() -> None:
    if i_shade == MODE_FLAT:
        GL.glShadeModel(GL.GL_FLAT)
    else:
        GL.glShadeModel(GL.GL_SMOOTH)

    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    GL.glPushMatrix()
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    GL.glRotatef(x_rot, 1.0, 0.0, 0.0)

    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPOT_DIRECTION, spot_dir)

    # Red cone enclosing the light source
    GL.glColor3ub(255, 0, 0)
    GL.glTranslatef(light_pos[0], light_pos[1], light_pos[2])
    draw_solid_cone(4.0, 6.0, 15, 15)

    # Yellow sphere -- lighting off so it appears self-lit
    GL.glPushAttrib(GL.GL_LIGHTING_BIT)
    GL.glDisable(GL.GL_LIGHTING)
    GL.glColor3ub(255, 255, 0)
    draw_solid_sphere(3.0, 15, 15)
    GL.glPopAttrib()

    GL.glPopMatrix()

    # The blue sphere being illuminated
    GL.glColor3ub(0, 0, 255)
    if i_tess == MODE_VERYLOW:
        draw_solid_sphere(30.0, 7, 7)
    elif i_tess == MODE_MEDIUM:
        draw_solid_sphere(30.0, 15, 15)
    else:
        draw_solid_sphere(30.0, 50, 50)


def imgui_panel() -> None:
    global i_shade, i_tess
    imgui.begin("Spot")
    imgui.text("Shade Model")
    if imgui.radio_button("Flat", i_shade == MODE_FLAT):
        i_shade = MODE_FLAT
    if imgui.radio_button("Smooth", i_shade == MODE_SMOOTH):
        i_shade = MODE_SMOOTH
    imgui.separator()
    imgui.text("Tessellation")
    if imgui.radio_button("Very Low", i_tess == MODE_VERYLOW):
        i_tess = MODE_VERYLOW
    if imgui.radio_button("Medium", i_tess == MODE_MEDIUM):
        i_tess = MODE_MEDIUM
    if imgui.radio_button("Very High", i_tess == MODE_VERYHIGH):
        i_tess = MODE_VERYHIGH
    imgui.end()


def setup_rc() -> None:
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_LIGHTING)

    GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, ambient_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, ambient_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, specular)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glLightf(GL.GL_LIGHT0, GL.GL_SPOT_CUTOFF, 50.0)
    GL.glEnable(GL.GL_LIGHT0)

    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
    GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, specref)
    GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)

    GL.glClearColor(0.0, 0.0, 0.0, 1.0)


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    f_aspect = float(w) / float(h)
    GLU.gluPerspective(35.0, f_aspect, 1.0, 500.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GL.glTranslatef(0.0, 0.0, -250.0)


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def handle_special_keys(window) -> None:
    global x_rot, y_rot
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        x_rot -= 5.0
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        x_rot += 5.0
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        y_rot -= 5.0
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        y_rot += 5.0


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

    window = glfw.create_window(800, 600, "Spot Light", None, None)
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

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        handle_special_keys(window)

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
