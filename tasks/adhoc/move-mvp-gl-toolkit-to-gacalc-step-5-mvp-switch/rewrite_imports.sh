#!/bin/bash
# Point mvp at the Cayley graph and GL toolkit that moved into gacalc 0.1.1
# (gacalc.cayley, gacalc.gl), and load the visualizations' shaders from
# gacalc.gl.SHADER_DIR instead of mvpvisualization's own directory.
#
# Idempotent: every pattern matches only the pre-move spelling, so a second run
# changes nothing.  Run from anywhere; paths resolve from the repo root.
# Import ORDER is left to `make format` (ruff's isort moves the gacalc lines into
# the third-party block).
set -e
cd "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"

mapfile -t files < <(git grep -l -E \
    'modelviewprojection(\.| import )(matrix_stack|cayley|mvpvisualization(\._pipeline| import (_pipeline|\()))' \
    -- 'src/*.py' ':!src/modelviewprojection/cayley' \
    ':!src/modelviewprojection/matrix_stack.py' \
    ':!src/modelviewprojection/mvpvisualization/_pipeline.py' \
    ':!src/modelviewprojection/mvpvisualization/cayley_gl.py' \
    ':!src/modelviewprojection/mvpvisualization/labels.py' \
    ':!src/modelviewprojection/graphingcalculator')

for f in "${files[@]}"; do
    echo "$f"
    perl -0pi -e '
        s/^import modelviewprojection\.matrix_stack as ms$/import gacalc.gl.matrix_stack as ms/mg;
        s/^from modelviewprojection import matrix_stack as ms$/from gacalc.gl import matrix_stack as ms/mg;
        s/^from modelviewprojection\.cayley import \(/from gacalc.cayley import (/mg;
        s/^(\s*)from modelviewprojection\.mvpvisualization\._pipeline import GLenum$/$1from gacalc.gl._pipeline import GLenum/mg;
        s/^from modelviewprojection\.mvpvisualization import _pipeline as _p$/from gacalc.gl import _pipeline as _p/mg;
        # the visualizations: cayley_gl + their shaders now come from gacalc.gl
        if (s/^from modelviewprojection\.mvpvisualization import \(\n    cayley_gl,\n\)$/from gacalc.gl import (\n    SHADER_DIR,\n    cayley_gl,\n)/mg) {
            s/^pwd: str = os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\n//mg;
            s/shader_dir=pwd\b/shader_dir=SHADER_DIR/g;
            s/^import os\n//mg unless /\bos\./;
        }
    ' "$f"
done
