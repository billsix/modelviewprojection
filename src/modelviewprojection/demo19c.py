
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

# Demo 19c -- Solar system (sun -> earth -> moon).
# Ported from OpenGL SuperBible 4e, chapter 4 example "solar".
#
# This is the canonical demo for *two* levels of nesting.  The earth's
# coordinate system is built from the sun's by (rotate, translate);
# the moon's coordinate system is built from the earth's the same way.
# That means when the earth orbits, the moon's whole local frame is
# carried along automatically -- exactly because the earth's transform
# is still on the matrix stack when we draw the moon.
#
# Pop the inner glPushMatrix/glPopMatrix in the moon block and watch the
# moon spiral away:  popping early throws away the earth's frame, so
# the moon orbits the sun directly.
#
# Controls:  arrow keys yaw/pitch the world; PageUp/PageDown move the
# camera in/out.

import math
import sys

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU

from modelviewprojection.windowing import on_key

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(
    500, 500, "ModelViewProjection Demo 19c -- Solar", None, None
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
GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)


def draw_in_square_viewport() -> None:
    GL.glClearColor(0.2, 0.2, 0.2, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    w, h = glfw.get_framebuffer_size(window)
    minimal_dimension = w if w < h else h

    GL.glEnable(GL.GL_SCISSOR_TEST)
    GL.glScissor(
        int((w - minimal_dimension) / 2.0),
        int((h - minimal_dimension) / 2.0),
        minimal_dimension,
        minimal_dimension,
    )

    GL.glClearColor(0.0289, 0.071875, 0.0972, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glDisable(GL.GL_SCISSOR_TEST)

    GL.glViewport(
        int(0.0 + (w - minimal_dimension) / 2.0),
        int(0.0 + (h - minimal_dimension) / 2.0),
        minimal_dimension,
        minimal_dimension,
    )


_quadric = GLU.gluNewQuadric()


def draw_sphere(radius: float) -> None:
    GLU.gluSphere(_quadric, radius, 24, 16)


x_rot: float = 0.3
y_rot: float = 0.0
camera_distance: float = 60.0

earth_orbit_angle: float = 0.0
moon_orbit_angle: float = 0.0


def handle_inputs() -> None:
    global x_rot, y_rot, camera_distance
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        y_rot += 0.03
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        y_rot -= 0.03
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        x_rot -= 0.03
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        x_rot += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_UP) == glfw.PRESS:
        camera_distance = max(15.0, camera_distance - 0.5)
    if glfw.get_key(window, glfw.KEY_PAGE_DOWN) == glfw.PRESS:
        camera_distance = min(200.0, camera_distance + 0.5)


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

    draw_in_square_viewport()
    handle_inputs()

    earth_orbit_angle += 1.0
    moon_orbit_angle += 12.0

    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(45.0, 1.0, 0.5, 500.0)

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GL.glTranslatef(0.0, 0.0, -camera_distance)
    GL.glRotatef(math.degrees(x_rot), 1.0, 0.0, 0.0)
    GL.glRotatef(math.degrees(y_rot), 0.0, 1.0, 0.0)

    # Sun -- world-space origin
    GL.glColor3f(1.0, 0.95, 0.2)
    draw_sphere(4.0)

    # Earth -- earth space relative to sun space
    GL.glPushMatrix()
    GL.glRotatef(earth_orbit_angle, 0.0, 1.0, 0.0)
    GL.glTranslatef(15.0, 0.0, 0.0)

    GL.glColor3f(0.2, 0.4, 1.0)
    draw_sphere(1.5)

    # Moon -- moon space relative to earth space.
    # Note: this push happens *while* the earth's rotate+translate
    # is still on the stack, so the moon inherits earth's frame.
    GL.glPushMatrix()
    GL.glRotatef(moon_orbit_angle, 0.0, 1.0, 0.0)
    GL.glTranslatef(3.5, 0.0, 0.0)
    GL.glColor3f(0.85, 0.85, 0.85)
    draw_sphere(0.5)
    GL.glPopMatrix()

    GL.glPopMatrix()

    glfw.swap_buffers(window)

glfw.terminate()
