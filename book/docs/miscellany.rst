..
   Copyright (c) 2018-2025 William Emerison Six

   Permission is granted to copy, distribute and/or modify this document
   under the terms of the GNU Free Documentation License, Version 1.3
   or any later version published by the Free Software Foundation;
   with no Invariant Sections, no Front-Cover Texts, and no Back-Cover Texts.

   A copy of the license is available at
   https://www.gnu.org/licenses/fdl-1.3.html.


Miscellany
**********

.. _firstclassfunctions:

First Class Functions
=====================

Functions are first class values in Python, and are objects just
like anything else.  The can be passed as arguments, stored in variables,
and applied later zero, 1, or more times.  As an example, here is a unit
test in the code to demonstrate.


* "test_first_class_functions" is a function that is run by pytest, a unit test
  framework [#unittest]_.


.. literalinclude:: ../../tests/test_firstclassfunctions.py
   :language: python
   :start-after: doc-region-begin test first class functions
   :end-before: doc-region-end test first class functions
   :linenos:
   :lineno-match:
   :caption: tests/test_firstclassfunctions.py

* Inside of the body of test_first_class_functions, we define a function
  named "doubler".  "doubler" take an integer as input, named "x", and
  returns an integer.  Within the body of "doubler", the input "x" is
  multiplied by 2, the result of which is the return value.
* "doubler" is a function that is only available within the scope of
  "test_firstclassfunctions".
* "add_five_to_result_of" is another local function.  It takes two parameters,
  "f" and "x".

  * The parameter f is a function that takes an int as a parameter, and
    returns an int. "f: typing.Callable[[int], int]" means that f
    can be treated as a function that can be called, where there is only
    one parameter to f, of type int, and the result of calling f is
    of type int
  * The parameter x is an int


If you are unfamiliar with looking at the lines above, it's
a session in the Python Read-Evaluate-Print loop, `read more here`_.

As a harder example, if Python didn't have recursion, but it does
have first class functions as values, the programmer could simulate
recursion by passing a function to itself as a parameter.

.. literalinclude:: ../../tests/test_firstclassfunctions.py
   :language: python
   :start-after: doc-region-begin test factorial no recursion
   :end-before: doc-region-end test factorial no recursion
   :linenos:
   :lineno-match:
   :caption: tests/test_firstclassfunctions.py




.. [#unittest] A unit test framework is a tool that helps programmers automatically check whether
               small pieces of their code (called units, like individual methods or functions)
               work as intended. Instead of running the program by hand and guessing if the
               results are correct, you can write tests once and rerun them anytime you change
               the code. This makes it much easier to catch bugs early, gives you confidence
               that new changes don’t break old features, and supports building larger, more
               reliable programs over time.

.. _read more here : https://realpython.com/interacting-with-python/
