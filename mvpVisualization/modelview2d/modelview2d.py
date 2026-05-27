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
import math
import os
import sys

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

window, impl, imguiio = _p.setup_window("Model View 2D")
_p.install_esc_close(window)


def draw_in_square_viewport() -> None:
    GL.glClearColor(0.2, 0.2, 0.2, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    w, h = glfw.get_framebuffer_size(window)
    minimum_dimension = w if w < h else h

    GL.glEnable(GL.GL_SCISSOR_TEST)
    GL.glScissor(
        int((w - minimum_dimension) / 2.0),
        int((h - minimum_dimension) / 2.0),
        minimum_dimension,
        minimum_dimension,
    )

    GL.glClearColor(13.0 / 255.0, 64.0 / 255.0, 5.0 / 255.0, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glDisable(GL.GL_SCISSOR_TEST)

    GL.glViewport(
        int(0.0 + (w - minimum_dimension) / 2.0),
        int(0.0 + (h - minimum_dimension) / 2.0),
        minimum_dimension,
        minimum_dimension,
    )


# ---------------------------------------------------------------------------
# Pipeline -- compile each shader program once, cache uniform / attribute
# locations.  The vert shaders here animate the projection derivation via a
# `time` uniform plus frustum constants (field_of_view, aspect_ratio, near_z,
# far_z), so each pipeline carries more uniform handles than the un-animated
# visualizations.
# ---------------------------------------------------------------------------


# Frustum constants used by the animated `project()` in every vert shader.
PROJ_FOV: float = 45.0
PROJ_ASPECT: float = 1.0
PROJ_NEAR_Z: float = -5.0
PROJ_FAR_Z: float = -150.0


# Triangle pipeline (paddles + square): position + per-vertex color, animated
triangle_pipeline = _p.build_pipeline(
    PWD, "triangle.vert", "triangle.frag", per_vertex_color=True, anim=True
)

# Ground pipeline: solid dark-gray cylinders.  Reuses ground.vert
# (hardcoded dark gray, no project() -- ground is static even in this
# animated demo) + triangle.frag.
ground_pipeline = _p.build_pipeline(PWD, "ground.vert", "triangle.frag")

# Axis pipeline: solid cylinder+cone arrows, animated.  Reuses axis.vert
# (uniform color + animated project()) + triangle.frag (no geom shader).
axis_pipeline = _p.build_pipeline(
    PWD, "axis.vert", "triangle.frag", color=True, anim=True
)

# NDC-cube pipeline (a 2D NDC outline in this demo, z=0): solid white
# cylinders, no cones, animated.  Reuses axis.vert + triangle.frag.
cube_pipeline = _p.build_pipeline(
    PWD, "axis.vert", "triangle.frag", color=True, anim=True
)


# ---------------------------------------------------------------------------
# Geometry.
# ---------------------------------------------------------------------------


def _build_2d_ndc_outline_cylinders(half_extent: float = 1.0) -> ndarray:
    """The 2D NDC outline as 4 cylinder edges forming a square at z=0
    with corners at ±half_extent.  modelview2d-specific; the 3D demos use
    _p.build_ndc_cube_cylinders().  Pass half_extent=10 for the
    virtual-camera "view volume" rendering (which used to do a scale(10)
    on a unit outline -- scaling propagated to the cylinder radius)."""
    h = half_extent
    edges = [
        ((-h, -h, 0.0), ( h, -h, 0.0)),
        (( h, -h, 0.0), ( h,  h, 0.0)),
        (( h,  h, 0.0), (-h,  h, 0.0)),
        ((-h,  h, 0.0), (-h, -h, 0.0)),
    ]
    return _p.build_cylinders_for_edges(edges)


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
    _build_2d_ndc_outline_cylinders(half_extent=1.0), cube_pipeline.attr_position
)
# A second outline at ±10 for the virtual-camera "view volume" rendering.
# Edges baked at this scale so the cylinder thickness matches the regular
# NDC outline instead of being scaled up 10x with the model matrix.
cube_big_vao, cube_big_vertex_count = _p.make_lines_vao(
    _build_2d_ndc_outline_cylinders(half_extent=10.0), cube_pipeline.attr_position
)


# ---------------------------------------------------------------------------
# Scene state.  No camera scroll here -- this demo is 2D, no zoom.
# ---------------------------------------------------------------------------


paddle1_position: ndarray = np.array([-9.0, 1.0, 0.0])
paddle1_rotation: float = math.radians(45.0)

paddle2_position: ndarray = np.array([9.0, 0.5, 0.0])
paddle2_rotation: float = math.radians(-20.0)

square_rotation: float = math.radians(90.0)
rotation_around_paddle1: float = math.radians(30.0)


camera = _p.Camera(r=25.0, rot_y=math.radians(0.0), rot_x=math.radians(0.0))


# ---------------------------------------------------------------------------
# Rendering helpers.  Each draw_* takes an explicit `time` because some
# callsites want the projection animation frozen at a specific moment (e.g.
# the NDC outline drawn at time=0).
# ---------------------------------------------------------------------------


def _set_frustum_uniforms(
    u_fov: int, u_aspect: int, u_near: int, u_far: int
) -> None:
    GL.glUniform1f(u_fov, PROJ_FOV)
    GL.glUniform1f(u_aspect, PROJ_ASPECT)
    GL.glUniform1f(u_near, PROJ_NEAR_Z)
    GL.glUniform1f(u_far, PROJ_FAR_Z)


def draw_triangles(vao: int, vertex_count: int, time: float) -> None:
    GL.glUseProgram(triangle_pipeline.program)
    GL.glBindVertexArray(vao)
    _p.set_uniforms(triangle_pipeline.u_m, triangle_pipeline.u_v, triangle_pipeline.u_p)
    _set_frustum_uniforms(
        triangle_pipeline.u_fov, triangle_pipeline.u_aspect, triangle_pipeline.u_near, triangle_pipeline.u_far
    )
    GL.glUniform1f(triangle_pipeline.u_time, time)
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, vertex_count)


def draw_ground(time: float) -> None:
    GL.glUseProgram(ground_pipeline.program)
    GL.glBindVertexArray(ground_vao)
    _p.set_uniforms(ground_pipeline.u_m, ground_pipeline.u_v, ground_pipeline.u_p)
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, ground_vertex_count)


def _emit_axis(
    r: float, g: float, b: float, time: float, grayed_out: bool
) -> None:
    if grayed_out:
        GL.glUniform3f(axis_pipeline.u_color, 0.5, 0.5, 0.5)
    else:
        GL.glUniform3f(axis_pipeline.u_color, r, g, b)
    _p.set_uniforms(axis_pipeline.u_m, axis_pipeline.u_v, axis_pipeline.u_p)
    _set_frustum_uniforms(axis_pipeline.u_fov, axis_pipeline.u_aspect, axis_pipeline.u_near, axis_pipeline.u_far)
    GL.glUniform1f(axis_pipeline.u_time, time)
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, axis_vertex_count)


def draw_axis(time: float, grayed_out: bool = False) -> None:
    """Draw X (red, +90Z rotation) and Y (green, default).  The 2D demo
    deliberately omits the Z axis."""
    GL.glUseProgram(axis_pipeline.program)
    GL.glBindVertexArray(axis_vao)
    with ms.push_matrix(ms.MatrixStack.model):
        # x axis -- rotate the Y-pointing arrow to point along +X
        with ms.push_matrix(ms.MatrixStack.model):
            ms.rotate_z(ms.MatrixStack.model, math.radians(-90.0))
            _emit_axis(1.0, 0.0, 0.0, time, grayed_out)
        # y axis -- already points +Y, no rotation needed
        _emit_axis(0.0, 1.0, 0.0, time, grayed_out)

        # White origin sphere -- shares the axis program's frustum+time
        # uniforms so the 2D projection animation applies to it too.
        GL.glBindVertexArray(sphere_vao)
        if grayed_out:
            GL.glUniform3f(axis_pipeline.u_color, 0.5, 0.5, 0.5)
        else:
            GL.glUniform3f(axis_pipeline.u_color, 1.0, 1.0, 1.0)
        _p.set_uniforms(axis_pipeline.u_m, axis_pipeline.u_v, axis_pipeline.u_p)
        _set_frustum_uniforms(axis_pipeline.u_fov, axis_pipeline.u_aspect, axis_pipeline.u_near, axis_pipeline.u_far)
        GL.glUniform1f(axis_pipeline.u_time, time)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, sphere_vertex_count)


def draw_cube(time: float) -> None:
    GL.glUseProgram(cube_pipeline.program)
    GL.glBindVertexArray(cube_vao)
    _p.set_uniforms(cube_pipeline.u_m, cube_pipeline.u_v, cube_pipeline.u_p)
    _set_frustum_uniforms(cube_pipeline.u_fov, cube_pipeline.u_aspect, cube_pipeline.u_near, cube_pipeline.u_far)
    GL.glUniform1f(cube_pipeline.u_time, time)
    GL.glUniform3f(cube_pipeline.u_color, 1.0, 1.0, 1.0)
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, cube_vertex_count)


def handle_inputs() -> None:
    global rotation_around_paddle1
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        rotation_around_paddle1 += 0.1

    global square_rotation
    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square_rotation += 0.1

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


virtual_camera_position = np.array([-1.5, 2.0, 0.0], dtype=np.float32)
virtual_camera_relative_offset = np.array([-0.0, 0.0, 0.0], dtype=np.float32)

TARGET_FRAMERATE = 60  # fps

# to try to standardize on 60 fps, compare times between frames
time_at_beginning_of_previous_frame = glfw.get_time()

animation_time = 0.0
animation_time_multiplier = 1.0
animation_paused = False
NDC = False


def highlighted_button(text: str, start_time: int, time: float) -> bool:
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

    imgui.set_next_window_bg_alpha(0.05)
    imgui.begin("Time", True)

    clicked_animation_paused, animation_paused = imgui.checkbox(
        "Pause", animation_paused
    )

    (
        clicked_line_thickness,
        line_thickness,
    ) = imgui.slider_float("Line Width", line_thickness, 1.0, 10.0)

    clicked_camera, camera.r = imgui.slider_float(
        "Camera Radius", camera.r, 10, 1000.0
    )
    (
        clicked_animation_time_multiplier,
        animation_time_multiplier,
    ) = imgui.slider_float("Sim Speed", animation_time_multiplier, 0.1, 10.0)
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
            if highlighted_button("T", 5, animation_time):
                animation_time = 5.0
            imgui.same_line()
            imgui.text(" o ")
            imgui.same_line()
            if highlighted_button("R", 10, animation_time):
                animation_time = 10.0
            imgui.same_line()
            imgui.text(" ) (x) ")

            imgui.set_next_item_open(True, imgui.Cond_.once)
            if imgui.tree_node("Square->World", "Square->World"):
                imgui.text("f_square_to_world(x) = ")
                imgui.text(" f_square_to_world o (")
                imgui.text("      ")
                imgui.same_line()
                if highlighted_button("R1", 20, animation_time):
                    animation_time = 20.0
                imgui.same_line()
                imgui.text(" o ")
                imgui.same_line()
                if highlighted_button("T_X", 25, animation_time):
                    animation_time = 25.0
                imgui.same_line()
                imgui.text(" o ")
                imgui.same_line()
                if highlighted_button("R2", 30, animation_time):
                    animation_time = 30.0
                imgui.same_line()
                imgui.text(" ) (x) ")
                imgui.tree_pop()
            imgui.tree_pop()

        imgui.set_next_item_open(True, imgui.Cond_.once)
        if imgui.tree_node("Paddle 2->World", "Paddle 2->World"):
            imgui.text("f_paddle2_to_world(x) = (")
            imgui.same_line()
            if highlighted_button("T", 40, animation_time):
                animation_time = 40.0
            imgui.same_line()
            imgui.text(" o ")
            imgui.same_line()
            if highlighted_button("R", 45, animation_time):
                animation_time = 45.0
            imgui.same_line()
            imgui.text(" ) (x) ")
            imgui.tree_pop()

        imgui.set_next_item_open(True, imgui.Cond_.once)
        if imgui.tree_node("Camera->World", "Camera->World"):
            imgui.text("f_camera_to_world(x) = ")
            imgui.same_line()
            if highlighted_button("T", 55, animation_time):
                animation_time = 55.0
            imgui.same_line()
            imgui.text("(x) ")
            imgui.tree_pop()
        imgui.tree_pop()

    imgui.set_next_item_open(True, imgui.Cond_.once)
    if imgui.tree_node(
        "Towards NDC, With Arrows, Top Down Reading",
        "Towards NDC, With Arrows, Top Down Reading",
    ):
        imgui.set_next_item_open(True, imgui.Cond_.once)
        if imgui.tree_node("World->Camera", "World->Camera"):
            imgui.text("f_camera_to_world^-1(x) = ")
            imgui.text("     f_world_to_camera(x) = ")
            imgui.same_line()
            if highlighted_button("T^-1", 60, animation_time):
                animation_time = 60.0
            imgui.same_line()
            imgui.text("(x)")
            imgui.tree_pop()
        imgui.set_next_item_open(True, imgui.Cond_.once)
        if imgui.tree_node("Camera->NDC", "Camera->NDC"):
            imgui.text("f_camera_to_ndc(x) = ortho(x) = ")
            imgui.same_line()
            if highlighted_button("Scale", 65, animation_time):
                animation_time = 65.0
            imgui.same_line()
            imgui.text("(x)")
            imgui.tree_pop()
        imgui.tree_pop()

    imgui.end()

    imgui.set_next_window_bg_alpha(0.05)
    imgui.begin("Display Options", True)

    clicked_NDC, NDC = imgui.checkbox("NDC", NDC)
    imgui.end()

    imgui.set_next_window_bg_alpha(0.05)
    imgui.begin("Camera Options", True)

    (
        clicked_virtual_camera_positionx_clicked,
        virtual_camera_position[0],
    ) = imgui.slider_float(
        "Camera X_Worldspace", virtual_camera_position[0], -25, 25.0
    )
    (
        clicked_virtual_camera_positiony_clicked,
        virtual_camera_position[1],
    ) = imgui.slider_float(
        "Camera Y_Worldspace", virtual_camera_position[1], -25, 25.0
    )
    (
        clicked_virtual_camera_positionz_clicked,
        virtual_camera_position[2],
    ) = imgui.slider_float(
        "Camera Z_Worldspace", virtual_camera_position[2], -25, 25.0
    )

    imgui.end()

    width, height = glfw.get_framebuffer_size(window)
    GL.glViewport(0, 0, width, height)
    GL.glClear(sum([GL.GL_COLOR_BUFFER_BIT, GL.GL_DEPTH_BUFFER_BIT]))

    # render scene
    handle_inputs()

    draw_in_square_viewport()

    ms.set_to_identity_matrix(ms.MatrixStack.model)
    ms.set_to_identity_matrix(ms.MatrixStack.view)
    ms.set_to_identity_matrix(ms.MatrixStack.projection)

    # set the projection matrix to be ortho
    if NDC:
        ms.ortho(
            left=-1.0, right=1.0, bottom=-1.0, top=1.0, near=0.0, far=550.0
        )
    else:
        ms.ortho(
            left=-15.0,
            right=15.0,
            bottom=-15.0,
            top=15.0,
            near=0.0,
            far=550.0,
        )

    # note - opengl matricies use degrees
    ms.translate(ms.MatrixStack.view, 0.0, 0.0, -camera.r)
    ms.rotate_x(ms.MatrixStack.view, camera.rot_x)
    ms.rotate_y(ms.MatrixStack.view, -camera.rot_y)

    # draw NDC in global space, so that we can see the camera space
    # go to NDC
    with ms.PushMatrix(ms.MatrixStack.model):
        draw_cube(time=0.0)  # time stays still to stop animation
    with ms.PushMatrix(ms.MatrixStack.model):
        ms.rotate_y(ms.MatrixStack.model, math.radians(90.0))
        ms.rotate_z(ms.MatrixStack.model, math.radians(90.0))
        draw_ground(animation_time)

    if animation_time > 60.0:
        ms.translate(
            ms.MatrixStack.model,
            -virtual_camera_position[0]
            * min(1.0, (animation_time - 60.0) / 5.0),
            -virtual_camera_position[1]
            * min(1.0, (animation_time - 60.0) / 5.0),
            -virtual_camera_position[2]
            * min(1.0, (animation_time - 60.0) / 5.0),
        )

    # draw virtual camera
    if animation_time > 55.0:
        with ms.push_matrix(ms.MatrixStack.model):
            if animation_time > 55.0:
                ms.translate(
                    ms.MatrixStack.model,
                    virtual_camera_position[0]
                    * min(1.0, (animation_time - 55.0) / 5.0),
                    virtual_camera_position[1]
                    * min(1.0, (animation_time - 55.0) / 5.0),
                    virtual_camera_position[2]
                    * min(1.0, (animation_time - 55.0) / 5.0),
                )
            with ms.PushMatrix(ms.MatrixStack.model):
                with ms.PushMatrix(ms.MatrixStack.model):
                    ms.rotate_y(ms.MatrixStack.model, math.radians(90.0))
                    ms.rotate_z(ms.MatrixStack.model, math.radians(90.0))
                    draw_ground(animation_time)

                GL.glDisable(GL.GL_DEPTH_TEST)
                draw_axis(0.0)  # 0 time so it doesn't shrink
                GL.glEnable(GL.GL_DEPTH_TEST)
                # Draw the larger view-volume outline using the ±10 VAO so
                # the cylinder thickness stays consistent with the NDC cube.
                GL.glUseProgram(cube_pipeline.program)
                GL.glBindVertexArray(cube_big_vao)
                _p.set_uniforms(cube_pipeline.u_m, cube_pipeline.u_v, cube_pipeline.u_p)
                _set_frustum_uniforms(cube_pipeline.u_fov, cube_pipeline.u_aspect, cube_pipeline.u_near, cube_pipeline.u_far)
                GL.glUniform1f(cube_pipeline.u_time, animation_time)
                GL.glUniform3f(cube_pipeline.u_color, 1.0, 1.0, 1.0)
                GL.glDrawArrays(GL.GL_TRIANGLES, 0, cube_big_vertex_count)

    GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

    if animation_time < 5.0:
        with ms.PushMatrix(ms.MatrixStack.model):
            ms.rotate_y(ms.MatrixStack.model, math.radians(90.0))
            ms.rotate_z(ms.MatrixStack.model, math.radians(90.0))
            draw_ground(animation_time)
        GL.glDisable(GL.GL_DEPTH_TEST)
        draw_axis(animation_time)
        GL.glEnable(GL.GL_DEPTH_TEST)
    else:
        GL.glDisable(GL.GL_DEPTH_TEST)
        draw_axis(animation_time, grayed_out=True)
        GL.glEnable(GL.GL_DEPTH_TEST)

    with ms.PushMatrix(ms.MatrixStack.model):
        if animation_time > 5.0:
            ms.translate(
                ms.MatrixStack.model,
                paddle1_position[0] * min(1.0, (animation_time - 5.0) / 5.0),
                paddle1_position[1] * min(1.0, (animation_time - 5.0) / 5.0),
                0.0,
            )
        if animation_time > 10.0:
            ms.rotate_z(
                ms.MatrixStack.model,
                paddle1_rotation * min(1.0, (animation_time - 10.0) / 5.0),
            )

        if animation_time > 0.0 and animation_time < 15.0:
            with ms.PushMatrix(ms.MatrixStack.model):
                ms.rotate_y(ms.MatrixStack.model, math.radians(90.0))
                ms.rotate_z(ms.MatrixStack.model, math.radians(90.0))
                draw_ground(animation_time)

            GL.glDisable(GL.GL_DEPTH_TEST)
            draw_axis(animation_time)
            GL.glEnable(GL.GL_DEPTH_TEST)
        if animation_time > 15.0:
            # ascontiguousarray puts the array in column major order
            draw_triangles(
                paddle1_vao, paddle1_vertex_count, animation_time
            )

        # # draw the square

        if animation_time > 20.0:
            ms.rotate_z(
                ms.MatrixStack.model,
                rotation_around_paddle1
                * min(1.0, (animation_time - 20.0) / 5.0),
            )
        if animation_time > 25.0:
            ms.translate(
                ms.MatrixStack.model,
                1.5 * min(1.0, (animation_time - 25.0) / 5.0),
                0.0,
                0.0,
            )
        if animation_time > 30.0:
            ms.rotate_z(
                ms.MatrixStack.model,
                square_rotation * min(1.0, (animation_time - 30.0) / 5.0),
            )

        if animation_time > 10.0 and animation_time < 35.0:
            with ms.PushMatrix(ms.MatrixStack.model):
                ms.rotate_y(ms.MatrixStack.model, math.radians(90.0))
                ms.rotate_z(ms.MatrixStack.model, math.radians(90.0))
                draw_ground(animation_time)
            GL.glDisable(GL.GL_DEPTH_TEST)
            draw_axis(animation_time)
            GL.glEnable(GL.GL_DEPTH_TEST)

        if animation_time > 35.0:
            draw_triangles(square_vao, square_vertex_count, animation_time)

    # get back to center of global space

    with ms.PushMatrix(ms.MatrixStack.model):
        # draw paddle 2
        if animation_time > 40.0:
            ms.translate(
                ms.MatrixStack.model,
                paddle2_position[0] * min(1.0, (animation_time - 40.0) / 5.0),
                paddle2_position[1] * min(1.0, (animation_time - 40.0) / 5.0),
                0.0,
            )
        if animation_time > 45.0:
            ms.rotate_z(
                ms.MatrixStack.model,
                paddle2_rotation * min(1.0, (animation_time - 45.0) / 5.0),
            )

        if animation_time > 40.0 and animation_time < 50.0:
            with ms.PushMatrix(ms.MatrixStack.model):
                ms.rotate_y(ms.MatrixStack.model, math.radians(90.0))
                ms.rotate_z(ms.MatrixStack.model, math.radians(90.0))
                draw_ground(animation_time)
            GL.glDisable(GL.GL_DEPTH_TEST)
            draw_axis(animation_time)
            GL.glEnable(GL.GL_DEPTH_TEST)

        if animation_time > 50.0:
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
