"""Prove the framebuffer grid morph is identical whether built as raw numpy
(_diag + hand-set translation column) or as gacalc InvertibleFunctions realized
through cayleyscene.to_matrix -- so rewriting the morph in the house gacalc
style changes nothing.

Run from the repo root in the container:
    make shell-exec SCRIPT=tasks/adhoc/framebuffer-in-perspective/verify_gacalc_morph.py
"""

import numpy as np
from gacalc.g3 import Vector
from gacalc.transforms import compose, scale_non_uniform, translate

from modelviewprojection.cayley import cayleyscene


def diag_with_offset(
    sx: float, sy: float, sz: float, ox: float, oy: float
) -> np.ndarray:
    """The old raw-numpy form: a diagonal scale with a translation column."""
    m = np.identity(4, dtype=float)
    m[0, 0], m[1, 1], m[2, 2] = sx, sy, sz
    m[0, 3], m[1, 3] = ox, oy
    return m


def gacalc_form(
    sx: float, sy: float, sz: float, ox: float, oy: float
) -> np.ndarray:
    """The house form: compose gacalc functions, realize with to_matrix.
    compose([translate, scale]) applies the scale first, then the translate --
    i.e. M @ v = translate(scale(v)) -- which is what the morph wants."""
    f = compose([translate(Vector(ox, oy, 0.0)), scale_non_uniform(sx, sy, sz)])
    return cayleyscene.to_matrix(f)


# Representative samples across the actual morph: flat (sz=0) with the
# bottom-left-at-origin offset, the warp to the NDC square, the extruded cube,
# and the epilogue expansion back to a 20x10 prism.
hw, hh = 10.0, 5.0
x_ndc, y_ndc = 1.0 / hw, 1.0 / hh
samples = [
    (1.0, 1.0, 0.0, hw, hh),  # flat, bottom-left at origin (tau=0)
    (1.0, 1.0, 0.0, 0.0, 0.0),  # flat, centred (tau=1)
    (x_ndc, y_ndc, 0.0, 0.0, 0.0),  # warped to NDC square, still flat
    (x_ndc, y_ndc, 1.0, 0.0, 0.0),  # NDC cube
    (hw, hh, 1.0, 0.0, 0.0),  # epilogue: expanded to the prism
    (0.4, 0.7, 0.5, 2.0, 1.0),  # arbitrary mid-morph
]

all_ok = True
for sx, sy, sz, ox, oy in samples:
    a = diag_with_offset(sx, sy, sz, ox, oy)
    b = gacalc_form(sx, sy, sz, ox, oy)
    ok = np.allclose(a, b)
    all_ok = all_ok and ok
    print(f"sx={sx} sy={sy} sz={sz} ox={ox} oy={oy} -> match={ok}")

print("ALL MATCH" if all_ok else "MISMATCH")
raise SystemExit(0 if all_ok else 1)
