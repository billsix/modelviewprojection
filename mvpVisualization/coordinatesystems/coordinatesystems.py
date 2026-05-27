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


import math
import os
import sys
from typing import Optional, Tuple

import glfw
import numpy as np
import OpenGL.GL as GL  # pip install PyOpenGL
from imgui_bundle import imgui
from numpy import ndarray

import modelviewprojection.pyMatrixStack as ms

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(PWD))
import _pipeline as _p  # noqa: E402


line_thickness = 2.0

window, impl, imguiio = _p.setup_window("Coordinate Systems")
_p.install_esc_close(window)


# ---------------------------------------------------------------------------
# Pipeline -- compile each shader program once, cache uniform / attribute
# locations.
# ---------------------------------------------------------------------------


# All four pipelines share the top-level shaders; this is a static demo, so
# they take the default project_identity.glsl (no projection animation).

# Triangle pipeline (paddles + square): per-vertex colour.
triangle_pipeline = _p.build_pipeline(
    "per_vertex_color.vert", "passthrough.frag", per_vertex_color=True
)

# Ground pipeline: dark-gray cylinders, solid uniform colour (set in draw_ground).
ground_pipeline = _p.build_pipeline(
    "uniform_color.vert", "passthrough.frag", color=True
)

# Axis pipeline: cylinder+cone arrows, per-axis uniform colour.
axis_pipeline = _p.build_pipeline(
    "uniform_color.vert", "passthrough.frag", color=True
)

# NDC-cube pipeline: white cylinders.  Same shared shader as the axis pipeline.
cube_pipeline = _p.build_pipeline(
    "uniform_color.vert", "passthrough.frag", color=True
)


# ---------------------------------------------------------------------------
# Geometry -- build VAOs once at module scope (handles registered through
# _pipeline for cleanup).
# ---------------------------------------------------------------------------

paddle1_vao, paddle1_vertex_count = _p.make_triangle_vao(
    _p.paddle_vertices, r=0.578123, g=0.0, b=1.0,
    attr_position=triangle_pipeline.attr_position, attr_color=triangle_pipeline.attr_color,
)
paddle2_vao, paddle2_vertex_count = _p.make_triangle_vao(
    _p.paddle_vertices, r=1.0, g=1.0, b=0.0,
    attr_position=triangle_pipeline.attr_position, attr_color=triangle_pipeline.attr_color,
)
square_vao, square_vertex_count = _p.make_triangle_vao(
    _p.square_vertices, r=0.0, g=0.0, b=1.0,
    attr_position=triangle_pipeline.attr_position, attr_color=triangle_pipeline.attr_color,
)
ground_vao, ground_vertex_count = _p.make_lines_vao(
    _p.build_ground_cylinders(), ground_pipeline.attr_position
)
axis_vao, axis_vertex_count = _p.make_lines_vao(
    _p.build_axis_arrow_solid(), axis_pipeline.attr_position
)
sphere_vao, sphere_vertex_count = _p.make_lines_vao(
    _p.build_origin_sphere_solid(), axis_pipeline.attr_position
)
cube_vao, cube_vertex_count = _p.make_lines_vao(
    _p.build_ndc_cube_cylinders(), cube_pipeline.attr_position
)


# ---------------------------------------------------------------------------
# Scene state -- plain module-level data.
# ---------------------------------------------------------------------------


paddle1_position: ndarray = np.array([-9.0, 1.0, 0.0])
paddle1_rotation: float = math.radians(0.0)

paddle2_position: ndarray = np.array([9.0, 0.5, 0.0])
paddle2_rotation: float = math.radians(0.0)

square_rotation: float = math.radians(0.0)
rotation_around_paddle1: float = math.radians(0.0)


camera = _p.Camera(
    r=35.0, rot_y=math.radians(45.0), rot_x=math.radians(-35.264)
)
_p.install_camera_scroll(window, imguiio, camera)


# ---------------------------------------------------------------------------
# Rendering helpers -- one draw_* per pipeline.  Each one assumes the model /
# view / projection stacks are already set up by the main loop.
# ---------------------------------------------------------------------------


def draw_triangles(vao: int, vertex_count: int) -> None:
    """Render a triangle-pipeline VAO (paddles, square)."""
    GL.glUseProgram(triangle_pipeline.program)
    GL.glBindVertexArray(vao)
    _p.set_uniforms(triangle_pipeline.u_m, triangle_pipeline.u_v, triangle_pipeline.u_p)
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, vertex_count)


def draw_ground() -> None:
    GL.glUseProgram(ground_pipeline.program)
    GL.glBindVertexArray(ground_vao)
    GL.glUniform3f(ground_pipeline.u_color, 0.1, 0.1, 0.1)
    _p.set_uniforms(ground_pipeline.u_m, ground_pipeline.u_v, ground_pipeline.u_p)
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, ground_vertex_count)


def _emit_axis(r: float, g: float, b: float, grayed_out: bool) -> None:
    """Emit one cylinder+cone axis arrow using whatever model transform is
    currently on ms's stack.  Caller has already glUseProgram'd and bound
    axis_vao."""
    if grayed_out:
        GL.glUniform3f(axis_pipeline.u_color, 0.5, 0.5, 0.5)
    else:
        GL.glUniform3f(axis_pipeline.u_color, r, g, b)
    _p.set_uniforms(axis_pipeline.u_m, axis_pipeline.u_v, axis_pipeline.u_p)
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, axis_vertex_count)


def draw_axis(grayed_out: bool = False) -> None:
    """Draw the 3-axis indicator (X red, Y green, Z blue) at the current
    model transform."""
    GL.glUseProgram(axis_pipeline.program)
    GL.glBindVertexArray(axis_vao)
    with ms.push_matrix(ms.MatrixStack.model):
        # x axis -- rotate the Y-pointing arrow geometry to point along +X
        with ms.push_matrix(ms.MatrixStack.model):
            ms.rotate_z(ms.MatrixStack.model, math.radians(-90.0))
            _emit_axis(1.0, 0.0, 0.0, grayed_out)
        # z axis
        with ms.push_matrix(ms.MatrixStack.model):
            ms.rotate_y(ms.MatrixStack.model, math.radians(90.0))
            ms.rotate_z(ms.MatrixStack.model, math.radians(90.0))
            _emit_axis(0.0, 0.0, 1.0, grayed_out)
        # y axis -- the arrow already points +Y, no rotation needed
        _emit_axis(0.0, 1.0, 0.0, grayed_out)

        # White sphere at the origin -- the dot gltDrawUnitAxes
        # finishes with, ported into the procedural pipeline.
        GL.glBindVertexArray(sphere_vao)
        if grayed_out:
            GL.glUniform3f(axis_pipeline.u_color, 0.5, 0.5, 0.5)
        else:
            GL.glUniform3f(axis_pipeline.u_color, 1.0, 1.0, 1.0)
        _p.set_uniforms(axis_pipeline.u_m, axis_pipeline.u_v, axis_pipeline.u_p)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, sphere_vertex_count)


def draw_cube() -> None:
    GL.glUseProgram(cube_pipeline.program)
    GL.glBindVertexArray(cube_vao)
    _p.set_uniforms(cube_pipeline.u_m, cube_pipeline.u_v, cube_pipeline.u_p)
    GL.glUniform3f(cube_pipeline.u_color, 1.0, 1.0, 1.0)
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, cube_vertex_count)


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
        camera.rot_y += math.radians(1.0) % 360.0
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.rot_y -= math.radians(1.0) % 360.0
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
                camera.rot_x -= 0.2 * math.radians(
                    new_mouse_position[1] - previous_mouse_position[1]
                )
    else:
        return_none = True

    if camera.rot_x > math.pi / 2.0:
        camera.rot_x = math.pi / 2.0
    if camera.rot_x < -math.pi / 2.0:
        camera.rot_x = -math.pi / 2.0

    return None if return_none else new_mouse_position


virtual_camera_position = np.array([-15.0, 0.0, 85.0], dtype=np.float32)
virtual_camera_rot_y = math.radians(25.0)
virtual_camera_rot_x = math.radians(15.0)


TARGET_FRAMERATE = 60  # fps

# to try to standardize on 60 fps, compare times between frames
time_at_beginning_of_previous_frame = glfw.get_time()

animation_time = 0.0
animation_time_multiplier = 1.0
animation_paused = False

center_view_on_ndc = True
center_view_on_paddle1 = False
center_view_on_square = False
center_view_on_paddle2 = False


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

    imgui.begin("Camera Control", True)

    if center_view_on_ndc:
        clicked_camera, camera.r = imgui.slider_float(
            "Camera Radius", camera.r, 10, 1000.0
        )

    (
        clicked_line_thickness,
        line_thickness,
    ) = imgui.slider_float("Line Width", line_thickness, 1.0, 10.0)

    if imgui.button("NDC"):
        center_view_on_ndc = True
        center_view_on_paddle1 = False
        center_view_on_square = False
        center_view_on_paddle2 = False
    if imgui.button("Paddle 1"):
        center_view_on_ndc = False
        center_view_on_paddle1 = True
        center_view_on_square = False
        center_view_on_paddle2 = False
    if imgui.button("Square"):
        center_view_on_ndc = False
        center_view_on_paddle1 = False
        center_view_on_square = True
        center_view_on_paddle2 = False
    if imgui.button("Paddle 2"):
        center_view_on_ndc = False
        center_view_on_paddle1 = False
        center_view_on_square = False
        center_view_on_paddle2 = True

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

    # camera management
    # make 3rd person camera centered on something

    # draw around center of world space, like being centered
    # on a player running around a world in a 3D, 3rd person
    # camera
    ms.translate(ms.MatrixStack.view, 0.0, 0.0, -camera.r)
    ms.rotate_x(ms.MatrixStack.view, -camera.rot_x)
    ms.rotate_y(ms.MatrixStack.view, -camera.rot_y)

    # but if the user selected view paddle 1 or view square, add
    # center on them
    if center_view_on_paddle1 or center_view_on_square:
        # center on square
        if center_view_on_square:
            ms.rotate_z(
                ms.MatrixStack.model,
                -square_rotation,
            )
            ms.translate(
                ms.MatrixStack.model,
                -1.5,
                0.0,
                0.0,
            )
            ms.rotate_z(
                ms.MatrixStack.model,
                -rotation_around_paddle1,
            )
            ms.translate(
                ms.MatrixStack.model,
                0.0,
                0.0,
                0.5,
            )

        # center on paddle 1
        ms.rotate_z(
            ms.MatrixStack.model,
            -paddle1_rotation,
        )
        ms.translate(
            ms.MatrixStack.model,
            -paddle1_position[0],
            -paddle1_position[1],
            0.0,
        )

    # center on paddle
    if center_view_on_paddle2:
        ms.rotate_z(
            ms.MatrixStack.model,
            -paddle2_rotation,
        )
        ms.translate(
            ms.MatrixStack.model,
            -paddle2_position[0],
            -paddle2_position[1],
            0.0,
        )

    # draw NDC in global space, so that we can see the camera space
    # go to NDC
    with ms.push_matrix(ms.MatrixStack.model):
        draw_cube()
    draw_ground()

    draw_axis()

    with ms.push_matrix(ms.MatrixStack.model):
        ms.translate(
            ms.MatrixStack.model,
            paddle1_position[0],
            paddle1_position[1],
            0.0,
        )
        ms.rotate_z(
            ms.MatrixStack.model,
            paddle1_rotation,
        )

        # ascontiguousarray puts the array in column major order
        draw_triangles(paddle1_vao, paddle1_vertex_count)
        GL.glDisable(GL.GL_DEPTH_TEST)
        draw_axis()
        GL.glEnable(GL.GL_DEPTH_TEST)

        # # draw the square

        ms.translate(
            ms.MatrixStack.model,
            0.0,
            0.0,
            -0.5,
        )
        ms.rotate_z(
            ms.MatrixStack.model,
            rotation_around_paddle1,
        )
        ms.translate(
            ms.MatrixStack.model,
            1.5,
            0.0,
            0.0,
        )
        ms.rotate_z(
            ms.MatrixStack.model,
            square_rotation,
        )

        draw_triangles(square_vao, square_vertex_count)
        GL.glDisable(GL.GL_DEPTH_TEST)
        draw_axis()
        GL.glEnable(GL.GL_DEPTH_TEST)

    # get back to center of global space

    with ms.push_matrix(ms.MatrixStack.model):
        # draw paddle 2
        ms.translate(
            ms.MatrixStack.model,
            paddle2_position[0],
            paddle2_position[1],
            0.0,
        )
        ms.rotate_z(
            ms.MatrixStack.model,
            paddle2_rotation,
        )

        draw_triangles(paddle2_vao, paddle2_vertex_count)
        GL.glDisable(GL.GL_DEPTH_TEST)
        draw_axis()
        GL.glEnable(GL.GL_DEPTH_TEST)

    imgui.render()
    impl.render(imgui.get_draw_data())

    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)


_p.cleanup()
glfw.terminate()
