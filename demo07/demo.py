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
# Learn about rotations, and the order in which to read
# a sequence of transformations.  This demo does not
# work correctly, because of a misunderstanding
# of how rotations work.

# == Rotate the Paddles About their Center

# [width="75%",options="header,footer"]
# |=======================================
# |Keyboard Input |Action
# |w              |Move Left Paddle Up
# |s              |Move Left Paddle Down
# |i              |Move Right Paddle Up
# |k              |Move Right Paddle Down
# |               |
# |*d*              |*Increase Left Paddle's Rotation*
# |*a*              |*Decrease Left Paddle's Rotation*
# |*l*              |*Increase Right Paddle's Rotation*
# |*j*              |*Decrease Right Paddle's Rotation*
# |=======================================



# === Rotation Around Origin (0,0)

# We can also rotate an object around (0,0) by rotating
# all of the object's vertices around (0,0).

# In high school math, you will have learned about sin, cos, and tangent.
# Typically the angles are described on the unit circle, where a rotation
# starts from the positive x axis.  We can expand on this knowledge, allowing
# us to rotate a given vertex around the origin (0,0).  This is done
# by separating the x and y value, rotating each of them seperately,
# and then adding the results together.

# That might not have been fully clear.  Let me try again.
# The vertex (0.5,0.4) can be separated into two vertices, (0.5,0) and (0,0.4).

# eog ../images/rotate3.png

# eog ../images/rotate4.png

# These vertices can be added together to create the original vertex.
# But, before we do that, let's rotate each of the vertices.

# (0.5,0) is on the x-axis, so rotating it by "angle" degrees, results
# in vertex (0.5*cos(angle), 0.5*sin(angle)).  Notice that both the x and
# y values are multiplied by 0.5.  This is because rotations should not affect
# the distance of the point from the origin (0,0).  (0.5,0) has length 0.5.
# (cos(angle), sin(angle) has length 1. By multipling both the x and y
# component by 0.5, we are scaling the vertex back to its original distance
# from the origin.

# eog ../images/rotate.png

# (0,0.4) is on the y-axis, so rotating it by "angle" degrees, results
# in vertex (0.4*-sin(angle), 0.4*cos(angle)).

# eog ../images/rotate2.png

# Wait.  Why is negative sin applied to the angle to make the x value,
# and cos applied to angle to make the y value?
# Trigonometric operations such as sin, cos, and tangent assume that the rotation is happening on
# the unit circle, starting from (1,0) on the x axis.  Since we want
# to rotate an angle starting from (0,1) on the y axis, sin and
# cos must be swapped.  Sin is positive from 0 to 90 degrees, but
# we want a negative value for our rotation of the y axis since the rotation is happening counter-clockwise,
# hence the negative sin.



# After the rotations have been applied, sum the results to
# get your vertex rotated around the origin!

# (0.5*cos(angle), 0.5*sin(angle)) + (0.4*-sin(angle), 0.4*cos(angle)) =
# (0.5*cos(angle) + 0.4*-sin(angle), 0.5*sin(angle) + 0.4*cos(angle))

# I prefer to think graphically instead of symbolically.
# Another way you can think of this is to rotate the the x axis
# and y axis, create graph paper (tick marks) along those new
# axis, and then draw the geometry on that new "basis",
# instead of the natural basis. (Natural basis just means
# the normal x and y axis).
# Think of basis as an origin, a unit in various directions,
# a graph paper lines drawn.  Then your geometry is drawn
# in that space.




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
                            "ModelViewProjection Demo 7",
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

    glClearColor(0.2, #r
                 0.2, #g
                 0.2, #b
                 1.0) #a
    glClear(GL_COLOR_BUFFER_BIT)

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    min = width if width < height else height

    glViewport(int(0.0 + (width - min)/2.0),  #min x
               int(0.0 + (height - min)/2.0), #min y
               min,                           #width x
               min)                           #width y

    glEnable(GL_SCISSOR_TEST)
    glScissor(int(0.0 + (width - min)/2.0),  #min x
              int(0.0 + (height - min)/2.0), #min y
              min,                           #width x
              min)                           #width y

    glClearColor(0.0, #r
                 0.0, #g
                 0.0, #b
                 1.0) #a
    glClear(GL_COLOR_BUFFER_BIT)
    glDisable(GL_SCISSOR_TEST)



class Vertex:
    def __init__(self,x,y):
        self.x = x
        self.y = y

    def translate(self, tx, ty):
        return Vertex(x=self.x + tx, y=self.y + ty)

    def scale(self, scale_x, scale_y):
        return Vertex(x=self.x * scale_x, y=self.y * scale_y)

    # NEW
    # definition of rotate, from the description above
    # cos and sin are defined in the math module.
    #
    # Question - how can you determine if math.cos and math.sin
    # are defined in terms of radians or in terms of degrees?
    def rotate(self,angle_in_radians):
        return Vertex(x= self.x * math.cos(angle_in_radians) - self.y * math.sin(angle_in_radians),
                      y= self.x * math.sin(angle_in_radians) + self.y * math.cos(angle_in_radians))

class Paddle:
    # NEW
    # a rotation instance variable is defined, with a default value of 0
    def __init__(self,vertices, r, g, b, global_position, rotation=0.0, offset_x=0.0, offset_y=0.0):
        self.vertices = vertices
        self.r = r
        self.g = g
        self.b = b
        self.rotation = rotation
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.global_position = global_position



paddle1 = Paddle(vertices=[Vertex(x=-10.0, y=-30.0),
                           Vertex(x= 10.0, y=-30.0),
                           Vertex(x= 10.0, y=30.0),
                           Vertex(x=-10.0, y=30.0)],
                 r=0.578123,
                 g=0.0,
                 b=1.0,
                 global_position=Vertex(-90.0,0.0))

paddle2 = Paddle(vertices=[Vertex(x=-10.0, y=-30.0),
                           Vertex(x= 10.0, y=-30.0),
                           Vertex(x= 10.0, y=30.0),
                           Vertex(x=-10.0, y=30.0)],
                 r=1.0,
                 g=0.0,
                 b=0.0,
                 global_position=Vertex(90.0,0.0))


def handle_movement_of_paddles():
    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.offset_y -= 10.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.offset_y += 10.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.offset_y -= 10.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.offset_y += 10.0

    global paddle_1_rotation, paddle_2_rotation

    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        paddle1.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        paddle1.rotation -= 0.1
    if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
        paddle2.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_L) == glfw.PRESS:
        paddle2.rotation -= 0.1


# Loop until the user closes the window
while not glfw.window_should_close(window):
    # Poll for and process events
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # render scene
    draw_in_square_viewport()
    handle_movement_of_paddles()

    # draw paddle1
    glColor3f(paddle1.r,
              paddle1.g,
              paddle1.b)

    glBegin(GL_QUADS)
    for model_space in paddle1.vertices:
        world_space = model_space.translate(tx=paddle1.global_position.x,
                                            ty=paddle1.global_position.y) \
                                 .translate(tx=paddle1.offset_x,
                                            ty=paddle1.offset_y) \
                                 .rotate(paddle1.rotation)
        ndc_space = world_space.scale(scale_x=1.0/100.0,
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
        world_space = model_space.translate(tx=paddle2.global_position.x,
                                            ty=paddle2.global_position.y) \
                                 .translate(tx=paddle2.offset_x,
                                            ty=paddle2.offset_y) \
                                 .rotate(paddle2.rotation)
        ndc_space = world_space.scale(scale_x=1.0/100.0,
                                      scale_y=1.0/100.0)
        glVertex2f(ndc_space.x,
                   ndc_space.y)
    glEnd()


    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)

glfw.terminate()
