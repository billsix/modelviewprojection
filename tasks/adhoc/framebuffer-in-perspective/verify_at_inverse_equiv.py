"""Prove the epilogue keeps the framebuffer GRID outline coincident with the
squashed SCENE (they must not drift apart mid-animation).

Both use one gacalc transform: the grid is `E . _warp` (its prism mesh -> NDC via
_warp, then E), the scene is `E` (on NDC points), where E = inverse(_warp) then
_place, animated with .at().  So a prism corner c drawn by the grid must land
exactly where the scene draws the NDC corner _warp(c).  This checks that across
the whole epilogue -- the regression that `inverse(f).at(t)` (reciprocal) vs a
linear stand-in introduced, now fixed by sharing E.

    make shell-exec CMD='python tasks/adhoc/framebuffer-in-perspective/verify_at_inverse_equiv.py'
"""

import numpy as np
from gacalc.g3 import Vector
from gacalc.transforms import compose, scale_non_uniform, translate

from modelviewprojection.cayley import cayleyscene as cs

interp = cs.interp
mat = cs.to_matrix

HW, HH = 10.0, 5.0
XN, YN = 1.0 / HW, 1.0 / HH
PROLOGUE_DUR = 2.0 + 3.0 * 5.0  # 17
DEMO_DUR = 112.0
EWARP = ETRANS = 5.0
EPI = PROLOGUE_DUR + DEMO_DUR  # 129


def warp() -> object:
    return scale_non_uniform(XN, YN, 1.0)


def place() -> object:
    return translate(Vector(HW, HH, 0.0))


def epilogue(t: float) -> object:
    rs = interp(t, EPI, EWARP)
    rt = interp(t, EPI + EWARP, ETRANS)
    # linear NDC->framebuffer scale (matches the demo), then translate
    return compose([place().at(rt), scale_non_uniform(HW, HH, 1.0).at(rs)])


PRISM_CORNERS = [
    Vector(sx * HW, sy * HH, sz * 1.0)
    for sx in (-1.0, 1.0)
    for sy in (-1.0, 1.0)
    for sz in (-1.0, 1.0)
]

ok = True
for k in range(0, int((EWARP + ETRANS + 4.0) * 2)):
    t = EPI + k * 0.5
    grid = mat(compose([epilogue(t), warp()]))
    scene = mat(epilogue(t))
    for c in PRISM_CORNERS:
        cp = np.array([c.coeff_e_1, c.coeff_e_2, c.coeff_e_3, 1.0])
        ndc = np.array([c.coeff_e_1 * XN, c.coeff_e_2 * YN, c.coeff_e_3, 1.0])
        if not np.allclose(grid @ cp, scene @ ndc):
            print(f"DRIFT at t={t}: corner {cp[:3]}")
            ok = False
# endpoints: t=EPI is NDC cube; t>=EPI+EWARP+ETRANS is the bottom-left prism
end = mat(compose([epilogue(EPI + EWARP + ETRANS), warp()]))
corner = end @ np.array([HW, HH, 1.0, 1.0])  # prism top-right-front
print("epilogue-end grid corner (expect ~20,10,1):", corner[:3])
print("GRID TRACKS SCENE across the epilogue" if ok else "DRIFT FOUND")
raise SystemExit(0 if ok else 1)
