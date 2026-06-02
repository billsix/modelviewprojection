# Copyright (c) 2018-2026 William Emerison Six
#
# Make the (non-package) mvpVisualization/ scripts importable from tests, so the
# Cayley-graph engine there can be unit-tested.  pytest imports conftest before
# collecting test modules, so this runs before their top-level imports.

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "mvpVisualization")
)
