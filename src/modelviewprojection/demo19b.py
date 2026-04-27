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

# Demo 19b -- Atom (nucleus + orbiting electrons).
# Ported from OpenGL SuperBible 4e, chapter 4 example "atom".
#
# This is the simplest demo of nested coordinate frames:  each electron
# is drawn in its own coordinate system, obtained from world space by
# (rotate around y) then (translate out along x).  Different orbits use
# different axes of revolution to show that nesting transforms is not
# special-cased to one axis.
#
# Watch what happens if you swap the order of glRotatef and glTranslatef
# below -- you will get a sphere translated and then spun in place,
# instead of a sphere put on an orbit.  Order of composition matters.
#
# Controls:  arrow keys yaw/pitch the world; PageUp/PageDown move the
# camera in/out.

import math
import os
import sys

import glfw
import OpenGL.GL as GL
import OpenGL.GLU as GLU

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(
    500, 500, "ModelViewProjection Demo 19b -- Atom", None, None
)
if not window:
    glfw.terminate()
    sys.exit()

glfw.make_context_current(window)


def on_key(win, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(win, 1)


glfw.set_key_callback(window, on_key)

GL.glClearColor(0.0289, 0.071875, 0.0972, 1.0)

GL.glEnable(GL.GL_DEPTH_TEST)
GL.glClearDepth(1.0)
GL.glDepthFunc(GL.GL_LEQUAL)
# wireframe so the spheres' 3D structure is visible without lighting
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
    GLU.gluSphere(_quadric, radius, 18, 12)


x_rot: float = 0.3
y_rot: float = 0.0
camera_distance: float = 25.0

electron_1_angle: float = 0.0
electron_2_angle: float = 0.0
electron_3_angle: float = 0.0


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
        camera_distance = max(8.0, camera_distance - 0.2)
    if glfw.get_key(window, glfw.KEY_PAGE_DOWN) == glfw.PRESS:
        camera_distance = min(80.0, camera_distance + 0.2)


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

    electron_1_angle += 6.0
    electron_2_angle += 4.0
    electron_3_angle += 8.0

    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(45.0, 1.0, 0.1, 200.0)

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()

    # camera:  pull the scene back, then yaw/pitch the world
    GL.glTranslatef(0.0, 0.0, -camera_distance)
    GL.glRotatef(math.degrees(x_rot), 1.0, 0.0, 0.0)
    GL.glRotatef(math.degrees(y_rot), 0.0, 1.0, 0.0)

    # red nucleus at the origin
    GL.glColor3f(1.0, 0.2, 0.2)
    draw_sphere(2.0)

    # First electron orbit -- around y, in the xz plane.
    # Each "with" of glPushMatrix/glPopMatrix creates a fresh
    # coordinate system to draw the electron in, then throws it away
    # so the next orbit is unaffected.
    GL.glColor3f(1.0, 1.0, 0.2)
    GL.glPushMatrix()
    GL.glRotatef(electron_1_angle, 0.0, 1.0, 0.0)
    GL.glTranslatef(7.0, 0.0, 0.0)
    draw_sphere(0.6)
    GL.glPopMatrix()

    # Second electron orbit -- around x, tilted into the yz plane
    GL.glColor3f(0.2, 1.0, 0.6)
    GL.glPushMatrix()
    GL.glRotatef(electron_2_angle, 1.0, 0.0, 0.0)
    GL.glTranslatef(0.0, 9.0, 0.0)
    draw_sphere(0.6)
    GL.glPopMatrix()

    # Third electron orbit -- around an oblique axis
    GL.glColor3f(0.4, 0.6, 1.0)
    GL.glPushMatrix()
    GL.glRotatef(electron_3_angle, 1.0, 1.0, 0.0)
    GL.glTranslatef(5.5, 0.0, 0.0)
    draw_sphere(0.6)
    GL.glPopMatrix()

    glfw.swap_buffers(window)

glfw.terminate()
