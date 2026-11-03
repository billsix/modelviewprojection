# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

"""Graphing-calculator programs built on the Cayley-graph engine.

Two standalone, run-by-path programs that plot first-class Python functions
the way a graphing calculator does -- ``grapher2d`` for ``f(x)`` and
``grapher3d`` for an ``f(x, y)`` surface.  Both reuse the course's shared GL
toolkit (``mvpvisualization.cayley_gl`` + ``_pipeline``), the ``matrix_stack``,
and ``cayley.cayleyscene.to_matrix``; only the ``ports/`` subtree is off-limits.
The functions to plot are authored in the program source (first-class
callables); the imgui menubar sets only the view (ranges, ticks, grid step)."""
