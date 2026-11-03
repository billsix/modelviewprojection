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

"""Runtime TeX billboard labels for the graphing calculators.

``texExpToPng`` (the C wrapper around ``latex`` + ``dvipng``, built into the
image) renders a LaTeX string to a transparent PNG; it is uploaded as an RGBA
texture and drawn as a camera-facing billboard quad (see ``billboard.vert``).
The billboard keeps a constant on-screen size at any depth and works in both the
2D ortho view and the 3D perspective view.

Graceful degradation is the point of the module: ``texExpToPng`` is on ``PATH``
in the podman image (the Dockerfile builds it from a pinned clone), but on a
bare host ``shutil.which`` returns ``None``, :data:`LabelRenderer.available` is
``False``, and every method is a no-op -- the program runs unchanged, just
without labels.

Reintroduced into mvp from the multivariate-math copy of the original (removed)
``mathdemos/_labels.py``; see
``tasks/archive/2026/11/03/graphing-calculator-latex-labels.md``.
"""

import ctypes
import hashlib
import os
import shutil
import subprocess
import tempfile
import typing

import numpy as np
import OpenGL.GL as GL
from OpenGL.GL import shaders as gl_shaders
from PIL import Image

#: The texExpToPng executable, or None if it is not installed.
TEXEXP: str | None = shutil.which("texExpToPng")
AVAILABLE: bool = TEXEXP is not None

_FLOATS_PER_VERT: int = 7  # center(3) + offset(2) + uv(2)
_VERTS: int = 6  # two triangles

#: A cached label: (texture id, pixel width, pixel height), or None if the
#: generation failed (cached so it is not retried every frame).
Label: typing.TypeAlias = tuple[int, int, int]


class LabelRenderer:
    """Generates and draws TeX billboard labels, or no-ops if texExpToPng is
    absent.

    Usage per frame::

        if labels.available:
            labels.begin(view_matrix, proj_matrix, (width, height))
            labels.draw(r"\\sin(x)", (x, y, 0.0))
            ...
            labels.end()
    """

    available: bool
    _dpi: int
    _fg: str
    _tex_cache: dict[str, Label | None]
    _cachedir: str | None
    _program: int
    _u_v: int
    _u_p: int
    _u_tex: int
    _vao: int
    _vbo: int
    _view: np.ndarray
    _proj: np.ndarray
    _vp: np.ndarray
    _vw: float
    _vh: float
    _prev_vao: int
    _prev_array_buffer: int
    _prev_blend: bool
    _prev_depth: bool

    def __init__(
        self, shader_dir: str, *, dpi: int = 600, fg: str = "rgb 1 1 1"
    ) -> None:
        self.available = AVAILABLE
        self._dpi = dpi
        self._fg = fg
        self._tex_cache = {}
        self._cachedir = None
        if not self.available:
            return
        self._cachedir = tempfile.mkdtemp(prefix="mvp_grapher_labels_")
        self._program = self._compile(shader_dir)
        self._u_v = GL.glGetUniformLocation(self._program, "vMatrix")
        self._u_p = GL.glGetUniformLocation(self._program, "pMatrix")
        self._u_tex = GL.glGetUniformLocation(self._program, "tex")
        self._vao = GL.glGenVertexArrays(1)
        self._vbo = GL.glGenBuffers(1)
        GL.glBindVertexArray(self._vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vbo)
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER,
            _VERTS * _FLOATS_PER_VERT * 4,
            None,
            GL.GL_DYNAMIC_DRAW,
        )
        stride: int = _FLOATS_PER_VERT * 4
        for loc, size, off in ((0, 3, 0), (1, 2, 3), (2, 2, 5)):
            GL.glEnableVertexAttribArray(loc)
            GL.glVertexAttribPointer(
                loc,
                size,
                GL.GL_FLOAT,
                GL.GL_FALSE,
                stride,
                ctypes.c_void_p(off * 4),
            )
        GL.glBindVertexArray(0)

    def _compile(self, shader_dir: str) -> int:
        def read(name: str) -> str:
            with open(os.path.join(shader_dir, name)) as f:
                return f.read()

        vs: int = gl_shaders.compileShader(
            read("billboard.vert"), GL.GL_VERTEX_SHADER
        )
        fs: int = gl_shaders.compileShader(
            read("billboard.frag"), GL.GL_FRAGMENT_SHADER
        )
        return gl_shaders.compileProgram(vs, fs)

    def _texture_for(self, latex: str) -> Label | None:
        if latex in self._tex_cache:
            return self._tex_cache[latex]
        result: Label | None = None
        png: str | None = self._generate(latex)
        if png is not None:
            result = self._load_texture(png)
        self._tex_cache[latex] = result
        return result

    def _generate(self, latex: str) -> str | None:
        if TEXEXP is None or self._cachedir is None:
            return None
        key: str = hashlib.sha1(
            f"{latex}|{self._dpi}|{self._fg}".encode()
        ).hexdigest()[:16]
        out: str = os.path.join(self._cachedir, key + ".png")
        if os.path.exists(out):
            return out
        try:
            subprocess.run(
                [
                    TEXEXP,
                    "--exp",
                    f"${latex}$",
                    "--size",
                    str(self._dpi),
                    "--fg",
                    self._fg,
                    "--bg",
                    "Transparent",
                    "--output",
                    out,
                ],
                cwd=self._cachedir,  # texExpToPng writes temp files in CWD
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            return None
        return out if os.path.exists(out) else None

    def _load_texture(self, png: str) -> Label:
        # Flip vertically: PIL is top-left origin, GL texture (0,0) is bottom
        # left.  (Image.Transpose enum: the module-level FLIP_TOP_BOTTOM
        # constant was removed in Pillow 10.)
        img: Image.Image = (
            Image.open(png)
            .convert("RGBA")
            .transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        )
        width: int = img.size[0]
        height: int = img.size[1]
        data: bytes = img.tobytes()
        tex: int = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE
        )
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGBA8,
            width,
            height,
            0,
            GL.GL_RGBA,
            GL.GL_UNSIGNED_BYTE,
            data,
        )
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        return (tex, width, height)

    def begin(
        self,
        view_matrix: np.ndarray,
        proj_matrix: np.ndarray,
        viewport: tuple[int, int],
    ) -> None:
        """Start a label pass: upload the view/projection, enable blending, turn
        depth testing off (labels read on top), and save the caller's VAO."""
        if not self.available:
            return
        self._view = np.ascontiguousarray(view_matrix, dtype=np.float32)
        self._proj = np.ascontiguousarray(proj_matrix, dtype=np.float32)
        # CPU copy (math convention, M @ column) for the behind-camera test.
        self._vp = np.asarray(proj_matrix, dtype=float) @ np.asarray(
            view_matrix, dtype=float
        )
        self._vw = float(viewport[0])
        self._vh = float(viewport[1])
        GL.glUseProgram(self._program)
        GL.glUniformMatrix4fv(self._u_v, 1, GL.GL_TRUE, self._view)
        GL.glUniformMatrix4fv(self._u_p, 1, GL.GL_TRUE, self._proj)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glUniform1i(self._u_tex, 0)
        # Save the caller's blend/depth enable state so end() restores exactly
        # what was set: grapher2d keeps GL_BLEND on for line smoothing and
        # grapher3d keeps GL_DEPTH_TEST on, so forcing a fixed state in end()
        # would silently break the next frame's rendering.
        self._prev_blend = bool(GL.glIsEnabled(GL.GL_BLEND))
        self._prev_depth = bool(GL.glIsEnabled(GL.GL_DEPTH_TEST))
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glDisable(GL.GL_DEPTH_TEST)
        # Save the caller's bindings so end() can restore them.
        self._prev_vao = int(GL.glGetIntegerv(GL.GL_VERTEX_ARRAY_BINDING))
        self._prev_array_buffer = int(
            GL.glGetIntegerv(GL.GL_ARRAY_BUFFER_BINDING)
        )
        GL.glBindVertexArray(self._vao)

    def draw(
        self,
        latex: str,
        center_world: typing.Sequence[float],
        *,
        height_px: float = 44.0,
    ) -> None:
        """Draw ``latex`` centered at world point ``center_world`` (xyz), sized
        to ``height_px`` screen pixels tall (width follows the glyph aspect)."""
        if not self.available:
            return
        tex: Label | None = self._texture_for(latex)
        if tex is None:
            return
        tex_id, img_w, img_h = tex
        c: np.ndarray = np.asarray(center_world, dtype=float).reshape(-1)[:3]
        clip: np.ndarray = self._vp @ np.array([c[0], c[1], c[2], 1.0])
        if clip[3] <= 1e-6:
            return  # behind the camera
        half_h: float = height_px / self._vh  # half-height in NDC
        half_w: float = (height_px * (img_w / img_h)) / self._vw  # pixel aspect
        corners: tuple[tuple[float, float, float, float], ...] = (
            (-half_w, -half_h, 0.0, 0.0),
            (half_w, -half_h, 1.0, 0.0),
            (half_w, half_h, 1.0, 1.0),
            (-half_w, -half_h, 0.0, 0.0),
            (half_w, half_h, 1.0, 1.0),
            (-half_w, half_h, 0.0, 1.0),
        )
        buf: np.ndarray = np.empty((_VERTS, _FLOATS_PER_VERT), dtype=np.float32)
        for i, (off_x, off_y, u, v) in enumerate(corners):
            buf[i] = (c[0], c[1], c[2], off_x, off_y, u, v)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vbo)
        GL.glBufferSubData(GL.GL_ARRAY_BUFFER, 0, buf.nbytes, buf)
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex_id)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, _VERTS)

    def end(self) -> None:
        """End a label pass: restore the caller's bindings and GL state."""
        if not self.available:
            return
        GL.glBindVertexArray(self._prev_vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._prev_array_buffer)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        if self._prev_blend:
            GL.glEnable(GL.GL_BLEND)
        else:
            GL.glDisable(GL.GL_BLEND)
        if self._prev_depth:
            GL.glEnable(GL.GL_DEPTH_TEST)
        else:
            GL.glDisable(GL.GL_DEPTH_TEST)

    def cleanup(self) -> None:
        """Delete the GL resources and the temp PNG cache dir."""
        if not self.available:
            return
        try:
            for entry in self._tex_cache.values():
                if entry is not None:
                    GL.glDeleteTextures([entry[0]])
            GL.glDeleteBuffers(1, [self._vbo])
            GL.glDeleteVertexArrays(1, [self._vao])
            GL.glDeleteProgram(self._program)
        except Exception:
            pass  # the GL context may already be gone at shutdown
        if self._cachedir:
            shutil.rmtree(self._cachedir, ignore_errors=True)
