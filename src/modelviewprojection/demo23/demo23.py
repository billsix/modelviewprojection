# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

# Demo 23 -- Lit Jet.  Ported from OpenGL SuperBible 4e chapter 5
# example "litjet".
#
# This is the next step after demo 22's Lambert cube:  the same shading
# math applied to a *complex* hand-coded mesh (17 triangles forming a
# jet plane), and extended with Blinn-Phong specular.  Demo 22 only
# needed a single normal per face of a cube; here every face has its
# own normal computed from the cross product, so students see the
# normal-generation step that m3dFindNormal() did silently in the
# original C++.
#
# The shader (litjet.frag) has three lighting modes selected by a
# uniform:
#     0 -- unlit (flat baseColor, like demo 21)
#     1 -- Lambert diffuse (matches demo 22's Block lighting)
#     2 -- Blinn-Phong (Lambert + half-vector specular highlight)
# An imgui radio group flips between them so the difference is
# visible side-by-side without restarting the program.
#
# Controls:
#   ImGui panel            -- lighting mode, wireframe toggle,
#                             ambient/diffuse/specular sliders,
#                             shininess slider
#   LEFT / RIGHT           -- yaw the camera
#   PAGE_UP / PAGE_DOWN    -- pitch the camera
#   UP / DOWN              -- walk forward / backward (camera-relative)
#   Q / E                  -- yaw the jet
#   A / D                  -- pitch the jet
#   ESC                    -- quit

import ctypes
import dataclasses
import math
import os
import sys

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GL.shaders as shaders
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

import modelviewprojection.pyMatrixStack as ms

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


# ---------------------------------------------------------------------------
# GLFW + GL 3.3 core context setup
# ---------------------------------------------------------------------------

if not glfw.init():
    sys.exit()

pwd = os.path.dirname(os.path.abspath(__file__))

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)

window = glfw.create_window(
    600, 600, "ModelViewProjection Demo 23 -- Lit Jet",
    None, None,
)
if not window:
    glfw.terminate()
    sys.exit()
glfw.make_context_current(window)


imgui.create_context()
impl = GlfwRenderer(window)


def on_key(win, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(win, 1)


glfw.set_key_callback(window, on_key)


# Sky-blue background -- the SuperBible original used (0,0,1,1).
GL.glClearColor(0.4, 0.6, 0.9, 1.0)
GL.glEnable(GL.GL_DEPTH_TEST)
GL.glClearDepth(1.0)
GL.glDepthFunc(GL.GL_LEQUAL)
GL.glEnable(GL.GL_CULL_FACE)
GL.glFrontFace(GL.GL_CCW)
GL.glCullFace(GL.GL_BACK)


# ---------------------------------------------------------------------------
# Scene state
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class Camera:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rot_y: float = 0.0
    rot_x: float = 0.0


# Jet is scaled to roughly fit a 2.5-unit cube (see _MESH_SCALE below),
# so this camera placement matches demo22a's distance-from-origin feel.
camera: Camera = Camera(x=0.0, y=0.3, z=4.0, rot_y=0.0, rot_x=0.0)

jet_yaw: float = 0.0
jet_pitch: float = 0.0

# imgui state -- module level so it survives across frames.
# 0 unlit, 1 Lambert, 2 Blinn-Phong (matches the shader's lightingMode)
lighting_mode: int = 2
wireframe: bool = False
ambient: float = 0.3       # SuperBible used 0.3
diffuse: float = 0.7       # SuperBible used 0.7
specular: float = 0.9
shininess: float = 64.0

# Light direction (unit vector toward the light) is parameterized by
# spherical coordinates so it can be slid live; see demo22a for the
# rationale.  Defaults put the light low and in front of the camera so
# the cone+bulb marker is visible from the starting view, and so the
# specular highlight on the jet body is obvious.
light_az_deg: float = 250.0
light_el_deg: float = 25.0


def handle_inputs() -> None:
    global jet_yaw, jet_pitch
    move_step: float = 0.1

    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.rot_y -= 0.03
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.rot_y += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_UP) == glfw.PRESS:
        camera.rot_x += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_DOWN) == glfw.PRESS:
        camera.rot_x -= 0.03
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera.x -= move_step * math.sin(camera.rot_y)
        camera.z -= move_step * math.cos(camera.rot_y)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.x += move_step * math.sin(camera.rot_y)
        camera.z += move_step * math.cos(camera.rot_y)

    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        jet_yaw += 0.05
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        jet_yaw -= 0.05
    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        jet_pitch += 0.05
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        jet_pitch -= 0.05


# ---------------------------------------------------------------------------
# Shader program
# ---------------------------------------------------------------------------


def compile_shader_program() -> int:
    with open(os.path.join(pwd, "litjet.vert")) as f:
        vs = shaders.compileShader(f.read(), GL.GL_VERTEX_SHADER)
    with open(os.path.join(pwd, "litjet.frag")) as f:
        fs = shaders.compileShader(f.read(), GL.GL_FRAGMENT_SHADER)
    return shaders.compileProgram(vs, fs)


program: int = compile_shader_program()

u_mvp = GL.glGetUniformLocation(program, "mvpMatrix")
u_model = GL.glGetUniformLocation(program, "modelMatrix")
u_base = GL.glGetUniformLocation(program, "baseColor")
u_camera_pos = GL.glGetUniformLocation(program, "cameraPosWS")
u_light_dir = GL.glGetUniformLocation(program, "lightDirWS")
u_ambient = GL.glGetUniformLocation(program, "ambientColor")
u_diffuse = GL.glGetUniformLocation(program, "diffuseColor")
u_specular = GL.glGetUniformLocation(program, "specularColor")
u_shininess = GL.glGetUniformLocation(program, "shininess")
u_lighting_mode = GL.glGetUniformLocation(program, "lightingMode")


def set_mvp_uniforms() -> None:
    GL.glUniformMatrix4fv(
        u_mvp, 1, GL.GL_TRUE,
        np.ascontiguousarray(
            ms.get_current_matrix(ms.MatrixStack.modelviewprojection),
            dtype=np.float32,
        ),
    )
    GL.glUniformMatrix4fv(
        u_model, 1, GL.GL_TRUE,
        np.ascontiguousarray(
            ms.get_current_matrix(ms.MatrixStack.model),
            dtype=np.float32,
        ),
    )


# ---------------------------------------------------------------------------
# Geometry -- jet mesh ported from SuperBible litjet.cpp.
#
# Each triangle is (a, b, c, n).  n=None means "compute via cross
# product" -- the same job m3dFindNormal() did in the original.  A
# handful of triangles in the C++ source pre-set glNormal3f(0,-1,0)
# and reused it for the next triangle (the underside of the body, the
# bottom of the tail fin, etc.); those keep the explicit normal here.
#
# Vertex coordinates are *as written in the SuperBible source* -- they
# span roughly x:-60..60, y:-0.5..25, z:-65..60.  We scale by 1/50 at
# upload time so the jet fits the unit-ish convention used since
# demo16; the shape is identical.
# ---------------------------------------------------------------------------


_FLOATS_PER_VERTEX = 6   # 3 pos + 3 normal
_STRIDE = _FLOATS_PER_VERTEX * 4
_MESH_SCALE = 1.0 / 50.0


def _face_normal(a, b, c) -> tuple[float, float, float]:
    """Outward normal of triangle (a, b, c) listed counter-clockwise."""
    ax, ay, az = a
    bx, by, bz = b
    cx, cy, cz = c
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    L = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx / L, ny / L, nz / L)


# (a, b, c, normal_or_None).  Order and orientation match litjet.cpp
# exactly; CCW from outside the jet so GL_BACK culling works.
_JET_TRIS: list = [
    # Nose cone -- bottom flat triangle, then two slanted sides.
    ((  0.0,  0.0,  60.0), (-15.0,  0.0, 30.0), ( 15.0,  0.0,  30.0),
        (0.0, -1.0, 0.0)),
    (( 15.0,  0.0,  30.0), (  0.0, 15.0, 30.0), (  0.0,  0.0,  60.0), None),
    ((  0.0,  0.0,  60.0), (  0.0, 15.0, 30.0), (-15.0,  0.0,  30.0), None),

    # Body -- left side, right side, flat bottom.
    ((-15.0,  0.0,  30.0), (  0.0, 15.0, 30.0), (  0.0,  0.0, -56.0), None),
    ((  0.0,  0.0, -56.0), (  0.0, 15.0, 30.0), ( 15.0,  0.0,  30.0), None),
    (( 15.0,  0.0,  30.0), (-15.0,  0.0, 30.0), (  0.0,  0.0, -56.0),
        (0.0, -1.0, 0.0)),

    # Wings -- single big bottom triangle, then a wedge on top.
    ((  0.0,  2.0,  27.0), (-60.0,  2.0, -8.0), ( 60.0,  2.0,  -8.0), None),
    (( 60.0,  2.0,  -8.0), (  0.0,  7.0, -8.0), (  0.0,  2.0,  27.0), None),
    (( 60.0,  2.0,  -8.0), (-60.0,  2.0, -8.0), (  0.0,  7.0,  -8.0), None),
    ((  0.0,  2.0,  27.0), (  0.0,  7.0, -8.0), (-60.0,  2.0,  -8.0), None),

    # Horizontal tail fin -- bottom flat, two slanted sides, back.
    ((-30.0, -0.5, -57.0), ( 30.0, -0.5, -57.0), (  0.0, -0.5, -40.0),
        (0.0, -1.0, 0.0)),
    ((  0.0, -0.5, -40.0), ( 30.0, -0.5, -57.0), (  0.0,  4.0, -57.0), None),
    ((  0.0,  4.0, -57.0), (-30.0, -0.5, -57.0), (  0.0, -0.5, -40.0), None),
    (( 30.0, -0.5, -57.0), (-30.0, -0.5, -57.0), (  0.0,  4.0, -57.0), None),

    # Vertical stabilizer at the rear.
    ((  0.0,  0.5, -40.0), (  3.0,  0.5, -57.0), (  0.0, 25.0, -65.0), None),
    ((  0.0, 25.0, -65.0), ( -3.0,  0.5, -57.0), (  0.0,  0.5, -40.0), None),
    ((  3.0,  0.5, -57.0), ( -3.0,  0.5, -57.0), (  0.0, 25.0, -65.0), None),
]


def _build_jet() -> np.ndarray:
    out: list[float] = []
    for a, b, c, n in _JET_TRIS:
        if n is None:
            n = _face_normal(a, b, c)
        for vert in (a, b, c):
            out.extend(v * _MESH_SCALE for v in vert)
            out.extend(n)
    return np.array(out, dtype=np.float32)


def _build_jet_wire() -> np.ndarray:
    """Edge list for wireframe mode -- every triangle's three edges,
    duplicates and all.  Cheap and clear."""
    out: list[float] = []
    zero = (0.0, 0.0, 0.0)
    for a, b, c, _n in _JET_TRIS:
        for p, q in ((a, b), (b, c), (c, a)):
            out.extend(v * _MESH_SCALE for v in p)
            out.extend(zero)
            out.extend(v * _MESH_SCALE for v in q)
            out.extend(zero)
    return np.array(out, dtype=np.float32)


def _build_marker_cone(radius: float, height: float,
                       slices: int) -> np.ndarray:
    """Cone with the base at z=0 and apex at z=+height, matching
    chapt05/spot.cpp's bulb-at-base / cone-body-behind layout.  Same
    6-float layout (pos + zero normal) as the jet.  Drawn unlit."""
    out: list[float] = []
    base_pts = []
    for i in range(slices + 1):
        t = i / slices * 2.0 * math.pi
        base_pts.append((radius * math.cos(t), radius * math.sin(t), 0.0))

    apex = (0.0, 0.0, height)
    base_center = (0.0, 0.0, 0.0)
    # Slant sides:  (apex, p[i], p[i+1]) is CCW from outside.
    for i in range(slices):
        for v in (apex, base_pts[i], base_pts[i + 1]):
            out.extend(v)
            out.extend((0.0, 0.0, 0.0))
    # Base cap:  outward normal is -z, so winding (center, p[i+1], p[i]).
    for i in range(slices):
        for v in (base_center, base_pts[i + 1], base_pts[i]):
            out.extend(v)
            out.extend((0.0, 0.0, 0.0))
    return np.array(out, dtype=np.float32)


def _build_marker_sphere(radius: float, slices: int,
                         stacks: int) -> np.ndarray:
    """Tiny UV sphere for the bulb (6-float layout, unlit)."""
    out: list[float] = []
    for i in range(stacks):
        phi0 = math.pi * (i / stacks) - math.pi / 2.0
        phi1 = math.pi * ((i + 1) / stacks) - math.pi / 2.0
        cphi0, sphi0 = math.cos(phi0), math.sin(phi0)
        cphi1, sphi1 = math.cos(phi1), math.sin(phi1)
        for j in range(slices):
            t0 = 2.0 * math.pi * (j / slices)
            t1 = 2.0 * math.pi * ((j + 1) / slices)
            ct0, st0 = math.cos(t0), math.sin(t0)
            ct1, st1 = math.cos(t1), math.sin(t1)
            p00 = (cphi0 * st0, sphi0, cphi0 * ct0)
            p10 = (cphi0 * st1, sphi0, cphi0 * ct1)
            p01 = (cphi1 * st0, sphi1, cphi1 * ct0)
            p11 = (cphi1 * st1, sphi1, cphi1 * ct1)
            for v in (p00, p10, p01, p10, p11, p01):
                out.extend(p * radius for p in v)
                out.extend((0.0, 0.0, 0.0))
    return np.array(out, dtype=np.float32)


def make_vao(vertex_data: np.ndarray) -> tuple[int, int, int]:
    vertex_data = np.ascontiguousarray(vertex_data, dtype=np.float32)
    vao = GL.glGenVertexArrays(1)
    vbo = GL.glGenBuffers(1)
    GL.glBindVertexArray(vao)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
    GL.glBufferData(
        GL.GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL.GL_STATIC_DRAW
    )
    GL.glEnableVertexAttribArray(0)
    GL.glVertexAttribPointer(
        0, 3, GL.GL_FLOAT, False, _STRIDE, ctypes.c_void_p(0)
    )
    GL.glEnableVertexAttribArray(1)
    GL.glVertexAttribPointer(
        1, 3, GL.GL_FLOAT, False, _STRIDE, ctypes.c_void_p(12)
    )
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    GL.glBindVertexArray(0)
    return vao, vbo, vertex_data.size // _FLOATS_PER_VERTEX


jet_vao, jet_vbo, jet_count = make_vao(_build_jet())
wire_vao, wire_vbo, wire_count = make_vao(_build_jet_wire())

# Light marker geometry -- jet is ~2.5 units wide so the marker is a
# touch larger than demo22a's:  cone radius 0.15, height 0.45, bulb
# 0.10.  Sits 2.0 units along the light direction.
marker_cone_vao, marker_cone_vbo, marker_cone_count = make_vao(
    _build_marker_cone(radius=0.15, height=0.45, slices=18)
)
marker_bulb_vao, marker_bulb_vbo, marker_bulb_count = make_vao(
    _build_marker_sphere(radius=0.10, slices=14, stacks=8)
)
LIGHT_MARKER_DISTANCE: float = 2.0
LIGHT_MARKER_CONE_COLOR: tuple = (0.85, 0.15, 0.15)
LIGHT_MARKER_BULB_COLOR: tuple = (1.00, 1.00, 0.00)


# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------

# SuperBible original used a positional light at (-50, 50, 100); we
# treat it as a directional light, normalized -- only the angle
# matters.  Re-derived from imgui sliders each frame.  The shader
# treats lightDirWS as "direction toward the light".
def light_dir_ws(az_deg: float, el_deg: float) -> tuple[float, float, float]:
    az = math.radians(az_deg)
    el = math.radians(el_deg)
    return (
        math.cos(el) * math.cos(az),
        math.sin(el),
        math.cos(el) * math.sin(az),
    )

# Mid-gray jet body, matching SuperBible glColor3ub(128,128,128).
JET_COLOR = (0.5, 0.5, 0.5)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

TARGET_FRAMERATE: int = 60
time_at_beginning_of_previous_frame: float = glfw.get_time()

while not glfw.window_should_close(window):
    while (
        glfw.get_time()
        < time_at_beginning_of_previous_frame + 1.0 / TARGET_FRAMERATE
    ):
        pass
    time_at_beginning_of_previous_frame = glfw.get_time()

    glfw.poll_events()
    impl.process_inputs()
    handle_inputs()

    imgui.new_frame()
    imgui.set_next_window_size(
        imgui.ImVec2(320, 360), imgui.Cond_.first_use_ever
    )
    imgui.begin("Lit Jet", True)
    imgui.text("Lighting model:")
    if imgui.radio_button("Unlit", lighting_mode == 0):
        lighting_mode = 0
    if imgui.radio_button("Lambert (diffuse only)", lighting_mode == 1):
        lighting_mode = 1
    if imgui.radio_button("Blinn-Phong (+ specular)", lighting_mode == 2):
        lighting_mode = 2
    imgui.separator()
    _, wireframe = imgui.checkbox("Wireframe", wireframe)
    imgui.separator()
    _, ambient = imgui.slider_float("Ambient", ambient, 0.0, 1.0)
    _, diffuse = imgui.slider_float("Diffuse", diffuse, 0.0, 1.0)
    _, specular = imgui.slider_float("Specular", specular, 0.0, 1.0)
    _, shininess = imgui.slider_float("Shininess", shininess, 1.0, 256.0)
    imgui.separator()
    imgui.text("Light direction (red cone + yellow bulb):")
    _, light_az_deg = imgui.slider_float(
        "Azimuth (deg)", light_az_deg, 0.0, 360.0)
    _, light_el_deg = imgui.slider_float(
        "Elevation (deg)", light_el_deg, 5.0, 89.0)
    imgui.end()

    light_dir = light_dir_ws(light_az_deg, light_el_deg)

    width, height = glfw.get_framebuffer_size(window)
    GL.glViewport(0, 0, width, height)
    GL.glClear(sum([GL.GL_COLOR_BUFFER_BIT, GL.GL_DEPTH_BUFFER_BIT]))

    ms.set_to_identity_matrix(ms.MatrixStack.model)
    ms.set_to_identity_matrix(ms.MatrixStack.view)
    ms.set_to_identity_matrix(ms.MatrixStack.projection)

    aspect = float(width) / float(height) if height > 0 else 1.0
    ms.perspective(
        field_of_view=45.0,
        aspect_ratio=aspect,
        near_z=0.1,
        far_z=40.0,
    )

    ms.rotate_x(ms.MatrixStack.view, -camera.rot_x)
    ms.rotate_y(ms.MatrixStack.view, -camera.rot_y)
    ms.translate(ms.MatrixStack.view, -camera.x, -camera.y, -camera.z)

    GL.glUseProgram(program)
    GL.glUniform3f(u_light_dir, *light_dir)
    GL.glUniform3f(u_camera_pos, camera.x, camera.y, camera.z)
    GL.glUniform3f(u_ambient, ambient, ambient, ambient)
    GL.glUniform3f(u_diffuse, diffuse, diffuse, diffuse)
    GL.glUniform3f(u_specular, specular, specular, specular)
    GL.glUniform1f(u_shininess, shininess)

    with ms.push_matrix(ms.MatrixStack.model):
        ms.rotate_y(ms.MatrixStack.model, jet_yaw)
        ms.rotate_x(ms.MatrixStack.model, jet_pitch)

        if wireframe:
            GL.glUniform1i(u_lighting_mode, 0)
            GL.glUniform3f(u_base, 1.0, 1.0, 0.0)
            set_mvp_uniforms()
            GL.glBindVertexArray(wire_vao)
            GL.glDrawArrays(GL.GL_LINES, 0, wire_count)
            GL.glBindVertexArray(0)
        else:
            GL.glUniform1i(u_lighting_mode, lighting_mode)
            GL.glUniform3f(u_base, *JET_COLOR)
            set_mvp_uniforms()
            GL.glBindVertexArray(jet_vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, jet_count)
            GL.glBindVertexArray(0)

    # ---- Light marker (red cone + yellow bulb) ----
    # Drawn outside the jet's model push so the marker isn't yawed/
    # pitched by the jet controls.  Unlit (lightingMode=0) so it
    # doesn't shade against itself.
    GL.glUniform1i(u_lighting_mode, 0)
    with ms.push_matrix(ms.MatrixStack.model):
        ms.translate(ms.MatrixStack.model,
                     light_dir[0] * LIGHT_MARKER_DISTANCE,
                     light_dir[1] * LIGHT_MARKER_DISTANCE,
                     light_dir[2] * LIGHT_MARKER_DISTANCE)
        # See demo22a for the rotation derivation:  +z -> +light_dir.
        ms.rotate_y(ms.MatrixStack.model,
                    math.radians(90.0 - light_az_deg))
        ms.rotate_x(ms.MatrixStack.model,
                    math.radians(-light_el_deg))

        GL.glUniform3f(u_base, *LIGHT_MARKER_CONE_COLOR)
        set_mvp_uniforms()
        GL.glBindVertexArray(marker_cone_vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, marker_cone_count)
        GL.glBindVertexArray(0)

        # Bulb at the base of the cone (= local origin).
        GL.glUniform3f(u_base, *LIGHT_MARKER_BULB_COLOR)
        set_mvp_uniforms()
        GL.glBindVertexArray(marker_bulb_vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, marker_bulb_count)
        GL.glBindVertexArray(0)

    GL.glUseProgram(0)

    imgui.render()
    impl.render(imgui.get_draw_data())
    glfw.swap_buffers(window)


# Clean up GL resources before tearing down the context.
GL.glBindVertexArray(0)
GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
GL.glUseProgram(0)
GL.glDeleteVertexArrays(1, [jet_vao])
GL.glDeleteVertexArrays(1, [wire_vao])
GL.glDeleteVertexArrays(1, [marker_cone_vao])
GL.glDeleteVertexArrays(1, [marker_bulb_vao])
GL.glDeleteBuffers(1, [jet_vbo])
GL.glDeleteBuffers(1, [wire_vbo])
GL.glDeleteBuffers(1, [marker_cone_vbo])
GL.glDeleteBuffers(1, [marker_bulb_vbo])
GL.glDeleteProgram(program)

glfw.terminate()
