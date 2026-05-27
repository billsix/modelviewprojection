
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
# Controls:  arrow keys yaw/pitch the world; PageUp/PageDown move the
# camera in/out.

import math
import sys

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU

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


def draw_solid_cylinder(
    base_radius: float, top_radius: float, height: float, slices: int
) -> None:
    """Cylinder side surface, oriented along +Z (replacement for gluCylinder)."""
    GL.glBegin(GL.GL_QUAD_STRIP)
    for i in range(slices + 1):
        a = 2.0 * math.pi * float(i) / slices
        c, s = math.cos(a), math.sin(a)
        GL.glNormal3f(c, s, 0.0)
        GL.glVertex3f(c * base_radius, s * base_radius, 0.0)
        GL.glVertex3f(c * top_radius, s * top_radius, height)
    GL.glEnd()


def draw_solid_cone(base: float, height: float, slices: int) -> None:
    """Cone with apex on +Z and base disk closing the bottom."""
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glNormal3f(0.0, 0.0, 1.0)
    GL.glVertex3f(0.0, 0.0, height)
    for i in range(slices + 1):
        a = 2.0 * math.pi * float(i) / slices
        GL.glVertex3f(math.cos(a) * base, math.sin(a) * base, 0.0)
    GL.glEnd()
    # Base disk
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glNormal3f(0.0, 0.0, -1.0)
    GL.glVertex3f(0.0, 0.0, 0.0)
    for i in range(slices, -1, -1):
        a = 2.0 * math.pi * float(i) / slices
        GL.glVertex3f(math.cos(a) * base, math.sin(a) * base, 0.0)
    GL.glEnd()


def draw_solid_sphere(radius: float, slices: int, stacks: int) -> None:
    """Solid sphere centered at the origin -- a white ball marking the origin,
    like the gluSphere call at the end of gltDrawUnitAxes.  Emits (lat1, lat0)
    per slice so the outward face winds CCW under the default
    glFrontFace(GL_CCW)."""
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


# doc-region-begin draw unit axes
def draw_unit_axes() -> None:
    """
    Draw a unit-length basis at the current origin of the modelview matrix:
    +X red, +Y green, +Z blue.  Each axis is a thin cylinder shaft with a
    cone arrowhead at the tip (port of gltDrawUnitAxes from the OpenGL
    SuperBible's gltools).  Call this anywhere inside a glPushMatrix /
    glPopMatrix block to visualize the current coordinate frame.
    """
    rod_radius = 0.05
    cone_radius = 0.12
    rod_length = 0.85
    cone_length = 0.15

    # +X axis -- red, rotate +90° about Y so the +Z-aligned cylinder
    # points along +X
    GL.glColor3f(1.0, 0.0, 0.0)
    GL.glPushMatrix()
    GL.glRotatef(90.0, 0.0, 1.0, 0.0)
    draw_solid_cylinder(rod_radius, rod_radius, rod_length, 20)
    GL.glTranslatef(0.0, 0.0, rod_length)
    draw_solid_cone(cone_radius, cone_length, 20)
    GL.glPopMatrix()

    # +Y axis -- green, rotate -90° about X so the cylinder points along +Y
    GL.glColor3f(0.0, 1.0, 0.0)
    GL.glPushMatrix()
    GL.glRotatef(-90.0, 1.0, 0.0, 0.0)
    draw_solid_cylinder(rod_radius, rod_radius, rod_length, 20)
    GL.glTranslatef(0.0, 0.0, rod_length)
    draw_solid_cone(cone_radius, cone_length, 20)
    GL.glPopMatrix()

    # +Z axis -- blue, default cylinder orientation
    GL.glColor3f(0.0, 0.0, 1.0)
    GL.glPushMatrix()
    draw_solid_cylinder(rod_radius, rod_radius, rod_length, 20)
    GL.glTranslatef(0.0, 0.0, rod_length)
    draw_solid_cone(cone_radius, cone_length, 20)
    GL.glPopMatrix()

    # White ball at the origin -- gltDrawUnitAxes finished with a small
    # gluSphere.  Our rod_radius is 0.05 (vs the SuperBible's 0.025), so use
    # radius 0.10 to keep the same ~2x-rod proportion (otherwise the sphere
    # disappears into the axis shafts).
    GL.glColor3f(1.0, 1.0, 1.0)
    draw_solid_sphere(0.10, 15, 15)
# doc-region-end draw unit axes


x_rot: float = 0.3
y_rot: float = 0.5
camera_distance: float = 5.0


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
        camera_distance = max(2.0, camera_distance - 0.1)
    if glfw.get_key(window, glfw.KEY_PAGE_DOWN) == glfw.PRESS:
        camera_distance = min(40.0, camera_distance + 0.1)


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
    # camera transform:  pull the world toward us along -z
    GL.glTranslatef(0.0, 0.0, -camera_distance)
    # spin the world so the axes are easy to see in 3D
    GL.glRotatef(math.degrees(x_rot), 1.0, 0.0, 0.0)
    GL.glRotatef(math.degrees(y_rot), 0.0, 1.0, 0.0)

    draw_unit_axes()

    glfw.swap_buffers(window)

glfw.terminate()
