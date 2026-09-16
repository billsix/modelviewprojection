"""Confirm gacalc's .at()/inverse() laws before using them for the framebuffer
morph (so the epilogue is inverse(forward).at(t), not hand-rolled factors).

    make shell-exec CMD='python tasks/adhoc/framebuffer-in-perspective/probe_gacalc_at_inverse.py'
"""

import numpy as np
from gacalc.g3 import Vector
from gacalc.transforms import compose, inverse, scale_non_uniform, translate

from modelviewprojection.cayley import cayleyscene as cs


def mat(f) -> np.ndarray:
    return cs.to_matrix(f)


s = scale_non_uniform(10.0, 5.0, 1.0)
tr = translate(Vector(10.0, 5.0, 0.0))

print("scale.at(0.5) diag:", np.diag(mat(s.at(0.5)))[:3])  # expect 5.5,3.0,1.0
print("translate.at(0.5) col3:", mat(tr.at(0.5))[:3, 3])  # expect 5.0,2.5,0.0
print("inverse(scale) diag:", np.diag(mat(inverse(s)))[:3])  # expect .1,.2,1
print(
    "inverse commutes with at:",
    np.allclose(mat(inverse(s).at(0.5)), mat(inverse(s.at(0.5)))),
)
# The epilogue scene transform: NDC -> framebuffer = inverse of
# (scale-to-ndc then center-translate), animated per phase.
x_ndc, y_ndc, hw, hh = 0.1, 0.2, 10.0, 5.0
ndc_to_prism = inverse(scale_non_uniform(x_ndc, y_ndc, 1.0))
to_bottom_left = inverse(translate(Vector(-hw, -hh, 0.0)))
full = compose([to_bottom_left.at(1.0), ndc_to_prism.at(1.0)])
got = mat(full) @ np.array([1.0, 1.0, 0.0, 1.0])  # NDC corner (1,1)
print("NDC (1,1) -> framebuffer:", got[:3], "(expect 20,10,0)")
