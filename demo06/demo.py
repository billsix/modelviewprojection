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
# Learn about modelspace.



# == Model-space

# |=======================================
# |Keyboard Input |Action
# |w              |Move Left Paddle Up
# |s              |Move Left Paddle Down
# |k              |Move Right Paddle Up
# |i              |Move Right Paddle Down
# |=======================================

# Normalized-device-coordinates are not a natural system of
# numbers for use by humans.  Imagine that the paddles in the previous
# chapters exist in real life, and are 20 meters wide and 60 meters tall.
# The graphics programmer should be able to use those numbers directly;
# they shouldn't have to manually transform the distances into normalized-device-coordinates.

# Whatever a convenient numbering system is (i.e. coordinate system) for modeling objects
# is called "model-space".  Since a paddle has four corners, which corner should be a
# the origin (0,0)?  If you don't already know what you want at the origin, then
# none of the corners should be; instead put the center of the object
# at the origin (By putting the center of the object at the origin,
# scaling and rotating the object are trivial).

# eog ../images/modelspace.png

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
                            "ModelViewProjection Demo 6",
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

    # NEW!
    def scale(self, x, y):
        return Vertex(x=self.x * x, y=self.y * y)


class Paddle:
    def __init__(self,vertices, r, g, b, global_position, offset_x=0.0, offset_y=0.0):
        self.vertices = vertices
        self.r = r
        self.g = g
        self.b = b
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.global_position = global_position
        # global position is probably poorly named.
        # it's the initial position for use if no inputs
        # are inputs, and the offset x and y are the aggregate
        # of the user's input.

# NEW! paddles are using modelspace coordinates instead of NDC
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

        # Model-space to World-space.

        # You can view the transformations from first transformation to last,
        # where all transformations happen relative to the world-space origin.
        # (this works well for world-space to camera-space,
        # but not so well for model-space transformations)
        # eog ../images/translationF.gif
        # eog ../images/translation2F.gif

        # Instead, for model-space to world-space transformations (and for these transformations only),
        # it's easier to read the transformations backwards, where the transformations
        # aren't relative to the global origin, instead it's from the local frame of reference.

        # When reading the transformations backwards, I think it's best to think of it
        # as moving the axises, and the plotting the data once the axies are in
        # their final place.

        # eog ../images/translationB.gif
        # eog ../images/translation2B.gif



        # Why do the two different views of the transformations matter?  In model-space
        # to world-space transformations, especially once rotation and scaling of model-space
        # is used, it allows the programmer to forget about most details, just specify
        # where new objects are relative to that which you are already drawing.

        # With that said, that doesn't mean that reading the transformations front to back
        # has no value.

        # This will make more sense once rotation is involved.
        world_space = model_space.translate(tx=paddle1.global_position.x,
                                            ty=paddle1.global_position.y) \
                                 .translate(tx=paddle1.offset_x,
                                            ty=paddle1.offset_y)

        # === Scaling

        # eog ../images/scale.png


        # Similarly, we can expand or shrink the size of an object
        # by "scale"ing each of the vertices of the object, assuming
        # the object's center is at (0,0).

        ndc_space = world_space.scale(x=1.0/100.0,
                                    y=1.0/100.0)
        glVertex2f(ndc_space.x,
                   ndc_space.y)
    glEnd()

    # draw paddle2
    glColor3f(paddle2.r,
              paddle2.g,
              paddle2.b)

    glBegin(GL_QUADS)
    for model_space in paddle2.vertices:

        # Do the same transformations to the second paddle

        world_space = model_space.translate(tx=paddle2.global_position.x,
                                            ty=paddle2.global_position.y) \
                                 .translate(tx=paddle2.offset_x,
                                            ty=paddle2.offset_y)

        ndc_space = world_space.scale(x=1.0/100.0,
                                      y=1.0/100.0)
        glVertex2f(ndc_space.x,
                   ndc_space.y)
    glEnd()


    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)

glfw.terminate()
