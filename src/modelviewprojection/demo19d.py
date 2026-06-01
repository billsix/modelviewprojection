
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

# Demo 19d -- Multi-planet system with moons.
# Ported from OpenGL SuperBible 4e, chapter 12 example "moons" (the
# hierarchy parts only -- this port omits the picking/selection code,
# which is a separate topic).
#
# This demo shows a *branching* hierarchy:  several planets each carry
# their own little system of moons.  Without a matrix stack you would
# have to invert each planet's transform before drawing the next one,
# which is exactly what glPushMatrix/glPopMatrix saves you from.
#
# Try removing one of the inner glPopMatrix calls -- the next planet
# will inherit the previous one's leftover transform and end up in the
# wrong place.
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

from modelviewprojection.cameracontrols import walk_around_camera
from modelviewprojection.clipping import draw_in_square_viewport
from modelviewprojection.windowing import on_key

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(
    500, 500, "ModelViewProjection Demo 19d -- Moons", None, None
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


_quadric = GLU.gluNewQuadric()


def draw_sphere(radius: float) -> None:
    GLU.gluSphere(_quadric, radius, 20, 14)


@dataclasses.dataclass
class Camera:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rot_y: float = 0.0
    rot_x: float = 0.0


camera: Camera = Camera(z=90.0)

clock: float = 0.0


def handle_inputs() -> None:
    walk_around_camera(window, camera, move_step=3.0)


# Each planet:  (color, orbit_radius, orbit_speed, planet_radius, moons)
# Each moon:    (color, orbit_radius, orbit_speed, moon_radius)
PLANETS = [
    (
        (0.6, 0.9, 1.0),  # mercury-ish
        12.0,
        2.0,
        1.2,
        [],
    ),
    (
        (0.2, 0.4, 1.0),  # earth
        22.0,
        1.0,
        2.5,
        [
            ((0.85, 0.85, 0.85), 5.0, 6.0, 0.6),
        ],
    ),
    (
        (1.0, 0.3, 0.2),  # mars
        34.0,
        0.7,
        2.0,
        [
            ((0.7, 0.7, 0.7), 4.0, 8.0, 0.4),
            ((0.7, 0.7, 0.7), 6.5, 4.0, 0.5),
        ],
    ),
    (
        (1.0, 0.7, 0.3),  # jupiter
        50.0,
        0.4,
        4.0,
        [
            ((0.85, 0.85, 0.85), 7.0, 5.0, 0.7),
            ((0.85, 0.85, 0.85), 9.5, 3.0, 0.6),
            ((0.85, 0.85, 0.85), 12.0, 2.0, 0.8),
        ],
    ),
]


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

    clock += 1.0 / 60.0

    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(45.0, 1.0, 0.5, 800.0)

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    # Walk-around camera:  rotate the world opposite the camera's heading,
    # then translate so the camera sits at origin in its own space.
    GL.glRotatef(math.degrees(-camera.rot_x), 1.0, 0.0, 0.0)
    GL.glRotatef(math.degrees(-camera.rot_y), 0.0, 1.0, 0.0)
    GL.glTranslatef(-camera.x, -camera.y, -camera.z)

    # Sun
    GL.glColor3f(1.0, 0.95, 0.2)
    draw_sphere(5.0)

    # Each planet draws inside its own push/pop, independently of its
    # siblings.  Each moon draws inside its planet's push/pop, so its
    # frame inherits the planet's orbital position.
    for planet_color, p_radius, p_speed, p_size, moons in PLANETS:
        GL.glPushMatrix()
        GL.glRotatef(math.degrees(clock * p_speed), 0.0, 1.0, 0.0)
        GL.glTranslatef(p_radius, 0.0, 0.0)

        GL.glColor3f(*planet_color)
        draw_sphere(p_size)

        for moon_color, m_radius, m_speed, m_size in moons:
            GL.glPushMatrix()
            GL.glRotatef(math.degrees(clock * m_speed), 0.0, 1.0, 0.0)
            GL.glTranslatef(m_radius, 0.0, 0.0)
            GL.glColor3f(*moon_color)
            draw_sphere(m_size)
            GL.glPopMatrix()

        GL.glPopMatrix()

    glfw.swap_buffers(window)

glfw.terminate()
