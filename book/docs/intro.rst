..
   Copyright (c) 2018-2025 William Emerison Six

   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction, including without limitation the rights
   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   copies of the Software, and to permit persons to whom the Software is
   furnished to do so, subject to the following conditions:

   The above copyright notice and this permission notice shall be included in all
   copies or substantial portions of the Software.

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
   SOFTWARE.

Introduction
============

Learn how to program in 3D computer graphics in Python!

.. figure:: _static/screenshots/frustum1.png
    :class: no-scale
    :align: center
    :alt: frustum1
    :figclass: align-center



Source code
^^^^^^^^^^^

This book references source code, which is at `https://github.com/billsix/modelviewprojection <https://github.com/billsix/modelviewprojection>`_

.. include:: ./version.txt

Approach
^^^^^^^^

This book takes a "mistake-driven development" approach: instead of
handing you polished math formulae, it walks you through building
complex graphics applications step by step. Along the way, we’ll make
mistakes—and then fix them—so you can see how solutions emerge in
real-world programming.

You’ll learn how to place objects in space, draw them relative to
others, add a camera that moves over time based on user input, and
transform all those objects into the 2D pixel coordinates of your
screen. By the end, you’ll understand the foundations of creating
first-person and third-person applications or games. The goal? To
empower you to build the graphics programs you want, using math you
mostly already know.

This book keeps things intentionally simple. The applications we create
won’t be particularly pretty or realistic-looking. For more advanced
topics, you’ll want to dive into references like the OpenGL “Red Book
” and “Blue Book,” or explore some of the tutorials listed at the end.

#. LearnOpenGL_
#. OpenGLTutorial_

.. _LearnOpenGL:  https://learnopengl.com/
.. _OpenGLTutorial:  http://www.opengl-tutorial.org/

While this book fills a huge gap by focusing on the basics in a hands
-on way, those other books are fantastic references for diving into
advanced topics.


Pre-requisities
^^^^^^^^^^^^^^^

#. Basic programming concepts in Python.

   #. YouTube videos

      #. Learn Python with Socratica_
      #. Microsoft_ Python Tutorials

   #. Books

      #. https://learnbyexample.github.io/100_page_python_intro/preface.html
      #. https://diveintopython3.problemsolving.io/

#. High school trigonometry

#. Linear Algebra (optional)

   #. 3Blue1Brown - Linear Transformations_
   #. 3Blue1Brown - Matrix Multiplication as Composition_

.. _Socratica: https://www.youtube.com/watch?v=bY6m6_IIN94&list=PLi01XoE8jYohWFPpC17Z-wWhPOSuh8Er-&index=2
.. _Microsoft: https://www.youtube.com/watch?v=jFCNu1-Xdsw&list=PLlrxD0HtieHhS8VzuMCfQD4uJ9yne1mE6
.. _Transformations: https://www.youtube.com/watch?v=kYB8IZa5AuE
.. _Composition: https://www.youtube.com/watch?v=XkY2DOUCWMU

Required Software
^^^^^^^^^^^^^^^^^

You will need to install Python. https://realpython.com/installing-python/

Before running this code, you need a virtual environment,
with dependencies installed. https://docs.python.org/3/tutorial/venv.html

Windows
~~~~~~~

On Windows, if you use the Developer command prompt, to set up the environment run

.. code-block::

   python -m venv venv
   cd venv\Scripts
   activate.bat
   cd ..\..\
   python -m pip install --upgrade pip setuptools
   python -m pip install -r requirements.txt

To run the Spyder IDE to execute the code in the book, open Spyder on the developer command
prompt

.. code-block::

   cd venv\Scripts
   activate.bat
   cd ..\..\
   spyder


MacOS or Linux
~~~~~~~~~~~~~~

On MacOS or Linux, on a terminal, to set up the environment, run

.. code-block:: bash

   python3 -m venv venv
   source venv/bin/activate
   python3 -m pip install --upgrade pip setuptools
   python3 -m pip install -r requirements.txt

To run the Spyder IDE to execute the code in the book, open Spyder on the developer command
prompt

.. code-block::

   source venv/bin/activate
   spyder



Linux
~~~~~

Install Python3, glfw via a package manager.  Use pip and virtualenv to install dependencies

Mac
~~~

Python Python3 (via anaconda, homebrew, macports, whatever), and use pip and virtualenv to install dependencies.
