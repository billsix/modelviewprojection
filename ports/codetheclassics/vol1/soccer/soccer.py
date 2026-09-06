# Code the Classics port: soccer, with its rendering engine inlined.
#
# Game code derived from Raspberry Pi Press's "Code the Classics" (vol 1):
#   Copyright (c) 2019 Eben Upton <eben@raspberrypi.org>
# Inlined engine (audio, images, renderer, keyboard, loop):
#   Copyright (c) 2026 William Emerison Six
# SPDX-License-Identifier: BSD-2-Clause
# Full license text: ports/codetheclassics/LICENSE.
"""soccer -- Substitute Soccer, a top-down football game from Code the
Classics vol. 1, on GLFW + OpenGL 3.3 core.

One self-contained file, read top to bottom like the course's demos: first
the small engine this game needs (a software audio mixer with a looping
crowd and a music fade, an image loader, a textured-quad renderer plus debug
lines and text, the anchored Actor sprite, keyboard state), then the game,
then the loop the game itself owns. The camera is the INVERSE of the
camera's placement, as the course teaches (Game.draw).
"""

from __future__ import annotations

import math
import os
import random
import signal
import sys
import threading
import time
from collections.abc import Callable, Generator, Iterator, Sequence
from dataclasses import InitVar, dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, cast

import gacalc.g3 as g3
import glfw
import numpy as np
import OpenGL.GL as GL
import sympy
from gacalc.g2 import Vector
from gacalc.transforms import (
    InvertibleFunction,
    inverse,
    scale_non_uniform,
    to_matrix,
    translate,
)
from numpy.typing import NDArray
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont

# ===== engine: shared state =====

WIDTH: int = 800
HEIGHT: int = 480
TITLE: str = "Substitute Soccer"

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

    def line(
        self, start: Vector, end: Vector, color: tuple[int, int, int]
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
    #: a fade-out: fade_gain multiplies volume and moves by fade_step per
    #: FRAME until it reaches 0, when the voice stops (music.fadeout)
    fade_gain: float = field(default=1.0, init=False)
    fade_step: float = field(default=0.0, init=False)
    stop_when_faded: bool = field(default=False, init=False)
    done: bool = field(default=False, init=False)

    def start_fadeout(self, ms: float) -> None:
        frames = max(_SAMPLE_RATE * ms / 1000.0, 1.0)
        self.fade_step = -self.fade_gain / frames
        self.stop_when_faded = True


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
            gain: _PCM | float
            if v.fade_step != 0.0:
                # a per-frame linear ramp while fading out
                ramp = v.fade_gain + v.fade_step * np.arange(
                    1, take + 1, dtype=np.float32
                )
                np.clip(ramp, 0.0, 1.0, out=ramp)
                v.fade_gain = float(ramp[-1])
                gain = np.repeat(ramp, _CHANNELS) * v.volume
                if v.fade_gain <= 0.0 and v.stop_when_faded:
                    v.done = True
            else:
                gain = v.fade_gain * v.volume
            sl = slice(filled * _CHANNELS, (filled + take) * _CHANNELS)
            out[sl] += seg * gain
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
    #: Volume (0.0-1.0) for current and future plays.
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
        until :meth:`stop` (the crowd)."""
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

    def fadeout(self, seconds: float) -> None:
        """Ramp the track to silence over ``seconds``, then stop it."""
        if self._voice is None or self._voice.done or seconds <= 0:
            self.stop()
            return
        self._looping = False
        self._voice.start_fadeout(seconds * 1000.0)


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
# or flat colour, switched by uUseTex and multiplied by uTint. soccer draws
# textured, untinted sprites, plus flat-colour lines for its debug overlays.

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

        # Dynamic buffer for the debug overlays' lines (raw pixel coords).
        self.prim.vao = GL.glGenVertexArrays(1)
        self.prim.vbo = GL.glGenBuffers(1)
        GL.glBindVertexArray(self.prim.vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.prim.vbo)
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, None)

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

    def line(
        self, start: Vector, end: Vector, color: tuple[int, int, int]
    ) -> None:
        """Draw a one-pixel line segment (the debug overlays)."""
        verts: NDArray[np.float32] = np.array([*start, *end], dtype=np.float32)
        GL.glBindVertexArray(self.prim.vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.prim.vbo)
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER, verts.nbytes, verts, GL.GL_DYNAMIC_DRAW
        )
        GL.glUniformMatrix4fv(self.uniforms.model, 1, GL.GL_TRUE, _identity())
        GL.glUniform1i(self.uniforms.use_tex, 0)
        r, g, b = color
        GL.glUniform4f(self.uniforms.tint, r / 255.0, g / 255.0, b / 255.0, 1.0)
        GL.glDrawArrays(GL.GL_LINES, 0, 2)

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
# position (or centred). soccer draws text only for its debug cost overlay.

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
    centered: bool = False,
) -> None:
    """Draw ``text`` with its top-left (or, if ``centered``, its centre) at
    ``(x, y)``."""
    img: Image = _render_text(text, size, color)
    if centered:
        x, y = x - img.width / 2, y - img.height / 2
    renderer.draw_image(img, (x, y))


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

HALF_WINDOW_W: float = WIDTH / 2

# Size of level, including both the pitch and the boundary surrounding it
LEVEL_W: int = 1000
LEVEL_H: int = 1400
HALF_LEVEL_W: int = LEVEL_W // 2
HALF_LEVEL_H: int = LEVEL_H // 2

HALF_PITCH_W: int = 442
HALF_PITCH_H: int = 622

GOAL_WIDTH: int = 186
GOAL_DEPTH: int = 20
HALF_GOAL_W: int = GOAL_WIDTH // 2

PITCH_BOUNDS_X = (HALF_LEVEL_W - HALF_PITCH_W, HALF_LEVEL_W + HALF_PITCH_W)
PITCH_BOUNDS_Y = (HALF_LEVEL_H - HALF_PITCH_H, HALF_LEVEL_H + HALF_PITCH_H)

GOAL_BOUNDS_X = (HALF_LEVEL_W - HALF_GOAL_W, HALF_LEVEL_W + HALF_GOAL_W)
GOAL_BOUNDS_Y = (
    HALF_LEVEL_H - HALF_PITCH_H - GOAL_DEPTH,
    HALF_LEVEL_H + HALF_PITCH_H + GOAL_DEPTH,
)

PITCH_RECT: Rect = Rect(
    PITCH_BOUNDS_X[0], PITCH_BOUNDS_Y[0], HALF_PITCH_W * 2, HALF_PITCH_H * 2
)
GOAL_0_RECT: Rect = Rect(
    GOAL_BOUNDS_X[0], GOAL_BOUNDS_Y[0], GOAL_WIDTH, GOAL_DEPTH
)
GOAL_1_RECT: Rect = Rect(
    GOAL_BOUNDS_X[0], GOAL_BOUNDS_Y[1] - GOAL_DEPTH, GOAL_WIDTH, GOAL_DEPTH
)

AI_MIN_X: int = 78
AI_MAX_X: int = LEVEL_W - 78
AI_MIN_Y: int = 98
AI_MAX_Y: int = LEVEL_H - 98

PLAYER_START_POS = [
    (350, 550),
    (650, 450),
    (200, 850),
    (500, 750),
    (800, 950),
    (350, 1250),
    (650, 1150),
]

LEAD_DISTANCE_1: int = 10
LEAD_DISTANCE_2: int = 50

DRIBBLE_DIST_X, DRIBBLE_DIST_Y = 18, 16

# Speeds for players in various situations. Speeds including 'BASE' can be boosted by the speed_boost difficulty
# setting (only for players on a computer-controlled team)
PLAYER_DEFAULT_SPEED: int = 2
CPU_PLAYER_WITH_BALL_BASE_SPEED: float = 2.6
PLAYER_INTERCEPT_BALL_SPEED: float = 2.75
LEAD_PLAYER_BASE_SPEED: float = 2.9
HUMAN_PLAYER_WITH_BALL_SPEED: int = 3
HUMAN_PLAYER_WITHOUT_BALL_SPEED: float = 3.3

DEBUG_SHOW_LEADS: bool = False
DEBUG_SHOW_TARGETS: bool = False
DEBUG_SHOW_PEERS: bool = False
DEBUG_SHOW_SHOOT_TARGET: bool = False
DEBUG_SHOW_COSTS: bool = False


# (eq=False on these dataclasses keeps identity comparison/hashing -- the
# generated __eq__ would compare fields and set __hash__ to None; slots=True
# fixes each object's attribute set to its declared fields, so every attribute
# an object ever gets is declared below)
@dataclass(eq=False, slots=True)
class Difficulty:
    goalie_enabled: bool

    #: When a player has the ball, either one or two players will be chosen from the other team to try to intercept
    #: the ball owner. Those players will have their 'lead' attributes set to a number indicating how far ahead of the
    #: ball they should try to run. (If they tried to go to where the ball is currently, they'd always trail behind)
    #: This attribute determines whether there should be one or two lead players
    second_lead_enabled: bool

    #: Speed boost to apply to CPU-team players in certain circumstances
    speed_boost: float

    #: Hold-off timer limits rate at which computer-controlled players can pass the ball
    holdoff_timer: int


DIFFICULTY: list[Difficulty] = [
    Difficulty(False, False, 0, 120),
    Difficulty(False, True, 0.1, 90),
    Difficulty(True, True, 0.2, 60),
]


# Custom sine/cosine functions for angles of 0 to 7, where 0 is up,
# 1 is up+right, 2 is right, etc.
def sin(x: float) -> float:
    return math.sin(x * math.pi / 4)


def cos(x: float) -> float:
    return sin(x + 2)


# Convert a vector to an angle in the range 0 to 7
def vec_to_angle(vec: Vector) -> int:
    # todo explain a bit
    # https://gamedev.stackexchange.com/questions/14602/what-are-atan-and-atan2-used-for-in-games
    return int(4 * math.atan2(vec.x, -vec.y) / math.pi + 8.5) % 8


# Convert an angle  in the range 0 to 7 to a direction vector. We use -cos rather than cos as increasing angles move
# in a clockwise rather than the usual anti-clockwise direction.
def angle_to_vec(angle: float) -> Vector:
    return Vector(sin(angle), -cos(angle))


# Used when calling functions such as sorted and min.
# todo explain more
# p.vpos - pos results in a Vector which we can get the length of, giving us
# the distance between pos and p.vpos
def dist_key(pos: Vector) -> Callable[[MyActor], float]:
    return lambda p: float((p.vpos - pos).magnitude())


# Turn a vector into a unit vector - i.e. a vector with length 1
# We also return the original length, before normalisation.
# We check for zero length, as trying to normalise a zero-length vector results in an error
def safe_normalise(vec: Vector) -> tuple[Vector, float]:
    length: float = float(vec.magnitude())
    if length == 0:
        return Vector(0, 0), 0
    else:
        return vec.normalize(), length


# MyActor extends Actor by providing the attribute 'vpos', which stores the object's current position in the
# WORLD (the level) as a vector. All code should change or read the position via vpos, as opposed to Actor's x/y or
# pos attributes, which are SCREEN positions. When the object is drawn, we set self.pos (equivalent to setting both
# self.x and self.y) based on vpos, mapped through the camera.
class MyActor(Actor):
    __slots__ = ("vpos",)

    def __init__(
        self, img: str, x: float = 0, y: float = 0, anchor: Anchor | None = None
    ) -> None:
        super().__init__(img, (0, 0), anchor=anchor)
        self.vpos: Vector = Vector(x, y)

    # Drawing maps this object's WORLD position (vpos) into screen space through
    # world_to_screen (built once per frame in Game.draw). This is the course's
    # "camera = the INVERSE of the camera's placement" (ch16/ch19), applied per
    # actor: one function replaces the ad-hoc `vpos - offset` subtraction. Not
    # an override of Actor.draw: it takes the map, so it has its own name.
    def draw_at(self, world_to_screen: InvertibleFunction[Vector]) -> None:
        # Set Actor's screen pos: world position through the world->screen map.
        self.pos = world_to_screen(self.vpos)
        self.draw()


# Ball physics model parameters
KICK_STRENGTH: float = 11.5
DRAG: float = 0.98


# ball physics for one axis
def ball_physics(
    pos: float, vel: float, bounds: tuple[float, float]
) -> tuple[float, float]:
    # Add velocity to position
    pos += vel

    # Check if ball is out of bounds, and bounce if so
    if pos < bounds[0] or pos > bounds[1]:
        pos, vel = pos - vel, -vel

    # Return new position and velocity, applying drag
    return pos, vel * DRAG


# Work out number of physics steps for ball to travel given distance
def steps(distance: float) -> int:
    # Initialize step count and initial velocity
    steps, vel = 0, KICK_STRENGTH

    # Run physics until distance reached or ball is nearly stopped
    while distance > 0 and vel > 0.25:
        distance, steps, vel = distance - vel, steps + 1, vel * DRAG

    return steps


@dataclass(eq=False, slots=True)
class Goal(MyActor):
    #: The team that defends this goal: 0 = the goal at the top, 1 = the bottom
    team: int

    def __post_init__(self) -> None:
        super().__init__(
            f"goal{self.team}", HALF_LEVEL_W, 0 if self.team == 0 else LEVEL_H
        )

    def active(self) -> bool:
        # Is ball within 500 pixels on the Y axis?
        return abs(game.ball.vpos.y - self.vpos.y) < 500


# Calculate if player 'target' is a good target for a pass from player 'source'
# target can also be a goal
def targetable(target: Player | Goal, source: Player) -> bool:
    # Find normalised (unit) vector v0 and distance d0 from source to target
    v0, d0 = safe_normalise(target.vpos - source.vpos)

    # If source player is on a computer-controlled team, avoid passes which are likely to be intercepted
    # (If source is player-controlled, that's the player's job)
    if not game.teams[source.team].human():
        # For each player p
        for p in game.players:
            # Find normalised vector v1 and distance d1 from source to p
            v1, d1 = safe_normalise(p.vpos - source.vpos)

            # If p is on the other team, and between source and target, and at a similiar
            # angular position, target is not a good target
            # Multiplying two vectors together invokes an operation known as dot product. It is calculated by
            # multiplying the X components of each vector, then multiplying the Y components, then adding the two
            # resulting numbers. When each of the input vectors is a unit vector (i.e. with a length of 1, as returned
            # from the safe_normalise function), the result of which is a number between -1 and 1. In this case we use
            # the result to determine whether player 'p' (vector v1) is in roughly the same direction as player 'target'
            # (vector v0), from the point of view of player 'source'.
            if (
                p.team != target.team
                and d1 > 0
                and d1 < d0
                and v0.scalar_product(v1) > 0.8
            ):
                return False

    # If target is on the same team, and ahead of source, and not too far away, and source is facing
    # approximately towards target (another dot product operation), then target is a good target.
    # The dot product operation (multiplying two unit vectors) is used to determine whether (and to what extent) the
    # source player is facing towards the target player. A value of 1 means target is directly ahead of source; -1
    # means they are directly behind; 0 means they are directly to the left or right.
    # See above for more explanation of dot product
    return (
        target.team == source.team
        and d0 > 0
        and d0 < 300
        and v0.scalar_product(angle_to_vec(source.dir)) > 0.8
    )


# Get average of two numbers; if the difference between the two is less than 1,
# snap to the second number. Used in Ball.update()
def avg(a: float, b: float) -> float:
    return b if abs(b - a) < 1 else (a + b) / 2


def on_pitch(pos: Vector) -> bool:
    # Only used when dribbling
    return (
        PITCH_RECT.collidepoint(pos)
        or GOAL_0_RECT.collidepoint(pos)
        or GOAL_1_RECT.collidepoint(pos)
    )


@dataclass(eq=False, slots=True)
class Ball(MyActor):
    #: Velocity
    vel: Vector = field(default_factory=lambda: Vector(0, 0))
    #: The player dribbling the ball, if any
    owner: Player | None = None
    #: Hold-off timer limiting how often a computer player can pass
    timer: int = 0
    shadow: MyActor = field(default_factory=lambda: MyActor("balls"))

    def __post_init__(self) -> None:
        super().__init__("ball", HALF_LEVEL_W, HALF_LEVEL_H)

    # Check for collision with player p
    def collide(self, p: Player) -> bool:
        # The ball collides with p if p's hold-off timer has expired
        # and it is DRIBBLE_DIST_X or fewer pixels away
        return (
            p.timer < 0 and (p.vpos - self.vpos).magnitude() <= DRIBBLE_DIST_X
        )

    def update(self) -> None:
        self.timer -= 1

        # If the ball has an owner, it's being dribbled, so its position is
        # based on its owner's position
        if self.owner:
            # Calculate new ball position for dribbling
            # Our target position will be a point just ahead of our owner. However, we don't want to just snap to that
            # position straight away. We want to transition to it over several frames, so we take the average of our
            # current position and the target position. We also use slightly different offsets for the X and Y axes,
            # to reflect that that the game's perspective is not completely top-down - so the positions the ball can
            # take in relation to the player should form an ellipse instead of a circle.
            # todo explain maths
            new_pos: Vector = Vector(
                avg(
                    float(self.vpos.x),
                    float(
                        self.owner.vpos.x + DRIBBLE_DIST_X * sin(self.owner.dir)
                    ),
                ),
                avg(
                    float(self.vpos.y),
                    float(
                        self.owner.vpos.y - DRIBBLE_DIST_Y * cos(self.owner.dir)
                    ),
                ),
            )

            if on_pitch(new_pos):
                # New position is on the pitch, so update
                self.vpos = new_pos
            else:
                # New position is off the pitch, so player loses the ball
                # Set hold-off timer so player can't immediately reacquire the ball
                self.owner.timer = 60

                # Give ball small velocity in player's direction of travel
                self.vel = angle_to_vec(self.owner.dir) * 3

                # Un-set owner
                self.owner = None
        else:
            # Run physics, one axis at a time

            # If ball is vertically inside the goal, it can only go as far as the
            # sides of the goal - otherwise it can go all the way to the sides of
            # the pitch
            bounds_x: tuple[int, int] = (
                GOAL_BOUNDS_X
                if abs(self.vpos.y - HALF_LEVEL_H) > HALF_PITCH_H
                else PITCH_BOUNDS_X
            )

            # If ball is horizontally inside the goal, it can go all the way to
            # the back of the net - otherwise it can only go up to the end of
            # the pitch
            bounds_y: tuple[int, int] = (
                GOAL_BOUNDS_Y
                if abs(self.vpos.x - HALF_LEVEL_W) < HALF_GOAL_W
                else PITCH_BOUNDS_Y
            )

            new_x, new_vel_x = ball_physics(
                float(self.vpos.x), float(self.vel.x), bounds_x
            )
            self.vpos = Vector(new_x, self.vpos.y)
            self.vel = Vector(new_vel_x, self.vel.y)
            new_y, new_vel_y = ball_physics(
                float(self.vpos.y), float(self.vel.y), bounds_y
            )
            self.vpos = Vector(self.vpos.x, new_y)
            self.vel = Vector(self.vel.x, new_vel_y)

        # Update shadow position to track ball
        self.shadow.vpos = self.vpos

        # Search for a player that can acquire the ball
        for target in game.players:
            # A player can acquire the ball if the ball has no owner, or the player is on the other team
            # from the owner, and collides with the ball
            if (
                not self.owner or self.owner.team != target.team
            ) and self.collide(target):
                if self.owner:
                    # New player is taking the ball from previous owner
                    # Set hold-off timer so previous owner can't immediately reacquire the ball
                    self.owner.timer = 60

                # Set hold-off timer (dependent on difficulty) to limit rate at which
                # computer-controlled players can pass the ball
                self.timer = game.difficulty.holdoff_timer

                # Update owner, and controllable player for player's team, to player
                game.teams[target.team].active_control_player = self.owner = (
                    target
                )

        # If the ball has an owner, it's time to decide whether to kick it
        if self.owner:
            team: Team = game.teams[self.owner.team]

            # Find the closest targetable player or goal (could be None)
            # First we create a list of all players/goals which can be targeted
            targetable_players: list[Player | Goal] = [
                p
                for p in [*game.players, *game.goals]
                if p.team == self.owner.team and targetable(p, self.owner)
            ]

            target: Player | Goal | None = None
            if targetable_players:
                # Choose the nearest one
                # dist_key returns a function which gets the distance of the ball owner from whichever player or goal (p)
                # the sorted function is currently assessing
                target = min(targetable_players, key=dist_key(self.owner.vpos))
                game.debug_shoot_target = target.vpos

            do_shoot: bool
            if team.controls is not None:
                # If the owner is player-controlled, we kick if the player hits their kick key
                do_shoot = team.controls.shoot()
            else:
                # If the owner is computer-controlled, we kick if the ball's hold-off timer has expired
                # and there is a targetable player or goal, and the targetable player or goal is in a more
                # favourable location (according to cost()) than the owner's location. (The upstream compared the
                # whole (cost, position) tuples, which would have crashed on an exact cost tie; only the cost counts.)
                do_shoot = (
                    self.timer <= 0
                    and target is not None
                    and cost(target.vpos, self.owner.team)[0]
                    < cost(self.owner.vpos, self.owner.team)[0]
                )

            if do_shoot:
                # play a random kick effect
                game.play_sound("kick", 4)

                if target:
                    # If there is a targetable player or goal, kick towards it

                    # If the owner is player-controlled, we assume the player will continue to hold the same direction
                    # keys down after the pass, so the target  will start moving in the same direction as the
                    # current owner; on this assumption, we will kick the ball slightly ahead of the target player's
                    # current position,  through a process of iterative refinement

                    # If the owner is computer-controlled, or the target is a goal, we only execute the loop once and
                    # so do not apply lead, as there are no keys being held down and goals don't move.

                    r: float = 0

                    # Decide how many times we're going to go through the loop - the more times, the more accurate
                    iterations: int = (
                        8 if team.human() and isinstance(target, Player) else 1
                    )

                    for _ in range(iterations):
                        # In the first loop, t will simply be the position of the targeted player or goal.
                        # In subsequent loops (if there are any), it will represent a position which is at the
                        # target's feet plus a bit further in whichever direction the player is currently pressing.
                        t: Vector = (
                            target.vpos + angle_to_vec(self.owner.dir) * r
                        )

                        # Get direction vector and distance between target pos and us
                        vec, length = safe_normalise(t - self.vpos)

                        # The steps function works out the number of physics steps the ball will take to travel
                        # the given distance
                        # todo r
                        r = HUMAN_PLAYER_WITHOUT_BALL_SPEED * steps(length)
                else:
                    # We're not targeting a player or goal, so just kick the ball straight ahead

                    # Get direction vector
                    vec = angle_to_vec(self.owner.dir)

                    # Make a rough guess at which player the ball might end up closest to so, we can set them as the new
                    # active player. Pick a point 250 pixels ahead and find the nearest player to that.
                    target = min(
                        [p for p in game.players if p.team == self.owner.team],
                        key=dist_key(self.vpos + (vec * 250)),
                    )

                if isinstance(target, Player):
                    # If we just kicked the ball towards a player, make that player the new active player for this team
                    game.teams[self.owner.team].active_control_player = target

                # Owner can't regain the ball for at least 10 frames
                self.owner.timer = 10

                # Set velocity
                self.vel = vec * KICK_STRENGTH

                # We no longer have an owner
                self.owner = None


# Return True if the given position is inside the level area, otherwise False
# Takes the goals into account so you can't run through them
def allow_movement(pos: Vector) -> bool:
    if abs(pos.x - HALF_LEVEL_W) > HALF_LEVEL_W:
        # Trying to walk off the left or right side of the level
        return False

    elif abs(pos.x - HALF_LEVEL_W) < HALF_GOAL_W + 20:
        # Player is within the bounds of the goals on the X axis, don't let them walk into, through or behind the goal
        # +20 takes with of player sprite into account
        return abs(pos.y - HALF_LEVEL_H) < HALF_PITCH_H

    else:
        # Player is outside the bounds of the goals on the X axis, so they can walk off the pitch and to the edge
        # of the level
        return abs(pos.y - HALF_LEVEL_H) < HALF_LEVEL_H


# Generate a score for a given position, where lower numbers are considered to be better.
# This is called when a computer-controlled player with the ball is working out which direction to run in, or whether
# to pass the ball to another player, or kick it into the goal.
# Several things make up the final score:
# - the distance to our own goal - further away is better
# - the proximity of players on the other team - we want to get the ball away from them as much as possible
# - a quadratic equation (don't panic too much!) causing the player to favour the centre of the pitch and their opponents goal
# - an optional handicap value which can bias the result towards or away from a particular position
def cost(pos: Vector, team: int, handicap: float = 0) -> tuple[float, Vector]:
    # Get pos of our own goal. We do it this way rather than getting the pos of the actual goal object
    # because this way gives us the pos of the goal's entrance, whereas the actual goal sprites are not anchored based
    # on the entrances.
    own_goal_pos: Vector = Vector(
        HALF_LEVEL_W, 78 if team == 1 else LEVEL_H - 78
    )
    inverse_own_goal_distance: float = 3500 / float(
        (pos - own_goal_pos).magnitude()
    )

    result: float = (
        inverse_own_goal_distance
        + sum(
            4000 / max(24, float((p.vpos - pos).magnitude()))
            for p in game.players
            if p.team != team
        )
        + float((pos.x - HALF_LEVEL_W) ** 2 / 200 - pos.y * (4 * team - 2))
        + handicap
    )

    return result, pos


# Not a dataclass: the super().__init__ position is the computed kickoff
# position (not the x/y args), and Player instances are compared by identity
# against game.kickoff_player / active_control_player.
class Player(MyActor):
    ANCHOR: ClassVar[Anchor] = (25, 37)

    # Kickoff wiring, assigned CROSS-OBJECT in Game.reset (a.peer = b,
    # b.mark = ..., zipped[0].lead = ...) rather than in __init__, so it is
    # declared here: every attribute a Player ever gets is a slot.
    __slots__ = (
        "peer",
        "mark",
        "lead",
        "home",
        "team",
        "dir",
        "anim_frame",
        "timer",
        "shadow",
        "debug_target",
    )
    peer: Player
    mark: Player | Goal
    lead: float | None

    def __init__(self, x: float, y: float, team: int) -> None:
        # Player objects are recreated each time there is a kickoff
        # Team will be 0 or 1
        # The x and y values supplied represent our 'home' position - the place we'll return to by default when not near
        # the ball. However, on creation, we want players to be in their kickoff positions, which means all players from
        # team 0 will be below the halfway line, and players from team 1 above. The player chosen to actually do the
        # kickoff is moved to be alongside the centre spot after the player objects have been created.

        # Calculate our initial position for kickoff by halving y, adding 550 and then subtracting either 400 for
        # team 1, or nothing for team 0
        kickoff_y: float = (y / 2) + 550 - (team * 400)

        # Call the constructor of the parent class (MyActor)
        super().__init__("blank", x, kickoff_y, Player.ANCHOR)

        # Remember home position, where we'll stand by default if we're not active (i.e. far from the ball)
        self.home: Vector = Vector(x, y)

        # Store team
        self.team: int = team

        # Facing direction: 0 = up, 1 = top right, up to 7 = top left
        self.dir: int = 0

        # Animation frame
        self.anim_frame: float = -1

        self.timer: int = 0

        self.shadow: MyActor = MyActor("blank", 0, 0, Player.ANCHOR)

        # Used when DEBUG_SHOW_TARGETS is on
        self.debug_target: Vector | None = Vector(0, 0)

    def active(self) -> bool:
        # Is ball within 400 pixels on the Y axis? If so I'll be considered active, meaning I'm currently doing
        # something useful in the game like trying to get the ball. If I'm not active, I'll either mark another player,
        # or just stay at my home position
        return abs(game.ball.vpos.y - self.home.y) < 400

    def update(self) -> None:
        # decrement holdoff timer
        self.timer -= 1

        # One of the main jobs of this method is to decide where the player will run to, and at what speed.
        # The default is to run slowly towards home position, but target and speed may be overwritten in the code below
        # start from home; rebound below, never mutated
        target: Vector = self.home
        speed: float = PLAYER_DEFAULT_SPEED

        # Some shorthand variables to make the code below a bit easier to follow
        my_team: Team = game.teams[self.team]
        pre_kickoff: bool = game.kickoff_player is not None
        i_am_kickoff_player: bool = self == game.kickoff_player
        ball: Ball = game.ball

        if (
            self == my_team.active_control_player
            and my_team.controls is not None
            and (not pre_kickoff or i_am_kickoff_player)
        ):
            # This player is the currently active player for its team, and is player-controlled, and either we're not
            # currently waiting for kickoff, or this player is the designated kickoff player.
            # The last part of the condition ensures that in a 2 player game, player 2 can't make their active player
            # run around while waiting for player 1 to do the kickoff (and vice versa)

            # A player with the ball runs slightly more slowly than one without
            speed = (
                HUMAN_PLAYER_WITH_BALL_SPEED
                if ball.owner == self
                else HUMAN_PLAYER_WITHOUT_BALL_SPEED
            )

            # Find target by calling the controller for the player's team
            target = self.vpos + my_team.controls.move(speed)

        elif ball.owner is not None:
            # Someone has the ball - is it me?
            if ball.owner == self:
                # We are the owner, and are computer-controlled (otherwise we would have taken the other arm
                # of the top-level if statement)

                # Evaluate five positions (left 90, left 45, ahead, right 45, right 90)
                # target is the one with the lowest value of cost()
                # List comprehension steps through the angles: -2 to 2, where 0 is up, 1 is up & right, etc
                # For each angle 'd', we call the cost function with a position, which is 3 pixels from the
                # current position, if the player were to move in the direction of d. We also pass cost() our team number.
                # The last parameter, abs(d), introduces a tendency for the player to continue running forward. Try
                # multiplying it by 3 or 4 to see what happens!

                # First, create a list of costs for each of the 5 tested positions - a lower number is better. Each
                # element is a tuple containing the cost and the position that cost relates to.
                costs: list[tuple[float, Vector]] = [
                    cost(
                        self.vpos + angle_to_vec(self.dir + d) * 3,
                        self.team,
                        abs(d),
                    )
                    for d in range(-2, 3)
                ]

                # Then choose the element with the lowest cost. We use min() to find the element with the lowest value.
                # min uses < to compare pairs of elements. Each element of costs is a tuple with two elements (a cost
                # value and the target position). When comparing a pair of tuples using <, Python first compares the
                # first element of each tuple. If they're different, that's what determines which tuple is considered to
                # have a lower value. If they're the same, Python moves on to looking at the next element. However, this
                # can lead to a crash in this case as the target position is an instance of the Vector class, which
                # does not support comparisons using <. In practice it's rare for two positions to have the same cost
                # value, but it's nevertheless prudent to eliminate the risk. The solution we chosen is to use the
                # optional 'key' parameter for min, telling the function to only use the first element of each tuple
                # for the comparisons.
                # When min finds the tuple with the minimum cost value, we extract the target pos (which is what we
                # actually care about) and discard the actual cost value - hence the '_' dummy variable
                _, target = min(costs, key=lambda element: element[0])

                # speed depends on difficulty
                speed = (
                    CPU_PLAYER_WITH_BALL_BASE_SPEED
                    + game.difficulty.speed_boost
                )

            elif ball.owner.team == self.team:
                # Ball is owned by another player on our team
                if self.active():
                    # If I'm near enough to the ball, try to run somewhere useful, and unique to this player - we
                    # don't want all players running to the same place. Target is halfway between home and a point
                    # 400 pixels ahead of the ball. Team 0 are trying to score in the goal at the top of the
                    # pitch, team 1 the goal at the bottom
                    direction: int = -1 if self.team == 0 else 1
                    target = Vector(
                        (ball.vpos.x + target.x) / 2,
                        (ball.vpos.y + 400 * direction + target.y) / 2,
                    )
                # If we're not active, we'll do the default action of moving towards our home position
            else:
                # Ball is owned by a player on the opposite team
                if self.lead is not None:
                    # We are one of the players chosen to pursue the owner

                    # Target a position in front of the ball's owner, the distance based on the value of lead, while
                    # making sure we keep just inside the pitch
                    target = (
                        ball.owner.vpos
                        + angle_to_vec(ball.owner.dir) * self.lead
                    )

                    # Stay on the pitch
                    target = Vector(
                        max(AI_MIN_X, min(AI_MAX_X, target.x)),
                        max(AI_MIN_Y, min(AI_MAX_Y, target.y)),
                    )

                    speed = LEAD_PLAYER_BASE_SPEED
                    if game.teams[1 - self.team].human():
                        speed += game.difficulty.speed_boost

                elif self.mark.active():
                    # The player or goal we've been chosen to mark is active

                    if my_team.human():
                        # If I'm on a human team, just run towards the ball.
                        # We don't do the marking behaviour below for human teams for a number of reasons. Try changing
                        # the code to see how the game feels when marking behaviour applies to both human and computer
                        # teams.
                        target = ball.vpos
                    else:
                        # Get vector between the ball and whatever we're marking
                        vec, length = safe_normalise(ball.vpos - self.mark.vpos)

                        # Alter length to choose a position in between the ball and whatever we're marking
                        # We don't apply this behaviour for human teams - in that case we just run straight at the ball
                        if isinstance(self.mark, Goal):
                            # If I'm currently the goalie, get in between the ball and goal, and don't get too far
                            # from the goal
                            length = min(150, length)
                        else:
                            # Otherwise, just get halfway between the ball and whoever I'm marking
                            length /= 2

                        target = self.mark.vpos + vec * length
        else:
            # No-one has the ball

            # If we're pre-kickoff and I'm the kickoff player, OR if we're not pre-kickoff and I'm active
            if (pre_kickoff and i_am_kickoff_player) or (
                not pre_kickoff and self.active()
            ):
                # Try to intercept the ball
                # Deciding where to go to achieve this is harder than you might think. You can't target the ball's
                # current location, because (assuming it's moving) by the time you get there it'll have moved on, so
                # you'll always be trailing behind it. And you can't target where it's going to end up after rolling to
                # a halt, because you might end up getting there before it and just be standing around waiting for it to
                # get there. What we want to do is find a target which allows us to intercept the ball along its path in
                # the minimum possible time and distance.
                # The code below simulates the ball's movement over a series of frames, working out where it would be
                # after each frame. We also work out how far the player could have moved at each frame, and whether
                # that distance would be enough to reach the currently simulated location of the ball.
                target = Vector(
                    *ball.vpos
                )  # current simulated location of ball
                vel: Vector = Vector(
                    *ball.vel
                )  # ball velocity - slows down each frame due to friction
                frame: int = 0

                # DRIBBLE_DIST_X is the distance at which a player can gain control of the ball.
                # vel.magnitude() > 0.5 ensures we don't keep simulating frames for longer than necessary - once the ball
                # is moving that slowly, it's not going to move much further, so there's no point in simulating dozens
                # more frames of very tiny movements. If you experience a decreased frame rate when no one has the ball,
                # try increasing 0.5 to a higher number.
                while (
                    (target - self.vpos).magnitude()
                    > PLAYER_INTERCEPT_BALL_SPEED * frame + DRIBBLE_DIST_X
                    and vel.magnitude() > 0.5
                ):
                    target += vel
                    vel *= DRAG
                    frame += 1

                speed = PLAYER_INTERCEPT_BALL_SPEED

            elif pre_kickoff:
                # Waiting for kick-off, but we're not the kickoff player
                # Just stay where we are. Without this we'd run to our home position, but that is different from
                # our position at kickoff (where all players are on their team's side of the pitch)
                target = Vector(target.x, self.vpos.y)

        # Get direction vector and distance beteen current pos and target pos
        # vec[0] and vec[1] will be the x and y components of the vector
        vec, distance = safe_normalise(target - self.vpos)

        self.debug_target = target

        # Check to see if we're already at the target position
        if distance > 0:
            # Limit movement to our max speed
            distance = min(distance, speed)

            # Set facing direction based on the direction we're moving
            target_dir: int = vec_to_angle(vec)

            # Update the x and y components of the player's position - but don't allow them to go off the edge of the
            # level. Processing the x and y components separately allows the player to slide along the edge when trying
            # to move diagonally off the edge of the level.
            if allow_movement(self.vpos + Vector(vec.x * distance, 0)):
                self.vpos = Vector(self.vpos.x + vec.x * distance, self.vpos.y)
            if allow_movement(self.vpos + Vector(0, vec.y * distance)):
                self.vpos = Vector(self.vpos.x, self.vpos.y + vec.y * distance)

            # todo
            self.anim_frame = (self.anim_frame + max(distance, 1.5)) % 72
        else:
            # Already at target position - just turn to face the ball
            target_dir = vec_to_angle(ball.vpos - self.vpos)
            self.anim_frame = -1

        # Update facing direction - each frame, move one step towards the target direction
        # This code essentially says that if the target direction is the same as the current direction, there should
        # be no change; if target is between 1 and 4 steps clockwise from current, we should rotate one step clockwise,
        # and if it's between 1 and 3 steps anticlockwise (which can also be thought of as 5 to 7 steps clockwise), we
        # should rotate one step anticlockwise - which is equivalent to stepping 7 steps clockwise
        dir_diff: int = target_dir - self.dir
        self.dir = (self.dir + [0, 1, 1, 1, 1, 7, 7, 7][dir_diff % 8]) % 8

        suffix: str = f"{self.dir}{(int(self.anim_frame) // 18) + 1}"

        self.image = f"player{self.team}{suffix}"
        self.shadow.image = f"players{suffix}"

        # Update shadow position to track player
        self.shadow.vpos = self.vpos


@dataclass(eq=False, slots=True)
class Team:
    #: The human's controls, or None for a computer-controlled team
    controls: Controls | None
    #: The player this team currently controls (arrow over its head)
    active_control_player: Player | None = None
    score: int = 0

    def human(self) -> bool:
        return self.controls is not None


@dataclass(eq=False, slots=True)
class Game:
    #: The two teams' controls (None = computer-controlled); __post_init__
    #: hands them to the teams
    p1_controls: InitVar[Controls | None] = None
    p2_controls: InitVar[Controls | None] = None
    difficulty_level: InitVar[int] = 2
    teams: list[Team] = field(init=False)
    difficulty: Difficulty = field(init=False)
    #: Counts down the "scored a goal" state; 0 = reset for kick-off
    score_timer: int = field(default=0, init=False)
    #: Which team has just scored - also governs who kicks off next
    scoring_team: int = field(default=1, init=False)
    # The per-kick-off state, set up by reset() (called from __post_init__)
    players: list[Player] = field(init=False)
    goals: list[Goal] = field(init=False)
    kickoff_player: Player | None = field(init=False)
    ball: Ball = field(init=False)
    #: What the camera looks at; chases the ball
    camera_focus: Vector = field(init=False)
    debug_shoot_target: Vector | None = field(default=None, init=False)

    def __post_init__(
        self,
        p1_controls: Controls | None,
        p2_controls: Controls | None,
        difficulty_level: int,
    ) -> None:
        self.teams = [Team(p1_controls), Team(p2_controls)]
        self.difficulty = DIFFICULTY[difficulty_level]

        try:
            if self.teams[0].human():
                # Beginning a game with at least 1 human player
                music.fadeout(1)
                sounds.load("crowd").play(-1)
                sounds.load("start").play()
            else:
                # No players - we must be on the menu. Play title music.
                music.play("theme")
                sounds.load("crowd").stop()
        except Exception:
            # Ignore sound errors
            pass

        self.reset()

    def reset(self) -> None:
        # Called at game start, and after a goal has been scored

        # Set up players list/positions
        # The lambda function is used to give the player start positions a slight random offset so they're not
        # perfectly aligned to their starting spots
        self.players = []

        def random_offset(coordinate: float) -> float:
            return coordinate + random.randint(-32, 32)

        for pos in PLAYER_START_POS:
            # pos is a pair of coordinates in a tuple
            # For each entry in pos, create one player for each team - positions are flipped (both horizontally and
            # vertically) versions of each other
            self.players.append(
                Player(random_offset(pos[0]), random_offset(pos[1]), 0)
            )
            self.players.append(
                Player(
                    random_offset(LEVEL_W - pos[0]),
                    random_offset(LEVEL_H - pos[1]),
                    1,
                )
            )

        # Players in the list are stored in an alternating fashion - a team 0 player, then a team 1 player, and so on.
        # The peer for each player is the opposing team player at the opposite end of the list. As there are 14 players
        # in total, the peers are 0 and 13, 1 and 12, 2 and 11, and so on.
        for a, b in zip(self.players, self.players[::-1]):
            a.peer = b

        # Create two goals
        self.goals = [Goal(i) for i in range(2)]

        # The current active player under control by each team, indicated by arrows over their heads
        # Choose first two players to begin with
        self.teams[0].active_control_player = self.players[0]
        self.teams[1].active_control_player = self.players[1]

        # If team 1 just scored (or if it's the start of the game), team 0 will kick off
        other_team = 1 if self.scoring_team == 0 else 0

        # Players are stored in the players list in an alternating fashion - the first player being on team 0, the
        # second on team 1, the third on team 0 etc. The player that kicks off will always be the first player of
        # the relevant team.
        self.kickoff_player = self.players[other_team]

        # Set pos of kickoff player. A team 0 player will stand to the left of the ball, team 1 on the right
        self.kickoff_player.vpos = Vector(
            HALF_LEVEL_W - 30 + other_team * 60, HALF_LEVEL_H
        )

        # Create ball
        self.ball = Ball()

        # Focus camera on ball - copy ball pos
        self.camera_focus = self.ball.vpos

        self.debug_shoot_target = None

    def update(self) -> None:
        self.score_timer -= 1

        if self.score_timer == 0:
            # Reset for new kick-off after goal scored
            self.reset()

        elif (
            self.score_timer < 0
            and abs(self.ball.vpos.y - HALF_LEVEL_H) > HALF_PITCH_H
        ):
            game.play_sound("goal", 2)

            self.scoring_team = 0 if self.ball.vpos.y < HALF_LEVEL_H else 1
            self.teams[self.scoring_team].score += 1
            # Game goes into "scored a goal" state for 60 frames
            self.score_timer = 60

        # Each frame, reset mark and lead of each player
        for b in self.players:
            b.mark = b.peer
            b.lead = None
            b.debug_target = None

        # Reset debug shoot target
        self.debug_shoot_target = None

        if self.ball.owner:
            # Ball has an owner (above is equivalent to s.ball.owner != None, or s.ball.owner is not None)
            # Assign some shorthand variables
            o: Player = self.ball.owner
            pos, team = o.vpos, o.team
            owners_target_goal: Goal = game.goals[team]
            other_team: int = 1 - team

            if self.difficulty.goalie_enabled:
                # Find the nearest opposing team player to the goal, and make them mark the goal
                nearest: Player = min(
                    [p for p in self.players if p.team != team],
                    key=dist_key(owners_target_goal.vpos),
                )

                # Set the ball owner's peer to mark whoever the goalie was marking, then set the goalie to mark the goal
                o.peer.mark = nearest.mark
                nearest.mark = owners_target_goal

            # Choose one or two lead players to spearhead the attack on the ball owner
            # Create a list of players who are on the opposite team from the ball owner, are allowed to acquire
            # the ball (their hold-off timer must not be positive), are not currently being controlled by a human,
            # and are not currently assigned to be the goalie. The list is sorted based on distance from the ball owner.
            chase_candidates: list[Player] = sorted(
                [
                    p
                    for p in self.players
                    if p.team != team
                    and p.timer <= 0
                    and (
                        not self.teams[other_team].human()
                        or p != self.teams[other_team].active_control_player
                    )
                    and not isinstance(p.mark, Goal)
                ],
                key=dist_key(pos),
            )

            # a is a list of players from chase_candidates who are upfield of the ball owner (i.e. towards our own goal, away from the
            # direction of the goal the ball owner is trying to score in). b is all the other players. It's possible for
            # one of these to be empty, as there might not be any players in the relevant direction.
            a: list[Player] = [
                p
                for p in chase_candidates
                if (p.vpos.y > pos.y if team == 0 else p.vpos.y < pos.y)
            ]
            b: list[Player] = [p for p in chase_candidates if p not in a]

            # Zip a and b together in an alternating fashion. Why do we add none_pair (i.e. [None,None]) to each list?
            # Because the zip function stops when there are no more items in one of the lists. We want our final list
            # to contain at least 2 elements. Adding none_pair (i.e. [None,None] as defined near the top) ensures that each
            # list has at least 2 items. But we don't want any values in the final list to be None, hence the final part
            # of the list comprehension 'for s in t if s', which discards any None values from the final result
            none_pair: list[None] = [None] * 2
            zipped = [
                s for t in zip(a + none_pair, b + none_pair) for s in t if s
            ]

            # Either one or two players (depending on difficulty settings) follow the ball owner, one from up-field and
            # one from down-field of the owner
            zipped[0].lead = LEAD_DISTANCE_1
            if self.difficulty.second_lead_enabled:
                zipped[1].lead = LEAD_DISTANCE_2

            # If the ball has an owner, kick-off must have taken place, so unset the kickoff player
            # Of course, kick-off might have already taken place a while ago, in which case kick-off_player will already
            # be None, and will remain None
            self.kickoff_player = None

        # Update all players and ball
        for obj in [*self.players, self.ball]:
            obj.update()

        owner: Player | None = self.ball.owner

        for team_num in range(2):
            team_obj: Team = self.teams[team_num]

            # Manual player switching when space is pressed
            if team_obj.controls is not None and team_obj.controls.shoot():
                # Find nearest player to the ball on our team
                # If the ball has an owner (who must be on the other team because if not, control would have
                # automatically switched to the ball owner and we wouldn't need to manually switch), we weight the
                # choice in favour of players who are upfield (towards our goal), since such players may be better
                # placed to intercept the ball owner.
                # The function dist_key_weighted is equivalent to the dist_key function earlier in the code, but with
                # this weighting added. We use this function as the key for the min function, which will choose
                # the player who results in the lowest value when passed as an argument to dist_key_weighted.
                def dist_key_weighted(p: Player) -> float:
                    dist_to_ball: float = float(
                        (p.vpos - self.ball.vpos).magnitude()
                    )
                    # Thonny gives a warning about the following line, relating to closures (an advanced topic), but
                    # in this case there is not actually a problem as the closure is only called within the loop
                    goal_dir: int = 2 * team_num - 1
                    if owner and (p.vpos.y - self.ball.vpos.y) * goal_dir < 0:
                        return dist_to_ball / 2
                    else:
                        return dist_to_ball

                self.teams[team_num].active_control_player = min(
                    [p for p in game.players if p.team == team_num],
                    key=dist_key_weighted,
                )

        # Get vector between current camera pos and ball pos
        camera_ball_vec, distance = safe_normalise(
            self.camera_focus - self.ball.vpos
        )
        if distance > 0:
            # Move camera towards ball, at no more than 8 pixels per frame
            self.camera_focus -= camera_ball_vec * min(distance, 8)

    def draw(self) -> None:
        # For the purpose of scrolling, all objects will be drawn with these offsets
        # the camera offset, clamped per axis to the level bounds
        offset: Vector = Vector(
            max(0, min(LEVEL_W - WIDTH, self.camera_focus.x - WIDTH / 2)),
            max(0, min(LEVEL_H - HEIGHT, self.camera_focus.y - HEIGHT / 2)),
        )
        # Camera as an INVERSE transformation (mvp course, ch16/ch19): placing the
        # camera at `offset` in the world is translate(offset); drawing needs the
        # opposite direction (world -> screen), i.e. its inverse. One
        # InvertibleFunction then maps every world position to screen space, and
        # world_to_screen(v) is exactly `v - offset` (proven byte-identical).
        world_to_screen: InvertibleFunction[Vector] = inverse(
            translate(b=offset)
        )

        # The pitch sits at the world origin; map it through the same function.
        pitch_pos: Vector = world_to_screen(Vector(0.0, 0.0))
        blit("pitch", float(pitch_pos.x), float(pitch_pos.y))

        # Prepare to draw all objects
        # 1. Create a list of all players and the ball, sorted based on their Y positions
        # 2. Add object shadows to the list
        # 3. Add the two goals at each end of the list
        # (note - technically we're not adding items to the list in steps two and three, we're creating a new list
        # which consists of the old list plus the new items)
        sprites: list[Ball | Player] = sorted(
            [self.ball, *self.players], key=lambda obj: obj.y
        )
        objects: list[MyActor] = [
            self.goals[0],
            *sprites,
            *(obj.shadow for obj in sprites),
            self.goals[1],
        ]

        # Draw all objects
        for obj in objects:
            obj.draw_at(world_to_screen)

        # Show active players
        for t in range(2):
            # Only show arrow for human teams
            active: Player | None = self.teams[t].active_control_player
            if self.teams[t].human() and active is not None:
                arrow_pos: Vector = world_to_screen(active.vpos) - Vector(
                    11, 45
                )
                blit(f"arrow{t}", float(arrow_pos.x), float(arrow_pos.y))

        # The debug overlays below keep the raw `vpos - offset` subtraction: they
        # are flag-gated scaffolding (off by default), and world_to_screen(v) is
        # the same value, demonstrated above on the real render path.
        if DEBUG_SHOW_LEADS:
            for p in self.players:
                if game.ball.owner and p.lead:
                    renderer.line(
                        game.ball.owner.vpos - offset,
                        p.vpos - offset,
                        (0, 0, 0),
                    )

        if DEBUG_SHOW_TARGETS:
            for p in self.players:
                if p.debug_target is not None:
                    renderer.line(
                        p.debug_target - offset, p.vpos - offset, (255, 0, 0)
                    )

        if DEBUG_SHOW_PEERS:
            for p in self.players:
                renderer.line(
                    p.peer.vpos - offset, p.vpos - offset, (0, 0, 255)
                )

        if DEBUG_SHOW_SHOOT_TARGET:
            if self.debug_shoot_target and self.ball.owner:
                renderer.line(
                    self.ball.owner.vpos - offset,
                    self.debug_shoot_target - offset,
                    (255, 0, 255),
                )

        if DEBUG_SHOW_COSTS and self.ball.owner:
            for x in range(0, LEVEL_W, 60):
                for y in range(0, LEVEL_H, 26):
                    c: float = cost(Vector(x, y), self.ball.owner.team)[0]
                    screen_pos: Vector = Vector(x, y) - offset
                    draw_text(
                        f"{c:.0f}",
                        float(screen_pos.x),
                        float(screen_pos.y),
                        centered=True,
                    )

    def play_sound(self, name: str, c: int) -> None:
        # Only play sounds if we're not in the menu state
        if state != State.MENU:
            try:
                sounds.load(f"{name}{random.randint(0, c - 1)}").play()
            except Exception:
                # Ignore sound errors
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


@dataclass(eq=False, slots=True)
class Controls:
    #: 0 = arrows + space, 1 = WASD + left shift
    player_num: InitVar[int]
    key_up: int = field(init=False)
    key_down: int = field(init=False)
    key_left: int = field(init=False)
    key_right: int = field(init=False)
    key_shoot: int = field(init=False)

    def __post_init__(self, player_num: int) -> None:
        (
            self.key_up,
            self.key_down,
            self.key_left,
            self.key_right,
            self.key_shoot,
        ) = (
            (
                glfw.KEY_UP,
                glfw.KEY_DOWN,
                glfw.KEY_LEFT,
                glfw.KEY_RIGHT,
                glfw.KEY_SPACE,
            )
            if player_num == 0
            else (
                glfw.KEY_W,
                glfw.KEY_S,
                glfw.KEY_A,
                glfw.KEY_D,
                glfw.KEY_LEFT_SHIFT,
            )
        )

    def move(self, speed: float) -> Vector:
        # Return vector representing amount of movement that should occur
        dx: int = (
            -1
            if keyboard[self.key_left]
            else 1
            if keyboard[self.key_right]
            else 0
        )
        dy: int = (
            -1 if keyboard[self.key_up] else 1 if keyboard[self.key_down] else 0
        )
        return Vector(dx, dy) * speed

    def shoot(self) -> bool:
        return key_just_pressed(self.key_shoot)


class State(Enum):
    MENU = 0
    PLAY = 1
    GAME_OVER = 2


class MenuState(Enum):
    NUM_PLAYERS = 0
    DIFFICULTY = 1


def update() -> None:
    global state, game, menu_state, menu_num_players, menu_difficulty

    match state:
        case State.MENU:
            if key_just_pressed(glfw.KEY_SPACE):
                if menu_state == MenuState.NUM_PLAYERS:
                    # If we're doing a 2 player game, skip difficulty selection
                    if menu_num_players == 1:
                        menu_state = MenuState.DIFFICULTY
                    else:
                        # Start 2P game
                        state = State.PLAY
                        menu_state = None
                        game = Game(Controls(0), Controls(1))
                else:
                    # Start 1P game
                    state = State.PLAY
                    menu_state = None
                    game = Game(Controls(0), None, menu_difficulty)
            else:
                # Detect + act on up/down arrow keys (each key_just_pressed call also records that key's
                # state for next frame, so both are always called, in this order)
                down_pressed: bool = key_just_pressed(glfw.KEY_DOWN)
                up_pressed: bool = key_just_pressed(glfw.KEY_UP)
                selection_change: int = (
                    1 if down_pressed else -1 if up_pressed else 0
                )
                if selection_change != 0:
                    try:
                        sounds.load("move").play()
                    except Exception:
                        # Ignore sound errors
                        pass
                    if menu_state == MenuState.NUM_PLAYERS:
                        menu_num_players = 2 if menu_num_players == 1 else 1
                    else:
                        menu_difficulty = (
                            menu_difficulty + selection_change
                        ) % 3

            game.update()

        case State.PLAY:
            # First player to 9 wins
            if (
                max([team.score for team in game.teams]) == 9
                and game.score_timer == 1
            ):
                state = State.GAME_OVER
            else:
                game.update()

        case State.GAME_OVER:
            if key_just_pressed(glfw.KEY_SPACE):
                # Switch to menu state, and create a new game object without a player
                state = State.MENU
                menu_state = MenuState.NUM_PLAYERS
                game = Game()

        case _:
            raise ValueError(f"unhandled game state {state!r}")


def draw() -> None:
    game.draw()

    match state:
        case State.MENU:
            # Draw title screen and menu
            # There are 5 menu images numbered 01, 02, 10, 11 and 12.
            # 01 and 02 are the images for indicating whether 1 or 2 player mode
            # is selected; 10, 11 and 12 are for the difficulty selection screen -
            # easy, medium or hard
            blit(
                f"menu0{menu_num_players}"
                if menu_state == MenuState.NUM_PLAYERS
                else f"menu1{menu_difficulty}",
                0,
                0,
            )

        case State.PLAY:
            # Display score bar at top
            blit("bar", HALF_WINDOW_W - 176, 0)

            # Show score for each team
            for i in range(2):
                blit(f"s{game.teams[i].score}", HALF_WINDOW_W + 7 - 39 * i, 6)

            # Show GOAL image if a goal has recently been scored
            if game.score_timer > 0:
                blit("goal", HALF_WINDOW_W - 300, HEIGHT / 2 - 88)

        case State.GAME_OVER:
            # Display "Game Over" image
            blit(f"over{int(game.teams[1].score > game.teams[0].score)}", 0, 0)

            # Show score for each team
            for i in range(2):
                blit(
                    f"l{i}{game.teams[i].score}",
                    HALF_WINDOW_W + 25 - 125 * i,
                    144,
                )

        case _:
            raise ValueError(f"unhandled game state {state!r}")


# Set the initial game state
state: State = State.MENU

# Menu state
menu_state: MenuState | None = MenuState.NUM_PLAYERS
menu_num_players: int = 1
menu_difficulty: int = 0

# Create a new Game object
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

# Fixed 60 Hz timestep -- soccer's update() takes no dt. PGZERO_MAX_FRAMES=N
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
