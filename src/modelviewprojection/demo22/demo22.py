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

# Demo 22 -- "3D Effects" / Block.
# Ported from OpenGL SuperBible 4e, chapter 1 example "Block".  Pick
# one of four progressively-more-realistic renderings of the same
# scene from the imgui control panel:
#
#   step 0:  wireframe cube (every edge drawn)
#   step 1:  solid uniform-colour cube (looks 2-D and goofy)
#   step 2:  same cube, with a directional light + Lambert shading
#   step 3:  textured cube + textured floor + shadow-mapped shadows
#
# Implementation notes:
#
# * OpenGL 3.3 core profile.  No fixed-function lighting/texturing --
#   every stage goes through the same shader pair (block.vert /
#   block.frag) with different uniforms.
# * Shadows are computed via a real two-pass shadow map:  first the
#   scene is rendered from the *light's* point of view into an
#   off-screen depth FBO (depth.vert / depth.frag), then the color
#   pass samples that depth map per-fragment to test occlusion.
# * `planar_shadow_matrix` (the original cheap-projection trick) is
#   still defined and book-referenced for the chapter, but is no
#   longer used at runtime.
# * The view rotation starts at +30 degrees about X and -30 degrees
#   about Y, matching the SuperBible original on the first frame.
#
# Controls:
#   ImGui panel            -- pick which stage to render
#   LEFT / RIGHT           -- yaw the camera
#   PAGE_UP / PAGE_DOWN    -- pitch the camera
#   UP / DOWN              -- walk forward / backward (camera relative)
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
    600, 600, "ModelViewProjection Demo 22 -- 3D Effects",
    None, None,
)
if not window:
    glfw.terminate()
    sys.exit()
glfw.make_context_current(window)


# ImGui setup -- mirrors the pattern used in demo21.
imgui.create_context()
impl = GlfwRenderer(window)


n_step: int = 0
STAGE_LABELS: list[str] = [
    "0  --  wireframe",
    "1  --  solid (no lighting)",
    "2  --  solid + Lambert lighting",
    "3  --  textured + lit + shadow-mapped",
]
# Only stage 3 turns shadows on -- stages 0-2 don't need the depth
# pre-pass and skip it (saves work, and keeps the visual output
# consistent with the labels).
SHADOW_STAGE: int = 3

# Light direction (toward the light, normalized) is parameterized by
# spherical coords so it can be slid live; both the Lambert shading on
# the cube AND the planar shadow on the floor reshape together when
# the user moves the slider, which is the whole pedagogical point.
# Defaults are tuned to put the cone+bulb marker centered in the
# starting camera view (camera at +x, +y, +z looking back toward
# origin):  az 60°, el 30° puts light_dir antiparallel to camera-
# forward, so the bulb sits in front of the cube from the camera's
# POV.  The SuperBible original was light direction (-80, 120, 100) ≈
# (az 129°, el 43°), which is more "physical" (sun above and to the
# left) but hides the marker behind the camera.  Slide and explore.
light_az_deg: float = 60.0
light_el_deg: float = 30.0


def on_key(win, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(win, 1)


# Setting our key callback after GlfwRenderer was constructed replaces
# the renderer's default keyboard handler.  That is fine here -- we
# only need the mouse to interact with the imgui radio buttons, and
# GlfwRenderer's mouse callbacks were installed separately and remain
# in place.
glfw.set_key_callback(window, on_key)


@dataclasses.dataclass
class Camera:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rot_y: float = 0.0
    rot_x: float = 0.0


# Initial pose:  position the camera so the cube and floor are visible
# at roughly the same angle as the SuperBible original (+30 deg X,
# -30 deg Y baked into the world).  Re-deriving:  the world rotation
# R_x(30) * R_y(-30) is equivalent to a camera with yaw = +30, pitch =
# -30 looking back along that direction.  Distance ~100 from the cube.
camera: Camera = Camera(
    x=40.0,
    y=43.0,
    z=85.0,
    rot_y=math.radians(30.0),
    rot_x=math.radians(-30.0),
)


def handle_inputs() -> None:
    """Same control scheme as demos 19 and 21:
       LEFT/RIGHT yaw, PAGE_UP/PAGE_DOWN pitch, UP/DOWN walk."""
    global camera
    move_step: float = 2.0  # scene units; cube is 50 units across

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


GL.glClearColor(0.0, 0.0, 0.0, 1.0)
GL.glEnable(GL.GL_DEPTH_TEST)
GL.glClearDepth(1.0)
GL.glDepthFunc(GL.GL_LEQUAL)
#GL.glLineWidth(2)


# ---------------------------------------------------------------------------
# Shader program
# ---------------------------------------------------------------------------


def _compile(vert_name: str, frag_name: str) -> int:
    with open(os.path.join(pwd, vert_name)) as f:
        vs = shaders.compileShader(f.read(), GL.GL_VERTEX_SHADER)
    with open(os.path.join(pwd, frag_name)) as f:
        fs = shaders.compileShader(f.read(), GL.GL_FRAGMENT_SHADER)
    return shaders.compileProgram(vs, fs)


# Two programs:  the main one for the color pass, and a depth-only
# program for the shadow-map pre-pass (it just rasterizes positions
# into the depth buffer of an off-screen FBO).
program: int = _compile("block.vert", "block.frag")
depth_program: int = _compile("depth.vert", "depth.frag")

u_mvp = GL.glGetUniformLocation(program, "mvpMatrix")
u_model = GL.glGetUniformLocation(program, "modelMatrix")
u_flat = GL.glGetUniformLocation(program, "flatColor")
u_use_lighting = GL.glGetUniformLocation(program, "useLighting")
u_use_texture = GL.glGetUniformLocation(program, "useTexture")
u_use_shadows = GL.glGetUniformLocation(program, "useShadows")
u_light_dir = GL.glGetUniformLocation(program, "lightDirWS")
u_ambient = GL.glGetUniformLocation(program, "ambientColor")
u_diffuse = GL.glGetUniformLocation(program, "diffuseColor")
u_tex = GL.glGetUniformLocation(program, "tex")
u_shadow_map = GL.glGetUniformLocation(program, "shadowMap")
u_light_space = GL.glGetUniformLocation(program, "lightSpaceMatrix")

# Depth program has its own (much smaller) uniform set.
u_depth_model = GL.glGetUniformLocation(depth_program, "modelMatrix")
u_depth_light_space = GL.glGetUniformLocation(
    depth_program, "lightSpaceMatrix"
)


def set_mvp_uniforms() -> None:
    """Push the current pyMatrixStack matrices into the bound program."""
    GL.glUniformMatrix4fv(
        u_mvp,
        1,
        GL.GL_TRUE,  # row-major, since pyMatrixStack stores row-major
        np.ascontiguousarray(
            ms.get_current_matrix(ms.MatrixStack.modelviewprojection),
            dtype=np.float32,
        ),
    )
    GL.glUniformMatrix4fv(
        u_model,
        1,
        GL.GL_TRUE,
        np.ascontiguousarray(
            ms.get_current_matrix(ms.MatrixStack.model),
            dtype=np.float32,
        ),
    )


# ---------------------------------------------------------------------------
# Texture loading
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
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR
    )
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR
    )
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
    GL.glTexImage2D(
        GL.GL_TEXTURE_2D,
        0,
        GL.GL_RGB8,
        w,
        h,
        0,
        GL.GL_RGB,
        GL.GL_UNSIGNED_BYTE,
        img,
    )
    GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
    return tex


tex_floor = load_texture(os.path.join(pwd, "floor.tga"))
tex_block_front = load_texture(os.path.join(pwd, "Block4.tga"))
tex_block_top = load_texture(os.path.join(pwd, "Block5.tga"))
tex_block_right = load_texture(os.path.join(pwd, "Block6.tga"))


# ---------------------------------------------------------------------------
# Geometry helpers.  Each VAO uses three attributes:
#   location 0: position (vec3)
#   location 1: normal   (vec3)   -- ignored when lighting is off
#   location 2: texcoord (vec2)   -- ignored when texturing is off
# Wireframe VAOs put zeros in normal/texcoord since they are unused.
# ---------------------------------------------------------------------------


_FLOATS_PER_VERTEX = 8  # 3 pos + 3 normal + 2 uv
_STRIDE = _FLOATS_PER_VERTEX * 4


def make_vao(vertex_data: np.ndarray) -> tuple[int, int, int]:
    """Build a VAO + VBO for an interleaved [pos3, normal3, uv2] array.
    Returns (vao, vbo, vertex_count).
    """
    vertex_data = np.ascontiguousarray(vertex_data, dtype=np.float32)
    vao = GL.glGenVertexArrays(1)
    vbo = GL.glGenBuffers(1)

    GL.glBindVertexArray(vao)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
    GL.glBufferData(
        GL.GL_ARRAY_BUFFER,
        vertex_data.nbytes,
        vertex_data,
        GL.GL_STATIC_DRAW,
    )

    # position
    GL.glEnableVertexAttribArray(0)
    GL.glVertexAttribPointer(
        0, 3, GL.GL_FLOAT, False, _STRIDE, ctypes.c_void_p(0)
    )
    # normal
    GL.glEnableVertexAttribArray(1)
    GL.glVertexAttribPointer(
        1, 3, GL.GL_FLOAT, False, _STRIDE, ctypes.c_void_p(12)
    )
    # texcoord
    GL.glEnableVertexAttribArray(2)
    GL.glVertexAttribPointer(
        2, 2, GL.GL_FLOAT, False, _STRIDE, ctypes.c_void_p(24)
    )

    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    GL.glBindVertexArray(0)

    return vao, vbo, vertex_data.size // _FLOATS_PER_VERTEX


# Cube geometry --------------------------------------------------------------
#
# 8 corners of a 50x50x50 cube centered on the origin, then 6 faces, each
# with a single outward normal and the same 0..1 texcoord square.  Faces
# are laid out in this order (matters for stage 5 which textures a subset
# of faces):
#
#   face 0  +Z (front)
#   face 1  -Z (back)
#   face 2  +Y (top)
#   face 3  -Y (bottom)
#   face 4  +X (right)
#   face 5  -X (left)


def _build_cube_solid() -> np.ndarray:
    s = 25.0
    # for each face: 4 corner positions (CCW from outside), then a single
    # outward normal, then the corresponding 4 uv coords.
    faces = [
        # +Z
        (
            [(-s, -s, +s), (+s, -s, +s), (+s, +s, +s), (-s, +s, +s)],
            (0.0, 0.0, 1.0),
            [(0, 0), (1, 0), (1, 1), (0, 1)],
        ),
        # -Z
        (
            [(+s, -s, -s), (-s, -s, -s), (-s, +s, -s), (+s, +s, -s)],
            (0.0, 0.0, -1.0),
            [(0, 0), (1, 0), (1, 1), (0, 1)],
        ),
        # +Y
        (
            [(-s, +s, +s), (+s, +s, +s), (+s, +s, -s), (-s, +s, -s)],
            (0.0, 1.0, 0.0),
            [(0, 0), (1, 0), (1, 1), (0, 1)],
        ),
        # -Y
        (
            [(-s, -s, -s), (+s, -s, -s), (+s, -s, +s), (-s, -s, +s)],
            (0.0, -1.0, 0.0),
            [(0, 0), (1, 0), (1, 1), (0, 1)],
        ),
        # +X
        (
            [(+s, -s, +s), (+s, -s, -s), (+s, +s, -s), (+s, +s, +s)],
            (1.0, 0.0, 0.0),
            [(0, 0), (1, 0), (1, 1), (0, 1)],
        ),
        # -X
        (
            [(-s, -s, -s), (-s, -s, +s), (-s, +s, +s), (-s, +s, -s)],
            (-1.0, 0.0, 0.0),
            [(0, 0), (1, 0), (1, 1), (0, 1)],
        ),
    ]

    out: list[float] = []
    for corners, normal, uvs in faces:
        # two triangles per face: (0,1,2) and (0,2,3)
        for i in (0, 1, 2, 0, 2, 3):
            out.extend(corners[i])
            out.extend(normal)
            out.extend(uvs[i])
    return np.array(out, dtype=np.float32)


def _build_cube_wire_full() -> np.ndarray:
    s = 25.0
    corners = [
        (-s, -s, -s), (+s, -s, -s), (+s, +s, -s), (-s, +s, -s),  # back face
        (-s, -s, +s), (+s, -s, +s), (+s, +s, +s), (-s, +s, +s),  # front face
    ]
    edges = [
        # back face
        (0, 1), (1, 2), (2, 3), (3, 0),
        # front face
        (4, 5), (5, 6), (6, 7), (7, 4),
        # connecting edges
        (0, 4), (1, 5), (2, 6), (3, 7),
    ]
    out: list[float] = []
    for a, b in edges:
        for ci in (a, b):
            out.extend(corners[ci])
            out.extend((0.0, 0.0, 0.0))  # unused normal
            out.extend((0.0, 0.0))       # unused uv
    return np.array(out, dtype=np.float32)


cube_solid_vao, _, cube_solid_count = make_vao(_build_cube_solid())
cube_wire_vao, _, cube_wire_count = make_vao(_build_cube_wire_full())


# Floor geometry -------------------------------------------------------------

FLOOR_Y = -25.3


def _build_floor() -> np.ndarray:
    e = 100.0
    y = FLOOR_Y
    # CCW seen from above (+Y normal)
    corners = [(-e, y, -e), (-e, y, +e), (+e, y, +e), (+e, y, -e)]
    uvs = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]
    n = (0.0, 1.0, 0.0)
    out: list[float] = []
    for i in (0, 1, 2, 0, 2, 3):
        out.extend(corners[i])
        out.extend(n)
        out.extend(uvs[i])
    return np.array(out, dtype=np.float32)


floor_vao, floor_vbo, floor_count = make_vao(_build_floor())


# Light marker geometry ------------------------------------------------------
# A red cone + yellow bulb sized for this demo's units (cube is 50
# units across, floor at y=-25).  Cone radius 5, height 12; bulb
# radius 4.  Sits at LIGHT_MARKER_DISTANCE units along +light_dir.

def _build_marker_cone(radius: float, height: float,
                       slices: int) -> np.ndarray:
    """Cone with the base at z=0 and apex at z=+height, matching
    chapt05/spot.cpp's bulb-at-base / cone-body-behind layout.  In
    the demo's 8-float layout (pos + zero normal + zero uv).  Drawn
    unlit."""
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
            out.extend((0.0, 0.0))
    # Base cap:  outward normal is -z, winding (center, p[i+1], p[i]).
    for i in range(slices):
        for v in (base_center, base_pts[i + 1], base_pts[i]):
            out.extend(v)
            out.extend((0.0, 0.0, 0.0))
            out.extend((0.0, 0.0))
    return np.array(out, dtype=np.float32)


def _build_marker_sphere(radius: float, slices: int,
                         stacks: int) -> np.ndarray:
    """UV sphere for the bulb (8-float layout, unlit)."""
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


marker_cone_vao, marker_cone_vbo, marker_cone_count = make_vao(
    _build_marker_cone(radius=5.0, height=12.0, slices=20)
)
marker_bulb_vao, marker_bulb_vbo, marker_bulb_count = make_vao(
    _build_marker_sphere(radius=4.0, slices=16, stacks=10)
)
LIGHT_MARKER_DISTANCE: float = 55.0
LIGHT_MARKER_CONE_COLOR: tuple = (0.85, 0.15, 0.15)
LIGHT_MARKER_BULB_COLOR: tuple = (1.00, 1.00, 0.00)


# ---------------------------------------------------------------------------
# Lighting + planar shadow constants
# ---------------------------------------------------------------------------


# SuperBible used a constant directional light at (-80, 120, 100, 0).
# We compute the same vector each frame from the imgui azimuth/
# elevation sliders so the shadow on the floor reshapes when the
# user slides the light around.
def light_dir_ws(az_deg: float, el_deg: float) -> tuple[float, float, float]:
    az = math.radians(az_deg)
    el = math.radians(el_deg)
    return (
        math.cos(el) * math.cos(az),
        math.sin(el),
        math.cos(el) * math.sin(az),
    )

# floor plane equation:  ax + by + cz + d = 0.  Floor is y = FLOOR_Y, so:
FLOOR_PLANE = (0.0, 1.0, 0.0, -FLOOR_Y)


# doc-region-begin planar shadow
def planar_shadow_matrix(plane, light) -> np.matrix:
    """
    Returns a 4x4 matrix that, applied to a world-space point, projects
    that point onto `plane` along the direction (or position) `light`.

    plane: (a, b, c, d) such that a*x + b*y + c*z + d = 0.
    light: (Lx, Ly, Lz, Lw).  Lw == 0 for a directional light.

    This is a singular matrix (determinant zero) -- it collapses 3-space
    onto a 2-D plane, which is exactly what a shadow does.
    """
    a, b, c, d = plane
    lx, ly, lz, lw = light
    dot = a * lx + b * ly + c * lz + d * lw
    return np.matrix(
        [
            [dot - lx * a,    -lx * b,       -lx * c,       -lx * d],
            [-ly * a,         dot - ly * b,  -ly * c,       -ly * d],
            [-lz * a,         -lz * b,       dot - lz * c,  -lz * d],
            [-lw * a,         -lw * b,       -lw * c,       dot - lw * d],
        ],
        dtype=np.float32,
    )
# doc-region-end planar shadow


# planar_shadow_matrix() above is kept for the book chapter; the
# in-app shadow now goes through a real depth-buffer pre-pass instead.


# ---------------------------------------------------------------------------
# Shadow map -- off-screen depth-only framebuffer
# ---------------------------------------------------------------------------
# Standard recipe:
#   * texture with internal format GL_DEPTH_COMPONENT24, filter LINEAR
#     (so PCF would just work if we wanted it), wrap CLAMP_TO_BORDER
#     with a white border so anything outside the light's frustum
#     reads "max depth" (no shadow);
#   * FBO with that texture attached as GL_DEPTH_ATTACHMENT and no
#     color attachment -- glDrawBuffer/glReadBuffer set to GL_NONE.
#
# 1024 x 1024 is fine for this scene's size (~100x100 ground); large
# enough that shadow edges aren't visibly chunky.

SHADOW_MAP_SIZE: int = 1024

shadow_depth_tex = GL.glGenTextures(1)
GL.glBindTexture(GL.GL_TEXTURE_2D, shadow_depth_tex)
GL.glTexImage2D(
    GL.GL_TEXTURE_2D, 0, GL.GL_DEPTH_COMPONENT24,
    SHADOW_MAP_SIZE, SHADOW_MAP_SIZE, 0,
    GL.GL_DEPTH_COMPONENT, GL.GL_FLOAT, None,
)
GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
GL.glTexParameteri(
    GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_BORDER
)
GL.glTexParameteri(
    GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_BORDER
)
GL.glTexParameterfv(
    GL.GL_TEXTURE_2D, GL.GL_TEXTURE_BORDER_COLOR,
    np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
)
GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

shadow_fbo = GL.glGenFramebuffers(1)
GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, shadow_fbo)
GL.glFramebufferTexture2D(
    GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT,
    GL.GL_TEXTURE_2D, shadow_depth_tex, 0,
)
GL.glDrawBuffer(GL.GL_NONE)
GL.glReadBuffer(GL.GL_NONE)
if (GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER)
        != GL.GL_FRAMEBUFFER_COMPLETE):
    raise RuntimeError("shadow FBO is not complete")
GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)


def look_at(eye: np.ndarray, target: np.ndarray,
            up: np.ndarray) -> np.matrix:
    """Standard right-handed look-at:  build the world-to-view matrix
    that places `eye` at the origin looking toward `target`, with
    `up` defining the world's vertical."""
    f = target - eye
    f = f / np.linalg.norm(f)
    s = np.cross(f, up)
    s = s / np.linalg.norm(s)
    u = np.cross(s, f)
    m = np.identity(4, dtype=np.float32)
    m[0, 0:3] = s
    m[1, 0:3] = u
    m[2, 0:3] = -f
    m[0, 3] = -np.dot(s, eye)
    m[1, 3] = -np.dot(u, eye)
    m[2, 3] =  np.dot(f, eye)
    return np.matrix(m)


def ortho(l, r, b, t, n, f) -> np.matrix:
    """Right-handed orthographic projection.  Maps [l,r] x [b,t] x
    [-n,-f] (camera-space) to the [-1,1] cube of clip space."""
    m = np.identity(4, dtype=np.float32)
    m[0, 0] =  2.0 / (r - l)
    m[1, 1] =  2.0 / (t - b)
    m[2, 2] = -2.0 / (f - n)
    m[0, 3] = -(r + l) / (r - l)
    m[1, 3] = -(t + b) / (t - b)
    m[2, 3] = -(f + n) / (f - n)
    return np.matrix(m)


def light_space_matrix(light_dir_vec) -> np.matrix:
    """Light view + projection.  For this directional light we put a
    pretend "eye" 200 units back along -light_dir from the scene
    center, frame the cube + visible floor in an orthographic frustum,
    and return projection * view as a single 4x4 ready to feed both
    the depth pass and the color pass.

    The frustum bounds (-80..+80 in xy, 1..400 in z) are sized to
    contain the cube (50 units, centered at (-10, 0, 10)) and a
    chunk of the floor wide enough for its shadow."""
    scene_center = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    ld = np.array(light_dir_vec, dtype=np.float32)
    eye = scene_center + ld * 200.0
    # Pick "up" to avoid the degenerate case when light is straight
    # up.  Z works because our light never has z exactly +/-1 within
    # the slider's elevation range.
    up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    if abs(ld[1]) > 0.999:
        up = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    view = look_at(eye, scene_center, up)
    proj = ortho(-80.0, 80.0, -80.0, 80.0, 1.0, 400.0)
    return proj @ view


# ---------------------------------------------------------------------------
# Per-stage rendering
# ---------------------------------------------------------------------------


def setup_uniforms(
    *,
    use_lighting: bool,
    use_texture: bool,
    use_shadows: bool = False,
    flat_color: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> None:
    GL.glUniform1i(u_use_lighting, 1 if use_lighting else 0)
    GL.glUniform1i(u_use_texture, 1 if use_texture else 0)
    GL.glUniform1i(u_use_shadows, 1 if use_shadows else 0)
    GL.glUniform3f(u_flat, *flat_color)
    GL.glUniform3f(u_light_dir, *light_dir)   # set in main loop each frame
    GL.glUniform3f(u_ambient, 0.2, 0.2, 0.2)
    GL.glUniform3f(u_diffuse, 0.7, 0.7, 0.7)
    GL.glUniform1i(u_tex, 0)
    GL.glUniform1i(u_shadow_map, 1)   # texture unit 1 for the depth map


def draw_floor(stage: int) -> None:
    with ms.push_matrix(ms.MatrixStack.model):
        if stage == 3:
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, tex_floor)
            # Floor is the main shadow receiver -- it gets the lit
            # path with shadows on, which is the whole reason this
            # demo went to a real shadow map.
            setup_uniforms(use_lighting=True, use_texture=True,
                           use_shadows=True)
        else:
            setup_uniforms(
                use_lighting=False,
                use_texture=False,
                flat_color=(0.0, 0.0, 0.9),
            )
        set_mvp_uniforms()
        GL.glBindVertexArray(floor_vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, floor_count)
        GL.glBindVertexArray(0)


def draw_cube(stage: int) -> None:
    """Draw the cube.  Stage 3 also receives shadows (the cube can
    self-shadow on its own underside, and from this angle the floor
    can shadow it back when the light is low)."""

    with ms.push_matrix(ms.MatrixStack.model):
        ms.translate(ms.MatrixStack.model, -10.0, 0.0, 10.0)

        if stage == 0:
            # full wireframe
            setup_uniforms(
                use_lighting=False,
                use_texture=False,
                flat_color=(1.0, 0.0, 0.0),
            )
            set_mvp_uniforms()
            GL.glBindVertexArray(cube_wire_vao)
            GL.glDrawArrays(GL.GL_LINES, 0, cube_wire_count)
            GL.glBindVertexArray(0)

        elif stage == 1:
            # solid uniform red -- no lighting, no texture
            setup_uniforms(
                use_lighting=False,
                use_texture=False,
                flat_color=(0.8, 0.0, 0.0),
            )
            set_mvp_uniforms()
            GL.glBindVertexArray(cube_solid_vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, cube_solid_count)
            GL.glBindVertexArray(0)

        elif stage == 2:
            # lit cube, no shadows yet
            setup_uniforms(
                use_lighting=True,
                use_texture=False,
                flat_color=(0.8, 0.0, 0.0),
            )
            set_mvp_uniforms()
            GL.glBindVertexArray(cube_solid_vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, cube_solid_count)
            GL.glBindVertexArray(0)

        elif stage == 3:
            # textured cube on all six faces + lit + shadow-mapped.
            # Opposite faces share a texture; vertex offsets in the
            # solid VAO are 6 apart in the order:
            # +Z, -Z, +Y, -Y, +X, -X.
            faces_to_draw = [
                (tex_block_front, 0),   # +Z front
                (tex_block_front, 6),   # -Z back
                (tex_block_top,   12),  # +Y top
                (tex_block_top,   18),  # -Y bottom
                (tex_block_right, 24),  # +X right
                (tex_block_right, 30),  # -X left
            ]
            setup_uniforms(use_lighting=True, use_texture=True,
                           use_shadows=True)
            set_mvp_uniforms()
            GL.glBindVertexArray(cube_solid_vao)
            for tex, off in faces_to_draw:
                GL.glActiveTexture(GL.GL_TEXTURE0)
                GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
                GL.glDrawArrays(GL.GL_TRIANGLES, off, 6)
            GL.glBindVertexArray(0)


def draw_shadow_casters(stage: int) -> None:
    """Single pass that draws ONLY the shadow-casting geometry into
    the depth FBO -- ground+cube here, no light marker (the bulb
    shouldn't shadow itself).  Caller has already bound the depth
    program and set lightSpaceMatrix; we just need to set modelMatrix
    and issue draw calls for each piece.

    For correctness we draw both the floor (so it can self-shadow at
    grazing angles) and the cube (the main caster).  At stages 0-2
    this function is never called -- the depth pass is gated."""
    # Floor
    with ms.push_matrix(ms.MatrixStack.model):
        GL.glUniformMatrix4fv(
            u_depth_model, 1, GL.GL_TRUE,
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.model),
                dtype=np.float32,
            ),
        )
        GL.glBindVertexArray(floor_vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, floor_count)

    # Cube
    with ms.push_matrix(ms.MatrixStack.model):
        ms.translate(ms.MatrixStack.model, -10.0, 0.0, 10.0)
        GL.glUniformMatrix4fv(
            u_depth_model, 1, GL.GL_TRUE,
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.model),
                dtype=np.float32,
            ),
        )
        GL.glBindVertexArray(cube_solid_vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, cube_solid_count)
    GL.glBindVertexArray(0)


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

    # Build the imgui frame.  Always do imgui.new_frame() before any
    # imgui call this frame, and pair it with imgui.render() / impl.render
    # before swapping buffers.
    imgui.new_frame()
    imgui.set_next_window_size(
        imgui.ImVec2(320, 320), imgui.Cond_.first_use_ever
    )
    imgui.begin("Rendering stage", True)
    imgui.text("Pick the level of realism:")
    imgui.separator()
    for i, label in enumerate(STAGE_LABELS):
        if imgui.radio_button(label, n_step == i):
            n_step = i
    imgui.separator()
    imgui.text("Light direction (red cone + yellow bulb):")
    _, light_az_deg = imgui.slider_float(
        "Azimuth (deg)", light_az_deg, 0.0, 360.0)
    _, light_el_deg = imgui.slider_float(
        "Elevation (deg)", light_el_deg, 5.0, 89.0)
    imgui.end()

    # Recompute light each frame so sliding it reshapes both the
    # Lambert shading AND the shadow map.
    light_dir = light_dir_ws(light_az_deg, light_el_deg)
    light_space = light_space_matrix(light_dir)
    light_space_arr = np.ascontiguousarray(light_space, dtype=np.float32)

    width, height = glfw.get_framebuffer_size(window)

    # ============================================================
    # Pass 1 -- depth pre-pass into the shadow FBO.  Only run for
    # the stage that actually uses shadows; otherwise the depth map
    # is junk-but-unused so we can skip the GPU work.
    # ============================================================
    if n_step == SHADOW_STAGE:
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, shadow_fbo)
        GL.glViewport(0, 0, SHADOW_MAP_SIZE, SHADOW_MAP_SIZE)
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
        # Front-face culling during the depth pass shifts shadow acne
        # to the *outside* of objects, where it's hidden by the
        # geometry itself.  Common trick.  Back to back-face culling
        # for the color pass.
        GL.glCullFace(GL.GL_FRONT)
        GL.glUseProgram(depth_program)
        GL.glUniformMatrix4fv(
            u_depth_light_space, 1, GL.GL_TRUE, light_space_arr
        )
        ms.set_to_identity_matrix(ms.MatrixStack.model)
        draw_shadow_casters(n_step)
        GL.glUseProgram(0)
        GL.glCullFace(GL.GL_BACK)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    # ============================================================
    # Pass 2 -- regular color pass into the default framebuffer.
    # ============================================================
    GL.glViewport(0, 0, width, height)
    GL.glClear(sum([GL.GL_COLOR_BUFFER_BIT, GL.GL_DEPTH_BUFFER_BIT]))

    ms.set_to_identity_matrix(ms.MatrixStack.model)
    ms.set_to_identity_matrix(ms.MatrixStack.view)
    ms.set_to_identity_matrix(ms.MatrixStack.projection)

    aspect = float(width) / float(height) if height > 0 else 1.0
    ms.perspective(
        field_of_view=45.0,
        aspect_ratio=aspect,
        near_z=1.0,
        far_z=1000.0,
    )

    ms.rotate_x(ms.MatrixStack.view, -camera.rot_x)
    ms.rotate_y(ms.MatrixStack.view, -camera.rot_y)
    ms.translate(ms.MatrixStack.view, -camera.x, -camera.y, -camera.z)

    GL.glUseProgram(program)
    # Bind the depth map on texture unit 1 -- u_shadow_map=1 was set
    # by setup_uniforms.  Stays bound across all the lit draws below.
    GL.glActiveTexture(GL.GL_TEXTURE1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, shadow_depth_tex)
    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glUniformMatrix4fv(u_light_space, 1, GL.GL_TRUE, light_space_arr)

    draw_floor(n_step)
    draw_cube(n_step)

    # ---- Light marker (red cone + yellow bulb) ----
    # Adapted from chapt05/spot.cpp:79-94.  Cone's local +z aligns with
    # +light_dir, base sits at the bulb, apex points back toward the
    # scene.  Drawn unlit so it doesn't shade against itself.
    with ms.push_matrix(ms.MatrixStack.model):
        ms.translate(ms.MatrixStack.model,
                     light_dir[0] * LIGHT_MARKER_DISTANCE,
                     light_dir[1] * LIGHT_MARKER_DISTANCE,
                     light_dir[2] * LIGHT_MARKER_DISTANCE)
        # Rotation chain:  T @ R_y(90 - az) @ R_x(-el).  See demo22a.
        ms.rotate_y(ms.MatrixStack.model,
                    math.radians(90.0 - light_az_deg))
        ms.rotate_x(ms.MatrixStack.model,
                    math.radians(-light_el_deg))

        setup_uniforms(use_lighting=False, use_texture=False,
                       flat_color=LIGHT_MARKER_CONE_COLOR)
        set_mvp_uniforms()
        GL.glBindVertexArray(marker_cone_vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, marker_cone_count)
        GL.glBindVertexArray(0)

        # Bulb at the base of the cone (= local origin).
        setup_uniforms(use_lighting=False, use_texture=False,
                       flat_color=LIGHT_MARKER_BULB_COLOR)
        set_mvp_uniforms()
        GL.glBindVertexArray(marker_bulb_vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, marker_bulb_count)
        GL.glBindVertexArray(0)

    GL.glUseProgram(0)

    imgui.render()
    impl.render(imgui.get_draw_data())

    glfw.swap_buffers(window)


glfw.terminate()
