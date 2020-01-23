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
# Add movement to the paddles using keyboard input.


# == Move the Paddles using the Keyboard

# |=======================================
# |Keyboard Input |Action
# |*w*              |*Move Left Paddle Up*
# |*s*              |*Move Left Paddle Down*
# |*k*              |*Move Right Paddle Down*
# |*i*              |*Move Right Paddle Up*
# |=======================================

# Paddles which don't move are quite boring.  Let's make them move up or down
# by getting keyboard input.


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
                            "ModelViewProjection Demo 4",
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


# define a class in Python for Vertex
class Vertex:
    # __init__ is the constructor, all methods
    # on an instance explicitly take self as the first parameter.
    # properties can be added dynamically to objects in Python.
    def __init__(self,x,y):
        self.x = x
        self.y = y

# define a class for the Paddle
class Paddle:
    def __init__(self,vertices, r, g, b, offset_x=0.0, offset_y=0.0):
        # Python allows default values to parameters, and allows
        # the calling function to specify the name of the argument
        self.vertices = vertices
        self.r = r
        self.g = g
        self.b = b
        self.offset_x = offset_x
        self.offset_y = offset_y


paddle1 = Paddle(vertices=[Vertex(x=-1.0,y=-0.3), # keyword arguments
                           Vertex(x=-0.8,y=-0.3), # can only be used at the end
                           Vertex(x=-0.8,y=0.3),  # try removing "y="
                           Vertex(x=-1.0,y=0.3)],
                 r=0.578123,
                 g=0.0,
                 b=1.0)

paddle2 = Paddle(vertices=[Vertex(0.8,-0.3),
                           Vertex(1.0,-0.3),
                           Vertex(1.0,0.3),
                           Vertex(0.8,0.3)],
                 r=1.0,
                 g=0.0,
                 b=0.0)


# -If 's' is pressed this frame, subtract 0.1 more from paddle1.offsetY.  If the
# key continues to be held down over time, paddle1.offsetY will continue to decrease.

# -If 'w' is pressed this frame, add 0.1 more to paddle1.offsetY.

# -If 'k' is pressed this frame, subtract 0.1 more from paddle_2_offset_Y.

# -If 'i' is pressed this frame, add 0.1 more to paddle_2_offset_Y.



def handle_movement_of_paddles():
    # when writing to global variables within a nested scope,
    # you need to declare their scope at the top of the nested scope.
    global paddle1, paddle2
    # for data that is just read, this is not needed.
    # it's a quick of Python's scope resolution rules,
    # but hey, Python is popular because of the good decisions
    # made in the aggregate, with some weirdness in corner cases

    # this is how you test if a key was pressed
    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.offset_y -= 0.1
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.offset_y += 0.1
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.offset_y -= 0.1
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.offset_y += 0.1


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

    # draw paddle 1
    glColor3f(paddle1.r,
              paddle1.g,
              paddle1.b)

    # Draw paddle 1, relative to the world-space origin.
    # Add paddle1.offsetY to the "y" component of every vertex
    #  eog ../images/plot3.png

    glBegin(GL_QUADS)
    # for loop in Python, each of paddle1's vertices gets
    # bound to "vertex" for the loop
    for vertex in paddle1.vertices:
        glVertex2f(vertex.x,
                   vertex.y + paddle1.offset_y) # add in the offset so that the paddle moves
    glEnd()

    # draw paddle 2
    glColor3f(paddle2.r,
              paddle2.g,
              paddle2.b)

    # Draw paddle 2, relative to the world-space origin.
    # Add paddle_2_offset_Y to the "y" component of every vertex
    # eog ../images/plot4.png
    glBegin(GL_QUADS)
    for vertex in paddle2.vertices:
        glVertex2f(vertex.x,
                   vertex.y + paddle2.offset_y)
    glEnd()




    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)

glfw.terminate()
