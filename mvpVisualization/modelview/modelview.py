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
import sys
from dataclasses import dataclass, field
from typing import Optional, Tuple

import glfw
import numpy as np
import numpy.typing
import OpenGL.GL as GL

import modelviewprojection.pyMatrixStack as ms

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 0)

window = glfw.create_window(1920, 1080, "Model View", None, None)
if not window:
    glfw.terminate()
    sys.exit()

# Make the window's context current
glfw.make_context_current(window)


# Install a key handler


def on_key(win, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(win, 1)


glfw.set_key_callback(window, on_key)


_prev_scroll_cb = None
def scroll_callback(win, x_offset, y_offset):
    if _prev_scroll_cb:
        _prev_scroll_cb(win, x_offset, y_offset)
    camera.r = camera.r + -1 * (y_offset * math.log(camera.r))
    if camera.r < 3.0:
        camera.r = 3.0
_prev_scroll_cb = glfw.set_scroll_callback(window, scroll_callback)


GL.glClearColor(13.0 / 255.0, 64.0 / 255.0, 5.0 / 255.0, 1.0)

# NEW - TODO - talk about opengl matricies and z pos/neg
GL.glEnable(GL.GL_DEPTH_TEST)
GL.glClearDepth(1.0)
GL.glDepthFunc(GL.GL_LEQUAL)


@dataclass
class Paddle:
    r: float
    g: float
    b: float
    position: numpy.typing.NDArray
    rotation: float = 0.0
    vertices: np.array = field(
        default_factory=lambda: np.array(
            [
                [-1.0, -3.0, 0.0],
                [1.0, -3.0, 0.0],
                [1.0, 3.0, 0.0],
                [-1.0, 3.0, 0.0],
            ],
            dtype=np.float32,
        )
    )


paddle1 = Paddle(
    r=0.578123,
    g=0.0,
    b=1.0,
    position=np.array([-9.0, 1.0, 0.0]),
    rotation=math.radians(45.0),
)

paddle2 = Paddle(
    r=1.0,
    g=1.0,
    b=0.0,
    position=np.array([9.0, 0.5, 0.0]),
    rotation=math.radians(-45.0),
)


@dataclass
class Camera:
    r: float = 0.0
    rot_y: float = 0.0
    rot_x: float = 0.0


camera = Camera(r=30.0, rot_y=math.radians(45.0), rot_x=math.radians(35.264))


square_rotation = math.radians(90.0)
rotation_around_paddle1 = math.radians(30.0)


def handle_inputs(
    previous_mouse_position: Optional[Tuple[float, float]],
) -> None:
    global rotation_around_paddle1
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        rotation_around_paddle1 += 0.1

    global square_rotation
    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square_rotation += 0.1

    global camera

    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.rot_y -= math.radians(1.0) % 360.0
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.rot_y += math.radians(1.0) % 360.0
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera.rot_x -= math.radians(1.0) % 360.0
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.rot_x += math.radians(1.0) % 360.0

    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.position[1] -= 1.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.position[1] += 1.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.position[1] -= 1.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.position[1] += 1.0

    global paddle_1_rotation, paddle_2_rotation

    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        paddle1.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        paddle1.rotation -= 0.1
    if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
        paddle2.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_L) == glfw.PRESS:
        paddle2.rotation -= 0.1

    global animation_time
    if glfw.get_key(window, glfw.KEY_1) == glfw.PRESS:
        animation_time = 5.0
    if glfw.get_key(window, glfw.KEY_2) == glfw.PRESS:
        animation_time = 15.0
    if glfw.get_key(window, glfw.KEY_3) == glfw.PRESS:
        animation_time = 35.0
    if glfw.get_key(window, glfw.KEY_4) == glfw.PRESS:
        animation_time = 55.0
    if glfw.get_key(window, glfw.KEY_5) == glfw.PRESS:
        animation_time = 70.0
    if glfw.get_key(window, glfw.KEY_6) == glfw.PRESS:
        animation_time = 85.0

    new_mouse_position = glfw.get_cursor_pos(window)
    return_none = False
    if glfw.PRESS == glfw.get_mouse_button(window, glfw.MOUSE_BUTTON_LEFT):
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


square_vertices = np.array(
    [[-0.5, -0.5, 0.0], [0.5, -0.5, 0.0], [0.5, 0.5, 0.0], [-0.5, 0.5, 0.0]],
    dtype=np.float32,
)
virtual_camera_position = np.array([-4.0, 0.0, 8.0], dtype=np.float32)
virtual_camera_rot_y = math.radians(-30.0)
virtual_camera_rot_x = math.radians(15.0)


def draw_ground() -> None:
    # ascontiguousarray puts the array in column major order
    GL.glLoadMatrixf(
        np.ascontiguousarray(ms.get_current_matrix(ms.MatrixStack.modelview).T)
    )
    GL.glColor3f(0.1, 0.1, 0.1)
    # 41 horizontal cylinders (along X, varying Z) + 41 vertical (along Z,
    # varying X), spanning [-20, 20] at y=-5.  Same edges as the cylinder
    # ground in the shader-based demos.
    for i in range(-20, 21, 1):
        coord = float(i)
        # horizontal at z = coord
        draw_cylinder_edge(
            (-20.0, -5.0, coord), (20.0, -5.0, coord), 0.05, 20
        )
        # vertical at x = coord
        draw_cylinder_edge(
            (coord, -5.0, -20.0), (coord, -5.0, 20.0), 0.05, 20
        )


def draw_solid_cylinder(
    base_radius: float, top_radius: float, height: float, slices: int
) -> None:
    """Cylinder side surface oriented along +Z."""
    GL.glBegin(GL.GL_QUAD_STRIP)
    for i in range(slices + 1):
        a = 2.0 * math.pi * float(i) / slices
        c, s = math.cos(a), math.sin(a)
        GL.glNormal3f(c, s, 0.0)
        GL.glVertex3f(c * base_radius, s * base_radius, 0.0)
        GL.glVertex3f(c * top_radius, s * top_radius, height)
    GL.glEnd()


def draw_solid_cone(base: float, height: float, slices: int) -> None:
    """Cone with apex on +Z and a base disk closing the bottom."""
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glNormal3f(0.0, 0.0, 1.0)
    GL.glVertex3f(0.0, 0.0, height)
    for i in range(slices + 1):
        a = 2.0 * math.pi * float(i) / slices
        GL.glVertex3f(math.cos(a) * base, math.sin(a) * base, 0.0)
    GL.glEnd()
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glNormal3f(0.0, 0.0, -1.0)
    GL.glVertex3f(0.0, 0.0, 0.0)
    for i in range(slices, -1, -1):
        a = 2.0 * math.pi * float(i) / slices
        GL.glVertex3f(math.cos(a) * base, math.sin(a) * base, 0.0)
    GL.glEnd()


def draw_solid_sphere(radius: float, slices: int, stacks: int) -> None:
    """Solid sphere centered at the origin -- the white ball that
    gltDrawUnitAxes finishes with.  (lat1, lat0)-pair winding keeps the
    outward face CCW under glFrontFace(GL_CCW)."""
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        s0, c0 = math.sin(lat0), math.cos(lat0)
        s1, c1 = math.sin(lat1), math.cos(lat1)
        GL.glBegin(GL.GL_QUAD_STRIP)
        for j in range(slices + 1):
            lng = 2.0 * math.pi * float(j) / slices
            cl, sl = math.cos(lng), math.sin(lng)
            GL.glNormal3f(cl * c1, sl * c1, s1)
            GL.glVertex3f(radius * cl * c1, radius * sl * c1, radius * s1)
            GL.glNormal3f(cl * c0, sl * c0, s0)
            GL.glVertex3f(radius * cl * c0, radius * sl * c0, radius * s0)
        GL.glEnd()


def draw_y_axis() -> None:
    """Draw a +Y-pointing cylinder shaft + cone arrowhead at the current
    modelview transform.  Caller has already issued glColor3f for the
    desired (or grayed-out) color."""
    rod_radius = 0.05
    cone_radius = 0.12
    rod_length = 0.85
    cone_length = 0.15

    # ascontiguousarray puts the array in column major order
    GL.glLoadMatrixf(
        np.ascontiguousarray(ms.get_current_matrix(ms.MatrixStack.modelview).T)
    )
    # The cylinder/cone helpers build along +Z; rotate -90 about X so they
    # point along +Y.
    GL.glRotatef(-90.0, 1.0, 0.0, 0.0)
    draw_solid_cylinder(rod_radius, rod_radius, rod_length, 20)
    GL.glTranslatef(0.0, 0.0, rod_length)
    draw_solid_cone(cone_radius, cone_length, 20)


def draw_axises(grayed_out: bool = False) -> None:
    with ms.push_matrix(ms.MatrixStack.model):
        # x axis
        with ms.push_matrix(ms.MatrixStack.model):
            ms.rotate_z(ms.MatrixStack.model, math.radians(-90.0))

            GL.glColor3f(1.0, 0.0, 0.0)
            if grayed_out:
                GL.glColor3f(0.5, 0.5, 0.5)
            draw_y_axis()

        # z
        GL.glColor3f(0.0, 0.0, 1.0)  # blue z
        with ms.push_matrix(ms.MatrixStack.model):
            ms.rotate_y(ms.MatrixStack.model, math.radians(90.0))
            ms.rotate_z(ms.MatrixStack.model, math.radians(90.0))

            GL.glColor3f(0.0, 0.0, 1.0)
            if grayed_out:
                GL.glColor3f(0.5, 0.5, 0.5)
            draw_y_axis()

        # y
        GL.glColor3f(0.0, 1.0, 0.0)  # green y
        if grayed_out:
            GL.glColor3f(0.5, 0.5, 0.5)
        draw_y_axis()

        # White (or grayed) sphere at the origin -- the dot that
        # gltDrawUnitAxes draws to mark the frame's origin.
        GL.glLoadMatrixf(
            np.ascontiguousarray(
                ms.get_current_matrix(ms.MatrixStack.modelview).T
            )
        )
        if grayed_out:
            GL.glColor3f(0.5, 0.5, 0.5)
        else:
            GL.glColor3f(1.0, 1.0, 1.0)
        # Rod radius here is 0.05, so 0.05 sphere disappears into the
        # axis shaft.  0.10 keeps the C++ 2x-rod visual ratio.
        draw_solid_sphere(0.10, 15, 15)


def draw_cylinder_edge(p0, p1, radius: float, slices: int) -> None:
    """Draw a cylinder shaft connecting p0 to p1 with the given radius.
    The cylinder helper builds along +Z; this rotates that local +Z to
    align with (p1 - p0) before drawing."""
    direction = np.asarray(p1, dtype=np.float64) - np.asarray(p0, dtype=np.float64)
    length = float(np.linalg.norm(direction))
    if length < 1e-9:
        return
    GL.glPushMatrix()
    GL.glTranslatef(float(p0[0]), float(p0[1]), float(p0[2]))
    forward = direction / length
    z_axis = np.array([0.0, 0.0, 1.0])
    cos_angle = float(np.dot(z_axis, forward))
    if cos_angle > 0.9999:
        pass  # already aligned with +Z
    elif cos_angle < -0.9999:
        GL.glRotatef(180.0, 1.0, 0.0, 0.0)
    else:
        axis = np.cross(z_axis, forward)
        axis_len = float(np.linalg.norm(axis))
        axis = axis / axis_len
        angle_deg = math.degrees(math.acos(cos_angle))
        GL.glRotatef(angle_deg, float(axis[0]), float(axis[1]), float(axis[2]))
    draw_solid_cylinder(radius, radius, length, slices)
    GL.glPopMatrix()


# this isn't really NDC, I scaled it so that it looks good, not be correct
def draw_ndc() -> None:
    GL.glLoadMatrixf(
        np.ascontiguousarray(ms.get_current_matrix(ms.MatrixStack.modelview).T)
    )

    GL.glColor3f(1.0, 1.0, 1.0)
    edges = [
        # back square (z = -1)
        ((-1.0, -1.0, -1.0), ( 1.0, -1.0, -1.0)),
        (( 1.0, -1.0, -1.0), ( 1.0,  1.0, -1.0)),
        (( 1.0,  1.0, -1.0), (-1.0,  1.0, -1.0)),
        ((-1.0,  1.0, -1.0), (-1.0, -1.0, -1.0)),
        # front square (z = +1)
        ((-1.0, -1.0,  1.0), ( 1.0, -1.0,  1.0)),
        (( 1.0, -1.0,  1.0), ( 1.0,  1.0,  1.0)),
        (( 1.0,  1.0,  1.0), (-1.0,  1.0,  1.0)),
        ((-1.0,  1.0,  1.0), (-1.0, -1.0,  1.0)),
        # connecting edges
        (( 1.0,  1.0, -1.0), ( 1.0,  1.0,  1.0)),
        (( 1.0, -1.0, -1.0), ( 1.0, -1.0,  1.0)),
        ((-1.0,  1.0, -1.0), (-1.0,  1.0,  1.0)),
        ((-1.0, -1.0, -1.0), (-1.0, -1.0,  1.0)),
    ]
    for p0, p1 in edges:
        draw_cylinder_edge(p0, p1, 0.05, 20)


TARGET_FRAMERATE = 60  # fps

# to try to standardize on 60 fps, compare times between frames
time_at_beginning_of_previous_frame = glfw.get_time()

animation_time = 0.0
animation_time_multiplier = 1.0
animation_paused = False


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
    # ms.ortho(left=-150.0,
    #          right=150.0,
    #          back=-150.0,
    #          top=150.0,
    #          near=1.0,
    #          far=10000.0)

    GL.glMatrixMode(GL.GL_PROJECTION)
    # ascontiguousarray puts the array in column major order
    GL.glLoadMatrixf(
        np.ascontiguousarray(ms.get_current_matrix(ms.MatrixStack.projection).T)
    )

    # note - opengl matricies use degrees
    ms.translate(ms.MatrixStack.view, 0.0, 0.0, -camera.r)
    ms.rotate_x(ms.MatrixStack.view, camera.rot_x)
    ms.rotate_y(ms.MatrixStack.view, -camera.rot_y)

    GL.glMatrixMode(GL.GL_MODELVIEW)

    # draw NDC in global space, so that we can see the camera space
    # go to NDC
    with ms.PushMatrix(ms.MatrixStack.model):
        draw_ndc()
    draw_ground()

    if animation_time > 80.0:
        ms.rotate_x(
            ms.MatrixStack.model,
            -virtual_camera_rot_x * min(1.0, (animation_time - 80.0) / 5.0),
        )
    if animation_time > 75.0:
        ms.rotate_y(
            ms.MatrixStack.model,
            -virtual_camera_rot_y * min(1.0, (animation_time - 75.0) / 5.0),
        )
    if animation_time > 70.0:
        ms.translate(
            ms.MatrixStack.model,
            -virtual_camera_position[0]
            * min(1.0, (animation_time - 70.0) / 5.0),
            -virtual_camera_position[1]
            * min(1.0, (animation_time - 70.0) / 5.0),
            -virtual_camera_position[2]
            * min(1.0, (animation_time - 70.0) / 5.0),
        )

    # draw virtual camera
    if animation_time > 55:
        with ms.push_matrix(ms.MatrixStack.model):
            if animation_time > 55:
                ms.translate(
                    ms.MatrixStack.model,
                    virtual_camera_position[0]
                    * min(1.0, (animation_time - 55.0) / 5.0),
                    virtual_camera_position[1]
                    * min(1.0, (animation_time - 55.0) / 5.0),
                    virtual_camera_position[2]
                    * min(1.0, (animation_time - 55.0) / 5.0),
                )
            if animation_time > 60:
                ms.rotate_y(
                    ms.MatrixStack.model,
                    virtual_camera_rot_y
                    * min(1.0, (animation_time - 60.0) / 5.0),
                )
            if animation_time > 65:
                ms.rotate_x(
                    ms.MatrixStack.model,
                    virtual_camera_rot_x
                    * min(1.0, (animation_time - 65.0) / 5.0),
                )

            draw_axises()

            draw_ndc()

    if (
        animation_time < 5.0
        or (animation_time > 35.0 and animation_time < 40.0)
        or (animation_time > 50.0 and animation_time < 55.0)
    ):
        draw_axises()
    else:
        draw_axises(grayed_out=True)

    with ms.PushMatrix(ms.MatrixStack.model):
        if animation_time > 5.0:
            ms.translate(
                ms.MatrixStack.model,
                paddle1.position[0] * min(1.0, (animation_time - 5.0) / 5.0),
                paddle1.position[1] * min(1.0, (animation_time - 5.0) / 5.0),
                0.0,
            )
        if animation_time > 10.0:
            ms.rotate_z(
                ms.MatrixStack.model,
                paddle1.rotation * min(1.0, (animation_time - 10.0) / 5.0),
            )

        if animation_time > 5.0 and animation_time < 15.0:
            draw_axises()
        GL.glColor3f(paddle1.r, paddle1.g, paddle1.b)
        if animation_time > 15.0:
            # ascontiguousarray puts the array in column major order
            GL.glLoadMatrixf(
                np.ascontiguousarray(
                    ms.get_current_matrix(ms.MatrixStack.modelview).T
                )
            )
            GL.glBegin(GL.GL_QUADS)
            for model_space in paddle1.vertices:
                GL.glVertex3f(model_space[0], model_space[1], model_space[2])
            GL.glEnd()

        # # draw the square

        if animation_time > 15.0:
            ms.translate(
                ms.MatrixStack.model,
                0.0,
                0.0,
                -1.0 * min(1.0, (animation_time - 15.0) / 5.0),
            )
        if animation_time > 20.0:
            ms.rotate_z(
                ms.MatrixStack.model,
                rotation_around_paddle1
                * min(1.0, (animation_time - 20.0) / 5.0),
            )
        if animation_time > 25.0:
            ms.translate(
                ms.MatrixStack.model,
                2.0 * min(1.0, (animation_time - 25.0) / 5.0),
                0.0,
                0.0,
            )
        if animation_time > 30.0:
            ms.rotate_z(
                ms.MatrixStack.model,
                square_rotation * min(1.0, (animation_time - 30.0) / 5.0),
            )

        if animation_time > 10.0 and animation_time < 35.0:
            draw_axises()

        GL.glColor3f(0.0, 0.0, 1.0)  # r  # g  # b
        if animation_time > 35.0:
            # ascontiguousarray puts the array in column major order
            GL.glLoadMatrixf(
                np.ascontiguousarray(
                    ms.get_current_matrix(ms.MatrixStack.modelview).T
                )
            )
            GL.glBegin(GL.GL_QUADS)
            for model_space in square_vertices:
                GL.glVertex3f(model_space[0], model_space[1], model_space[2])
            GL.glEnd()

    # get back to center of global space

    with ms.PushMatrix(ms.MatrixStack.model):
        # draw paddle 2

        if animation_time > 40.0:
            ms.translate(
                ms.MatrixStack.model,
                paddle2.position[0] * min(1.0, (animation_time - 40.0) / 5.0),
                paddle2.position[1] * min(1.0, (animation_time - 40.0) / 5.0),
                0.0,
            )
        if animation_time > 45.0:
            ms.rotate_z(
                ms.MatrixStack.model,
                paddle2.rotation * min(1.0, (animation_time - 45.0) / 5.0),
            )

        if animation_time > 40.0 and animation_time < 50.0:
            draw_axises()

        GL.glColor3f(paddle2.r, paddle2.g, paddle2.b)
        if animation_time > 50.0:
            # ascontiguousarray puts the array in column major order
            GL.glLoadMatrixf(
                np.ascontiguousarray(
                    ms.get_current_matrix(ms.MatrixStack.modelview).T
                )
            )
            GL.glBegin(GL.GL_QUADS)
            for model_space in paddle2.vertices:
                GL.glVertex3f(model_space[0], model_space[1], model_space[2])
            GL.glEnd()

    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)


glfw.terminate()
