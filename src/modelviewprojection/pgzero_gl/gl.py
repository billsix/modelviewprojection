# Copyright (c) 2026 William Emerison Six
# SPDX-License-Identifier: LGPL-2.1-only
# Full license text: src/modelviewprojection/pgzero_gl/LICENSE.

"""OpenGL 3.3 core helpers the Code-the-Classics renderers call down into.

Each game keeps its own ``Renderer``, shaders and uniform table; these are the
pieces that are the same in every one of them: compiling and linking a shader
program, a VAO + VBO of 2-D positions, and the orthographic projection from
the games' top-left-origin, y-down pixel space to NDC. Matrices are row-major
numpy, uploaded with ``transpose=GL_TRUE``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gacalc.g3 as g3
import numpy as np
import OpenGL.GL as GL
from gacalc.transforms import compose, scale_non_uniform, to_matrix, translate
from numpy.typing import NDArray


def ortho_pixels(width: float, height: float) -> NDArray[np.float32]:
    """Map pixel space (0,0)=top-left .. (width,height)=bottom-right to NDC:
    scale to a 2 x 2 box (y flipped, z into the clip range), then move its
    corner to (-1, 1). Built once per renderer.
    """
    return np.asarray(
        to_matrix(
            compose(
                [
                    translate(b=-1 * g3.Vector.e_1 + 1 * g3.Vector.e_2),
                    scale_non_uniform(2.0 / width, -2.0 / height, -1),
                ]
            ),
            g3.Vector,
        ),
        dtype=np.float32,
    )


def compile_shader(src: str, kind: Any) -> int:
    """Compile one GLSL shader of the given ``kind``; raise on a compile error.

    ``kind`` is a PyOpenGL ``GL_*_SHADER`` constant (opaque, so typed ``Any``).
    """
    sid: int = GL.glCreateShader(kind)
    GL.glShaderSource(sid, src)
    GL.glCompileShader(sid)
    if GL.glGetShaderiv(sid, GL.GL_COMPILE_STATUS) != GL.GL_TRUE:
        raise RuntimeError(GL.glGetShaderInfoLog(sid).decode())
    return sid


def link_program(vertex_source: str, fragment_source: str) -> int:
    """Compile both shaders and link them into a program; raise on failure."""
    vs: int = compile_shader(src=vertex_source, kind=GL.GL_VERTEX_SHADER)
    fs: int = compile_shader(src=fragment_source, kind=GL.GL_FRAGMENT_SHADER)
    program: int = GL.glCreateProgram()
    GL.glAttachShader(program, vs)
    GL.glAttachShader(program, fs)
    GL.glLinkProgram(program)
    if GL.glGetProgramiv(program, GL.GL_LINK_STATUS) != GL.GL_TRUE:
        raise RuntimeError(GL.glGetProgramInfoLog(program).decode())
    GL.glDeleteShader(vs)
    GL.glDeleteShader(fs)
    return program


@dataclass(slots=True, eq=False)
class GLBuffer:
    """A vertex array object and the vertex buffer it reads 2-D positions
    (attribute 0) from."""

    vao: int
    vbo: int


def make_buffer(data: NDArray[np.float32] | None) -> GLBuffer:
    """Create a VAO + VBO of 2-D positions at attribute 0; ``data`` fills a
    static buffer, ``None`` leaves a dynamic one to be filled per draw."""
    vao: int = GL.glGenVertexArrays(1)
    vbo: int = GL.glGenBuffers(1)
    GL.glBindVertexArray(vao)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
    if data is not None:
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER, data.nbytes, data, GL.GL_STATIC_DRAW
        )
    GL.glEnableVertexAttribArray(0)
    GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
    return GLBuffer(vao, vbo)
