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

window, impl, imguiio = _p.setup_window("Push Matrix")
_p.install_esc_close(window)


# ---------------------------------------------------------------------------
# Pipeline -- compile each shader program once, cache uniform / attribute
# locations.
# ---------------------------------------------------------------------------


# Triangle pipeline (paddles + square)
triangle_program: int = _p.compile_program(PWD, "triangle.vert", "triangle.frag")
u_triangle_m: int = GL.glGetUniformLocation(triangle_program, "mMatrix")
u_triangle_v: int = GL.glGetUniformLocation(triangle_program, "vMatrix")
u_triangle_p: int = GL.glGetUniformLocation(triangle_program, "pMatrix")
triangle_attr_position: int = GL.glGetAttribLocation(
    triangle_program, "position"
)
triangle_attr_color: int = GL.glGetAttribLocation(triangle_program, "color_in")

# Ground pipeline: solid dark-gray cylinders.  Reuses ground.vert
# (hardcoded dark gray) + triangle.frag (no geom shader).
ground_program: int = _p.compile_program(PWD, "ground.vert", "triangle.frag")
u_ground_m: int = GL.glGetUniformLocation(ground_program, "mMatrix")
u_ground_v: int = GL.glGetUniformLocation(ground_program, "vMatrix")
u_ground_p: int = GL.glGetUniformLocation(ground_program, "pMatrix")
ground_attr_position: int = GL.glGetAttribLocation(ground_program, "position")

# Axis pipeline: solid cylinder+cone arrows (axis.vert + triangle.frag, no geom)
axis_program: int = _p.compile_program(PWD, "axis.vert", "triangle.frag")
u_axis_m: int = GL.glGetUniformLocation(axis_program, "mMatrix")
u_axis_v: int = GL.glGetUniformLocation(axis_program, "vMatrix")
u_axis_p: int = GL.glGetUniformLocation(axis_program, "pMatrix")
u_axis_color: int = GL.glGetUniformLocation(axis_program, "color")
axis_attr_position: int = GL.glGetAttribLocation(axis_program, "position")

# NDC-cube pipeline: solid white cylinders, no end cones.  Reuses the
# axis.vert + triangle.frag shader pair (same as the axis pipeline).
cube_program: int = _p.compile_program(PWD, "axis.vert", "triangle.frag")
u_cube_m: int = GL.glGetUniformLocation(cube_program, "mMatrix")
u_cube_v: int = GL.glGetUniformLocation(cube_program, "vMatrix")
u_cube_p: int = GL.glGetUniformLocation(cube_program, "pMatrix")
u_cube_color: int = GL.glGetUniformLocation(cube_program, "color")
cube_attr_position: int = GL.glGetAttribLocation(cube_program, "position")


# ---------------------------------------------------------------------------
# Geometry.
# ---------------------------------------------------------------------------

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
cube_vao, cube_vertex_count = _p.make_lines_vao(
    _p.build_ndc_cube_cylinders(), cube_attr_position
)


# ---------------------------------------------------------------------------
# Scene state.
# ---------------------------------------------------------------------------


paddle1_position: ndarray = np.array([-9.0, 1.0, 0.0])
paddle1_rotation: float = math.radians(45.0)

paddle2_position: ndarray = np.array([9.0, 0.5, 0.0])
paddle2_rotation: float = math.radians(-20.0)

square_rotation: float = math.radians(45.0)
rotation_around_paddle1: float = math.radians(10.0)


camera = _p.Camera(
    r=25.0, rot_y=math.radians(45.0), rot_x=math.radians(35.264)
)
_p.install_camera_scroll(window, imguiio, camera)


# ---------------------------------------------------------------------------
# Rendering helpers.
# ---------------------------------------------------------------------------


def draw_triangles(vao: int, vertex_count: int) -> None:
    GL.glUseProgram(triangle_program)
    GL.glBindVertexArray(vao)
    _p.upload_mvp(u_triangle_m, u_triangle_v, u_triangle_p)
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, vertex_count)
    GL.glBindVertexArray(0)


def draw_ground() -> None:
    GL.glUseProgram(ground_program)
    GL.glBindVertexArray(ground_vao)
    _p.upload_mvp(u_ground_m, u_ground_v, u_ground_p)
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, ground_vertex_count)
    GL.glBindVertexArray(0)


def _emit_axis(r: float, g: float, b: float, grayed_out: bool) -> None:
    if grayed_out:
        GL.glUniform3f(u_axis_color, 0.5, 0.5, 0.5)
    else:
        GL.glUniform3f(u_axis_color, r, g, b)
    _p.upload_mvp(u_axis_m, u_axis_v, u_axis_p)
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
    GL.glBindVertexArray(0)


def draw_cube() -> None:
    GL.glUseProgram(cube_program)
    GL.glBindVertexArray(cube_vao)
    _p.upload_mvp(u_cube_m, u_cube_v, u_cube_p)
    GL.glUniform3f(u_cube_color, 1.0, 1.0, 1.0)
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, cube_vertex_count)
    GL.glBindVertexArray(0)


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


virtual_camera_position = np.array([-15.0, 0.0, 85.0], dtype=np.float32)
virtual_camera_rot_y = math.radians(25.0)
virtual_camera_rot_x = math.radians(15.0)


TARGET_FRAMERATE = 60  # fps

# to try to standardize on 60 fps, compare times between frames
time_at_beginning_of_previous_frame = glfw.get_time()

animation_time = 0.0
animation_time_multiplier = 1.0
animation_paused = False


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
            if highlighted_button("R_z", 10, animation_time):
                animation_time = 10.0
            imgui.same_line()
            imgui.text(" ) (x) ")

            imgui.set_next_item_open(True, imgui.Cond_.once)
            if imgui.tree_node("Square->World", "Square->World"):
                imgui.text("f_translate_neg_z(x) = ")
                imgui.text(" f_paddle1_to_world o ")
                imgui.same_line()
                if highlighted_button("T_-Z", 15, animation_time):
                    animation_time = 15.0
                imgui.text(" f_paddle1_to_world o (")

                imgui.set_next_item_open(True, imgui.Cond_.once)
                if imgui.tree_node("4 Squares", "4 Squares"):
                    imgui.text("f_square1(x) = ")
                    imgui.text(" f_translate_neg_z o (")
                    imgui.text("     ")
                    imgui.same_line()
                    if highlighted_button("R_Z##2", 20, animation_time):
                        animation_time = 20.0
                    imgui.same_line()
                    imgui.text(" o ")
                    imgui.same_line()
                    if highlighted_button("T_X##2", 25, animation_time):
                        animation_time = 25.0
                    imgui.same_line()
                    imgui.text(" o ")
                    imgui.same_line()
                    if highlighted_button("R2_Z##2", 30, animation_time):
                        animation_time = 30.0
                    imgui.same_line()
                    imgui.text(" ) (x) ")

                    imgui.text("f_square2(x) = ")
                    imgui.text(" f_translate_neg_z o (")
                    imgui.text("     ")
                    imgui.same_line()
                    if highlighted_button("R_Z+90Deg", 40, animation_time):
                        animation_time = 40.0
                    imgui.same_line()
                    imgui.text(" o ")
                    imgui.same_line()
                    if highlighted_button("T_X##3", 45, animation_time):
                        animation_time = 45.0
                    imgui.same_line()
                    imgui.text(" o ")
                    imgui.same_line()
                    if highlighted_button("R2_Z##3", 50, animation_time):
                        animation_time = 50.0
                    imgui.same_line()
                    imgui.text(" ) (x) ")

                    imgui.text("f_square3(x) = ")
                    imgui.text(" f_translate_neg_z o (")
                    imgui.text("     ")
                    imgui.same_line()
                    if highlighted_button("R_Z+180Deg", 60, animation_time):
                        animation_time = 60.0
                    imgui.same_line()
                    imgui.text(" o ")
                    imgui.same_line()
                    if highlighted_button("T_X##4", 65, animation_time):
                        animation_time = 65.0
                    imgui.same_line()
                    imgui.text(" o ")
                    imgui.same_line()
                    if highlighted_button("R2_Z##4", 70, animation_time):
                        animation_time = 70.0
                    imgui.same_line()
                    imgui.text(" ) (x) ")

                    imgui.text("f_square4(x) = ")
                    imgui.text(" f_translate_neg_z o (")
                    imgui.text("     ")
                    imgui.same_line()
                    if highlighted_button("R_Z+270Deg", 80, animation_time):
                        animation_time = 80.0
                    imgui.same_line()
                    imgui.text(" o ")
                    imgui.same_line()
                    if highlighted_button("T_X##5", 85, animation_time):
                        animation_time = 85.0
                    imgui.same_line()
                    imgui.text(" o ")
                    imgui.same_line()
                    if highlighted_button("R2_Z##5", 90, animation_time):
                        animation_time = 90.0
                    imgui.same_line()
                    imgui.text(" ) (x) ")
                    imgui.tree_pop()

                imgui.tree_pop()
            imgui.tree_pop()
        imgui.tree_pop()

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

    # note - opengl matricies use degrees
    ms.translate(ms.MatrixStack.view, 0.0, 0.0, -camera.r)
    ms.rotate_x(ms.MatrixStack.view, camera.rot_x)
    ms.rotate_y(ms.MatrixStack.view, -camera.rot_y)

    # draw NDC in global space, so that we can see the camera space
    # go to NDC
    with ms.PushMatrix(ms.MatrixStack.model):
        draw_cube()
    draw_ground()

    if animation_time < 5.0 or animation_time > 95:
        draw_axis()
    else:
        draw_axis(grayed_out=True)

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

        if animation_time > 15.0:
            # ascontiguousarray puts the array in column major order
            draw_triangles(paddle1_vao, paddle1_vertex_count)
        if animation_time > 0.0 and animation_time < 15.0:
            draw_axis()

        # # draw the square

        if animation_time > 15.0:
            ms.translate(
                ms.MatrixStack.model,
                0.0,
                0.0,
                -5.0 * min(1.0, (animation_time - 15.0) / 5.0),
            )
        if animation_time > 15:
            draw_axis(grayed_out=animation_time > 20.0)

        # square 1
        with ms.PushMatrix(ms.MatrixStack.model):
            if animation_time > 20.0:
                ms.rotate_z(
                    ms.MatrixStack.model,
                    rotation_around_paddle1
                    * min(1.0, (animation_time - 20.0) / 5.0),
                )
            if animation_time > 25.0:
                ms.translate(
                    ms.MatrixStack.model,
                    3.0 * min(1.0, (animation_time - 25.0) / 5.0),
                    0.0,
                    0.0,
                )
            if animation_time > 30.0:
                ms.rotate_z(
                    ms.MatrixStack.model,
                    square_rotation * min(1.0, (animation_time - 30.0) / 5.0),
                )

            if animation_time > 35.0:
                draw_triangles(square_vao, square_vertex_count)
            if animation_time > 20.0 and animation_time < 35.0:
                draw_axis()
        # square 2
        with ms.PushMatrix(ms.MatrixStack.model):
            if animation_time > 40.0:
                ms.rotate_z(
                    ms.MatrixStack.model,
                    (rotation_around_paddle1 + math.radians(90))
                    * min(1.0, (animation_time - 40.0) / 5.0),
                )
            if animation_time > 45.0:
                ms.translate(
                    ms.MatrixStack.model,
                    3.0 * min(1.0, (animation_time - 45.0) / 5.0),
                    0.0,
                    0.0,
                )
            if animation_time > 50.0:
                ms.rotate_z(
                    ms.MatrixStack.model,
                    square_rotation * min(1.0, (animation_time - 50.0) / 5.0),
                )

            if animation_time > 55.0:
                draw_triangles(square_vao, square_vertex_count)
            if animation_time > 40.0 and animation_time < 55.0:
                draw_axis()
        # square 3
        with ms.PushMatrix(ms.MatrixStack.model):
            if animation_time > 60.0:
                ms.rotate_z(
                    ms.MatrixStack.model,
                    (rotation_around_paddle1 + math.radians(180))
                    * min(1.0, (animation_time - 60.0) / 5.0),
                )
            if animation_time > 65.0:
                ms.translate(
                    ms.MatrixStack.model,
                    3.0 * min(1.0, (animation_time - 65.0) / 5.0),
                    0.0,
                    0.0,
                )
            if animation_time > 70.0:
                ms.rotate_z(
                    ms.MatrixStack.model,
                    square_rotation * min(1.0, (animation_time - 70.0) / 5.0),
                )

            if animation_time > 75.0:
                draw_triangles(square_vao, square_vertex_count)
            if animation_time > 60.0 and animation_time < 75.0:
                draw_axis()
        # square 4
        with ms.PushMatrix(ms.MatrixStack.model):
            if animation_time > 80.0:
                ms.rotate_z(
                    ms.MatrixStack.model,
                    (rotation_around_paddle1 + math.radians(270))
                    * min(1.0, (animation_time - 80.0) / 5.0),
                )
            if animation_time > 85.0:
                ms.translate(
                    ms.MatrixStack.model,
                    3.0 * min(1.0, (animation_time - 85.0) / 5.0),
                    0.0,
                    0.0,
                )
            if animation_time > 90.0:
                ms.rotate_z(
                    ms.MatrixStack.model,
                    square_rotation * min(1.0, (animation_time - 90.0) / 5.0),
                )

            if animation_time > 95.0:
                draw_triangles(square_vao, square_vertex_count)
            if animation_time > 80.0 and animation_time < 95.0:
                draw_axis()

    imgui.render()
    impl.render(imgui.get_draw_data())

    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)


_p.cleanup()
glfw.terminate()
