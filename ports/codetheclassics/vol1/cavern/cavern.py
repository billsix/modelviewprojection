# Code the Classics port: cavern, with its rendering engine inlined.
#
# Game code derived from Raspberry Pi Press's "Code the Classics" (vol 1):
#   Copyright (c) 2019 Eben Upton <eben@raspberrypi.org>
# Inlined engine (audio, images, renderer, keyboard, loop):
#   Copyright (c) 2026 William Emerison Six
# SPDX-License-Identifier: BSD-2-Clause
# Full license text: ports/codetheclassics/LICENSE.
"""cavern -- Bubble Bobble style platformer, from Code the Classics vol. 1,
on GLFW + OpenGL 3.3 core.

One self-contained file, read top to bottom like the course's demos: first
the small engine this game needs (a software audio mixer, an image loader, a
textured-quad renderer, the anchored Actor sprite, keyboard state), then the
game, then the loop the game itself owns.
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
from random import choice, randint, random, shuffle
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, cast, override

import gacalc.g3 as g3
import glfw
import numpy as np
import OpenGL.GL as GL
import sympy
from gacalc.g2 import Vector
from gacalc.transforms import (
    InvertibleFunction,
    compose,
    scale_non_uniform,
    to_matrix,
    translate,
)
from numpy.typing import NDArray
from PIL import Image as PILImage

# ===== engine: shared state =====

WIDTH: int = 800
HEIGHT: int = 480
TITLE: str = "Cavern"

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
    compose(
        [
            translate(b=_TX * g3.Vector.e_1 + _TY * g3.Vector.e_2),
            scale_non_uniform(_W, _H, 1),
        ]
    ),
    (_TX, _TY, _W, _H),
)


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
# each frame -- they are the only keys cavern reads.

_NAME_TO_KEY: dict[str, int] = {
    "left": glfw.KEY_LEFT,
    "right": glfw.KEY_RIGHT,
    "up": glfw.KEY_UP,
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

# Set up constants
NUM_ROWS: int = 18
NUM_COLUMNS: int = 28

LEVEL_X_OFFSET: int = 50
GRID_BLOCK_SIZE: int = 25

ANCHOR_CENTRE: Anchor = ("center", "center")
ANCHOR_CENTRE_BOTTOM: Anchor = ("center", "bottom")

LEVELS = [
    [
        "XXXXX     XXXXXXXX     XXXXX",
        "",
        "",
        "",
        "",
        "   XXXXXXX        XXXXXXX   ",
        "",
        "",
        "",
        "   XXXXXXXXXXXXXXXXXXXXXX   ",
        "",
        "",
        "",
        "XXXXXXXXX          XXXXXXXXX",
        "",
        "",
        "",
    ],
    [
        "XXXX    XXXXXXXXXXXX    XXXX",
        "",
        "",
        "",
        "",
        "    XXXXXXXXXXXXXXXXXXXX    ",
        "",
        "",
        "",
        "XXXXXX                XXXXXX",
        "      X              X      ",
        "       X            X       ",
        "        X          X        ",
        "         X        X         ",
        "",
        "",
        "",
    ],
    [
        "XXXX    XXXX    XXXX    XXXX",
        "",
        "",
        "",
        "",
        "  XXXXXXXX        XXXXXXXX  ",
        "",
        "",
        "",
        "XXXX      XXXXXXXX      XXXX",
        "",
        "",
        "",
        "    XXXXXX        XXXXXX    ",
        "",
        "",
        "",
    ],
]


def block(x: int, y: int) -> bool:
    # Is there a level grid block at these coordinates?
    grid_x: int = (x - LEVEL_X_OFFSET) // GRID_BLOCK_SIZE
    grid_y: int = y // GRID_BLOCK_SIZE
    if not 0 < grid_y < NUM_ROWS:
        return False
    row: str = game.grid[grid_y]
    return 0 <= grid_x < NUM_COLUMNS and len(row) > 0 and row[grid_x] != " "


def sign(x: float) -> int:
    # Returns -1 or 1 depending on whether number is positive or negative
    return -1 if x < 0 else 1


class GameObject(Protocol):
    """What Game.update and Game.draw need of everything in play: a per-frame
    update and a draw. Every Actor subclass below satisfies it structurally
    (deliberately not by subclassing the protocol -- an explicit subclass
    inherits the stub members, so a missing method would go unreported).
    """

    def update(self) -> None: ...

    def draw(self) -> None: ...


class CollideActor(Actor):
    """An Actor that moves a pixel at a time, stopping at blocks and edges."""

    __slots__ = ()

    def __init__(self, pos: PointLike, anchor: Anchor = ANCHOR_CENTRE) -> None:
        super().__init__("blank", pos, anchor)

    def move(self, dx: int, dy: int, speed: int) -> bool:
        new_x, new_y = int(self.x), int(self.y)

        # Movement is done 1 pixel at a time, which ensures we don't get embedded into a wall we're moving towards
        for _ in range(speed):
            new_x, new_y = new_x + dx, new_y + dy

            if new_x < 70 or new_x > 730:
                # Collided with edge of level
                return True

            # Normally you don't need brackets surrounding the condition for an if statement (unlike many other
            # languages), but in the case where the condition is split into multiple lines, using brackets removes
            # the need to use the \ symbol at the end of each line.
            # The code below checks to see if we're position we're trying to move into overlaps with a block. We only
            # need to check the direction we're actually moving in. So first, we check to see if we're moving down
            # (dy > 0). If that's the case, we then check to see if the proposed new y coordinate is a multiple of
            # GRID_BLOCK_SIZE. If it is, that means we're directly on top of a place where a block might be. If that's
            # also true, we then check to see if there is actually a block at the given position. If there's a block
            # there, we return True and don't update the object to the new position.
            # For movement to the right, it's the same except we check to ensure that the new x coordinate is a multiple
            # of GRID_BLOCK_SIZE. For moving left, we check to see if the new x coordinate is the last (right-most)
            # pixel of a grid block.
            # Note that we don't check for collisions when the player is moving up.
            if (
                dy > 0
                and new_y % GRID_BLOCK_SIZE == 0
                or dx > 0
                and new_x % GRID_BLOCK_SIZE == 0
                or dx < 0
                and new_x % GRID_BLOCK_SIZE == GRID_BLOCK_SIZE - 1
            ) and block(new_x, new_y):
                return True

            # We only update the object's position if there wasn't a block there.
            self.pos = new_x, new_y

        # Didn't collide with block or edge of level
        return False


# (eq=False on these Actor dataclasses keeps identity comparison/hashing --
# the generated __eq__ would compare fields and set __hash__ to None; slots=True
# fixes each object's attribute set to its declared fields, so every attribute
# an object ever gets is declared below)
@dataclass(eq=False, slots=True)
class Orb(CollideActor):
    MAX_TIMER: ClassVar[int] = 250

    #: named spawn_pos, NOT pos: pos is an Actor property, and a dataclass
    #: would treat the property object as this field's default value
    spawn_pos: InitVar[PointLike]
    #: Orbs are initially blown horizontally, then start floating upwards
    direction_x: int
    floating: bool = False
    #: Number representing which type of enemy is trapped in this bubble
    trapped_enemy_type: int | None = None
    timer: int = -1
    #: Number of frames during which we will be pushed horizontally
    blown_frames: int = 6

    def __post_init__(self, spawn_pos: PointLike) -> None:
        super().__init__(spawn_pos)

    def hit_test(self, bolt: "Bolt") -> bool:
        # Check for collision with a bolt
        collided: bool = self.collidepoint(bolt.pos)
        if collided:
            self.timer = Orb.MAX_TIMER - 1
        return collided

    def update(self) -> None:
        self.timer += 1

        if self.floating:
            # Float upwards
            self.move(0, -1, randint(1, 2))
        else:
            # Move horizontally
            if self.move(self.direction_x, 0, 4):
                # If we hit a block, start floating
                self.floating = True

        if self.timer == self.blown_frames:
            self.floating = True
        elif self.timer >= Orb.MAX_TIMER or self.y <= -40:
            # Pop if our lifetime has run out or if we have gone off the top of the screen
            game.pops.append(Pop(self.pos, 1))
            if self.trapped_enemy_type is not None:
                # trapped_enemy_type is either zero or one. A value of one means there's a chance of creating a
                # powerup such as an extra life or extra health
                game.fruits.append(Fruit(self.pos, self.trapped_enemy_type))
            game.play_sound("pop", 4)

        if self.timer < 9:
            # Orb grows to full size over the course of 9 frames - the animation frame updating every 3 frames
            self.image = f"orb{self.timer // 3}"
        elif self.trapped_enemy_type is not None:
            self.image = f"trap{self.trapped_enemy_type}{(self.timer // 4) % 8}"
        else:
            self.image = f"orb{3 + (((self.timer - 9) // 8) % 4)}"


@dataclass(eq=False, slots=True)
class Bolt(CollideActor):
    SPEED: ClassVar[int] = 7

    spawn_pos: InitVar[PointLike]
    direction_x: int
    active: bool = True

    def __post_init__(self, spawn_pos: PointLike) -> None:
        super().__init__(spawn_pos)

    def update(self) -> None:
        # Move horizontally and check to see if we've collided with a block
        if self.move(self.direction_x, 0, Bolt.SPEED):
            # Collided
            self.active = False
        else:
            # We didn't collide with a block - check to see if we collided with an orb or the player
            for obj in game.orbs + [game.player]:
                if obj and obj.hit_test(self):
                    self.active = False
                    break

        direction_idx: str = "1" if self.direction_x > 0 else "0"
        self.image = f"bolt{direction_idx}{(game.timer // 4) % 2}"


@dataclass(eq=False, slots=True)
class Pop(Actor):
    spawn_pos: InitVar[PointLike]
    #: 0 = a fruit vanishing, 1 = an orb bursting
    type: int
    timer: int = -1

    def __post_init__(self, spawn_pos: PointLike) -> None:
        super().__init__("blank", spawn_pos)

    def update(self) -> None:
        self.timer += 1
        self.image = f"pop{self.type}{self.timer // 2}"


class GravityActor(CollideActor):
    """A CollideActor that falls under gravity and lands on blocks."""

    MAX_FALL_SPEED: ClassVar[int] = 10

    __slots__ = ("vel_y", "landed")

    def __init__(self, pos: PointLike) -> None:
        super().__init__(pos, ANCHOR_CENTRE_BOTTOM)

        self.vel_y: int = 0
        self.landed: bool = False

    def update(self) -> None:
        self.fall(detect=True)

    def fall(self, detect: bool) -> None:
        # Apply gravity, without going over the maximum fall speed
        self.vel_y = min(self.vel_y + 1, GravityActor.MAX_FALL_SPEED)

        # The detect parameter indicates whether we should check for collisions with blocks as we fall. Normally we
        # want this to be the case. If the player is in the process of losing a life, however, we want them to just
        # fall out of the level, so False is passed in that case (Player.update).
        if detect:
            # Move vertically in the appropriate direction, at the appropriate speed
            if self.move(0, sign(self.vel_y), abs(self.vel_y)):
                # If move returned True, we must have landed on a block.
                # Note that move doesn't apply any collision detection when the player is moving up - only down
                self.vel_y = 0
                self.landed = True

            if self.top >= HEIGHT:
                # Fallen off bottom - reappear at top
                self.y = 1
        else:
            # Collision detection disabled - just update the Y coordinate without any further checks
            self.y += self.vel_y


# Class for pickups including fruit, extra health and extra life. Not a
# dataclass: its constructor CHOOSES the fruit type with random.choice, in a
# branch that depends on the trapped enemy -- the RNG call order is behaviour.
class Fruit(GravityActor):
    __slots__ = ("type", "time_to_live")

    class Type(IntEnum):
        # IntEnum: sprite names are built as "fruit" + str(type), and since
        # Python 3.11 str() of an IntEnum member is the plain number.
        APPLE = 0
        RASPBERRY = 1
        LEMON = 2
        EXTRA_HEALTH = 3
        EXTRA_LIFE = 4

    def __init__(self, pos: PointLike, trapped_enemy_type: int = 0) -> None:
        super().__init__(pos)

        # Choose which type of fruit we're going to be.
        if trapped_enemy_type == Robot.TYPE_NORMAL:
            self.type: Fruit.Type = choice(
                [Fruit.Type.APPLE, Fruit.Type.RASPBERRY, Fruit.Type.LEMON]
            )
        else:
            # If trapped_enemy_type is 1, it means this fruit came from bursting an orb containing the more dangerous type
            # of enemy. In this case there is a chance of getting an extra help or extra life power up
            # We create a list containing the possible types of fruit, in proportions based on the probability we want
            # each type of fruit to be chosen
            types: list[Fruit.Type] = 10 * [
                Fruit.Type.APPLE,
                Fruit.Type.RASPBERRY,
                Fruit.Type.LEMON,
            ]  # Each of these appear in the list 10 times
            types += 9 * [Fruit.Type.EXTRA_HEALTH]  # This appears 9 times
            types += [Fruit.Type.EXTRA_LIFE]  # This only appears once
            self.type = choice(types)  # Randomly choose one from the list

        self.time_to_live: int = 500  # Counts down to zero

    @override
    def update(self) -> None:
        super().update()

        # Does the player exist, and are they colliding with us?
        player: Player | None = game.player
        if player and player.collidepoint(self.center):
            match self.type:
                case Fruit.Type.EXTRA_HEALTH:
                    player.health = min(3, player.health + 1)
                    game.play_sound("bonus")
                case Fruit.Type.EXTRA_LIFE:
                    player.lives += 1
                    game.play_sound("bonus")
                case Fruit.Type.APPLE | Fruit.Type.RASPBERRY | Fruit.Type.LEMON:
                    player.score += (self.type + 1) * 100
                    game.play_sound("score")
                case _:
                    raise ValueError(f"unhandled fruit type {self.type!r}")

            self.time_to_live = 0  # Disappear
        else:
            self.time_to_live -= 1

        if self.time_to_live <= 0:
            # Create 'pop' animation
            game.pops.append(Pop((self.x, self.y - 27), 0))

        self.image = f"fruit{self.type}{[0, 1, 2, 1][(game.timer // 6) % 4]}"


@dataclass(eq=False, slots=True)
class Player(GravityActor):
    lives: int = 2
    score: int = 0
    # The per-life state, (re)set by reset() at every (re)spawn.
    #: -1 = left, 1 = right
    direction_x: int = field(init=False)
    fire_timer: int = field(init=False)
    #: Invulnerable while positive; above 100 means "just hurt"
    hurt_timer: int = field(init=False)
    health: int = field(init=False)
    #: The orb still being blown further by holding space, if any
    blowing_orb: Orb | None = field(init=False)

    def __post_init__(self) -> None:
        # Call constructor of parent class. Initial pos is 0,0 but reset is always called straight afterwards which
        # will set the actual starting position.
        super().__init__((0, 0))

    def reset(self) -> None:
        self.pos = (WIDTH / 2, 100)
        self.vel_y = 0
        self.direction_x = 1
        self.fire_timer = 0
        self.hurt_timer = 100
        self.health = 3
        self.blowing_orb = None

    def hit_test(self, other: "Bolt") -> bool:
        # Check for collision between player and bolt - called from Bolt.update. Also check hurt_timer - after being hurt,
        # there is a period during which the player cannot be hurt again
        if self.collidepoint(other.pos) and self.hurt_timer < 0:
            # Player loses 1 health, is knocked in the direction the bolt had been moving, and can't be hurt again
            # for a while
            self.hurt_timer = 200
            self.health -= 1
            self.vel_y = -12
            self.landed = False
            self.direction_x = other.direction_x
            if self.health > 0:
                game.play_sound("ouch", 4)
            else:
                game.play_sound("die")
            return True
        else:
            return False

    @override
    def update(self) -> None:
        # Fall - the parameter is whether we want to perform collision detection as we fall. If health
        # is zero, we want the player to just fall out of the level
        self.fall(detect=self.health > 0)

        self.fire_timer -= 1
        self.hurt_timer -= 1

        if self.landed:
            # Hurt timer starts at 200, but drops to 100 once the player has landed
            self.hurt_timer = min(self.hurt_timer, 100)

        if self.hurt_timer > 100:
            # We've just been hurt. Either carry out the sideways motion from being knocked by a bolt, or if health is
            # zero, we're dropping out of the level, so check for our sprite reaching a certain Y coordinate before
            # reducing our lives count and responding the player. We check for the Y coordinate being the screen height
            # plus 50%, rather than simply the screen height, because the former effectively gives us a short delay
            # before the player respawns.
            if self.health > 0:
                self.move(self.direction_x, 0, 4)
            else:
                if self.top >= HEIGHT * 1.5:
                    self.lives -= 1
                    self.reset()
        else:
            # We're not hurt
            # Get keyboard input. dx represents the direction the player is facing
            dx: int = -1 if keyboard.left else 1 if keyboard.right else 0

            if dx != 0:
                self.direction_x = dx

                # If we haven't just fired an orb, carry out horizontal movement
                if self.fire_timer < 10:
                    self.move(dx, 0, 4)

            # Do we need to create a new orb? Space must have been pressed and released, the minimum time between
            # orbs must have passed, and there is a limit of 5 orbs.
            if space_pressed() and self.fire_timer <= 0 and len(game.orbs) < 5:
                # x position will be 38 pixels in front of the player position, while ensuring it is within the
                # bounds of the level
                x: float = min(730, max(70, self.x + self.direction_x * 38))
                self.blowing_orb = Orb((x, self.y - 35), self.direction_x)
                game.orbs.append(self.blowing_orb)
                game.play_sound("blow", 4)
                self.fire_timer = 20

            if keyboard.up and self.vel_y == 0 and self.landed:
                # Jump
                self.vel_y = -16
                self.landed = False
                game.play_sound("jump")

        # Holding down space causes the current orb (if there is one) to be blown further
        if keyboard.space:
            if self.blowing_orb:
                # Increase blown distance up to a maximum of 120
                self.blowing_orb.blown_frames += 4
                if self.blowing_orb.blown_frames >= 120:
                    # Can't be blown any further
                    self.blowing_orb = None
        else:
            # If we let go of space, we relinquish control over the current orb - it can't be blown any further
            self.blowing_orb = None

        # Set sprite image. If we're currently hurt, the sprite will flash on and off on alternate frames.
        self.image = "blank"
        if self.hurt_timer <= 0 or self.hurt_timer % 2 == 1:
            dir_index: str = "1" if self.direction_x > 0 else "0"
            if self.hurt_timer > 100:
                self.image = (
                    f"recoil{dir_index}"
                    if self.health > 0
                    else f"fall{(game.timer // 4) % 2}"
                )
            elif self.fire_timer > 0:
                self.image = f"blow{dir_index}"
            elif dx == 0:
                self.image = "still"
            else:
                self.image = f"run{dir_index}{(game.timer // 8) % 4}"


@dataclass(eq=False, slots=True)
class Robot(GravityActor):
    TYPE_NORMAL: ClassVar[int] = 0
    TYPE_AGGRESSIVE: ClassVar[int] = 1

    spawn_pos: InitVar[PointLike]
    #: TYPE_NORMAL or TYPE_AGGRESSIVE (the latter shoots at orbs)
    type: int
    direction_x: int = 1
    alive: bool = True
    change_dir_timer: int = 0
    fire_timer: int = 100
    #: Pixels per frame, chosen at random when the robot spawns
    speed: int = field(init=False)

    def __post_init__(self, spawn_pos: PointLike) -> None:
        super().__init__(spawn_pos)
        self.speed = randint(1, 3)

    @override
    def update(self) -> None:
        super().update()

        self.change_dir_timer -= 1
        self.fire_timer += 1

        # Move in current direction - turn around if we hit a wall
        if self.move(self.direction_x, 0, self.speed):
            self.change_dir_timer = 0

        if self.change_dir_timer <= 0:
            # Randomly choose a direction to move in
            # If there's a player, there's a two thirds chance that we'll move towards them
            directions: list[int] = [-1, 1]
            if game.player:
                directions.append(sign(game.player.x - self.x))
            self.direction_x = choice(directions)
            self.change_dir_timer = randint(100, 250)

        # The more powerful type of robot can deliberately shoot at orbs - turning to face them if necessary
        if self.type == Robot.TYPE_AGGRESSIVE and self.fire_timer >= 24:
            # Go through all orbs to see if any can be shot at
            for orb in game.orbs:
                # The orb must be at our height, and within 200 pixels on the x axis
                if (
                    orb.y >= self.top
                    and orb.y < self.bottom
                    and abs(orb.x - self.x) < 200
                ):
                    self.direction_x = sign(orb.x - self.x)
                    self.fire_timer = 0
                    break

        # Check to see if we can fire at player
        if self.fire_timer >= 12:
            # Random chance of firing each frame. Likelihood increases 10 times if player is at the same height as us
            fire_probability: float = game.fire_probability()
            if (
                game.player
                and self.top < game.player.bottom
                and self.bottom > game.player.top
            ):
                fire_probability *= 10
            if random() < fire_probability:
                self.fire_timer = 0
                game.play_sound("laser", 4)

        elif self.fire_timer == 8:
            #  Once the fire timer has been set to 0, it will count up - frame 8 of the animation is when the actual bolt is fired
            game.bolts.append(
                Bolt(
                    self.pos + Vector(self.direction_x * 20, -38),
                    self.direction_x,
                )
            )

        # Am I colliding with an orb? If so, become trapped by it
        for orb in game.orbs:
            if orb.trapped_enemy_type is None and self.collidepoint(orb.center):
                self.alive = False
                orb.floating = True
                orb.trapped_enemy_type = self.type
                game.play_sound("trap", 4)
                break

        # Choose and set sprite image
        direction_idx: str = "1" if self.direction_x > 0 else "0"
        frame: int = (
            5 + (self.fire_timer // 4)
            if self.fire_timer < 12
            else 1 + ((game.timer // 4) % 4)
        )
        self.image = f"robot{self.type}{direction_idx}{frame}"


@dataclass(eq=False, slots=True)
class Game:
    #: The player, or None on the menu (attract mode: robots, no player)
    player: Player | None = None
    level_colour: int = field(default=-1, init=False)
    level: int = field(default=-1, init=False)
    # The per-level state, set up by next_level() (called from __post_init__)
    grid: list[str] = field(init=False)
    timer: int = field(init=False)
    fruits: list[Fruit] = field(init=False)
    bolts: list[Bolt] = field(init=False)
    enemies: list[Robot] = field(init=False)
    pops: list[Pop] = field(init=False)
    orbs: list[Orb] = field(init=False)
    #: Enemy types still to spawn this level (0 = normal, 1 = aggressive)
    pending_enemies: list[int] = field(init=False)

    def __post_init__(self) -> None:
        self.next_level()

    def fire_probability(self) -> float:
        # Likelihood per frame of each robot firing a bolt - they fire more often on higher levels
        return 0.001 + (0.0001 * min(100, self.level))

    def max_enemies(self) -> int:
        # Maximum number of enemies on-screen at once - increases as you progress through the levels
        return min((self.level + 6) // 2, 8)

    def next_level(self) -> None:
        self.level_colour = (self.level_colour + 1) % 4
        self.level += 1

        # Set up grid
        self.grid = LEVELS[self.level % len(LEVELS)]

        # The last row is a copy of the first row
        # Note that we don't do 'self.grid.append(self.grid[0])'. That would alter the original data in the LEVELS list
        # Instead, what this line does is create a brand new list, which is distinct from the list in LEVELS, and
        # consists of the level data plus the first row of the level. It's also interesting to note that you can't
        # do 'self.grid += [self.grid[0]]', because that's equivalent to using append.
        # As an alternative, we could have copied the list on the line below '# Set up grid', by writing
        # 'self.grid = list(LEVELS...', then used append or += on the line below.
        self.grid = self.grid + [self.grid[0]]

        self.timer = -1

        if self.player:
            self.player.reset()

        self.fruits = []
        self.bolts = []
        self.enemies = []
        self.pops = []
        self.orbs = []

        # At the start of each level we create a list of pending enemies - enemies to be created as the level plays out.
        # When this list is empty, we have no more enemies left to create, and the level will end once we have destroyed
        # all enemies currently on-screen. Each element of the list will be either 0 or 1, where 0 corresponds to
        # a standard enemy, and 1 is a more powerful enemy.
        # First we work out how many total enemies and how many of each type to create
        num_enemies: int = 10 + self.level
        num_strong_enemies: int = 1 + int(self.level / 1.5)
        num_weak_enemies: int = num_enemies - num_strong_enemies

        # Then we create the list of pending enemies, using Python's ability to create a list by multiplying a list
        # by a number, and by adding two lists together. The resulting list will consist of a series of copies of
        # the number 1 (the number depending on the value of num_strong_enemies), followed by a series of copies of
        # the number zero, based on num_weak_enemies.
        self.pending_enemies = num_strong_enemies * [
            Robot.TYPE_AGGRESSIVE
        ] + num_weak_enemies * [Robot.TYPE_NORMAL]

        # Finally we shuffle the list so that the order is randomised (using Python's random.shuffle function)
        shuffle(self.pending_enemies)

        self.play_sound("level", 1)

    def get_robot_spawn_x(self) -> float:
        # Find a spawn location for a robot, by checking the top row of the grid for empty spots
        # Start by choosing a random grid column
        r: int = randint(0, NUM_COLUMNS - 1)

        for i in range(NUM_COLUMNS):
            # Keep looking at successive columns (wrapping round if we go off the right-hand side) until
            # we find one where the top grid column is unoccupied
            grid_x: int = (r + i) % NUM_COLUMNS
            if self.grid[0][grid_x] == " ":
                return GRID_BLOCK_SIZE * grid_x + LEVEL_X_OFFSET + 12

        # If we failed to find an opening in the top grid row (shouldn't ever happen), just spawn the enemy
        # in the centre of the screen
        return WIDTH / 2

    def update(self) -> None:
        self.timer += 1

        # Update all objects (the player, when there is one, between the
        # pops and the orbs)
        player: list[GameObject] = [self.player] if self.player else []
        objects: list[GameObject] = [
            *self.fruits,
            *self.bolts,
            *self.enemies,
            *self.pops,
            *player,
            *self.orbs,
        ]
        for obj in objects:
            obj.update()

        # Use list comprehensions to remove objects which are no longer wanted from the lists. For example, we recreate
        # self.fruits such that it contains all existing fruits except those whose time_to_live counter has reached zero
        self.fruits = [f for f in self.fruits if f.time_to_live > 0]
        self.bolts = [b for b in self.bolts if b.active]
        self.enemies = [e for e in self.enemies if e.alive]
        self.pops = [p for p in self.pops if p.timer < 12]
        self.orbs = [o for o in self.orbs if o.timer < 250 and o.y > -40]

        # Every 100 frames, create a random fruit (unless there are no remaining enemies on this level)
        if (
            self.timer % 100 == 0
            and len(self.pending_enemies + self.enemies) > 0
        ):
            # Create fruit at random position
            self.fruits.append(Fruit((randint(70, 730), randint(75, 400))))

        # Every 81 frames, if there is at least 1 pending enemy, and the number of active enemies is below the current
        # level's maximum enemies, create a robot
        if (
            self.timer % 81 == 0
            and len(self.pending_enemies) > 0
            and len(self.enemies) < self.max_enemies()
        ):
            # Retrieve and remove the last element from the pending enemies list
            robot_type: int = self.pending_enemies.pop()
            pos: tuple[float, int] = (self.get_robot_spawn_x(), -30)
            self.enemies.append(Robot(pos, robot_type))

        # End level if there are no enemies remaining to be created, no existing enemies, no fruit, no popping orbs,
        # and no orbs containing trapped enemies. (We don't want to include orbs which don't contain trapped enemies,
        # as the level would never end if the player kept firing new orbs)
        if not (
            self.pending_enemies or self.fruits or self.enemies or self.pops
        ) and not any(orb.trapped_enemy_type is not None for orb in self.orbs):
            self.next_level()

    def draw(self) -> None:
        # Draw appropriate background for this level
        blit(f"bg{self.level_colour}", 0, 0)

        block_sprite: str = f"block{self.level % 4}"

        # Display blocks
        for row_y in range(NUM_ROWS):
            row: str = self.grid[row_y]
            if len(row) > 0:
                # Initial offset - large blocks at edge of level are 50 pixels wide
                x: int = LEVEL_X_OFFSET
                for block in row:
                    if block != " ":
                        blit(block_sprite, x, row_y * GRID_BLOCK_SIZE)
                    x += GRID_BLOCK_SIZE

        # Draw all objects (the player, when there is one, on top)
        player: list[GameObject] = [self.player] if self.player else []
        objects: list[GameObject] = [
            *self.fruits,
            *self.bolts,
            *self.enemies,
            *self.pops,
            *self.orbs,
            *player,
        ]
        for obj in objects:
            obj.draw()

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


# Widths of the letters A to Z in the font images
CHAR_WIDTH: list[int] = [
    27,
    26,
    25,
    26,
    25,
    25,
    26,
    25,
    12,
    26,
    26,
    25,
    33,
    25,
    26,
    25,
    27,
    26,
    26,
    25,
    26,
    26,
    38,
    25,
    25,
    25,
]


def char_width(char: str) -> int:
    # Return width of given character. For characters other than the letters A to Z (i.e. space, and the digits 0 to 9),
    # the width of the letter A is returned. ord gives the ASCII/Unicode code for the given character.
    return CHAR_WIDTH[max(0, ord(char) - 65)]


def draw_text(text: str, y: float, x: float | None = None) -> None:
    if x is None:
        # If no X pos specified, draw text in centre of the screen - must first work out total width of text
        x = (WIDTH - sum(char_width(c) for c in text)) // 2

    for char in text:
        blit(f"font0{ord(char)}", x, y)
        x += char_width(char)


IMAGE_WIDTH: dict[str, int] = {"life": 44, "plus": 40, "health": 40}


def draw_status() -> None:
    # Only called while playing, so there is a player
    player: Player | None = game.player
    assert player is not None

    # Display score, right-justified at edge of screen
    number_width: int = CHAR_WIDTH[0]
    s: str = str(player.score)
    draw_text(s, 451, WIDTH - 2 - (number_width * len(s)))

    # Display level number
    draw_text(f"LEVEL {game.level + 1}", 451)

    # Display lives and health
    # We only display a maximum of two lives - if there are more than two, a plus symbol is displayed
    lives_health: list[str] = ["life"] * min(2, player.lives)
    if player.lives > 2:
        lives_health.append("plus")
    if player.lives >= 0:
        lives_health += ["health"] * player.health

    x: int = 0
    for image in lives_health:
        blit(image, x, 450)
        x += IMAGE_WIDTH[image]


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
                # Switch to play state, and create a new Game object, passing it a new Player object to use
                state = State.PLAY
                game = Game(Player())
            else:
                game.update()

        case State.PLAY:
            assert game.player is not None
            if game.player.lives < 0:
                game.play_sound("over")
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
    game.draw()

    match state:
        case State.MENU:
            # Draw title screen
            blit("title", 0, 0)

            # Draw "Press SPACE" animation, which has 10 frames numbered 0 to 9
            # The first part gives us a number between 0 and 159, based on the game timer
            # Dividing by 4 means we go to a new animation frame every 4 frames
            # We enclose this calculation in the min function, with the other argument being 9, which results in the
            # animation staying on frame 9 for three quarters of the time. Adding 40 to the game timer is done to alter
            # which stage the animation is at when the game first starts
            anim_frame: int = min(((game.timer + 40) % 160) // 4, 9)
            blit(f"space{anim_frame}", 130, 280)

        case State.PLAY:
            draw_status()

        case State.GAME_OVER:
            draw_status()
            # Display "Game Over" image
            blit("over", 0, 0)

        case _:
            raise ValueError(f"unhandled game state {state!r}")


# Start the music (with no sound device the game simply plays silently)
music.play("theme")
music.set_volume(0.3)

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

# Fixed 60 Hz timestep -- cavern's update() takes no dt. PGZERO_MAX_FRAMES=N
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
