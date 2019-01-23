#!/usr/bin/env python
##// The MIT License (MIT)
##//
##// Copyright (c) 2017-2018 William Emerison Six
##//
##// Permission is hereby granted, free of charge, to any person obtaining a copy
##// of this software and associated documentation files (the "Software"), to deal
##// in the Software without restriction, including without limitation the rights
##// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
##// copies of the Software, and to permit persons to whom the Software is
##// furnished to do so, subject to the following conditions:
##//
##// The above copyright notice and this permission notice shall be included in all
##// copies or substantial portions of the Software.
##//
##// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
##// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
##// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
##// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
##// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
##// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
##// SOFTWARE.

##= Model View Projection
##:author: Bill Six <billsix@gmail.com>
##:doctype: book
##:toc:
##
##[dedication]
##= Dedication
##
##To Teresa, Liam, Adam, and Kate.
##
##
##[preface]
##= Preface
##
##"I had no idea how much math was involved in computer graphics."
##
##Unfortunately many students of computer graphics have the impression
##that the writing of computer graphics programs requires knowledge of
##advanced math; which is patently untrue.
##Only the understanding of high-school level geometry is required.
##Using math you already know, this book builds both 2D and 3D
##applications from the ground up using OpenGL, a standard for graphics
##programming.
##
##Thoughout the book, I show how to place objects in space,
##how to draw objects relative to other objects, how to add a
##camera which moves over time based on user input, and how to transform all
##the objects into the 2D pixel coordinates
##of the computer screen.  By the end of this book, you will understand the basics of
##how to create first-person
##and third-person applications/games.  I made this book to show programmers
##how to make the kind
##of graphics programs which they want to make, using
##math they aleady know.
##
##This book is purposely limited in scope, and
##the applications produced are not particurly pretty nor realistic-looking.
##For advanced graphics topics, you'll need to consult other references,
##such as the OpenGL "red book" and "blue book".
##Although this book fills a huge gap that other books do not address,
##those other books are excellent reference books for advanced topics.
##
##
##
##
##[[intro]]
##= Introduction
##

##== Copyright
##
##(C) 2017-2018, William Emerison Six. The source, and the generated book, are free under the MIT licence

##[[basics]]
##== Basics
##
##
##The device attached to a computer which displays information to the user is called a *monitor*.
##The monitor is composed of a two-dimensional array of light-emitting elements, each called a *pixel*.
##At a given time, each individual pixel is instructed to display
##one specific color, represented within the computer as a number.
##The aggregate of the colors at each pixel at one moment in time, called a *frame*,
##provides a picture that has some meaning to the human user.
##
##
##
##In OpenGL, the bottom left pixel of a window is coordinate (0,0).  The top right is (window_width,window_height)
##
##.1024x768 monitor
##[caption="Figure 1: "]
##image:monitor.png[align="center",title="Foo"]
##
##.1920x1200 monitor
##image:monitor2.png[align="center",title="Foo"]
##
##
##Frames are created within the computer and sent to the monitor
##at a rate over time, called the *framerate*,
##measured in *Hertz*.  By updating frames quickly and at a constant rate, the computer
##provides the end-user with the illusion of motion.
##
##TODO - insert 3 20x20 frames which show motion
##
##
##
##[[openWindow]]
##=== Opening a Window
##
##Desktop operating systems allow the user to run more than one
##program at a time, where each program draws into a subsect of
##the monitor called a window.
##
##
##To create and to open a window in a cross-platform manner, this
##book will call procedures provided by the widely-ported GLFW library (supporting Windows, macOS, Linux).
##GLFW also provides procedures for receiving
##keyboard input and for controller inputfootnote:[tested with a wired XBox 360 controller].
##
##Much of the code listed from here until section<<the-event-loop>> will be of little interest upon first reading.
##As such, the reader may choose to skip ahead to section<<the-event-loop>> now.
##
##The code for the entire book is available at https://github.com/billsix/modelviewprojection,
##contained within "mvp/modelviewprojection.py". The code and the contents of the book are licenced
##using the open-source MIT license.
##
##
##==== Include Headers
##
##
##[source,Python,linenums]
##----
import sys
import os
import numpy as np
import math
from OpenGL.GL import *
import glfw
import ctypes


print("Which Chapter would you like to execute?")
chapterNumber = input()

## TODO - explain these decorators or move them somewhere else
# - if the user selected this demo, then run it now.
# this way, overridden/updated functions do not affect this
# demo

demoNumber = 1
def registerDemo(F):
    global demoNumber
    if int(chapterNumber) == demoNumber:
        global render_scene
        render_scene = F
        main_loop()
        sys.exit(0)
    else:
        demoNumber += 1
        return F
##----

##==== GLFW/OpenGL Initialization
##
##-Initialize GLFW.
##[source,Python,linenums]
##----
if not glfw.init():
    sys.exit()
##----
##
##One frame is created incrementally over time on the CPU, but the frame
##is sent to the monitor
##only when frame is completely drawn, and each pixel has a color.
##The act of sending the frame to the monitor is called *flushing*
##the frame.
##Flushing takes time,
##and if the call to flush were to blockfootnote:[meaning it would not return control back to the call-ing procedure until the flush is complete], we would
##have wasted CPU time.  To avoid this,
##OpenGL has two *framebuffers*footnote:[regions of memory which will eventually contain the full data for a frame],
##only one of which is "active", or writable, at a given time.
##"glfwSwapBuffers" is a non-blocking call which initiates the flushing
##the current buffer, and which switches the current writable framebuffer to the
##other one, thus allowing the CPU to resume.
##
##-Set the version of OpenGL
##
##OpenGL has been around a long time, and has multiple, possibly incompatible versions.
##
##[source,Python,linenums]
##----
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR,1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR,4)
##----

##Create a 500 pixel by 500 pixel window, which the user can resize.
##[source,Python,linenums]
##----
window = glfw.create_window(500,
                            500,
                            "ModelViewProjection",
                            None,
                            None)
if not window:
    glfw.terminate()
    sys.exit()
##----

##[source,Python,linenums]
##----
# Make the window's context current
glfw.make_context_current(window)

# Install a key handler
def on_key(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window,1)
glfw.set_key_callback(window, on_key)
##----

##For every frame drawn, each pixel has a default color, set by
##calling "glClearColor". "0,0,0,1", means black "0,0,0", without
##transparency (the "1").
##[source,Python,linenums]
##----
glClearColor(0.0,
             0.0,
             0.0,
             1.0)
##----

##Enable blending of new values in a fragment with the old value.
##[source,Python,linenums]
##----
glEnable(GL_BLEND)
##----
##Specify how a given fragment's color value within the framebuffer combines with a second color.  This new
##blended value is then set for the fragment.
##[source,Python,linenums]
##----
glBlendFunc(GL_SRC_ALPHA,
            GL_ONE_MINUS_SRC_ALPHA)

glMatrixMode(GL_PROJECTION);
glLoadIdentity();
glMatrixMode(GL_MODELVIEW);
glLoadIdentity();
##----


##[[the-event-loop]]
##==== The Event Loop
##
##When you pause a movie, motion stops and you see one picture.
##Movies are composed of sequence of pictures, when
##rendered in quick succession, provide the illusion of motion.
##
##Interactive computer graphics are rendered the same way,
##one "frame" at a time.
##
##Render a frame for the user-selected demo, flush the complete frame to the monitor.
##Unless the user closed the window, repeat indefinitely.
##

##[source,Python,linenums]
##----
def main_loop():
    # Loop until the user closes the window
    while not glfw.window_should_close(window):
        # Poll for and process events
        glfw.poll_events()

        width, height = glfw.get_framebuffer_size(window)
        glViewport(0, 0, width, height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
##----

##Regardless of which demo will be run, certain things need
##to happen every frame.  The color of each pixel withith
##the current framebuffer
##is reset to a default color.
##
##[source,Python,linenums]
##----
        # currently undefined, but will be before the event loop is called
        render_scene()
##----

##[source,Python,linenums]
##----
        # done with frame, flush and swap buffers
        # Swap front and back buffers
        glfw.swap_buffers(window)

    glfw.terminate()
##----

##When a graphics application is executing, it is creating new
##frames (pictures) at some rate (e.g. 60 frames per second).  At any given
##frame, the user of the application might do something, (e.g.
##move the mouse, click, type on the keyboard, close the application).
##
##At the beginning of every frame, ask OpenGL if it received one
##of these events since we last asked (i.e., the previous frame).
##
##
##
##== Black Screen
##
##To understand the material of this book well, the reader is advised to
##execute the demos.  To do so, the source
##code for this book may be obtained at https://github.com/billsix/modelviewprojection.
##It has been tested on macOS and on Linux.  Install Python3 and NumPy.
##
##Add the "mvp" direction to your PYTHONPATH, and type
##"python modelviewprojection.py". When prompted, type "1" and then press the "Enter" key.
##
##The first demo is the least interesting graphical program possible.
##
##The event loop, defined in section <<the-event-loop>>, executes a few procedures
##before calling the current procedure.

##-Sets the color at every pixel black.  (A constant color is better than whatever
##color happened to be the previous time it was drawn.)
##
##-If the user resized the window, reset OpenGL's mappings from *normalized-device-coordinates*
##to *screen-coordinates*.
##
##-Cleared the depth buffer (don't worry about this for now).
##
##
##[source,Python,linenums]
##----
@registerDemo
def demo1():
    # The baseline behavior.  A black screen.
    pass
##----

##When this code returns, the event loop flushes (i.e) sends the frame to the monitor.  Since
##no geometry was drawn, the color value for each pixel is still black.
##
##Each color is represented by a number, so the frame is something like this:
##
##
##....
##bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##....
##
##
##

##The event loop then calls this code over and over again, and since we retain no state and
##we draw nothing, a black screen will be displayed every frame until the user
##closes the window, and says to himself, "why did I buy Doom 3"?



##== Draw Paddles
##
##
##A black screen is not particularly interesting, so
##let's draw something, say, two rectangles.
##Where should they be, and what color should they be?

##"glColor3f" sets a global variable, which makes it the color to be used
##for the subsequently-drawn graphical shape.  The background will be black,
##so lets make the first paddle purple, and a second paddle red.
##
##"glBegin(GL_QUADS)" tells OpenGL that we will soon specify 4 *vertices*,
##(i.e. points) which define the
##quadrilateral.  The vertices will be specified by calling "glVertex2f" 4 times.


##[source,Python,linenums]
##----
@registerDemo
def demo2():
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
##----

##"glEnd()" tells OpenGL that we have finished providing vertices for
##the begun quadrilateral.
##

##The framebuffer, which has not yet been flushed to the monitor, has geometry which looks like this:

##image:plot1.png[align="center",title="Foo"]


##[source,Python,linenums]
##----
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
##----

##The framebuffer, which has not yet been flushed to the monitor, has geometry which looks like this:

##image:plot2.png[align="center",title="Foo"]


##The frame sent to the monitor is a set of values like this:
##....
##bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##pppppbbbbbbbbbbbbbbbbbbbbbbbbbbbrrrrr
##pppppbbbbbbbbbbbbbbbbbbbbbbbbbbbrrrrr
##pppppbbbbbbbbbbbbbbbbbbbbbbbbbbbrrrrr
##pppppbbbbbbbbbbbbbbbbbbbbbbbbbbbrrrrr
##pppppbbbbbbbbbbbbbbbbbbbbbbbbbbbrrrrr
##pppppbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
##....

##What do we have to do to convert from normalized-device-coordinates
##into individual colors for each pixel?  Nothing, OpenGL does that for us; therefore
##we never have to think in terms of pixels, only in terms of vertices of shapes,
##specified by normalized-device-coordinates.
##
##Why is that desirable?
##
##=== Normalized-Device-Coordinates
##
##The author owns two monitors, one which has 1024x768 pixels, and one which has
##1920x1200 pixels.  When he purchases a game from Steam, he expects that his game
##will run correctly on either monitor, in full-screen mode.  If a graphics programmer
##had to explictly set each indiviual pixel's color, the the programmer would have to
##program using "screen-space"footnote:[Any "space" means a system of numbers which you're using.
##Screen-space means you're specifically using pixel coordinates, i.e, set pixel (5,10) to be red].

##What looks alright is screen-space on a large monitor...

##image:screenspace2.png[align="center",title="Programming using Screen Space on Large Monitor"]

##isn't even the same picture on a smaller monitor.

##image:screenspace.png[align="center",title="Programming using Screen Space on Small Monitor"]



##Like any good program or library, OpenGL abstracts over screen-space, thus freeing the
##programmer from caring about screen size.  If a programmer does not want to program
##in discretefootnote:[discrete means integer values, not continuous] screen-space,
##what type of numbers should he use?  Firstly, it should be a continuous space, meaning
##that it should be in decimal numbers.  Because if a real-world object is 10.3 meters long, a programmer
##should be able to enter "float foo = 10.3".  Secondly, it should be a fixed range vertically
##and an fixed range horizontally.  OpenGL will have to convert points from some space to screen-space,
##and since OpenGL does this in hardware (i.e. you can't programmatically change how the conversion
##happens), it should be a fixed size.

##OpenGL uses *normalized-device-coordinates* footnote:[normalized- meaning a distance value of
##1; device- the monitor; coordinates- the system of numbers (i.e. space) in which you are working],
##which is a continous space from -1.0 to 1.0 horizontally,
##and -1.0 to 1.0 vertically.


##By specifying geometry using normalized-device-coordinates,
##OpenGL will automatically convert from a continuous, -1.0 to 1.0 space,
##to discrete pixel-space.

##image:ndcSpace.png[align="center",title="Programming using Screen Space on Large Monitor"]

##Whether we own a small monitor

##image:ndcSpace1.png[align="center",title="Programming using Screen Space on Small Monitor"]

##or a large monitor.

##image:screenspace2.png[align="center",title="Programming using Screen Space on Large Monitor"]


##-Exercise 1.  The window is resizable by the user while it runs.
##Do the paddles both  still appear in the window if you make it really thin?  What if
##you make it very wide?


##Answer - (Regardless of the window's width to height ratio, the pixel in the upper left of
##the window still maps to normalized-device-coordinate (-1.0,-1.0), and the pixel
##in the bottom right of the window still maps to (1.0,1.0).

##-Exercise 2.  How would you convert from ndc-space to screen-space, given
##a monitor width _w_ and height _h_?

##== Keeping the Paddles Proportional
##
##=== Create procedure to ensure proportionality
##In the previous chapter, if the user resized the window, the paddles looked bad,
##as they were shrunk in one direction if the window became too thin or too fat.


##image:disproportionate1.png[align="center",title="Foo"]


##image:disproportionate2.png[align="center",title="Foo"]


##Assume that this is a problem for the application we are making.  What
##would a solution be?  Ideally, we would like to draw our paddles with
##a black background within a square region in the center of the window, regardless of the dimensions
##of the window.

##OpenGL has a solution for us.  The *viewport* is a rectangular region
##within the window into which OpenGL will render.  The normalized-device-coordinates
##will therefore resolve to the sub-screen space of the viewport, instead of the whole
##window.
##

##image:viewport.png[align="center",title="Programming using Screen Space on Large Monitor"]

##Because we will only draw in a subset of the window, and because all subsequent
##chapters will use this functionality, I have created a procedure for use
##in all chapters. "draw_in_square_viewport" is a C++ lambda, which just
##means that it's a procedure defined at runtime.  Don't worry about the details
##of lambdas, just know that the following two types are the same:



##[source,Python,linenums]
##----
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
##----


##=== Set the viewport, and then execute the code from chapter 3.


##[source,Python,linenums]
##----
@registerDemo
def demo3():
    draw_in_square_viewport()
    demo2()
##----


##
##== Move the Paddles using the Keyboard
##
##[width="75%",options="header,footer"]
##|=======================================
##|Keyboard Input |Action
##|*w*              |*Move Left Paddle Up*
##|*s*              |*Move Left Paddle Down*
##|*k*              |*Move Right Paddle Up*
##|*i*              |*Move Right Paddle Down*
##|=======================================
##Paddles which don't move are quite boring.  Let's make them move up or down
##by getting keyboard input.
##
##

##[source,Python,linenums]
##----
class Vertex:
    def __init__(self,x,y):
        self.x = x
        self.y = y

class Paddle:
    def __init__(self,vertices, r, g, b, offsetX=0.0, offsetY=0.0):
        self.vertices = vertices
        self.r = r
        self.g = g
        self.b = b
        self.offsetX = offsetX
        self.offsetY = offsetY

paddle1 = Paddle(vertices=[Vertex(-1.0,-0.3),
                           Vertex(-0.8,-0.3),
                           Vertex(-0.8,0.3),
                           Vertex(-1.0,0.3)],
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


inputHandlers = []
def handle_inputs():
    for f in inputHandlers:
        f()

def handle_movement_of_paddles():
    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.offsetY -= 0.1
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.offsetY += 0.1
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.offsetY -= 0.1
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.offsetY += 0.1
inputHandlers.append(handle_movement_of_paddles)
##----

##Define a draw method on the Paddle class.  Python allows
##both instance variables and methods to be added to a class
##after it has already been defined.  Although the author
##doesn't recommend cavalier use of this concept, graphics
##are best explained incrementally, and the dynamic features
##of Python help towards this goal.
##

##[source,Python,linenums]
##----
# define the method, currently unbound to a class
def draw(self):
    glColor3f(self.r,
              self.g,
              self.b)

    glBegin(GL_QUADS)
    for vertex in self.vertices:
        glVertex2f(vertex.x,
                   vertex.y + self.offsetY)
    glEnd()
# add the draw method to the Paddle class
Paddle.draw = draw
##----



##-If 's' is pressed this frame, subtract 0.1 more from paddle1.offsetY.  If the
##key continues to be held down over time, paddle1.offsetY will continue to decrease.

##-If 'w' is pressed this frame, add 0.1 more to paddle1.offsetY.

##-If 'k' is pressed this frame, subtract 0.1 more from paddle_2_offset_Y.

##-If 'i' is pressed this frame, add 0.1 more to paddle_2_offset_Y.

##Remember, these are static variables, so changes to these variables will
##accumulate across frames.
##


##[source,Python,linenums]
##----
@registerDemo
def demo4():
    draw_in_square_viewport()
    handle_inputs()
##----

##Draw paddle 1, relative to the world-space origin.
##Add paddle1.offsetY to the "y" component of every vertex

##[source,Python,linenums]
##----
    paddle1.draw()
##----

##image:plot3.png[align="center",title="Foo"]


##Draw paddle 2, relative to the world-space origin.
##Add paddle_2_offset_Y to the "y" component of every vertex


##[source,Python,linenums]
##----
    paddle2.draw()
##----

##image:plot4.png[align="center",title="Foo"]


##== Translation
##
##[width="75%",options="header,footer"]
##|=======================================
##|Keyboard Input |Action
##|w              |Move Left Paddle Up
##|s              |Move Left Paddle Down
##|k              |Move Right Paddle Up
##|i              |Move Right Paddle Down
##|=======================================
##
##Transforming vertices, such as translating, is the core concept
##of computer graphics.



##=== Translation
##Rather than incrementing y values before calling "glVertex",
##instead call "translate" on the vertex, and call "glVertex2f"
##on the translated vertex.

##image:translationF.gif[align="center",title="Foo"]

## TODO -- rename translate's x and y to tx and ty
##[source,Python,linenums]
##----
# add translate method to Vertex
def translate(self, tx, ty):
    return Vertex(x=self.x + tx, y=self.y + ty)
Vertex.translate = translate

def draw(self):
    glColor3f(self.r,
              self.g,
              self.b)

    glBegin(GL_QUADS)
    for vertex in self.vertices:
        translated = vertex.translate(tx=0.0,
                                      ty=self.offsetY)
        glVertex2f(translated.x,
                   translated.y)
    glEnd()
Paddle.draw = draw

@registerDemo
def demo5():
    draw_in_square_viewport()
    handle_inputs()

    paddle1.draw()
    paddle2.draw()
##----



##== Model-space
##
##[width="75%",options="header,footer"]
##|=======================================
##|Keyboard Input |Action
##|w              |Move Left Paddle Up
##|s              |Move Left Paddle Down
##|k              |Move Right Paddle Up
##|i              |Move Right Paddle Down
##|=======================================

##Normalized-device-coordinates are not a natural system of
##numbers for use by humans.  Imagine that the paddles in the previous
##chapters exist in real life, and are 20 meters wide and 60 meters tall.
##The graphics programmer should be able to use those numbers directly;
##they shouldn't have to manually trasform the distances into normalized-device-coordinates.
##
##Whatever a convenient numbering system is (i.e. coordinate system) for modeling objects
##is called "model-space".  Since a paddle has four corners, which corner should be a
##the origin (0,0)?  If you don't already know what you want at the origin, then
##none of the corners should be; instead put the center of the object
##at the originfootnote:[By putting the center of the object at the origin,
##scaling and rotating the object are trivial].

##image:modelspace.png[align="center",title="Foo"]


##[source,Python,linenums]
##----
paddle1.globalPosition = Vertex(-90.0,0.0)
paddle1.vertices=[Vertex(x=-10.0, y=-30.0),
                  Vertex(x= 10.0, y=-30.0),
                  Vertex(x= 10.0, y=30.0),
                  Vertex(x=-10.0, y=30.0)]

paddle2.globalPosition = Vertex(90.0,0.0)
paddle2.vertices = [Vertex(x=-10.0, y=-30.0),
                    Vertex(x= 10.0, y=-30.0),
                    Vertex(x= 10.0, y=30.0),
                    Vertex(x=-10.0, y=30.0)]

def draw(self):
    glColor3f(self.r,
              self.g,
              self.b)

    glBegin(GL_QUADS)
    for modelspace in self.vertices:
        worldSpace = modelspace.translate(tx=self.globalPosition.x,
                                          ty=self.globalPosition.y) \
                               .translate(tx=0.0,
                                          ty=self.offsetY)

        ndcSpace = worldSpace.scale(x=1.0/100.0,
                                    y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()
Paddle.draw = draw
##----

##Model-space to World-space.

##You can view the transformations from first transformation to last,
##where all transformations happen relative to the world-space origin.
##(this works well for world-space to camera-space,
##but not so well for model-space transformations)

##image:translation2F.gif[align="center",title="Foo"]


##Instead, for model-space to world-space transformations (and for these transformations only),
##it's easier to read the transformations backwards, where the transformations
##aren't relative to the global origin, instead it's from the local frame of reference.


##image:translation2B.gif[align="center",title="Foo"]



##Why do the two different views of the transformations matter?  In model-space
##to world-space transformations, especially once rotation and scaling of model-space
##is used, it allows the programmer to forget about most details, just specify
##where new objects are relative to that which you are already drawing.

##With that said, that doesn't mean that reading the transformations front to back
##has no value.  But it only has value in world-space to camera-space conversions,
##and from camera-space to ndc-space.

##This will make more sense once rotation is involved.




##=== Scaling

##image:scale.png[align="center",title="Foo"]

##
##Similarly, we can expand or shrink the size of an object
##by "scale"ing each of the vertices of the object, assuming
##the object's center is at (0,0).


##[source,Python,linenums]
##----
# add scale method to Vertex
def scale(self, x, y):
    return Vertex(x=self.x * x, y=self.y * y)
Vertex.scale = scale
##----

##image:modelspacePaddle7.png[align="center",title="Foo"]

#World-space to NDC-space.

##image:modelspacePaddle8.png[align="center",title="Foo"]



##[source,Python,linenums]
##----
def handle_movement_of_paddles():
    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.offsetY -= 10.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.offsetY += 10.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.offsetY -= 10.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.offsetY += 10.0
inputHandlers = []
inputHandlers.append(handle_movement_of_paddles)
##----


##[source,Python,linenums]
##----
@registerDemo
def demo6():
    draw_in_square_viewport()
    handle_inputs()
    paddle1.draw()
    paddle2.draw()
##----

##=== Rotation Around Origin (0,0)
##
##We can also rotate an object around (0,0) by rotating
##all of the object's vertices around (0,0).  Although defined now,
##this won't
##be used until later.

##In high school math, you will have learned about sin, cos, and tangent.
##Typically the angles are described on the unit circle, where a rotation
##starts from the positive x axis.  We can expand on this knowledge, allowing
##us to rotate a given vertex around the origin (0,0).  This is done
##by separating the x and y value, rotating each of them seperately,
##and then adding the results together.

##That might not have been fully clear.  Let me try again.
##The vertex (0.5,0.4) can be separated into two vertices, (0.5,0) and (0,0.4).

##image:rotate3.png[align="center",title="Foo"]

##image:rotate4.png[align="center",title="Foo"]


##These vertices can be added together to create the original vertex.
##But, before we do that, let's rotate each of the vertices.
##
##(0.5,0) is on the x-axis, so rotating it by "angle" degrees, results
##in vertex (0.5*cos(angle), 0.5*sin(angle)).  Notice that both the x and
##y values are multiplied by 0.5.  This is because rotations should not affect
##the distance of the point from the origin (0,0).  (0.5,0) has length 0.5.
##(cos(angle), sin(angle) has length 1. By multipling both the x and y
##component by 0.5, we are scaling the vertex back to its original distance
##from the origin.

##image:rotate.png[align="center",title="Foo"]

##(0,0.4) is on the y-axis, so rotating it by "angle" degrees, results
##in vertex (0.4*-sin(angle), 0.4*cos(angle)).

##image:rotate2.png[align="center",title="Foo"]

##Wait.  Why is negative
##sin applied to the angle to make the x value, and cos applied to angle to make the y value?
##Trigonometric operations such as sin, cos, and tangent assume that the rotation is happening on
##the unit circle, starting from (1,0) on the x axis.  Since we want
##to rotate an angle starting from (0,1) on the y axis, we sin and
##cos must be swapped.  Sin is positive from 0 to 90 degrees, but
##we want a negative value for our rotation of the y axis since the rotation is happening counter-clockwise,
##hence the negative sin.
##


##After the rotations have been applied, sum the results to
##get your vertex rotated around the origin!

##(0.5*cos(angle), 0.5*sin(angle)) + (0.4*-sin(angle), 0.4*cos(angle)) =
##(0.5*cos(angle) + 0.4*-sin(angle), 0.5*sin(angle) + 0.4*cos(angle))




##[source,Python,linenums]
##----
paddle1.rotation = 0.0
paddle2.rotation = 0.0
##----





##[source,Python,linenums]
##----
# add rotate method to Vertex
def rotate(self,angle_in_radians):
    return Vertex(x= self.x * math.cos(angle_in_radians) - self.y * math.sin(angle_in_radians),
                  y= self.x * math.sin(angle_in_radians) + self.y * math.cos(angle_in_radians))
Vertex.rotate = rotate
##----


##== Rotate the Paddles About their Center
##
##[width="75%",options="header,footer"]
##|=======================================
##|Keyboard Input |Action
##|w              |Move Left Paddle Up
##|s              |Move Left Paddle Down
##|k              |Move Right Paddle Up
##|i              |Move Right Paddle Down
##|               |
##|*d*              |*Increase Left Paddle's Rotation*
##|*a*              |*Decrease Left Paddle's Rotation*
##|*l*              |*Increase Right Paddle's Rotation*
##|*j*              |*Decrease Right Paddle's Rotation*
##|=======================================

### TODO - describe angle as radians
### TODO - show unit circle
### TODO - show orthonormal basis
### TODO - show basic proof of rotate

##[source,Python,linenums]
##----
def handle_paddle_rotations():
    global paddle_1_rotation, paddle_2_rotation

    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        paddle1.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        paddle1.rotation -= 0.1
    if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
        paddle2.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_L) == glfw.PRESS:
        paddle2.rotation -= 0.1
inputHandlers.append(handle_paddle_rotations)
##----


##[source,Python,linenums]
##----
def draw(self):
    glColor3f(self.r,
              self.g,
              self.b)

    glBegin(GL_QUADS)
    for modelspace in self.vertices:
        worldSpace = modelspace.translate(tx=self.globalPosition.x,
                                          ty=self.globalPosition.y) \
                               .translate(tx=0.0,
                                          ty=self.offsetY) \
                               .rotate(self.rotation)
        ndcSpace = worldSpace.scale(x=1.0/100.0,
                                    y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()
Paddle.draw = draw

@registerDemo
def demo7():
    draw_in_square_viewport()
    handle_inputs()

    paddle1.draw()
    paddle2.draw()
##----

##TODO - Explain how this does not do what we want.  Show example graphs.



##[source,Python,linenums]
##----
# add rotate around method to Vertex
def rotate_around(self, angle_in_radians, center):
    translateToCenter = self.translate(tx=-center.x,
                                       ty=-center.y)
    rotatedAroundOrigin = translateToCenter.rotate(angle_in_radians)
    backToCenter = rotatedAroundOrigin.translate(tx=center.x,
                                                 ty=center.y)
    return backToCenter
Vertex.rotate_around = rotate_around
##----


##[source,Python,linenums]
##----
def draw(self):
    glColor3f(self.r,
              self.g,
              self.b)

    glBegin(GL_QUADS)
    for modelspace in self.vertices:
        rotatePoint = Vertex(0.0,0.0).translate(tx=self.globalPosition.x,
                                                ty=self.globalPosition.y) \
                                     .translate(tx=0.0,
                                                ty=self.offsetY)
        worldSpace = modelspace.translate(tx=self.globalPosition.x,
                                          ty=self.globalPosition.y) \
                                .translate(tx=0.0,
                                           ty=self.offsetY)
        worldSpace = worldSpace.rotate_around(self.rotation, rotatePoint)
        ndcSpace = worldSpace.scale(x=1.0/100.0,
                                    y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()
Paddle.draw = draw

@registerDemo
def demo8():
    draw_in_square_viewport()
    handle_inputs()

    paddle1.draw()
    paddle2.draw()

##----


## TODO - explain that translate each points and the origin.  We then rotate around the new origin
## by translating back to the global origin, doing the rotation, and then redoing the translation.
## Regardless of the inefficiency of this calculation, it should be clear to the reader
## that we are not thinking about this correctly.  The initial translate is effectively canceled out,
## leaving a rotation and then a translation.

##[source,Python,linenums]
##----
def draw(self):
    glColor3f(self.r,
              self.g,
              self.b)

    glBegin(GL_QUADS)
    for modelspace in self.vertices:
        worldSpace = modelspace.rotate(self.rotation) \
                               .translate(tx=self.globalPosition.x,
                                          ty=self.globalPosition.y) \
                               .translate(tx=0.0,
                                          ty=self.offsetY)

        ndcSpace = worldSpace.scale(x=1.0/100.0,
                                    y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()
Paddle.draw = draw
##----


##[source,Python,linenums]
##----
def draw(self):
    glColor3f(self.r,
              self.g,
              self.b)

    glBegin(GL_QUADS)
    for modelspace in self.vertices:
        worldSpace = modelspace.rotate(self.rotation) \
                               .translate(tx=self.globalPosition.x,
                                          ty=self.globalPosition.y) \
                               .translate(tx=0.0,
                                          ty=self.offsetY)

        ndcSpace = worldSpace.scale(x=1.0/100.0,
                                    y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()
Paddle.draw = draw


@registerDemo
def demo9():
    draw_in_square_viewport()
    handle_inputs()

    paddle1.draw()
    paddle2.draw()
##----


##image:rotation1F.gif[align="center",title="Foo"]

##image:rotation1B.gif[align="center",title="Foo"]





##== Camera Management
##
##[width="75%",options="header,footer"]
##|=======================================
##|Keyboard Input |Action
##|w              |Move Left Paddle Up
##|s              |Move Left Paddle Down
##|k              |Move Right Paddle Up
##|i              |Move Right Paddle Down
##|               |
##|d              |Increase Left Paddle's Rotation
##|a              |Decrease Left Paddle's Rotation
##|l              |Increase Right Paddle's Rotation
##|j              |Decrease Right Paddle's Rotation
##|               |
##|*UP*             |*Move the Camera Up*
##|*DOWN*           |*Move the Camera Down*
##|*LEFT*           |*Move the Camera Left*
##|*RIGHT*          |*Move the Camera Right*
##|=======================================
##[source,C,linenums]
# TODO - describe implicit camera at origin, and making it's location explicit
# TODO - descriibe desire for moving camera


##[source,Python,linenums]
##----
camera_x = 0.0
camera_y = 0.0
##----

##[source,Python,linenums]
##----
def handle_camera_movement():
    global camera_x, camera_y

    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera_y += 10.0
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera_y -= 10.0
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera_x -= 10.0
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera_x += 10.0
inputHandlers.append(handle_camera_movement)
##----


##[source,Python,linenums]
##----
def draw(self):
    glColor3f(self.r,
              self.g,
              self.b)

    glBegin(GL_QUADS)
    for modelspace in self.vertices:
        worldSpace = modelspace.rotate(self.rotation) \
                               .translate(tx=self.globalPosition.x,
                                          ty=self.globalPosition.y) \
                               .translate(tx=0.0,
                                          ty=self.offsetY)

        cameraSpace = worldSpace.translate(tx=-camera_x,
                                           ty=-camera_y)
        ndcSpace = cameraSpace.scale(x=1.0/100.0,
                                     y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()
Paddle.draw = draw

@registerDemo
def demo10():
    draw_in_square_viewport()
    handle_inputs()

    paddle1.draw()
    paddle2.draw()
##----


##== Relative Objects
##
##[width="75%",options="header,footer"]
##|=======================================
##|Keyboard Input |Action
##|w              |Move Left Paddle Up
##|s              |Move Left Paddle Down
##|k              |Move Right Paddle Up
##|i              |Move Right Paddle Down
##|               |
##|d              |Increase Left Paddle's Rotation
##|a              |Decrease Left Paddle's Rotation
##|l              |Increase Right Paddle's Rotation
##|j              |Decrease Right Paddle's Rotation
##|               |
##|UP             |Move the Camera Up
##|DOWN           |Move the Camera Down
##|LEFT           |Move the Camera Left
##|RIGHT          |Move the Camera Right
##|               |
##|=======================================


##[source,Python,linenums]
##----
square = [Vertex(x=-5.0, y=-5.0),
          Vertex(x= 5.0, y=-5.0),
          Vertex(x= 5.0, y= 5.0),
          Vertex(x=-5.0, y= 5.0)]


@registerDemo
def demo11():
    draw_in_square_viewport()
    handle_inputs()

    paddle1.draw()

    # draw the square relative to paddle 1
    glColor3f(0.0, #r
              0.0, #g
              1.0) #b
    glBegin(GL_QUADS)
    for modelspace in square:
        worldSpace = modelspace.translate(tx=20.0, ty=0.0) \
                               .rotate(paddle1.rotation) \
                               .translate(tx=paddle1.globalPosition.x,
                                          ty=paddle1.globalPosition.y) \
                               .translate(tx=paddle1.offsetX,
                                          ty=paddle1.offsetY)
        cameraSpace = worldSpace.translate(tx=-camera_x,
                                           ty=-camera_y)
        ndcSpace = cameraSpace.scale(x=1.0/100.0,
                                     y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()

    paddle2.draw()
##----

##== Rotate the Square About Its Origin
##
##[width="75%",options="header,footer"]
##|=======================================
##|Keyboard Input |Action
##|w              |Move Left Paddle Up
##|s              |Move Left Paddle Down
##|k              |Move Right Paddle Up
##|i              |Move Right Paddle Down
##|               |
##|d              |Increase Left Paddle's Rotation
##|a              |Decrease Left Paddle's Rotation
##|l              |Increase Right Paddle's Rotation
##|j              |Decrease Right Paddle's Rotation
##|               |
##|UP             |Move the Camera Up
##|DOWN           |Move the Camera Down
##|LEFT           |Move the Camera Left
##|RIGHT          |Move the Camera Right
##|               |
##|*q*              |*Rotate the square around its center.*
##|=======================================

##[source,Python,linenums]
##----
square_rotation = 0.0
##----

##[source,Python,linenums]
##----
def handle_square_rotation():
    global square_rotation
    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square_rotation += 0.1
inputHandlers.append(handle_square_rotation)
##----


##[source,Python,linenums]
##----
@registerDemo
def demo12():
    draw_in_square_viewport()
    handle_inputs()
##----

##Handle the rotation.


##[source,Python,linenums]
##----
    paddle1.draw()

    glColor3f(0.0, #r
              0.0, #g
              1.0) #b
    glBegin(GL_QUADS)
    for modelspace in square:
        worldSpace = modelspace.rotate(square_rotation) \
                               .translate(tx=20.0, ty=0.0) \
                               .rotate(paddle1.rotation) \
                               .translate(tx=paddle1.globalPosition.x,
                                          ty=paddle1.globalPosition.y) \
                               .translate(tx=paddle1.offsetX,
                                          ty=paddle1.offsetY)

        cameraSpace = worldSpace.translate(tx=-camera_x,
                                           ty=-camera_y)
        ndcSpace = cameraSpace.scale(x=1.0/100.0,
                                     y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()

    paddle2.draw()
##----

##== Relative Rotation
##[width="75%",options="header,footer"]
##|=======================================
##|Keyboard Input |Action
##|w              |Move Left Paddle Up
##|s              |Move Left Paddle Down
##|k              |Move Right Paddle Up
##|i              |Move Right Paddle Down
##|               |
##|d              |Increase Left Paddle's Rotation
##|a              |Decrease Left Paddle's Rotation
##|l              |Increase Right Paddle's Rotation
##|j              |Decrease Right Paddle's Rotation
##|               |
##|UP             |Move the Camera Up
##|DOWN           |Move the Camera Down
##|LEFT           |Move the Camera Left
##|RIGHT          |Move the Camera Right
##|               |
##|q              |Rotate the square around its center
##|*e*              |*Rotate the square around the left paddle*
##|=======================================
##

##[source,C,linenums]
##----
rotationAroundPaddle1 = 0.0
##----


##[source,Python,linenums]
##----
def handle_relative_rotation():
    global rotationAroundPaddle1
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        rotationAroundPaddle1 += 0.1
inputHandlers.append(handle_relative_rotation)
##----

##[source,Python,linenums]
##----
@registerDemo
def demo13():
    draw_in_square_viewport()
    handle_inputs()
##----

##[source,Python,linenums]
##----
    paddle1.draw()

    glColor3f(0.0, #r
              0.0, #g
              1.0) #b
    glBegin(GL_QUADS)
    for modelspace in square:
        worldSpace = modelspace.rotate(square_rotation) \
                               .translate(tx=20.0, ty=0.0) \
                               .rotate(rotationAroundPaddle1) \
                               .rotate(paddle1.rotation) \
                               .translate(tx=paddle1.globalPosition.x,
                                          ty=paddle1.globalPosition.y) \
                               .translate(tx=paddle1.offsetX,
                                          ty=paddle1.offsetY)

        cameraSpace = worldSpace.translate(tx=-camera_x,
                                           ty=-camera_y)
        ndcSpace = cameraSpace.scale(x=1.0/100.0,
                                     y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()

    paddle2.draw()
##----


##== Adding Depth
##//TODO - discuss what the z component is, show graphs.
##//TODO - show X, Y, and Z rotations graphically with gnuplot.
##//TODO - make appendix for rotation around arbitrary axis
##[source,C,linenums]
##----
class Vertex3:
    def __init__(self,x,y,z):
        self.x = x
        self.y = y
        self.z = z

def translate(self, tx, ty, tz):
    return Vertex3(x=self.x + tx,
                   y=self.y + ty,
                   z=self.z + tz)
Vertex3.translate = translate


def rotateX(self, angle_in_radians):
    return Vertex3(x=self.x,
                   y=self.y*math.cos(angle_in_radians) - self.z*math.sin(angle_in_radians),
                   z=self.y*math.sin(angle_in_radians) + self.z*math.cos(angle_in_radians))
Vertex3.rotateX = rotateX

def rotateY(self, angle_in_radians):
    return Vertex3(x=self.z*math.sin(angle_in_radians) + self.x*math.cos(angle_in_radians),
                   y=self.y,
                   z=self.z*math.cos(angle_in_radians) - self.x*math.sin(angle_in_radians))
Vertex3.rotateY = rotateY

def rotateZ(self, angle_in_radians):
    return Vertex3(x=self.x*math.cos(angle_in_radians) - self.y*math.sin(angle_in_radians),
                   y=self.x*math.sin(angle_in_radians) + self.y*math.cos(angle_in_radians),
                   z=self.z)
Vertex3.rotateZ = rotateZ

def scale(self, scale_x, scale_y, scale_z):
    return Vertex3(x=self.x * scale_x,
                   y=self.y * scale_y,
                   z=self.z * scale_z)
Vertex3.scale = scale

def ortho(self,
          min_x,
          max_x,
          min_y,
          max_y,
          min_z,
          max_z):
    x_length = max_x-min_x
    y_length = max_y-min_y
    z_length = max_z-min_z
    return self.translate(tx=-(max_x-x_length/2.0),
		          ty=-(max_y-y_length/2.0),
		          tz=-(max_z-z_length/2.0)) \
               .scale(1/(x_length/2.0),
                      1/(y_length/2.0),
                      1/(-z_length/2.0))
Vertex3.ortho = ortho

# Install a key handler
# negate z length because it is already negative, and do not want to flip the data

##----

##[source,Python,linenums]
##----
paddle1.vertices = [Vertex3(x=-10.0, y=-30.0, z=0.0),
                    Vertex3(x= 10.0, y=-30.0, z=0.0),
                    Vertex3(x= 10.0, y= 30.0, z=0.0),
                    Vertex3(x=-10.0, y=30.0,  z=0.0)]
paddle2.vertices = paddle1.vertices

square = [Vertex3(x=-5.0, y=-5.0, z=0.0),
          Vertex3(x= 5.0, y=-5.0, z=0.0),
          Vertex3(x= 5.0, y= 5.0, z=0.0),
          Vertex3(x=-5.0, y=5.0,  z=0.0)]
##----


##== Moving the Camera in 3D

##[source,C,linenums]
##----
moving_camera_x = 0.0
moving_camera_y = 0.0
moving_camera_z = 40.0
moving_camera_rot_y = 0.0
moving_camera_rot_x = 0.0


def handle_3D_movement():
    global moving_camera_x
    global moving_camera_y
    global moving_camera_z
    global moving_camera_rot_x
    global moving_camera_rot_y

    move_multiple = 15.0
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        moving_camera_rot_y -= 0.03
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        moving_camera_rot_y += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_UP) == glfw.PRESS:
        moving_camera_rot_x += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_DOWN) == glfw.PRESS:
        moving_camera_rot_x -= 0.03;
##//TODO -  explaing movement on XZ-plane
##//TODO -  show camera movement in graphviz
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        moving_camera_x -= move_multiple * math.sin(moving_camera_rot_y)
        moving_camera_z -= move_multiple * math.cos(moving_camera_rot_y)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        moving_camera_x += move_multiple * math.sin(moving_camera_rot_y);
        moving_camera_z += move_multiple * math.cos(moving_camera_rot_y);


inputHandlers = []
inputHandlers.append(handle_movement_of_paddles)
inputHandlers.append(handle_paddle_rotations)
inputHandlers.append(handle_square_rotation)
inputHandlers.append(handle_relative_rotation)

inputHandlers.append(handle_3D_movement)


##----

##[source,Python,linenums]
##----
def cameraSpaceToNDCSpaceFn(self):
    return self.ortho(min_x= -100.0,
                      max_x= 100.0,
                      min_y= -100.0,
                      max_y= 100.0,
                      min_z= 100.0,
                      max_z= -100.0)
Vertex3.cameraSpaceToNDCSpaceFn = cameraSpaceToNDCSpaceFn
##----


##[source,Python,linenums]
##----
def draw(self):
    glColor3f(self.r,
              self.g,
              self.b)

    glBegin(GL_QUADS)
    for modelspace in self.vertices:
        worldSpace = modelspace.rotateZ(self.rotation) \
                               .translate(tx=self.globalPosition.x,
                                          ty=self.globalPosition.y,
                                          tz=0.0) \
                               .translate(tx=0.0,
                                          ty=self.offsetY,
                                          tz=0.0)

        cameraSpace = worldSpace.translate(tx=-moving_camera_x,
                                           ty=-moving_camera_y,
                                           tz=-moving_camera_z) \
                                .rotateY( -moving_camera_rot_y) \
                                .rotateX( -moving_camera_rot_x)
        ndcSpace = cameraSpace.cameraSpaceToNDCSpaceFn()
        glVertex3f(ndcSpace.x,
                   ndcSpace.y,
                   ndcSpace.z)
    glEnd()
Paddle.draw = draw


@registerDemo
def demo14():
    draw_in_square_viewport()
    handle_inputs()

##----


##// TODO -- draw_paddle_1 is still using only 2D, explain implicit 3D of z have 0 for a value
##Draw square, relative to paddle 1.
##[source,C,linenums]
##----
    paddle1.draw()

    glColor3f(0.0, #r
              0.0, #g
              1.0) #b
    glBegin(GL_QUADS)
    for modelspace in square:
        worldSpace = modelspace.rotateZ(square_rotation) \
                               .translate(tx=20.0, ty=0.0, tz=0.0) \
                               .rotateZ(rotationAroundPaddle1) \
                               .rotateZ(paddle1.rotation) \
                               .translate(tx=paddle1.globalPosition.x,
                                          ty=paddle1.globalPosition.y,
                                          tz=0.0) \
                               .translate(tx=paddle1.offsetX,
                                          ty=paddle1.offsetY,
                                          tz=-10.0) # TODO - explain why this should be visible

        cameraSpace = worldSpace.translate(tx=-moving_camera_x,
                                           ty=-moving_camera_y,
                                           tz=-moving_camera_z) \
                                .rotateY( -moving_camera_rot_y) \
                                .rotateX( -moving_camera_rot_x)
        ndcSpace = cameraSpace.cameraSpaceToNDCSpaceFn()
        glVertex3f(ndcSpace.x,
                   ndcSpace.y,
                   ndcSpace.z)
    glEnd()

    paddle2.draw()
##----


####TODO - discuss the framebuffer, and how it allows us to draw in
####       a depth-independent manner.  we could force the programmer
####       to sort objects by depth before drawing, but that's why mario64
####       looked good and crash bandicoot had limited perspectives.
####       also reference the section in the beginning which clears the
####       depth buffer.


##Set the default depth for all fragments
##[source,Python,linenums]
##----
glClearDepth(-1.0)
##----
##Set the depth test for all fragments.
##[source,Python,linenums]
##----
glDepthFunc(GL_GREATER)
##----


##[source,Python,linenums]
##----
# for all demos from now on, actually use the depth test
glEnable(GL_DEPTH_TEST)

@registerDemo
def demo15():
    demo14()
##----

####TODO - write something about how "now that depth testing is enabled for all subequent demos, rerun the##//vious demo to show that the square becomes hidden as the user navigates


##[source,Python,linenums]
##----
moving_camera_x = 0.0
moving_camera_y = 0.0
moving_camera_z = 400.0
moving_camera_rot_y = 0.0
moving_camera_rot_x = 0.0

def perspective(self, nearZ, farZ):
    field_of_view =  math.radians(45.0/2.0)
    width, height = glfw.get_framebuffer_size(window)
    y_angle =  (width / height) * field_of_view


    sheared_x = self.x / math.fabs(self.z) * math.fabs(nearZ)
    sheared_y = self.y / math.fabs(self.z) * math.fabs(nearZ)
    projected =  Vertex3(sheared_x,
			 sheared_y,
			 self.z)

    x_min_of_box = math.fabs(nearZ) * math.tan(field_of_view)
    y_min_of_box = math.fabs(nearZ) * math.tan(y_angle)
    return projected.ortho(min_x= -x_min_of_box,
			   max_x= x_min_of_box,
                           min_y= -y_min_of_box,
			   max_y= y_min_of_box,
                           min_z= nearZ,
			   max_z= farZ)
Vertex3.perspective = perspective

##----


##[source,Python,linenums]
##----
def cameraSpaceToNDCSpaceFn(self):
    return self.perspective(-0.1, -10000.0)
Vertex3.cameraSpaceToNDCSpaceFn = cameraSpaceToNDCSpaceFn
##----

##[source,Python,linenums]
##----

@registerDemo
def demo16():
    demo15()
##----


#### TODO -- add in notion of matrix stacks
