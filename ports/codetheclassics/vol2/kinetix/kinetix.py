# Code the Classics port: kinetix, with its rendering engine inlined.
#
# Game code derived from Raspberry Pi Press's "Code the Classics" (vol 2):
#   Copyright (c) 2024 Eben Upton <eben@raspberrypi.com>
# Inlined engine (audio, images, renderer, keyboard, loop):
#   Copyright (c) 2026 William Emerison Six
# SPDX-License-Identifier: BSD-2-Clause
# Full license text: ports/codetheclassics/LICENSE.
"""kinetix -- Breakout style brick breaker with powerups, from Code the
Classics vol. 2, on GLFW + OpenGL 3.3 core.

One self-contained file, read top to bottom like the course's demos: first
the small engine this game needs (a software audio mixer, an image loader
plus CPU-drawn surfaces for the brick and shadow layers, a textured-quad
renderer with a scissor clip, the anchored Actor sprite, keyboard and gamepad
state), then the game, then the loop the game itself owns.
"""

from __future__ import annotations

import math
import os
import signal
import sys
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Generator, Iterator, Sequence
from dataclasses import InitVar, dataclass, field
from enum import Enum, IntEnum
from random import choice, randint, random, uniform
from typing import TYPE_CHECKING, Any, Protocol, cast, override

import gacalc.g3 as g3
import glfw
import numpy as np
import OpenGL.GL as GL
import sympy
from gacalc.g2 import Vector
from gacalc.transforms import (
    InvertibleFunction,
    plane_rotation,
    scale_non_uniform,
    to_matrix,
    translate,
)
from numpy.typing import NDArray
from PIL import Image as PILImage

# ===== engine: shared state =====

WIDTH: int = 640
HEIGHT: int = 640
TITLE: str = "Kinetix"

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

    def set_clip(
        self, rect: tuple[float, float, float, float] | None
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


@dataclass(slots=True, eq=False)
class Surface(Image):
    """An Image the game draws INTO on the CPU (``fill``/``blit`` composite
    into ``rgba``); the GL texture is re-uploaded lazily when dirty. Built by
    :meth:`Surface.create`. These change rarely (e.g. when a brick breaks), so
    the CPU compositing is cheap enough.
    """

    #: True when ``rgba`` changed since the last upload
    _dirty: bool = field(default=True, init=False)

    def fill(
        self,
        color: tuple[int, int, int, int],
        rect: tuple[float, float, float, float] | None = None,
    ) -> None:
        """Fill the whole surface (or the ``rect`` sub-region) with ``color``."""
        if rect is None:
            self.rgba[...] = color
        else:
            x, y, w, h = rect
            x0, y0 = max(0, x), max(0, y)
            x1, y1 = min(self.width, x + w), min(self.height, y + h)
            if x1 > x0 and y1 > y0:
                self.rgba[y0:y1, x0:x1] = color
        self._dirty = True

    def blit(self, src: Image, pos: tuple[float, float]) -> None:
        """Alpha-composite ``src`` onto this surface with its top-left at ``pos``."""
        src_rgba: NDArray[np.uint8] = src.rgba
        sh, sw = src_rgba.shape[0], src_rgba.shape[1]
        px, py = pos
        x, y = int(px), int(py)
        # Clip to destination bounds.
        dx0, dy0 = max(0, x), max(0, y)
        dx1, dy1 = min(self.width, x + sw), min(self.height, y + sh)
        if dx1 <= dx0 or dy1 <= dy0:
            return
        sx0, sy0 = dx0 - x, dy0 - y
        s: NDArray[np.float32] = src_rgba[
            sy0 : sy0 + (dy1 - dy0), sx0 : sx0 + (dx1 - dx0)
        ].astype(np.float32)
        d: NDArray[np.float32] = self.rgba[dy0:dy1, dx0:dx1].astype(np.float32)
        # straight-alpha src-over
        sa: NDArray[np.float32] = s[..., 3:4] / 255.0
        da: NDArray[np.float32] = d[..., 3:4] / 255.0
        out_a: NDArray[np.float32] = sa + da * (1.0 - sa)
        with np.errstate(invalid="ignore", divide="ignore"):
            out_rgb: NDArray[Any] = (
                s[..., :3] * sa + d[..., :3] * da * (1.0 - sa)
            ) / np.where(out_a == 0, 1.0, out_a)
        self.rgba[dy0:dy1, dx0:dx1, :3] = np.clip(out_rgb, 0, 255).astype(
            np.uint8
        )
        self.rgba[dy0:dy1, dx0:dx1, 3:4] = np.clip(
            out_a * 255.0, 0, 255
        ).astype(np.uint8)
        self._dirty = True

    def set_alpha(self, a: float) -> None:
        """Scale the whole surface's alpha by ``a`` (0-255) -- used for fades."""
        self.rgba[..., 3] = np.clip(
            self.rgba[..., 3].astype(np.float32) * (a / 255.0), 0, 255
        ).astype(np.uint8)
        self._dirty = True

    def gl_texture(self) -> int:
        """Return this surface's GL texture name, re-uploading it if dirty."""
        if self._tex is None:
            self._tex = GL.glGenTextures(1)
        if self._dirty:
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._tex)
            for p in (GL.GL_TEXTURE_MIN_FILTER, GL.GL_TEXTURE_MAG_FILTER):
                GL.glTexParameteri(GL.GL_TEXTURE_2D, p, GL.GL_NEAREST)
            for p in (GL.GL_TEXTURE_WRAP_S, GL.GL_TEXTURE_WRAP_T):
                GL.glTexParameteri(GL.GL_TEXTURE_2D, p, GL.GL_CLAMP_TO_EDGE)
            GL.glTexImage2D(
                GL.GL_TEXTURE_2D,
                0,
                GL.GL_RGBA,
                self.width,
                self.height,
                0,
                GL.GL_RGBA,
                GL.GL_UNSIGNED_BYTE,
                np.ascontiguousarray(self.rgba),
            )
            self._dirty = False
        return cast(int, self._tex)

    @classmethod
    def create(cls, width: int, height: int, transparent: bool) -> Surface:
        """A ``width`` x ``height`` surface, fully transparent or opaque black."""
        rgba: NDArray[np.uint8] = np.zeros((height, width, 4), dtype=np.uint8)
        if not transparent:
            rgba[..., 3] = 255
        return cls(rgba)


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

    def set_clip(self, rect: tuple[float, float, float, float] | None) -> None:
        """Clip drawing to pixel ``rect`` (``None`` disables clipping)."""
        if rect is None:
            GL.glDisable(GL.GL_SCISSOR_TEST)
            return
        x, y, w, h = rect
        sx: float = self.fb_width / self.width
        sy: float = self.fb_height / self.height
        GL.glEnable(GL.GL_SCISSOR_TEST)
        # glScissor is in framebuffer pixels with origin bottom-left.
        GL.glScissor(
            int(x * sx),
            int(self.fb_height - (y + h) * sy),
            int(w * sx),
            int(h * sy),
        )

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
# ``keyboard.<name>`` is True while that key is held. The GLFW key callback
# below feeds presses and releases in; the game polls the names in the table
# each frame -- they are the only keys kinetix reads.

_NAME_TO_KEY: dict[str, int] = {
    "left": glfw.KEY_LEFT,
    "right": glfw.KEY_RIGHT,
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


# ===== engine: joystick =====
#
# A gamepad through GLFW. BEST EFFORT: with no controller attached every query
# returns a neutral value, so the game stays fully playable on the keyboard.
# (Gamepad behaviour can't be verified headless -- that is for on-hardware
# testing.) pyGLFW hands joystick state back as a (POINTER, count) tuple, so
# ``list()`` of it would be [pointer, count], not the values: index the pointer.

# GLFW hat bit flags -> (x, y) with y up = +1.
_HAT_UP = 1
_HAT_RIGHT = 2
_HAT_DOWN = 4
_HAT_LEFT = 8


def joystick_count() -> int:
    """Return how many joysticks GLFW sees."""
    return sum(1 for jid in range(16) if glfw.joystick_present(jid))


def _read_glfw_array(result: Any) -> list[Any]:
    """Unpack pyGLFW's ``(ctypes_array_pointer, count)`` joystick return."""
    if not result:
        return []
    arr, count = result
    return [arr[i] for i in range(count)]


@dataclass(slots=True, eq=False)
class Joystick:
    """A single gamepad, addressed by its GLFW joystick id (0-based)."""

    index: int

    def _axes(self) -> list[float]:
        try:
            return _read_glfw_array(glfw.get_joystick_axes(self.index))
        except Exception:
            return []

    def _buttons(self) -> list[int]:
        try:
            return _read_glfw_array(glfw.get_joystick_buttons(self.index))
        except Exception:
            return []

    def _hats(self) -> list[int]:
        try:
            return _read_glfw_array(glfw.get_joystick_hats(self.index))
        except Exception:
            return []

    def get_axis(self, i: int) -> float:
        """Return axis ``i`` in -1.0..1.0 (0.0 if out of range / unavailable)."""
        a: list[float] = self._axes()
        try:
            return float(a[i]) if i < len(a) else 0.0
        except (TypeError, ValueError):
            return 0.0

    def get_numbuttons(self) -> int:
        """Return the number of buttons."""
        return len(self._buttons())

    def get_button(self, i: int) -> int:
        """Return button ``i`` as 1 (pressed) / 0 (released or out of range)."""
        b: list[int] = self._buttons()
        if i >= len(b):
            return 0
        try:
            return int(b[i])
        except (TypeError, ValueError):
            return 1 if b[i] else 0

    def get_numhats(self) -> int:
        """Return the number of hats (d-pads)."""
        return len(self._hats())

    def get_hat(self, i: int) -> tuple[int, int]:
        """Return hat ``i`` as ``(x, y)`` in {-1, 0, 1}, y up ((0, 0) if absent)."""
        h: list[int] = self._hats()
        if i >= len(h):
            return (0, 0)
        v: int = h[i]
        x: int = (1 if v & _HAT_RIGHT else 0) - (1 if v & _HAT_LEFT else 0)
        y: int = (1 if v & _HAT_UP else 0) - (1 if v & _HAT_DOWN else 0)
        return (x, y)


# ===== game code =====

#: A rotation in the plane by an angle: the multiball spread turns the ball's
#: direction by 120 and 240 degrees (a gacalc rotor, see generate_multiballs)
_turn = plane_rotation(Vector.e_1, Vector.e_2)

# Set up constants
BAT_SPEED: int = 8

BAT_MIN_X: int = 35
BAT_MAX_X: int = 605

TOP_EDGE: int = 50
RIGHT_EDGE: int = 617
LEFT_EDGE: int = 23

BAT_TOP_EDGE: int = 590

BALL_INITIAL_OFFSET: int = 10

# Default direction for a Ball. A shared object, but Ball copies it (see the
# defensive-copy note on the class), so no ball aliases another's direction.
DEFAULT_BALL_DIR: Vector = Vector(0, 0)

BALL_START_SPEED: int = 5
BALL_MIN_SPEED: int = 4
BALL_MAX_SPEED: int = 11

# Normal ball speed up interval (10 seconds at 60 frames per second)
BALL_SPEED_UP_INTERVAL: int = 10 * 60
# Speed up interval for when the ball is above a speed threshold
BALL_SPEED_UP_INTERVAL_FAST: int = 15 * 60
BALL_FAST_SPEED_THRESHOLD: int = 7

BALL_RADIUS: int = 7

BULLET_SPEED: int = 8

BRICKS_X_START: int = 20
BRICKS_Y_START: int = 100

BRICK_WIDTH: int = 40
BRICK_HEIGHT: int = 20
SHADOW_OFFSET: int = 10

POWERUP_CHANCE: float = 0.2

FIRE_INTERVAL: int = 30

PORTAL_ANIMATION_SPEED: int = 5

LEVELS = [
    [
        "        ",
        "        ",
        "        ",
        "     a  ",
        "    a7a ",
        "     a  ",
        "     a55",
        "    444 ",
        "   333a ",
        "  222a  ",
        " 111a   ",
        "   11aa ",
        "    111 ",
        "    6   ",
        "     6  ",
    ],
    [
        "        ",
        "        ",
        "    3   ",
        "    3   ",
        "    3   ",
        "    3000",
        "    3000",
        "   53000",
        "   53000",
        "  35a555",
        " 3 5aa55",
        "3  5aaa5",
        "  355555",
        "  333333",
        "   333  ",
        "    33  ",
        "     3  ",
    ],
    [
        "   7    ",
        "  77    ",
        " 7777   ",
        " 7777   ",
        " 77777  ",
        " 77777  ",
        " 77 777 ",
        " 7  7777",
        " 7   717",
        "     777",
        "      77",
        "      7 ",
        "     c7 ",
        "      c ",
        "      c ",
    ],
    [
        "   03   ",
        "   30   ",
        "    03  ",
        "    30  ",
        "     0  ",
        " 8   0  ",
        " 88 8033",
        "  883333",
        "   8333d",
        "   33733",
        "  33373d",
        " 3333333",
        " 3c 333d",
        " cc 3333",
        " c   3 3",
        "     3 3",
        "    3 3 ",
        "    c 3 ",
        "    cc3c",
        "    cccc",
        "      d ",
    ],
    [
        "5   9  0",
        "0   4  3",
        "08  4  4",
        "53  47 2",
        " 39 92 1",
        " 84  2  ",
        "  47 26 ",
        "5 92 71 ",
        "08 26 1 ",
        "53971 1 ",
        " 8471c6 ",
        "  926acc",
        "   71aad",
        "039 6aac",
        "dc421ac ",
        "  dccc  ",
        "    d   ",
    ],
    [
        "  dccccd",
        "  c89765",
        "  c34210",
        "  c34210",
        "  c34210",
        "  c34210",
        "  c3421d",
        "  c34210",
        "  c34210",
        "  c34210",
        "  c34210",
        "  c89765",
        "  dccccd",
    ],
]


def get_mirrored_level(level: list[str]) -> list[str]:
    # For each row, return a new row which includes the existing row plus
    # a mirrored version.
    # row[-2::-1] produces a mirorred version of the list, excluding the last element
    return [row + row[-2::-1] for row in level]


class GameObject(Protocol):
    """What Game.update and Game.draw need of everything in play: a per-frame
    update and a draw. Every Actor subclass below satisfies it structurally
    (deliberately not by subclassing the protocol -- an explicit subclass
    inherits the stub members, so a missing method would go unreported).
    """

    def update(self) -> None: ...

    def draw(self) -> None: ...


class Controls(ABC):
    """How the bat is driven: the keyboard, a gamepad, or the title screen's
    AI. Tracks the fire button's edge so a press counts once."""

    __slots__ = ("fire_previously_down", "is_fire_pressed")

    def __init__(self) -> None:
        self.fire_previously_down: bool = False
        self.is_fire_pressed: bool = False

    def update(self) -> None:
        # Call each frame to update fire status
        fire_down: bool = self.fire_down()
        self.is_fire_pressed = fire_down and not self.fire_previously_down
        self.fire_previously_down = fire_down

    @abstractmethod
    def get_x(self) -> float:
        # Overridden by subclasses
        pass

    @abstractmethod
    def fire_down(self) -> bool:
        # Overridden by subclasses
        pass

    def fire_pressed(self) -> bool:
        return self.is_fire_pressed


class KeyboardControls(Controls):
    __slots__ = ()

    @override
    def get_x(self) -> float:
        return (
            -BAT_SPEED if keyboard.left else BAT_SPEED if keyboard.right else 0
        )

    @override
    def fire_down(self) -> bool:
        return keyboard.space


class JoystickControls(Controls):
    __slots__ = ("joystick",)

    def __init__(self, joystick: Joystick) -> None:
        super().__init__()
        self.joystick: Joystick = joystick

    @override
    def get_x(self) -> float:
        # First check if there is an input on the dpad for the X axis. The dpad is classified here as a joystick 'hat'
        if self.joystick.get_numhats() > 0 and self.joystick.get_hat(0)[0] != 0:
            return self.joystick.get_hat(0)[0] * BAT_SPEED

        # If no input on the dpad, check for analogue left/right input. A dead-zone is necessary because some
        # devices may register a small amount of input even when the player isn't moving the analogue stick
        axis_value: float = self.joystick.get_axis(0)
        return 0 if abs(axis_value) < 0.2 else axis_value * BAT_SPEED

    @override
    def fire_down(self) -> bool:
        # Before checking button 0, check to make sure that the controller actually has any buttons
        # There are some weird devices out there which could cause a crash if this check were not present
        if self.joystick.get_numbuttons() <= 0:
            print("Warning: controller does not have any buttons!")
            return False
        return self.joystick.get_button(0) != 0


class AIControls(Controls):
    __slots__ = ("offset",)

    def __init__(self) -> None:
        super().__init__()
        self.offset: int = 0

    @override
    def get_x(self) -> float:
        if game.portal_active:
            # If the portal to the next level is open, just move right so that we go through it
            return BAT_SPEED
        else:
            # Randomly shift the bat AI offset over time, so the AI player doesn't constantly hit the ball perfectly
            # in the centre of the bat. Limit offset between -40 and 40
            self.offset += randint(-1, 1)
            self.offset = min(max(-40, self.offset), 40)

            # Follow position of the first ball (in case of multiball)
            return min(
                BAT_SPEED,
                max(-BAT_SPEED, game.balls[0].x - (game.bat.x + self.offset)),
            )

    @override
    def fire_down(self) -> bool:
        # Just have the AI mash the fire button
        return randint(0, 5) == 0


class Powerup(IntEnum):
    # These numbers correspond to the sprite filenames
    # e.g. barrel06 is extend bat, frame 6
    EXTEND_BAT = 0
    GUN = 1
    SMALL_BAT = 2
    MAGNET = 3
    MULTI_BALL = 4
    FAST_BALLS = 5
    SLOW_BALLS = 6
    PORTAL = 7
    EXTRA_LIFE = 8


class BatType(IntEnum):
    NORMAL = 0
    MAGNET = 1
    GUN = 2
    EXTENDED = 3
    SMALL = 4


#: The powerups that change the bat, and what they change it to
POWERUP_BAT_TYPES: dict[Powerup, BatType] = {
    Powerup.EXTEND_BAT: BatType.EXTENDED,
    Powerup.GUN: BatType.GUN,
    Powerup.SMALL_BAT: BatType.SMALL,
    Powerup.MAGNET: BatType.MAGNET,
}

#: The sound played when each powerup is collected (PORTAL has its own)
POWERUP_SOUNDS: dict[Powerup, str] = {
    Powerup.EXTEND_BAT: "bat_extend",
    Powerup.GUN: "bat_gun",
    Powerup.MAGNET: "magnet",
    Powerup.SMALL_BAT: "bat_small",
    Powerup.EXTRA_LIFE: "extra_life",
    Powerup.FAST_BALLS: "speed_up",
    Powerup.SLOW_BALLS: "powerup",
    Powerup.MULTI_BALL: "multiball",
}


class CollisionType(Enum):
    WALL = 0
    BAT = 1
    BAT_EDGE = 2
    BRICK = 3
    INDESTRUCTIBLE_BRICK = 4


# (eq=False on these Actor dataclasses keeps identity comparison/hashing --
# the generated __eq__ would compare fields and set __hash__ to None; slots=True
# fixes each object's attribute set to its declared fields, so every attribute
# an object ever gets is declared below)
@dataclass(eq=False, slots=True)
class Bullet(Actor):
    #: named spawn_pos, NOT pos: pos is an Actor property, and a dataclass
    #: would treat the property object as this field's default value
    spawn_pos: InitVar[PointLike]
    #: 0 = fired from the bat's left gun, 1 = the right
    side: InitVar[int]
    alive: bool = True

    def __post_init__(self, spawn_pos: PointLike, side: int) -> None:
        super().__init__(f"bullet{side}", spawn_pos)

    def update(self) -> None:
        self.y -= BULLET_SPEED

        c: Collision | None = game.collide(self.x, self.y, Vector(0, -1), 2)
        if c is not None:
            self.alive = False
            game.impacts.append(Impact(self.pos, 15))
            if c.kind in (
                CollisionType.BRICK,
                CollisionType.INDESTRUCTIBLE_BRICK,
            ):
                game.play_sound("bullet_hit", 4)


# The barrel class represents the collectable powerups that sometimes fall from destroyed bricks
# Not a dataclass: init chooses the powerup type from a weighted table that
# reads live game state and consumes RNG -- the init logic is the interesting part.
class Barrel(Actor):
    __slots__ = ("type", "time", "shadow")

    def __init__(self, pos: PointLike) -> None:
        super().__init__("blank", pos)

        # Decide powerup type, with each type able to have its own probability
        # First we create a dictionary of types to weights, where a higher weight means that powerup is more likely
        # to be chosen. For the PORTAL powerup, which opens a portal to the next level, it can't be generated unless
        # there are only a few bricks remaining, at which point it becomes very likely
        weights: dict[Powerup, int] = {
            Powerup.EXTEND_BAT: 6,
            Powerup.GUN: 6,
            Powerup.SMALL_BAT: 6,
            Powerup.MAGNET: 6,
            Powerup.MULTI_BALL: 6,
            Powerup.FAST_BALLS: 6,
            Powerup.SLOW_BALLS: 6,
            Powerup.EXTRA_LIFE: 2,
            Powerup.PORTAL: 0
            if game.bricks_remaining > 20 or game.portal_active
            else 20,
        }

        # Create a list of powerup types, with each type repeated a certain
        # number of times based on its weight
        types: list[Powerup] = [
            type for type, weight in weights.items() for _ in range(weight)
        ]

        # Randomly choose one of the types from the list. Types which
        # are repeated many times are more likely to be chosen
        self.type: Powerup = choice(types)

        self.time: int = 0

        # Create separate actor for shadow sprite
        self.shadow: Actor = Actor(
            "barrels", self.pos + Vector(SHADOW_OFFSET, SHADOW_OFFSET)
        )

    def update(self) -> None:
        self.time += 1
        self.y += 1

        w: float = (game.bat.width // 2) + BALL_RADIUS

        # Check for barrel being collected by bat
        if (
            BAT_TOP_EDGE - 10 <= self.y <= BAT_TOP_EDGE + 30
            and abs(self.x - game.bat.x) < w
        ):
            # Create barrel collection animation - sprites 'impacte0' to 'impacte4'
            # 14 is E in hexadecimal
            game.impacts.append(Impact((self.x, self.y - 11), 14))

            # Play sound effect (if this powerup has a sound effect)
            if self.type in POWERUP_SOUNDS:
                game.play_sound(POWERUP_SOUNDS[self.type])

            # Move barrel off the bottom of the screen, it will then be deleted
            self.y = HEIGHT + 100

            match self.type:
                # the bat-changing powerups share one handler, keyed by
                # the POWERUP_BAT_TYPES table
                case t if t in POWERUP_BAT_TYPES:
                    game.bat.change_type(POWERUP_BAT_TYPES[t])
                case Powerup.MULTI_BALL:
                    game.balls = [
                        j for b in game.balls for j in b.generate_multiballs()
                    ]
                case Powerup.FAST_BALLS:
                    game.change_all_ball_speeds(3)
                case Powerup.SLOW_BALLS:
                    game.change_all_ball_speeds(-3)
                case Powerup.PORTAL:
                    game.activate_portal()
                case Powerup.EXTRA_LIFE:
                    game.lives += 1
                case _:
                    raise ValueError(f"unhandled powerup {self.type!r}")

        # The name of each powerup sprite has the format "barrel[powerup type][frame]",
        # where powerup type is a number from 0 to 8 and frame is a number from 0 to 9
        # We switch to a new animation frame every 10 game frames
        self.image = f"barrel{int(self.type)}{self.time // 10 % 10}"

        self.shadow.pos = self.pos + Vector(SHADOW_OFFSET, SHADOW_OFFSET)


# The Impact class is used for the animations played when the ball hits a wall or destroys a brick
@dataclass(eq=False, slots=True)
class Impact(Actor):
    spawn_pos: InitVar[PointLike]
    #: 0-15, the impact sprite family (a brick's number, 12 for the ball, ...)
    type: int
    time: int = 0

    def __post_init__(self, spawn_pos: PointLike) -> None:
        super().__init__("blank", spawn_pos)

    def update(self) -> None:
        # The impact animation sprites have names like 'impact00' where the first digit is the type of impact and
        # the second is the animation frame. The type is converted into a hexadecimal number. The type can be between
        # 0 and 15, where values from 10 to 15 are represented by the hexadecimal digits a to f. The Python hex
        # function is used to convert the type to hexadecimal, the resulting string will always start with '0x' meaning
        # hexadecimal, so we strip off the first two characters from the start of string.
        self.image = "impact" + hex(self.type)[2:] + str(self.time // 4)

        self.time += 1


# Not a dataclass: x/y params intentionally overwrite Actor's x/y AFTER the
# super().__init__ call (a dataclass would assign them first and lose them).
class Ball(Actor):
    __slots__ = (
        "dir",
        "stuck_to_bat",
        "bat_offset",
        "speed",
        "speed_up_timer",
        "time_since_touched_bat",
        "time_since_damaged_brick",
        "shadow",
    )

    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        dir: Vector = DEFAULT_BALL_DIR,
        stuck_to_bat: bool = True,
        speed: int = BALL_START_SPEED,
    ) -> None:
        super().__init__("ball0", (0, 0))

        self.x = x
        self.y = y

        # Direction should always be a unit vector (a vector with a length of 1).
        # gacalc vectors are frozen, so two balls sharing one dir object cannot
        # affect each other -- changing a ball's direction rebinds self.dir to a
        # new vector rather than mutating the shared one -- so no copy is needed.
        self.dir: Vector = dir

        self.stuck_to_bat: bool = stuck_to_bat
        self.bat_offset: float = BALL_INITIAL_OFFSET

        self.speed: int = speed

        self.speed_up_timer: int = 0
        self.time_since_touched_bat: int = 0
        self.time_since_damaged_brick: int = 0

        self.shadow: Actor = Actor("balls", self.pos + Vector(16, 16))

    def update(self) -> None:
        self.time_since_damaged_brick += 1

        if self.stuck_to_bat:
            self.x = game.bat.x + self.bat_offset
            self.y = game.bat.y - BALL_RADIUS

            # Launch ball from bat if fire is pressed
            if game.controls.fire_pressed():
                self.stuck_to_bat = False
                _, self.dir = self.get_bat_bounce_vector()
        else:
            # Normal ball movement
            self.time_since_touched_bat += 1

            # Speed up every so often
            # If ball hasn't touched bat in a while, speed up more frequently
            self.speed_up_timer += 1
            if self.time_since_touched_bat > 5 * 60:
                self.speed_up_timer += 1
            interval: int = (
                BALL_SPEED_UP_INTERVAL
                if self.speed < BALL_FAST_SPEED_THRESHOLD
                else BALL_SPEED_UP_INTERVAL_FAST
            )
            interval2: float = interval * 0.75
            if self.speed_up_timer > interval or (
                self.speed_up_timer > interval2
                and self.time_since_touched_bat > interval2
            ):
                self.increment_speed()
                self.speed_up_timer = 0

            # Move one pixel at a time, speed times (rounded down to a whole number)
            for _ in range(self.speed):
                # Move and collide on X axis
                self.x += self.dir.x

                c: Collision | None = game.collide(self.x, self.y, self.dir)

                if c is not None:
                    # Invert X direction and move back to previous position, before the collision
                    self.dir = Vector(-self.dir.x, self.dir.y)
                    self.x += self.dir.x

                    if c.show_impact:
                        # Create impact animation type 12 (C in hexadecimal)
                        game.impacts.append(Impact(c.pos, 0xC))

                    if c.kind == CollisionType.BRICK:
                        self.time_since_damaged_brick = 0

                    Ball.collision_sound(c.kind)

                # Original y position before movement
                oy: float = self.y

                # Move and collide on Y axis
                self.y += self.dir.y

                c = game.collide(self.x, self.y, self.dir)

                if c is not None:
                    # Invert Y direction and move back to previous position, before the collision
                    self.dir = Vector(self.dir.x, -self.dir.y)
                    self.y += self.dir.y

                    if c.show_impact:
                        # Create impact animation type 12 (C in hexadecimal)
                        game.impacts.append(Impact(c.pos, 0xC))

                    if c.kind == CollisionType.BRICK:
                        self.time_since_damaged_brick = 0

                    Ball.collision_sound(c.kind)

                elif self.dir.y > 0:
                    # Check for collision with bat - only if we're moving down

                    # If bottom of ball was previously above/at top edge of bat, but is now below it
                    if (
                        oy + BALL_RADIUS <= BAT_TOP_EDGE
                        and self.y + BALL_RADIUS > BAT_TOP_EDGE
                    ):
                        # See if we're colliding on X axis
                        collided_x, new_dir = self.get_bat_bounce_vector()
                        if collided_x:
                            # Ball collided with bat
                            if game.bat.current_type == BatType.MAGNET:
                                self.stuck_to_bat = True
                                self.bat_offset = self.x - game.bat.x
                                self.dir = Vector(0, 0)
                            else:
                                # No magnet powerup, bounce ball in the direction we got from get_bat_bounce_vector
                                self.dir = new_dir

                            self.time_since_touched_bat = 0

                            game.impacts.append(Impact((self.x, self.y), 0xC))

                            Ball.collision_sound(CollisionType.BAT)

                            # If we became stuck to the bat, break out of the movement/speed loop
                            if self.stuck_to_bat:
                                break

                    # If bottom of ball is below top edge of bat, and top of ball is above halfway point of bat
                    elif (
                        self.y + BALL_RADIUS > BAT_TOP_EDGE
                        and self.y < BAT_TOP_EDGE + 15
                    ):
                        # If the ball hits the top of the bat, the section above will deal with it, if we get here
                        # and the bat/ball positions on the X axis overlap, that means the ball must have hit the
                        # side of the bat.

                        # See if we're colliding on X axis
                        collided_x, _ = self.get_bat_bounce_vector()
                        if collided_x:
                            # Detected ball hitting the side of the bat
                            # Send the ball off at an extreme angle, and increase speed

                            # Determine whether the ball will go left or right
                            dx: int = 1 if self.x > game.bat.x else -1

                            # Determine new direction vector, with a slightly random Y velocity
                            # The new direction vector is normalised to ensure that it is a unit vector
                            self.dir = Vector(
                                dx, uniform(-0.3, -0.1)
                            ).normalize()

                            self.time_since_touched_bat = 0

                            game.impacts.append(
                                Impact((self.x, BAT_TOP_EDGE), 0xC)
                            )

                            self.speed = min(self.speed + 4, BALL_MAX_SPEED)

                            Ball.collision_sound(CollisionType.BAT_EDGE)

        # Set shadow actor's position
        self.shadow.pos = self.pos + Vector(16, 16)

    def increment_speed(self) -> None:
        self.speed = min(self.speed + 1, BALL_MAX_SPEED)

    def get_bat_bounce_vector(self) -> tuple[bool, Vector]:
        # Determine the direction vector to use for the ball bouncing off the bat
        # For bat side collisions this is handled in update, in that case this
        # method is just used to determine whether the ball overlapped with the
        # bat on the X axis

        # dx = difference in X position between centre of bat and centre of ball
        dx: float = self.x - game.bat.x

        # dx must be within w pixels for the ball to be able to hit the bat
        w: float = (game.bat.width // 2) + BALL_RADIUS

        # Is ball is within the correct range of the bat on the X axis?
        if abs(dx) < w:
            # Return that the ball was within the correct range on the X
            # axis for there to be a collision, and the bounce vector this
            # position corresponds to
            vec: Vector = Vector(dx / w, -0.5).normalize()
            return True, vec
        else:
            # Return that the ball was not close enough on the X axis for a
            # collision to be possible. Return a vector pointing straight up
            # in case any code tries to use the bounce vector in this scenario.
            # This shouldn't happen, but better safe than sorry - returning
            # None for these values could result in a crash in such a scenario
            return False, Vector(0, -1)

    def generate_multiballs(self) -> list[Ball]:
        # Get multi ball initial positions
        # This method is called for each existing ball, returning a list of 3 new balls for each one
        # The original ball is then discarded
        balls: list[Ball] = []
        for i in range(3):
            # Create direction vector for new ball, the first ball will have the same direction as
            # its original parent ball, the others will have direction vectors rotated 120 and 240
            # degrees from that
            vec: Vector = _turn(math.radians(i * 120))(self.dir)
            if abs(vec.y) < 0.15:
                # dy could be zero if the ball is currently stuck to the bat, or could be very close
                # to zero by chance, which could lead to the ball bouncing left and right for ages
                # So if either of these happen, just generate a random upward vector
                vec = Vector(uniform(-1, 1), -1).normalize()

            balls.append(Ball(self.x, self.y, vec, False, self.speed))

        return balls

    @staticmethod
    def collision_sound(collision_type: CollisionType) -> None:
        # A static method relates to the class as a whole rather than a specific instance
        # of the class, so doesn't have self as the first parameter
        match collision_type:
            case CollisionType.BRICK | CollisionType.INDESTRUCTIBLE_BRICK:
                game.play_sound("hit_brick")
            case CollisionType.WALL:
                game.play_sound("hit_wall")
            case CollisionType.BAT:
                if game.bat.current_type == BatType.MAGNET:
                    game.play_sound("ball_stick")
                else:
                    game.play_sound("hit_fast")
            case CollisionType.BAT_EDGE:
                if game.bat.current_type == BatType.MAGNET:
                    game.play_sound("ball_stick")
                else:
                    game.play_sound("hit_veryfast")
            case _:
                raise ValueError(f"unhandled collision {collision_type!r}")


@dataclass(eq=False, slots=True)
class Bat(Actor):
    controls: Controls
    fire_timer: int = 0
    #: The values of target_type and current_type are instances the BatType enum
    #: Normally these will be the same. If the player has just picked up a powerup/powerdown
    #: then type is the type of bat we're transitioning to, once the transition animation has finished
    #: the current type is set to the type
    current_type: BatType = BatType.NORMAL
    target_type: BatType = BatType.NORMAL
    frame: int = 0
    #: Set once the bat has driven into the open portal at the right edge
    portal_animation_active: bool = False
    #: The shadow sprite, positioned from our own x/y (so created after super().__init__ has set them)
    shadow: Actor = field(init=False)

    def __post_init__(self) -> None:
        super().__init__("blank", (320, 590), anchor=("center", 15))
        self.shadow = Actor(
            "blank", self.pos + Vector(16, 16), anchor=("center", 15)
        )

    def update(self) -> None:
        # Handle animating to a new bat type
        # If we're a normal bat, we animate to a new type over 12 game frames,
        # changing animation frame every 4 game frames
        # e.g. changing from normal bat (sprite: bat00) to small bat, we go to
        # bat40 (which is the same as the normal bat), then through bat41, bat42
        # and ending at bat43, the fully shrunk bat.
        if (
            self.target_type != BatType.NORMAL
            and self.target_type == self.current_type
            and self.frame < 12
        ):
            self.frame += 1

        # If we're switching to a new type from something other than normal bat,
        # we first animate backwards to the first frame of the current type
        if self.target_type != self.current_type and self.frame > 0:
            self.frame -= 1

        # When we're at frame 0, we can update the current type to equal the
        # new type
        if self.frame == 0:
            self.current_type = self.target_type

        # Choose sprite based on current_type and frame
        self.image = f"bat{int(self.current_type)}{self.frame // 4}"

        self.fire_timer -= 1

        # Fire gun?
        if (
            self.controls.fire_down()
            and self.current_type == BatType.GUN
            and self.frame == 12
            and self.fire_timer <= 0
        ):
            self.fire_timer = FIRE_INTERVAL

            self.image += "f"  # not really visible for the 1 frame it's shown

            game.bullets.append(Bullet(self.pos - Vector(20, 0), 0))
            game.bullets.append(Bullet(self.pos + Vector(20, 0), 1))

            game.play_sound("laser")

        # Move bat based on controls, don't let it go off the edge of the screen
        new_x: float = self.x + self.controls.get_x()

        # Enforce left boundary
        new_x = max(BAT_MIN_X + (self.width // 2), new_x)

        if not game.portal_active:
            # Enforce right boundary
            new_x = min(BAT_MAX_X - (self.width // 2), new_x)

        self.x = new_x

        # Check for leaving level via portal
        if game.portal_active and new_x == BAT_MAX_X - (self.width // 2):
            self.portal_animation_active = True

        # Update shadow actor
        self.shadow.x = self.x + 16
        self.shadow.y = self.y + 16
        self.shadow.image = f"bats{int(self.current_type)}{self.frame // 4}"

    def change_type(self, type: BatType) -> None:
        self.target_type = type

    def is_portal_transition_complete(self) -> bool:
        return self.x - (self.width // 2) >= WIDTH


# Does the ball (x, y, radius) collide with the brick at the given
# grid position? Returns the point at which the collision occurred
def brick_collide(
    pos: Vector, grid_x: int, grid_y: int, r: float
) -> Vector | None:
    # Get ball extent as a square
    x0: float = float(pos.x - r)
    y0: float = float(pos.y - r)
    x1: float = float(pos.x + r)
    y1: float = float(pos.y + r)

    # Get brick's left, top, right and bottom coordinates
    xb0: int = grid_x * BRICK_WIDTH + BRICKS_X_START
    yb0: int = grid_y * BRICK_HEIGHT + BRICKS_Y_START
    xb1: int = xb0 + BRICK_WIDTH
    yb1: int = yb0 + BRICK_HEIGHT

    # Calculate brick centre position
    xbc: int = (xb0 + xb1) // 2
    ybc: int = (yb0 + yb1) // 2

    # Detecting bounce off side of brick
    # if ball right edge > brick left edge,
    #  and ball left edge < brick right edge
    #  and ball y centre > brick top edge
    #  and ball y centre < brick bottom edge
    if x1 > xb0 and x0 < xb1 and yb0 < pos.y < yb1:
        return Vector(xb0 if pos.x < xbc else xb1, pos.y)

    # Detect bounce off top or bottom of brick
    # if ball x centre > brick left edge
    #  and ball x centre < brick right edge
    #  and ball y bottom > brick y top
    #  and ball y top < brick y bottom
    if xb0 < pos.x < xb1 and y1 > yb0 and y0 < yb1:
        return Vector(pos.x, yb0 if pos.y < ybc else yb1)

    # Get closest brick corner
    # We call the Python min function with a list of positions (one for each corner of the brick)
    # The key argument is a lambda function which calculates the squared distance between pos_vector (the pos we're
    # checking) and the corner position (p). We use length_squared rather than length because it's faster and we just
    # care about which corner is closest, not what the actual distance is
    closest: Vector = min(
        [
            Vector(xb0, yb0),
            Vector(xb1, yb0),
            Vector(xb0, yb1),
            Vector(xb1, yb1),
        ],
        key=lambda p: (pos - p).magnitude_squared(),
    )

    # Check if we are actually overlapping with the nearest corner: return the corner position if so, else no
    # collision with this brick
    return closest if (pos - closest).magnitude() < r else None


@dataclass(slots=True, eq=False)
class Collision:
    """What a ball or bullet hit, from Game.collide."""

    #: where the impact animation goes
    pos: Vector
    #: whether to show that animation (walls yes; bricks draw their own)
    show_impact: bool
    kind: CollisionType


@dataclass(eq=False, slots=True)
class Game:
    #: What drives the bat; the title screen's AI plays by default
    controls: Controls = field(default_factory=AIControls)
    lives: int = 3
    score: int = field(default=0, init=False)
    # The per-level state, set up by new_level() (called from __post_init__)
    #: The bricks and their shadows, each drawn once into a CPU surface
    brick_surface: Surface = field(init=False)
    shadow_surface: Surface = field(init=False)
    num_rows: int = field(init=False)
    num_cols: int = field(init=False)
    #: Brick type per grid cell (0-13, hexadecimal in the level data), or None
    bricks: list[list[int | None]] = field(init=False)
    #: Destructible bricks left (brick 13 is indestructible)
    bricks_remaining: int = field(init=False)
    balls: list[Ball] = field(init=False)
    bat: Bat = field(init=False)
    bullets: list[Bullet] = field(init=False)
    barrels: list[Barrel] = field(init=False)
    impacts: list[Impact] = field(init=False)
    level_num: int = field(init=False)
    #: The exit portal: open, its animation frame, and the frame timer
    portal_active: bool = field(init=False)
    portal_frame: int = field(init=False)
    portal_timer: int = field(init=False)

    def __post_init__(self) -> None:
        self.new_level(0)

    def new_level(self, level_num: int) -> None:
        self.play_sound("start_game")

        # Go back to first level if we've finished last level
        if level_num >= len(LEVELS):
            level_num = 0

        # Create bitmaps for brick and shadow backgrounds
        self.brick_surface = Surface.create(WIDTH, HEIGHT, transparent=True)
        self.shadow_surface = Surface.create(WIDTH, HEIGHT, transparent=True)

        level: list[str] = get_mirrored_level(LEVELS[level_num])

        self.num_rows = len(level)
        self.num_cols = len(level[0])

        # Convert level data, a list of strings, to as 2D list of integers (or None where no brick is present)
        # The numbers in the level data are in hexadecimal (base 16), where A to F represent 10 to 15
        self.bricks = [
            [
                None if level[y][x] == " " else int(level[y][x], 16)
                for x in range(self.num_cols)
            ]
            for y in range(self.num_rows)
        ]

        # Draw bricks, and count how many there are, not counting brick ID 13 which is indestructible
        self.bricks_remaining = 0
        for y in range(self.num_rows):
            for x in range(self.num_cols):
                self.redraw_brick(x, y)
                brick: int | None = self.bricks[y][x]
                if brick is not None and brick != 13:
                    self.bricks_remaining += 1

        self.balls = [Ball()]
        self.bat = Bat(self.controls)

        self.bullets = []
        self.barrels = []
        self.impacts = []
        self.level_num = level_num
        self.portal_active = False
        self.portal_frame = 0
        self.portal_timer = 0

    def redraw_brick(self, x: int, y: int) -> None:
        screen_x: int = x * BRICK_WIDTH + BRICKS_X_START
        screen_y: int = y * BRICK_HEIGHT + BRICKS_Y_START
        brick: int | None = self.bricks[y][x]
        if brick is not None:
            # Display a brick at this position

            # Get brick image via filename, the files have names brick0 to brickd, see Impact class for a comment
            # explaining how we use hexadecimal numbers here
            # Display the brick image to the brick surface, which is an image just containing the bricks
            self.brick_surface.blit(
                images.load(f"brick{brick:x}"), (screen_x, screen_y)
            )

            # Update shadow surface
            self.shadow_surface.blit(
                images.load("bricks"),
                (screen_x + SHADOW_OFFSET, screen_y + SHADOW_OFFSET),
            )
        else:
            # Remove a brick (and its shadow) from this position)
            self.brick_surface.fill(
                (0, 0, 0, 0), (screen_x, screen_y, BRICK_WIDTH, BRICK_HEIGHT)
            )
            self.shadow_surface.fill(
                (0, 0, 0, 0),
                (
                    screen_x + SHADOW_OFFSET,
                    screen_y + SHADOW_OFFSET,
                    BRICK_WIDTH,
                    BRICK_HEIGHT,
                ),
            )

    def collide(
        self, x: float, y: float, dir: Vector, r: float = BALL_RADIUS
    ) -> Collision | None:
        # Called to check whether a ball or a bullet would collide with something if it moved in the specified direction
        # Only checks for walls and bricks, collisions with bat are handled elsewhere
        # If there's a collision with a destructible brick, the brick will take damage

        # Extract x and y of direction into separate variables
        dx, dy = dir

        if dx < 0 and x < LEFT_EDGE + r:
            return Collision(Vector(LEFT_EDGE, y), True, CollisionType.WALL)
        if dx > 0 and x > RIGHT_EDGE - r:
            return Collision(Vector(RIGHT_EDGE, y), True, CollisionType.WALL)
        if dy < 0 and y < TOP_EDGE + r:
            return Collision(Vector(x, TOP_EDGE), True, CollisionType.WALL)

        # Work out the range of brick rows and columns that the ball overlaps
        # This means we don't need to check the ball against every brick,
        # only against the bricks it could potentially be colliding with
        x0: int = max(0, math.floor((x - BRICKS_X_START - r) / BRICK_WIDTH))
        y0: int = max(0, math.floor((y - BRICKS_Y_START - r) / BRICK_HEIGHT))
        x1: int = min(
            self.num_cols - 1,
            math.floor((x - BRICKS_X_START + r) / BRICK_WIDTH),
        )
        y1: int = min(
            self.num_rows - 1,
            math.floor((y - BRICKS_Y_START + r) / BRICK_HEIGHT),
        )

        # Collide with bricks
        for yb in range(y0, y1 + 1):
            for xb in range(x0, x1 + 1):
                # Is there a brick in this position?
                brick: int | None = self.bricks[yb][xb]
                if brick is None:
                    continue
                # Check for collision with current brick
                c: Vector | None = brick_collide(Vector(x, y), xb, yb, r)
                if c is None:
                    continue

                # There was a collision
                centre_pos: tuple[int, int] = (
                    xb * BRICK_WIDTH + BRICKS_X_START + BRICK_WIDTH // 2,
                    yb * BRICK_HEIGHT + BRICKS_Y_START + BRICK_HEIGHT // 2,
                )

                collision_type: CollisionType = CollisionType.BRICK

                # Check brick type
                # Brick 12 (brickc.png) requires a hit to turn into brick 11
                # Brick 13 (brickd.png) is indestructible
                if brick >= 12:
                    # Indestructible brick
                    if brick == 13:
                        collision_type = CollisionType.INDESTRUCTIBLE_BRICK
                    self.impacts.append(Impact(centre_pos, 13))
                    if brick == 12:
                        self.bricks[yb][xb] = 11
                else:
                    self.impacts.append(Impact(centre_pos, brick))

                    if random() < POWERUP_CHANCE:
                        self.barrels.append(Barrel(centre_pos))

                    self.bricks[yb][xb] = None
                    self.redraw_brick(xb, yb)

                    self.bricks_remaining -= 1
                    if self.bricks_remaining == 0:
                        self.activate_portal()

                    self.score += 10

                return Collision(c, False, collision_type)

        return None

    def activate_portal(self) -> None:
        self.portal_active = True
        self.play_sound("portal_exit")

    def update(self) -> None:
        # Update bat and balls
        movers: list[GameObject] = [self.bat, *self.balls]
        for obj in movers:
            obj.update()

        # Remove any balls which are off the bottom of the screen
        # We achieve this by regenerating the balls list using a list comprehension, only keeping balls which are
        # still on the screen
        self.balls = [obj for obj in self.balls if obj.y < HEIGHT]

        # Lose a life if there are no balls
        if not self.balls:
            # We don't care about how many lives the player has in demo mode
            if self.lives > 0 or self.in_demo_mode():
                self.lives -= 1
                self.balls = [Ball()]
                self.bat.change_type(BatType.NORMAL)

            self.play_sound("lose_life")

        # Update impacts, barrels and bullets
        effects: list[GameObject] = [
            *self.impacts,
            *self.barrels,
            *self.bullets,
        ]
        for obj in effects:
            obj.update()

        # Remove timed-out impacts, barrels which have gone off the bottom of
        # the screen, and bullets which are no longer alive
        self.impacts = [obj for obj in self.impacts if obj.time < 16]
        self.barrels = [obj for obj in self.barrels if obj.y < HEIGHT]
        self.bullets = [obj for obj in self.bullets if obj.alive]

        # Update the portal that allows you to leave the level
        if self.portal_active:
            if self.portal_frame < 3:
                # Update portal animation
                self.portal_timer -= 1
                if self.portal_timer <= 0:
                    self.portal_timer = PORTAL_ANIMATION_SPEED
                    self.portal_frame += 1
            elif self.bat.is_portal_transition_complete():
                self.new_level(self.level_num + 1)

        # If no balls have damaged/destroyed bricks or touched the bat in the last 30 seconds, change all
        # indestructible bricks to two-hit bricks, to avoid a situation where the ball can get stuck bouncing
        # between indestructible bricks
        if self.detect_stuck_balls():
            # Go through all bricks, change indestructible bricks to two-hit bricks
            changed_any: bool = False
            for row in range(self.num_rows):
                for col in range(self.num_cols):
                    # 13 is indestructible brick, 12 is two-hit brick
                    if self.bricks[row][col] == 13:
                        self.bricks[row][col] = 12
                        self.redraw_brick(col, row)
                        changed_any = True

            # Play a sound effect, but only if there were indestructible blocks that were changed
            if changed_any:
                self.play_sound("bat_small", 1)

            # To prevent this triggering again next frame, which should have no gameplay impact but could have
            # a performance impact, we'll pretend that one of the balls has touched the bat in the last 30 seconds
            if self.balls:
                self.balls[0].time_since_touched_bat = 0

    def detect_stuck_balls(self) -> bool:
        # Detect whether all balls are stuck bouncing between indestructible bricks: no ball has damaged a brick
        # or touched the bat in the last 30 seconds. (Having no balls in play doesn't count as all balls being stuck)
        return bool(self.balls) and all(
            ball.time_since_damaged_brick >= 30 * 60
            and ball.time_since_touched_bat >= 30 * 60
            for ball in self.balls
        )

    def draw(self) -> None:
        blit(f"arena{self.level_num % len(LEVELS)}", 0, 0)

        # Draw exit portal
        blit(f"portal_exit{self.portal_frame}", WIDTH - 70 - 20, HEIGHT - 70)

        # Draw enemy doors - currently unused, but animations are present for the doors opening and closing,
        # and for enemies - try adding enemies to the game and making use of these animations!
        blit("portal_meanie00", 110, 40)
        blit("portal_meanie10", 440, 40)

        # This prevents drawing onto the edges of the screen, meaning that the
        # shadows don't overlap with the darker part of the right hand wall
        renderer.set_clip((20, 42, 600, 598))

        # Draw brick shadows
        renderer.draw_image(self.shadow_surface, (0.0, 0.0))

        # Draw shadows for powerup barrels, balls and bat
        shadowed: list[Barrel | Ball | Bat] = [
            *self.barrels,
            *self.balls,
            self.bat,
        ]
        for obj in shadowed:
            obj.shadow.draw()

        # Draw bricks
        renderer.draw_image(self.brick_surface, (0.0, 0.0))

        # Draw balls, bat, barrels and bullets
        sprites: list[GameObject] = [
            *self.balls,
            self.bat,
            *self.barrels,
            *self.bullets,
        ]
        for obj in sprites:
            obj.draw()

        # Cancel screen clipping mode set earlier
        renderer.set_clip(None)

        # Draw impact animations
        for impact in self.impacts:
            impact.draw()

        # Only draw score and lives in normal mode, not in AI/demo mode
        if not self.in_demo_mode():
            self.draw_score()
            self.draw_lives()

    def draw_score(self) -> None:
        # Draw each digit of the score, from left to right
        for i, digit in enumerate(str(self.score)):
            blit(f"digit{digit}", 15 + 55 * i, 50)

    def draw_lives(self) -> None:
        for i in range(self.lives):
            blit("life", 50 * i, HEIGHT - 20)

    def play_sound(self, name: str, count: int = 1) -> None:
        # We don't play any in-game sound effects if player is an AI player - as this means we're on the menu
        if not self.in_demo_mode():
            try:
                # Sounds with several varieties are named "name0", "name1", ...
                sounds.load(f"{name}{randint(0, count - 1)}").play()
            except Exception as e:
                # If no sound file of that name was found, print the error, which includes the filename.
                # Also occurs if sound fails to play for another reason (e.g. if this machine has no sound hardware)
                print(e)

    def change_all_ball_speeds(self, change: int) -> None:
        for b in self.balls:
            b.speed = min(max(b.speed + change, BALL_MIN_SPEED), BALL_MAX_SPEED)

    def in_demo_mode(self) -> bool:
        return isinstance(self.controls, AIControls)


def setup_joystick_controls() -> None:
    # We call this on startup, and keep calling it if no controller is present,
    # so a controller can be connected while the game is open
    global joystick_controls
    joystick_controls = (
        JoystickControls(Joystick(0)) if joystick_count() > 0 else None
    )


def update_controls() -> None:
    keyboard_controls.update()
    # Allow a controller to be connected while the game is open
    if joystick_controls is None:
        setup_joystick_controls()
    if joystick_controls is not None:
        joystick_controls.update()


class State(Enum):
    TITLE = 1
    PLAY = 2
    GAME_OVER = 3


def update() -> None:
    global state, game, total_frames

    total_frames += 1

    update_controls()

    match state:
        case State.TITLE:
            ai_controls.update()
            game.update()

            # Check for start game
            for controls in (keyboard_controls, joystick_controls):
                # Check for fire button being pressed on each controls object
                # joystick_controls will be None if there is no controller, so must check for that
                if controls is not None and controls.fire_pressed():
                    game = Game(controls)
                    state = State.PLAY
                    music.stop()
                    break

        case State.PLAY:
            if game.lives > 0:
                game.update()
            else:
                game.play_sound("game_over")
                state = State.GAME_OVER

        case State.GAME_OVER:
            for controls in (keyboard_controls, joystick_controls):
                if controls is not None and controls.fire_pressed():
                    # Return to title screen, which includes a game being played by AI in the background
                    game = Game(ai_controls)
                    state = State.TITLE
                    music.play("title_theme")

        case _:
            raise ValueError(f"unhandled game state {state!r}")


def draw() -> None:
    game.draw()

    match state:
        case State.TITLE:
            blit("title", 0, 0)
            blit("startgame", 20, 80)
            blit(f"start{(total_frames // 4) % 13}", WIDTH // 2 - 250 // 2, 530)

        case State.PLAY:
            pass  # nothing drawn over the game while playing

        case State.GAME_OVER:
            blit(
                f"gameover{(total_frames // 4) % 15}",
                WIDTH // 2 - 450 // 2,
                450,
            )

        case _:
            raise ValueError(f"unhandled game state {state!r}")


# Start the music (with no sound device the game simply plays silently)
music.play("title_theme")
music.set_volume(0.3)

# Set up controls
joystick_controls: JoystickControls | None
keyboard_controls: KeyboardControls = KeyboardControls()
ai_controls: AIControls = AIControls()
setup_joystick_controls()

# Set up state and Game object
state: State = State.TITLE
game: Game = Game(ai_controls)

total_frames: int = 0

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

# Fixed 60 Hz timestep -- kinetix's update() takes no dt. PGZERO_MAX_FRAMES=N
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
