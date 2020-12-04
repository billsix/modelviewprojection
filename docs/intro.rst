Introduction
============

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
^^^^^^^^

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
^^^^^^^^^^^^^^^^^

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
