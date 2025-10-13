..
   Copyright (c) 2018-2025 William Emerison Six

   Permission is granted to copy, distribute and/or modify this document
   under the terms of the GNU Free Documentation License, Version 1.3
   or any later version published by the Free Software Foundation;
   with no Invariant Sections, no Front-Cover Texts, and no Back-Cover Texts.

   A copy of the license is available at
   https://www.gnu.org/licenses/fdl-1.3.html.

****************
Math Homework #1
****************


Objective
=========

Using 1 Dimensional Vector math, given a function definition in Python for
celsius to kelvin and for fahrenheit to celsius, implement in Python

- fahrenheit to kelvin
- celsius to fahrenheit
- kelvin to fahrenheit


This book provides a math library in Python.  We import them here.

We'll use pytest's approx
method to test if two floating point values are close enough to the same
value.  We import a type :class:`modelviewprojection.mathutils.InvertibleFunction`,
:py:meth:`modelviewprojection.mathutils.compose`, :py:meth:`modelviewprojection.mathutils.inverse`

Important note.  The links in the previous paragraphs are links to API documentation.
API documentation is like a guidebook that explains how to use a library.  It tells
you what functions, classes, and modules are available, what inputs they require,
what they return, and examples of how to use them correctly.  Instead of guessing
or relying on scattered internet posts, the API gives you the most accurate
and up to date information straight from the source.  For your assignments (and
your future work), clicking on the API docs will save you time, help you avoid mistakes
and show you features that you might not realize exists.



.. literalinclude:: ../../assignments/demo02/vec1.py
   :language: python
   :start-after: doc-region-begin imports
   :end-before: doc-region-end imports
   :linenos:
   :lineno-match:
   :caption: assignments/demo02/vec1.py

We can do addition on :class:`modelviewprojection.mathutils1d.Vector1D` using "+", :py:meth:`modelviewprojection.mathutils1d.Vector1D.__add__`



.. literalinclude:: ../../assignments/demo02/vec1.py
   :language: python
   :start-after: doc-region-begin adding vectors
   :end-before: doc-region-end adding vectors
   :linenos:
   :lineno-match:
   :caption: assignments/demo02/vec1.py

We can do subtraction on :class:`modelviewprojection.mathutils1d.Vector1D` using "-", :py:meth:`modelviewprojection.mathutils1d.Vector1D.__sub__`


.. literalinclude:: ../../assignments/demo02/vec1.py
   :language: python
   :start-after: doc-region-begin subtracting vectors
   :end-before: doc-region-end subtracting vectors
   :linenos:
   :lineno-match:
   :caption: assignments/demo02/vec1.py

We can do multiply a scalar by  :class:`modelviewprojection.mathutils1d.Vector1D` using "*", :py:meth:`modelviewprojection.mathutils1d.Vector1D.__mul__`


.. literalinclude:: ../../assignments/demo02/vec1.py
   :language: python
   :start-after: doc-region-begin multiplying scalar by a vector
   :end-before: doc-region-end multiplying scalar by a vector
   :linenos:
   :lineno-match:
   :caption: assignments/demo02/vec1.py

We can do negate a  :class:`modelviewprojection.mathutils1d.Vector1D` using "-", :py:meth:`modelviewprojection.mathutils1d.Vector1D.__neg__`


.. literalinclude:: ../../assignments/demo02/vec1.py
   :language: python
   :start-after: doc-region-begin negating a vector
   :end-before: doc-region-end negating a vector
   :linenos:
   :lineno-match:
   :caption: assignments/demo02/vec1.py

Translate Implementation
------------------------

Next we have a very import function, :py:meth:`modelviewprojection.mathutils.translate`.  Read
the API documentation in the link, it's a very important function.

Translate is a function which partially binds a constant :class:`Vector1D` to
one of the arguments of :py:meth:`Vector1D.__add__`, thus creating
a new function of one argument.

In high school math, you'd learn about classes of functions,  such as
affine functions that follow the pattern
:math:`f(x) = m \times x + b`.  You were told that :math:`m` and :math:`b`
were constant.

You could recognize :math:`f(x) = 2 \times x + 3` as being an affine function
where :math:`m=2` and :math:`b=3`.  You could recognize
:math:`f(x) = 5 \times x + 0` as being an affine function where
:math:`m=5` and :math:`b=0`.  You could recognize :math:`f(x) = x \times x` as
not being affine, although it's
implicit that :math:`b=0`, there is no constant times :math:`x`
But could you generate a new function for a given :math:`m` and given
:math:`b`?

Perhaps you could use notation such as :math:`f_{m=2,b=3}(x)` to be a function :math:`2 \times x + 3`,
or :math:`f(x; m=2,b=3)` to be a function :math:`2 \times x + 3`.

We will use the folliwng notation for translate, :math:`T_{b}(x) = x + b`, where if
we specify a constant :math:`b`, it will be notated as :math:`T_{b=3}` equals an expression
:math:`x + 3`.

Here, we call the translate function to create a new function, named "fn",
notated :math:`T_{b=2}`, which is a function of a variable :math:`x`, and a constant 2,
:math:`T_{b=2}(x) = x + 2`.

Usage (Black Box)
^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../assignments/demo02/vec1.py
   :language: python
   :start-after: doc-region-begin invertible function
   :end-before: doc-region-end invertible function
   :linenos:
   :lineno-match:
   :caption: assignments/demo02/vec1.py


Now that we've generated a function using translate, we can now apply it, 0, 1,
or many times.

.. literalinclude:: ../../assignments/demo02/vec1.py
   :language: python
   :start-after: doc-region-begin applying invertible function
   :end-before: doc-region-end applying invertible function
   :linenos:
   :lineno-match:
   :caption: assignments/demo02/vec1.py

Inverting such a function is done by negating :math:`b`, so (:math:`{T_{b=2}}^{-1} \circ {T_{b=2}}) (x) = ({T_{b=-2}} \circ {T_{b=2}}) (x) = x`

To get the inverse in Python, we can call the :py:meth:`modelviewprojection.mathutils.inverse` function
on our function, without having to worry about how it's implemented.



.. literalinclude:: ../../assignments/demo02/vec1.py
   :language: python
   :start-after: doc-region-begin applying inverse function
   :end-before: doc-region-end applying inverse function
   :linenos:
   :lineno-match:
   :caption: assignments/demo02/vec1.py


What's nice about that is we can look at the implementation of :py:meth:`modelviewprojection.mathutils.translate`
once, understand how it works internally, and then forget those details and treat
it as an invertible BlackBox_.

.. _BlackBox:  https://en.wikipedia.org/wiki/Black_box

Definition (White Box)
^^^^^^^^^^^^^^^^^^^^^^


.. literalinclude:: ../../src/modelviewprojection/mathutils.py
   :language: python
   :start-after: doc-region-begin define translate
   :end-before: doc-region-end define translate
   :linenos:
   :lineno-match:
   :caption: src/modelviewprojection/mathutils.py



Function Composition
--------------------

Similarly to how we defined :math:`T_{b}(x) = x + b` for adding a constant
:math:`b`, we can define a "scaling" function :math:`S_{m}(x) = m \times x`.  We can use
function composition of a partially bound :math:`S` and partially bound :math:`T`
to generate new instances of :math:`f(x) = m \times x + b`

:math:`f(x) = {m}{x} + b = T_{b=2} \circ S_{m=5}`



.. literalinclude:: ../../assignments/demo02/vec1.py
   :language: python
   :start-after: doc-region-begin y = m*x + b
   :end-before: doc-region-end y = m*x + b
   :linenos:
   :lineno-match:
   :caption: assignments/demo02/vec1.py

Assignment
==========

Provided functions
------------------

In :ref:`tempconversionlabel` you were provided definitions
of functions to convert between fahrenheit, celsius, and kelvin.
Provided to you are Python implementations of three of those
functions

.. literalinclude:: ../../assignments/demo02/vec1.py
   :language: python
   :start-after: doc-region-begin defined functions
   :end-before: doc-region-end defined functions
   :linenos:
   :lineno-match:
   :caption: assignments/demo02/vec1.py

Functions to implement
----------------------

Your task is to modify the three functions below so that
the asserts all pass


.. literalinclude:: ../../assignments/demo02/vec1.py
   :language: python
   :start-after: doc-region-begin work to do
   :end-before: doc-region-end work to do
   :linenos:
   :lineno-match:
   :caption: assignments/demo02/vec1.py
