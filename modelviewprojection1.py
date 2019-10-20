# "I had no idea how much math was involved in computer graphics."

# Unfortunately many students of computer graphics have the impression
# that the writing of computer graphics programs requires knowledge of
# advanced math; which is patently untrue.
# Only the understanding of high-school level geometry is required.
# Using math you already know, this book builds both 2D and 3D
# applications from the ground up using OpenGL, a standard for graphics
# programming.

# Thoughout the book, I show how to place objects in space,
# how to draw objects relative to other objects, how to add a
# camera which moves over time based on user input, and how to transform all
# the objects into the 2D pixel coordinates of the computer screen.
# By the end of this book, you will understand the basics of
# how to create first-person and third-person applications/games.
# I made this book to show programmers how to make the kind
# of graphics programs which they want to make, using
# math they aleady know.

# This book is purposely limited in scope, and
# the applications produced are not particurly pretty nor realistic-looking.
# For advanced graphics topics, you'll need to consult other references,
# such as the OpenGL "red book" and "blue book".
# Although this book fills a huge gap that other books do not address,
# those other books are excellent reference books for advanced topics.

###### Basics
#
# The device attached to a computer which displays information to the user is called a *monitor*.
# The monitor is composed of a two-dimensional array of light-emitting elements, each called a *pixel*.
# At a given time, each individual pixel is instructed to display
# one specific color, represented within the computer as a number.
# The aggregate of the colors at each pixel at one moment in time, called a *frame*,
# provides a picture that has some meaning to the human user.
#
# In OpenGL, the bottom left pixel of a window is coordinate (0,0).  The top right is (window_width,window_height)
#
# 1024x768 monitor
# eog monitor.png
#
# 1920x1200 monitor
# eog monitor2.png
#
#
# Frames are created within the computer and sent to the monitor
# at a rate over time, called the *framerate*,
# measured in *Hertz*.  By updating frames quickly and at a constant rate, the computer
# provides the end-user with the illusion of motion.
#
# TODO - insert 3 20x20 frames which show motion

import sys
import os
import numpy as np
import math
from OpenGL.GL import *
import glfw

##### Opening a Window
#
# Desktop operating systems allow the user to run more than one
# program at a time, where each program draws into a subsection of
# the monitor called a window.
#
#
# To create and to open a window in a cross-platform manner, this
# book will call procedures provided by the widely-ported GLFW library (supporting Windows, macOS, Linux).
# GLFW also provides procedures for receiving
# keyboard input and for controller.
#


###### GLFW/OpenGL Initialization
#
# -Initialize GLFW.
#
if not glfw.init():
    sys.exit()
# One frame is created incrementally over time on the CPU, but the frame
# is sent to the monitor
# only when frame is completely drawn, and each pixel has a color.
# The act of sending the frame to the monitor is called *flushing*
# the frame.
# Flushing takes time,
# and if the call to flush were to blockfootnote:[meaning it would not return control back to the call-ing procedure until the flush is complete], we would
# have wasted CPU time.  To avoid this,
# OpenGL has two *framebuffers*footnote:[regions of memory which will eventually contain the full data for a frame],
# only one of which is "active", or writable, at a given time.
# "glfwSwapBuffers" is a non-blocking call which initiates the flushing
# the current buffer, and which switches the current writable framebuffer to the
# other one, thus allowing the CPU to resume.
#
# -Set the version of OpenGL
# OpenGL has been around a long time, and has multiple, possibly incompatible versions.
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR,1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR,4)
# Create a 500 pixel by 500 pixel window, which the user can resize.
window = glfw.create_window(500,
                            500,
                            "ModelViewProjection Demo 1",
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

# For every frame drawn, each pixel has a default color, set by
# calling "glClearColor". "0,0,0,1", means black "0,0,0", without
# transparency (the "1").
glClearColor(0.0,
             0.0,
             0.0,
             1.0)

#Enable blending of new values in a fragment with the old value.
glEnable(GL_BLEND)

# Specify how a given fragment's color value within the framebuffer combines with a second color.  This new
#blended value is then set for the fragment.
glBlendFunc(GL_SRC_ALPHA,
            GL_ONE_MINUS_SRC_ALPHA)

glMatrixMode(GL_PROJECTION);
glLoadIdentity();
glMatrixMode(GL_MODELVIEW);
glLoadIdentity();



###### The Event Loop
#
# When you pause a movie, motion stops and you see one picture.
# Movies are composed of sequence of pictures, when
# rendered in quick succession, provide the illusion of motion.
#
# Interactive computer graphics are rendered the same way,
# one "frame" at a time.
#
# Render a frame, flush the complete frame to the monitor.
# Unless the user closed the window, repeat indefinitely.
#
# The color of each pixel withith
# the current framebuffer
# is reset to a default color.
#
# When a graphics application is executing, it is creating new
# frames (pictures) at some rate (e.g. 60 frames per second).  At any given
# frame, the user of the application might do something, (e.g.
# move the mouse, click, type on the keyboard, close the application).
#
# At the beginning of every frame, ask GLFW if it received one
# of these events since we last asked (i.e., the previous frame).


# Loop until the user closes the window
while not glfw.window_should_close(window):
    # Poll for and process events
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # render scene
    # do nothing

    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)

glfw.terminate()


###### Black Screen
#
# Add the "mvp" direction to your PYTHONPATH, and type
# "python modelviewprojection.py". When prompted, type "1" and then press the "Enter" key.
#
# The first demo is the least interesting graphical program possible.
#
# -Sets the color at every pixel black.  (A constant color is better than whatever
# color happened to be the previous time it was drawn.)
#
# -If the user resized the window, reset OpenGL's mappings from *normalized-device-coordinates*
# to *screen-coordinates*.
#
# -Cleared the depth buffer (don't worry about this for now).
#
# When this code returns, the event loop flushes (i.e) sends the frame to the monitor.  Since
# no geometry was drawn, the color value for each pixel is still black.

# Each color is represented by a number, so the frame is something like this:


# ....
# bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
# ....




# The event loop then calls this code over and over again, and since we retain no state and
# we draw nothing, a black screen will be displayed every frame until the user
# closes the window, and says to himself, "why did I buy Doom 3"?
