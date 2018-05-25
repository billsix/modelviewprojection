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
##(C) 2017, William Emerison Six. The source, and the generated book, are free under the MIT licence

##[[basics]]
##== Basics
##
##
##The device attached to a computer which displays information to the user is called a *monitor*.
##The monitor is composed of a two-dimensional array of light-emitting elements called *pixel*.
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
##keyboard input, controller inputfootnote:[tested with a wired XBox 360 controller], and
##to load images from the filesystem.
##
##Much of the code listed from here until section<<the-event-loop>> will be of little interest upon first reading.
##As such, the reader may choose to skip ahead to section<<the-event-loop>> now.
##
##The code for the entire book is available at https:##github.com/billsix/modelviewprojection,
##contained within "src/main.cpp". The code, but not the contents of the book, is licenced
##using the open-source Apache 2.0 license.
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
from glfw.glfw import *
import ctypes


if __name__ != '__main__':
    sys.exit(1)

print("Which Chapter would you like to execute?")
chapterNumber = input()

## TODO - explain these decorators or move them somewhere else
# - if the user selected this demo, then run it now.
# this way, overridden/updated functions do not affect this
# demo
def demoNumber(theDemoNumber):
    def actualDecorator(F):
        if int(chapterNumber) == theDemoNumber:
            global render_scene
            render_scene = F
            main_loop()
            sys.exit(0)
        else:
            return F
    return actualDecorator

# Append function F to the list of callables called
# on handling input
def inputHandler(F):
    global handle_inputs
    try:
        handle_inputs
    except Exception:
        return F

    oldHandler = handle_inputs
    def chainThem():
        oldHandler()
        F()
    return chainThem

##----

##==== GLFW/OpenGL Initialization
##
##-Initialize GLFW.
##[source,Python,linenums]
##----
if not glfwInit():
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
glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR,1)
glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR,4)
##----

##Create a 500 pixel by 500 pixel window, which the user can resize.
##[source,Python,linenums]
##----
window = glfwCreateWindow(500,
                          500,
                          str.encode("pyNuklear demo - GLFW OpenGL2"),
                          None,
                          None)
if not window:
    glfwTerminate()
    sys.exit()
##----

##[source,Python,linenums]
##----
# Make the window's context current
glfwMakeContextCurrent(window)

# Install a key handler
def on_key(window, key, scancode, action, mods):
    if key == GLFW_KEY_ESCAPE and action == GLFW_PRESS:
        glfwSetWindowShouldClose(window,1)
glfwSetKeyCallback(window, on_key)
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
glEnable(GL_DEPTH_TEST)

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
    while not glfwWindowShouldClose(window):
        # Poll for and process events
        glfwPollEvents()

        width, height = glfwGetFramebufferSize(window)
        glViewport(0, 0, width, height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
##----

##=== Render the Selected Demo
##
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

##==== The User Closed the App, Exit Cleanly.
        # done with frame, flush and swap buffers
        # Swap front and back buffers
##[source,Python,linenums]
##----
        glfwSwapBuffers(window)

    glfwTerminate()
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
##run the compile the program and run the demos.  To do so, the source
##code for this book may be obtained at https:##github.com/billsix/modelviewprojection.
##It has been tested on Windows 10 (Visual Studio Community 2017),
##Linux, and OS X.
##
##Once built, execute "modelviewprojection". When prompted, type "2" and then press the "Enter" key.
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
@demoNumber(1)
def demo1():
    # The baseline behavior.  A black screen.
    pass
##----

##When this code returns, the event loop flushes (i.e) sends the frame to the monitor.  Since
##no geometry was drawn, the color value for each pixel is still black.
##
##Each color is represende by a number, so the frame is something like this:
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
##so lets make the first paddle white, and a second paddle yellow.
##
##"glBegin(GL_QUADS)" tells OpenGL that we will soon specify 4 *vertices*,
##(i.e. points) which define the
##quadrilateral.  The vertices will be specified by calling "glVertex2f" 4 times.


##[source,Python,linenums]
##----
@demoNumber(2)
def demo2():
##----

##Draw paddle 1.

##[source,Python,linenums]
##----
    glColor3f(1.0, #r
              1.0, #g
              1.0) #b
    glBegin(GL_QUADS)
    glVertex2f(-1.0, #x
               -0.3) #y
    glVertex2f(-0.8, #x
               -0.3) #y
    glVertex2f(-0.8, #x
               0.3)  #y
    glVertex2f(-1.0, #x
               0.3)  #y
    glEnd();
##----

##"glEnd()" tells OpenGL that we have finished providing vertices for
##the begun quadrilateral.
##

##The framebuffer, which has not yet been flushed to the monitor, has geometry which looks like this:

##image:plot1.png[align="center",title="Foo"]


##Draw paddle 2.


##[source,Python,linenums]
##----
    glColor3f(1.0,
              1.0,
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
##wwwwwbbbbbbbbbbbbbbbbbbbbbbbbbbbyyyyy
##wwwwwbbbbbbbbbbbbbbbbbbbbbbbbbbbyyyyy
##wwwwwbbbbbbbbbbbbbbbbbbbbbbbbbbbyyyyy
##wwwwwbbbbbbbbbbbbbbbbbbbbbbbbbbbyyyyy
##wwwwwbbbbbbbbbbbbbbbbbbbbbbbbbbbyyyyy
##wwwwwbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
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
    glClear(GL_COLOR_BUFFER_BIT);
##----

##[source,Python,linenums]
##----
    width, height = glfwGetFramebufferSize(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
##----

##[source,Python,linenums]
##----
    min = width if width < height else height

    glViewport(int(0.0 + (width - min)/2.0),  #min x
               int(0.0 + (height - min)/2.0), #min y
               min,                           #width x
               min)                           #width y

    glEnable(GL_SCISSOR_TEST);
    glScissor(int(0.0 + (width - min)/2.0),  #min x
              int(0.0 + (height - min)/2.0), #min y
              min,                           #width x
              min)                           #width y
##----

##[source,Python,linenums]
##----
    glClearColor(0.0, #r
                 0.0, #g
                 0.0, #b
                 1.0) #a
    glClear(GL_COLOR_BUFFER_BIT);
    glDisable(GL_SCISSOR_TEST);
##----


##=== Set the viewport, and then execute the code from chapter 3.


##[source,Python,linenums]
##----
@demoNumber(3)
def demo3():
    draw_in_square_viewport()
    demo2()
##----

##Yes, the author is aware that "goto" statements are frowned upon.
##But would the reader prefer for chapter 3's code to be duplicated here?

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
##Static variables are initialized to a value only the first time the procedure is executed.
##In subsequent calls to "render_scene", they retain the value they had the last time
##"render_scene" was calledfootnote:[Since the rest of the demos are entirely defined
##within "render_scene", all statically defined variables, such as these offsets, are
##available to every demo, and as such, future demos will reference these values].


##[source,Python,linenums]
##----
paddle_1_offset_Y = 0.0;
paddle_2_offset_Y = 0.0;

@inputHandler
def handle_inputs():
    global paddle_1_offset_Y, paddle_2_offset_Y

    if glfwGetKey(window, GLFW_KEY_S) == GLFW_PRESS:
        paddle_1_offset_Y -= 0.1
    if glfwGetKey(window, GLFW_KEY_W) == GLFW_PRESS:
        paddle_1_offset_Y += 0.1
    if glfwGetKey(window, GLFW_KEY_K) == GLFW_PRESS:
        paddle_2_offset_Y -= 0.1
    if glfwGetKey(window, GLFW_KEY_I) == GLFW_PRESS:
        paddle_2_offset_Y += 0.1
##----



##-If 's' is pressed this frame, subtract 0.1 more from paddle_1_offset_Y.  If the
##key continues to be held down over time, paddle_1_offset_Y will continue to decrease.

##-If 'w' is pressed this frame, add 0.1 more to paddle_1_offset_Y.

##-If 'k' is pressed this frame, subtract 0.1 more from paddle_2_offset_Y.

##-If 'i' is pressed this frame, add 0.1 more to paddle_2_offset_Y.

##Remember, these are static variables, so changes to these variables will
##accumulate across frames.
##


##[source,Python,linenums]
##----
@demoNumber(4)
def demo4():
    draw_in_square_viewport()
    handle_inputs()
##----

##Draw paddle 1, relative to the world-space origin.
##Add paddle_1_offset_Y to the "y" component of every vertex

##[source,Python,linenums]
##----
    glColor3f(1.0, #r
              1.0, #g
              1.0) #b
    glBegin(GL_QUADS)
    glVertex2f(-1.0, #x
               -0.3+paddle_1_offset_Y) #y
    glVertex2f(-0.8, #x
               -0.3+paddle_1_offset_Y) #y
    glVertex2f(-0.8, #x
               0.3+paddle_1_offset_Y)  #y
    glVertex2f(-1.0, #x
               0.3+paddle_1_offset_Y)  #y
    glEnd();
##----

##image:plot3.png[align="center",title="Foo"]


##Draw paddle 2, relative to the world-space origin.
##Add paddle_2_offset_Y to the "y" component of every vertex


##[source,Python,linenums]
##----
    glColor3f(1.0,
              1.0,
              0.0)
    glBegin(GL_QUADS)

    glVertex2f(0.8,
               -0.3+paddle_2_offset_Y)
    glVertex2f(1.0,
               -0.3+paddle_2_offset_Y)
    glVertex2f(1.0,
               0.3+paddle_2_offset_Y)
    glVertex2f(0.8,
               0.3+paddle_2_offset_Y)
    glEnd()
##----

##image:plot4.png[align="center",title="Foo"]


##== Model Vertices with a Data-Structure
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
##of computer graphics.  So create a class for common transformations.


##[source,Python,linenums]
##----
class Vertex:
    def __init__(self,x,y):
        self.x = x
        self.y = y
##----

##=== Translation
##Rather than incrementing y values before calling "glVertex",
##instead call "translate" on the vertex.

##image:translate.png[align="center",title="Foo"]


##[source,Python,linenums]
##----
# add translate method to Vertex
def translate(self, x, y):
    return Vertex(x=self.x + x, y=self.y + y)
Vertex.translate = translate
##----


##[source,Python,linenums]
##----
paddle = [Vertex(x=-0.1, y=-0.3),
          Vertex(x= 0.1, y=-0.3),
          Vertex(x= 0.1, y=0.3),
          Vertex(x=-0.1, y=0.3)]
##----


##[source,Python,linenums]
##----
@demoNumber(5)
def demo5():
    draw_in_square_viewport()
    handle_inputs()
##----
##Draw paddle 1, relative to the world-space origin.
##[source,Python,linenums]
##----
    glColor3f(1.0, #r
              1.0, #g
              1.0) #b
    glBegin(GL_QUADS)
    for v in paddle:
        newPosition = v.translate(x=-0.9,
                                  y=paddle_1_offset_Y);
        glVertex2f(newPosition.x,
                   newPosition.y)
    glEnd()
##----

##Draw paddle 2, relative to the world-space origin.
##[source,Python,linenums]
##----
    glColor3f(1.0, #r
              1.0, #g
              0.0) #b
    glBegin(GL_QUADS)
    for v in paddle:
        newPosition = v.translate(x=0.9,
                                  y=paddle_2_offset_Y);
        glVertex2f(newPosition.x,
                      newPosition.y)
    glEnd()
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
paddle = [Vertex(x=-10.0, y=-30.0),
          Vertex(x= 10.0, y=-30.0),
          Vertex(x= 10.0, y=30.0),
          Vertex(x=-10.0, y=30.0)]
##----

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


##[source,Python,linenums]
##----
@inputHandler
def handle_inputs():
    global paddle_1_offset_Y, paddle_2_offset_Y

    if glfwGetKey(window, GLFW_KEY_S) == GLFW_PRESS:
        paddle_1_offset_Y -= 10.0
    if glfwGetKey(window, GLFW_KEY_W) == GLFW_PRESS:
        paddle_1_offset_Y += 10.0
    if glfwGetKey(window, GLFW_KEY_K) == GLFW_PRESS:
        paddle_2_offset_Y -= 10.0
    if glfwGetKey(window, GLFW_KEY_I) == GLFW_PRESS:
        paddle_2_offset_Y += 10.0
##----


##[source,Python,linenums]
##----
@demoNumber(6)
def demo6():
    draw_in_square_viewport()
    handle_inputs()
##----
##[source,Python,linenums]
##----
    glColor3f(1.0, #r
              1.0, #g
              1.0) #b
    glBegin(GL_QUADS)
    for modelspace in paddle:
        worldSpace = modelspace.translate(x=-90.0,
                                          y=paddle_1_offset_Y);
        ndcSpace = worldSpace.scale(x=1.0/100.0,
                                    y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()
##----

##[source,Python,linenums]
##----
    glColor3f(1.0, #r
              1.0, #g
              0.0) #b
    glBegin(GL_QUADS)
    for modelspace in paddle:
        worldSpace = modelspace.translate(x=90.0,
                                          y=paddle_2_offset_Y);
        ndcSpace = worldSpace.scale(x=1.0/100.0,
                                    y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()
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
paddle_1_rotation = 0.0
paddle_2_rotation = 0.0
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

#### TODO - describe angle as radians
#### TODO - show unit circle
#### TODO - show orthonormal basis
#### TODO - show basic proof of rotate

##[source,Python,linenums]
##----
@inputHandler
def handle_inputs():
    global paddle_1_rotation, paddle_2_rotation

    if glfwGetKey(window, GLFW_KEY_A) == GLFW_PRESS:
        paddle_1_rotation += 0.1;
    if glfwGetKey(window, GLFW_KEY_D) == GLFW_PRESS:
        paddle_1_rotation -= 0.1;
    if glfwGetKey(window, GLFW_KEY_J) == GLFW_PRESS:
        paddle_2_rotation += 0.1;
    if glfwGetKey(window, GLFW_KEY_L) == GLFW_PRESS:
        paddle_2_rotation -= 0.1;
##----


##[source,Python,linenums]
##----
@demoNumber(7)
def demo7():
    draw_in_square_viewport()
    handle_inputs()
##----
##[source,Python,linenums]
##----
    glColor3f(1.0, #r
              1.0, #g
              1.0) #b
    glBegin(GL_QUADS)
    for modelspace in paddle:
        worldSpace = modelspace.rotate(paddle_1_rotation) \
                               .translate(x=-90.0,
                                          y=paddle_1_offset_Y);
        ndcSpace = worldSpace.scale(x=1.0/100.0,
                                    y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()
##----

##[source,Python,linenums]
##----
    glColor3f(1.0, #r
              1.0, #g
              0.0) #b
    glBegin(GL_QUADS)
    for modelspace in paddle:
        worldSpace = modelspace.rotate(paddle_2_rotation) \
                               .translate(x=90.0,
                                          y=paddle_2_offset_Y);
        ndcSpace = worldSpace.scale(x=1.0/100.0,
                                    y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()

##----




##[source,Python,linenums]
##----
# add rotate around method to Vertex
def rotate_around(angle_in_radians, center):
    translateToCenter = translate(-center.x,
                                  -center.y)
    rotatedAroundOrigin = translateToCenter.rotate(angle_in_radians)
    backToCenter = rotatedAroundOrigin.translate(center.x,
                                                 center.y)
    return backToCenter

Vertex.rotate_around = rotate_around
##----


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
#### TODO - describe implicit camera at origin, and making it's location explicit
#### TODO - descriibe desire for moving camera


##[source,Python,linenums]
##----
camera_x = 0.0
camera_y = 0.0
##----

##[source,Python,linenums]
##----
@inputHandler
def handle_inputs():
    global camera_x, camera_y

    if glfwGetKey(window, GLFW_KEY_UP) == GLFW_PRESS:
        camera_y += 10.0
    if glfwGetKey(window, GLFW_KEY_DOWN) == GLFW_PRESS:
        camera_y -= 10.0
    if glfwGetKey(window, GLFW_KEY_LEFT) == GLFW_PRESS:
        camera_x -= 10.0
    if glfwGetKey(window, GLFW_KEY_RIGHT) == GLFW_PRESS:
        camera_x += 10.0
##----


##[source,Python,linenums]
##----
@demoNumber(8)
def demo8():
    draw_in_square_viewport()
    handle_inputs()
##----
##[source,Python,linenums]
##----
    glColor3f(1.0, #r
              1.0, #g
              1.0) #b
    glBegin(GL_QUADS)
    for modelspace in paddle:
        worldSpace = modelspace.rotate(paddle_1_rotation) \
                               .translate(x=-90.0,
                                          y=paddle_1_offset_Y);
        cameraSpace = worldSpace.translate(x=-camera_x,
                                           y=-camera_y)
        ndcSpace = cameraSpace.scale(x=1.0/100.0,
                                     y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()
##----

##[source,Python,linenums]
##----
    glColor3f(1.0, #r
              1.0, #g
              0.0) #b
    glBegin(GL_QUADS)
    for modelspace in paddle:
        worldSpace = modelspace.rotate(paddle_2_rotation) \
                               .translate(x=90.0,
                                          y=paddle_2_offset_Y);
        cameraSpace = worldSpace.translate(x=-camera_x,
                                           y=-camera_y)
        ndcSpace = cameraSpace.scale(x=1.0/100.0,
                                     y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()
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
##|=======================================

##[source,Python,linenums]
##----
def draw_paddle_1():
    glColor3f(1.0, #r
              1.0, #g
              1.0) #b
    glBegin(GL_QUADS)
    for modelspace in paddle:
        worldSpace = modelspace.rotate(paddle_1_rotation) \
                               .translate(x=-90.0,
                                          y=paddle_1_offset_Y);
        cameraSpace = worldSpace.translate(x=-camera_x,
                                           y=-camera_y)
        ndcSpace = cameraSpace.scale(x=1.0/100.0,
                                     y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()
##----

##[source,Python,linenums]
##----
def draw_paddle_2():
    glColor3f(1.0, #r
              1.0, #g
              0.0) #b
    glBegin(GL_QUADS)
    for modelspace in paddle:
        worldSpace = modelspace.rotate(paddle_2_rotation) \
                               .translate(x=90.0,
                                          y=paddle_2_offset_Y);
        cameraSpace = worldSpace.translate(x=-camera_x,
                                           y=-camera_y)
        ndcSpace = cameraSpace.scale(x=1.0/100.0,
                                     y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()

square = [Vertex(x=-5.0, y=-5.0),
          Vertex(x= 5.0, y=-5.0),
          Vertex(x= 5.0, y= 5.0),
          Vertex(x=-5.0, y= 5.0)]


@demoNumber(9)
def demo9():
    draw_in_square_viewport()
    handle_inputs()

    draw_paddle_1()


    glColor3f(0.0, #r
              0.0, #g
              1.0) #b
    glBegin(GL_QUADS)
    for modelspace in square:
        worldSpace = modelspace.translate(20.0, 0.0) \
                               .rotate(paddle_1_rotation) \
                               .translate(x=-90.0,
                                          y=paddle_1_offset_Y);
        cameraSpace = worldSpace.translate(x=-camera_x,
                                           y=-camera_y)
        ndcSpace = cameraSpace.scale(x=1.0/100.0,
                                     y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()

    draw_paddle_2()
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
square_rotation = 0.0;
##----

##[source,Python,linenums]
##----
@inputHandler
def handle_inputs():
    global square_rotation
    if glfwGetKey(window, GLFW_KEY_Q) == GLFW_PRESS:
        square_rotation += 0.1
##----


##[source,Python,linenums]
##----
@demoNumber(10)
def demo10():
    draw_in_square_viewport()
    handle_inputs()
##----

##Handle the rotation.


##[source,Python,linenums]
##----
    draw_paddle_1()

    glColor3f(0.0, #r
              0.0, #g
              1.0) #b
    glBegin(GL_QUADS)
    for modelspace in square:
        worldSpace = modelspace.rotate(square_rotation) \
                               .translate(20.0, 0.0) \
                               .rotate(paddle_1_rotation) \
                               .translate(x=-90.0,
                                          y=paddle_1_offset_Y);
        cameraSpace = worldSpace.translate(x=-camera_x,
                                           y=-camera_y)
        ndcSpace = cameraSpace.scale(x=1.0/100.0,
                                     y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()

    draw_paddle_2()
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
rotation_around_paddle_1 = 0.0;
##----


##[source,Python,linenums]
##----
@inputHandler
def handle_inputs():
    global rotation_around_paddle_1
    if glfwGetKey(window, GLFW_KEY_E) == GLFW_PRESS:
        rotation_around_paddle_1 += 0.1
##----

##[source,Python,linenums]
##----
@demoNumber(11)
def demo11():
    draw_in_square_viewport()
    handle_inputs()
##----

##[source,Python,linenums]
##----
    draw_paddle_1()

    glColor3f(0.0, #r
              0.0, #g
              1.0) #b
    glBegin(GL_QUADS)
    for modelspace in square:
        worldSpace = modelspace.rotate(square_rotation) \
                               .translate(20.0, 0.0) \
                               .rotate(rotation_around_paddle_1) \
                               .rotate(paddle_1_rotation) \
                               .translate(x=-90.0,
                                          y=paddle_1_offset_Y);
        cameraSpace = worldSpace.translate(x=-camera_x,
                                           y=-camera_y)
        ndcSpace = cameraSpace.scale(x=1.0/100.0,
                                     y=1.0/100.0)
        glVertex2f(ndcSpace.x,
                   ndcSpace.y)
    glEnd()

    draw_paddle_2()
##----
