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
# |i              |Move Right Paddle Up
# |k              |Move Right Paddle Down
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
# at the origin (Because by putting the center of the object at the origin,
# scaling and rotating the object are trivial).

# eog ../images/modelspace.png

# Modelspace - the coordinate system (origin plus axis), in which some object's
# geometry is defined.

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
    min = width if width < height else height

    glEnable(GL_SCISSOR_TEST)
    glScissor(int((width - min)/2.0),  #min x
              int((height - min)/2.0), #min y
              min,                     #width x
              min)                     #width y

    glClearColor(0.0, #r
                 0.0, #g
                 0.0, #b
                 1.0) #a
    glClear(GL_COLOR_BUFFER_BIT)
    glDisable(GL_SCISSOR_TEST)

    glViewport(int(0.0 + (width - min)/2.0),  #min x
               int(0.0 + (height - min)/2.0), #min y
               min,                           #width x
               min)                           #width y



class Vertex:
    def __init__(self,x,y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Vertex(x={repr(self.x)},y={repr(self.y)})"

    def translate(self, tx, ty):
        return Vertex(x=self.x + tx, y=self.y + ty)

    # NEW!
    def scale(self, scale_x, scale_y):
        return Vertex(x=self.x * scale_x, y=self.y * scale_y)


class Paddle:
    def __init__(self,vertices, r, g, b, initial_position, input_offset_x=0.0, input_offset_y=0.0):
        self.vertices = vertices
        self.r = r
        self.g = g
        self.b = b
        self.input_offset_x = input_offset_x
        self.input_offset_y = input_offset_y
        self.initial_position = initial_position
        # global position is probably poorly named.
        # it's the initial position for use if no inputs
        # are inputs, and the offset x and y are the aggregate
        # of the user's input.

    def __repr__(self):
        return f"Paddle(vertices={repr(self.vertices)},r={repr(self.r)},g={repr(self.g)},b={repr(self.b)},initial_position={repr(self.initial_position)},input_offset_x={repr(self.input_offset_x)},input_offset_y={repr({self.input_offset_y})})"

# NEW! paddles are using modelspace coordinates instead of NDC
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


def handle_movement_of_paddles():
    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.input_offset_y -= 10.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.input_offset_y += 10.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.input_offset_y -= 10.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.input_offset_y += 10.0


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

        # Instead, for model-space to world-space transformations,
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
        # has no value.  Front to back can useful when dealing with cameraspace transformations,
        # introduced later.

        # This will make more sense once rotation is involved.
        world_space = model_space.translate(tx=paddle1.initial_position.x,
                                            ty=paddle1.initial_position.y) \
                                 .translate(tx=paddle1.input_offset_x,
                                            ty=paddle1.input_offset_y)

        # === Scaling

        # eog ../images/scale.png


        # Similarly, we can expand or shrink the size of an object
        # by "scale"ing each of the vertices of the object.
        # Our global space is -100 to 100 in both dimesnions,
        # and to get it into NDC, we need to scale by dividing by 100

        ndc_space = world_space.scale(scale_x=1.0/100.0,
                                      scale_y=1.0/100.0)
        glVertex2f(ndc_space.x,
                   ndc_space.y)

        # The follwing diagrams shows the functions that transition between spaces.
        # The arrow represents a function from one space to another.  All spaces
        # will resolve to NDC.

        # eog ../images/demo06.png

    glEnd()

    # draw paddle2
    glColor3f(paddle2.r,
              paddle2.g,
              paddle2.b)

    glBegin(GL_QUADS)
    for model_space in paddle2.vertices:

        # Do the same transformations to the second paddle

        world_space = model_space.translate(tx=paddle2.initial_position.x,
                                            ty=paddle2.initial_position.y) \
                                 .translate(tx=paddle2.input_offset_x,
                                            ty=paddle2.input_offset_y)

        ndc_space = world_space.scale(scale_x=1.0/100.0,
                                      scale_y=1.0/100.0)
        glVertex2f(ndc_space.x,
                   ndc_space.y)
    glEnd()


    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)

glfw.terminate()
