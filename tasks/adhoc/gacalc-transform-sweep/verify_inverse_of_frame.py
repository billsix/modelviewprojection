"""Prove the identity that lets the mvpvisualization "View From" center-on drop
`np.linalg.inv` for gacalc `inverse()`:

    to_matrix(inverse(compose([A, B]))) == inv(to_matrix(A) @ to_matrix(B))

for affine A, B -- so replacing
    frame_m = inv @ to_matrix(transform(space, t));  np.linalg.inv(frame_m)
with
    to_matrix(inverse(compose([inverse_transform(t), transform(space, t)])))
uploads the identical view matrix.

    make shell-exec CMD='python tasks/adhoc/gacalc-transform-sweep/verify_inverse_of_frame.py'
"""

import math

import numpy as np
from gacalc.g3 import Vector
from gacalc.transforms import compose, inverse, scale_non_uniform, translate

from modelviewprojection.cayley import cayleyscene as cs
from modelviewprojection.mathutils import rotate_x, rotate_y, rotate_z

mat = cs.to_matrix

# A, B: representative affine functions (the kinds the demos compose -- the
# world->camera inverse is translate+rotate; placements add scale).
A = compose(
    [translate(Vector(-1.5, 0.4, 8.5)), rotate_y(0.44), rotate_x(0.26)]
)
B = compose(
    [
        translate(Vector(-9.0, 1.0, 0.0)),
        rotate_z(math.radians(45.0)),
        scale_non_uniform(1.3, 0.7, 1.0),
    ]
)

lhs = mat(inverse(compose([A, B])))  # the gacalc way
rhs = np.linalg.inv(mat(A) @ mat(B))  # the old numpy way
print("gacalc inverse == numpy inverse of the frame:", np.allclose(lhs, rhs))
raise SystemExit(0 if np.allclose(lhs, rhs) else 1)
