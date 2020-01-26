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
# Given the goal of keeping the paddles proportial regardless of window
# size, fix the previous demo.


# == Keeping the Paddles Proportional

# === Create procedure to ensure proportionality
# In the previous demo, if the user resized the window, the paddles looked bad,
# as they were shrunk in one direction if the window became too thin or too fat.


#  eog ../images/disproportionate1.png
#  eog ../images/disproportionate2.png



# Assume that this is a problem for the application we are making.  What
# would a solution be?  Ideally, we would like to draw our paddles with
# a black background within a square region in the center of the window, regardless of the dimensions
# of the window.

# OpenGL has a solution for us.  The *viewport* is a rectangular region
# within the window into which OpenGL will render.  The normalized-device-coordinates
# will therefore resolve to the sub-screen space of the viewport, instead of the whole
# window.


# eog ../images/viewport.png

# Because we will only draw in a subset of the window, and because all subsequent
# chapters will use this functionality, I have created a procedure for use
# in all chapters. "draw_in_square_viewport" is a function.



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
                            "ModelViewProjection Demo 3",
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

    # the scissor test allows us to specify a region
    # of the framebuffer into which the opengl operations
    # will apply.  In this case, in the framebuffer is all gray.
    # by calling glScissor, we are setting a value on a square
    # of pixels which says "only do the opengl call on these".
    # As we will learn later, OpenGL stores much more information
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


# Loop until the user closes the window
while not glfw.window_should_close(window):
    # Poll for and process events
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # render scene
    draw_in_square_viewport()

    # draw paddle 1
    glColor3f(0.578123, #r
              0.0,      #g
              1.0)      #b
    glBegin(GL_QUADS)
    glVertex2f(-1.0, #x
               -0.3) #y
    glVertex2f(-0.8, #x
               -0.3) #y
    glVertex2f(-0.8, #x
               0.3)  #y
    glVertex2f(-1.0, #x
               0.3)  #y
    glEnd()
    # draw paddle 2
    glColor3f(1.0,
              0.0,
              0.0)
    glBegin(GL_QUADS)

    glVertex2f(0.8,
               -0.3)
    glVertex2f(1.0,
               -0.3)
    glVertex2f(1.0,
               0.3)
    glVertex2f(0.8,
               0.3)
    glEnd()


    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)

glfw.terminate()
