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


import colorsys
import ctypes
import math
import os
import sys
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Tuple, Type

import glfw
import numpy as np
import OpenGL.GL as GL  # pip install PyOpenGL
from imgui_bundle import imgui, imgui_ctx
from numpy import ndarray

import modelviewprojection.pyMatrixStack as ms

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(PWD))
import _pipeline as _p  # noqa: E402


line_thickness = 2.0


@dataclass
class State:
    name: str
    duration: float
    start_time: float = 0.0

    def interpolate(self, time):
        return min(
            1.0,
            (time - self.start_time) / self.duration,
        )


class StepNumber(Enum):
    beginning = State("Beginning", 2.0)
    paddle_1_translate = State("Paddle 1 Translate", 5.0)
    paddle_1_rotate = State("Paddle 1 Rotate", 5.0)
    square_translate_z = State("Square Translate z", 5.0)
    square_rotate_z_first = State("Square Rotate Z First", 5.0)
    square_translate_x = State("Square Translate X", 5.0)
    square_rotate_z_second = State("Square Rotate Z Second", 5.0)
    paddle_2_translate = State("Paddle 2 Translate", 5.0)
    paddle_2_rotate = State("Paddle 2 Rotate", 5.0)
    camera_pre_placement_pause = State("Camera Pre Placement Pause", 5.0)
    camera_translate = State("Camera Translate", 5.0)
    camera_rotate_y = State("Camera Rotate Y", 5.0)
    camera_rotate_x = State("Camera Rotate X", 5.0)
    camera_inverse_translate = State("Camera Inverse Translate", 5.0)
    camera_inverse_rotate_y = State("Camera Inverse Rotate Y", 5.0)
    camera_inverse_rotate_x = State("Camera Inverse Rotate X", 5.0)
    camera_frustum_pause = State("Camera Frustum Pause", 10.0)
    camera_frustum_squash_x = State("Camera Frustum Squash X", 5.0)
    camera_frustum_squash_y = State("Camera Frustum Squash Y", 5.0)
    camera_frustum_translate = State("Camera Frustum Translate", 5.0)
    camera_frustum_scale = State("Camera Frustum Scale", 5.0)
    end = State("End", 5.0)


def calculate_start_times(states_enum: Type[StepNumber]) -> List[State]:
    """Calculate start times for all states."""
    start_time = 0.0
    _updated_states = []
    for state in states_enum:
        current_state = state.value
        current_state.start_time = start_time
        _updated_states.append(current_state)
        start_time += current_state.duration
    return _updated_states


updated_states = calculate_start_times(StepNumber)


# possible things that the viewer may want to center the camera on
class CenterViewOn(Enum):
    ndc = auto()
    paddle1 = auto()
    square = auto()
    paddle2 = auto()
    camera = auto()


# the current object to focus on
center_view_on = CenterViewOn.ndc


window, impl, imguiio = _p.setup_window("Model View Perspective Projection")
_p.install_esc_close(window)


# ---------------------------------------------------------------------------
# Frustum -- state-only dataclass read by the uniform setters.  When the
# user moves the imgui sliders, rebuild_frustum_vao() re-uploads vertex data
# (vertex data is genuinely uploaded to GPU memory; uniforms are merely set).
# ---------------------------------------------------------------------------


@dataclass
class Frustum:
    field_of_view: float
    aspect_ratio: float
    near_z: float
    far_z: float


frustum = Frustum(
    field_of_view=45.0, aspect_ratio=16.0 / 9.0, near_z=-2.0, far_z=-50.0
)


# ---------------------------------------------------------------------------
# Pipeline.
# ---------------------------------------------------------------------------


# Hard-coded "fixed" frustum values used by the paddle/ground/axis/cube
# pipelines (only the perspective Frustum exposes its near/far to the user).
PIPELINE_FOV: float = 45.0
PIPELINE_ASPECT: float = 1.0


# Triangle pipeline (paddles + square): position + per-vertex color, animated
triangle_program: int = _p.compile_program(PWD, "triangle.vert", "triangle.frag")
u_triangle_m: int = GL.glGetUniformLocation(triangle_program, "mMatrix")
u_triangle_v: int = GL.glGetUniformLocation(triangle_program, "vMatrix")
u_triangle_p: int = GL.glGetUniformLocation(triangle_program, "pMatrix")
u_triangle_fov: int = GL.glGetUniformLocation(triangle_program, "field_of_view")
u_triangle_aspect: int = GL.glGetUniformLocation(
    triangle_program, "aspect_ratio"
)
u_triangle_near: int = GL.glGetUniformLocation(triangle_program, "near_z")
u_triangle_far: int = GL.glGetUniformLocation(triangle_program, "far_z")
u_triangle_time: int = GL.glGetUniformLocation(triangle_program, "time")
triangle_attr_position: int = GL.glGetAttribLocation(
    triangle_program, "position"
)
triangle_attr_color: int = GL.glGetAttribLocation(triangle_program, "color_in")

# Ground pipeline: solid dark-gray cylinders.  Reuses ground.vert
# (hardcoded dark gray, no project() -- ground is static) + triangle.frag.
ground_program: int = _p.compile_program(PWD, "ground.vert", "triangle.frag")
u_ground_m: int = GL.glGetUniformLocation(ground_program, "mMatrix")
u_ground_v: int = GL.glGetUniformLocation(ground_program, "vMatrix")
u_ground_p: int = GL.glGetUniformLocation(ground_program, "pMatrix")
ground_attr_position: int = GL.glGetAttribLocation(ground_program, "position")

# Axis pipeline: solid cylinder+cone arrows + frustum near/far, no `time`
# uniform.  Reuses axis.vert (uniform color via VS_OUT) + triangle.frag.
axis_program: int = _p.compile_program(PWD, "axis.vert", "triangle.frag")
u_axis_m: int = GL.glGetUniformLocation(axis_program, "mMatrix")
u_axis_v: int = GL.glGetUniformLocation(axis_program, "vMatrix")
u_axis_p: int = GL.glGetUniformLocation(axis_program, "pMatrix")
u_axis_color: int = GL.glGetUniformLocation(axis_program, "color")
u_axis_fov: int = GL.glGetUniformLocation(axis_program, "field_of_view")
u_axis_aspect: int = GL.glGetUniformLocation(axis_program, "aspect_ratio")
u_axis_near: int = GL.glGetUniformLocation(axis_program, "near_z")
u_axis_far: int = GL.glGetUniformLocation(axis_program, "far_z")
axis_attr_position: int = GL.glGetAttribLocation(axis_program, "position")

# NDC-cube pipeline: solid white cylinders.  Reuses cube.vert (which
# hardcodes white and has NO project() -- the cube is the static NDC
# reference that the world morphs into) + triangle.frag.
cube_program: int = _p.compile_program(PWD, "cube.vert", "triangle.frag")
u_cube_m: int = GL.glGetUniformLocation(cube_program, "mMatrix")
u_cube_v: int = GL.glGetUniformLocation(cube_program, "vMatrix")
u_cube_p: int = GL.glGetUniformLocation(cube_program, "pMatrix")
cube_attr_position: int = GL.glGetAttribLocation(cube_program, "position")

# Frustum pipeline: thick lines via the geometry shader, NOT cylinders.
# The squash animation scales back-edge X/Y by near_z/far_z (~0.04x), which
# would shrink solid-cylinder geometry to sub-pixel width and produce a
# stippled appearance.  frustum.geom expands each line into a screen-space
# quad of constant pixel thickness, so back edges stay visible at any
# squash factor.
frustum_program: int = _p.compile_program(
    PWD, "frustum.vert", "frustum.frag", "frustum.geom"
)
u_frustum_m: int = GL.glGetUniformLocation(frustum_program, "mMatrix")
u_frustum_v: int = GL.glGetUniformLocation(frustum_program, "vMatrix")
u_frustum_p: int = GL.glGetUniformLocation(frustum_program, "pMatrix")
u_frustum_fov: int = GL.glGetUniformLocation(frustum_program, "field_of_view")
u_frustum_aspect: int = GL.glGetUniformLocation(frustum_program, "aspect_ratio")
u_frustum_near: int = GL.glGetUniformLocation(frustum_program, "near_z")
u_frustum_far: int = GL.glGetUniformLocation(frustum_program, "far_z")
u_frustum_time: int = GL.glGetUniformLocation(frustum_program, "time")
u_frustum_thickness: int = GL.glGetUniformLocation(
    frustum_program, "u_thickness"
)
u_frustum_viewport: int = GL.glGetUniformLocation(
    frustum_program, "u_viewport_size"
)
frustum_attr_position: int = GL.glGetAttribLocation(frustum_program, "position")


# ---------------------------------------------------------------------------
# Geometry.
# ---------------------------------------------------------------------------


def _perspective_frustum_edges(f: Frustum) -> list:
    """The 12 edges of the perspective frustum as (p0, p1) pairs.  Front
    corners scale with -near_z by tan(fov/2), back corners with -far_z, both
    multiplied by aspect_ratio in X."""
    front_top = -f.near_z * math.tan(math.radians(f.field_of_view) / 2.0)
    front_right = front_top * f.aspect_ratio
    front_left = -front_right
    front_bottom = -front_top

    back_top = -f.far_z * math.tan(math.radians(f.field_of_view) / 2.0)
    back_right = back_top * f.aspect_ratio
    back_left = -back_right
    back_bottom = -back_top

    near = f.near_z
    far = f.far_z

    return [
        # front face
        ((front_left,  front_top,    near), (front_right, front_top,    near)),
        ((front_right, front_top,    near), (front_right, front_bottom, near)),
        ((front_right, front_bottom, near), (front_left,  front_bottom, near)),
        ((front_left,  front_bottom, near), (front_left,  front_top,    near)),
        # back face
        ((back_left,   back_top,     far),  (back_right,  back_top,     far)),
        ((back_right,  back_top,     far),  (back_right,  back_bottom,  far)),
        ((back_right,  back_bottom,  far),  (back_left,   back_bottom,  far)),
        ((back_left,   back_bottom,  far),  (back_left,   back_top,     far)),
        # connecting edges
        ((front_left,  front_top,    near), (back_left,   back_top,     far)),
        ((front_right, front_top,    near), (back_right,  back_top,     far)),
        ((front_left,  front_bottom, near), (back_left,   back_bottom,  far)),
        ((front_right, front_bottom, near), (back_right,  back_bottom,  far)),
    ]


def _build_perspective_frustum_lines(f: Frustum) -> ndarray:
    """Flat line-pair vertex array for ``GL_LINES``: 12 edges = 24 endpoints
    = 72 floats.  The frustum.geom shader expands each line into a thick
    screen-space quad."""
    verts: list[float] = []
    for p0, p1 in _perspective_frustum_edges(f):
        verts += [float(p0[0]), float(p0[1]), float(p0[2])]
        verts += [float(p1[0]), float(p1[1]), float(p1[2])]
    return np.array(verts, dtype=np.float32)


paddle1_vao, paddle1_vertex_count = _p.make_triangle_vao(
    _p.paddle_vertices, r=0.578123, g=0.0, b=1.0,
    attr_position=triangle_attr_position, attr_color=triangle_attr_color,
)
paddle2_vao, paddle2_vertex_count = _p.make_triangle_vao(
    _p.paddle_vertices, r=1.0, g=1.0, b=0.0,
    attr_position=triangle_attr_position, attr_color=triangle_attr_color,
)
square_vao, square_vertex_count = _p.make_triangle_vao(
    _p.square_vertices, r=0.0, g=0.0, b=1.0,
    attr_position=triangle_attr_position, attr_color=triangle_attr_color,
)
ground_vao, ground_vertex_count = _p.make_lines_vao(
    _p.build_ground_cylinders(), ground_attr_position
)
axis_vao, axis_vertex_count = _p.make_lines_vao(
    _p.build_axis_arrow_solid(), axis_attr_position
)
sphere_vao, sphere_vertex_count = _p.make_lines_vao(
    _p.build_origin_sphere_solid(), axis_attr_position
)
cube_vao, cube_vertex_count = _p.make_lines_vao(
    _p.build_ndc_cube_cylinders(), cube_attr_position
)


# Frustum VAO: needs to be rebuildable when the imgui sliders move, so we
# track the VBO separately and reuse it via glBufferData.  Handles still
# register through _p for cleanup.
def _build_frustum_vao() -> Tuple[int, int, int]:
    vertices = _build_perspective_frustum_lines(frustum)
    vertices = np.ascontiguousarray(vertices, dtype=np.float32).flatten()
    n_verts = vertices.size // _p.floatsPerVertex
    vbo = _p.make_vbo(vertices, usage=GL.GL_DYNAMIC_DRAW)
    vao = _p.make_vao([
        _p.AttribSpec(vbo=vbo, location=frustum_attr_position,
                      size=_p.floatsPerVertex, layout=(0, 0)),
    ])
    return vao, vbo, n_verts


frustum_vao, frustum_vbo, frustum_vertex_count = _build_frustum_vao()


def rebuild_frustum_vao() -> None:
    """Re-upload frustum vertices in place when the imgui sliders change
    the frustum's FOV / aspect / near / far values.  Reuses the existing
    VAO/VBO."""
    global frustum_vertex_count
    vertices = _build_perspective_frustum_lines(frustum)
    vertices = np.ascontiguousarray(vertices, dtype=np.float32).flatten()
    frustum_vertex_count = vertices.size // _p.floatsPerVertex
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, frustum_vbo)
    GL.glBufferData(
        GL.GL_ARRAY_BUFFER,
        _p.glfloat_size * vertices.size,
        vertices,
        GL.GL_STATIC_DRAW,
    )
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)


# ---------------------------------------------------------------------------
# Scene state.
# ---------------------------------------------------------------------------


paddle1_position: ndarray = np.array([-9.0, 1.0, 0.0])
paddle1_rotation: float = math.radians(45.0)

paddle2_position: ndarray = np.array([9.0, 0.5, 0.0])
paddle2_rotation: float = math.radians(-20.0)

square_rotation: float = math.radians(90.0)
rotation_around_paddle1: float = math.radians(30.0)


camera = _p.Camera(
    r=25.0, rot_y=math.radians(45.0), rot_x=math.radians(35.264)
)
_p.install_camera_scroll(window, imguiio, camera)


# ---------------------------------------------------------------------------
# Rendering helpers.
# ---------------------------------------------------------------------------


def draw_triangles(vao: int, vertex_count: int, time: float) -> None:
    GL.glUseProgram(triangle_program)
    GL.glBindVertexArray(vao)
    _p.set_uniforms(u_triangle_m, u_triangle_v, u_triangle_p)
    GL.glUniform1f(u_triangle_fov, PIPELINE_FOV)
    GL.glUniform1f(u_triangle_aspect, PIPELINE_ASPECT)
    GL.glUniform1f(u_triangle_near, frustum.near_z)
    GL.glUniform1f(u_triangle_far, frustum.far_z)
    GL.glUniform1f(u_triangle_time, time)
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, vertex_count)


def draw_ground(time: float) -> None:
    GL.glUseProgram(ground_program)
    GL.glBindVertexArray(ground_vao)
    _p.set_uniforms(u_ground_m, u_ground_v, u_ground_p)
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, ground_vertex_count)

    # Original Ground.render() drew an extra grayed-out axis floating below
    # the ground when this flag was set.  Preserved verbatim.
    if show_ground_axis:
        GL.glDisable(GL.GL_DEPTH_TEST)
        with ms.PushMatrix(ms.MatrixStack.model):
            ms.translate(ms.MatrixStack.model, 0.0, -50.0, 0.0)
            ms.scale(ms.MatrixStack.model, 2.0, 2.0, 2.0)
            draw_axis()
        GL.glEnable(GL.GL_DEPTH_TEST)


def _emit_axis(r: float, g: float, b: float, grayed_out: bool) -> None:
    if grayed_out:
        GL.glUniform3f(u_axis_color, 0.5, 0.5, 0.5)
    else:
        GL.glUniform3f(u_axis_color, r, g, b)
    _p.set_uniforms(u_axis_m, u_axis_v, u_axis_p)
    GL.glUniform1f(u_axis_fov, PIPELINE_FOV)
    GL.glUniform1f(u_axis_aspect, PIPELINE_ASPECT)
    GL.glUniform1f(u_axis_near, frustum.near_z)
    GL.glUniform1f(u_axis_far, frustum.far_z)
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, axis_vertex_count)


def draw_axis(grayed_out: bool = False) -> None:
    GL.glUseProgram(axis_program)
    GL.glBindVertexArray(axis_vao)
    with ms.push_matrix(ms.MatrixStack.model):
        # x axis
        with ms.push_matrix(ms.MatrixStack.model):
            ms.rotate_z(ms.MatrixStack.model, math.radians(-90.0))
            _emit_axis(1.0, 0.0, 0.0, grayed_out)
        # z axis
        with ms.push_matrix(ms.MatrixStack.model):
            ms.rotate_y(ms.MatrixStack.model, math.radians(90.0))
            ms.rotate_z(ms.MatrixStack.model, math.radians(90.0))
            _emit_axis(0.0, 0.0, 1.0, grayed_out)
        # y axis
        _emit_axis(0.0, 1.0, 0.0, grayed_out)

        # White origin sphere -- same frustum-warp uniforms as the axes
        # so it gets clipped/projected through the same pipeline.
        GL.glBindVertexArray(sphere_vao)
        if grayed_out:
            GL.glUniform3f(u_axis_color, 0.5, 0.5, 0.5)
        else:
            GL.glUniform3f(u_axis_color, 1.0, 1.0, 1.0)
        _p.set_uniforms(u_axis_m, u_axis_v, u_axis_p)
        GL.glUniform1f(u_axis_fov, PIPELINE_FOV)
        GL.glUniform1f(u_axis_aspect, PIPELINE_ASPECT)
        GL.glUniform1f(u_axis_near, frustum.near_z)
        GL.glUniform1f(u_axis_far, frustum.far_z)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, sphere_vertex_count)


def draw_cube() -> None:
    GL.glUseProgram(cube_program)
    GL.glBindVertexArray(cube_vao)
    _p.set_uniforms(u_cube_m, u_cube_v, u_cube_p)
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, cube_vertex_count)


def draw_frustum(time: float) -> None:
    GL.glUseProgram(frustum_program)
    GL.glBindVertexArray(frustum_vao)
    _p.set_uniforms(u_frustum_m, u_frustum_v, u_frustum_p)
    GL.glUniform1f(u_frustum_fov, frustum.field_of_view)
    GL.glUniform1f(u_frustum_aspect, frustum.aspect_ratio)
    GL.glUniform1f(u_frustum_near, frustum.near_z)
    GL.glUniform1f(u_frustum_far, frustum.far_z)
    GL.glUniform1f(u_frustum_time, time)
    GL.glUniform1f(u_frustum_thickness, line_thickness)
    GL.glUniform2f(u_frustum_viewport, width, height)
    GL.glDrawArrays(GL.GL_LINES, 0, frustum_vertex_count)


def handle_inputs(
    previous_mouse_position: Optional[Tuple[float, float]],
) -> Optional[Tuple[float, float]]:
    global rotation_around_paddle1
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        rotation_around_paddle1 += 0.1

    global square_rotation
    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square_rotation += 0.1

    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.rot_y -= math.radians(1.0) % 360.0
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.rot_y += math.radians(1.0) % 360.0
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera.rot_x -= math.radians(1.0) % 360.0
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.rot_x += math.radians(1.0) % 360.0

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1_position[1] -= 1.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1_position[1] += 1.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2_position[1] -= 1.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2_position[1] += 1.0

    global paddle1_rotation, paddle2_rotation
    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        paddle1_rotation += 0.1
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        paddle1_rotation -= 0.1
    if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
        paddle2_rotation += 0.1
    if glfw.get_key(window, glfw.KEY_L) == glfw.PRESS:
        paddle2_rotation -= 0.1

    new_mouse_position = glfw.get_cursor_pos(window)
    return_none = False
    if glfw.PRESS == glfw.get_mouse_button(window, glfw.MOUSE_BUTTON_LEFT):
        if not imguiio.want_capture_mouse:
            if previous_mouse_position:
                camera.rot_y -= 0.2 * math.radians(
                    new_mouse_position[0] - previous_mouse_position[0]
                )
                camera.rot_x += 0.2 * math.radians(
                    new_mouse_position[1] - previous_mouse_position[1]
                )
    else:
        return_none = True

    if camera.rot_x > math.pi / 2.0:
        camera.rot_x = math.pi / 2.0
    if camera.rot_x < -math.pi / 2.0:
        camera.rot_x = -math.pi / 2.0

    return None if return_none else new_mouse_position


virtual_camera_position = np.array([-1.5, 0.0, 8.5], dtype=np.float32)
virtual_camera_rot_y = math.radians(25.0)
virtual_camera_rot_x = math.radians(15.0)
virtual_camera_relative_offset = np.array([-0.0, 0.0, 0.0], dtype=np.float32)

TARGET_FRAMERATE = 60  # fps

# to try to standardize on 60 fps, compare times between frames
time_at_beginning_of_previous_frame = glfw.get_time()

animation_time = 0.0
animation_time_multiplier = 1.0
animation_paused = False
show_ground_axis = False


def highlighted_button(text: str, start_time: float, time: float) -> bool:
    highlight = time > start_time and (time - start_time) < 5
    if highlight:
        imgui.push_id(str(3))
        r, g, b = colorsys.hsv_to_rgb(0 / 7.0, 0.6, 0.6)
        imgui.push_style_color(imgui.Col_.button.value, (r, g, b, 1.0))
        r, g, b = colorsys.hsv_to_rgb(0 / 7.0, 0.7, 0.7)
        imgui.push_style_color(imgui.Col_.button_hovered.value, (r, g, b, 1.0))
        r, g, b = colorsys.hsv_to_rgb(0 / 7.0, 0.8, 0.8)
        imgui.push_style_color(imgui.Col_.button_active.value, (r, g, b, 1.0))
    return_value = imgui.button(label=text)
    if highlight:
        imgui.pop_style_color(3)
        imgui.pop_id()
    return return_value


# local variable for event loop
previous_mouse_position = None

# Loop until the user closes the window
while not glfw.window_should_close(window):
    # poll the time to try to get a constant framerate
    while (
        glfw.get_time()
        < time_at_beginning_of_previous_frame + 1.0 / TARGET_FRAMERATE
    ):
        pass
    # set for comparison on the next frame
    time_at_beginning_of_previous_frame = glfw.get_time()

    if not animation_paused:
        animation_time += 1.0 / 60.0 * animation_time_multiplier

    # Poll for and process events
    glfw.poll_events()
    impl.process_inputs()

    imgui.new_frame()

    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("File", True):
            clicked_quit, selected_quit = imgui.menu_item(
                "Quit", "Cmd+Q", False, True
            )

            if clicked_quit:
                exit(0)

            imgui.end_menu()
        imgui.end_main_menu_bar()

    imgui.set_next_window_size(
        imgui.ImVec2(453, 564), imgui.Cond_.first_use_ever
    )
    # imgui.set_next_window_position(imgui.ImVec2(15, 30), imgui.Cond_.first_use_ever)
    imgui.set_next_window_bg_alpha(0.7)

    imgui.begin("Options", True)
    if imgui.collapsing_header("Time"):
        clicked_animation_paused, animation_paused = imgui.checkbox(
            "Pause", animation_paused
        )
        clicked_camera, camera.r = imgui.slider_float(
            "Camera Radius", camera.r, 10, 1000.0
        )
        (
            clicked_animation_time_multiplier,
            animation_time_multiplier,
        ) = imgui.slider_float(
            "Sim Speed", animation_time_multiplier, -10.0, 10.0
        )
        if imgui.button("Restart"):
            animation_time = 0.0

        imgui.set_next_item_open(True, imgui.Cond_.once)
        if imgui.tree_node(
            "From World Space, Against Arrows, Read Bottom Up",
            "From World Space, Against Arrows, Read Bottom Up",
        ):
            imgui.set_next_item_open(True, imgui.Cond_.once)
            if imgui.tree_node("Paddle 1->World", "Paddle 1->World"):
                imgui.text("f_paddle1_to_world(x) = ")
                imgui.text(" = (")
                imgui.same_line()
                if highlighted_button(
                    "T",
                    StepNumber.paddle_1_translate.value.start_time,
                    animation_time,
                ):
                    animation_time = (
                        StepNumber.paddle_1_translate.value.start_time
                    )
                imgui.same_line()
                imgui.text(" o ")
                imgui.same_line()
                if highlighted_button(
                    "R_z",
                    StepNumber.paddle_1_rotate.value.start_time,
                    animation_time,
                ):
                    animation_time = StepNumber.paddle_1_rotate.value.start_time
                imgui.same_line()
                imgui.text(" ) (x) ")

                imgui.set_next_item_open(True, imgui.Cond_.once)
                if imgui.tree_node("Square->World", "Square->World"):
                    imgui.text("f_square_to_world(x) = ")
                    imgui.text(" f_paddle1_to_world o (")
                    imgui.text("      ")
                    imgui.same_line()
                    if highlighted_button(
                        "T_-Z",
                        StepNumber.square_translate_z.value.start_time,
                        animation_time,
                    ):
                        animation_time = (
                            StepNumber.square_translate_z.value.start_time
                        )
                    imgui.same_line()
                    imgui.text(" o ")
                    imgui.same_line()
                    if highlighted_button(
                        "R_Z",
                        StepNumber.square_rotate_z_first.value.start_time,
                        animation_time,
                    ):
                        animation_time = (
                            StepNumber.square_rotate_z_first.value.start_time
                        )
                    imgui.same_line()
                    imgui.text(" o ")
                    imgui.same_line()
                    if highlighted_button(
                        "T_X",
                        StepNumber.square_translate_x.value.start_time,
                        animation_time,
                    ):
                        animation_time = (
                            StepNumber.square_translate_x.value.start_time
                        )
                    imgui.same_line()
                    imgui.text(" o ")
                    imgui.same_line()
                    if highlighted_button(
                        "R2_Z",
                        StepNumber.square_rotate_z_second.value.start_time,
                        animation_time,
                    ):
                        animation_time = (
                            StepNumber.square_rotate_z_second.value.start_time
                        )
                    imgui.same_line()
                    imgui.text(" ) (x) ")
                    imgui.tree_pop()
                imgui.tree_pop()

            imgui.set_next_item_open(True, imgui.Cond_.once)
            if imgui.tree_node("Paddle 2->World", "Paddle 2->World"):
                imgui.text("f_paddle2_to_world(x) = (")
                imgui.same_line()
                if highlighted_button(
                    "T",
                    StepNumber.paddle_2_translate.value.start_time,
                    animation_time,
                ):
                    animation_time = (
                        StepNumber.paddle_2_translate.value.start_time
                    )
                imgui.same_line()
                imgui.text(" o ")
                imgui.same_line()
                if highlighted_button(
                    "R",
                    StepNumber.paddle_2_rotate.value.start_time,
                    animation_time,
                ):
                    animation_time = StepNumber.paddle_2_rotate.value.start_time
                imgui.same_line()
                imgui.text(" ) (x) ")
                imgui.tree_pop()

            imgui.set_next_item_open(True, imgui.Cond_.once)
            if imgui.tree_node("Camera->World", "Camera->World"):
                imgui.text("f_camera_to_world(x) = (")
                imgui.same_line()
                if highlighted_button(
                    "T",
                    StepNumber.camera_translate.value.start_time,
                    animation_time,
                ):
                    animation_time = (
                        StepNumber.camera_translate.value.start_time
                    )
                imgui.same_line()
                imgui.text(" o ")
                imgui.same_line()
                if highlighted_button(
                    "R_Y",
                    StepNumber.camera_rotate_y.value.start_time,
                    animation_time,
                ):
                    animation_time = StepNumber.camera_rotate_y.value.start_time
                imgui.same_line()
                imgui.text(" o ")
                imgui.same_line()
                if highlighted_button(
                    "R_X",
                    StepNumber.camera_rotate_x.value.start_time,
                    animation_time,
                ):
                    animation_time = StepNumber.camera_rotate_x.value.start_time
                imgui.same_line()
                imgui.text(" ) (x) ")
                imgui.tree_pop()
            imgui.tree_pop()

        imgui.set_next_item_open(True, imgui.Cond_.once)
        if imgui.tree_node(
            "Towards NDC, With Arrows, Top Down Reading",
            "Towards NDC, With Arrows, Top Down Reading",
        ):
            imgui.set_next_item_open(True, imgui.Cond_.once)
            if imgui.tree_node("World->Camera", "World->Camera"):
                imgui.text("f_camera_to_world^-1(x) = f_world_to_camera(x) = ")
                imgui.text("   ")
                imgui.same_line()
                if highlighted_button(
                    "R^-1_X",
                    StepNumber.camera_inverse_rotate_x.value.start_time,
                    animation_time,
                ):
                    animation_time = (
                        StepNumber.camera_inverse_rotate_x.value.start_time
                    )
                imgui.same_line()
                imgui.text(" (")
                imgui.same_line()
                if highlighted_button(
                    "R^-1_Y",
                    StepNumber.camera_inverse_rotate_y.value.start_time,
                    animation_time,
                ):
                    animation_time = (
                        StepNumber.camera_inverse_rotate_y.value.start_time
                    )
                imgui.same_line()
                imgui.text(" (")
                imgui.same_line()
                if highlighted_button(
                    "T^-1",
                    StepNumber.camera_inverse_translate.value.start_time,
                    animation_time,
                ):
                    animation_time = (
                        StepNumber.camera_inverse_translate.value.start_time
                    )
                imgui.same_line()
                imgui.text("* x))")
                imgui.tree_pop()
            imgui.set_next_item_open(True, imgui.Cond_.once)
            if imgui.tree_node(
                "Frustum->Rectangular Prism",
                "Frustum->Rectangular Prism",
            ):
                imgui.text("f_frustum_to_prism(x) = ")
                imgui.same_line()
                if highlighted_button(
                    "Squash Y",
                    StepNumber.camera_frustum_squash_y.value.start_time,
                    animation_time,
                ):
                    animation_time = (
                        StepNumber.camera_frustum_squash_y.value.start_time
                    )
                imgui.same_line()
                imgui.text(" (")
                imgui.same_line()
                if highlighted_button(
                    "Squash X",
                    StepNumber.camera_frustum_squash_x.value.start_time,
                    animation_time,
                ):
                    animation_time = (
                        StepNumber.camera_frustum_squash_x.value.start_time
                    )
                imgui.same_line()
                imgui.text(" * x)")
                imgui.tree_pop()
            imgui.set_next_item_open(True, imgui.Cond_.once)
            if imgui.tree_node(
                "Ortho, Rectangular Prism->NDC",
                "Ortho, Rectangular Prism->NDC",
            ):
                imgui.text("f_ortho(x) = ")
                imgui.same_line()
                if highlighted_button(
                    "Scale",
                    StepNumber.camera_frustum_scale.value.start_time,
                    animation_time,
                ):
                    animation_time = (
                        StepNumber.camera_frustum_scale.value.start_time
                    )
                imgui.same_line()
                imgui.text(" (")
                imgui.same_line()
                if highlighted_button(
                    "T - Center",
                    StepNumber.camera_frustum_translate.value.start_time,
                    animation_time,
                ):
                    animation_time = (
                        StepNumber.camera_frustum_translate.value.start_time
                    )
                imgui.same_line()
                imgui.text(" * x)")
                imgui.tree_pop()
            imgui.tree_pop()

    if imgui.collapsing_header("Camera Options"):
        (
            clicked_virtual_camera_positionx_clicked,
            virtual_camera_position[0],
        ) = imgui.slider_float(
            "Camera X_Worldspace", virtual_camera_position[0], -200, 200.0
        )
        (
            clicked_virtual_camera_positiony_clicked,
            virtual_camera_position[1],
        ) = imgui.slider_float(
            "Camera Y_Worldspace", virtual_camera_position[1], -200, 200.0
        )
        (
            clicked_virtual_camera_positionz_clicked,
            virtual_camera_position[2],
        ) = imgui.slider_float(
            "Camera Z_Worldspace", virtual_camera_position[2], -200, 200.0
        )
        (
            clicked_virtual_camera_positionrotx_clicked,
            virtual_camera_rot_x,
        ) = imgui.slider_float(
            "Camera Rot X", virtual_camera_rot_x, -math.pi, math.pi
        )
        (
            clicked_virtual_camera_positionroty_clicked,
            virtual_camera_rot_y,
        ) = imgui.slider_float(
            "Camera Rot Y", virtual_camera_rot_y, -math.pi, math.pi
        )

        with imgui_ctx.push_button_repeat():
            if imgui.button("Translate -Z_Cameraspace"):
                virtual_camera_position[0] -= math.sin(virtual_camera_rot_y)
                virtual_camera_position[2] -= math.cos(virtual_camera_rot_y)
            if imgui.button("Translate Z_Cameraspace"):
                virtual_camera_position[0] += math.sin(virtual_camera_rot_y)
                virtual_camera_position[2] += math.cos(virtual_camera_rot_y)
            if imgui.button("Translate X_Cameraspace"):
                virtual_camera_position[0] += math.cos(virtual_camera_rot_y)
                virtual_camera_position[2] -= math.sin(virtual_camera_rot_y)
            if imgui.button("Translate -X_Cameraspace"):
                virtual_camera_position[0] -= math.cos(virtual_camera_rot_y)
                virtual_camera_position[2] += math.sin(virtual_camera_rot_y)

        (
            clicked_virtual_camera_field_of_view,
            frustum.field_of_view,
        ) = imgui.slider_float("Camera FOV", frustum.field_of_view, 5.0, 120.0)

        if clicked_virtual_camera_field_of_view:
            rebuild_frustum_vao()

        (
            clicked_virtual_camera_aspect_ratio,
            frustum.aspect_ratio,
        ) = imgui.slider_float(
            "Camera AspectRatio", frustum.aspect_ratio, 0.1, 3.0
        )

        if clicked_virtual_camera_aspect_ratio:
            rebuild_frustum_vao()

        (
            clicked_virtual_camera_near_z,
            frustum.near_z,
        ) = imgui.slider_float("Camera near_z", frustum.near_z, -200.0, -1.0)

        if clicked_virtual_camera_near_z:
            rebuild_frustum_vao()

        (
            clicked_virtual_camera_far_z,
            frustum.far_z,
        ) = imgui.slider_float(
            "Camera far_z",
            frustum.far_z,
            frustum.near_z,
            frustum.near_z - 500.0,
        )

        if clicked_virtual_camera_far_z:
            rebuild_frustum_vao()

    if imgui.collapsing_header("Display Options"):
        clicked_show_ground_axises, show_ground_axis = imgui.checkbox(
            "Show Ground Axises", show_ground_axis
        )

        (
            clicked_line_thickness,
            line_thickness,
        ) = imgui.slider_float("Line Width", line_thickness, 1.0, 10.0)

        if imgui.button("NDC"):
            center_view_on = CenterViewOn.ndc
        imgui.same_line()
        if imgui.button("Paddle 1"):
            center_view_on = CenterViewOn.paddle1
        imgui.same_line()
        if imgui.button("Square"):
            center_view_on = CenterViewOn.square
        imgui.same_line()
        if imgui.button("Paddle 2"):
            center_view_on = CenterViewOn.paddle2
        imgui.same_line()
        if imgui.button("Camera"):
            center_view_on = CenterViewOn.camera

    imgui.end()

    width, height = glfw.get_framebuffer_size(window)
    GL.glViewport(0, 0, width, height)
    GL.glClear(sum([GL.GL_COLOR_BUFFER_BIT, GL.GL_DEPTH_BUFFER_BIT]))

    # render scene
    previous_mouse_position = handle_inputs(previous_mouse_position)

    ms.set_to_identity_matrix(ms.MatrixStack.model)
    ms.set_to_identity_matrix(ms.MatrixStack.view)
    ms.set_to_identity_matrix(ms.MatrixStack.projection)

    # set the projection matrix to be perspective
    ms.perspective(
        field_of_view=45.0,
        aspect_ratio=float(width) / float(height),
        near_z=0.1,
        far_z=10000.0,
    )

    # draw around center of world space, like being centered
    # on a player running around a world in a 3D, 3rd person
    # camera
    ms.translate(ms.MatrixStack.view, 0.0, 0.0, -camera.r)
    ms.rotate_x(ms.MatrixStack.view, camera.rot_x)
    ms.rotate_y(ms.MatrixStack.view, -camera.rot_y)

    # but if the user selected view paddle 1 or view square, add
    # center on them
    if (
        center_view_on == CenterViewOn.paddle1
        or center_view_on == center_view_on.square
    ):
        # center on square
        if center_view_on == CenterViewOn.square:
            ms.translate(
                ms.MatrixStack.model,
                -15.0,
                0.0,
                0.0,
            )
            ms.translate(
                ms.MatrixStack.model,
                0.0,
                0.0,
                5.0,
            )

        # center on paddle 1
        ms.translate(
            ms.MatrixStack.model,
            -paddle1_position[0],
            -paddle1_position[1],
            0.0,
        )

    # center on paddle
    if center_view_on == CenterViewOn.paddle2:
        ms.translate(
            ms.MatrixStack.model,
            -paddle2_position[0],
            -paddle2_position[1],
            0.0,
        )
    if center_view_on == CenterViewOn.camera:
        if animation_time > (
            StepNumber.camera_inverse_translate.value.start_time
        ):
            (
                ms.translate(
                    ms.MatrixStack.model,
                    virtual_camera_position[0]
                    * StepNumber.camera_inverse_translate.value.interpolate(
                        animation_time
                    ),
                    virtual_camera_position[1]
                    * StepNumber.camera_inverse_translate.value.interpolate(
                        animation_time
                    ),
                    virtual_camera_position[2]
                    * StepNumber.camera_inverse_translate.value.interpolate(
                        animation_time
                    ),
                )
            )

        if animation_time > (StepNumber.camera_translate.value.start_time):
            if animation_time > (StepNumber.camera_translate.value.start_time):
                (
                    ms.translate(
                        ms.MatrixStack.model,
                        -virtual_camera_position[0]
                        * StepNumber.camera_translate.value.interpolate(
                            animation_time
                        ),
                        -virtual_camera_position[1]
                        * StepNumber.camera_translate.value.interpolate(
                            animation_time
                        ),
                        -virtual_camera_position[2]
                        * StepNumber.camera_translate.value.interpolate(
                            animation_time
                        ),
                    ),
                )

    # draw NDC in global space, so that we can see the camera space
    # go to NDC
    draw_ground(animation_time)
    GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
    with ms.PushMatrix(ms.MatrixStack.model):
        draw_cube()
    GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

    if animation_time > (StepNumber.camera_inverse_rotate_x.value.start_time):
        ms.rotate_x(
            ms.MatrixStack.model,
            -virtual_camera_rot_x
            * StepNumber.camera_inverse_rotate_x.value.interpolate(
                animation_time
            ),
        )
    if animation_time > (StepNumber.camera_inverse_rotate_y.value.start_time):
        ms.rotate_y(
            ms.MatrixStack.model,
            -virtual_camera_rot_y
            * StepNumber.camera_inverse_rotate_y.value.interpolate(
                animation_time
            ),
        )
    if animation_time > (StepNumber.camera_inverse_translate.value.start_time):
        ms.translate(
            ms.MatrixStack.model,
            -virtual_camera_position[0]
            * StepNumber.camera_inverse_translate.value.interpolate(
                animation_time
            ),
            -virtual_camera_position[1]
            * StepNumber.camera_inverse_translate.value.interpolate(
                animation_time
            ),
            -virtual_camera_position[2]
            * StepNumber.camera_inverse_translate.value.interpolate(
                animation_time
            ),
        )

    # draw virtual camera
    if animation_time > (StepNumber.camera_translate.value.start_time):
        with ms.push_matrix(ms.MatrixStack.model):
            if animation_time > (StepNumber.camera_translate.value.start_time):
                ms.translate(
                    ms.MatrixStack.model,
                    virtual_camera_position[0]
                    * StepNumber.camera_translate.value.interpolate(
                        animation_time
                    ),
                    virtual_camera_position[1]
                    * StepNumber.camera_translate.value.interpolate(
                        animation_time
                    ),
                    virtual_camera_position[2]
                    * StepNumber.camera_translate.value.interpolate(
                        animation_time
                    ),
                )
            if animation_time > (StepNumber.camera_rotate_y.value.start_time):
                ms.rotate_y(
                    ms.MatrixStack.model,
                    virtual_camera_rot_y
                    * StepNumber.camera_rotate_y.value.interpolate(
                        animation_time
                    ),
                )
            if animation_time > (StepNumber.camera_rotate_x.value.start_time):
                ms.rotate_x(
                    ms.MatrixStack.model,
                    virtual_camera_rot_x
                    * StepNumber.camera_rotate_x.value.interpolate(
                        animation_time
                    ),
                )

            draw_ground(animation_time)
            GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

            if animation_time > (StepNumber.camera_rotate_y.value.start_time):
                draw_frustum(animation_time)
            draw_axis()
            draw_cube()

    if animation_time < StepNumber.paddle_1_translate.value.start_time:
        draw_axis()
    else:
        draw_axis(grayed_out=True)

    with ms.PushMatrix(ms.MatrixStack.model):
        if animation_time > (StepNumber.paddle_1_translate.value.start_time):
            ms.translate(
                ms.MatrixStack.model,
                paddle1_position[0]
                * StepNumber.paddle_1_translate.value.interpolate(
                    animation_time
                ),
                paddle1_position[1]
                * StepNumber.paddle_1_translate.value.interpolate(
                    animation_time
                ),
                0.0,
            )
        if animation_time > (StepNumber.paddle_1_rotate.value.start_time):
            ms.rotate_z(
                ms.MatrixStack.model,
                paddle1_rotation
                * StepNumber.paddle_1_rotate.value.interpolate(animation_time),
            )

        if animation_time > (StepNumber.beginning.value.start_time) and (
            animation_time < StepNumber.square_translate_z.value.start_time
        ):
            draw_axis()
        if animation_time > (StepNumber.square_translate_z.value.start_time):
            # ascontiguousarray puts the array in column major order
            draw_triangles(
                paddle1_vao, paddle1_vertex_count, animation_time
            )

        # # draw the square

        if animation_time > (StepNumber.square_translate_z.value.start_time):
            ms.translate(
                ms.MatrixStack.model,
                0.0,
                0.0,
                -5.0
                * StepNumber.square_translate_z.value.interpolate(
                    animation_time
                ),
            )
        if animation_time > (StepNumber.square_rotate_z_first.value.start_time):
            ms.rotate_z(
                ms.MatrixStack.model,
                rotation_around_paddle1
                * StepNumber.square_rotate_z_first.value.interpolate(
                    animation_time
                ),
            )
        if animation_time > (StepNumber.square_translate_x.value.start_time):
            ms.translate(
                ms.MatrixStack.model,
                1.5
                * StepNumber.square_translate_x.value.interpolate(
                    animation_time
                ),
                0.0,
                0.0,
            )
        if animation_time > (
            StepNumber.square_rotate_z_second.value.start_time
        ):
            ms.rotate_z(
                ms.MatrixStack.model,
                square_rotation
                * StepNumber.square_rotate_z_second.value.interpolate(
                    animation_time
                ),
            )

        if animation_time > (StepNumber.paddle_1_rotate.value.start_time) and (
            animation_time < StepNumber.paddle_2_translate.value.start_time
        ):
            draw_axis()

        if animation_time > (StepNumber.paddle_2_translate.value.start_time):
            draw_triangles(square_vao, square_vertex_count, animation_time)

    # get back to center of global space

    with ms.PushMatrix(ms.MatrixStack.model):
        # draw paddle 2
        if animation_time > (StepNumber.paddle_2_translate.value.start_time):
            ms.translate(
                ms.MatrixStack.model,
                paddle2_position[0]
                * StepNumber.paddle_2_translate.value.interpolate(
                    animation_time
                ),
                paddle2_position[1]
                * StepNumber.paddle_2_translate.value.interpolate(
                    animation_time
                ),
                0.0,
            )
        if animation_time > (StepNumber.paddle_2_rotate.value.start_time):
            ms.rotate_z(
                ms.MatrixStack.model,
                paddle2_rotation
                * StepNumber.paddle_2_rotate.value.interpolate(animation_time),
            )

        if animation_time > (
            StepNumber.paddle_2_translate.value.start_time
        ) and (
            animation_time
            < (StepNumber.camera_pre_placement_pause.value.start_time)
        ):
            draw_axis()

        if animation_time > (
            StepNumber.camera_pre_placement_pause.value.start_time
        ):
            draw_triangles(
                paddle2_vao, paddle2_vertex_count, animation_time
            )

    imgui.render()
    impl.render(imgui.get_draw_data())

    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)


_p.cleanup()
glfw.terminate()
