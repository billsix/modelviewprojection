
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
# one of six progressively-more-realistic renderings of the same scene
# from the imgui control panel:
#
#   step 0:  wireframe cube (every edge drawn)
#   step 1:  solid uniform-colour cube (looks 2-D and goofy)
#   step 2:  same cube, with a directional light + Lambert shading
#   step 3:  lit cube + shadow on the floor
#   step 4:  textured cube + textured floor + shadow
#
# Stages 3 and 4 cast a shadow on the floor.  TWO algorithms are
# implemented and selectable from the imgui panel:
#
#   "planar"      -- collapse the cube onto the floor plane via a
#                    rank-3 4x4 matrix (`planar_shadow_matrix`); draw
#                    the flattened cube as a black quad.  Cheap and
#                    exact for shadows on a single plane, but can't
#                    handle a cube shadowing itself or shadows on
#                    non-planar surfaces.
#
#   "shadow_map"  -- render the scene from the light's POV into a
#                    1024x1024 depth texture, then in a second pass
#                    sample that texture per fragment to decide
#                    whether the fragment is in shadow.  General-
#                    purpose; works on arbitrary geometry.  Compare
#                    by toggling the radio button while watching the
#                    floor.
#
# A "View shadow map" checkbox in the panel replaces the scene with a
# fullscreen visualization of the depth texture so students can see
# what the light "sees".  Same idea as the SuperBible v7 shadowmapping
# debug view.
#
# Implementation notes:
#
# * OpenGL 3.3 core profile.  No fixed-function lighting/texturing --
#   the planar / Lambert path goes through block.vert / block.frag,
#   the shadow-mapping path uses three additional inline shader pairs
#   (declared in this file as multi-line strings, not separate .vert /
#   .frag files):  one for rendering the depth pass, one for the
#   camera pass with shadow lookup, one for the depth visualization.
# * The "planar shadow" is a real linear transformation:  a 4x4 matrix
#   that flattens any point onto the floor plane along the light
#   direction.  See `planar_shadow_matrix` below.
# * The view rotation starts at +30 degrees about X and -30 degrees
#   about Y, matching the SuperBible original on the first frame.
#
# Controls:
#   ImGui panel            -- pick stage, shadow algorithm, depth view
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
from modelviewprojection.cameracontrols import walk_around_camera
from modelviewprojection.shading import light_dir_ws
from modelviewprojection.windowing import on_key

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

# macOS Core Profile requires a non-zero VAO bound at all times for
# any vertex-attribute or draw call (VAO 0 is prohibited).  Generate
# one here and leave it bound as the default; per-mesh VAOs
# override-bind when they need a specific layout, and we never call
# glBindVertexArray(0).  Mesa and NVIDIA tolerate the spec violation
# silently; Apple's driver does not.
_default_vao = GL.glGenVertexArrays(1)
GL.glBindVertexArray(_default_vao)


# ImGui setup -- mirrors the pattern used in demo21.
imgui.create_context()
impl = GlfwRenderer(window)


n_step: int = 0
STAGE_LABELS: list[str] = [
    "0  --  wireframe",
    "1  --  solid (no lighting)",
    "2  --  solid + Lambert lighting",
    "3  --  lit + shadow",
    "4  --  textured + lit + shadow",
]

# Shadow technique used for stages 3 and 4.  ``"planar"`` is the
# original SuperBible / demo22 approach: a 4x4 flatten matrix collapses
# the cube onto the floor and we draw the flattened cube as a black
# quad.  ``"shadow_map"`` is the two-pass texture-based approach:
# render the scene from the light's POV into a depth texture, then
# sample it per fragment in the camera pass.  See the long header
# comment for the comparison.
shadow_algo: str = "planar"

# When True, the main render loop short-circuits and just draws the
# fullscreen visualization of the depth texture.  Only meaningful when
# ``shadow_algo == "shadow_map"``; the planar path doesn't have a
# shadow map to view.
view_shadow_map: bool = False

# Shadow map resolution.  1024 is plenty for a cube + floor and keeps
# the FBO under 4 MB; the v7 shadowmapping demo uses 4096 because its
# scene has 4 distinct objects, but here we only have one occluder.
SHADOW_TEX_SIZE: int = 1024

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
    # scene units; cube is 50 units across
    walk_around_camera(window, camera, move_step=2.0)


GL.glClearColor(0.0, 0.0, 0.0, 1.0)
GL.glEnable(GL.GL_DEPTH_TEST)
GL.glClearDepth(1.0)
GL.glDepthFunc(GL.GL_LEQUAL)
#GL.glLineWidth(2)


# ---------------------------------------------------------------------------
# Shader program
# ---------------------------------------------------------------------------


def compile_shader_program() -> int:
    with open(os.path.join(pwd, "block.vert")) as f:
        vs = shaders.compileShader(f.read(), GL.GL_VERTEX_SHADER)
    with open(os.path.join(pwd, "block.frag")) as f:
        fs = shaders.compileShader(f.read(), GL.GL_FRAGMENT_SHADER)
    # validate=False -- see _compile_inline below for the macOS reason.
    return shaders.compileProgram(vs, fs, validate=False)


# This file has four shader pipelines side-by-side, plus an FBO + two
# textures used for shadow mapping.  Group each pipeline's program
# handle and uniform locations into one dataclass per pipeline -- only
# one instance of each, but the grouping replaces ~30 ungrouped
# globals with five named bundles, and makes "this u_mvp belongs to
# the main lit program, that u_mvp belongs to the block-shadow
# program" obvious at the call site (main.u_mvp vs block_shadow.u_mvp).
# The `u_` prefix on uniform
# fields keeps them visually distinct from non-uniform fields.
@dataclasses.dataclass(frozen=True)
class MainPipeline:
    """Lit + textured pass that does NOT consume a shadow map."""
    program: int
    u_mvp: int
    u_model: int
    u_flat: int
    u_use_lighting: int
    u_use_texture: int
    u_light_dir: int
    u_ambient: int
    u_diffuse: int
    u_tex: int


def _build_main_pipeline() -> MainPipeline:
    prog = compile_shader_program()
    return MainPipeline(
        program=prog,
        u_mvp=GL.glGetUniformLocation(prog, "mvpMatrix"),
        u_model=GL.glGetUniformLocation(prog, "modelMatrix"),
        u_flat=GL.glGetUniformLocation(prog, "flatColor"),
        u_use_lighting=GL.glGetUniformLocation(prog, "useLighting"),
        u_use_texture=GL.glGetUniformLocation(prog, "useTexture"),
        u_light_dir=GL.glGetUniformLocation(prog, "lightDirWS"),
        u_ambient=GL.glGetUniformLocation(prog, "ambientColor"),
        u_diffuse=GL.glGetUniformLocation(prog, "diffuseColor"),
        u_tex=GL.glGetUniformLocation(prog, "tex"),
    )


main = _build_main_pipeline()


# ---------------------------------------------------------------------------
# Shadow-mapping shaders (inline)
# ---------------------------------------------------------------------------
#
# These are kept here as Python strings rather than being broken out into
# .vert / .frag files because they're additive teaching content -- the
# original Block demo uses just block.vert / block.frag and we want
# students to be able to read those without distraction.  The shadow-
# mapping path is opt-in via the imgui radio.

# Light pass: render the scene from the light's POV.  We don't even
# need a fragment stage that writes a real color -- the depth buffer
# is the only thing we keep.  We do bind a R32F color attachment too
# so the same FBO can be sampled as a normal 2D texture for the
# "View shadow map" overlay (sampler2DShadow can't be sampled with a
# regular texture() call).
SHADOW_DEPTH_VS = """
#version 330 core
layout (location = 0) in vec3 position;
uniform mat4 lightMVP;        // = lightProj * lightView * model
void main() {
    gl_Position = lightMVP * vec4(position, 1.0);
}
"""

SHADOW_DEPTH_FS = """
#version 330 core
out float depth_out;          // R32F color attachment, just for visualization
void main() {
    depth_out = gl_FragCoord.z;
}
"""

# Camera pass with shadow lookup.  Same lighting math as block.frag,
# plus a sampler2DShadow lookup whose result multiplies the diffuse
# term.  ``shadowCoord`` is the fragment's position transformed into
# the light's clip space, scale-biased into [0, 1] texture coords;
# textureProj does the perspective divide and depth comparison in
# hardware.
BLOCK_SHADOW_VS = """
#version 330 core
layout (location = 0) in vec3 position;
layout (location = 1) in vec3 normal_in;
layout (location = 2) in vec2 texcoord_in;

uniform mat4 mvpMatrix;
uniform mat4 modelMatrix;
uniform mat4 shadowMatrix;    // = scaleBias * lightProj * lightView * model

out vec3 v_normal_ws;
out vec2 v_texcoord;
out vec4 v_shadow_coord;

void main() {
    gl_Position   = mvpMatrix * vec4(position, 1.0);
    v_normal_ws   = mat3(modelMatrix) * normal_in;
    v_texcoord    = texcoord_in;
    v_shadow_coord = shadowMatrix * vec4(position, 1.0);
}
"""

BLOCK_SHADOW_FS = """
#version 330 core
in vec3 v_normal_ws;
in vec2 v_texcoord;
in vec4 v_shadow_coord;

uniform vec3 flatColor;
uniform bool useLighting;
uniform bool useTexture;
uniform vec3 lightDirWS;
uniform vec3 ambientColor;
uniform vec3 diffuseColor;
uniform sampler2D tex;
uniform sampler2DShadow shadowMap;

out vec4 fragColor;

void main() {
    vec3 base = useTexture ? texture(tex, v_texcoord).rgb : flatColor;
    if (useLighting) {
        vec3 n = normalize(v_normal_ws);
        float diff = max(dot(n, normalize(lightDirWS)), 0.0);
        // textureProj returns 1.0 if the fragment is closer to the
        // light than the recorded depth (i.e. lit), 0.0 if occluded.
        // Hardware does perspective divide + depth compare for us.
        float lit_factor = textureProj(shadowMap, v_shadow_coord);
        vec3 lit = ambientColor * base
                 + diffuseColor * base * diff * lit_factor;
        fragColor = vec4(lit, 1.0);
    } else {
        fragColor = vec4(base, 1.0);
    }
}
"""

# Fullscreen quad that visualizes the depth texture.  Uses normalized
# UVs so the depth map fills the whole window regardless of either
# the framebuffer size or the depth texture size.  See feedback memory
# `feedback_render_to_texture_match_framebuffer.md`.
SHADOW_VIEW_VS = """
#version 330 core
out vec2 v_uv;
void main() {
    const vec4 verts[4] = vec4[4](
        vec4(-1.0, -1.0, 0.5, 1.0),
        vec4( 1.0, -1.0, 0.5, 1.0),
        vec4(-1.0,  1.0, 0.5, 1.0),
        vec4( 1.0,  1.0, 0.5, 1.0)
    );
    const vec2 uvs[4] = vec2[4](
        vec2(0.0, 0.0), vec2(1.0, 0.0),
        vec2(0.0, 1.0), vec2(1.0, 1.0)
    );
    gl_Position = verts[gl_VertexID];
    v_uv = uvs[gl_VertexID];
}
"""

SHADOW_VIEW_FS = """
#version 330 core
in vec2 v_uv;
uniform sampler2D depthTex;     // R32F debug attachment, not the sampler2DShadow
out vec4 fragColor;

void main() {
    float d = texture(depthTex, v_uv).r;
    // The depth values cluster near the far plane; remap so the
    // contents are visible.  Same trick as the v7 shadowmapping demo.
    d = (d - 0.95) * 15.0;
    fragColor = vec4(d, d, d, 1.0);
}
"""


def _compile_inline(vs_src: str, fs_src: str) -> int:
    # validate=False: PyOpenGL otherwise runs glValidateProgram
    # immediately after link, which on macOS Core Profile complains
    # that samplers of different types share texture unit 0 (the
    # default) -- e.g. block_shadow.program has both `tex` (sampler2D)
    # and `shadowMap` (sampler2DShadow).  We assign each sampler its
    # own unit at draw time, so the validation is too eager.  Mesa
    # and NVIDIA don't run the check at link time so this is silently
    # OK there.
    return shaders.compileProgram(
        shaders.compileShader(vs_src, GL.GL_VERTEX_SHADER),
        shaders.compileShader(fs_src, GL.GL_FRAGMENT_SHADER),
        validate=False,
    )


@dataclasses.dataclass(frozen=True)
class ShadowDepthPipeline:
    """Depth-only render from the light's POV, into the shadow FBO."""
    program: int
    u_lightMVP: int


@dataclasses.dataclass(frozen=True)
class BlockShadowPipeline:
    """Same scene draw as MainPipeline, but consumes the shadow map."""
    program: int
    u_mvp: int
    u_model: int
    u_shadow: int          # shadowMatrix = scaleBias * lightProj * lightView * model
    u_flat: int
    u_use_lighting: int
    u_use_texture: int
    u_light_dir: int
    u_ambient: int
    u_diffuse: int
    u_tex: int
    u_shadow_map: int


@dataclasses.dataclass(frozen=True)
class ShadowViewPipeline:
    """Fullscreen-quad debug overlay sampling the shadow depth texture."""
    program: int
    u_depth_tex: int


def _build_shadow_depth_pipeline() -> ShadowDepthPipeline:
    prog = _compile_inline(SHADOW_DEPTH_VS, SHADOW_DEPTH_FS)
    return ShadowDepthPipeline(
        program=prog,
        u_lightMVP=GL.glGetUniformLocation(prog, "lightMVP"),
    )


def _build_block_shadow_pipeline() -> BlockShadowPipeline:
    prog = _compile_inline(BLOCK_SHADOW_VS, BLOCK_SHADOW_FS)
    return BlockShadowPipeline(
        program=prog,
        u_mvp=GL.glGetUniformLocation(prog, "mvpMatrix"),
        u_model=GL.glGetUniformLocation(prog, "modelMatrix"),
        u_shadow=GL.glGetUniformLocation(prog, "shadowMatrix"),
        u_flat=GL.glGetUniformLocation(prog, "flatColor"),
        u_use_lighting=GL.glGetUniformLocation(prog, "useLighting"),
        u_use_texture=GL.glGetUniformLocation(prog, "useTexture"),
        u_light_dir=GL.glGetUniformLocation(prog, "lightDirWS"),
        u_ambient=GL.glGetUniformLocation(prog, "ambientColor"),
        u_diffuse=GL.glGetUniformLocation(prog, "diffuseColor"),
        u_tex=GL.glGetUniformLocation(prog, "tex"),
        u_shadow_map=GL.glGetUniformLocation(prog, "shadowMap"),
    )


def _build_shadow_view_pipeline() -> ShadowViewPipeline:
    prog = _compile_inline(SHADOW_VIEW_VS, SHADOW_VIEW_FS)
    return ShadowViewPipeline(
        program=prog,
        u_depth_tex=GL.glGetUniformLocation(prog, "depthTex"),
    )


shadow_depth = _build_shadow_depth_pipeline()
block_shadow = _build_block_shadow_pipeline()
shadow_view = _build_shadow_view_pipeline()


# ---------------------------------------------------------------------------
# Shadow-map FBO + textures
# ---------------------------------------------------------------------------
#
# Two attachments: a depth texture used as ``sampler2DShadow`` in the
# camera pass, and an R32F color attachment that mirrors the depth
# values for the "View shadow map" debug overlay (sampler2DShadow
# can't be sampled with a plain ``texture()`` call).

@dataclasses.dataclass(frozen=True)
class ShadowResources:
    """The FBO and two textures used for shadow mapping.

    Two attachments: a depth texture used as ``sampler2DShadow`` in
    the camera pass, and an R32F color attachment that mirrors the
    depth values for the "View shadow map" debug overlay
    (``sampler2DShadow`` can't be sampled with a plain ``texture()``).
    """
    fbo: int
    depth_tex: int       # GL_DEPTH_COMPONENT32F, used as sampler2DShadow
    debug_tex: int       # GL_R32F, color attachment for the debug overlay


def _build_shadow_resources() -> ShadowResources:
    fbo = GL.glGenFramebuffers(1)
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fbo)

    depth_tex = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, depth_tex)
    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_DEPTH_COMPONENT32F,
                    SHADOW_TEX_SIZE, SHADOW_TEX_SIZE, 0,
                    GL.GL_DEPTH_COMPONENT, GL.GL_FLOAT, None)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
    # Hardware depth comparison so textureProj gives back 0/1 directly.
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_COMPARE_MODE,
                       GL.GL_COMPARE_REF_TO_TEXTURE)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_COMPARE_FUNC,
                       GL.GL_LEQUAL)
    GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT,
                              GL.GL_TEXTURE_2D, depth_tex, 0)

    debug_tex = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, debug_tex)
    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_R32F,
                    SHADOW_TEX_SIZE, SHADOW_TEX_SIZE, 0,
                    GL.GL_RED, GL.GL_FLOAT, None)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0,
                              GL.GL_TEXTURE_2D, debug_tex, 0)

    if (GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER)
            != GL.GL_FRAMEBUFFER_COMPLETE):
        raise RuntimeError("shadow FBO incomplete")

    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
    return ShadowResources(fbo=fbo, depth_tex=depth_tex, debug_tex=debug_tex)


shadow_res = _build_shadow_resources()


# Scale-bias matrix to convert clip-space [-1, 1] coordinates into
# texture space [0, 1].  Multiplied with the light's projection-view-
# model in shadowMatrix.
_SCALE_BIAS = np.array([
    [0.5, 0.0, 0.0, 0.5],
    [0.0, 0.5, 0.0, 0.5],
    [0.0, 0.0, 0.5, 0.5],
    [0.0, 0.0, 0.0, 1.0],
], dtype=np.float32)


def _light_proj_view(light_dir: tuple[float, float, float]
                     ) -> tuple[np.ndarray, np.ndarray]:
    """Build an orthographic light-space projection-view pair big
    enough to cover the cube + floor footprint from any light angle.
    Returns (proj, view) as 4x4 numpy arrays in pyMatrixStack's
    row-major convention."""
    # Light position: 100 units along light_dir from origin.
    lx, ly, lz = (c * 100.0 for c in light_dir)
    # lookat from light_pos to origin, world up = +Y.
    eye = np.array([lx, ly, lz], dtype=np.float32)
    center = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    up = np.array([0.0, 1.0, 0.0], dtype=np.float32)

    f = center - eye
    f /= np.linalg.norm(f)
    upn = up - f * np.dot(f, up)
    if np.linalg.norm(upn) < 1e-6:
        upn = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    upn /= np.linalg.norm(upn)
    s = np.cross(f, upn)

    view = np.identity(4, dtype=np.float32)
    view[0, :3] = s
    view[1, :3] = upn
    view[2, :3] = -f
    view[0, 3] = -np.dot(s, eye)
    view[1, 3] = -np.dot(upn, eye)
    view[2, 3] = np.dot(f, eye)

    # Orthographic frustum sized to envelop the cube (50 across) +
    # floor (200 across).  Generous near/far so the cube is never
    # near-plane-clipped from the light's POV.
    L, R, B, T, N, F = -120.0, 120.0, -120.0, 120.0, 1.0, 300.0
    proj = np.identity(4, dtype=np.float32)
    proj[0, 0] = 2.0 / (R - L)
    proj[1, 1] = 2.0 / (T - B)
    proj[2, 2] = -2.0 / (F - N)
    proj[0, 3] = -(R + L) / (R - L)
    proj[1, 3] = -(T + B) / (T - B)
    proj[2, 3] = -(F + N) / (F - N)
    return proj, view


def render_shadow_map(stage: int, light_dir: tuple[float, float, float]
                      ) -> np.ndarray:
    """Pass 1: render the cube (and the floor, just in case) into the
    depth FBO from the light's POV.  Returns the shadowMatrix
    (= scaleBias * lightProj * lightView), used by the camera pass to
    transform world-space fragment positions into shadow-map UVs.

    The cube is the only realistic shadow caster in this scene, but
    we render the floor too -- it's effectively free and means the
    debug-view depth visualization shows the floor's depth as
    well, which makes the scene legible."""
    light_proj, light_view = _light_proj_view(light_dir)

    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, shadow_res.fbo)
    GL.glViewport(0, 0, SHADOW_TEX_SIZE, SHADOW_TEX_SIZE)
    # Save the camera-pass clear color so we can restore it at the
    # end of this function -- otherwise the "depth=far is white"
    # clear leaks into the next frame's screen clear.
    saved_clear = (GL.GLfloat * 4)()
    GL.glGetFloatv(GL.GL_COLOR_CLEAR_VALUE, saved_clear)
    GL.glClearColor(1.0, 1.0, 1.0, 1.0)  # depth=far for fragments we don't write
    GL.glClear(GL.GL_DEPTH_BUFFER_BIT | GL.GL_COLOR_BUFFER_BIT)
    # Polygon offset to fight self-shadowing acne on the cube.  The
    # offset is in shadow-map space; tune empirically.
    GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)
    GL.glPolygonOffset(2.0, 4.0)
    GL.glUseProgram(shadow_depth.program)

    def _draw_obj(model_xform_extra=None,
                  vao=cube_solid_vao, count=cube_solid_count):
        # lightMVP = lightProj * lightView * model
        # Compute model from pyMatrixStack's current model matrix.
        model = ms.get_current_matrix(ms.MatrixStack.model)
        mvp = light_proj @ light_view @ np.asarray(model, dtype=np.float32)
        GL.glUniformMatrix4fv(
            shadow_depth.u_lightMVP, 1, GL.GL_TRUE,
            np.ascontiguousarray(mvp, dtype=np.float32))
        GL.glBindVertexArray(vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, count)

    # Cube
    with ms.push_matrix(ms.MatrixStack.model):
        ms.translate(ms.MatrixStack.model, -10.0, 0.0, 10.0)
        _draw_obj()
    # Floor (helps the debug-view show context)
    _draw_obj(vao=floor_vao, count=floor_count)

    GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)
    GL.glClearColor(saved_clear[0], saved_clear[1],
                    saved_clear[2], saved_clear[3])
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    return _SCALE_BIAS @ light_proj @ light_view


def set_uniforms() -> None:
    """Push the current pyMatrixStack matrices into the bound program.

    When ``_using_shadow_map`` is on we also feed the block_shadow
    program's ``shadowMatrix`` uniform with ``shadow_matrix * model``
    so the vertex shader can transform fragment positions into the
    light's clip-space and sample the shadow texture."""
    mvp_loc = block_shadow.u_mvp if _using_shadow_map else main.u_mvp
    model_loc = block_shadow.u_model if _using_shadow_map else main.u_model

    model = ms.get_current_matrix(ms.MatrixStack.model)
    GL.glUniformMatrix4fv(
        mvp_loc,
        1,
        GL.GL_TRUE,
        np.ascontiguousarray(
            ms.get_current_matrix(ms.MatrixStack.modelviewprojection),
            dtype=np.float32,
        ),
    )
    GL.glUniformMatrix4fv(
        model_loc, 1, GL.GL_TRUE,
        np.ascontiguousarray(model, dtype=np.float32),
    )

    if _using_shadow_map:
        # shadowMatrix in the VS is the per-vertex transform from
        # model space to shadow-map UV space.  Pre-multiply by the
        # current model matrix here so the shader gets a single
        # ready-to-use matrix.
        sm = _shadow_pv_scaled @ np.asarray(model, dtype=np.float32)
        GL.glUniformMatrix4fv(
            block_shadow.u_shadow, 1, GL.GL_TRUE,
            np.ascontiguousarray(sm, dtype=np.float32),
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


# Two-step VAO/VBO construction.  The OpenGL model is:
#   1. A VBO holds bytes (vertex data, color data, etc.).
#   2. A VAO records "this attribute slot reads N floats from THIS
#      VBO at THIS offset/stride."  A VAO can mix attributes from
#      multiple VBOs; one VBO can be referenced by multiple VAOs
#      with different layouts.
#
# Splitting them lets one VBO feed multiple pipelines.  In demo22 the
# cube position/normal/uv VBO is referenced by three pipelines (the
# main lit pass, the block-shadow pass, and the shadow-depth pass),
# so the split isn't a deduplication gain here -- it's just clearer
# at the source level.
@dataclasses.dataclass(frozen=True)
class AttribSpec:
    """One vertex attribute pulled from one VBO."""
    vbo: int
    location: int
    size: int                     # floats per vertex (2/3/4)
    layout: tuple[int, int]       # (stride_bytes, offset_bytes)


def make_vbo(data: np.ndarray, usage: int = GL.GL_STATIC_DRAW) -> int:
    """Allocate a VBO and upload ``data``.  Touches no VAO state."""
    data = np.ascontiguousarray(data, dtype=np.float32)
    vbo = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, data.nbytes, data, usage)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    return vbo


def make_vao(attribs: list[AttribSpec]) -> int:
    """Build a VAO that reads each AttribSpec from its VBO."""
    vao = GL.glGenVertexArrays(1)
    GL.glBindVertexArray(vao)
    for a in attribs:
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, a.vbo)
        GL.glEnableVertexAttribArray(a.location)
        stride, offset = a.layout
        GL.glVertexAttribPointer(
            a.location, a.size, GL.GL_FLOAT, False,
            stride, ctypes.c_void_p(offset),
        )
    return vao


def _interleaved_attribs(vbo: int) -> list[AttribSpec]:
    """The standard pos3/normal3/uv2 attribute layout used by every
    mesh in this demo.  Pinned to attribute slots 0/1/2 to match the
    block.vert / shadow_depth / block_shadow shaders."""
    return [
        AttribSpec(vbo=vbo, location=0, size=3, layout=(_STRIDE, 0)),   # pos
        AttribSpec(vbo=vbo, location=1, size=3, layout=(_STRIDE, 12)),  # normal
        AttribSpec(vbo=vbo, location=2, size=2, layout=(_STRIDE, 24)),  # uv
    ]


def _make_interleaved_mesh(vertex_data: np.ndarray) -> tuple[int, int, int]:
    """Convenience: build a VBO + VAO for the standard interleaved
    layout in one step.  Returns (vao, vbo, vertex_count) -- same
    shape as the previous all-in-one ``make_vao``, used by the five
    mesh sites below."""
    vertex_data = np.ascontiguousarray(vertex_data, dtype=np.float32)
    vbo = make_vbo(vertex_data)
    vao = make_vao(_interleaved_attribs(vbo))
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


cube_solid_vao, _, cube_solid_count = _make_interleaved_mesh(_build_cube_solid())
cube_wire_vao,  _, cube_wire_count  = _make_interleaved_mesh(_build_cube_wire_full())


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


floor_vao, floor_vbo, floor_count = _make_interleaved_mesh(_build_floor())


# Light marker geometry ------------------------------------------------------
# A red cone + yellow bulb sized for this demo's units (cube is 50
# units across, floor at y=-25).  Cone radius 5, height 12; bulb
# radius 4.  Sits at light_radius units along +light_dir.

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


marker_cone_vao, marker_cone_vbo, marker_cone_count = _make_interleaved_mesh(
    _build_marker_cone(radius=5.0, height=12.0, slices=20)
)
marker_bulb_vao, marker_bulb_vbo, marker_bulb_count = _make_interleaved_mesh(
    _build_marker_sphere(radius=4.0, slices=16, stacks=10)
)
# light_radius is the distance of the visible cone+bulb marker from
# the origin along light_dir.  The light itself is directional, so
# Lambert/shadow shading is independent of distance -- this slider is
# purely a visual cue (helps students see "the light is over there"
# without changing what the floor and cube actually receive).
light_radius: float = 55.0
LIGHT_MARKER_CONE_COLOR: tuple = (0.85, 0.15, 0.15)
LIGHT_MARKER_BULB_COLOR: tuple = (1.00, 1.00, 0.00)


# ---------------------------------------------------------------------------
# Lighting + planar shadow constants
# ---------------------------------------------------------------------------


# SuperBible used a constant directional light at (-80, 120, 100, 0).
# We compute the same vector each frame from the imgui azimuth/
# elevation sliders so the shadow on the floor reshapes when the
# user slides the light around.
# light_dir_ws is imported from modelviewprojection.shading (see imports above).

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


# Recomputed in the per-frame draw loop from the slider-driven
# light_dir; see `shadow_matrix` in the main loop below.


# ---------------------------------------------------------------------------
# Per-stage rendering
# ---------------------------------------------------------------------------


def setup_uniforms(
    *,
    use_lighting: bool,
    use_texture: bool,
    flat_color: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> None:
    """Bind whichever shader program is active for this stage and
    populate its scalar / vector uniforms.  ``_using_shadow_map`` is
    set by the main loop just before calling draw_*; when it's True we
    use ``block_shadow.program`` (extra ``shadowMap`` + ``shadowMatrix``
    uniforms), otherwise ``main.program``."""
    if _using_shadow_map:
        GL.glUseProgram(block_shadow.program)
        GL.glUniform1i(block_shadow.u_use_lighting, 1 if use_lighting else 0)
        GL.glUniform1i(block_shadow.u_use_texture, 1 if use_texture else 0)
        GL.glUniform3f(block_shadow.u_flat, *flat_color)
        GL.glUniform3f(block_shadow.u_light_dir, *light_dir)
        GL.glUniform3f(block_shadow.u_ambient, 0.2, 0.2, 0.2)
        GL.glUniform3f(block_shadow.u_diffuse, 0.7, 0.7, 0.7)
        GL.glUniform1i(block_shadow.u_tex, 0)
        GL.glUniform1i(block_shadow.u_shadow_map, 1)   # texture unit 1
    else:
        GL.glUseProgram(main.program)
        GL.glUniform1i(main.u_use_lighting, 1 if use_lighting else 0)
        GL.glUniform1i(main.u_use_texture, 1 if use_texture else 0)
        GL.glUniform3f(main.u_flat, *flat_color)
        GL.glUniform3f(main.u_light_dir, *light_dir)
        GL.glUniform3f(main.u_ambient, 0.2, 0.2, 0.2)
        GL.glUniform3f(main.u_diffuse, 0.7, 0.7, 0.7)
        GL.glUniform1i(main.u_tex, 0)


# State written by the main loop just before calling draw_floor /
# draw_cube; set_uniforms / setup_uniforms read these.
_using_shadow_map: bool = False
_shadow_pv_scaled: np.ndarray = np.identity(4, dtype=np.float32)


def draw_floor(stage: int) -> None:
    # When shadow_algo == "shadow_map" and we're in a shadow-casting
    # stage (3 or 4), the floor needs lighting on so the FS runs the
    # shadow lookup.  In the planar-shadow path the floor stays
    # unlit (the shadow is a separate black quad drawn over it).
    receive_shadow = stage in (3, 4) and shadow_algo == "shadow_map"

    with ms.push_matrix(ms.MatrixStack.model):
        if stage == 4:
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, tex_floor)
            setup_uniforms(use_lighting=receive_shadow, use_texture=True)
        elif receive_shadow:
            setup_uniforms(
                use_lighting=True,
                use_texture=False,
                flat_color=(0.0, 0.0, 0.9),
            )
        else:
            setup_uniforms(
                use_lighting=False,
                use_texture=False,
                flat_color=(0.0, 0.0, 0.9),
            )
        set_uniforms()
        GL.glBindVertexArray(floor_vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, floor_count)


def draw_cube(stage: int) -> None:
    """Draw the cube (and, for stages 3/4, its planar shadow)."""

    # All cube drawing happens inside this push so the cube's translation
    # is independent of the floor.
    with ms.push_matrix(ms.MatrixStack.model):
        ms.translate(ms.MatrixStack.model, -10.0, 0.0, 10.0)

        if stage == 0:
            # full wireframe
            setup_uniforms(
                use_lighting=False,
                use_texture=False,
                flat_color=(1.0, 0.0, 0.0),
            )
            set_uniforms()
            GL.glBindVertexArray(cube_wire_vao)
            GL.glDrawArrays(GL.GL_LINES, 0, cube_wire_count)

        elif stage == 1:
            # solid uniform red -- no lighting, no texture
            setup_uniforms(
                use_lighting=False,
                use_texture=False,
                flat_color=(0.8, 0.0, 0.0),
            )
            set_uniforms()
            GL.glBindVertexArray(cube_solid_vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, cube_solid_count)

        elif stage == 2:
            # lit cube
            setup_uniforms(
                use_lighting=True,
                use_texture=False,
                flat_color=(0.8, 0.0, 0.0),
            )
            set_uniforms()
            GL.glBindVertexArray(cube_solid_vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, cube_solid_count)

        elif stage == 3:
            # lit cube + planar shadow
            setup_uniforms(
                use_lighting=True,
                use_texture=False,
                flat_color=(0.8, 0.0, 0.0),
            )
            set_uniforms()
            GL.glBindVertexArray(cube_solid_vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, cube_solid_count)

        elif stage == 4:
            # textured cube on all six faces + shadow.  Opposite faces
            # share a texture, so the cube looks like a wooden block from
            # any angle.  Face vertex offsets in the solid VAO are 6
            # apart in the order:  +Z, -Z, +Y, -Y, +X, -X.
            faces_to_draw = [
                (tex_block_front, 0),   # +Z front
                (tex_block_front, 6),   # -Z back
                (tex_block_top,   12),  # +Y top
                (tex_block_top,   18),  # -Y bottom
                (tex_block_right, 24),  # +X right
                (tex_block_right, 30),  # -X left
            ]
            setup_uniforms(use_lighting=True, use_texture=True)
            set_uniforms()
            GL.glBindVertexArray(cube_solid_vao)
            for tex, off in faces_to_draw:
                GL.glActiveTexture(GL.GL_TEXTURE0)
                GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
                GL.glDrawArrays(GL.GL_TRIANGLES, off, 6)

    # Planar-shadow pass.  Only run when shadow_algo == "planar" --
    # the shadow_map path puts the shadow term inside the camera-pass
    # fragment shader instead, so we must not also stamp a black quad
    # on the floor here.
    if stage in (3, 4) and shadow_algo == "planar":
        # The shadow polygons end up exactly coplanar with the floor
        # (both at y = -25.3), which makes the depth test flip-flop pixel
        # by pixel -- the classic "z-fighting" flicker.  glPolygonOffset
        # nudges the shadow's depth slightly toward the camera so it
        # reliably wins the depth test against the floor.  Disabling
        # depth writes also stops the shadow's own overlapping faces
        # from fighting each other.
        GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)
        GL.glPolygonOffset(-1.0, -1.0)
        GL.glDepthMask(GL.GL_FALSE)

        with ms.push_matrix(ms.MatrixStack.model):
            # shadow operates on world-space points; we need to flatten
            # AFTER the cube is in the world, so pre-multiply: model =
            # SHADOW * translate(-10,0,10).  pyMatrixStack.multiply does
            # current = current * rhs, so doing multiply(SHADOW) then
            # translate(...) yields exactly that.
            ms.multiply(ms.MatrixStack.model, shadow_matrix)
            ms.translate(ms.MatrixStack.model, -10.0, 0.0, 10.0)

            setup_uniforms(
                use_lighting=False,
                use_texture=False,
                flat_color=(0.0, 0.0, 0.0),
            )
            set_uniforms()
            GL.glBindVertexArray(cube_solid_vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, cube_solid_count)

        GL.glDepthMask(GL.GL_TRUE)
        GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)


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
    imgui.text("Shadow algorithm (stages 3, 4):")
    if imgui.radio_button("planar (4x4 flatten matrix)",
                          shadow_algo == "planar"):
        shadow_algo = "planar"
        view_shadow_map = False     # planar has no shadow map to view
    if imgui.radio_button("shadow map (depth texture)",
                          shadow_algo == "shadow_map"):
        shadow_algo = "shadow_map"
    if shadow_algo == "shadow_map":
        _, view_shadow_map = imgui.checkbox(
            "View shadow map (replaces scene)", view_shadow_map)
    imgui.separator()
    imgui.text("Light direction (red cone + yellow bulb):")
    _, light_az_deg = imgui.slider_float(
        "Azimuth (deg)", light_az_deg, 0.0, 360.0)
    _, light_el_deg = imgui.slider_float(
        "Elevation (deg)", light_el_deg, 5.0, 89.0)
    _, light_radius = imgui.slider_float(
        "Radius (marker only)", light_radius, 10.0, 150.0)
    imgui.end()

    # Recompute light + shadow each frame so the slider drives both
    # the Lambert shading on the cube AND the planar shadow on the
    # floor.  light_dir is read by setup_uniforms via closure scope.
    light_dir = light_dir_ws(light_az_deg, light_el_deg)
    shadow_matrix = planar_shadow_matrix(
        FLOOR_PLANE, (light_dir[0], light_dir[1], light_dir[2], 0.0)
    )

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
        near_z=1.0,
        far_z=1000.0,
    )

    # FPS-style camera transform:  inverse of (translate by camera.pos
    # then yaw, then pitch).  Same form as demos 19 and 21.
    ms.rotate_x(ms.MatrixStack.view, -camera.rot_x)
    ms.rotate_y(ms.MatrixStack.view, -camera.rot_y)
    ms.translate(ms.MatrixStack.view, -camera.x, -camera.y, -camera.z)

    # Decide which path we're on this frame.  When stages 3 / 4 use
    # the shadow-map algorithm we need a depth pass first; the camera
    # pass then samples that texture for shadow occlusion.
    using_sm = shadow_algo == "shadow_map" and n_step in (3, 4)

    if using_sm:
        # Pass 1: depth from light's POV.  Returns the shadowMatrix
        # (= scaleBias * lightProj * lightView) for the camera pass.
        # render_shadow_map saves/restores glClearColor itself, so we
        # only need to put the viewport back to the window size.
        _shadow_pv_scaled = render_shadow_map(n_step, light_dir)
        GL.glViewport(0, 0, width, height)

    if using_sm and view_shadow_map:
        # Skip the scene entirely; just visualize the depth texture
        # full-screen.  Same approach as the v7 shadowmapping demo.
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glUseProgram(shadow_view.program)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, shadow_res.debug_tex)
        GL.glUniform1i(shadow_view.u_depth_tex, 0)
        # The fullscreen quad's vertices are baked into the VS; bind
        # the default VAO so no per-mesh attributes leak in.
        GL.glBindVertexArray(_default_vao)
        GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)
        GL.glEnable(GL.GL_DEPTH_TEST)
    else:
        # Normal scene render.  When using_sm, draw_floor / draw_cube
        # see _using_shadow_map=True and switch to block_shadow.program.
        _using_shadow_map = using_sm
        if using_sm:
            GL.glActiveTexture(GL.GL_TEXTURE1)
            GL.glBindTexture(GL.GL_TEXTURE_2D, shadow_res.depth_tex)
            GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glUseProgram(block_shadow.program if using_sm else main.program)
        draw_floor(n_step)
        draw_cube(n_step)
        _using_shadow_map = False

    # ---- Light marker (red cone + yellow bulb) ----
    # Adapted from chapt05/spot.cpp:79-94.  Cone's local +z aligns with
    # +light_dir, base sits at the bulb, apex points back toward the
    # scene.  Drawn unlit so it doesn't shade against itself.
    with ms.push_matrix(ms.MatrixStack.model):
        ms.translate(ms.MatrixStack.model,
                     light_dir[0] * light_radius,
                     light_dir[1] * light_radius,
                     light_dir[2] * light_radius)
        # Rotation chain:  T @ R_y(90 - az) @ R_x(-el).  See demo22a.
        ms.rotate_y(ms.MatrixStack.model,
                    math.radians(90.0 - light_az_deg))
        ms.rotate_x(ms.MatrixStack.model,
                    math.radians(-light_el_deg))

        setup_uniforms(use_lighting=False, use_texture=False,
                       flat_color=LIGHT_MARKER_CONE_COLOR)
        set_uniforms()
        GL.glBindVertexArray(marker_cone_vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, marker_cone_count)

        # Bulb at the base of the cone (= local origin).
        setup_uniforms(use_lighting=False, use_texture=False,
                       flat_color=LIGHT_MARKER_BULB_COLOR)
        set_uniforms()
        GL.glBindVertexArray(marker_bulb_vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, marker_bulb_count)

    GL.glUseProgram(0)

    imgui.render()
    impl.render(imgui.get_draw_data())

    glfw.swap_buffers(window)


glfw.terminate()
