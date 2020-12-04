.. Model View Projection documentation master file, created by
   sphinx-quickstart on Thu Dec  3 20:16:17 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Introduction
============

.. toctree::
   :maxdepth: 2
   :caption: Contents:



Learn how to build 3D graphics using math you already know.
This codebase demonstrates how to create objects, put
them where you want them to go, view the scene with a camera
that can move, and how to project that 3D data to a 2D screen.


For further information, such as lighting, shadows, and
OpenGL in more explicit detail, consult

#. OpenGL redbook/bluebook. (OpenGL superbible v4, because it covers fixed function and shaders)
#. Mathematics for 3D Game Programming and Computer Graphics
#. Computer Graphics: Principles and Practice in C (2nd Edition)

For RayTracing

#. Physically Based Rendering
#. Ray Tracing from the Ground Up


Approach
--------

This book uses "mistake-driven-development".  I show incrementally
how to build a more complex graphics application, making mistakes along
the way, and then fixing the mistakes.


Thoughout the book, I show how to place objects in space,
how to draw objects relative to other objects, how to add a
camera which moves over time based on user input, and how to transform all
the objects into the 2D pixel coordinates of the computer screen.
By the end of this book, you will understand the basics of
how to create first-person and third-person applications/games.
I made this book to show programmers how to make the kind
of graphics programs which they want to make, using
math they aleady know.

This book is purposely limited in scope, and
the applications produced are not particurly pretty nor realistic-looking.
For advanced graphics topics, you'll need to consult other references,
such as the OpenGL "red book" and "blue book".
Although this book fills a huge gap that other books do not address,
those other books are excellent reference books for advanced topics.



Required Software
-----------------

Bbefore running this code, you need a virtual environment,
with dependencies installed.

Visual Studio takes care of this for you, but on a Mac or
on Linux, run

.. code-block:: bash

   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip setuptools
   pip install -r requirements.txt


Windows
~~~~~~~

Use Visual Studio 2019 (Tested on community, but I'm sure it will work on others).

Linux
~~~~~

Install Python3, glfw via a package manager.  Use pip and virtualenv to install dependencies

Mac
~~~

Python Python3 (via anaconda, homebrew, macports, whatever), and use pip and virtualenv to install dependencies.


Opening a Window - Demo 01
==========================

Purpose
-------

Learn how to open a window, make a black screen, and close
the window.

Basics
------

The device attached to a computer which displays information to the user is called a *monitor*.

The monitor is composed of a two-dimensional array of light-emitting elements, each called a *pixel*.

At a given time, each individual pixel is instructed by the computer to display
one specific color, represented within the computer as a number.
The aggregate of the colors at each pixel at one moment in time, called a *frame*,
provides a picture that has some meaning to the human user.
# In OpenGL, the bottom left pixel of a window is coordinate (0,0).  The top right is (window_width,window_height)


.. figure:: _static/monitor.png
    :align: center
    :alt: 1024x768 monitor
    :figclass: align-center

    1024x768 monitor


.. figure:: _static/monitor2.png
    :align: center
    :alt: 1920x1200 monitor
    :figclass: align-center

    1920x1200 monitor




Frames are created within the computer and sent to the monitor
at a rate over time, called the *framerate*,
measured in *Hertz*.  By updating frames quickly and at a constant rate, the computer
provides the end-user with the illusion of motion.


Code
----

Import Python modules.  Python's modules are a way of distributing code
without namespace collisions

.. code-block:: Python

   import sys  # sys is imported, all function calls will be of sys.function
   import os  # basic operating system functions
   import numpy as np  # numpy is a fast math/matrix library.
   import math  # basic math utilities
   from OpenGL.GL import *  # here, we are importing OpenGL's submodule GL



But we will not need the module's prefix to call
the functions.  I did this for uniformity
with the C++ code in the Superbible book.

.. code-block:: Python

   import glfw  # the windowing library


On a Python prompt, you can use tab-complete to see which functions
are defined on a module.  you can also type help(modulename) (q is
used to quit out of the pager).  help works on any object, including modules.


Opening A Window
----------------

Desktop operating systems allow the user to run more than one
program at a time, where each program draws into a subsection of
the monitor called a window.


To create and to open a window in a cross-platform manner, this
book will call procedures provided by the widely-ported GLFW library (supporting Windows, macOS, Linux).
GLFW also provides procedures for receiving
keyboard input and for controller.


GLFW/OpenGL Initialization
--------------------------

Initialize GLFW.

.. code-block:: Python

     if not glfw.init():  # many objects can be treating as booleans,
         # and the Python keyword "not" negates it
         # Python does not use brackets to show nesting.
         # instead it uses whitespace.
         # You probably want to find keyboard shortcuts
         # to indent/unindent.  On Emacs, I use tab
         sys.exit()  # if you can't create a window, quit


One frame is created incrementally at a time on the CPU, but the frame
is sent to the monitor
only when frame is completely drawn, and each pixel has a color.
The act of sending the frame to the monitor is called *flushing*
the frame.
Flushing takes time,
and if the call to flush were to block (meaning it would not return control
back to the call-ing procedure until the flush is complete), we would
have wasted CPU time.  To avoid this,
OpenGL has two *framebuffers* (regions of memory which will eventually
contain the full data for a frame),
only one of which is "active", or writable, at a given time.
"glfwSwapBuffers" is a non-blocking call which initiates the flushing
the current buffer, and which switches the current writable framebuffer to the
other one, thus allowing the CPU to resume.  If this doesn't make
sense right now, don't worry.


Set the version of OpenGL

OpenGL has been around a long time, and has multiple, possibly incompatible versions.

.. code-block:: Python

     glfw.window_hint(
         glfw.CONTEXT_VERSION_MAJOR, 1
     )  # python methods normally use lower case
     # and words are seperated by underscores.
     glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)


Create a 500 pixel by 500 pixel window, which the user can resize.


.. code-block:: Python

     window = glfw.create_window(500, 500, "ModelViewProjection Demo 1", None, None)

None is the equivalent of null.
I frequently will put argument lists vertically, though it in not required.

If GLFW cannot open the window, quit.  Unlike MC Hammer, we are quite legit, yet still
able to quit.

.. code-block:: Python

     if not window:
         glfw.terminate()  # need to clean up gracefully
         sys.exit()


Make the window's context current


.. code-block:: Python

     glfw.make_context_current(window)

Install a key handler.


.. code-block:: Python

     def on_key(window, key, scancode, action, mods):
         if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
             glfw.set_window_should_close(window, 1)

     glfw.set_key_callback(window, on_key)


Functions are first class values in Python, and are objects just
like anything else.  The can be passed as arguments, for evaluation
later

For every frame drawn, each pixel has a default color, set by
calling "glClearColor". "0,0,0,1", means black "0,0,0", without
transparency (the "1").


.. code-block:: Python

     glClearColor(0.0, 0.0, 0.0, 1.0)


Don't worry about the 4 lines here.  Although they are necessary,
we will cover them later.

.. code-block:: Python

     glMatrixMode(GL_PROJECTION)
     glLoadIdentity()
     glMatrixMode(GL_MODELVIEW)
     glLoadIdentity()

The Event Loop
--------------

When you pause a movie, motion stops and you see one picture.
Movies are composed of sequence of pictures, when
rendered in quick succession, provide the illusion of motion.

Interactive computer graphics are rendered the same way,
one "frame" at a time.

Render a frame, flush the complete frame to the monitor.
Unless the user closed the window, repeat indefinitely.

The color of each pixel within
the current framebuffer
is reset to a default color.

When a graphics application is executing, it is creating new
frames (pictures) at some rate (e.g. 60 frames per second).  At any given
frame, the user of the application might do something, (e.g.
move the mouse, click, type on the keyboard, close the application).

At the beginning of every frame, ask GLFW if it received one
of these events since we last asked (i.e., the previous frame).


Loop until the user closes the window


.. code-block:: Python

     while not glfw.window_should_close(window):
         # Poll for and process events
         glfw.poll_events()

         # get the size of the framebuffer.  Python
         # allows the returning of multiple values
         # in the form of a tuple.  Assigning
         # to the variables this way is a form of "destructuring"
         width, height = glfw.get_framebuffer_size(window)
         glViewport(0, 0, width, height)
         # since the frame is about to be drawn, make it a blank slate.
         # the color of each pixel will be the clear color.
         # Programming in OpenGL is a bit different than normal programming,
         # in that individual function calls do not always do everything you need
         # in isolation.  Instead, they mutate state, which may require
         # multiple function calls to complete a certain task.
         glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

         # render scene
         # do nothing

         # done with frame, flush and swap buffers
         # Swap front and back buffers
         glfw.swap_buffers(window)

     glfw.terminate()

Black Screen
------------

Type "python demo.py", or "python3 demo.py" to run.

The first demo is the least interesting graphical program possible.

#. Sets the color at every pixel black.  (A constant color is better than whatever
color happened to be the previous time it was drawn.)

#. If the user resized the window, reset OpenGL's mappings from *normalized-device-coordinates*
to *screen-coordinates*.

#. Cleared the depth buffer (don't worry about this for now).

When this code returns, the event loop flushes (i.e) sends the frame to the monitor.  Since
no geometry was drawn, the color value for each pixel is still black.

Each color is represented by a number, so the frame is something like this:


bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb



The event loop then calls this code over and over again, and since we retain no state and
we draw nothing, a black screen will be displayed every frame until the user
closes the window, and says to himself, "why did I buy Doom 3"?


Draw A Rectange - Demo 02
=========================

Purpose
-------

Learn how to plot a rectangle.  Learn about OpenGL's coordinate system.


Code
----

The setup code is the same.  Initialize GLFW.  Set the OpenGL version.
Create the window.  Set a key handler for closing.  Set the background to be black.
Execute the event/drawing loop.

Within the event loop, demo02/demo.py draws 2 rectangles, as one might see in
a game of Pong.


Draw Paddles

A black screen is not particularly interesting, so
let's draw something, say, two rectangles.
Where should they be, and what color should they be?

"glColor3f" sets a global variable, which makes it the color to be used
for the subsequently-drawn graphical shape.  The background will be black,
so lets make the first paddle purple, and a second paddle red.

"glBegin(GL_QUADS)" tells OpenGL that we will soon specify 4 *vertices*,
(i.e. points) which define the
quadrilateral.  The vertices will be specified by calling "glVertex2f" 4 times.

"glEnd()" tells OpenGL that we have finished providing vertices for
the begun quadrilateral.

.. code-block:: Python

    # render scene
    # draw paddle 1
    glColor3f(0.578123, 0.0, 1.0)  # r  # g  # b
    glBegin(GL_QUADS)
    glVertex2f(-1.0, -0.3)  # x  # y
    glVertex2f(-0.8, -0.3)  # x  # y
    glVertex2f(-0.8, 0.3)  # x  # y
    glVertex2f(-1.0, 0.3)  # x  # y
    glEnd()

The framebuffer, which has not yet been flushed to the monitor, has geometry which looks like this:

.. figure:: _static/plot1.png
    :align: center
    :alt: Rectangle
    :figclass: align-center

    Rectangle


.. code-block:: Python

    # draw paddle 2
    glColor3f(1.0, 0.0, 0.0)
    glBegin(GL_QUADS)

    glVertex2f(0.8, -0.3)
    glVertex2f(1.0, -0.3)
    glVertex2f(1.0, 0.3)
    glVertex2f(0.8, 0.3)
    glEnd()

The framebuffer, which has not yet been flushed to the monitor,
has geometry which looks like this:

.. figure:: _static/plot2.png
    :align: center
    :alt: Rectangle
    :figclass: align-center

    Rectangle

.. code-block:: Python

    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)


The frame sent to the monitor is a set of values like this:

bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
pppppbbbbbbbbbbbbbbbbbbbbbbbbbbbrrrrr
pppppbbbbbbbbbbbbbbbbbbbbbbbbbbbrrrrr
pppppbbbbbbbbbbbbbbbbbbbbbbbbbbbrrrrr
pppppbbbbbbbbbbbbbbbbbbbbbbbbbbbrrrrr
pppppbbbbbbbbbbbbbbbbbbbbbbbbbbbrrrrr
pppppbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb


What do we have to do to convert from normalized-device-coordinates
into individual colors for each pixel?  Nothing, OpenGL does that for us; therefore
we never have to think in terms of pixels, only in terms of vertices of shapes,
specified by normalized-device-coordinates.

Why is that desirable?

Normalized-Device-Coordinates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The author owns two monitors, one which has 1024x768 pixels, and one which has
1920x1200 pixels.  When he purchases a game from Steam, he expects that his game
will run correctly on either monitor, in full-screen mode.  If a graphics programmer
had to explictly set each indiviual pixel's color, the the programmer would have to
program using "screen-space"(Any "space" means a system of numbers which you're using.
Screen-space means you're specifically using pixel coordinates, i.e, set pixel (5,10) to be red).

What looks alright is screen-space on a large monitor...

.. figure:: _static/screenspace2.png
    :align: center
    :alt: Screenspace
    :figclass: align-center

    Screenspace


Isn't even the same picture on a smaller monitor.

.. figure:: _static/screenspace.png
    :align: center
    :alt: Screenspace
    :figclass: align-center

    Screenspace



Like any good program or library, OpenGL abstracts over screen-space, thus freeing the
programmer from caring about screen size.  If a programmer does not want to program
in discrete (discrete means integer values, not continuous) screen-space,
what type of numbers should he use?  Firstly, it should be a continuous space, meaning
that it should be in decimal numbers.  Because if a real-world object is 10.3 meters long, a programmer
should be able to enter "float foo = 10.3".  Secondly, it should be a fixed range vertically
and an fixed range horizontally.  OpenGL will have to convert points from some space to screen-space,
and since OpenGL does this in hardware (i.e. you can't programmatically change how the conversion
happens), it should be a fixed size.

OpenGL uses *normalized-device-coordinates* (normalized- meaning a distance value of
1; device- the monitor; coordinates- the system of numbers (i.e. space) in which you are working),
which is a continous space from -1.0 to 1.0 horizontally,
and -1.0 to 1.0 vertically.


By specifying geometry using normalized-device-coordinates,
OpenGL will automatically convert from a continuous, -1.0 to 1.0 space,
to discrete pixel-space.

.. figure:: _static/ndcSpace.png
    :align: center
    :alt: NDC space
    :figclass: align-center

    NDC space


Whether we own a small monitor

.. figure:: _static/ndcSpace1.png
    :align: center
    :alt: NDC space
    :figclass: align-center

    NDC space

Or a large monitor.

.. figure:: _static/screenspace2.png
    :align: center
    :alt: NDC space
    :figclass: align-center

    NDC space



-Exercise 1.  The window is resizable by the user while it runs.
Do the paddles both  still appear in the window if you make it really thin?  What if
you make it very wide?


Answer - (Regardless of the window's width to height ratio, the pixel in the upper left of
the window still maps to normalized-device-coordinate (-1.0,-1.0), and the pixel
in the bottom right of the window still maps to (1.0,1.0).

-Exercise 2.  How would you convert from ndc-space to screen-space, given
a monitor width _w_ and height _h_?







Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
