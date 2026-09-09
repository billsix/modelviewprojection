# Copyright (c) 2018-2026 William Emerison Six
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Assignment 2 -- Screen space.
#
# This is demo11's scene and demo11's transformations, with the last step of
# the pipeline taken out.  Your job is to put it back.
#
# The demos hand OpenGL coordinates in NDC -- x and y both between -1 and 1 --
# and let glViewport stretch that square onto the window.  Here the projection
# is set up differently, with gluOrtho2D(0, width, 0, height), so OpenGL is
# expecting SCREEN coordinates: x between 0 and the window width, y between 0
# and the window height, measured in pixels.  Something has to convert one to
# the other, and that something is the two functions below.
#
# RUN IT FIRST AND EXPECT AN EMPTY WINDOW.  That is correct, not a bug: the
# two functions currently hand back the NDC vector unchanged, so every vertex
# lands within one pixel of the bottom-left corner.  The paddles appear once
# you write the mapping.
#
#   * ndc_to_screenspace_full_screen -- stretch the NDC square over the WHOLE
#     window.  Simplest, and the paddles will look squashed or stretched when
#     the window is not square.
#   * ndc_to_screenspace_aspect_not_distorted -- keep the paddles' proportions
#     no matter how the window is resized, by using the same scale on both
#     axes -- the smaller of width and height is the one that fits -- and
#     centering the result.
#
# Set KEEP_ASPECT_RATIO to choose which one runs, write both, and resize the
# window to see the difference.
#
# The controls are demo11's: W/S and I/K move the paddles, A/D and J/L rotate
# them, the arrow keys move the camera.


import dataclasses
import sys
import typing

import glfw
import OpenGL.GL as GL
from gacalc.g2 import Vector, e_1, e_2
from gacalc.transforms import (
    InvertibleFunction,
    compose,
    inverse,
    translate,
    uniform_scale,
)
from OpenGL.GLU import gluOrtho2D

import modelviewprojection.util.colorutils as colorutils
from modelviewprojection.mathutils import rotate
from modelviewprojection.util.windowing import on_key

# Which of the two mappings the event loop uses.  Flip it and rerun.
KEEP_ASPECT_RATIO: bool = False

zero: Vector = Vector.zero()

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(
    500, 500, "ModelViewProjection Assignment 2 - Screen Space", None, None
)
if not window:
    glfw.terminate()
    sys.exit()

glfw.make_context_current(window)


glfw.set_key_callback(window, on_key)

GL.glClearColor(0.0289, 0.071875, 0.0972, 1.0)


# doc-region-begin ndc to screenspace full screen
def ndc_to_screenspace_full_screen(
    ndc: Vector, width: float, height: float
) -> Vector:
    """Map the NDC square onto the whole window.

    ``ndc`` has both coordinates in [-1, 1]; the result should have x in
    [0, width] and y in [0, height], so that the NDC square covers every
    pixel.  Resizing the window to a non-square shape will distort the
    paddles -- that is this mapping's honest behaviour, and the reason the
    other one below exists.
    """
    # TODO -- remove the `return ndc`, and map NDC onto the full window.
    return ndc


# doc-region-end ndc to screenspace full screen


# doc-region-begin ndc to screenspace aspect not distorted
def ndc_to_screenspace_aspect_not_distorted(
    ndc: Vector, width: float, height: float
) -> Vector:
    """Map the NDC square onto the window without distorting it.

    Same idea as above, but the paddles must keep their proportions at any
    window shape.  Scale both axes by the same amount -- the window's smaller
    dimension is the one that fits -- and center what is left over, so the
    NDC square lands as a square in the middle of the window.
    """
    # TODO -- remove the `return ndc`, and map NDC on without distorting it.
    return ndc


# doc-region-end ndc to screenspace aspect not distorted


@dataclasses.dataclass
class Paddle:
    vertices: list[Vector]
    color: colorutils.Color3
    position: Vector
    rotation: float = 0.0


paddle1: Paddle = Paddle(
    vertices=[
        -1 * e_1 + -3 * e_2,
        e_1 + -3 * e_2,
        e_1 + 3 * e_2,
        -1 * e_1 + 3 * e_2,
    ],
    color=colorutils.Color3(r=0.578123, g=0.0, b=1.0),
    position=-9 * e_1,
)

paddle2: Paddle = Paddle(
    vertices=[
        -1 * e_1 + -3 * e_2,
        e_1 + -3 * e_2,
        e_1 + 3 * e_2,
        -1 * e_1 + 3 * e_2,
    ],
    color=colorutils.Color3(r=1.0, g=1.0, b=0.0),
    position=9 * e_1,
)


@dataclasses.dataclass
class Camera:
    position_ws: Vector = dataclasses.field(default_factory=lambda: zero)


camera: Camera = Camera()


def handle_inputs() -> None:
    global camera

    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera.position_ws += e_2
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.position_ws -= e_2
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.position_ws -= e_1
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.position_ws += e_1

    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.position -= e_2
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.position += e_2
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.position -= e_2
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.position += e_2

    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        paddle1.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        paddle1.rotation -= 0.1
    if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
        paddle2.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_L) == glfw.PRESS:
        paddle2.rotation -= 0.1


def modelspace_to_ndc(paddle: Paddle) -> InvertibleFunction[Vector]:
    """demo11's pipeline: model space -> world -> camera -> NDC."""
    return compose(
        [
            # camera space to NDC
            uniform_scale(m=1.0 / 10.0),
            # world space to camera space
            inverse(translate(b=camera.position_ws)),
            # model space to world space
            compose(
                [
                    translate(b=paddle.position),
                    rotate(paddle.rotation),
                ]
            ),
        ]
    )


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
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)  # ty: ignore

    # Unlike the demos, this program hands OpenGL SCREEN coordinates, so the
    # projection covers the window in pixels rather than the NDC square.
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    gluOrtho2D(0.0, float(width), 0.0, float(height))

    handle_inputs()

    ndc_to_screenspace: typing.Callable[[Vector, float, float], Vector] = (
        ndc_to_screenspace_aspect_not_distorted
        if KEEP_ASPECT_RATIO
        else ndc_to_screenspace_full_screen
    )

    for paddle in (paddle1, paddle2):
        GL.glColor3f(*paddle.color)
        GL.glBegin(GL.GL_QUADS)
        ms_to_ndc: InvertibleFunction[Vector] = modelspace_to_ndc(paddle)
        for v_ms in paddle.vertices:
            GL.glVertex2f(*ndc_to_screenspace(ms_to_ndc(v_ms), width, height))
        GL.glEnd()

    glfw.swap_buffers(window)

glfw.terminate()
