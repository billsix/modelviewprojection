
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

# Demo 19a -- A unit-axis gizmo (X red, Y green, Z blue).
# Ported from OpenGL SuperBible 4e, chapter 10 example "axes3d".
#
# Why this demo:  every coordinate system you use in the course has
# three basis vectors -- e_1, e_2, e_3.  Drawing them at the origin
# of a frame makes the frame's orientation visible.  Drop a
# draw_unit_axes() call inside any glPushMatrix block to "see" what
# the current modelview matrix is doing to the basis.
#
# Controls:  LEFT/RIGHT yaw, PAGE_UP/PAGE_DOWN pitch, UP/DOWN walk
# forward/back -- standard walk-around camera shared with the other
# 3D demos.

import dataclasses
import math
import sys

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU

from modelviewprojection.axes import draw_unit_axes
from modelviewprojection.cameracontrols import walk_around_camera
from modelviewprojection.clipping import draw_in_square_viewport
from modelviewprojection.windowing import on_key

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(
    500, 500, "ModelViewProjection Demo 19a -- Axes", None, None
)
if not window:
    glfw.terminate()
    sys.exit()

glfw.make_context_current(window)


glfw.set_key_callback(window, on_key)

GL.glClearColor(0.0289, 0.071875, 0.0972, 1.0)

GL.glEnable(GL.GL_DEPTH_TEST)
GL.glClearDepth(1.0)
GL.glDepthFunc(GL.GL_LEQUAL)


@dataclasses.dataclass
class Camera:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rot_y: float = 0.0
    rot_x: float = 0.0


camera: Camera = Camera(z=5.0)


def handle_inputs() -> None:
    walk_around_camera(window, camera, move_step=0.1)


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

    width, height = glfw.get_framebuffer_size(window)
    GL.glViewport(0, 0, width, height)
    GL.glClear(sum([GL.GL_COLOR_BUFFER_BIT, GL.GL_DEPTH_BUFFER_BIT]))

    draw_in_square_viewport(window)
    handle_inputs()

    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(45.0, 1.0, 0.1, 100.0)

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    # Walk-around camera transform:  rotate the world opposite the
    # camera's heading, then translate so the camera sits at origin
    # in its own space.
    GL.glRotatef(math.degrees(-camera.rot_x), 1.0, 0.0, 0.0)
    GL.glRotatef(math.degrees(-camera.rot_y), 0.0, 1.0, 0.0)
    GL.glTranslatef(-camera.x, -camera.y, -camera.z)

    draw_unit_axes()

    glfw.swap_buffers(window)

glfw.terminate()
