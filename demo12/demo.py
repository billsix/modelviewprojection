#Copyright (c) 2018-2020 William Emerison Six
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.


# PURPOSE
#
# Rotate the square around it's origin.  Reading the modelspace to
# world space transformations should make this straightforward.
# Try reading them from the top down.  Does in make sense that way?
#
#
#

# |=======================================
# |Keyboard Input |Action
# |w              |Move Left Paddle Up
# |s              |Move Left Paddle Down
# |i              |Move Right Paddle Up
# |k              |Move Right Paddle Down
# |               |
# |d              |Increase Left Paddle's Rotation
# |a              |Decrease Left Paddle's Rotation
# |l              |Increase Right Paddle's Rotation
# |j              |Decrease Right Paddle's Rotation
# |               |
# |q              |Rotate the square around it's center
# |               |
# |UP             |Move the camera up, moving the objects down
# |DOWN           |Move the camera down, moving the objects up
# |LEFT           |Move the camera left, moving the objects right
# |RIGHT          |Move the camera right, moving the objects left
# |=======================================

import sys
import os
import numpy as np
import math
from OpenGL.GL import *
import glfw

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR,1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR,4)

window = glfw.create_window(500,
                            500,
                            "ModelViewProjection Demo 12",
                            None,
                            None)
if not window:
    glfw.terminate()
    sys.exit()

# Make the window's context current
glfw.make_context_current(window)

# Install a key handler
def on_key(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window,1)
glfw.set_key_callback(window, on_key)

glClearColor(0.0,
             0.0,
             0.0,
             1.0)


glMatrixMode(GL_PROJECTION);
glLoadIdentity();
glMatrixMode(GL_MODELVIEW);
glLoadIdentity();


def draw_in_square_viewport():
    # clear to gray.
    glClearColor(0.2, #r
                 0.2, #g
                 0.2, #b
                 1.0) #a
    glClear(GL_COLOR_BUFFER_BIT)

    width, height = glfw.get_framebuffer_size(window)
    # figure out the minimum dimension of the window
    min = width if width < height else height

    # per pixel than just it's current color.
    glEnable(GL_SCISSOR_TEST)
    glScissor(int((width - min)/2.0),  #min x
              int((height - min)/2.0), #min y
              min,                     #width x
              min)                     #width y

    glClearColor(0.0, #r
                 0.0, #g
                 0.0, #b
                 1.0) #a
    # gl clear will only update the square to black values.
    glClear(GL_COLOR_BUFFER_BIT)
    # disable the scissor test, so now any opengl calls will
    # happen as usual.
    glDisable(GL_SCISSOR_TEST)

    # But, we only want to draw within the black square.
    # We set the viewport, so that the NDC coordinates
    # will be mapped the the region of screen coordinates
    # that we care about, which is the black square.
    glViewport(int(0.0 + (width - min)/2.0),  #min x
               int(0.0 + (height - min)/2.0), #min y
               min,                           #width x
               min)                           #width y


class Vertex:
    def __init__(self,x,y):
        self.x = x
        self.y = y

    def translate(self, tx, ty):
        return Vertex(x=self.x + tx, y=self.y + ty)

    def scale(self, scale_x, scale_y):
        return Vertex(x=self.x * scale_x, y=self.y * scale_y)

    def rotate(self,angle_in_radians):
        return Vertex(x= self.x * math.cos(angle_in_radians) - self.y * math.sin(angle_in_radians),
                      y= self.x * math.sin(angle_in_radians) + self.y * math.cos(angle_in_radians))

class Paddle:
    def __init__(self,vertices, r, g, b, initial_position, rotation=0.0, input_offset_x=0.0, input_offset_y=0.0):
        self.vertices = vertices
        self.r = r
        self.g = g
        self.b = b
        self.rotation = rotation
        self.input_offset_x = input_offset_x
        self.input_offset_y = input_offset_y
        self.initial_position = initial_position


paddle1 = Paddle(vertices=[Vertex(x=-10.0, y=-30.0),
                           Vertex(x= 10.0, y=-30.0),
                           Vertex(x= 10.0, y=30.0),
                           Vertex(x=-10.0, y=30.0)],
                 r=0.578123,
                 g=0.0,
                 b=1.0,
                 initial_position=Vertex(-90.0,0.0))

paddle2 = Paddle(vertices=[Vertex(x=-10.0, y=-30.0),
                           Vertex(x= 10.0, y=-30.0),
                           Vertex(x= 10.0, y=30.0),
                           Vertex(x=-10.0, y=30.0)],
                 r=1.0,
                 g=0.0,
                 b=0.0,
                 initial_position=Vertex(90.0,0.0))
camera_x = 0.0
camera_y = 0.0

square = [Vertex(x=-5.0, y=-5.0),
          Vertex(x= 5.0, y=-5.0),
          Vertex(x= 5.0, y= 5.0),
          Vertex(x=-5.0, y= 5.0)]
square_rotation = 0.0


def handle_inputs():
    global square_rotation
    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square_rotation += 0.1

    global camera_x, camera_y

    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera_y += 10.0
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera_y -= 10.0
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera_x -= 10.0
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera_x += 10.0

    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.input_offset_y -= 10.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.input_offset_y += 10.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.input_offset_y -= 10.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.input_offset_y += 10.0

    global paddle_1_rotation, paddle_2_rotation

    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        paddle1.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        paddle1.rotation -= 0.1
    if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
        paddle2.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_L) == glfw.PRESS:
        paddle2.rotation -= 0.1

TARGET_FRAMERATE = 60 # fps

# to try to standardize on 60 fps, compare times between frames
time_at_beginning_of_previous_frame = glfw.get_time()

# Loop until the user closes the window
while not glfw.window_should_close(window):
    # poll the time to try to get a constant framerate
    while glfw.get_time() < time_at_beginning_of_previous_frame +  1.0/TARGET_FRAMERATE:
        pass
    # set for comparison on the next frame
    time_at_beginning_of_previous_frame = glfw.get_time()

    # Poll for and process events
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # render scene
    draw_in_square_viewport()
    handle_inputs()

    # draw paddle1
    glColor3f(paddle1.r,
              paddle1.g,
              paddle1.b)

    glBegin(GL_QUADS)
    for model_space in paddle1.vertices:
        world_space = model_space.rotate(paddle1.rotation) \
                                 .translate(tx=paddle1.initial_position.x,
                                            ty=paddle1.initial_position.y) \
                                 .translate(tx=paddle1.input_offset_x,
                                            ty=paddle1.input_offset_y)

        camera_space = world_space.translate(tx=-camera_x,
                                             ty=-camera_y)
        ndc_space = camera_space.scale(scale_x=1.0/100.0,
                                       scale_y=1.0/100.0)
        glVertex2f(ndc_space.x,
                   ndc_space.y)
    glEnd()

    # draw square
    glColor3f(0.0, #r
              0.0, #g
              1.0) #b
    glBegin(GL_QUADS)
    for model_space in square:
        paddle_1_space = model_space.rotate(square_rotation) \
                                    .translate(tx=20.0, ty=0.0)
        world_space = paddle_1_space.rotate(paddle1.rotation) \
                                    .translate(tx=paddle1.initial_position.x,
                                               ty=paddle1.initial_position.y) \
                                    .translate(tx=paddle1.input_offset_x,
                                               ty=paddle1.input_offset_y)
        camera_space = world_space.translate(tx=-camera_x,
                                             ty=-camera_y)
        ndc_space = camera_space.scale(scale_x=1.0/100.0,
                                       scale_y=1.0/100.0)
        glVertex2f(ndc_space.x,
                   ndc_space.y)
    glEnd()

    # draw paddle2
    glColor3f(paddle2.r,
              paddle2.g,
              paddle2.b)

    glBegin(GL_QUADS)
    for model_space in paddle2.vertices:
        world_space = model_space.rotate(paddle2.rotation) \
                                 .translate(tx=paddle2.initial_position.x,
                                            ty=paddle2.initial_position.y) \
                                 .translate(tx=paddle2.input_offset_x,
                                            ty=paddle2.input_offset_y)

        camera_space = world_space.translate(tx=-camera_x,
                                             ty=-camera_y)
        ndc_space = camera_space.scale(scale_x=1.0/100.0,
                                       scale_y=1.0/100.0)
        glVertex2f(ndc_space.x,
                   ndc_space.y)
    glEnd()

    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)

glfw.terminate()
