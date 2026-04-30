
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

# Demo 22a -- Textured Pyramid.  Ported from OpenGL SuperBible 4e
# chapter 8 example "Pyramid".
#
# This is the gentle introduction to texturing:  one mesh, one texture,
# no shadows.  Demo 22 ("Block") layers lighting + planar shadows + a
# multi-texture cube on top of the same idea -- read this one first.
#
# Implementation notes:
#
# * OpenGL 3.3 core profile, single shader pair (pyramid.vert /
#   pyramid.frag).  The shader has uniforms for "useTexture" and
#   "useLighting" so the same program drives every stage of the
#   imgui control panel.
# * Per-face normals are computed once in Python (see _build_pyramid)
#   from the cross product of two edges, exactly like the SuperBible
#   original called m3dFindNormal().
# * Texture filtering (NEAREST vs LINEAR) is exposed in imgui so
#   students can see the difference between blocky-texel sampling and
#   bilinear interpolation.
#
# Controls:
#   ImGui panel            -- textured / lit / wireframe toggles,
#                             texture filter, ambient/diffuse sliders
#   LEFT / RIGHT           -- yaw the camera
#   PAGE_UP / PAGE_DOWN    -- pitch the camera
#   UP / DOWN              -- walk forward / backward (camera-relative)
#   Q / E                  -- yaw the pyramid (replaces SuperBible
#                             arrow keys, since arrows fly the camera)
#   A / D                  -- pitch the pyramid
#   ESC                    -- quit

import ctypes
import dataclasses
import math
import os
import sys

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GL.shaders as shaders
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

import modelviewprojection.pyMatrixStack as ms



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
    600, 600, "ModelViewProjection Demo 22a -- Textured Pyramid",
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


GL.glClearColor(0.0, 0.0, 0.0, 1.0)
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


# Pyramid is unit-scale (about 1 wide, 0.8 tall).  Sit the camera back
# a bit and look slightly downward so the pyramid is centered.
camera: Camera = Camera(x=0.0, y=0.4, z=3.0, rot_y=0.0, rot_x=0.0)

pyramid_yaw: float = 0.0
pyramid_pitch: float = 0.0

# imgui-driven toggles -- module level so they survive across frames.
use_texture: bool = True
use_lighting: bool = True
wireframe: bool = False
filter_nearest: bool = False  # False -> GL_LINEAR, True -> GL_NEAREST
ambient: float = 0.25
diffuse: float = 0.75

# Light direction (a unit vector pointing *toward* the light) is
# parameterized by spherical coordinates so it can be slid live.  No
# distance slider -- it's a directional light, infinitely far away;
# only the *angle* matters.  The yellow cone+bulb marker is drawn at
# a fixed visualization offset along the direction so students see
# WHERE the sun is, even though strictly speaking a directional light
# has no position.  Defaults roughly match the SuperBible original
# (-10, 5, 5) but tuned so the marker sits in the starting FOV.
light_az_deg: float = 250.0     # 0 = +X, 90 = +Z, 180 = -X, 270 = -Z
light_el_deg: float = 25.0      # angle above the XZ plane


def handle_inputs() -> None:
    global pyramid_yaw, pyramid_pitch
    move_step: float = 0.05  # pyramid is ~1 unit across

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
        pyramid_yaw += 0.05
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        pyramid_yaw -= 0.05
    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        pyramid_pitch += 0.05
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        pyramid_pitch -= 0.05


# ---------------------------------------------------------------------------
# Shader program
# ---------------------------------------------------------------------------


def compile_shader_program() -> int:
    with open(os.path.join(pwd, "pyramid.vert")) as f:
        vs = shaders.compileShader(f.read(), GL.GL_VERTEX_SHADER)
    with open(os.path.join(pwd, "pyramid.frag")) as f:
        fs = shaders.compileShader(f.read(), GL.GL_FRAGMENT_SHADER)
    return shaders.compileProgram(vs, fs)


program: int = compile_shader_program()

u_mvp = GL.glGetUniformLocation(program, "mvpMatrix")
u_model = GL.glGetUniformLocation(program, "modelMatrix")
u_flat = GL.glGetUniformLocation(program, "flatColor")
u_use_lighting = GL.glGetUniformLocation(program, "useLighting")
u_use_texture = GL.glGetUniformLocation(program, "useTexture")
u_light_dir = GL.glGetUniformLocation(program, "lightDirWS")
u_ambient = GL.glGetUniformLocation(program, "ambientColor")
u_diffuse = GL.glGetUniformLocation(program, "diffuseColor")
u_tex = GL.glGetUniformLocation(program, "tex")


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
# Texture
# ---------------------------------------------------------------------------


def load_texture(path: str) -> int:
    img = iio.imread(path)
    if img.ndim == 2:
        img = np.stack([img, img, img], axis=-1)
    h, w = img.shape[:2]
    img = np.ascontiguousarray(img, dtype=np.uint8)

    tex = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE
    )
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE
    )
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR
    )
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR
    )
    GL.glTexImage2D(
        GL.GL_TEXTURE_2D, 0, GL.GL_RGB8, w, h, 0,
        GL.GL_RGB, GL.GL_UNSIGNED_BYTE, img,
    )
    GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
    return tex


tex_stone = load_texture(os.path.join(pwd, "stone.tga"))


# ---------------------------------------------------------------------------
# Geometry -- pyramid with per-face normals + uv coords.
#
# Five corners (numbered to match the SuperBible source):
#   0: top
#   1: back-left  base
#   2: back-right base
#   3: front-right base
#   4: front-left base
#
# Six triangles:  two for the square base, four for the slanted sides.
# Each side gets a uv triangle (0.5, 1.0) -> (0, 0) -> (1, 0) so the
# stone texture's apex meets the pyramid's apex.
# ---------------------------------------------------------------------------


_FLOATS_PER_VERTEX = 8  # 3 pos + 3 normal + 2 uv
_STRIDE = _FLOATS_PER_VERTEX * 4


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


def _build_pyramid() -> np.ndarray:
    corners = [
        ( 0.0,  0.80,  0.00),  # 0 top
        (-0.5,  0.00, -0.50),  # 1 back-left
        ( 0.5,  0.00, -0.50),  # 2 back-right
        ( 0.5,  0.00,  0.50),  # 3 front-right
        (-0.5,  0.00,  0.50),  # 4 front-left
    ]

    # base normal points down, two triangles cover the square.  uv
    # tiles the stone texture once across the base.
    base_n = (0.0, -1.0, 0.0)
    triangles = [
        # base (CCW from below, so normal faces -Y)
        (corners[2], corners[4], corners[1], base_n,
         [(1, 1), (0, 0), (0, 1)]),
        (corners[2], corners[3], corners[4], base_n,
         [(1, 1), (1, 0), (0, 0)]),
        # front face (apex, front-left, front-right)
        (corners[0], corners[4], corners[3],
         _face_normal(corners[0], corners[4], corners[3]),
         [(0.5, 1.0), (0.0, 0.0), (1.0, 0.0)]),
        # left face (apex, back-left, front-left)
        (corners[0], corners[1], corners[4],
         _face_normal(corners[0], corners[1], corners[4]),
         [(0.5, 1.0), (0.0, 0.0), (1.0, 0.0)]),
        # back face (apex, back-right, back-left)
        (corners[0], corners[2], corners[1],
         _face_normal(corners[0], corners[2], corners[1]),
         [(0.5, 1.0), (0.0, 0.0), (1.0, 0.0)]),
        # right face (apex, front-right, back-right)
        (corners[0], corners[3], corners[2],
         _face_normal(corners[0], corners[3], corners[2]),
         [(0.5, 1.0), (0.0, 0.0), (1.0, 0.0)]),
    ]

    out: list[float] = []
    for a, b, c, n, uvs in triangles:
        for vert, uv in zip((a, b, c), uvs):
            out.extend(vert)
            out.extend(n)
            out.extend(uv)
    return np.array(out, dtype=np.float32)


def _build_pyramid_wire() -> np.ndarray:
    corners = [
        ( 0.0,  0.80,  0.00),
        (-0.5,  0.00, -0.50),
        ( 0.5,  0.00, -0.50),
        ( 0.5,  0.00,  0.50),
        (-0.5,  0.00,  0.50),
    ]
    edges = [
        # base
        (1, 2), (2, 3), (3, 4), (4, 1),
        # apex to each base corner
        (0, 1), (0, 2), (0, 3), (0, 4),
    ]
    out: list[float] = []
    for a, b in edges:
        for ci in (a, b):
            out.extend(corners[ci])
            out.extend((0.0, 0.0, 0.0))
            out.extend((0.0, 0.0))
    return np.array(out, dtype=np.float32)


def _build_marker_cone(radius: float, height: float,
                       slices: int) -> np.ndarray:
    """Right circular cone with the base at the origin and the apex
    sticking out along +z.  Modeled to match chapt05/spot.cpp:84-85
    (`glutSolidCone` after `glTranslatef(lightPos)`):  the light bulb
    sits at the cone's base, and the cone body extends *behind* the
    bulb -- so when the model matrix rotates +z onto +light_dir, the
    base (and the bulb) end up closest to the scene and the apex
    points back toward the light source.

    Drawn unlit, so normals are zeros and uvs are (0, 0)."""
    out: list[float] = []
    base_pts = []
    for i in range(slices + 1):
        t = i / slices * 2.0 * math.pi
        # Base ring sits at z=0, apex juts out to z=+height.
        base_pts.append((radius * math.cos(t), radius * math.sin(t), 0.0))

    apex = (0.0, 0.0, height)
    base_center = (0.0, 0.0, 0.0)

    # Slant sides:  (apex, p[i], p[i+1]) is CCW from outside (the
    # cross-product points radially-outward + slightly toward +z).
    for i in range(slices):
        for v in (apex, base_pts[i], base_pts[i + 1]):
            out.extend(v)
            out.extend((0.0, 0.0, 0.0))
            out.extend((0.0, 0.0))

    # Base cap:  outward normal is -z (away from the apex, toward the
    # bulb-and-scene side).  Winding (center, p[i+1], p[i]).
    for i in range(slices):
        for v in (base_center, base_pts[i + 1], base_pts[i]):
            out.extend(v)
            out.extend((0.0, 0.0, 0.0))
            out.extend((0.0, 0.0))
    return np.array(out, dtype=np.float32)


def _build_marker_sphere(radius: float, slices: int,
                         stacks: int) -> np.ndarray:
    """Tiny UV sphere for the "bulb" inside the cone.  Same winding
    rules as demo24's sphere generator (p00, p10, p01) gives outward
    normals; here normals don't matter because the marker is drawn
    unlit, but the winding still has to be CCW for back-face culling."""
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
                out.extend((0.0, 0.0))
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
    GL.glEnableVertexAttribArray(2)
    GL.glVertexAttribPointer(
        2, 2, GL.GL_FLOAT, False, _STRIDE, ctypes.c_void_p(24)
    )
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    GL.glBindVertexArray(0)
    return vao, vbo, vertex_data.size // _FLOATS_PER_VERTEX


pyramid_vao, pyramid_vbo, pyramid_count = make_vao(_build_pyramid())
wire_vao, wire_vbo, wire_count = make_vao(_build_pyramid_wire())

# Light marker geometry -- a small cone "arrow" plus a tiny sphere
# "bulb" inside it, both shown unlit.  Sized for the unit-scale
# pyramid:  cone is ~0.3 long with 0.1 base radius, bulb is 0.07 across.
marker_cone_vao, marker_cone_vbo, marker_cone_count = make_vao(
    _build_marker_cone(radius=0.10, height=0.30, slices=18)
)
marker_bulb_vao, marker_bulb_vbo, marker_bulb_count = make_vao(
    _build_marker_sphere(radius=0.07, slices=14, stacks=8)
)
LIGHT_MARKER_DISTANCE: float = 1.4   # how far from origin the marker sits
LIGHT_MARKER_CONE_COLOR: tuple = (0.85, 0.15, 0.15)   # red, like spot.cpp
LIGHT_MARKER_BULB_COLOR: tuple = (1.00, 1.00, 0.00)   # yellow


# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------

# SuperBible original used a positional light at (-10, 5, 5).  We
# treat it as a directional light:  only the angle matters, not the
# distance.  Re-derived from imgui sliders each frame so the user can
# slide the light around.
def light_dir_ws(az_deg: float, el_deg: float) -> tuple[float, float, float]:
    az = math.radians(az_deg)
    el = math.radians(el_deg)
    return (
        math.cos(el) * math.cos(az),
        math.sin(el),
        math.cos(el) * math.sin(az),
    )


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
        imgui.ImVec2(300, 260), imgui.Cond_.first_use_ever
    )
    imgui.set_next_window_size(
        imgui.ImVec2(320, 340), imgui.Cond_.first_use_ever
    )
    imgui.begin("Pyramid", True)
    _, use_texture = imgui.checkbox("Textured", use_texture)
    _, use_lighting = imgui.checkbox("Lit", use_lighting)
    _, wireframe = imgui.checkbox("Wireframe", wireframe)
    imgui.separator()
    imgui.text("Texture filter:")
    if imgui.radio_button("Linear (smooth)", not filter_nearest):
        filter_nearest = False
    if imgui.radio_button("Nearest (blocky)", filter_nearest):
        filter_nearest = True
    imgui.separator()
    _, ambient = imgui.slider_float("Ambient", ambient, 0.0, 1.0)
    _, diffuse = imgui.slider_float("Diffuse", diffuse, 0.0, 1.0)
    imgui.separator()
    imgui.text("Light direction (red cone + yellow bulb):")
    _, light_az_deg = imgui.slider_float(
        "Azimuth (deg)", light_az_deg, 0.0, 360.0)
    _, light_el_deg = imgui.slider_float(
        "Elevation (deg)", light_el_deg, 5.0, 89.0)
    imgui.end()

    light_dir = light_dir_ws(light_az_deg, light_el_deg)

    # Apply the imgui-selected texture filter (cheap; just sets two
    # parameters on the bound texture object).
    flt = GL.GL_NEAREST if filter_nearest else GL.GL_LINEAR
    GL.glBindTexture(GL.GL_TEXTURE_2D, tex_stone)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, flt)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, flt)
    GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

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
    GL.glUniform3f(u_ambient, ambient, ambient, ambient)
    GL.glUniform3f(u_diffuse, diffuse, diffuse, diffuse)
    GL.glUniform1i(u_tex, 0)

    with ms.push_matrix(ms.MatrixStack.model):
        ms.rotate_y(ms.MatrixStack.model, pyramid_yaw)
        ms.rotate_x(ms.MatrixStack.model, pyramid_pitch)

        if wireframe:
            GL.glUniform1i(u_use_lighting, 0)
            GL.glUniform1i(u_use_texture, 0)
            GL.glUniform3f(u_flat, 1.0, 1.0, 0.0)
            set_mvp_uniforms()
            GL.glBindVertexArray(wire_vao)
            GL.glDrawArrays(GL.GL_LINES, 0, wire_count)
            GL.glBindVertexArray(0)
        else:
            GL.glUniform1i(u_use_lighting, 1 if use_lighting else 0)
            GL.glUniform1i(u_use_texture, 1 if use_texture else 0)
            GL.glUniform3f(u_flat, 0.8, 0.6, 0.4)  # sandstone fallback
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, tex_stone)
            set_mvp_uniforms()
            GL.glBindVertexArray(pyramid_vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, pyramid_count)
            GL.glBindVertexArray(0)

    # ---- Light marker (red cone + yellow bulb) ----
    # Adapted from chapt05/spot.cpp:79-94, but oriented along a
    # *direction* instead of anchored at a point-light position:  the
    # cone's local +z axis is rotated onto +light_dir and the whole
    # thing is translated outward by LIGHT_MARKER_DISTANCE so the apex
    # points back toward the scene -- "the sun is over there, shining
    # this way."  Drawn unlit (useLighting=0, useTexture=0) so the
    # marker doesn't shade itself against the very light it represents.
    GL.glUniform1i(u_use_lighting, 0)
    GL.glUniform1i(u_use_texture, 0)
    with ms.push_matrix(ms.MatrixStack.model):
        ms.translate(ms.MatrixStack.model,
                     light_dir[0] * LIGHT_MARKER_DISTANCE,
                     light_dir[1] * LIGHT_MARKER_DISTANCE,
                     light_dir[2] * LIGHT_MARKER_DISTANCE)
        # Rotate so the cone's local +z axis ends up parallel to
        # +light_dir.  See the comment in demo24 for the derivation;
        # the order here is rotate_y FIRST (post-multiplied last),
        # then rotate_x, so the matrix evaluates as
        #   T(distance*ld) @ R_y(90 - az) @ R_x(-el).
        ms.rotate_y(ms.MatrixStack.model,
                    math.radians(90.0 - light_az_deg))
        ms.rotate_x(ms.MatrixStack.model,
                    math.radians(-light_el_deg))

        # Cone -- red, apex closer to scene, base near the bulb.
        GL.glUniform3f(u_flat, *LIGHT_MARKER_CONE_COLOR)
        set_mvp_uniforms()
        GL.glBindVertexArray(marker_cone_vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, marker_cone_count)
        GL.glBindVertexArray(0)

        # Bulb -- yellow sphere at the base of the cone (= local
        # origin), where the light conceptually shines from.
        GL.glUniform3f(u_flat, *LIGHT_MARKER_BULB_COLOR)
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
GL.glDeleteVertexArrays(1, [pyramid_vao])
GL.glDeleteVertexArrays(1, [wire_vao])
GL.glDeleteVertexArrays(1, [marker_cone_vao])
GL.glDeleteVertexArrays(1, [marker_bulb_vao])
GL.glDeleteBuffers(1, [pyramid_vbo])
GL.glDeleteBuffers(1, [wire_vbo])
GL.glDeleteBuffers(1, [marker_cone_vbo])
GL.glDeleteBuffers(1, [marker_bulb_vbo])
GL.glDeleteTextures(1, [tex_stone])
GL.glDeleteProgram(program)

glfw.terminate()
