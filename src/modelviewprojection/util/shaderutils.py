# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

"""Shared MVP uniform upload for the shader-era demos.

`set_mvp_uniforms` was duplicated verbatim in demo22a, demo23 and demo24 --
the three demos whose vertex shader wants both the full
model-view-projection matrix and the model matrix on its own (the latter for
lighting, which needs world-space positions and normals).  They import it from
here instead of redefining it.

Unlike the fixed-function demos, which let `matrix_stack` push matrices
straight into GL, these upload the stack's current matrices by hand, so this
is where the stack meets the shader.
"""

import numpy as np
import OpenGL.GL as GL

import modelviewprojection.matrix_stack as ms


def set_mvp_uniforms(u_mvp: int, u_model: int) -> None:
    """Upload the current modelviewprojection and model matrices.

    `u_mvp` and `u_model` are uniform locations from
    `glGetUniformLocation`; each demo looks its own up once, next to the
    program it compiled, and passes them in.  (The demos kept these in module
    globals when the function lived beside them; a shared helper has to be
    told which program's uniforms to write.)

    `GL_TRUE` for the transpose argument, because `matrix_stack` keeps
    matrices row-major and GLSL wants them column-major.
    """
    GL.glUniformMatrix4fv(
        u_mvp,
        1,
        GL.GL_TRUE,
        np.ascontiguousarray(
            ms.get_current_matrix(ms.MatrixStack.modelviewprojection),
            dtype=np.float32,
        ),
    )
    GL.glUniformMatrix4fv(
        u_model,
        1,
        GL.GL_TRUE,
        np.ascontiguousarray(
            ms.get_current_matrix(ms.MatrixStack.model),
            dtype=np.float32,
        ),
    )
