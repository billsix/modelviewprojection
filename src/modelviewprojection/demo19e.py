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

# Demo 19e -- Sphereworld:  an FPS camera flying through a populated
# world.  Ported from OpenGL SuperBible 4e, chapter 4 example
# "sphereworld".
#
# This is what the FPS-style camera from demos 17-19 was *for*.  The
# scene is just a ground grid, a field of randomly placed actor
# spheres, and a small composite gizmo at the origin (a torus with one
# orbiting moon) so you have a visible reference point as you fly.
#
# Controls:  LEFT/RIGHT yaw, PAGE_UP/PAGE_DOWN pitch, UP/DOWN walk
# forward/back -- standard walk-around camera shared with the other
# 3D demos.  ESC quits.

import dataclasses
import math
import random
import sys

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU

from modelviewprojection.cameracontrols import walk_around_camera
from modelviewprojection.windowing import on_key

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(
    500, 500, "ModelViewProjection Demo 19e -- Sphereworld", None, None
)
if not window:
    glfw.terminate()
    sys.exit()

glfw.make_context_current(window)


glfw.set_key_callback(window, on_key)

GL.glClearColor(0.0, 0.0, 0.20, 1.0)

GL.glEnable(GL.GL_DEPTH_TEST)
GL.glClearDepth(1.0)
GL.glDepthFunc(GL.GL_LEQUAL)
# wireframe everything -- mirrors the SuperBible original
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

    GL.glClearColor(0.0, 0.0, 0.20, 1.0)
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
    GLU.gluSphere(_quadric, radius, 14, 10)


def draw_ground() -> None:
    extent: float = 20.0
    step: float = 1.0
    y: float = -0.4
    GL.glColor3f(0.4, 0.4, 0.4)
    GL.glBegin(GL.GL_LINES)
    line: float = -extent
    while line <= extent + 1e-6:
        # lines parallel to z
        GL.glVertex3f(line, y, extent)
        GL.glVertex3f(line, y, -extent)
        # lines parallel to x
        GL.glVertex3f(extent, y, line)
        GL.glVertex3f(-extent, y, line)
        line += step
    GL.glEnd()


@dataclasses.dataclass
class Actor:
    x: float
    y: float
    z: float


NUM_SPHERES: int = 30
random.seed(1234)
actors: list[Actor] = [
    Actor(
        x=random.uniform(-18.0, 18.0),
        y=0.0,
        z=random.uniform(-18.0, 18.0),
    )
    for _ in range(NUM_SPHERES)
]


@dataclasses.dataclass
class Camera:
    x: float = 0.0
    y: float = 0.0
    z: float = 6.0
    rot_y: float = 0.0
    rot_x: float = 0.0


camera: Camera = Camera()


def handle_inputs() -> None:
    walk_around_camera(window, camera, move_step=0.15)


y_rot: float = 0.0

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

    y_rot += 0.5

    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(35.0, 1.0, 1.0, 100.0)

    # camera transform -- inverse of where the camera "is".
    # Apply rotations first (so the world counter-rotates around us),
    # then translate the world by -camera.position.  This matches
    # demo19's structure exactly.
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GL.glRotatef(math.degrees(-camera.rot_x), 1.0, 0.0, 0.0)
    GL.glRotatef(math.degrees(-camera.rot_y), 0.0, 1.0, 0.0)
    GL.glTranslatef(-camera.x, -camera.y, -camera.z)

    draw_ground()

    # Field of actor spheres, each in its own pushed coordinate system.
    GL.glColor3f(0.7, 0.9, 1.0)
    for a in actors:
        GL.glPushMatrix()
        GL.glTranslatef(a.x, a.y, a.z)
        draw_sphere(0.2)
        GL.glPopMatrix()

    # Centerpiece:  a torus with a small moon orbiting it, two units
    # in front of the world origin.
    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, -2.5)

    # The moon orbits the centerpiece, not the world
    GL.glPushMatrix()
    GL.glRotatef(-y_rot * 2.0, 0.0, 1.0, 0.0)
    GL.glTranslatef(1.0, 0.0, 0.0)
    GL.glColor3f(1.0, 0.6, 0.2)
    draw_sphere(0.1)
    GL.glPopMatrix()

    # Spinning torus body.  GLU has no torus, so build one as a ring
    # of small spheres -- enough to see the orbit clearly in wireframe.
    GL.glRotatef(y_rot, 0.0, 1.0, 0.0)
    GL.glColor3f(1.0, 1.0, 0.4)
    n_segments: int = 28
    for i in range(n_segments):
        theta: float = 2.0 * math.pi * i / n_segments
        GL.glPushMatrix()
        GL.glRotatef(math.degrees(theta), 0.0, 1.0, 0.0)
        GL.glTranslatef(0.5, 0.0, 0.0)
        draw_sphere(0.07)
        GL.glPopMatrix()

    GL.glPopMatrix()

    glfw.swap_buffers(window)

glfw.terminate()
