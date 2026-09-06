# Code the Classics port: myriapod, with its rendering engine inlined.
#
# Game code derived from Raspberry Pi Press's "Code the Classics" (vol 1):
#   Copyright (c) 2019 Eben Upton <eben@raspberrypi.org>
# Inlined engine (audio, images, renderer, keyboard, loop):
#   Copyright (c) 2026 William Emerison Six
# SPDX-License-Identifier: BSD-2-Clause
# Full license text: ports/codetheclassics/LICENSE.
"""myriapod -- Centipede style shooter, from Code the Classics vol. 1, on
GLFW + OpenGL 3.3 core.

One self-contained file, read top to bottom like the course's demos: first
the small engine this game needs (a software audio mixer, an image loader, a
textured-quad renderer, the anchored Actor sprite, keyboard state), then the
game, then the loop the game itself owns. The myriapod segments' quarter
turns are geometric-algebra rotations (multiplication by the unit
pseudoscalar), see the segment-movement section.
"""

from __future__ import annotations

import os
import signal
import sys
import threading
import time
from collections.abc import Callable, Generator, Iterator, Sequence
from dataclasses import InitVar, dataclass, field
from enum import Enum, IntEnum
from random import choice, randint, random
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, cast

import gacalc.g3 as g3
import glfw
import numpy as np
import OpenGL.GL as GL
import sympy
from gacalc.g2 import Vector, e_12
from gacalc.transforms import (
    InvertibleFunction,
    identity,
    inverse,
    scale_non_uniform,
    to_matrix,
    translate,
)
from numpy.typing import NDArray
from PIL import Image as PILImage

# ===== engine: shared state =====

WIDTH: int = 480
HEIGHT: int = 800
TITLE: str = "Myriapod"

#: The directory holding this game's ``images/``, ``sounds/`` and ``music/``.
ASSET_ROOT: str = os.path.dirname(os.path.abspath(__file__))


class SpriteRenderer(Protocol):
    """What the game needs of a rendering pipeline: start a frame, then draw
    textured sprites into pixel space.

    ``Renderer`` below implements it with OpenGL 3.3 core + shaders (see
    boing_gl1.py for the fixed-function OpenGL 1.x rendering of the same
    interface).
    Protocols are structural: having the members IS implementing it, and the
    checker verifies that where the renderer is assigned to the
    ``SpriteRenderer``-typed ``renderer`` global (window section, below).
    Deliberately NOT declared by subclassing the protocol -- an explicit
    subclass would inherit the stub members, so a missing method would go
    unreported.
    """

    def begin_frame(
        self, fb_width: int | None = None, fb_height: int | None = None
    ) -> None: ...

    def draw_image(
        self, image: Image, topleft: tuple[float, float]
    ) -> None: ...


# ===== engine: audio =====
#
# Sound effects and the music track, mixed in software on ONE miniaudio
# output device: every effect is decoded into memory once, each play is a
# "voice" over that buffer, the music streams from disk in chunks, and the
# device's callback sums the live voices. Starting or stopping a voice is a
# flag flip -- zero device operations after startup. (One OS stream per
# voice, the earlier design, audibly clunked and eventually froze a game
# once the audio client slots ran out; see
# tasks/archive/2026/07/09/leadingedge-audio-clunk-and-freeze.md.)
#
# Audio is BEST EFFORT: if miniaudio can't be imported or no device opens,
# every call is a no-op and the game plays silently (as it does headless).

if TYPE_CHECKING:
    import miniaudio

#: interleaved float32 PCM at the mixing format
_PCM = NDArray[np.float32]

# the miniaudio module, or None if it isn't installed (Any: the sentinel
# and the module share a type)
_ma: Any = None
try:
    import miniaudio as _miniaudio

    _ma = _miniaudio
except Exception:  # pragma: no cover - depends on runtime env
    pass

# One mixing format for everything; decode/stream converts to it.
_SAMPLE_RATE = 44100
_CHANNELS = 2

# Cap the concurrent voices per effect so a rapidly re-fired sound (the
# ball hitting a bat) recycles its oldest voice instead of piling up.
_MAX_VOICES_PER_SOUND = 8


@dataclass(slots=True)
class _Voice:
    """One playing instance inside the mixer: a position in a shared sample
    buffer (an effect) or a pull-stream (the music), plus its volume.

    Mutated under the engine lock; consumed by the mixer callback.
    """

    samples: _PCM | None
    stream: Iterator[Any] | None
    volume: float
    #: frame offset into ``samples`` (buffer voices only)
    pos: int = field(default=0, init=False)
    done: bool = field(default=False, init=False)


@dataclass(slots=True)
class _Engine:
    """The single miniaudio PlaybackDevice + the software mixer feeding it."""

    #: Guards ``_voices`` between the game thread and the mixer callback.
    _lock: threading.Lock = field(default_factory=threading.Lock)
    #: Every live voice; the callback sums them and drops the finished ones.
    _voices: list[_Voice] = field(default_factory=list)
    #: The one output device, opened on the first play; None until then.
    _device: miniaudio.PlaybackDevice | None = None
    #: True once opening the device failed, so we never retry (audio off).
    _failed: bool = False

    # -- device ---------------------------------------------------------
    def _ensure_device(self) -> bool:
        if self._device is not None:
            return True
        if self._failed or _ma is None:
            return False
        try:
            device = _ma.PlaybackDevice(
                output_format=_ma.SampleFormat.FLOAT32,
                nchannels=_CHANNELS,
                sample_rate=_SAMPLE_RATE,
            )
            gen = self._mixer()
            next(gen)  # prime the generator protocol
            # numpy arrays satisfy the buffer protocol miniaudio consumes;
            # its stubs only admit bytes/array.array, hence the cast.
            device.start(cast(Any, gen))
            self._device = device
            return True
        except Exception:
            # no sound hardware (e.g. the headless build container):
            # audio becomes a no-op.
            self._failed = True
            return False

    # -- the mixer callback (runs on miniaudio's thread) ------------------
    def _mixer(self) -> Generator[_PCM, int, None]:
        required = yield np.zeros(0, dtype=np.float32)
        while True:
            out = np.zeros(required * _CHANNELS, dtype=np.float32)
            with self._lock:
                voices = list(self._voices)
            for v in voices:
                try:
                    self._mix_voice(v, out, required)
                except Exception:
                    v.done = True
            with self._lock:
                self._voices = [v for v in self._voices if not v.done]
            required = yield out

    def _mix_voice(self, v: _Voice, out: _PCM, frames: int) -> None:
        """Add up to ``frames`` frames of ``v`` into ``out`` (interleaved)."""
        filled = 0
        while filled < frames and not v.done:
            if v.stream is not None:
                chunk = self._next_stream_chunk(v)
                if chunk is None:
                    v.done = True
                    break
                take = min(frames - filled, len(chunk) // _CHANNELS)
                seg = chunk[: take * _CHANNELS]
                # stash any remainder for the next pull
                rest = chunk[take * _CHANNELS :]
                v.samples = rest if len(rest) else None
            else:
                assert v.samples is not None
                total = len(v.samples) // _CHANNELS
                if v.pos >= total:
                    v.done = True
                    break
                take = min(frames - filled, total - v.pos)
                seg = v.samples[v.pos * _CHANNELS : (v.pos + take) * _CHANNELS]
                v.pos += take
            sl = slice(filled * _CHANNELS, (filled + take) * _CHANNELS)
            out[sl] += seg * v.volume
            filled += take

    def _next_stream_chunk(self, v: _Voice) -> _PCM | None:
        """The music path: the leftover stash, else the next decoded chunk."""
        if v.samples is not None and len(v.samples):
            chunk, v.samples = v.samples, None
            return chunk
        assert v.stream is not None
        try:
            return np.asarray(next(v.stream), dtype=np.float32)
        except StopIteration:
            return None

    # -- game-thread API ---------------------------------------------------
    def play_buffer(self, samples: _PCM, volume: float) -> _Voice | None:
        if not self._ensure_device():
            return None
        v = _Voice(samples, None, volume)
        with self._lock:
            self._voices.append(v)
        return v

    def play_stream(
        self, stream: Iterator[Any], volume: float
    ) -> _Voice | None:
        if not self._ensure_device():
            return None
        v = _Voice(None, stream, volume)
        with self._lock:
            self._voices.append(v)
        return v

    def stop_voice(self, v: _Voice) -> None:
        with self._lock:
            v.done = True

    def shutdown(self) -> None:
        """Stop the output device and its native callback thread.

        miniaudio's ``PlaybackDevice`` runs its mixer callback on a background
        thread that is NOT a Python ``threading.Thread``; if it is left running
        when the game loop ends, the process hangs on exit -- the window closes
        but Python never returns (seen on real hardware playing music; headless
        the device never opens, so this is a no-op there). Closing the device
        stops that thread. Idempotent and best-effort -- audio is optional.

        The device is closed with the lock RELEASED: ``close()`` joins the
        callback thread, which itself takes ``self._lock`` in the mixer, so
        holding it here would deadlock.
        """
        with self._lock:
            self._voices = []
            device = self._device
            self._device = None
        if device is not None:
            try:
                device.close()
            except Exception:
                pass


_engine = _Engine()


def shutdown_audio() -> None:
    """Tear down the audio backend at game exit (see :meth:`_Engine.shutdown`)."""
    _engine.shutdown()


def _decode(path: str) -> _PCM:
    decoded = _ma.decode_file(
        path,
        output_format=_ma.SampleFormat.FLOAT32,
        nchannels=_CHANNELS,
        sample_rate=_SAMPLE_RATE,
    )
    return np.asarray(decoded.samples, dtype=np.float32)


@dataclass(slots=True)
class Sound:
    """A sound effect: decoded ONCE into a shared buffer on first play; each
    play is a lightweight mixer voice over that buffer, so plays overlap."""

    path: str
    #: The decoded PCM, filled on the first play.
    _samples: _PCM | None = field(default=None, init=False)
    #: This effect's live voices (capped at ``_MAX_VOICES_PER_SOUND``).
    _voices: list[_Voice] = field(default_factory=list, init=False)

    def _buffer(self) -> _PCM | None:
        if self._samples is None:
            try:
                self._samples = _decode(self.path)
            except Exception:
                return None
        return self._samples

    def _live(self) -> list[_Voice]:
        self._voices = [v for v in self._voices if not v.done]
        return self._voices

    def play(self) -> None:
        """Play the effect, overlapping any prior plays still sounding."""
        if _ma is None:
            return
        buf = self._buffer()
        if buf is None:
            return
        live = self._live()
        if len(live) >= _MAX_VOICES_PER_SOUND:
            _engine.stop_voice(live[0])  # oldest voice yields its budget
        v = _engine.play_buffer(buf, 1.0)
        if v is not None:
            self._voices.append(v)


@dataclass(slots=True)
class _Music:
    """The single streamed, looping background track."""

    #: The playing track's voice, or None when stopped.
    _voice: _Voice | None = None
    _volume: float = 1.0
    #: Read by the stream generator at the end of each pass through the file.
    _looping: bool = False

    def _path(self, name: str) -> str | None:
        """Resolve a track ``name`` to a file under ``music/``, or ``None``."""
        base: str = os.path.join(ASSET_ROOT, "music", name)
        if os.path.isfile(base):
            return base
        for ext in ("ogg", "mp3", "wav"):
            p: str = base + "." + ext
            if os.path.exists(p):
                return p
        return None

    def _stream(self, path: str) -> Iterator[Any]:
        outer = self

        def gen() -> Iterator[Any]:
            # music streams from disk (a decoded multi-minute track would be
            # tens of MB); looping restarts the stream, so the loop seam
            # lands on a chunk boundary.
            while True:
                inner = _ma.stream_file(
                    path,
                    output_format=_ma.SampleFormat.FLOAT32,
                    nchannels=_CHANNELS,
                    sample_rate=_SAMPLE_RATE,
                    frames_to_read=1024,
                )
                for chunk in inner:
                    yield chunk
                if not outer._looping:
                    return

        return gen()

    def play(self, name: str) -> None:
        """Play track ``name`` on loop, replacing whatever was playing."""
        if _ma is None:
            return
        p: str | None = self._path(name)
        if not p:
            self.stop()
            return
        try:
            self.stop()
            self._looping = True
            self._voice = _engine.play_stream(self._stream(p), self._volume)
        except Exception:
            self._voice = None

    def set_volume(self, v: float) -> None:
        """Set the music volume (0.0-1.0), applied to the current track if any."""
        self._volume = v
        if self._voice is not None and not self._voice.done:
            self._voice.volume = v

    def stop(self) -> None:
        """Stop the current track."""
        self._looping = False
        if self._voice is not None:
            _engine.stop_voice(self._voice)
            self._voice = None


music = _Music()

# ===== engine: images and sounds =====
#
# ``images.load("ball")`` reads ``images/ball.png`` once and caches it;
# ``sounds.load("hit0")`` does the same under ``sounds/``. An image decodes to
# a CPU RGBA array immediately, so its size is known before the window exists
# (game objects are built at import time), but its GL texture is uploaded
# lazily on first draw, because the GL context doesn't exist yet at import.


@dataclass(slots=True, eq=False)
class Image:
    """A loaded image: CPU pixels now, GL texture on first draw. Built by
    :meth:`Image.load` (or :meth:`Image.from_rgba` for rendered text)."""

    #: H x W x 4 uint8 pixels, straight alpha
    rgba: NDArray[np.uint8]
    #: The GL texture name, uploaded lazily by gl_texture()
    _tex: int | None = field(default=None, init=False)

    @property
    def width(self) -> int:
        return int(self.rgba.shape[1])

    @property
    def height(self) -> int:
        return int(self.rgba.shape[0])

    def gl_texture(self) -> int:
        """Return this image's GL texture name, uploading it to the GPU on first call."""
        if self._tex is None:
            self._tex = GL.glGenTextures(1)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._tex)
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST
            )
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST
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
                GL.GL_RGBA,
                self.width,
                self.height,
                0,
                GL.GL_RGBA,
                GL.GL_UNSIGNED_BYTE,
                self.rgba,
            )
        return cast(int, self._tex)

    @classmethod
    def from_rgba(cls, arr: NDArray[Any]) -> Image:
        """Wrap an H x W x 4 array (e.g. rendered text) as an :class:`Image`."""
        return cls(np.ascontiguousarray(arr.astype(np.uint8)))

    @classmethod
    def load(cls, path: str) -> Image:
        """Decode the image file at ``path`` into an :class:`Image`."""
        # Decode with Pillow + convert("RGBA").  This correctly turns palette
        # (mode "P") transparency and grayscale/LA into a real alpha channel --
        # imageio drops palette transparency (returns 3-channel RGB), which made
        # transparent sprite backgrounds render as opaque white boxes.
        return cls.from_rgba(np.array(PILImage.open(path).convert("RGBA")))


@dataclass(slots=True)
class _Loader[T]:
    """A cached loader for one asset folder: ``load(name)`` finds
    ``<ASSET_ROOT>/<subdir>/<name>.<ext>`` and builds it once with ``make``."""

    #: The folder under ``ASSET_ROOT`` ("images", "sounds").
    subdir: str
    #: Extensions tried, in order, when ``name`` has none.
    extns: tuple[str, ...]
    #: Builds the asset from its path (``Image`` or ``Sound``).
    make: Callable[[str], T]
    _cache: dict[str, T] = field(default_factory=dict, init=False)

    def _path(self, name: str) -> str | None:
        """Resolve ``name`` to an on-disk path under the folder, or ``None``."""
        base: str = os.path.join(ASSET_ROOT, self.subdir, name)
        if os.path.isfile(base):
            return base
        for ext in self.extns:
            p: str = base + "." + ext
            if os.path.exists(p):
                return p
        return None

    def load(self, name: str) -> T:
        """Load (and cache) the asset ``name``; raise ``KeyError`` if absent."""
        if name not in self._cache:
            p: str | None = self._path(name)
            if p is None:
                raise KeyError(
                    f"No {self.subdir[:-1]} found like {name!r} in {self.subdir}/"
                )
            self._cache[name] = self.make(p)
        return self._cache[name]


images: _Loader[Image] = _Loader(
    "images", ("png", "gif", "jpg", "jpeg", "bmp"), Image.load
)
sounds: _Loader[Sound] = _Loader("sounds", ("ogg", "wav", "oga"), Sound)

# ===== engine: renderer (OpenGL 3.3 core) =====
#
# The game positions its sprites in a top-left-origin, y-down pixel space. An
# orthographic projection (ortho_pixels) maps that space to NDC, and every
# sprite is the unit quad, scaled to the image's size and translated to its
# top-left corner, textured with the image. Matrices are row-major numpy,
# uploaded with ``transpose=GL_TRUE``.


def _identity() -> NDArray[np.float32]:
    """Return a 4x4 identity matrix."""
    return np.identity(4, dtype=np.float32)


# The sprite's model matrix (scale the unit quad to w x h, then move it to
# (tx, ty) pixels) and the orthographic projection are DEFINED with gacalc's
# transforms -- the course's own math -- and converted to the GL 4x4 by
# ``to_matrix``, which puts the translation in the last column (column vectors,
# premultiply; the ``GL_TRUE`` on upload transposes into GL's layout). The model
# matrix is needed per sprite per frame, so it is converted ONCE, at import,
# over sympy symbols, into a template that a draw fills by poking four numbers:
# 0.47 microseconds a sprite, against 3.19 for two numpy matrices and a matmul
# (tasks/reference/gacalc-transforms-in-the-renderer.md).


@dataclass(slots=True, frozen=True)
class MatrixTemplate:
    """A 4x4 matrix with a few varying entries: its constant part, and the
    (row, column, parameter) of each entry that is a parameter -- read off a
    gacalc transform built over sympy symbols. Build one with
    :meth:`MatrixTemplate.compile`.
    """

    #: the matrix with every parameter entry zeroed
    constants: NDArray[np.float32]
    #: (row, column, index into fill()'s arguments) per parameter entry
    slots: tuple[tuple[int, int, int], ...]

    @classmethod
    def compile(
        cls, fn: InvertibleFunction[g3.Vector], params: Sequence[sympy.Symbol]
    ) -> MatrixTemplate:
        """The template of ``fn``, a gacalc transform over the symbols ``params``."""
        m = to_matrix(fn, g3.Vector, backend="sympy")
        assert isinstance(m, sympy.Matrix)
        constants: NDArray[np.float32] = np.array(
            [
                [
                    0.0 if m[i, j].free_symbols else float(m[i, j])
                    for j in range(4)
                ]
                for i in range(4)
            ],
            dtype=np.float32,
        )
        slots = tuple(
            (i, j, params.index(m[i, j]))
            for i in range(4)
            for j in range(4)
            if m[i, j].free_symbols
        )
        return cls(constants, slots)

    def fill(self, *params: float) -> NDArray[np.float32]:
        """The matrix for these parameter values."""
        m: NDArray[np.float32] = self.constants.copy()
        for row, col, k in self.slots:
            m[row, col] = params[k]
        return m


_TX, _TY, _W, _H = sympy.symbols("tx ty w h")
#: The model matrix: scale the unit quad to (w, h), then translate to (tx, ty);
#: ``MODEL.fill(tx, ty, w, h)``
MODEL: MatrixTemplate = MatrixTemplate.compile(
    translate(b=_TX * g3.Vector.e_1 + _TY * g3.Vector.e_2)
    @ scale_non_uniform(_W, _H, 1),
    (_TX, _TY, _W, _H),
)


def ortho_pixels(width: float, height: float) -> NDArray[np.float32]:
    """Map pixel space (0,0)=top-left .. (width,height)=bottom-right to NDC:
    scale to a 2 x 2 box (y flipped, z into the clip range), then move its
    corner to (-1, 1). Built once per renderer.
    """
    return np.asarray(
        to_matrix(
            translate(b=-1 * g3.Vector.e_1 + 1 * g3.Vector.e_2)
            @ scale_non_uniform(2.0 / width, -2.0 / height, -1),
            g3.Vector,
        ),
        dtype=np.float32,
    )


# One shader program, shared by all the games' renderers: textured (sprites)
# or flat colour, switched by uUseTex and multiplied by uTint. boing only ever
# draws textured, untinted sprites, so uUseTex stays 1 and uTint stays white;
# the flat-colour branch is kept so this renderer is the same program the
# richer games run.

_VERT = """
#version 330 core
layout(location = 0) in vec2 aPos;
uniform mat4 uOrtho;
uniform mat4 uModel;
uniform vec2 uTexOffset;
uniform vec2 uTexScale;
out vec2 vTex;
void main() {
    vTex = aPos * uTexScale + uTexOffset;
    gl_Position = uOrtho * uModel * vec4(aPos, 0.0, 1.0);
}
"""

_FRAG = """
#version 330 core
in vec2 vTex;
uniform sampler2D uTex;
uniform vec4 uTint;
uniform bool uUseTex;
out vec4 frag;
void main() {
    if (uUseTex) {
        frag = texture(uTex, vTex) * uTint;
    } else {
        frag = uTint;
    }
}
"""


def _compile(src: str, kind: Any) -> int:
    """Compile one GLSL shader of the given ``kind``; raise on a compile error.

    ``kind`` is a PyOpenGL ``GL_*_SHADER`` constant (opaque, so typed ``Any``).
    """
    sid: int = GL.glCreateShader(kind)
    GL.glShaderSource(sid, src)
    GL.glCompileShader(sid)
    if GL.glGetShaderiv(sid, GL.GL_COMPILE_STATUS) != GL.GL_TRUE:
        raise RuntimeError(GL.glGetShaderInfoLog(sid).decode())
    return sid


@dataclass(slots=True, eq=False)
class Uniforms:
    """The shader program's uniform locations, queried once after linking."""

    ortho: int
    model: int
    tint: int
    use_tex: int
    tex: int
    tex_off: int
    tex_scale: int


@dataclass(slots=True, eq=False)
class GLBuffer:
    """A vertex array object and the vertex buffer it reads 2-D positions
    (attribute 0) from."""

    vao: int
    vbo: int


def _link_program() -> int:
    """Compile both shaders and link them into a program; raise on failure."""
    vs: int = _compile(src=_VERT, kind=GL.GL_VERTEX_SHADER)
    fs: int = _compile(src=_FRAG, kind=GL.GL_FRAGMENT_SHADER)
    program: int = GL.glCreateProgram()
    GL.glAttachShader(program, vs)
    GL.glAttachShader(program, fs)
    GL.glLinkProgram(program)
    if GL.glGetProgramiv(program, GL.GL_LINK_STATUS) != GL.GL_TRUE:
        raise RuntimeError(GL.glGetProgramInfoLog(program).decode())
    GL.glDeleteShader(vs)
    GL.glDeleteShader(fs)
    return program


def _make_buffer(data: NDArray[np.float32] | None) -> GLBuffer:
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


@dataclass(slots=True, eq=False)
class Renderer:
    """The GL state a frame needs: the program, its uniforms, the unit-quad
    buffer and the pixel-space projection. Build one with
    :meth:`Renderer.create` once the GL context exists; the constructor takes
    already-linked GL objects (tests, or another backend, may pass their own).
    """

    #: logical (game) pixels
    width: int
    height: int
    #: Maps pixel space to NDC (row-major; uploaded transposed).
    ortho: NDArray[np.float32]
    program: int
    uniforms: Uniforms
    #: The unit quad [0,1]x[0,1] as two triangles -- every sprite's geometry
    quad: GLBuffer
    #: Framebuffer pixels -- may exceed logical on HiDPI / scaled displays.
    #: Updated every begin_frame from the real framebuffer size.
    fb_width: int = field(init=False)
    fb_height: int = field(init=False)

    def __post_init__(self) -> None:
        self.fb_width = self.width
        self.fb_height = self.height

    def begin_frame(
        self, fb_width: int | None = None, fb_height: int | None = None
    ) -> None:
        """Start a frame: update framebuffer size, clear, bind the program + ortho."""
        if fb_width and fb_height:
            self.fb_width = fb_width
            self.fb_height = fb_height
        GL.glDisable(GL.GL_SCISSOR_TEST)
        GL.glViewport(0, 0, self.fb_width, self.fb_height)
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        GL.glUseProgram(self.program)
        GL.glUniformMatrix4fv(self.uniforms.ortho, 1, GL.GL_TRUE, self.ortho)

    def draw_image(self, image: Image, topleft: tuple[float, float]) -> None:
        """Draw ``image`` as a textured quad with its top-left at ``topleft``."""
        tx, ty = topleft
        model: NDArray[np.float32] = MODEL.fill(
            tx, ty, image.width, image.height
        )
        GL.glBindVertexArray(self.quad.vao)
        GL.glUniformMatrix4fv(self.uniforms.model, 1, GL.GL_TRUE, model)
        GL.glUniform2f(self.uniforms.tex_off, 0.0, 0.0)
        GL.glUniform2f(self.uniforms.tex_scale, 1.0, 1.0)
        GL.glUniform1i(self.uniforms.use_tex, 1)
        GL.glUniform4f(self.uniforms.tint, 1.0, 1.0, 1.0, 1.0)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, image.gl_texture())
        GL.glUniform1i(self.uniforms.tex, 0)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)

    @classmethod
    def create(cls, width: int, height: int) -> Renderer:
        """Build the renderer for a ``width`` x ``height`` pixel game: link the
        program, query its uniforms, upload the unit quad, set the blend
        state. Needs a current GL context."""
        program: int = _link_program()
        uniforms = Uniforms(
            ortho=GL.glGetUniformLocation(program, "uOrtho"),
            model=GL.glGetUniformLocation(program, "uModel"),
            tint=GL.glGetUniformLocation(program, "uTint"),
            use_tex=GL.glGetUniformLocation(program, "uUseTex"),
            tex=GL.glGetUniformLocation(program, "uTex"),
            tex_off=GL.glGetUniformLocation(program, "uTexOffset"),
            tex_scale=GL.glGetUniformLocation(program, "uTexScale"),
        )
        quad_verts: NDArray[np.float32] = np.array(
            [0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1], dtype=np.float32
        )
        quad = _make_buffer(quad_verts)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glDisable(GL.GL_DEPTH_TEST)
        return cls(
            width,
            height,
            ortho_pixels(width=width, height=height),
            program,
            uniforms,
            quad,
        )


# ===== window and GL context =====
# This file is a program, not a module: from here on it acquires resources (a
# window, a GL context, later the sound device) and then runs the game loop.
# A tool that imports it to inspect it stops here instead of opening a window.
if __name__ != "__main__":
    sys.exit("this is a game, run it directly rather than importing it")

# Like the course's demos, the window and the renderer are created right
# here at module level, before any game object exists; if either fails the
# exception ends the program. Everything below can use ``renderer`` directly.
if not glfw.init():
    raise RuntimeError("glfw.init() failed")
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
window = glfw.create_window(WIDTH, HEIGHT, TITLE, None, None)
if not window:
    glfw.terminate()
    raise RuntimeError("glfw.create_window() failed")
glfw.make_context_current(window)
glfw.swap_interval(1)
# macOS core profile requires a non-zero VAO bound at all times.
GL.glBindVertexArray(GL.glGenVertexArrays(1))
renderer: SpriteRenderer = Renderer.create(WIDTH, HEIGHT)

# ===== engine: sprite drawing =====
# Backgrounds, blocks, text and status icons are drawn by name at a top-left
# pixel position; the moving objects are Actors (next section).


def blit(name: str, x: float, y: float) -> None:
    """Draw sprite ``name`` with its TOP-LEFT at ``(x, y)``."""
    renderer.draw_image(images.load(name), (x, y))


# ===== engine: rectangles and sprites =====
#
# An Actor is an image positioned by an anchor (default: its centre) in the
# top-left-origin pixel space, backed by a float rectangle so movement at
# non-integer speeds keeps its sub-pixel position. The game's objects subclass
# Actor: ``actor.image = "name"`` swaps the sprite keeping the anchor position,
# and ``.pos`` / ``.x`` / ``.y`` are the anchor position (``.pos`` as a gacalc
# vector, so game code adds velocities and takes differences directly).

#: A position the engine accepts: a pair, or a gacalc vector (both unpack).
#: Why a union and not one type -- measured, with the numbers -- is
#: tasks/reference/point-type-decision.md: the boundary unpack costs 0.05-0.13
#: microseconds, upstream's literal tuples stay as written, and all arithmetic
#: is on Vector.
PointLike = tuple[float, float] | Vector
#: An anchor: per axis a named fraction ("left"/"center"/...) or a pixel offset.
Anchor = tuple[str | float, str | float]

_ANCHOR_FRAC: dict[str, dict[str, float]] = {
    "x": {"left": 0.0, "center": 0.5, "middle": 0.5, "right": 1.0},
    "y": {"top": 0.0, "center": 0.5, "middle": 0.5, "bottom": 1.0},
}


def _anchor_component(value: str | float, dim: str, total: float) -> float:
    """Resolve one anchor component: a named fraction of ``total``, or pixels."""
    if isinstance(value, str):
        return total * _ANCHOR_FRAC[dim][value]
    return float(value)


@dataclass(slots=True)
class Rect:
    """An axis-aligned rectangle in pixel space, float coordinates."""

    left: float
    top: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.left + self.width

    @property
    def bottom(self) -> float:
        return self.top + self.height

    @property
    def centerx(self) -> float:
        return self.left + self.width / 2

    @property
    def centery(self) -> float:
        return self.top + self.height / 2

    @property
    def center(self) -> tuple[float, float]:
        return (self.centerx, self.centery)

    @property
    def topleft(self) -> tuple[float, float]:
        return (self.left, self.top)

    def collidepoint(self, p: PointLike) -> bool:
        """Return whether the point ``p`` lies inside (edges: left/top in)."""
        px, py = p
        return self.left <= px < self.right and self.top <= py < self.bottom


class Actor:
    """A sprite: an image positioned by an anchor (default: its centre).

    Not a dataclass: its setup is ordered (image, then size, then position)
    and everything game-facing is a property over the private rect. The four
    slots make the whole Actor hierarchy dict-free once the subclasses are
    ``slots=True`` dataclasses.
    """

    __slots__ = ("_rect", "_anchor_value", "_image", "_image_name")

    def __init__(
        self,
        image: str,
        pos: PointLike | None = None,
        anchor: Anchor | None = None,
    ) -> None:
        self._anchor_value: Anchor = (
            anchor if anchor is not None else ("center", "center")
        )
        self._image: Image = images.load(image)
        self._image_name: str = image
        self._rect: Rect = Rect(
            0.0, 0.0, float(self._image.width), float(self._image.height)
        )
        if pos is not None:
            self._set_pos(pos)

    # -- image ----------------------------------------------------------------
    def _set_image(self, name: str) -> None:
        """Swap the sprite to ``name``, keeping the anchor position."""
        keep: Vector = self._anchor_pos()
        self._image = images.load(name)
        self._image_name = name
        self._rect.width = float(self._image.width)
        self._rect.height = float(self._image.height)
        self._set_pos(keep)

    # -- anchor / position ----------------------------------------------------
    def _anchor_offset(self) -> Vector:
        """Return the anchor's pixel offset from the rect's top-left corner."""
        ax, ay = self._anchor_value
        return Vector(
            _anchor_component(ax, "x", self._rect.width),
            _anchor_component(ay, "y", self._rect.height),
        )

    def _anchor_pos(self) -> Vector:
        """Return the anchor position: the top-left corner plus the offset."""
        return Vector(self._rect.left, self._rect.top) + self._anchor_offset()

    def _set_pos(self, pos: PointLike) -> None:
        """Move the sprite so its anchor lands on ``pos``."""
        # Vector(*pos) accepts a pair OR a gacalc vector (both iterate to x, y).
        # float(): gacalc's .x/.y are Coef (float | sympy Expr); the rect is float.
        topleft: Vector = Vector(*pos) - self._anchor_offset()
        self._rect.left = float(topleft.x)
        self._rect.top = float(topleft.y)

    # -- the game-facing surface, as properties -------------------------------
    # float(): gacalc's Vector .x/.y are Coef (float | sympy Expr), not float.
    @property
    def x(self) -> float:
        return float(self._anchor_pos().x)

    @x.setter
    def x(self, value: float) -> None:
        self._set_pos((value, float(self._anchor_pos().y)))

    @property
    def y(self) -> float:
        return float(self._anchor_pos().y)

    @y.setter
    def y(self, value: float) -> None:
        self._set_pos((float(self._anchor_pos().x), value))

    @property
    def pos(self) -> Vector:
        return self._anchor_pos()

    @pos.setter
    def pos(self, value: PointLike) -> None:
        self._set_pos(value)

    @property
    def image(self) -> str:
        return self._image_name

    @image.setter
    def image(self, name: str) -> None:
        self._set_image(name)

    @property
    def anchor(self) -> Anchor:
        return self._anchor_value

    @anchor.setter
    def anchor(self, value: Anchor) -> None:
        self._anchor_value = value

    @property
    def top(self) -> float:
        return self._rect.top

    @property
    def bottom(self) -> float:
        return self._rect.bottom

    @property
    def center(self) -> tuple[float, float]:
        return self._rect.center

    # -- drawing & geometry ---------------------------------------------------
    def draw(self) -> None:
        """Draw the sprite at its current position."""
        renderer.draw_image(self._image, self._rect.topleft)

    def collidepoint(self, p: PointLike) -> bool:
        """Return whether the point ``p`` lies within this sprite's rect."""
        return self._rect.collidepoint(p)


# ===== engine: keyboard =====
#
# ``keyboard.<name>`` is True while that key is held. The GLFW key callback
# below feeds presses and releases in; the game polls the names in the table
# each frame -- they are the only keys myriapod reads.

_NAME_TO_KEY: dict[str, int] = {
    "left": glfw.KEY_LEFT,
    "right": glfw.KEY_RIGHT,
    "up": glfw.KEY_UP,
    "down": glfw.KEY_DOWN,
    "space": glfw.KEY_SPACE,
}


@dataclass(slots=True)
class Keyboard:
    """``keyboard.<name>`` is True while that key is held."""

    #: GLFW key codes currently held down.
    _pressed: set[int] = field(default_factory=set)

    def press(self, key: int) -> None:
        """Mark GLFW key code ``key`` as held (called from the key callback)."""
        self._pressed.add(key)

    def release(self, key: int) -> None:
        """Mark GLFW key code ``key`` as released."""
        self._pressed.discard(key)

    def __getattr__(self, name: str) -> bool:
        """Return whether the named key (``keyboard.space``, ...) is held."""
        code: int | None = _NAME_TO_KEY.get(name)
        if code is None:
            raise AttributeError(name)
        return code in self._pressed


keyboard = Keyboard()


def _key_cb(win: Any, key: int, scancode: int, action: int, mods: int) -> None:
    if action == glfw.PRESS:
        keyboard.press(key)
        if key == glfw.KEY_ESCAPE:  # Esc always quits (no title-bar needed)
            glfw.set_window_should_close(win, True)
    elif action == glfw.RELEASE:
        keyboard.release(key)


glfw.set_key_callback(window, _key_cb)

# ===== game code =====

DEBUG_TEST_RANDOM_POSITIONS: bool = False

#: Sprites are positioned by an anchor point; most are anchored at their centre
CENTRE_ANCHOR: Anchor = ("center", "center")

num_grid_rows: int = 25
num_grid_cols: int = 14


# Convert a position in pixel units to a position in grid units. In this game, a grid square is 32 pixels.
def pos2cell(x: float, y: float) -> tuple[int, int]:
    return ((int(x) - 16) // 32, int(y) // 32)


# Convert grid cell position to pixel coordinates, with a given offset
def cell2pos(
    cell_x: int, cell_y: int, x_offset: int = 0, y_offset: int = 0
) -> tuple[int, int]:
    # If the requested offset is zero, returns the centre of the requested cell, hence the +16. In the case of the
    # X axis, there's a 16 pixel border at the left and right of the screen, hence +16 becomes +32.
    return ((cell_x * 32) + 32 + x_offset, (cell_y * 32) + 16 + y_offset)


# A 90-degree turn in the e_1 e_2 plane. In 2-D geometric algebra that turn IS
# multiplication by the unit pseudoscalar e_12: (x, y) -> (-y, x). It is EXACT
# (e_12's components are +/-1, so no sin/cos and no floating-point error, unlike
# a general rotate(theta) rotor). Named as an InvertibleFunction so it composes:
# a segment's entry edge selects a 0/90/180/270-degree turn (I^0..I^3), which is
# rotate_90_degrees applied in_edge times -- the _rotations table below.
rotate_90_degrees: InvertibleFunction[Vector] = InvertibleFunction(
    func=lambda v: v * e_12,
    latex_repr=r"R_{+90}",
    inverse=lambda v: v * -e_12,
    latex_repr_inv=r"R_{-90}",
)
# Rotating 90 degrees twice is multiplication by e_12^2 = -1: a 180-degree turn
# is negation (its own inverse) -- cheaper than composing rotate_90_degrees with
# itself.
rotate_180_degrees: InvertibleFunction[Vector] = InvertibleFunction(
    func=lambda v: v * -1,
    latex_repr=r"R_{180}",
    inverse=lambda v: v * -1,
    latex_repr_inv=r"R_{180}",
)
# in_edge selects the turn: identity, +90, 180, +270. Rotating three times is
# exactly the inverse of rotating once (e_12^3 = -e_12), so the last entry is
# inverse(rotate_90_degrees) rather than three composed turns.
_rotations: list[InvertibleFunction[Vector]] = [
    identity(),
    rotate_90_degrees,
    rotate_180_degrees,
    inverse(rotate_90_degrees),
]


class GameObject(Protocol):
    """What Game.update and Game.draw need of everything in play: a per-frame
    update and a draw. Every Actor subclass below satisfies it structurally
    (deliberately not by subclassing the protocol -- an explicit subclass
    inherits the stub members, so a missing method would go unreported).
    """

    def update(self) -> None: ...

    def draw(self) -> None: ...


# (eq=False on these Actor dataclasses keeps identity comparison/hashing --
# the generated __eq__ would compare fields and set __hash__ to None; slots=True
# fixes each object's attribute set to its declared fields, so every attribute
# an object ever gets is declared below)
@dataclass(eq=False, slots=True)
class Explosion(Actor):
    #: named spawn_pos, NOT pos: pos is an Actor property, and a dataclass
    #: would treat the property object as this field's default value
    spawn_pos: InitVar[PointLike]
    #: 0 = rock hit, 1 = the player exploding, 2 = a segment or meanie
    type: int
    timer: int = 0

    def __post_init__(self, spawn_pos: PointLike) -> None:
        super().__init__("blank", spawn_pos)

    def update(self) -> None:
        self.timer += 1

        # Set sprite based on explosion type and timer - update to a new image
        # every four frames
        self.image = f"exp{self.type}{self.timer // 4}"


@dataclass(eq=False, slots=True)
class Player(Actor):
    INVULNERABILITY_TIME: ClassVar[int] = 100
    RESPAWN_TIME: ClassVar[int] = 100
    RELOAD_TIME: ClassVar[int] = 10

    spawn_pos: InitVar[PointLike]
    #: These determine which frame of animation the player sprite will use
    direction: int = 0
    frame: int = 0
    lives: int = 3
    alive: bool = True
    #: timer is used for animation, respawning and for ensuring the player is
    #: invulnerable immediately after respawning
    timer: int = 0
    #: When the player shoots, this is set to RELOAD_TIME - it then counts
    #: down - when it reaches zero the player can shoot again
    fire_timer: int = 0

    def __post_init__(self, spawn_pos: PointLike) -> None:
        super().__init__("blank", spawn_pos)

    def move(self, dx: int, dy: int, speed: int) -> None:
        # dx and dy will each be either 0, -1 or 1. speed is an integer indicating
        # how many pixels we should move in the specified direction.
        for _ in range(speed):
            # For each pixel we want to move, we must first check if it's a valid place to move to
            if game.allow_movement(self.x + dx, self.y + dy):
                self.x += dx
                self.y += dy

    def update(self) -> None:
        self.timer += 1

        if self.alive:
            # Get keyboard input. dx and dy represent the direction the player is facing on each axis
            dx: int = -1 if keyboard.left else 1 if keyboard.right else 0
            dy: int = -1 if keyboard.up else 1 if keyboard.down else 0

            # Move in the relevant directions by the specified number of pixels. The purpose of 3 - abs(dy) is to
            # generate vectors which look either like (3,0) (which is 3 units long) or (2, 2) (which is sqrt(8) long)
            # so we move roughly the same distance regardless of whether we're travelling straight along the x or y axis.
            # or at 45 degrees. Without this, we would move noticeably faster when travelling diagonally.
            self.move(dx, 0, 3 - abs(dy))
            self.move(0, dy, 3 - abs(dx))

            # When the player presses a key to start handing in a new direction, we don't want the sprite to just
            # instantly change to facing in that new direction. That would look wrong, since in the real world vehicles
            # can't just suddenly change direction in the blink of an eye.
            # Instead, we want the vehicle to turn to face the new direction over several frames. If the vehicle is
            # currently facing down, and the player presses the left arrow key, the vehicle should first turn to face
            # diagonally down and to the left, and then turn to face left.

            # Each number in the following list corresponds to a direction - 0 is up, 1 is up and to the right, and
            # so on in clockwise order. -1 means no direction.
            # Think of it as a grid, as follows:
            # 7  0  1
            # 6 -1  2
            # 5  4  3
            directions: list[int] = [7, 0, 1, 6, -1, 2, 5, 4, 3]

            # But! If you look at the values that self.direction actually takes on during the game, you only see
            # numbers from 0 to 3. This is because although there are eight possible directions of travel, there are
            # only four orientations of the player vehicle. The same sprite, for example, is used if the player is
            # travelling either left or right. This is why the direction is ultimately clamped to a range of 0 to 4.
            # 0 = facing up or down
            # 1 = facing top right or bottom left
            # 2 = facing left or right
            # 3 = facing bottom right or top left

            # # It can be useful to think of the vehicle as being able to drive both forwards and backwards.

            # Choose the relevant direction from the above list, based on dx and dy
            dir: int = directions[dx + 3 * dy + 4]

            # Every other frame, if the player is pressing a key to move in a particular direction, update the current
            # direction to rotate towards facing the new direction
            if self.timer % 2 == 0 and dir >= 0:
                # We first calculate the difference between the desired direction and the current direction.
                difference: int = dir - self.direction

                # We use the following list to decide how much to rotate by each frame, based on difference.
                # It's easiest to think about this by just considering the first four direction values - 0 to 3,
                # corresponding to facing up, to fit into the bottom right. However, because of the symmetry of the
                # player sprites as described above, these calculations work for all possible directions.
                # If there is no difference, no rotation is required.
                # If the difference is 1, we rotate by 1 (clockwise)
                # If the difference is 2, then the target direction is at right angles to the current direction,
                # so we have a free choice as to whether to turn clockwise or anti-clockwise to align with the
                # target direction. We choose clockwise.
                # If the difference is three, the symmetry of the player sprites means that we can reach the desired
                # animation frame by rotating one unit anti-clockwise.
                rotation_table: list[int] = [0, 1, 1, -1]

                rotation: int = rotation_table[difference % 4]
                self.direction = (self.direction + rotation) % 4

            self.fire_timer -= 1

            # Fire cannon (or allow firing animation to finish)
            if self.fire_timer < 0 and (self.frame > 0 or keyboard.space):
                if self.frame == 0:
                    # Create a bullet
                    game.play_sound("laser")
                    game.bullets.append(Bullet((self.x, self.y - 8)))
                self.frame = (self.frame + 1) % 3
                self.fire_timer = Player.RELOAD_TIME

            # Check to see if any enemy segments collide with the player, as well as the flying enemy.
            # We create a list consisting of all enemy segments, and append another list containing only the
            # flying enemy.
            all_enemies: list[Segment | FlyingEnemy | None] = [
                *game.segments,
                game.flying_enemy,
            ]
            for enemy in all_enemies:
                # The flying enemy might not exist, in which case its value
                # will be None. We cannot call a method or access any attributes
                # of a 'None' object, so we must first check for that case.
                # "if object:" is shorthand for "if object != None".
                if enemy and enemy.collidepoint(self.pos):
                    # Collision has occurred, check to see whether player is invulnerable
                    if self.timer > Player.INVULNERABILITY_TIME:
                        game.play_sound("player_explode")
                        game.explosions.append(Explosion(self.pos, 1))
                        self.alive = False
                        self.timer = 0
                        self.lives -= 1
        else:
            # Not alive
            # Wait a while before respawning
            if self.timer > Player.RESPAWN_TIME:
                # Respawn
                self.alive = True
                self.timer = 0
                self.pos = (240, 768)
                game.clear_rocks_for_respawn(
                    *self.pos
                )  # Ensure there are no rocks at the player's respawn position

        # Display the player sprite if alive - BUT, if player is currently invulnerable, due to having just respawned,
        # switch between showing and not showing the player sprite on alternate frames
        invulnerable: bool = self.timer > Player.INVULNERABILITY_TIME
        self.image = (
            f"player{self.direction}{self.frame}"
            if self.alive and (invulnerable or self.timer % 2 == 0)
            else "blank"
        )


# Not a dataclass: the super().__init__ position depends on `side`, computed
# (sometimes randomly) from player_x, and the RNG call order is behaviour.
class FlyingEnemy(Actor):
    __slots__ = ("moving_x", "dx", "dy", "type", "health", "timer")

    def __init__(self, player_x: float) -> None:
        # Choose which side of the screen we start from. Don't start right next to the player as that would be
        # unfair - if not near player, start on a random side
        side: int = (
            1 if player_x < 160 else 0 if player_x > 320 else randint(0, 1)
        )

        super().__init__("blank", (550 * side - 35, 688))

        # Always moves in the same X direction, but randomly pauses to just fly straight up or down
        self.moving_x: int = 1  # 0 if we're currently moving only vertically, 1 if moving along x axis (as well as y axis)
        self.dx: int = (
            1 - 2 * side
        )  # Move left or right depending on which side of the screen we're on
        self.dy: int = choice([-1, 1])  # Start moving either up or down
        self.type: int = randint(0, 2)  # 3 different colours

        self.health: int = 1

        self.timer: int = 0

    def update(self) -> None:
        self.timer += 1

        # Move
        self.x += self.dx * self.moving_x * (3 - abs(self.dy))
        self.y += self.dy * (3 - abs(self.dx * self.moving_x))

        if self.y < 592 or self.y > 784:
            # Gone too high or low - reverse y direction
            self.moving_x = randint(0, 1)
            self.dy = -self.dy

        self.image = f"meanie{self.type}{[0, 2, 1, 2][(self.timer // 4) % 4]}"


# Not a dataclass: init branches on `totem` (RNG, health, a sound side
# effect) and computes the anchor for super().__init__.
class Rock(Actor):
    __slots__ = ("type", "health", "show_health", "timer")

    def __init__(self, x: int, y: int, totem: bool = False) -> None:
        # Use a custom anchor point for totem rocks, which are taller than other rocks
        anchor: Anchor = (24, 60) if totem else CENTRE_ANCHOR
        super().__init__("blank", cell2pos(x, y), anchor=anchor)

        self.type: int = randint(0, 3)

        if totem:
            # Totem rocks take five hits and give bonus points
            game.play_sound("totem_create")
            self.health: int = 5
            self.show_health: int = 5
        else:
            # Non-totem rocks are initially displayed as if they have one health, and animate until they
            # show the actualy sprite for their health level - resulting in a 'growing' animation.
            self.health = randint(3, 4)
            self.show_health = 1

        self.timer: int = 1

    def damage(self, amount: int, damaged_by_bullet: bool = False) -> bool:
        # Damage can occur by being hit by bullets, or by being destroyed by a segment, or by being cleared from the
        # player's respawn location. Points can be earned by hitting special "totem" rocks, which have 5 health, but
        # this should only happen when they are hit by a bullet.
        if damaged_by_bullet and self.health == 5:
            game.play_sound("totem_destroy")
            game.score += 100
        else:
            if amount > self.health - 1:
                game.play_sound("rock_destroy")
            else:
                game.play_sound("hit", 4)

        game.explosions.append(Explosion(self.pos, 2 * (self.health == 5)))
        self.health -= amount
        self.show_health = self.health

        self.anchor, self.pos = CENTRE_ANCHOR, self.pos

        # Return False if we've lost all our health, otherwise True
        return self.health < 1

    def update(self) -> None:
        self.timer += 1

        # Every other frame, update the growing animation
        if self.timer % 2 == 1 and self.show_health < self.health:
            self.show_health += 1

        if self.health == 5 and self.timer > 200:
            # Totem rocks turn into normal rocks if not shot within 200 frames
            self.damage(1)

        colour: int = max(game.wave, 0) % 3
        self.image = f"rock{colour}{self.type}{max(self.show_health - 1, 0)}"


@dataclass(eq=False, slots=True)
class Bullet(Actor):
    spawn_pos: InitVar[PointLike]
    #: True once this bullet has hit something (the list drops it)
    done: bool = False

    def __post_init__(self, spawn_pos: PointLike) -> None:
        super().__init__("bullet", spawn_pos)

    def update(self) -> None:
        # Move up the screen, 24 pixels per frame
        self.y -= 24

        # game.damage checks to see if there is a rock at the given position - if so, it damages
        # the rock and returns True
        # An asterisk before a list or tuple will unpack the contents into separate values
        grid_cell: tuple[int, int] = pos2cell(*self.pos)
        if game.damage(*grid_cell, 1, True):
            # Hit a rock - destroy self
            self.done = True
        else:
            # Didn't hit a rock
            # Check each myriapod segment, and the flying enemy, to see if this bullet collides with them
            targets: list[Segment | FlyingEnemy | None] = [
                *game.segments,
                game.flying_enemy,
            ]
            for obj in targets:
                # Is this a valid object reference, and if so, does this bullet's location overlap with the
                # object's rectangle?
                if obj and obj.collidepoint(self.pos):
                    # Create explosion
                    game.explosions.append(Explosion(obj.pos, 2))

                    obj.health -= 1

                    # Is the object an instance of the Segment class?
                    if isinstance(obj, Segment):
                        # Should we create a new rock in the segment's place? Health must be zero, there must be no
                        # rock there already, and the player sprite must not overlap with the location
                        # (bullets exist only while there is a player)
                        assert game.player is not None
                        if (
                            obj.health == 0
                            and not game.grid[obj.cell_y][obj.cell_x]
                            and game.allow_movement(
                                game.player.x,
                                game.player.y,
                                obj.cell_x,
                                obj.cell_y,
                            )
                        ):
                            # Create new rock - 20% chance of being a totem
                            game.grid[obj.cell_y][obj.cell_x] = Rock(
                                obj.cell_x, obj.cell_y, random() < 0.2
                            )

                        game.play_sound("segment_explode")
                        game.score += 10
                    else:
                        # If it's not a segment, it must be the flying enemy
                        game.play_sound("meanie_explode")
                        game.score += 20

                    self.done = True  # Destroy self

                    # Don't continue the for loop, this bullet has hit something so shouldn't hit anything else
                    return


# SEGMENT MOVEMENT
# The code below creates several constants used in the Segment class in relation to movement and directions

# Each myriapod segment moves in relation to its current grid cell.
# A segment enters a cell from a particular edge (stored in 'in_edge' in the Segment class)
# After five frames it decides which edge it's going leave that cell through (stored in out_edge).
# For example, it might carry straight on and leave through the opposite edge from the one it started at.
# Or it might turn 90 degrees and leave through an edge to its left or right.
# In this case it initially turn 45 degrees and continues along that path for 8 frames. It then turns another
# 45 degrees, at which point they are heading directly towards the next grid cell.
# A segment spends a total of 16 frames in each cell. Within the update method, the variable 'phase' refers to
# where it is in that cycle - 0 meaning it's just entered a grid cell, and 15 meaning it's about to leave it.

# Let's imagine the case where a segment enters from the left edge of a cell and then turns to leave from the
# bottom edge. The segment will initially move along the horizontal (X) axis, and will end up moving along the
# vertical (Y) axis. In this case we'll call the X axis the primary axis, and the Y axis the secondary axis.
# The lists SECONDARY_AXIS_SPEED and SECONDARY_AXIS_POSITIONS are used to determine the movement of the segment.
# This is explained in more detail in the Segment.update method.


# In Python, multiplying a list by a number creates a list where the contents
# are repeated the specified number of times. So the code below is equivalent to:
# SECONDARY_AXIS_SPEED = [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1 , 1, 2, 2, 2, 2]
# This list represents how much the segment moves along the secondary axis, in situations where it makes two 45° turns
# as described above. For the first four frames it doesn't move at all along the secondary axis. For the next eight
# frames it moves at one pixel per frame, then for the last four frames it moves at two pixels per frame.
SECONDARY_AXIS_SPEED = [0] * 4 + [1] * 8 + [2] * 4


# The code below creates a list of 16 elements, where each element is the sum of all the equivalent elements in the
# SECONDARY_AXIS_SPEED list up to that point.
# It is equivalent to writing:
# SECONDARY_AXIS_POSITIONS = [0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14]
# This list stores the total secondary axis movement that will have occurred at each phase in the segment's movement
# through the current grid cell (if the segment is turning)
SECONDARY_AXIS_POSITIONS = [sum(SECONDARY_AXIS_SPEED[:i]) for i in range(16)]


class Direction(IntEnum):
    # IntEnum, not Enum: directions index the DX/DY lists and participate
    # in min(Direction, key=...) selection below.
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3


# X and Y directions indexed into by in_edge and out_edge in Segment
# The indices correspond to the direction numbers above, i.e. 0 = up, 1 = right, 2 = down, 3 = left
DX: list[int] = [0, 1, 0, -1]
DY: list[int] = [-1, 0, 1, 0]


def inverse_direction(dir: Direction) -> Direction:
    match dir:
        case Direction.UP:
            return Direction.DOWN
        case Direction.RIGHT:
            return Direction.LEFT
        case Direction.DOWN:
            return Direction.UP
        case Direction.LEFT:
            return Direction.RIGHT
        case _:
            raise ValueError(f"not a direction: {dir!r}")


def is_horizontal(dir: Direction) -> bool:
    return dir in (Direction.LEFT, Direction.RIGHT)


@dataclass(eq=False, slots=True)
class Segment(Actor):
    #: Grid cell positions
    cell_x: int
    cell_y: int
    health: int
    #: Determines whether the 'fast' version of the sprite is used. Note that the actual speed of the myriapod is
    #: determined by how much time is included in the State.update method
    fast: bool
    #: Should this segment use the head sprite?
    head: bool
    #: Each myriapod segment moves in a defined pattern within its current cell, before moving to the next one.
    #: It will start at one of the edges - represented by a number, where 0=down,1=right,2=up,3=left
    #: self.in_edge stores the edge through which it entered the cell.
    #: Several frames after entering a cell, it chooses which edge to leave through - stored in out_edge
    #: The path it follows is explained in the update and rank methods
    in_edge: Direction = Direction.LEFT
    out_edge: Direction = Direction.RIGHT
    #: Prevents segment from moving in a particular direction
    disallow_direction: Direction = Direction.UP
    #: Used to create winding/snaking motion
    previous_x_direction: Direction = Direction.RIGHT

    def __post_init__(self) -> None:
        super().__init__("blank")

    def rank(self) -> Callable[[Direction], tuple[bool, ...]]:
        # The rank method creates and returns a function. Don't worry if this seems a strange concept - it is
        # fairly advanced stuff. The returned function is passed to Python's 'min' function in the update method,
        # as the 'key' optional parameter. min then calls this function with the numbers 0 to 3, representing the four
        # directions

        def inner(proposed_out_edge: Direction) -> tuple[bool, ...]:
            # proposed_out_edge is one of the four Directions - see Direction and DX/DY above
            # This function returns a tuple consisting of a series of factors determining which grid cell the segment should try to move into next.
            # These are not absolute rules - rather they are used to rank the four directions in order of preference,
            # i.e. which direction is the best (or at least, least bad) to move in. The factors are boolean (True or False)
            # values. A value of False is preferable to a value of True.
            # The order of the factors in the returned tuple determines their importance in deciding which way to go,
            # with the most important factor coming first.
            new_cell_x: int = self.cell_x + DX[proposed_out_edge]
            new_cell_y: int = self.cell_y + DY[proposed_out_edge]

            # Does this direction take us to a cell which is outside the grid?
            # Note: when the segments start, they are all outside the grid so this would be True, except for the case of
            # walking onto the top-left cell of the grid. But the end result of this and the following factors is that
            # it will still be allowed to continue walking forwards onto the screen.
            out: bool = (
                new_cell_x < 0
                or new_cell_x > num_grid_cols - 1
                or new_cell_y < 0
                or new_cell_y > num_grid_rows - 1
            )

            # We don't want it to to turn back on itself..
            turning_back_on_self: bool = proposed_out_edge == self.in_edge

            # ..or go in a direction that's disallowed (see comments in update method)
            direction_disallowed: bool = (
                proposed_out_edge == self.disallow_direction
            )

            # Check to see if there's a rock at the proposed new grid cell.
            # rock will either be the Rock object at the new grid cell, or None.
            # It will be set to None if there is no Rock object is at the new location, or if the new location is
            # outside the grid. We also have to account for the special case where the segment is off the left-hand
            # side of the screen on the first row, where it is initially created. We mustn't try to access that grid
            # cell (unlike most languages, in Python trying to access a list index with negative value won't necessarily
            # result in a crash, but it's still not a good idea)
            rock: Rock | None = (
                None
                if out or (new_cell_y == 0 and new_cell_x < 0)
                else game.grid[new_cell_y][new_cell_x]
            )
            rock_present: bool = rock is not None

            # Is new cell already occupied by another segment, or is another segment trying to enter my cell from
            # the opposite direction?
            occupied_by_segment: bool = (
                new_cell_x,
                new_cell_y,
            ) in game.occupied or (
                self.cell_x,
                self.cell_y,
                proposed_out_edge,
            ) in game.occupied

            # Prefer to move horizontally, unless there's a rock in the way.
            # If there are rocks both horizontally and vertically, prefer to move vertically
            horizontal_blocked: bool = (
                is_horizontal(proposed_out_edge)
                if rock_present
                else not is_horizontal(proposed_out_edge)
            )

            # Prefer not to go in the previous horizontal direction after we move up/down
            same_as_previous_x_direction: bool = (
                proposed_out_edge == self.previous_x_direction
            )

            # Finally we create and return a tuple of factors determining which cell segment should try to move into next.
            # Most important first - e.g. we shouldn't enter a new cell if if's outside the grid
            return (
                out,
                turning_back_on_self,
                direction_disallowed,
                occupied_by_segment,
                rock_present,
                horizontal_blocked,
                same_as_previous_x_direction,
            )

        return inner

    def update(self) -> None:
        # Segments take either 16 or 8 frames to pass through each grid cell, depending on the amount by which
        # game.time is updated each frame. phase will be a number between 0 and 15 indicating where we're at
        # in that cycle.
        phase: int = game.time % 16

        if phase == 0:
            # At this point, the segment is entering a new grid cell. We first update our current grid cell coordinates.
            self.cell_x += DX[self.out_edge]
            self.cell_y += DY[self.out_edge]

            # We then need to update in_edge. If, for example, we left the previous cell via its right edge, that means
            # we're entering the new cell via its left edge.
            self.in_edge = inverse_direction(self.out_edge)

            # During normal gameplay, once a segment reaches the bottom of the screen, it starts moving up again.
            # Once it reaches row 18, it starts moving down again, so that it remains a threat to the player.
            # During the title screen, we allow segments to go all the way back up to the top of the screen.
            if self.cell_y == (18 if game.player else 0):
                self.disallow_direction = Direction.UP
            if self.cell_y == num_grid_rows - 1:
                self.disallow_direction = Direction.DOWN

        elif phase == 4:
            # At this point we decide which new cell we're going to go into (and therefore, which edge of the current
            # cell we will leave via - to be stored in out_edge)
            # iterate the four Direction members, choosing the best-ranked one
            # Python's built-in 'min' function usually chooses the lowest number, so would usually return 0 as the result.
            # But if the optional 'key' argument is specified, this changes how the function determines the result.
            # The rank function (see above) returns a function (named 'inner' in rank), which min calls to decide
            # how the items should be ordered. The argument to inner represents a possible direction to move in.
            # The 'inner' function returns a tuple of boolean values - for example: (True,False,False,True,etc..)
            # When Python compares two such tuples, it considers values of False to be less than values of True,
            # and values that come earlier in the sequence are more significant than later values. So (False,True)
            # would be considered less than (True,False).
            self.out_edge = min(Direction, key=self.rank())

            if is_horizontal(self.out_edge):
                self.previous_x_direction = self.out_edge

            new_cell_x: int = self.cell_x + DX[self.out_edge]
            new_cell_y: int = self.cell_y + DY[self.out_edge]

            # Destroy any rock that might be in the new cell
            if new_cell_x >= 0 and new_cell_x < num_grid_cols:
                game.damage(new_cell_x, new_cell_y, 5)

            # Set new cell as occupied. It's a case of whichever segment is processed first, gets first dibs on a cell
            # The second line deals with the case where two segments are moving towards each other and are in
            # neighbouring cells. It allows a segment to tell if another segment trying to enter its cell from
            # the opposite direction
            game.occupied.add((new_cell_x, new_cell_y))
            game.occupied.add(
                (new_cell_x, new_cell_y, inverse_direction(self.out_edge))
            )

        # turn_idx tells us whether the segment is going to be making a 90 degree turn in the current cell, or moving
        # in a straight line. 1 = anti-clockwise turn, 2 = straight ahead, 3 = clockwise turn, 0 = leaving through same
        # edge from which we entered (unlikely to ever happen in practice)
        turn_idx: int = (self.out_edge - self.in_edge) % 4

        # Calculate segment offset in the cell, measured from the cell's centre
        # We start off assuming that the segment is starting from the top of the cell - i.e. self.in_edge being Direction.UP,
        # corresponding to zero. The primary and secondary axes, as described under "SEGMENT MOVEMENT" above, are Y and X.
        # We then apply a calculation to rotate these X and Y offsets, based on the actual direction the segment is coming from.
        # Let's take as an example the case where the segment is moving in a straight line from top to bottom.
        # We calculate offset_x by multiplying SECONDARY_AXIS_POSITIONS[phase] by 2-turn_idx. In this case, turn_idx
        # will be 2.  So 2 - turn_idx will be zero. Multiplying anything by zero gives zero, so we end up with no
        # movement on the X axis - which is what we want in this case.
        # The starting point for the offset_y calculation is that the segment starts at an offset of -16 and must cover
        # 32 pixels over the 16 phases - therefore we must multiply phase by 2. We then subtract the result of the
        # previous line, in which stolen_y_movement was calculated by multiplying SECONDARY_AXIS_POSITIONS[phase] by
        # turn_idx % 2.  mod 2 gives either zero (if turn_idx is 0 or 2), or 1 if it's 1 or 3. In the case we're looking
        # at, turn_idx is 2, so stolen_y_movement is zero.
        # The end result of all this is that in the case where the segment is moving in a straight line through a cell,
        # it just moves at 2 pixels per frame along the primary axis. If it's turning, it starts out moving at 2px
        # per frame on the primary axis, but then starts moving along the secondary axis based on the values in
        # SECONDARY_AXIS_POSITIONS. In this case we don't want it to continue moving along the primary axis - it should
        # initially slow to moving at 1px per phase, and then stop moving completely. Effectively, the secondary axis
        # is stealing movement from the primary axis - hence the name 'stolen_y_movement'
        offset_x: int = SECONDARY_AXIS_POSITIONS[phase] * (2 - turn_idx)
        stolen_y_movement: int = (turn_idx % 2) * SECONDARY_AXIS_POSITIONS[
            phase
        ]
        offset_y: int = -16 + (phase * 2) - stolen_y_movement

        # Recall the code above assumes the segment starts from the top edge
        # moving down; the actual entry edge (in_edge) rotates that by
        # 0/90/180/270 degrees. in_edge indexes the rotate_90_degrees table
        # (I^0..I^3) built above -- a named quarter turn, which in 2-D GA is
        # multiply by the pseudoscalar e_12 (exact; see the function). This
        # replaces the hand-written 2x2 rotation matrices with the geometric
        # algebra the whole course is built on.
        rotated: Vector = _rotations[self.in_edge](Vector(offset_x, offset_y))
        offset_x, offset_y = int(rotated.x), int(rotated.y)

        # Finally, we can calculate the segment's position on the screen. See cell2pos function above.
        self.pos = cell2pos(self.cell_x, self.cell_y, offset_x, offset_y)

        # We now need to decide which image the segment should use as its sprite.
        # Images for segment sprites follow the format 'segABCDE' where A is 0 or 1 depending on whether this is a
        # fast-moving segment, B is 0 or 1 depending on whether we currently have 1 or 2 health, C is whether this
        # is the head segment of a myriapod, D represents the direction we're facing (0 = up, 1 = top right,
        # up to 7 = top left) and E is how far we are through the walking animation (0 to 3)

        # Three variables go into the calculation of the direction. turn_idx tells us if we're making a turn in this
        # cell - and if so, whether we're turning clockwise or anti-clockwise. self.in_edge tells us which side of the
        # grid cell we entered from. And we can use SECONDARY_AXIS_SPEED[phase] to find out whether we should be facing
        # along the primary axis, secondary axis or diagonally between them.
        # (turn_idx - 2) gives 0 if straight, -1 if turning anti-clockwise, 1 if turning clockwise
        # Multiplying this by SECONDARY_AXIS_SPEED[phase] gives 0 if we're not doing a turn in this cell, or if
        # we are going to be turning but have not yet begun to turn. If we are doing a turn in this cell, and we're
        # at a phase where we should be showing a sprite with a new rotation, the result will be -1 or 1 if we're
        # currently in the first (45°) part of a turn, or -2 or 2 if we have turned 90°.
        # The next part of the calculation multiplies in_edge by 2 and then adds the result to the result of the previous
        # part. in_edge will be a number from 0 to 3, representing all possible directions in 90° increments.
        # It must be multiplied by two because the direction value we're calculating will be a number between 0 and 7,
        # representing all possible directions in 45° increments.
        # In the sprite filenames, the penultimate number represents the direction the sprite is facing, where a value
        # of zero means it's facing up. But in this code, if, for example, in_edge were zero, this means the segment is
        # coming from the top edge of its cell, and therefore should be facing down. So we add 4 to account for this.
        # After all this, we may have ended up with a number outside the desired range of 0 to 7. So the final step
        # is to MOD by 8.
        direction: int = (
            (SECONDARY_AXIS_SPEED[phase] * (turn_idx - 2))
            + (self.in_edge * 2)
            + 4
        ) % 8

        leg_frame: int = phase // 4  # 16 phase cycle, 4 frames of animation

        # Converting a boolean value to an integer gives 0 for False and 1 for True.
        self.image = (
            f"seg{int(self.fast)}{int(self.health == 2)}{int(self.head)}"
            f"{direction}{leg_frame}"
        )


@dataclass(eq=False, slots=True)
class Game:
    #: The player, or None on the menu (attract mode: a myriapod, no player)
    player: Player | None = None
    wave: int = field(default=-1, init=False)
    #: Segment clock; advances by 1, or 2 on every fourth wave (faster myriapod)
    time: int = field(default=0, init=False)
    #: 14 columns x 25 rows, each a Rock or None; rocks are added later
    grid: list[list[Rock | None]] = field(init=False)
    bullets: list[Bullet] = field(default_factory=list, init=False)
    explosions: list[Explosion] = field(default_factory=list, init=False)
    segments: list[Segment] = field(default_factory=list, init=False)
    flying_enemy: FlyingEnemy | None = field(default=None, init=False)
    score: int = field(default=0, init=False)
    #: Cells (x, y) claimed by a segment this frame, plus (x, y, edge) entries
    #: for the edge a segment is about to enter a cell through; reset each frame
    occupied: set[tuple[int, ...]] = field(default_factory=set, init=False)

    def __post_init__(self) -> None:
        self.grid = [[None] * num_grid_cols for _ in range(num_grid_rows)]

    def damage(
        self, cell_x: int, cell_y: int, amount: int, from_bullet: bool = False
    ) -> bool:
        # Find the rock at this grid cell (or None if no rock here)
        rock: Rock | None = self.grid[cell_y][cell_x]

        if rock is not None:
            # rock.damage returns False if the rock has lost all its health - in this case, the grid cell will be set
            # to None, overwriting the rock object reference
            if rock.damage(amount, from_bullet):
                self.grid[cell_y][cell_x] = None

        # Return whether or not there was a rock at this position
        return rock is not None

    def allow_movement(
        self, x: float, y: float, ax: int = -1, ay: int = -1
    ) -> bool:
        # ax/ay are only supplied when a segment is being destroyed, and we check to see if we should create a new
        # rock in the segment's place. They indicate a grid cell location where we're planning to create the new rock,
        # we need to ensure the new rock would not overlap with the player sprite

        # Don't go off edge of screen or above the player zone
        if x < 40 or x > 440 or y < 592 or y > 784:
            return False

        # Get coordinates of corners of player sprite's collision rectangle
        x0, y0 = pos2cell(x - 18, y - 10)
        x1, y1 = pos2cell(x + 18, y + 10)

        # Check each corner against grid
        for yi in range(y0, y1 + 1):
            for xi in range(x0, x1 + 1):
                if self.grid[yi][xi] or xi == ax and yi == ay:
                    return False

        return True

    def clear_rocks_for_respawn(self, x: float, y: float) -> None:
        # Destroy any rocks that might be overlapping with the player when they respawn
        # Could be more than one rock, hence the loop
        x0, y0 = pos2cell(x - 18, y - 10)
        x1, y1 = pos2cell(x + 18, y + 10)

        for yi in range(y0, y1 + 1):
            for xi in range(x0, x1 + 1):
                self.damage(xi, yi, 5)

    def update(self) -> None:
        # Increment time - used by segments. Time moves twice as fast every fourth wave.
        self.time += 2 if self.wave % 4 == 3 else 1

        # At the start of each frame, we reset occupied to be an empty set. As each individual myriapod segment is
        # updated, it will create entries in the occupied set to indicate that other segments should not attempt to
        # enter its current grid cell. There are two types of entries that are created in the occupied set. One is a
        # tuple consisting of a pair of numbers, representing grid cell coordinates. The other is a tuple consisting of
        # three numbers - the first two being grid cell coordinates, the third representing an edge through which a
        # segment is trying to enter a cell.
        # It is only used for myriapod segments - not rocks. Those are stored in self.grid.
        self.occupied = set()

        # Call update method on all objects: bullets, segments, explosions, then the player and the flying enemy
        # (each only when it exists), then every rock in the grid (row by row)
        player: list[GameObject] = [self.player] if self.player else []
        flying: list[GameObject] = (
            [self.flying_enemy] if self.flying_enemy else []
        )
        objects: list[GameObject] = [
            *self.bullets,
            *self.segments,
            *self.explosions,
            *player,
            *flying,
            *(rock for row in self.grid for rock in row if rock),
        ]
        for obj in objects:
            obj.update()

        # Recreate the bullets list, which will contain all existing bullets except those which have gone off the screen or have hit something
        self.bullets = [b for b in self.bullets if b.y > 0 and not b.done]

        # Recreate the explosions list, which will contain all existing explosions except those which have completed their animations
        self.explosions = [e for e in self.explosions if e.timer != 31]

        # Recreate the segments list, which will contain all existing segments except those whose health is zero
        self.segments = [s for s in self.segments if s.health > 0]

        if self.flying_enemy:
            # Destroy flying enemy if it goes off the left or right sides of the screen, or health is zero
            if (
                self.flying_enemy.health <= 0
                or self.flying_enemy.x < -35
                or self.flying_enemy.x > 515
            ):
                self.flying_enemy = None
        elif (
            random() < 0.01
        ):  # If there is no flying enemy, small chance of creating one each frame
            self.flying_enemy = FlyingEnemy(
                self.player.x if self.player else 240
            )

        if not self.segments:
            # No myriapod segments - start a new wave
            # First, ensure there are enough rocks. Count the number of rocks in the grid and if there aren't enough,
            # create one per frame. Initially there should be 30 rocks - each wave, this goes up by one.
            num_rocks: int = sum(
                rock is not None for row in self.grid for rock in row
            )
            if num_rocks < 31 + self.wave:
                while True:
                    x, y = (
                        randint(0, num_grid_cols - 1),
                        randint(1, num_grid_rows - 3),
                    )  # Leave last 2 rows rock-free
                    if self.grid[y][x] is None:
                        self.grid[y][x] = Rock(x, y)
                        break
            else:
                # New wave and enough rocks - create a new myriapod
                game.play_sound("wave")
                self.wave += 1
                self.time = 0
                self.segments = []
                num_segments: int = (
                    8 + self.wave // 4 * 2
                )  # On the first four waves there are 8 segments - then 10, and so on
                for i in range(num_segments):
                    if DEBUG_TEST_RANDOM_POSITIONS:
                        cell_x, cell_y = randint(1, 7), randint(1, 7)
                    else:
                        cell_x, cell_y = -1 - i, 0
                    # Determines whether segments take one or two hits to kill, based on the wave number.
                    # e.g. on wave 0 all segments take one hit; on wave 1 they alternate between one and two hits
                    health: int = [[1, 1], [1, 2], [2, 2], [1, 1]][
                        self.wave % 4
                    ][i % 2]
                    fast: bool = (
                        self.wave % 4 == 3
                    )  # Every fourth myriapod moves faster than usual
                    head: bool = (
                        i == 0
                    )  # The first segment of each myriapod is the head
                    self.segments.append(
                        Segment(cell_x, cell_y, health, fast, head)
                    )

    def draw(self) -> None:
        blit(f"bg{max(self.wave, 0) % 3}", 0, 0)

        # Create a list of all objects which need to be drawn: bullets, segments, explosions, the player (when
        # there is one) and every rock in the grid
        player: list[Actor] = [self.player] if self.player else []
        all_objs: list[Actor] = [
            *self.bullets,
            *self.segments,
            *self.explosions,
            *player,
            *(rock for row in self.grid for rock in row if rock),
        ]

        # We want to draw objects in order based on their Y position. Objects further down the screen should be drawn
        # after (and therefore in front of) objects higher up the screen. We can use Python's built-in sort function
        # to put the items in the desired order, before we draw them. The following function specifies the criteria
        # used to decide how the objects are sorted.
        def sort_key(obj: Actor) -> tuple[bool, float]:
            # Returns a tuple consisting of two elements. The first is whether the object is an instance of the
            # Explosion class (True or False). A value of true means it will be displayed in front of other objects.
            # The second element is the object's y position
            return (isinstance(obj, Explosion), obj.y)

        # Sort list using the above function to determine order
        all_objs.sort(key=sort_key)

        # Draw the objects, then the flying enemy on top of everything else
        for obj in all_objs:
            obj.draw()
        if self.flying_enemy:
            self.flying_enemy.draw()

    def play_sound(self, name: str, count: int = 1) -> None:
        # Some sounds have multiple varieties. If count > 1, we'll randomly choose one from those
        # We don't play any sounds if there is no player (e.g. if we're on the menu)
        if self.player:
            try:
                # Sounds with several varieties are named "name0", "name1", ...
                sounds.load(f"{name}{randint(0, count - 1)}").play()
            except Exception as e:
                # If no such sound file exists, print the name
                print(e)


# Is the space bar currently being pressed down?
space_down: bool = False


# Has the space bar just been pressed? i.e. gone from not being pressed, to being pressed
def space_pressed() -> bool:
    global space_down
    pressed: bool = keyboard.space and not space_down
    space_down = keyboard.space
    return pressed


class State(Enum):
    MENU = 1
    PLAY = 2
    GAME_OVER = 3


def update() -> None:
    global state, game

    match state:
        case State.MENU:
            if space_pressed():
                state = State.PLAY
                game = Game(
                    Player((240, 768))
                )  # Create new Game object, with a Player object

            game.update()

        case State.PLAY:
            assert game.player is not None
            if game.player.lives == 0 and game.player.timer == 100:
                sounds.load("gameover").play()
                state = State.GAME_OVER
            else:
                game.update()

        case State.GAME_OVER:
            if space_pressed():
                # Switch to menu state, and create a new game object without a player
                state = State.MENU
                game = Game()

        case _:
            raise ValueError(f"unhandled game state {state!r}")


def draw() -> None:
    # Draw the game, which covers both the game during gameplay but also the game displaying in the background
    # during the main menu and game over screens
    game.draw()

    match state:
        case State.MENU:
            # Display logo
            blit("title", 0, 0)

            # 14 frames of animation for "Press space to start", updating every 4 frames
            blit(f"space{(game.time // 4) % 14}", 0, 420)

        case State.PLAY:
            assert game.player is not None
            # Display number of lives
            for i in range(game.player.lives):
                blit("life", i * 40 + 8, 4)

            # Display score
            score: str = str(game.score)
            for i in range(1, len(score) + 1):
                # In Python, a negative index into a list (or in this case, into a string) gives you items in reverse order,
                # e.g. 'hello'[-1] gives 'o', 'hello'[-2] gives 'l', etc.
                blit(f"digit{score[-i]}", 468 - i * 24, 5)

        case State.GAME_OVER:
            # Display "Game Over" image
            blit("over", 0, 0)

        case _:
            raise ValueError(f"unhandled game state {state!r}")


# Start the music (with no sound device the game simply plays silently)
music.play("theme")
music.set_volume(0.4)

# Set the initial game state
state: State = State.MENU

# Create a new Game object, without a Player object
game: Game = Game()


# ===== main loop =====
# Like the course's demos, the game runs its own loop and calls *down* into
# update()/draw() and the renderer -- library style, nothing calls back up
# into the game.


# Ctrl-C / SIGTERM (e.g. `podman stop`) ask the window to close between
# frames; handlers are restored in the finally. Main-thread only.
def _request_quit(_signum: int, _frame: Any) -> None:
    glfw.set_window_should_close(window, True)


_prev_handlers: list[tuple[int, Any]] = []
for _sig in (signal.SIGINT, signal.SIGTERM):
    try:
        _prev_handlers.append((_sig, signal.signal(_sig, _request_quit)))
    except (ValueError, OSError):
        pass

# Fixed 60 Hz timestep -- myriapod's update() takes no dt. PGZERO_MAX_FRAMES=N
# (set by the headless frame-capture harness) stops after N frames.
_max_frames = int(os.environ.get("PGZERO_MAX_FRAMES", "0") or 0)
_dt = 1.0 / 60.0
_next_t = time.perf_counter()
_frame_count = 0
try:
    while not glfw.window_should_close(window):
        glfw.poll_events()
        update()
        fb_w, fb_h = glfw.get_framebuffer_size(window)
        renderer.begin_frame(fb_width=fb_w, fb_height=fb_h)
        draw()
        glfw.swap_buffers(window)
        _frame_count += 1
        if _max_frames and _frame_count >= _max_frames:
            break
        _next_t += _dt
        _sleep = _next_t - time.perf_counter()
        if _sleep > 0:
            time.sleep(_sleep)
        else:
            _next_t = time.perf_counter()
finally:
    for _sig, _prev in _prev_handlers:
        try:
            signal.signal(_sig, _prev)
        except (ValueError, OSError):
            pass
    # Stop the audio device's native callback thread before exit, else a
    # music-playing game hangs the process after the window closes.
    shutdown_audio()
    glfw.terminate()
