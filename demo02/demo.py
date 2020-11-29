# Copyright (c) 2018-2020 William Emerison Six
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# PURPOSE
# Learn how to draw some geometry, and give it a color


import sys
import os
import numpy as np
import math
from OpenGL.GL import *
import glfw

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500, 500, "ModelViewProjection Demo 2", None, None)
if not window:
    glfw.terminate()
    sys.exit()

# Make the window's context current
glfw.make_context_current(window)

# Install a key handler
def on_key(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, 1)


glfw.set_key_callback(window, on_key)

glClearColor(0.0, 0.0, 0.0, 1.0)


glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glMatrixMode(GL_MODELVIEW)
glLoadIdentity()

# Loop until the user closes the window
while not glfw.window_should_close(window):
    # Poll for and process events
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Draw Paddles

    # A black screen is not particularly interesting, so
    # let's draw something, say, two rectangles.
    # Where should they be, and what color should they be?

    # "glColor3f" sets a global variable, which makes it the color to be used
    # for the subsequently-drawn graphical shape.  The background will be black,
    # so lets make the first paddle purple, and a second paddle red.

    # "glBegin(GL_QUADS)" tells OpenGL that we will soon specify 4 *vertices*,
    # (i.e. points) which define the
    # quadrilateral.  The vertices will be specified by calling "glVertex2f" 4 times.

    # "glEnd()" tells OpenGL that we have finished providing vertices for
    # the begun quadrilateral.

    # render scene
    # draw paddle 1
    glColor3f(0.578123, 0.0, 1.0)  # r  # g  # b
    glBegin(GL_QUADS)
    glVertex2f(-1.0, -0.3)  # x  # y
    glVertex2f(-0.8, -0.3)  # x  # y
    glVertex2f(-0.8, 0.3)  # x  # y
    glVertex2f(-1.0, 0.3)  # x  # y
    glEnd()

    # The framebuffer, which has not yet been flushed to the monitor, has geometry which looks like this:
    # eog ../images/plot1.png

    # draw paddle 2
    glColor3f(1.0, 0.0, 0.0)
    glBegin(GL_QUADS)

    glVertex2f(0.8, -0.3)
    glVertex2f(1.0, -0.3)
    glVertex2f(1.0, 0.3)
    glVertex2f(0.8, 0.3)
    glEnd()

    # The framebuffer, which has not yet been flushed to the monitor, has geometry which looks like this:
    # eog ../images/plot2.png

    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)

glfw.terminate()


# The frame sent to the monitor is a set of values like this:
# ....
# bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# pppppbbbbbbbbbbbbbbbbbbbbbbbbbbbrrrrr
# pppppbbbbbbbbbbbbbbbbbbbbbbbbbbbrrrrr
# pppppbbbbbbbbbbbbbbbbbbbbbbbbbbbrrrrr
# pppppbbbbbbbbbbbbbbbbbbbbbbbbbbbrrrrr
# pppppbbbbbbbbbbbbbbbbbbbbbbbbbbbrrrrr
# pppppbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# ....

# What do we have to do to convert from normalized-device-coordinates
# into individual colors for each pixel?  Nothing, OpenGL does that for us; therefore
# we never have to think in terms of pixels, only in terms of vertices of shapes,
# specified by normalized-device-coordinates.

# Why is that desirable?

####### Normalized-Device-Coordinates

# The author owns two monitors, one which has 1024x768 pixels, and one which has
# 1920x1200 pixels.  When he purchases a game from Steam, he expects that his game
# will run correctly on either monitor, in full-screen mode.  If a graphics programmer
# had to explictly set each indiviual pixel's color, the the programmer would have to
# program using "screen-space"(Any "space" means a system of numbers which you're using.
# Screen-space means you're specifically using pixel coordinates, i.e, set pixel (5,10) to be red).

# What looks alright is screen-space on a large monitor...
# eog ../images/screenspace2.png

# isn't even the same picture on a smaller monitor.
# eog ../images/screenspace.png


# Like any good program or library, OpenGL abstracts over screen-space, thus freeing the
# programmer from caring about screen size.  If a programmer does not want to program
# in discrete (discrete means integer values, not continuous) screen-space,
# what type of numbers should he use?  Firstly, it should be a continuous space, meaning
# that it should be in decimal numbers.  Because if a real-world object is 10.3 meters long, a programmer
# should be able to enter "float foo = 10.3".  Secondly, it should be a fixed range vertically
# and an fixed range horizontally.  OpenGL will have to convert points from some space to screen-space,
# and since OpenGL does this in hardware (i.e. you can't programmatically change how the conversion
# happens), it should be a fixed size.

# OpenGL uses *normalized-device-coordinates* (normalized- meaning a distance value of
# 1; device- the monitor; coordinates- the system of numbers (i.e. space) in which you are working),
# which is a continous space from -1.0 to 1.0 horizontally,
# and -1.0 to 1.0 vertically.


# By specifying geometry using normalized-device-coordinates,
# OpenGL will automatically convert from a continuous, -1.0 to 1.0 space,
# to discrete pixel-space.

# eog ../images/ndcSpace.png

# Whether we own a small monitor

# eog ../images/ndcSpace1.png

# or a large monitor.

# eog ../images/screenspace2.png


# -Exercise 1.  The window is resizable by the user while it runs.
# Do the paddles both  still appear in the window if you make it really thin?  What if
# you make it very wide?


# Answer - (Regardless of the window's width to height ratio, the pixel in the upper left of
# the window still maps to normalized-device-coordinate (-1.0,-1.0), and the pixel
# in the bottom right of the window still maps to (1.0,1.0).

# -Exercise 2.  How would you convert from ndc-space to screen-space, given
# a monitor width _w_ and height _h_?
