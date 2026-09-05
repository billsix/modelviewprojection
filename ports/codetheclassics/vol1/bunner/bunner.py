# Code the Classics port: bunner, with its rendering engine inlined.
#
# Game code derived from Raspberry Pi Press's "Code the Classics" (vol 1):
#   Copyright (c) 2019 Eben Upton <eben@raspberrypi.org>
# Inlined engine (audio, images, renderer, keyboard, loop):
#   Copyright (c) 2026 William Emerison Six
# SPDX-License-Identifier: BSD-2-Clause
# Full license text: ports/codetheclassics/LICENSE.
"""bunner -- Infinite Bunner, a Frogger style road-and-river crosser from
Code the Classics vol. 1, on GLFW + OpenGL 3.3 core.

One self-contained file, read top to bottom like the course's demos: first
the small engine this game needs (a software audio mixer with looping
ambience, an image loader, a textured-quad renderer plus a debug outline and
text, the anchored Actor sprite, keyboard state), then the game, then the
loop the game itself owns.
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
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, cast, override

import gacalc.g3 as g3
import glfw
import numpy as np
import OpenGL.GL as GL
import sympy
from gacalc.g2 import Vector
from gacalc.transforms import (
    InvertibleFunction,
    scale_non_uniform,
    to_matrix,
    translate,
)
from numpy.typing import NDArray
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont

# ===== engine: shared state =====

WIDTH: int = 480
HEIGHT: int = 800
TITLE: str = "Infinite Bunner"

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

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        color: tuple[int, int, int],
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
    #: buffer voices only: wrap around gaplessly instead of finishing
    looping: bool
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
                    if v.looping:
                        v.pos = 0  # gapless wraparound
                        continue
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
    def play_buffer(
        self, samples: _PCM, volume: float, looping: bool
    ) -> _Voice | None:
        if not self._ensure_device():
            return None
        v = _Voice(samples, None, volume, looping)
        with self._lock:
            self._voices.append(v)
        return v

    def play_stream(
        self, stream: Iterator[Any], volume: float
    ) -> _Voice | None:
        if not self._ensure_device():
            return None
        v = _Voice(None, stream, volume, False)
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
    #: Volume (0.0-1.0) for current and future plays (the looping ambience
    #: is faded by distance every frame).
    _volume: float = field(default=1.0, init=False)
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

    def play(self, loops: int = 0) -> None:
        """Play the effect, overlapping any prior plays; ``loops=-1`` loops it
        until :meth:`stop`."""
        if _ma is None:
            return
        buf = self._buffer()
        if buf is None:
            return
        live = self._live()
        if len(live) >= _MAX_VOICES_PER_SOUND:
            _engine.stop_voice(live[0])  # oldest voice yields its budget
        v = _engine.play_buffer(buf, self._volume, looping=loops != 0)
        if v is not None:
            self._voices.append(v)

    def stop(self) -> None:
        """Stop all currently-playing instances of this effect."""
        for v in self._live():
            _engine.stop_voice(v)

    def set_volume(self, v: float) -> None:
        """Set this effect's volume (0.0-1.0), applied to current + future plays."""
        self._volume = v
        for voice in self._live():
            voice.volume = v


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
# or flat colour, switched by uUseTex and multiplied by uTint. bunner draws
# textured, untinted sprites, plus flat-colour outlines for its debug overlay.

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
    buffer, the dynamic overlay buffer and the pixel-space projection. Build one with
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
    #: A dynamic buffer the debug overlays fill per draw
    prim: GLBuffer
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

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        color: tuple[int, int, int],
    ) -> None:
        """Draw the one-pixel outline of a rectangle (the debug overlay)."""
        verts: NDArray[np.float32] = np.array(
            [x, y, x + w, y, x + w, y + h, x, y + h, x, y], dtype=np.float32
        )
        GL.glBindVertexArray(self.prim.vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.prim.vbo)
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER, verts.nbytes, verts, GL.GL_DYNAMIC_DRAW
        )
        GL.glUniformMatrix4fv(self.uniforms.model, 1, GL.GL_TRUE, _identity())
        GL.glUniform1i(self.uniforms.use_tex, 0)
        r, g, b = color
        GL.glUniform4f(self.uniforms.tint, r / 255.0, g / 255.0, b / 255.0, 1.0)
        GL.glDrawArrays(GL.GL_LINE_LOOP, 0, 5)

    @classmethod
    def create(cls, width: int, height: int) -> Renderer:
        """Build the renderer for a ``width`` x ``height`` pixel game: link the
        program, query its uniforms, upload the unit quad and an empty dynamic buffer, set the blend
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
        prim = _make_buffer(None)
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
            prim,
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


# ===== engine: text =====
#
# Text is rasterized with Pillow to an RGBA bitmap, wrapped as an Image (lazy
# GL texture), cached by (text, size, colour) and drawn at a top-left pixel
# position. bunner draws text only for its debug row-boundary overlay.

_font_cache: dict[int, Any] = {}
_text_cache: dict[tuple[str, int, tuple[int, int, int]], Image] = {}


def _get_font(size: int) -> Any:
    """Return a cached PIL font: a system DejaVuSans, else Pillow's default."""
    if size not in _font_cache:
        font: Any = ImageFont.load_default()
        for path in (
            "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        ):
            if os.path.exists(path):
                font = ImageFont.truetype(path, size)
                break
        _font_cache[size] = font
    return _font_cache[size]


def _render_text(text: str, size: int, color: tuple[int, int, int]) -> Image:
    """Rasterize ``text`` to a cached Image."""
    key = (text, size, color)
    if key not in _text_cache:
        font: Any = _get_font(size)
        bbox = ImageDraw.Draw(PILImage.new("RGBA", (1, 1))).textbbox(
            (0, 0), text, font=font
        )
        w, h = int(max(1, bbox[2] - bbox[0])), int(max(1, bbox[3] - bbox[1]))
        surf: Any = PILImage.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(surf).text(
            (-bbox[0], -bbox[1]), text, font=font, fill=(*color, 255)
        )
        _text_cache[key] = Image.from_rgba(np.array(surf))
    return _text_cache[key]


def draw_text(
    text: str,
    x: float,
    y: float,
    color: tuple[int, int, int] = (255, 255, 255),
    size: int = 24,
) -> None:
    """Draw ``text`` with its top-left at ``(x, y)``."""
    renderer.draw_image(_render_text(text, size, color), (x, y))


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

    @property
    def width(self) -> float:
        return self._rect.width

    @property
    def height(self) -> float:
        return self._rect.height

    # -- drawing & geometry ---------------------------------------------------
    def draw(self) -> None:
        """Draw the sprite at its current position."""
        renderer.draw_image(self._image, self._rect.topleft)

    def collidepoint(self, p: PointLike) -> bool:
        """Return whether the point ``p`` lies within this sprite's rect."""
        return self._rect.collidepoint(p)


# ===== engine: keyboard =====
#
# ``keyboard[code]`` is True while that GLFW key is held. The GLFW key
# callback below feeds presses and releases in; the game polls the codes
# it needs each frame.


@dataclass(slots=True)
class Keyboard:
    """``keyboard[code]`` is True while that GLFW key is held."""

    #: GLFW key codes currently held down.
    _pressed: set[int] = field(default_factory=set)

    def press(self, key: int) -> None:
        """Mark GLFW key code ``key`` as held (called from the key callback)."""
        self._pressed.add(key)

    def release(self, key: int) -> None:
        """Mark GLFW key code ``key`` as released."""
        self._pressed.discard(key)

    def __getitem__(self, code: int) -> bool:
        """Return whether the GLFW key ``code`` is currently held."""
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

ROW_HEIGHT: int = 40

# See what happens when you change this to True
DEBUG_SHOW_ROW_BOUNDARIES: bool = False


class GameObject(Protocol):
    """What Game.update and Game.draw need of everything in play: a per-frame
    update, and a draw at a scroll offset. Every MyActor subclass below
    satisfies it structurally (deliberately not by subclassing the protocol --
    an explicit subclass inherits the stub members, so a missing method would
    go unreported).
    """

    def update(self) -> None: ...

    def draw_at(self, offset_x: float, offset_y: float) -> None: ...


# MyActor extends Actor by allowing an object to have a list of child objects,
# which are drawn relative to the parent object.
class MyActor(Actor):
    __slots__ = ("children",)

    def __init__(
        self,
        image: str,
        pos: tuple[float, float],
        anchor: Anchor = ("center", "bottom"),
    ) -> None:
        super().__init__(image, pos, anchor)

        self.children: list[MyActor] = []

    def draw_at(self, offset_x: float, offset_y: float) -> None:
        # Draw this object (and its children, relative to it) shifted by the
        # offset - the screen's scroll position. Not an override of Actor.draw:
        # it takes the offsets, so it has its own name.
        self.x += offset_x
        self.y += offset_y

        self.draw()
        for child_obj in self.children:
            child_obj.draw_at(self.x, self.y)

        self.x -= offset_x
        self.y -= offset_y

    def update(self) -> None:
        for child_obj in self.children:
            child_obj.update()


# The eagle catches the rabbit if it goes off the bottom of the screen
# (eq=False on these Actor dataclasses keeps identity comparison/hashing --
# the generated __eq__ would compare fields and set __hash__ to None; slots=True
# fixes each object's attribute set to its declared fields, so every attribute
# an object ever gets is declared below)
@dataclass(eq=False, slots=True)
class Eagle(MyActor):
    #: named spawn_pos, NOT pos: pos is an Actor property, and a dataclass
    #: would treat the property object as this field's default value
    spawn_pos: InitVar[tuple[float, float]]

    def __post_init__(self, spawn_pos: tuple[float, float]) -> None:
        super().__init__("eagles", spawn_pos)
        self.children.append(MyActor("eagle", (0, -32)))

    @override
    def update(self) -> None:
        self.y += 12


class PlayerState(Enum):
    ALIVE = 0
    SPLAT = 1
    SPLASH = 2
    EAGLE = 3


class Direction(IntEnum):
    # IntEnum, not Enum: directions index the DX/DY/direction_keys lists,
    # and sprite names are built as e.g. "sit" + str(direction) -- since
    # Python 3.11 str() of an IntEnum member is the plain number, so those
    # stay byte-identical.
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3


direction_keys: list[int] = [
    glfw.KEY_UP,
    glfw.KEY_RIGHT,
    glfw.KEY_DOWN,
    glfw.KEY_LEFT,
]

# X and Y directions indexed into by in_edge and out_edge in Segment
# The indices correspond to the direction numbers above, i.e. 0 = up, 1 = right, 2 = down, 3 = left
# Numbers 0 to 3 correspond to up, right, down, left
DX: list[int] = [0, 4, 0, -4]
DY: list[int] = [-4, 0, 4, 0]


@dataclass(eq=False, slots=True)
class Bunner(MyActor):
    MOVE_DISTANCE: ClassVar[int] = 10

    spawn_pos: InitVar[tuple[float, float]]
    state: PlayerState = PlayerState.ALIVE
    direction: Direction = Direction.DOWN
    timer: int = 0
    #: If a control input is pressed while the rabbit is in the middle of jumping, it's added to the input queue
    input_queue: list[Direction] = field(default_factory=list)
    #: Keeps track of the furthest distance we've reached so far in the level, for scoring
    #: (Level Y coordinates decrease as the screen scrolls)
    min_y: float = field(init=False)

    def __post_init__(self, spawn_pos: tuple[float, float]) -> None:
        super().__init__("blank", spawn_pos)
        self.min_y = self.y

    def handle_input(self, dir: Direction) -> None:
        # Find row that player is trying to move to. This may or may not be the row they're currently standing on,
        # depending on whether the proposed movement would take them onto a different row
        for row in game.rows:
            if row.y == self.y + Bunner.MOVE_DISTANCE * DY[dir]:
                # Found the target row
                # Can the player move to the new location? Can't move if there's something in the way
                # (or if the new location is off the screen)
                if row.allow_movement(self.x + Bunner.MOVE_DISTANCE * DX[dir]):
                    # It's okay to move here, so set direction and timer. Player will move one pixel per frame
                    # for the specified number of frames
                    self.direction = dir
                    self.timer = Bunner.MOVE_DISTANCE
                    game.play_sound("jump", 1)

                # No need to continue searching
                return

    @override
    def update(self) -> None:
        # Check each control direction
        for direction in Direction:
            if key_just_pressed(direction_keys[direction]):
                self.input_queue.append(direction)

        match self.state:
            case PlayerState.ALIVE:
                # While the player is alive, the timer variable is used for movement. If it's zero, the player is on
                # the ground. If it's above zero, they're currently jumping to a new location.

                # Are we on the ground, and are there inputs to process?
                if self.timer == 0 and len(self.input_queue) > 0:
                    # Take the next input off the queue and process it
                    self.handle_input(self.input_queue.pop(0))

                land: bool = False
                if self.timer > 0:
                    # Apply movement
                    self.x += DX[self.direction]
                    self.y += DY[self.direction]
                    self.timer -= 1
                    land = (
                        self.timer == 0
                    )  # If timer reaches zero, we've just landed

                current_row: Row | None = next(
                    (row for row in game.rows if row.y == self.y), None
                )

                if current_row:
                    # Row.check receives the player's X coordinate and returns the new state the player should be in
                    # (normally ALIVE, but SPLAT or SPLASH if they've collided with a vehicle or if they've fallen in
                    # the water). It also returns a second result which is only used if there was a collision, and even
                    # then only for certain collisions. When the new state is SPLAT, we will add a new child object to the
                    # current row, with the appropriate 'splat' image. In this case, the second result returned from
                    # check_collision is a Y offset which affects the position of this new child object. If the player is
                    # hit by a car the Y offset is zero, but if they are hit by a train the returned offset is 8 as this
                    # positioning looks a little better.
                    self.state, dead_obj_y_offset = current_row.check_collision(
                        self.x
                    )
                    if self.state == PlayerState.ALIVE:
                        # Water rows move the player along the X axis, if standing on a log
                        self.x += current_row.push()

                        if land:
                            # Just landed - play sound effect appropriate to the current row
                            current_row.play_sound()
                    else:
                        if self.state == PlayerState.SPLAT:
                            # Add 'splat' graphic to current row with the specified position and Y offset
                            current_row.children.insert(
                                0,
                                MyActor(
                                    "splat" + str(self.direction),
                                    (self.x, dead_obj_y_offset),
                                ),
                            )
                        self.timer = 100
                else:
                    # There's no current row - either because player is currently changing row, or the row they were on
                    # has been deleted. Has the player gone off the bottom of the screen?
                    if self.y > game.scroll_pos + HEIGHT + 80:
                        # Create eagle
                        game.eagle = Eagle((self.x, game.scroll_pos))
                        self.state = PlayerState.EAGLE
                        self.timer = 150
                        game.play_sound("eagle")

                # Limit x position so player doesn't go off the screen. The player movement code doesn't allow jumping off
                # the screen, but without this line, the player could be carried off the screen by a log
                self.x = max(16, min(WIDTH - 16, self.x))
            case _:
                # Not alive - timer now counts down prior to game over screen
                self.timer -= 1

        # Keep track of the furthest we've got in the level
        self.min_y = min(self.min_y, self.y)

        # Choose sprite image
        self.image = "blank"
        if self.state == PlayerState.ALIVE:
            self.image = (
                f"{'jump' if self.timer > 0 else 'sit'}{self.direction}"
            )
        elif self.state == PlayerState.SPLASH and self.timer > 84:
            # Display appropriate 'splash' animation frame. Note that we use a different technique to display the
            # 'splat' image - see: comments earlier in this method. The reason two different techniques are used is
            # that the splash image should be drawn on top of other objects, whereas the splat image must be drawn
            # underneath other objects. Since the player is always drawn on top of other objects, changing the player
            # sprite is a suitable method of displaying the splash image.
            self.image = f"splash{int((100 - self.timer) / 2)}"


# Mover is the base class for Car, Log and Train
# The thing they all have in common, besides inheriting from MyActor, is that they need to store whether they're
# moving left or right and update their X position each frame
class Mover(MyActor):
    __slots__ = ("dx",)

    def __init__(self, dx: int, image: str, pos: tuple[float, float]) -> None:
        super().__init__(image, pos)

        self.dx: int = dx

    @override
    def update(self) -> None:
        self.x += self.dx


class Car(Mover):
    # These correspond to the indicies of the lists self.sounds and self.played. Used in Car.update to trigger
    # playing of the corresponding sound effects.
    SOUND_ZOOM: ClassVar[int] = 0
    SOUND_HONK: ClassVar[int] = 1

    __slots__ = ("played", "sounds")

    def __init__(self, dx: int, pos: tuple[float, float]) -> None:
        super().__init__(dx, f"car{randint(0, 3)}{'0' if dx < 0 else '1'}", pos)

        # Cars have two sound effects. Each can only play once. We use this
        # list to keep track of which has already played.
        self.played: list[bool] = [False, False]
        self.sounds: list[tuple[str, int]] = [("zoom", 6), ("honk", 4)]

    def play_sound(self, num: int) -> None:
        if not self.played[num]:
            # Select a sound and pass the name and count to Game.play_sound.
            # The asterisk operator unpacks the two items and passes them to play_sound as separate arguments
            game.play_sound(*self.sounds[num])
            self.played[num] = True


class Log(Mover):
    __slots__ = ()

    def __init__(self, dx: int, pos: tuple[float, float]) -> None:
        super().__init__(dx, f"log{randint(0, 1)}", pos)


class Train(Mover):
    __slots__ = ()

    def __init__(self, dx: int, pos: tuple[float, float]) -> None:
        super().__init__(
            dx, f"train{randint(0, 2)}{'0' if dx < 0 else '1'}", pos
        )


# Row is the base class for Pavement, Grass, Dirt, Rail and ActiveRow
# Each row corresponds to one of the 40 pixel high images which make up sections of grass, road, etc.
# The last row of each section is 60 pixels high and overlaps with the row above
class Row(MyActor):
    __slots__ = ("index", "dx")

    def __init__(self, base_image: str, index: int, y: float) -> None:
        # base_image and index form the name of the image file to use
        # Last argument is the anchor point to use
        super().__init__(f"{base_image}{index}", (0, y), ("left", "bottom"))

        self.index: int = index

        # X direction of moving elements on this row
        # Zero by default - only ActiveRows (see below) and Rail have moving elements
        self.dx: int = 0

    def next(self) -> Row:
        # Every kind of row decides what comes above it. See comments in Game.update
        raise NotImplementedError

    def collide(self, x: float, margin: float = 0) -> MyActor | None:
        # Check to see if the given X coordinate is in contact with any of this row's child objects (e.g. logs, cars,
        # hedges). A negative margin makes the collideable area narrower than the child object's sprite, while a
        # positive margin makes the collideable area wider.
        return next(
            (
                child_obj
                for child_obj in self.children
                if child_obj.x - child_obj.width / 2 - margin
                <= x
                < child_obj.x + child_obj.width / 2 + margin
            ),
            None,
        )

    def push(self) -> int:
        return 0

    def play_sound(self) -> None:
        # The sound of landing on this kind of row; every kind has one
        raise NotImplementedError

    def check_collision(self, x: float) -> tuple[PlayerState, int]:
        # Returns the new state the player should be in, based on whether or not the player collided with anything on
        # this road. As this class is the base class for other types of row, this method defines the default behaviour
        # - i.e. unless a subclass overrides this method, the player can walk around on a row without dying.
        return PlayerState.ALIVE, 0

    def allow_movement(self, x: float) -> bool:
        # Ensure the player can't walk off the left or right sides of the screen
        return x >= 16 and x <= WIDTH - 16


class ActiveRow(Row):
    __slots__ = ("child_type", "timer")

    # child_type's precise shape: Car/Log constructors take (dx, pos) -- NOT
    # Mover's (dx, image, pos) -- so `type[Mover]` would mistype the calls.
    def __init__(
        self,
        child_type: Callable[[int, tuple[float, float]], Mover],
        dxs: list[int],
        base_image: str,
        index: int,
        y: float,
    ) -> None:
        super().__init__(base_image, index, y)

        # Class to be used for child objects (e.g. Car)
        self.child_type: Callable[[int, tuple[float, float]], Mover] = (
            child_type
        )
        self.timer: float = 0
        # Randomly choose a direction for cars/logs to move
        self.dx = choice(dxs)

        # Populate the row with child objects (cars or logs). Without this, the row would initially be empty.
        x: float = -WIDTH / 2 - 70
        while x < WIDTH / 2 + 70:
            x += randint(240, 480)
            pos: tuple[float, int] = (WIDTH / 2 + (x if self.dx > 0 else -x), 0)
            self.children.append(self.child_type(self.dx, pos))

    @override
    def update(self) -> None:
        super().update()

        # Recreate the children list, excluding any which are too far off the edge of the screen to be visible
        self.children = [
            c for c in self.children if c.x > -70 and c.x < WIDTH + 70
        ]

        self.timer -= 1

        # Create new child objects on a random interval
        if self.timer < 0:
            pos: tuple[int, int] = (WIDTH + 70 if self.dx < 0 else -70, 0)
            self.children.append(self.child_type(self.dx, pos))
            # 240 is minimum distance between the start of one child object and the start of the next, assuming its
            # speed is 1. If the speed is 2, they can occur twice as frequently without risk of overlapping with
            # each other. The maximum distance is double the minimum distance (1 + random value of 1)
            self.timer = (1 + random()) * (240 / abs(self.dx))


# Grass rows sometimes contain hedges
class Hedge(MyActor):
    __slots__ = ()

    def __init__(self, x: int, y: int, pos: tuple[float, float]) -> None:
        super().__init__(f"bush{x}{y}", pos)


def generate_hedge_mask() -> list[bool]:
    # In this context, a mask is a series of boolean values which allow or prevent parts of an underlying image from showing through.
    # This function creates a mask representing the presence or absence of hedges in a Grass row. False means a hedge
    # is present, True represents a gap. Initially we create a list of 12 elements. For each element there is a small
    # chance of a gap, but normally all element will be False, representing a hedge. We then randomly set one item to
    # True, to ensure that there is always at least one gap that the player can get through
    mask: list[bool] = [random() < 0.01 for _ in range(12)]
    mask[randint(0, 11)] = True  # force there to be one gap

    # We then widen gaps to a minimum of 3 tiles. This happens in two steps.
    # First, we recreate the mask list, except this time whether a gap is present is based on whether there was a gap
    # in either the original element or its neighbouring elements. When using Python's built-in sum function, a value
    # of True is treated as 1 and False as 0. We must use the min/max functions to ensure that we don't try to look
    # at a neighbouring element which doesn't exist (e.g. there is no neighbour to the right of the last element)
    mask = [sum(mask[max(0, i - 1) : min(12, i + 2)]) > 0 for i in range(12)]

    # We want to ensure gaps are a minimum of 3 tiles wide, but the previous line only ensures a minimum gap of 2 tiles
    # at the edges. The last step is to return a new list consisting of the old list with the first and last elements duplicated
    return [mask[0]] + mask + 2 * [mask[-1]]


def classify_hedge_segment(
    mask: list[bool], previous_mid_segment: int | None
) -> tuple[int | None, int | None]:
    # This function helps determine which sprite should be used by a particular hedge segment. Hedge sprites are numbered
    # 00, 01, 10, 11, 20, 21 - up to 51. The second number indicates whether it's a bottom (0) or top (1) segment,
    # but this method is concerned only with the first number. 0 represents a single-tile-width hedge. 1 and 2 represent
    # the left-most or right-most sprites in a multi-tile-width hedge. 3, 4 and 5 all represent middle pieces in hedges
    # which are 3 or more tiles wide.

    # mask is a list of 4 boolean values - a slice from the list generated by generate_hedge_mask. True represents a gap
    # and False represents a hedge. mask[1] is the item we're currently looking at.
    # mask[1] == True represents a gap, so there will be no hedge sprite at this location. Otherwise there's a
    # hedge here - need to check either side of it to see if it's a single-width, left-most, right-most or middle
    # piece. The calculation generates a number from 0 to 3 accordingly. Note that when boolean values are used in
    # arithmetic in Python, False is treated as being 0 and True as 1.
    sprite_x: int | None = None if mask[1] else 3 - 2 * mask[0] - mask[2]

    if sprite_x != 3:
        # Not a middle piece
        return sprite_x, None

    # If this is a middle piece, to ensure the piece tiles correctly, we alternate between sprites 3 and 4.
    # If the next piece is going to be the last of this hedge section (sprite 2), we need to make sure that sprite 3
    # does not precede it, as the two do not tile together correctly. In this case we should use sprite 5.
    # mask[3] tells us whether there's a gap 2 tiles to the right - which means the next tile will be sprite 2
    if previous_mid_segment == 4 and mask[3]:
        return 5, None
    # Alternate between 3 and 4
    sprite_x = 4 if previous_mid_segment == 3 else 3
    return sprite_x, sprite_x


#: How every row is built: (the row below it, its index, its y). Grass, Dirt and
#: Pavement ignore the predecessor, but keeping the shape uniform lets next()
#: build any kind of row the same way.
RowFactory = Callable[["Row | None", int, float], "Row"]


def _next_after_plain_row(row: Row, same: RowFactory) -> Row:
    # Grass and Dirt rows share one sequence: indexes 0-5 jump to 8-13, 6 goes
    # to 7, 7 to 15, 8-14 count up, and after 15 comes a Road or Water row.
    row_class: RowFactory
    if row.index <= 5:
        row_class, index = same, row.index + 8
    elif row.index == 6:
        row_class, index = same, 7
    elif row.index == 7:
        row_class, index = same, 15
    elif 8 <= row.index <= 14:
        row_class, index = same, row.index + 1
    else:
        row_class, index = choice((Road, Water)), 0

    # Create an object of the chosen row class
    return row_class(row, index, row.y - ROW_HEIGHT)


class Grass(Row):
    __slots__ = ("hedge_row_index", "hedge_mask")

    def __init__(self, predecessor: Row | None, index: int, y: float) -> None:
        super().__init__("grass", index, y)

        # In computer graphics, a mask is a series of boolean (true or false) values indicating which parts of an image
        # will be transparent. Grass rows may contain hedges which block the player's movement, and we use a similar
        # mechanism here. In our hedge mask, values of False mean a hedge is present, while True means there is a gap
        # in the hedges. Hedges are two rows high - once hedges have been created on a row, the pattern will be
        # duplicated on the next row (although the sprites will be different - e.g. there are separate sprites
        # for the top-left and bottom-left corners of a hedge). Note that the upper sprites overlap with the row above.
        # 0 or 1, or None if no hedges on this row
        self.hedge_row_index: int | None = None
        self.hedge_mask: list[bool] | None = None

        if (
            not isinstance(predecessor, Grass)
            or predecessor.hedge_row_index is None
        ):
            # Create a brand-new set of hedges? We will only create hedges if the previous row didn't have any.
            # We also only want hedges to appear on certain types of grass row, and on only a random selection
            # of rows
            if random() < 0.5 and index > 7 and index < 14:
                self.hedge_mask = generate_hedge_mask()
                self.hedge_row_index = 0
        elif predecessor.hedge_row_index == 0:
            self.hedge_mask = predecessor.hedge_mask
            self.hedge_row_index = 1

        if self.hedge_row_index is not None and self.hedge_mask is not None:
            # See comments in classify_hedge_segment for explanation of previous_mid_segment
            previous_mid_segment: int | None = None
            for i in range(1, 13):
                sprite_x, previous_mid_segment = classify_hedge_segment(
                    self.hedge_mask[i - 1 : i + 3], previous_mid_segment
                )
                if sprite_x is not None:
                    self.children.append(
                        Hedge(sprite_x, self.hedge_row_index, (i * 40 - 20, 0))
                    )

    @override
    def allow_movement(self, x: float) -> bool:
        # allow_movement in the base class ensures that the player can't walk off the left and right sides of the
        # screen. The call to our own collide method ensures that the player can't walk through hedges. The margin of
        # 8 prevents the player sprite from overlapping with the edge of a hedge.
        return super().allow_movement(x) and not self.collide(x, 8)

    def play_sound(self) -> None:
        game.play_sound("grass", 1)

    @override
    def next(self) -> Row:
        return _next_after_plain_row(self, Grass)


class Dirt(Row):
    __slots__ = ()

    def __init__(self, predecessor: Row | None, index: int, y: float) -> None:
        super().__init__("dirt", index, y)

    def play_sound(self) -> None:
        game.play_sound("dirt", 1)

    @override
    def next(self) -> Row:
        return _next_after_plain_row(self, Dirt)


class Water(ActiveRow):
    __slots__ = ()

    def __init__(self, predecessor: Row | None, index: int, y: float) -> None:
        assert predecessor is not None  # water rows always follow a row
        # dxs contains a list of possible directions (and speeds) in which child objects (in this case, logs) on this
        # row could move. We pass the lists to the constructor of the base class, which randomly chooses one of the
        # directions. We want logs on alternate rows to move in opposite directions, so we take advantage of the fact
        # that that in Python, multiplying a list by True or False results in either the same list, or an empty list.
        # So by looking at the direction of child objects on the previous row (predecessor.dx), we can decide whether
        # child objects on this row should move left or right. If this is the first of a series of Water rows,
        # predecessor.dx will be zero, so child objects could move in either direction.
        dxs: list[int] = [-2, -1] * (predecessor.dx >= 0) + [1, 2] * (
            predecessor.dx <= 0
        )
        super().__init__(Log, dxs, "water", index, y)

    @override
    def update(self) -> None:
        super().update()

        for log in self.children:
            # Child (log) object positions are relative to the parent row. If the player exists, and the player is at the
            # same Y position, and is colliding with the current log, make the log dip down into the water slightly
            if (
                game.bunner
                and self.y == game.bunner.y
                and log == self.collide(game.bunner.x, -4)
            ):
                log.y = 2
            else:
                log.y = 0

    @override
    def push(self) -> int:
        # Called when the player is standing on a log on this row, so player object can be moved at the same speed and
        # in the same direction as the log
        return self.dx

    @override
    def check_collision(self, x: float) -> tuple[PlayerState, int]:
        # If we're colliding with a log, that's a good thing!
        # margin of -4 ensures we can't stand right on the edge of a log
        if self.collide(x, -4):
            return PlayerState.ALIVE, 0
        else:
            game.play_sound("splash")
            return PlayerState.SPLASH, 0

    def play_sound(self) -> None:
        game.play_sound("log", 1)

    @override
    def next(self) -> Row:
        # After 2 water rows, there's a 50-50 chance of the next row being either another water row, or a dirt row
        row_class: RowFactory
        if self.index == 7 or (self.index >= 1 and random() < 0.5):
            row_class, index = Dirt, randint(4, 6)
        else:
            row_class, index = Water, self.index + 1

        # Create an object of the chosen row class
        return row_class(self, index, self.y - ROW_HEIGHT)


class Road(ActiveRow):
    __slots__ = ()

    def __init__(self, predecessor: Row | None, index: int, y: float) -> None:
        assert predecessor is not None  # road rows always follow a row
        # Specify the possible directions and speeds from which the movement of cars on this row will be chosen
        # We use Python's set data structure to specify that the car velocities on this row will be any of the numbers
        # from -5 to 5, except for zero or the velocity of the cars on the previous row
        dxs: list[int] = list(set(range(-5, 6)) - set([0, predecessor.dx]))
        super().__init__(Car, dxs, "road", index, y)

    @override
    def update(self) -> None:
        super().update()

        # Trigger car sound effects. The zoom effect should play when the player is on the row above or below the car,
        # the honk effect should play when the player is on the same row.
        for y_offset, car_sound_num in [
            (-ROW_HEIGHT, Car.SOUND_ZOOM),
            (0, Car.SOUND_HONK),
            (ROW_HEIGHT, Car.SOUND_ZOOM),
        ]:
            # Is the player on the appropriate row?
            if game.bunner and game.bunner.y == self.y + y_offset:
                for child_obj in self.children:
                    # The child object must be a car
                    if isinstance(child_obj, Car):
                        # The car must be within 100 pixels of the player on the x-axis, and moving towards the player
                        # child_obj.dx < 0 is True or False depending on whether the car is moving left or right, and
                        # dx < 0 is True or False depending on whether the player is to the left or right of the car.
                        # If the results of these two comparisons are different, the car is moving towards the player.
                        # Also, for the zoom sound, the car must be travelling faster than one pixel per frame
                        dx = child_obj.x - game.bunner.x
                        if (
                            abs(dx) < 100
                            and ((child_obj.dx < 0) != (dx < 0))
                            and (y_offset == 0 or abs(child_obj.dx) > 1)
                        ):
                            child_obj.play_sound(car_sound_num)

    @override
    def check_collision(self, x: float) -> tuple[PlayerState, int]:
        if self.collide(x):
            game.play_sound("splat", 1)
            return PlayerState.SPLAT, 0
        else:
            return PlayerState.ALIVE, 0

    def play_sound(self) -> None:
        game.play_sound("road", 1)

    @override
    def next(self) -> Row:
        row_class: RowFactory
        if self.index == 0:
            row_class, index = Road, 1
        elif self.index < 5:
            # 80% chance of another road
            r: float = random()
            if r < 0.8:
                row_class, index = Road, self.index + 1
            elif r < 0.88:
                row_class, index = Grass, randint(0, 6)
            elif r < 0.94:
                row_class, index = Rail, 0
            else:
                row_class, index = Pavement, 0
        else:
            # We've reached maximum of 5 roads in a row, so choose something else
            r = random()
            if r < 0.6:
                row_class, index = Grass, randint(0, 6)
            elif r < 0.9:
                row_class, index = Rail, 0
            else:
                row_class, index = Pavement, 0

        # Create an object of the chosen row class
        return row_class(self, index, self.y - ROW_HEIGHT)


class Pavement(Row):
    __slots__ = ()

    def __init__(self, predecessor: Row | None, index: int, y: float) -> None:
        super().__init__("side", index, y)

    def play_sound(self) -> None:
        game.play_sound("sidewalk", 1)

    @override
    def next(self) -> Row:
        row_class: RowFactory
        if self.index < 2:
            row_class, index = Pavement, self.index + 1
        else:
            row_class, index = Road, 0

        # Create an object of the chosen row class
        return row_class(self, index, self.y - ROW_HEIGHT)


# Note that Rail does not inherit from ActiveRow
class Rail(Row):
    __slots__ = ("predecessor",)

    def __init__(self, predecessor: Row | None, index: int, y: float) -> None:
        super().__init__("rail", index, y)

        assert predecessor is not None  # rail rows always follow a row
        self.predecessor: Row = predecessor

    @override
    def update(self) -> None:
        super().update()

        # Only Rail rows with index 1 have trains on them
        if self.index != 1:
            return

        # Recreate the children list, excluding any which are too far off the edge of the screen to be visible
        self.children = [
            c for c in self.children if c.x > -1000 and c.x < WIDTH + 1000
        ]

        # If on-screen, and there is currently no train, and with a 1% chance every frame, create a train
        if (
            self.y < game.scroll_pos + HEIGHT
            and len(self.children) == 0
            and random() < 0.01
        ):
            # Randomly choose a direction for trains to move. This can be different for each train created
            dx: int = choice([-20, 20])
            self.children.append(
                Train(dx, (WIDTH + 1000 if dx < 0 else -1000, -13))
            )
            game.play_sound("bell")
            game.play_sound("train", 2)

    @override
    def check_collision(self, x: float) -> tuple[PlayerState, int]:
        if self.index == 2 and self.predecessor.collide(x):
            game.play_sound("splat", 1)
            return (
                PlayerState.SPLAT,
                8,
            )  # For the meaning of the second return value, see comments in Bunner.update
        else:
            return PlayerState.ALIVE, 0

    def play_sound(self) -> None:
        game.play_sound("grass", 1)

    @override
    def next(self) -> Row:
        row_class: RowFactory
        if self.index < 3:
            row_class, index = Rail, self.index + 1
        else:
            row_class, index = choice(((Road, 0), (Water, 0)))

        # Create an object of the chosen row class
        return row_class(self, index, self.y - ROW_HEIGHT)


@dataclass(eq=False, slots=True)
class Game:
    #: The player, or None on the menu (attract mode: the scenery scrolls by)
    bunner: Bunner | None = None
    #: The river/traffic ambience currently looping, by name
    looped_sounds: dict[str, Sound] = field(default_factory=dict, init=False)
    eagle: Eagle | None = field(default=None, init=False)
    rows: list[Row] = field(init=False)
    #: Level y coordinate of the top of the screen; decreases as the level
    #: scrolls up (a float while playing: the speed depends on the player)
    scroll_pos: float = field(init=False)

    def __post_init__(self) -> None:
        if self.bunner:
            music.set_volume(0.4)
        else:
            music.play("theme")
            music.set_volume(1)

        # First (bottom) row is always grass
        self.rows = [Grass(None, 0, 0)]

        self.scroll_pos = -HEIGHT

    def update(self) -> None:
        if self.bunner:
            # Scroll faster if the player is close to the top of the screen. Limit scroll speed to
            # between 1 and 3 pixels per frame.
            self.scroll_pos -= max(
                1,
                min(
                    3,
                    float(self.scroll_pos + HEIGHT - self.bunner.y)
                    / (HEIGHT // 4),
                ),
            )
        else:
            self.scroll_pos -= 1

        # Recreate the list of rows, excluding any which have scrolled off the bottom of the screen
        self.rows = [
            row
            for row in self.rows
            if row.y < int(self.scroll_pos) + HEIGHT + ROW_HEIGHT * 2
        ]

        # In Python, a negative index into a list gives you items in reverse order, e.g. my_list[-1] gives you the
        # last element of a list. Here, we look at the last row in the list - which is the top row - and check to see
        # if it has scrolled sufficiently far down that we need to add a new row above it. This may need to be done
        # multiple times - particularly when the game starts, as only one row is added to begin with.
        while self.rows[-1].y > int(self.scroll_pos) + ROW_HEIGHT:
            self.rows.append(self.rows[-1].next())

        # Update all rows, and the player and eagle (if present)
        objects: list[GameObject] = [*self.rows]
        if self.bunner:
            objects.append(self.bunner)
        if self.eagle:
            objects.append(self.eagle)
        for obj in objects:
            obj.update()

        # Play river and traffic sound effects, and adjust volume each frame based on the player's proximity to rows
        # of the appropriate types. For each such row, a number is generated representing how much the row should
        # contribute to the volume of the sound effect. These numbers are added together by Python's sum function.
        # On the following line we ensure that the volume can never be above 40% of the maximum possible volume.
        if self.bunner:
            for name, count, row_class in [
                ("river", 2, Water),
                ("traffic", 3, Road),
            ]:
                # The generator picks out each row of the appropriate type, e.g. Water rows if we're currently
                # updating the "river" sound effect.
                volume: float = min(
                    0.4,
                    sum(
                        16.0 / max(16.0, abs(r.y - self.bunner.y))
                        for r in self.rows
                        if isinstance(r, row_class)
                    )
                    - 0.2,
                )
                self.loop_sound(name, count, volume)

    def draw(self) -> None:
        # Create a list of all objects which need to be drawn. This includes all rows, plus the player
        # (a new list, so sorting it below doesn't reorder self.rows)
        all_objs: list[MyActor] = [*self.rows]

        if self.bunner:
            all_objs.append(self.bunner)

        # We want to draw objects in order based on their Y position. In general, objects further down the screen should be drawn
        # after (and therefore in front of) objects higher up the screen. We can use Python's built-in sort function
        # to put the items in the desired order, before we draw the  The following function specifies the criteria
        # used to decide how the objects are sorted.
        def sort_key(obj: MyActor) -> float:
            # Adding 39 and then doing an integer divide by 40 (the height of each row) deals with the situation where
            # the player sprite would otherwise be drawn underneath the row below. This could happen when the player
            # is moving up or down. If you assume that it occupies a 40x40 box which can be at an arbitrary y offset,
            # it generates the row number of the bottom row that that box overlaps. If the player happens to be
            # perfectly aligned to a row, adding 39 and dividing by 40 has no effect on the result. If it isn't, even
            # by a single pixel, the +39 causes it to be drawn one row later.
            return (obj.y + 39) // ROW_HEIGHT

        # Sort list using the above function to determine order
        all_objs.sort(key=sort_key)

        # Always draw eagle on top of everything
        if self.eagle:
            all_objs.append(self.eagle)

        for obj in all_objs:
            # Draw the object, taking the scroll position into account
            obj.draw_at(0, -int(self.scroll_pos))

        if DEBUG_SHOW_ROW_BOUNDARIES:
            # In draw order, so each row's label overlaps the next row's outline
            # the same way the sprites do
            for row in all_objs:
                if isinstance(row, Row):
                    top: float = row.y - int(self.scroll_pos)
                    renderer.rect(
                        row.x, top, WIDTH, ROW_HEIGHT, (255, 255, 255)
                    )
                    draw_text(str(row.index), row.x, top - ROW_HEIGHT)

    def score(self) -> int:
        assert self.bunner is not None  # only scored while playing
        return int(-320 - self.bunner.min_y) // 40

    def play_sound(self, name: str, count: int = 1) -> None:
        try:
            # Some sounds have multiple varieties, named "name0", "name1", ... If count > 1, we'll randomly choose
            # one from those. We don't play any sounds if there is no player (e.g. if we're on the menu)
            if self.bunner:
                sounds.load(f"{name}{randint(0, count - 1)}").play()
        except Exception:
            # If a sound fails to play, ignore the error
            pass

    def loop_sound(self, name: str, count: int, volume: float) -> None:
        try:
            # Similar to play_sound above, but for looped sounds we need to keep a reference to the sound so that we can
            # later modify its volume or turn it off. We use the dictionary self.looped_sounds for this - the sound
            # effect name is the key, and the value is the corresponding sound reference.
            if volume > 0 and name not in self.looped_sounds:
                sound: Sound = sounds.load(f"{name}{randint(0, count - 1)}")
                sound.play(loops=-1)  # -1 means sound will loop indefinitely
                self.looped_sounds[name] = sound

            if name in self.looped_sounds:
                if volume > 0:
                    self.looped_sounds[name].set_volume(volume)
                else:
                    self.looped_sounds.pop(name).stop()
        except Exception:
            # If a sound fails to play, ignore the error
            pass

    def stop_looped_sounds(self) -> None:
        try:
            for sound in self.looped_sounds.values():
                sound.stop()
            self.looped_sounds.clear()
        except Exception:
            # If sound system is not working/present, ignore the error
            pass


# Dictionary to keep track of which keys (GLFW codes) were held down last frame
key_status: dict[int, bool] = {}


# Was the given key just pressed? (i.e. is it currently down, but wasn't down on the previous frame?)
def key_just_pressed(key: int) -> bool:
    # The dictionary.get method allows us to check for a given entry without giving an error if that entry is not
    # present in the dictionary. False is the default value returned when the key is not present.
    pressed: bool = not key_status.get(key, False) and keyboard[key]

    # Before we return, we need to update the key's entry in the key_status dictionary (or create an entry if there
    # wasn't one already
    key_status[key] = keyboard[key]

    return pressed


def display_number(n: int, colour: int, x: float, align: int) -> None:
    # align: 0 for left, 1 for right
    digits: str = str(n)
    for i, digit in enumerate(digits):
        blit(f"digit{colour}{digit}", x + (i - len(digits) * align) * 25, 0)


class State(Enum):
    MENU = 1
    PLAY = 2
    GAME_OVER = 3


def update() -> None:
    global state, game, high_score

    match state:
        case State.MENU:
            if key_just_pressed(glfw.KEY_SPACE):
                state = State.PLAY
                game = Game(Bunner((240, -320)))
            else:
                game.update()

        case State.PLAY:
            assert game.bunner is not None
            # Is it game over?
            if game.bunner.state != PlayerState.ALIVE and game.bunner.timer < 0:
                # Update high score
                high_score = max(high_score, game.score())

                # Write high score file
                try:
                    with open("high.txt", "w") as file:
                        file.write(str(high_score))
                except Exception:
                    # If an error occurs writing the file, just ignore it and carry on, rather than crashing
                    pass

                state = State.GAME_OVER
            else:
                game.update()

        case State.GAME_OVER:
            # Switch to menu state, and create a new game object without a player
            if key_just_pressed(glfw.KEY_SPACE):
                game.stop_looped_sounds()
                state = State.MENU
                game = Game()

        case _:
            raise ValueError(f"unhandled game state {state!r}")


def draw() -> None:
    game.draw()

    match state:
        case State.MENU:
            blit("title", 0, 0)
            # On the menu the scroll position only ever moves a whole pixel a frame, so it is integral
            blit(
                f"start{[0, 1, 2, 1][int(game.scroll_pos) // 6 % 4]}",
                (WIDTH - 270) // 2,
                HEIGHT - 240,
            )

        case State.PLAY:
            # Display score and high score
            display_number(game.score(), 0, 0, 0)
            display_number(high_score, 1, WIDTH - 10, 1)

        case State.GAME_OVER:
            # Display "Game Over" image
            blit("gameover", 0, 0)

        case _:
            raise ValueError(f"unhandled game state {state!r}")


# Load high score from file (in the current directory, as the original does)
try:
    with open("high.txt") as f:
        high_score: int = int(f.read())
except Exception:
    # If opening the file fails (likely because it hasn't yet been created), set high score to 0
    high_score = 0

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

# Fixed 60 Hz timestep -- bunner's update() takes no dt. PGZERO_MAX_FRAMES=N
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
