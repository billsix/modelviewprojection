# vertexblend.py
# Vertex blending / "skinning": a two-bone arm where each vertex has a
# weight indicating how much it follows bone-1 vs. bone-2. The single
# vertex shader uses two modelview matrices and blends positions and
# normals based on the per-vertex weight attribute.
#
# C++ used a right-click GLUT menu; this port uses an imgui panel for
# the model/render params (vertex blending, show bones, sphere of
# influence, elbow bend). X/Y/Z move the camera (shift = -); Escape
# quits.
#
# OpenGL SuperBible, Chapter 16
# Python port of vertexblend.cpp by Benjamin Lipchak

import math
import os
import sys

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GL.shaders as shaders_mod
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402

_window = None  # set in main(); used by the Quit control button
window_width: int = 1024
window_height: int = 768

use_blending: bool = True
show_bones: bool = False

prog_obj: int = 0
v_shader: int = 0

light_pos_loc: int = -1
mv2_loc: int = -1
mv2_it_loc: int = -1
weight_loc: int = -1

camera_pos = [50.0, 75.0, 50.0, 1.0]
camera_zoom: float = 0.4
light_pos = np.array([-50.0, 100.0, 50.0, 1.0], dtype=np.float32)

elbow_bend: float = 45.0
sphere_of_influence: float = 1.0

max_tex_size: int = 0


def transform_vec3(v: np.ndarray, m: np.ndarray) -> np.ndarray:
    out = np.zeros(3, dtype=np.float32)
    for r in range(3):
        out[r] = (
            m[r] * v[0] + m[r + 4] * v[1] + m[r + 8] * v[2] + m[r + 12] * v[3]
        )
    return out


def create_pow_map(r: float, g: float, b: float) -> None:
    tex_size = min(max_tex_size, 512)
    texels = np.zeros(tex_size * 4, dtype=np.float32)
    for x in range(tex_size):
        t = (float(x) / float(tex_size - 1)) * 0.125 + 0.875
        v = pow(t, 128.0)
        texels[x * 4 + 0] = r * v
        texels[x * 4 + 1] = g * v
        texels[x * 4 + 2] = b * v
        texels[x * 4 + 3] = 1.0
    texels[0] = texels[1] = texels[2] = 0.0
    GL.glTexImage1D(
        GL.GL_TEXTURE_1D,
        0,
        GL.GL_RGBA16,
        tex_size,
        0,
        GL.GL_RGBA,
        GL.GL_FLOAT,
        texels,
    )


def prepare_shader() -> None:
    global v_shader, prog_obj, light_pos_loc, mv2_loc, mv2_it_loc, weight_loc
    fname = os.path.join(PWD, "shaders", "skinning.vs")
    with open(fname) as f:
        vs_src = f.read()
    v_shader = shaders_mod.compileShader(vs_src, GL.GL_VERTEX_SHADER)
    prog_obj = GL.glCreateProgram()
    GL.glAttachShader(prog_obj, v_shader)
    GL.glLinkProgram(prog_obj)
    if not GL.glGetProgramiv(prog_obj, GL.GL_LINK_STATUS):
        info = GL.glGetProgramInfoLog(prog_obj)
        sys.stderr.write(f"Program link error: {info}\n")
        sys.exit(1)
    light_pos_loc = GL.glGetUniformLocation(prog_obj, "lightPos")
    mv2_loc = GL.glGetUniformLocation(prog_obj, "mv2")
    mv2_it_loc = GL.glGetUniformLocation(prog_obj, "mv2IT")
    weight_loc = GL.glGetAttribLocation(prog_obj, "weight")


def draw_cylinder(
    length: float,
    diameter1: float,
    diameter2: float,
    start_weight: float,
    end_weight: float,
) -> None:
    num_facets = 50
    num_sections = 50
    angle_incr = (2.0 * math.pi) / num_facets

    if start_weight == 0.5:
        influence_start = sphere_of_influence
    else:
        influence_start = 1.0 - sphere_of_influence

    for i in range(num_facets):
        a1 = i * angle_incr
        a2 = ((i + 1) % num_facets) * angle_incr
        y1f = math.sin(a1) * diameter1
        y1o = math.sin(a1) * diameter2
        z1f = math.cos(a1) * diameter1
        z1o = math.cos(a1) * diameter2
        y2f = math.sin(a2) * diameter1
        y2o = math.sin(a2) * diameter2
        z2f = math.cos(a2) * diameter1
        z2o = math.cos(a2) * diameter2
        n1y, n1z = y1f, z1f
        n2y, n2z = y2f, z2f

        GL.glBegin(GL.GL_QUAD_STRIP)
        GL.glVertexAttrib1f(weight_loc, start_weight if use_blending else 1.0)
        GL.glNormal3f(0.0, n1y, n1z)
        GL.glVertex3f(0.0, y1f, z1f)
        GL.glNormal3f(0.0, n2y, n2z)
        GL.glVertex3f(0.0, y2f, z2f)

        for j in range(num_sections):
            param_end = float(j + 1) / float(num_sections)
            length_end = param_end * length
            y1e = y1f + (param_end * (y1o - y1f))
            z1e = z1f + (param_end * (z1o - z1f))
            y2e = y2f + (param_end * (y2o - y2f))
            z2e = z2f + (param_end * (z2o - z2f))

            if not use_blending:
                w_end = 1.0
            elif influence_start > 0.0 and param_end <= influence_start:
                p = param_end * (1.0 / influence_start)
                w_end = start_weight + p * (1.0 - start_weight)
            elif influence_start < 1.0:
                p = (param_end - influence_start) * (
                    1.0 / (1.0 - influence_start)
                )
                w_end = 1.0 + p * (end_weight - 1.0)
            else:
                w_end = 1.0

            GL.glVertexAttrib1f(weight_loc, w_end)
            GL.glNormal3f(0.0, n1y, n1z)
            GL.glVertex3f(length_end, y1e, z1e)
            GL.glNormal3f(0.0, n2y, n2z)
            GL.glVertex3f(length_end, y2e, z2e)

        GL.glEnd()

    if show_bones:
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_BLEND)
        GL.glColor4f(1.0, 1.0, 1.0, 0.75)
        GL.glNormal3f(0.0, 1.0, 0.0)
        GL.glVertexAttrib1f(weight_loc, 1.0)
        GL.glBegin(GL.GL_LINES)
        GL.glVertex3f(0.0, 0.0, 0.0)
        GL.glVertex3f(length, 0.0, 0.0)
        GL.glEnd()
        GL.glColor3f(1.0, 1.0, 0.0)
        GL.glBegin(GL.GL_POINTS)
        GL.glVertex3f(0.0, 0.0, 0.0)
        GL.glVertex3f(length, 0.0, 0.0)
        GL.glEnd()
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_BLEND)


def invert_matrix(m: np.ndarray) -> np.ndarray:
    """4x4 column-major matrix invert via numpy."""
    m44 = m.reshape((4, 4), order="F")
    inv44 = np.linalg.inv(m44)
    return np.asarray(inv44, dtype=np.float32).flatten(order="F")


def draw_models() -> None:
    mv = np.array(
        GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX), dtype=np.float32
    ).flatten()
    light_pos_eye = transform_vec3(light_pos, mv)
    GL.glUniform3fv(light_pos_loc, 1, light_pos_eye)

    # Upper arm: mv2 is the *forearm's* frame (rotated by elbow), so
    # vertices weighted toward bone-2 follow it.
    GL.glPushMatrix()
    GL.glRotatef(elbow_bend, 0.0, 0.0, 1.0)
    GL.glTranslatef(-50.0, 0.0, 0.0)
    mv2 = np.array(
        GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX), dtype=np.float32
    ).flatten()
    GL.glPopMatrix()
    GL.glTranslatef(-50.0, 0.0, 0.0)

    GL.glUniformMatrix4fv(mv2_loc, 1, GL.GL_FALSE, mv2)
    mv2_it_4 = invert_matrix(mv2)
    mv2_it_3 = np.zeros(9, dtype=np.float32)
    for i in range(9):
        mv2_it_3[i] = mv2_it_4[((i // 3) * 4) + (i % 3)]
    GL.glUniformMatrix3fv(mv2_it_loc, 1, GL.GL_TRUE, mv2_it_3)

    GL.glColor3f(0.0, 0.0, 0.90)
    draw_cylinder(50.0, 15.0, 9.0, 1.0, 0.5)

    # Forearm: now mv2 is the *shoulder's* frame; vertices weighted
    # toward bone-2 stay attached to the upper arm.
    GL.glTranslatef(50.0, 0.0, 0.0)
    GL.glPushMatrix()
    mv2 = np.array(
        GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX), dtype=np.float32
    ).flatten()
    GL.glPopMatrix()
    GL.glRotatef(elbow_bend, 0.0, 0.0, 1.0)

    GL.glUniformMatrix4fv(mv2_loc, 1, GL.GL_FALSE, mv2)
    mv2_it_4 = invert_matrix(mv2)
    for i in range(9):
        mv2_it_3[i] = mv2_it_4[((i // 3) * 4) + (i % 3)]
    GL.glUniformMatrix3fv(mv2_it_loc, 1, GL.GL_TRUE, mv2_it_3)

    GL.glColor3f(0.9, 0.0, 0.0)
    draw_cylinder(40.0, 9.0, 5.0, 0.5, 1.0)


def render_scene() -> None:
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    if window_width > window_height:
        ar = float(window_width) / float(window_height)
        GL.glFrustum(
            -ar * camera_zoom,
            ar * camera_zoom,
            -camera_zoom,
            camera_zoom,
            1.0,
            1000.0,
        )
    else:
        ar = float(window_height) / float(window_width)
        GL.glFrustum(
            -camera_zoom,
            camera_zoom,
            -ar * camera_zoom,
            ar * camera_zoom,
            1.0,
            1000.0,
        )
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GLU.gluLookAt(
        camera_pos[0],
        camera_pos[1],
        camera_pos[2],
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
    )
    GL.glViewport(0, 0, window_width, window_height)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    draw_models()


def _nudge_cam(axis: int, d: float) -> None:
    camera_pos[axis] += d


def imgui_menubar() -> None:
    # All controls live in the top menubar. Movement items run once per click
    # and show their key in the shortcut column (discovery); hold the key for
    # continuous motion.
    global use_blending, show_bones, sphere_of_influence, elbow_bend
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action(
            "Quit", "Esc", lambda: glfw.set_window_should_close(_window, True)
        )
        imgui.end_menu()
    if imgui.begin_menu("Render options", True):
        clicked, v = imgui.menu_item("Vertex blending", "", use_blending, True)
        if clicked:
            use_blending = v
        clicked, v = imgui.menu_item("Show bones", "", show_bones, True)
        if clicked:
            show_bones = v
        imgui.separator()
        _, sphere_of_influence = imgui.slider_float(
            "Influence", sphere_of_influence, 0.0, 1.0
        )
        _, elbow_bend = imgui.slider_float(
            "Elbow bend", elbow_bend, -150.0, 150.0
        )
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _common.menu_action("Camera +X", "X", lambda: _nudge_cam(0, 5.0))
        _common.menu_action("Camera -X", "Shift+X", lambda: _nudge_cam(0, -5.0))
        _common.menu_action("Camera +Y", "Y", lambda: _nudge_cam(1, 5.0))
        _common.menu_action("Camera -Y", "Shift+Y", lambda: _nudge_cam(1, -5.0))
        _common.menu_action("Camera +Z", "Z", lambda: _nudge_cam(2, 5.0))
        _common.menu_action("Camera -Z", "Shift+Z", lambda: _nudge_cam(2, -5.0))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def setup_rc() -> None:
    global max_tex_size
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glDepthFunc(GL.GL_LEQUAL)
    GL.glShadeModel(GL.GL_SMOOTH)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glPointSize(10.0)
    GL.glLineWidth(5.0)

    max_tex_size = GL.glGetIntegerv(GL.GL_MAX_TEXTURE_SIZE)

    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_ADD)
    GL.glBindTexture(GL.GL_TEXTURE_1D, 0)
    GL.glTexParameteri(GL.GL_TEXTURE_1D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(
        GL.GL_TEXTURE_1D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE
    )
    create_pow_map(1.0, 1.0, 1.0)
    GL.glEnable(GL.GL_TEXTURE_1D)

    prepare_shader()
    GL.glUseProgram(prog_obj)


def change_size(w: int, h: int) -> None:
    global window_width, window_height
    window_width, window_height = w, h


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, mods: int) -> None:
    # Model/render params (blending, show bones, sphere of influence,
    # elbow bend) moved to the imgui panel; keys here are camera
    # navigation only.
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)
    elif key == glfw.KEY_X:
        camera_pos[0] += -5.0 if (mods & glfw.MOD_SHIFT) else 5.0
    elif key == glfw.KEY_Y:
        camera_pos[1] += -5.0 if (mods & glfw.MOD_SHIFT) else 5.0
    elif key == glfw.KEY_Z:
        camera_pos[2] += -5.0 if (mods & glfw.MOD_SHIFT) else 5.0


def main() -> None:
    global _window
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    window = glfw.create_window(
        window_width, window_height, "Vertex Blending Demo", None, None
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
