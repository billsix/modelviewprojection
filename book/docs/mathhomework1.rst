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

Using 1 Dimensional Vector math, given a function definiton in Python for
celsius to kelvin and for fahrenheit to celsius, implement in Python

- fahrenheit to kelvin
- celsius to fahrenheit
- kelvin to fahrenheit


This book provides a math library in Python.  We import them here.

We'll use pytest's approx
method to test if two floating point values are close enough to the same
value.  We import a type :class:`modelviewprojection.mathutils.InvertibleFunction`,
:py:meth:`modelviewprojection.mathutils.compose`, :py:meth:`modelviewprojection.mathutils.inverse`

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
   :start-after: doc-region-begin muliplying scalar by a vector
   :end-before: doc-region-end muliplying scalar by a vector
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

.. literalinclude:: ../../assignments/demo02/vec1.py
   :language: python
   :start-after: doc-region-begin invertible function
   :end-before: doc-region-end invertible function
   :linenos:
   :lineno-match:
   :caption: assignments/demo02/vec1.py

.. literalinclude:: ../../assignments/demo02/vec1.py
   :language: python
   :start-after: doc-region-begin applying invertible function
   :end-before: doc-region-end applying invertible function
   :linenos:
   :lineno-match:
   :caption: assignments/demo02/vec1.py

.. literalinclude:: ../../assignments/demo02/vec1.py
   :language: python
   :start-after: doc-region-begin y = m*x + b
   :end-before: doc-region-end y = m*x + b
   :linenos:
   :lineno-match:
   :caption: assignments/demo02/vec1.py

.. literalinclude:: ../../assignments/demo02/vec1.py
   :language: python
   :start-after: doc-region-begin defined functions
   :end-before: doc-region-end defined functions
   :linenos:
   :lineno-match:
   :caption: assignments/demo02/vec1.py

.. literalinclude:: ../../assignments/demo02/vec1.py
   :language: python
   :start-after: doc-region-begin work to do
   :end-before: doc-region-end work to do
   :linenos:
   :lineno-match:
   :caption: assignments/demo02/vec1.py
