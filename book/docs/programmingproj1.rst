..
   Copyright (c) 2018-2025 William Emerison Six

   Permission is granted to copy, distribute and/or modify this document
   under the terms of the GNU Free Documentation License, Version 1.3
   or any later version published by the Free Software Foundation;
   with no Invariant Sections, no Front-Cover Texts, and no Back-Cover Texts.

   A copy of the license is available at
   https://www.gnu.org/licenses/fdl-1.3.html.

**********************
Programming Project #1
**********************

Objective
=========

Draw whatever you'd like in NDC. The following from assignments/assignment1.py
should get you started with a bunch of example code.


.. literalinclude:: ../../assignments/assignment1.py
   :language: python
   :start-after: doc-region-begin event loop
   :end-before: doc-region-end event loop
   :linenos:
   :lineno-match:
   :caption: assignments/assignment1.py

Examples
========


Draw a triangle
---------------

Draw a triangle that doesn't move, using predefined coordinates
in NDC.

.. literalinclude:: ../../assignments/assignment1.py
   :language: python
   :start-after: doc-region-begin draw a triangle
   :end-before: doc-region-end draw a triangle
   :linenos:
   :lineno-match:
   :caption: assignments/assignment1.py



Draw an Oscillating Triangle
----------------------------

In the event loop, it defines elapsed time in seconds.  We can use
this value to change the position of a triangle over time, and change
the color.

.. literalinclude:: ../../assignments/assignment1.py
   :language: python
   :start-after: doc-region-begin draw an oscillating triangle
   :end-before: doc-region-end draw an oscillating triangle
   :linenos:
   :lineno-match:
   :caption: assignments/assignment1.py


Draw X^2 (Precomputed)
----------------------

We can also draw math functions like on a graphing calculator.
Here's an example of using GL_Lines, where line segments are
expressed in pairs of glVertexs, as such, values need to be duplicated.

.. literalinclude:: ../../assignments/assignment1.py
   :language: python
   :start-after: doc-region-begin draw x squared precomputed
   :end-before: doc-region-end draw x squared precomputed
   :linenos:
   :lineno-match:
   :caption: assignments/assignment1.py

Draw (X-1/2)^2 (Dynamically)
----------------------------

Using a generic plot function, we can plot any Python function

Black Box
^^^^^^^^^


.. literalinclude:: ../../assignments/assignment1.py
   :language: python
   :start-after: doc-region-begin draw (x minus 1/2)^2
   :end-before: doc-region-end draw (x minus 1/2)^2
   :linenos:
   :lineno-match:
   :caption: assignments/assignment1.py

Implementation (White Box)
^^^^^^^^^^^^^^^^^^^^^^^^^^


.. literalinclude:: ../../assignments/assignment1.py
   :language: python
   :start-after: doc-region-begin generic plot function
   :end-before: doc-region-end generic plot function
   :linenos:
   :lineno-match:
   :caption: assignments/assignment1.py



Draw Unnamed Function
---------------------

Unlike the example before, where we named a local function x_minus_onehalf_squared,
we don't have to name a new function, we can instead make a new unnamed function
on the fly with lambda.

.. literalinclude:: ../../assignments/assignment1.py
   :language: python
   :start-after: doc-region-begin unnamed_function
   :end-before: doc-region-end unnamed_function
   :linenos:
   :lineno-match:
   :caption: assignments/assignment1.py

Draw Circle
-----------

We can draw a circle by breaking it up into triangles.

.. literalinclude:: ../../assignments/assignment1.py
   :language: python
   :start-after: doc-region-begin circle
   :end-before: doc-region-end circle
   :linenos:
   :lineno-match:
   :caption: assignments/assignment1.py
