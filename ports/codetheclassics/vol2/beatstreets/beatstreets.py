# Code the Classics port: beatstreets, with its rendering engine inlined.
#
# Game code derived from Raspberry Pi Press's "Code the Classics" (vol 2):
#   Copyright (c) 2024 Eben Upton <eben@raspberrypi.com>
# Inlined engine (audio, images, renderer, keyboard, loop):
#   Copyright (c) 2026 William Emerison Six
# SPDX-License-Identifier: BSD-2-Clause
# Full license text: ports/codetheclassics/LICENSE.
"""beatstreets -- a side-scrolling beat-em-up of combos, weapons and portals,
from Code the Classics vol. 2, on GLFW + OpenGL 3.3 core.

One self-contained file, read top to bottom like the course's demos: first
the small engine this game needs (a software audio mixer, an image loader and
a CPU-drawn surface for the intro fade, a textured-quad renderer that can
draw part of an image and the debug outlines, the anchored Actor sprite with
rect collision, keyboard and gamepad state), then the game -- its fighters'
attacks come from attacks.json -- then the loop the game itself owns.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Generator, Iterator, Sequence
from dataclasses import InitVar, dataclass, field
from enum import Enum
from random import choice, randint
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
TITLE: str = "Beat Streets"

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

    def filled_rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        color: tuple[int, int, int],
    ) -> None: ...

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        color: tuple[int, int, int],
    ) -> None: ...

    def draw_image_region(
        self, image: Image, topleft: tuple[float, float], region: IntRect
    ) -> None: ...

    def circle(
        self, pos: PointLike, radius: float, color: tuple[int, int, int]
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
        rect: tuple[int, int, int, int] | None = None,
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

    def circle(
        self, pos: PointLike, radius: float, color: tuple[int, int, int]
    ) -> None:
        """Draw a one-pixel circle outline (the debug overlays)."""
        cx, cy = pos
        n: int = 48
        verts: NDArray[np.float32] = np.array(
            [
                c
                for i in range(n)
                for c in (
                    cx + radius * np.cos(2.0 * np.pi * i / n),
                    cy + radius * np.sin(2.0 * np.pi * i / n),
                )
            ],
            dtype=np.float32,
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
        GL.glDrawArrays(GL.GL_LINE_LOOP, 0, n)

    def draw_image_region(
        self, image: Image, topleft: tuple[float, float], region: IntRect
    ) -> None:
        """Draw only ``region`` (a pixel rect within ``image``, e.g. one tile of
        a tileset) with its top-left at ``topleft``."""
        tx, ty = topleft
        model: NDArray[np.float32] = MODEL.fill(
            tx, ty, region.width, region.height
        )
        GL.glBindVertexArray(self.quad.vao)
        GL.glUniformMatrix4fv(self.uniforms.model, 1, GL.GL_TRUE, model)
        GL.glUniform2f(
            self.uniforms.tex_off,
            region.left / image.width,
            region.top / image.height,
        )
        GL.glUniform2f(
            self.uniforms.tex_scale,
            region.width / image.width,
            region.height / image.height,
        )
        GL.glUniform1i(self.uniforms.use_tex, 1)
        GL.glUniform4f(self.uniforms.tint, 1.0, 1.0, 1.0, 1.0)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, image.gl_texture())
        GL.glUniform1i(self.uniforms.tex, 0)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)

    def filled_rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        color: tuple[int, int, int],
    ) -> None:
        """Draw a filled rectangle at ``(x, y)`` of size ``(w, h)``."""
        model: NDArray[np.float32] = MODEL.fill(x, y, w, h)
        GL.glBindVertexArray(self.quad.vao)
        GL.glUniformMatrix4fv(self.uniforms.model, 1, GL.GL_TRUE, model)
        GL.glUniform1i(self.uniforms.use_tex, 0)
        r, g, b = color
        GL.glUniform4f(self.uniforms.tint, r / 255.0, g / 255.0, b / 255.0, 1.0)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        color: tuple[int, int, int],
    ) -> None:
        """Draw the one-pixel outline of a rectangle (the debug overlays)."""
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


# ===== engine: system text =====
#
# Text rasterized with Pillow to an RGBA bitmap, wrapped as an Image (lazy GL
# texture), cached by (text, size, colour) and drawn at a top-left pixel
# position -- for the debug overlays only; the game's own text is its bitmap
# font (draw_text, in the game code).

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


def draw_system_text(
    text: str,
    x: float,
    y: float,
    color: tuple[int, int, int] = (255, 255, 255),
    size: int = 24,
) -> None:
    """Draw ``text`` in the system font with its top-left at ``(x, y)``."""
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


class RectLike(Protocol):
    """Anything with four edges: the engine's ``Rect``, a game's ``IntRect``, or
    an ``Actor`` (whose edge properties read its rect)."""

    @property
    def left(self) -> float: ...

    @property
    def top(self) -> float: ...

    @property
    def right(self) -> float: ...

    @property
    def bottom(self) -> float: ...


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

    def colliderect(self, o: RectLike) -> bool:
        """Return whether this rect and ``o`` overlap (touching edges don't)."""
        return (
            self.left < o.right
            and self.right > o.left
            and self.top < o.bottom
            and self.bottom > o.top
        )


@dataclass(slots=True)
class IntRect:
    """pygame's integer rectangle: whole-pixel edges, and plain mutable fields
    (a level builder grows them in place)."""

    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    def colliderect(self, o: RectLike) -> bool:
        """Return whether this rect and ``o`` overlap (touching edges don't)."""
        return (
            self.left < o.right
            and self.right > o.left
            and self.top < o.bottom
            and self.bottom > o.top
        )


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
    def left(self) -> float:
        return self._rect.left

    @property
    def right(self) -> float:
        return self._rect.right

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
# each frame -- they are the only keys beatstreets reads.

_NAME_TO_KEY: dict[str, int] = {
    "left": glfw.KEY_LEFT,
    "right": glfw.KEY_RIGHT,
    "up": glfw.KEY_UP,
    "down": glfw.KEY_DOWN,
    "space": glfw.KEY_SPACE,
    "z": glfw.KEY_Z,
    "lctrl": glfw.KEY_LEFT_CONTROL,
    "x": glfw.KEY_X,
    "lalt": glfw.KEY_LEFT_ALT,
    "c": glfw.KEY_C,
    "lshift": glfw.KEY_LEFT_SHIFT,
    "a": glfw.KEY_A,
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

HEALTH_STAMINA_BAR_WIDTH: int = 235
HEALTH_STAMINA_BAR_HEIGHT: int = 26

INTRO_ENABLED: bool = True

FLYING_KICK_VEL_X: int = 3
FLYING_KICK_VEL_Y: int = -8

JUMP_GRAVITY: float = 0.4
THROWN_GRAVITY: float = 0.025
WEAPON_GRAVITY: float = 0.5

BARREL_THROW_VEL_X: int = 4
BARREL_THROW_VEL_Y: int = 0

# For when player is thrown by boss
PLAYER_THROW_VEL_X: int = 5
PLAYER_THROW_VEL_Y: float = 0.5

# By default, the effect of an attack on the opponent's stamina is damage * 100
# Some attacks have an additional stamina damage multiplier
BASE_STAMINA_DAMAGE_MULTIPLIER: int = 100

# If stamina goes below zero, player can be knocked over more easily and minimum interval between attacks
# is longer
MIN_STAMINA: int = -100

# Defaults for Fighter/Enemy constructor params, as named module-level constants
# rather than inline ``Vector(...)`` defaults (which ruff B008 flags as a call in
# a default argument). gacalc vectors are frozen, so sharing one is safe -- storing
# the argument directly, with no defensive copy, cannot alias-mutate anything.
DEFAULT_HALF_HIT_AREA: Vector = Vector(25, 20)
DEFAULT_ENEMY_SPEED: Vector = Vector(1, 1)

DEBUG_LOGGING_ENABLED: bool = False
DEBUG_SHOW_SCROLL_POS: bool = False
DEBUG_SHOW_BOUNDARY: bool = False
DEBUG_SHOW_ATTACKS: bool = False
DEBUG_SHOW_TARGET_POS: bool = False
DEBUG_SHOW_ANCHOR_POINTS: bool = False
DEBUG_SHOW_HIT_AREA_WIDTH: bool = False
DEBUG_SHOW_LOGS: bool = False
DEBUG_SHOW_HEALTH_AND_STAMINA: bool = False
DEBUG_PROFILING: bool = False

# These symbols substitute for the controller button images when displaying text.
# The symbols representing these images must be ones that aren't actually used themselves, e.g. we don't use the
# percent sign in text
SPECIAL_FONT_SYMBOLS: dict[str, str] = {"xb_a": "%"}

# Create a version of SPECIAL_FONT_SYMBOLS where the keys and values are swapped
SPECIAL_FONT_SYMBOLS_INVERSE: dict[str, str] = {
    v: k for k, v in SPECIAL_FONT_SYMBOLS.items()
}

#: Overlays the debug flags queue during update, drawn at the end of the frame
debug_drawcalls: list[Callable[[], None]] = []


def xy(v: Vector) -> tuple[float, float]:
    # A screen-space vector as the pixel pair the renderer takes
    return (float(v.x), float(v.y))


# Class for measuring how long code takes to run
@dataclass(slots=True)
class Profiler:
    name: str = ""
    #: When this profiler was created
    start_time: float = field(default_factory=time.perf_counter)

    def get_ms(self) -> float:
        return (time.perf_counter() - self.start_time) * 1000

    def __str__(self) -> str:
        return f"{self.name}: {self.get_ms()}ms"


MIN_WALK_Y: int = 310

ENEMY_APPROACH_PLAYER_DISTANCE: int = 85
ENEMY_APPROACH_PLAYER_DISTANCE_SCOOTERBOY: int = 140
ENEMY_APPROACH_PLAYER_DISTANCE_BARREL: int = 180

ANCHOR_CENTRE: Anchor = ("center", "center")
ANCHOR_CENTRE_BOTTOM: Anchor = ("center", "bottom")

BACKGROUND_TILE_SPACING: int = 290

# 1st row of TILE_DEMO+_3.png
BACKGROUND_TILES: list[str] = [
    "wall_end1",
    "wall_fill1",
    "wall_fill5",
    "wall_fill2",
    "alley1",
    "wall_end6",
    "wall_fill7",
    "wall_fill5",
    "alley2",
    "wall_end3",
    "wall_fill3",
    "wall_fill4",
    "wall_fill8",
    "alley5",
    "wall_end2",
    "alley3",
    "wall_end4",
    "wall_fill6",
    # row 2
    "alley6",
    "wall_end8",
    "wall_fill4",
    "alley7",
    "wall_end5",
    "alley8",
    "set_pc_a1",
    "set_pc_a2",
    "alley9",
    "set_pc_b1",
    "set_pc_b2",
    "set_pc_b3",
    "wall_end3",
    "wall_fill3",
    "alley8",
    "set_pc_a1",
    "set_pc_a2",
    "wall_fill2",
    # 3
    "con_start2",
    "con_end1a",
    "con_end2",
    "con_start2",
    "con_end1",
    "con_fill1",
    "con_end2a",
    "con_start2",
    "con_end1a",
    "con_fill1a",
    "con_end2",
    "set_pc_c1",
    "set_pc_c2",
    "set_pc_c3",
    "con_start1",
    "con_end1",
    "con_fill1",
    "con_fill2",
    "con_fill1a",
    "con_fill2a",
    # 4
    "wall_end1",
    "alley10",
    "steps_end1a",
    "steps_fill1a",
    "steps_fill2a",
    "steps_end2a",
    "flats_alley1",
    "steps_end1",
    "steps_end2",
    "flats_alley1",
    "flats_end1a",
    "steps_fill2",
    "steps_fill1",
    "flats_end2a",
    "flats_alley2",
    "set_pc_d1",
    "set_pc_d2",
    "set_pc_d3",
    "steps_end2a",
]

# A black image whose alpha (transparency) we vary, to fade in from the intro text
fullscreen_black_bmp: Surface = Surface.create(WIDTH, HEIGHT, transparent=False)


# Utility functions


def clamp(value: float, min_val: float, max_val: float) -> float:
    # Clamp a value within a given range
    return min(max(value, min_val), max_val)


def remap(
    old_val: float,
    old_min: float,
    old_max: float,
    new_min: float,
    new_max: float,
) -> float:
    # Remap a number from one range to a different range
    # e.g. remapping 5 from source range of 0 to 10, to destination range of 0 to 100, becomes 50
    return (new_max - new_min) * (old_val - old_min) / (
        old_max - old_min
    ) + new_min


def remap_clamp(
    old_val: float,
    old_min: float,
    old_max: float,
    new_min: float,
    new_max: float,
) -> float:
    # Like remap, but constrains the resulting value so that it can't be outside the new range
    # These first two lines are in case new_min and new_max are inverted
    lower_limit: float = min(new_min, new_max)
    upper_limit: float = max(new_min, new_max)
    return min(
        upper_limit,
        max(lower_limit, remap(old_val, old_min, old_max, new_min, new_max)),
    )


def sign(x: float) -> int:
    # Returns 1, 0 or -1 depending on whether number is positive, zero or negative
    return 0 if x == 0 else -1 if x < 0 else 1


def move_towards(n: float, target: float, speed: float) -> tuple[float, int]:
    # Returns new value, and the direction of travel (-1, 0 or 1)
    if n < target:
        return min(n + speed, target), 1
    elif n > target:
        return max(n - speed, target), -1
    else:
        return n, 0


class ScrollObject(Protocol):
    """What Game.update and Game.draw need of everything in the level: a
    world position (for draw order), a per-frame update and a draw at the
    scroll offset. Every ScrollHeightActor subclass below satisfies it
    structurally (deliberately not by subclassing the protocol -- an explicit
    subclass inherits the stub members, so a missing method would go
    unreported).
    """

    @property
    def vpos(self) -> Vector: ...

    def update(self) -> None: ...

    def draw_at(self, offset: Vector) -> None: ...

    def get_draw_order_offset(self) -> int: ...


# ABC = abstract base class - a class which is only there to serve as a base class, not to be instantiated directly
class Controls(ABC):
    NUM_BUTTONS: ClassVar[int] = 4

    __slots__ = ("button_previously_down", "is_button_pressed")

    def __init__(self) -> None:
        self.button_previously_down: list[bool] = [False] * Controls.NUM_BUTTONS
        self.is_button_pressed: list[bool] = [False] * Controls.NUM_BUTTONS

    def update(self) -> None:
        # Call each frame to update button status
        for button in range(Controls.NUM_BUTTONS):
            button_down: bool = self.button_down(button)
            self.is_button_pressed[button] = (
                button_down and not self.button_previously_down[button]
            )
            self.button_previously_down[button] = button_down

    @abstractmethod
    def get_x(self) -> int: ...

    @abstractmethod
    def get_y(self) -> int: ...

    @abstractmethod
    def button_down(self, button: int) -> bool: ...

    def button_pressed(self, button: int) -> bool:
        return self.is_button_pressed[button]


class KeyboardControls(Controls):
    __slots__ = ()

    @override
    def get_x(self) -> int:
        return -1 if keyboard.left else 1 if keyboard.right else 0

    @override
    def get_y(self) -> int:
        return -1 if keyboard.up else 1 if keyboard.down else 0

    @override
    def button_down(self, button: int) -> bool:
        match button:
            case 0:
                return keyboard.space or keyboard.z or keyboard.lctrl  # punch
            case 1:
                return keyboard.x or keyboard.lalt  # kick
            case 2:
                return keyboard.c or keyboard.lshift  # elbow
            case 3:
                return keyboard.a  # flying kick
            case _:
                return False


class JoystickControls(Controls):
    __slots__ = ("joystick",)

    def __init__(self, joystick: Joystick) -> None:
        super().__init__()
        self.joystick: Joystick = joystick

    def get_axis(self, axis_num: int) -> int:
        if (
            self.joystick.get_numhats() > 0
            and self.joystick.get_hat(0)[axis_num] != 0
        ):
            # For some reason, dpad up/down are inverted when getting inputs from
            # an Xbox controller, so need to negate the value if axis_num is 1
            return self.joystick.get_hat(0)[axis_num] * (
                -1 if axis_num == 1 else 1
            )

        # Analogue input, with a dead-zone, as digital movement
        axis_value: float = self.joystick.get_axis(axis_num)
        return 0 if abs(axis_value) < 0.6 else 1 if axis_value > 0 else -1

    @override
    def get_x(self) -> int:
        return self.get_axis(0)

    @override
    def get_y(self) -> int:
        return self.get_axis(1)

    @override
    def button_down(self, button: int) -> bool:
        # Before checking button, check to make sure that the controller actually has enough buttons
        # There are some weird devices out there which could cause a crash if this check were not present
        if self.joystick.get_numbuttons() <= button:
            print("Warning: main controller does not have enough buttons!")
            return False
        return self.joystick.get_button(button) != 0


#: A sound to play: its name and the number of varieties to choose from
type SoundSpec = tuple[str, int]


# (eq=False on these dataclasses keeps identity comparison/hashing -- the
# generated __eq__ would compare fields and set __hash__ to None; slots=True
# fixes each object's attribute set to its declared fields. Field/parameter
# names must stay exactly as they are: instances are constructed via
# Attack(**value) from attacks.json -- where the flags arrive as the string
# "True", which is truthy, so the game only ever tests them.)
@dataclass(eq=False, slots=True)
class Attack:
    #: The animation to play (attack sprites are named <fighter>_<sprite>_...); the
    #: barrel and scooter "attacks" only ever hit, so have none
    sprite: str = ""
    #: Damage to the opponent's health
    strength: int = 0
    #: Frames for which animation plays, this allows us to stay on the last frame longer than previous frames
    anim_time: int = 0
    #: Frames for which each animation frame plays
    frame_time: int = 5
    #: Number of frames in animation
    frames: int = 0
    #: frames on which an opponent can be hit by this attack
    hit_frames: Sequence[int] = ()
    #: Can't attack for this many frames after attack animation finishes
    recovery_time: int = 0
    #: Opponent must be closer than this for attack to hit
    reach: int = 80
    #: Is this an attack where we throw something, such as a barrel or the player?
    throw: bool = False
    #: Is this the attack where the boss grabs the player and throws him?
    grab: bool = False
    #: Button number -> the attack that continues the combo if pressed soon after
    combo_next: dict[int, str] | None = None
    #: The json key is 'flyingkick' but the attribute the game reads is
    #: 'flying_kick' -- an InitVar keeps the constructor parameter name while
    #: __post_init__ stores it under the game-facing name.
    flyingkick: InitVar[bool] = False
    flying_kick: bool = field(init=False)
    stamina_cost: int = 10
    rear_attack: bool = False
    #: Does this attack do additional damage to the opponent's stamina?
    stamina_damage_multiplier: float = 1
    stun_time_multiplier: float = 1
    initial_sound: SoundSpec | None = None
    hit_sound: SoundSpec | None = None

    def __post_init__(self, flyingkick: bool) -> None:
        self.flying_kick = flyingkick

        # Some data for attacks loaded from attacks.json must be modified to be in the format the game expects
        # For example, the keys in combo_next should be integers, but are strings in the json file as JSON only allows
        # string keys, and the sound specs are JSON lists
        if self.combo_next is not None:
            self.combo_next = {
                int(key): value for (key, value) in self.combo_next.items()
            }
        if self.initial_sound is not None:
            self.initial_sound = (self.initial_sound[0], self.initial_sound[1])
        if self.hit_sound is not None:
            self.hit_sound = (self.hit_sound[0], self.hit_sound[1])


# Load attack data from file (resolve relative to this script so the game can be
# launched from any working directory, not just its own folder)
with open(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "attacks.json")
) as attacks_file:
    # Turn values in the dictionary into constructor parameters of the Attack class
    ATTACKS: dict[str, Attack] = {
        key: Attack(**value) for key, value in json.load(attacks_file).items()
    }


# The ScrollHeightActor class extends Actor by providing the attribute 'vpos', which stores the object's current
# position in the level. All code should change or read the position via vpos, as opposed to Actor's x/y or pos
# attributes. When the object is drawn, we set self.pos (equivalent to setting both self.x and self.y) based on vpos,
# but taking scrolling into account.
# It also includes the attribute height_above_ground which allows an actor to be considered to be in the air. This
# should be taken into account when determining draw order, as a fighter who is jumping will be further up the screen
# on the Y axis than if they were on the ground, but it's their Y position in relation to the ground which should
# determine whether they're drawn behind or in front of other actors.
class ScrollHeightActor(Actor):
    __slots__ = ("vpos", "height_above_ground", "shadow_actor")

    def __init__(
        self,
        img: str,
        pos: PointLike,
        anchor: Anchor | None = None,
        separate_shadow: bool = False,
    ) -> None:
        super().__init__(img, pos, anchor=anchor)
        self.vpos: Vector = Vector(*pos)
        self.height_above_ground: float = 0
        # Most sprites have the shadow as part of the sprite, but for the player it is separate
        self.shadow_actor: Actor | None = (
            Actor("blank", pos, anchor=anchor) if separate_shadow else None
        )

    def draw_at(self, offset: Vector) -> None:
        # Draw with the supplied scroll offset. Not an override of Actor.draw: it takes the offset, so it has its
        # own name.
        # Camera as an INVERSE transformation (mvp course, ch16/ch19): the scroll
        # offset places the camera in world space, so mapping a world position to
        # the screen is the INVERSE of that placement. world_to_screen(v) is
        # exactly `v - offset` (byte-identical). The beat-em-up height flatten is
        # NOT part of the camera, so it stays a separate subtraction on the y.
        world_to_screen: InvertibleFunction[Vector] = inverse(
            translate(b=offset)
        )
        # Draw shadow first, if we are using a separate shadow sprite
        if self.shadow_actor is not None:
            self.shadow_actor.pos = world_to_screen(self.vpos)
            self.shadow_actor.image = (
                "blank" if self.image == "blank" else f"{self.image}_shadow"
            )
            self.shadow_actor.draw()

        # Set Actor's screen pos. The height flatten is a world-space shift on y,
        # subtracted AFTER the camera map (kept out of world_to_screen so the
        # shadow above stays on the ground); as a Vector it assigns straight to
        # pos, and `x - 0` leaves x byte-identical.
        self.pos = world_to_screen(self.vpos) - Vector(
            0, self.height_above_ground
        )
        self.draw()
        if DEBUG_SHOW_ANCHOR_POINTS:
            renderer.circle(self.pos, 5, (255, 255, 255))

    def on_screen(self) -> bool:
        # Use self.x rather than self.vpos.x to get actual screen position rather than world position
        # Note that self.x only updates when the actor is drawn, so if vpos.x is updated during update causing the
        # actor to move off-screen, the value returned by this method will not update until the following frame
        return 0 < self.x < WIDTH

    def get_draw_order_offset(self) -> int:
        # See Player and Stick classes for explanation
        return 0


# Inherits from both ScrollHeightActor and ABC (abstract base class). A keyword-only dataclass: the
# subclasses' super().__init__ calls name every argument, and the fields below are the whole of a
# fighter's state
@dataclass(eq=False, slots=True, kw_only=True)
class Fighter(ScrollHeightActor, ABC):
    WEAPON_HOLD_HEIGHT: ClassVar[int] = 100

    class FallingState(Enum):
        STANDING = 0
        FALLING = 1
        GETTING_UP = 2
        GRABBED = 3
        THROWN = 4

    #: named spawn_pos/spawn_anchor, NOT pos/anchor: those are Actor properties,
    #: and a dataclass would treat the property object as the field's default
    spawn_pos: InitVar[PointLike]
    spawn_anchor: InitVar[Anchor]
    separate_shadow: InitVar[bool] = False
    #: x and y speed
    speed: Vector
    #: e.g. "hero" or "enemy"
    sprite: str
    health: int
    anim_update_rate: int = 8
    stamina: float = 500
    #: Determines whether an opponent's attack will hit us, based on the distance between us and the attack's reach
    #: Larger number for the portal, because the portal is physically bigger
    half_hit_area: Vector = field(default_factory=lambda: DEFAULT_HALF_HIT_AREA)
    lives: int = 1
    #: Used for enemies with multiple colour variants - appended to sprite name
    colour_variant: int | None = None
    #: Sound for me being hit (only used by portal)
    hit_sound: str | None = None
    facing_x: int = field(default=1, init=False)
    #: Updates each game frame, then is translated into an animation frame number depending on the animation
    #: being played
    frame: int = field(default=0, init=False)
    #: Last attack is current attack if attack_timer is above zero
    last_attack: Attack | None = field(default=None, init=False)
    #: Above zero = currently attacking, zero or below = time since last attack
    attack_timer: int = field(default=0, init=False)
    #: Are we knocked down or in the process of being knocked down?
    falling_state: Fighter.FallingState = field(
        default=FallingState.STANDING, init=False
    )
    #: Are we currently walking? Used to determine whether to use standing or walking animation
    walking: bool = field(default=False, init=False)
    #: Velocity X used when falling or being pushed backwards or for flying kick, velocity Y for jumping
    vel: Vector = field(default_factory=lambda: Vector(0, 0), init=False)
    #: The name of the weapon being picked up, while that animation plays
    pickup_animation: str | None = field(default=None, init=False)
    #: if above 0, we've just been hit and are doing the animation where we recoil from that
    hit_timer: float = field(default=0, init=False)
    hit_frame: int = field(default=0, init=False)
    max_stamina: float = field(init=False)
    start_health: int = field(init=False)
    weapon: Weapon | None = field(default=None, init=False)
    #: Used for animation where Scooterboy enemy is knocked off his scooter
    just_knocked_off_scooter: bool = field(default=False, init=False)
    use_die_animation: bool = field(default=False, init=False)
    logs: list[str] = field(default_factory=list, init=False)

    def __post_init__(
        self, spawn_pos: PointLike, spawn_anchor: Anchor, separate_shadow: bool
    ) -> None:
        super().__init__(
            "blank", spawn_pos, spawn_anchor, separate_shadow=separate_shadow
        )
        self.max_stamina = self.stamina
        self.start_health = self.health

    def log(self, message: str) -> None:
        if DEBUG_LOGGING_ENABLED:
            line: str = f"{game.timer} {message} {self.vpos}"
            print(self, line)
            self.logs.append(line)

    def update(self) -> None:
        self.attack_timer -= 1

        # Apply gravity and velocity if in air
        if self.height_above_ground > 0 or self.vel.y != 0:
            self.vpos = Vector(self.vpos.x + self.vel.x, self.vpos.y)
            self.vel = Vector(
                self.vel.x,
                self.vel.y
                + (
                    THROWN_GRAVITY
                    if self.falling_state == Fighter.FallingState.THROWN
                    else JUMP_GRAVITY
                ),
            )
            self.height_above_ground -= self.vel.y
            self.apply_movement_boundaries(float(self.vel.x), 0)
            if self.height_above_ground < 0:
                self.height_above_ground = 0
                self.vel = Vector(0, 0)

                # Don't do the been hit animation after landing (from flying kick or from being thrown)
                self.hit_timer = 0

        # Update logic and animation based on current situation - falling, getting up, hit, pickup animation, or normal
        # walking/standing/attacking

        # Check for falling and dying
        # Portals don't fall when they die, so the logic for them dying is within their class
        if self.falling_state == Fighter.FallingState.FALLING:
            # Get pushed backwards
            self.vpos = Vector(self.vpos.x + self.vel.x, self.vpos.y)
            new_vel_x, _ = move_towards(float(self.vel.x), 0, 0.5)
            self.vel = Vector(new_vel_x, self.vel.y)

            self.apply_movement_boundaries(float(self.vel.x), 0)

            self.frame += 1

            if self.frame > 120:
                # If we're not yet out of health, get up and reset stamina
                if self.health > 0:
                    self.falling_state = Fighter.FallingState.GETTING_UP
                    self.frame = 0
                    self.stamina = self.max_stamina
                else:
                    # If we're out of health, flash on and off for a short while, then lose a life
                    if self.frame > 240:
                        self.lives -= 1

                        # If we still have lives left, get up
                        if self.lives > 0:
                            self.health = self.start_health
                            self.falling_state = Fighter.FallingState.GETTING_UP
                            self.frame = 0
                            self.stamina = self.max_stamina
                            self.use_die_animation = False
                        else:
                            self.died()

        elif self.falling_state == Fighter.FallingState.GETTING_UP:
            self.frame += 1
            # Move forward slightly as we get up
            self.vpos = Vector(self.vpos.x + 0.1 * self.facing_x, self.vpos.y)
            if self.frame > 20:
                self.falling_state = Fighter.FallingState.STANDING
                self.frame = 0

        elif self.falling_state == Fighter.FallingState.THROWN:
            self.frame += 1
            if self.height_above_ground <= 0:
                self.falling_state = Fighter.FallingState.FALLING
                self.frame = 80

        elif self.hit_timer > 0:
            # Playing the 'hit' animation, briefly stunned
            self.hit_timer -= 1

        elif self.pickup_animation is not None:
            # Doing animation for picking up a weapon
            self.frame += 1
            if self.frame > 30:
                self.pickup_animation = None

        elif self.override_walking():
            # If this is the case, we're in some kind of special state, managed by a subclass, which means we shouldn't
            # do the usual walking/attacking behaviour below - e.g. Scooterboy riding scooter
            pass

        elif self.falling_state == Fighter.FallingState.STANDING:
            # Standing, walking or attacking

            # Recover stamina over time
            if self.stamina < self.max_stamina:
                self.stamina += 1

            # Update position of held weapon
            # The weapon actor is invisible while being held as we switch to a different fighter sprite using the
            # weapon, but we update weapon pos so that if we drop the weapon, it reappears as a distinct sprite in the
            # correct location
            if self.weapon is not None:
                self.weapon.vpos = self.vpos + Vector(self.facing_x * 20, 0)

            # Are we ready to attack or pick up/drop a weapon?
            # If we're out of stamina, recovery time will be longer
            last_attack_recovery_time: int = (
                0
                if self.last_attack is None
                else self.last_attack.recovery_time
            )
            if self.stamina <= 0:
                last_attack_recovery_time *= 3
            if self.attack_timer <= -last_attack_recovery_time:
                # Not currently attacking, do we want to start attacking?

                # Before deciding if we want to attack - do we instead want to pick up or drop a weapon?
                if self.weapon is None:
                    # Find weapons within reach
                    nearby_weapons: list[Weapon] = [
                        weapon
                        for weapon in game.weapons
                        if (weapon.vpos - self.vpos).magnitude() < 50
                    ]
                    if nearby_weapons and self.determine_pick_up_weapon():
                        # Sort nearby weapons by distance. magnitude_squared is used to order them instead of
                        # magnitude as it is more efficient
                        nearby_weapons.sort(
                            key=lambda weapon: (
                                weapon.vpos - self.vpos
                            ).magnitude_squared()
                        )
                        for weapon in nearby_weapons:
                            if weapon.can_be_picked_up():
                                self.pickup_animation = weapon.name
                                self.frame = 0
                                self.weapon = weapon
                                weapon.pick_up(Fighter.WEAPON_HOLD_HEIGHT)
                                break
                elif self.determine_drop_weapon():
                    self.drop_weapon()

                # Attack? Only allow if we didn't just start picking up a weapon!
                if self.pickup_animation is None:
                    attack: Attack | None = self.determine_attack()
                    if attack is not None:
                        self.log(f"Attack {attack.sprite}")
                        self.last_attack = attack
                        self.attack_timer = attack.anim_time
                        self.stamina -= attack.stamina_cost
                        self.stamina = max(self.stamina, MIN_STAMINA)
                        self.frame = 0

                        if attack.initial_sound is not None:
                            # * = unpack the elements of the tuple (sound to play, and number of variations) into
                            # arguments to pass to play_sound
                            game.play_sound(*attack.initial_sound)

                        # Is this a flying kick?
                        if attack.flying_kick:
                            self.vel = Vector(
                                FLYING_KICK_VEL_X * self.facing_x,
                                FLYING_KICK_VEL_Y,
                            )

                        # Grab player?
                        if attack.grab:
                            game.player.grabbed()

            # Update movement and animation, and pick up a weapon if desired
            # Must check attack_timer again as an attack may only just have started during the previous block of code
            if self.attack_timer <= 0:
                # Not attacking
                # Update facing_x. If get_desired_facing returns None, leave facing_x as it is
                desired_facing: int | None = self.get_desired_facing()
                if desired_facing is not None:
                    self.facing_x = desired_facing

                target: Vector = self.get_move_target()
                if target != self.vpos:
                    self.walking = True

                    new_x, dx = move_towards(
                        float(self.vpos.x), float(target.x), float(self.speed.x)
                    )
                    self.vpos = Vector(new_x, self.vpos.y)
                    new_y, dy = move_towards(
                        float(self.vpos.y), float(target.y), float(self.speed.y)
                    )
                    self.vpos = Vector(self.vpos.x, new_y)

                    self.apply_movement_boundaries(dx, dy)

                    self.frame += 1

                else:
                    # No movement, reset frame to standing
                    self.walking = False
                    self.frame = 7  # Resetting frame to 7 rather than zero fixes an issue where it looks weird if you only walk for a fraction of a second
            else:
                # Currently attacking (so there is a current attack)
                self.frame += 1
                assert self.last_attack is not None

                frame: int = self.get_attack_frame()

                # If current frame of attack is a hit frame, inflict damage to enemies
                if frame in self.last_attack.hit_frames:
                    # Is this a throw attack?
                    if self.last_attack.throw:
                        # If the current attack is a grab attack, that means we're the boss throwing the player
                        if self.last_attack.grab:
                            # Throw the player, if we haven't already done that on a previous frame
                            if (
                                game.player.falling_state
                                == Fighter.FallingState.GRABBED
                            ):
                                game.player.hit(self, self.last_attack)
                                game.player.thrown(self.facing_x)

                        # Otherwise it's a normal throw of a barrel - make sure we still have the weapon, might have
                        # released it on a previous frame!
                        elif isinstance(self.weapon, Barrel):
                            self.weapon.throw(self.facing_x, self)
                            self.weapon = None

                    # Call attack regardless of whether this is a throw attack, this fixes an issue where the barrel
                    # doesn't hit opponents because the position it's in when it's released is already past them
                    self.attack(self.last_attack)

    def attack(self, attack: Attack) -> None:
        # See if there is an opponent directly in front of us who we can hit (or behind us if it's a rear attack
        # such as elbow)
        if attack.strength > 0:
            # Loop through all opponents to see which (if any) this attack should hit
            for opponent in self.get_opponents():
                vec: Vector = opponent.vpos - self.vpos
                facing_correct: bool = sign(self.facing_x) == sign(float(vec.x))
                if attack.rear_attack:
                    facing_correct = not facing_correct

                # Should attack hit this opponent?
                if (
                    abs(vec.y) < opponent.half_hit_area.y
                    and facing_correct
                    and abs(vec.x) < attack.reach + opponent.half_hit_area.x
                ):
                    opponent.hit(self, attack)

                    # If we're using a weapon, it may have broken as a result of being used
                    if self.weapon is not None and self.weapon.is_broken():
                        self.drop_weapon()

            if DEBUG_SHOW_ATTACKS:
                attack_facing: int = self.facing_x * (
                    -1 if attack.rear_attack else 1
                )
                debug_rect: Rect = Rect(
                    self.x - (attack.reach if attack_facing == -1 else 0),
                    self.y - 5,
                    attack.reach,
                    10,
                )
                debug_drawcalls.append(
                    lambda: renderer.filled_rect(
                        debug_rect.left,
                        debug_rect.top,
                        debug_rect.width,
                        debug_rect.height,
                        (255, 0, 0),
                    )
                )

    def hit(self, hitter: Fighter | Barrel, attack: Attack) -> None:
        # Hitter can be another fighter, or a weapon such as a barrel
        # Can't be hit if we're falling/getting up
        if (
            self.falling_state == Fighter.FallingState.STANDING
            or self.falling_state == Fighter.FallingState.GRABBED
        ):
            # Can't be hit if we're already in the hit animation
            if self.hit_timer <= 0:
                self.stamina -= (
                    attack.strength
                    * BASE_STAMINA_DAMAGE_MULTIPLIER
                    * attack.stamina_damage_multiplier
                )
                self.stamina = max(self.stamina, MIN_STAMINA)
                self.health -= attack.strength

                # Hit timer ensures we can't receive damage again until it's counted down, and stuns the fighter
                # Stronger attacks stun for longer
                self.hit_timer = (
                    attack.strength * 8 * attack.stun_time_multiplier
                )
                self.hit_frame = randint(0, 1)

                # Stop our attack if we're in the middle of one - unless it's a flying kick, in which case continue.
                # Code elsewhere will ensure we don't do the 'been hit' animation at the end of a flying kick
                if self.attack_timer > 0 and (
                    self.last_attack is not None
                    and not self.last_attack.flying_kick
                ):
                    self.attack_timer = 0

                # Drop weapon
                if self.weapon is not None:
                    self.drop_weapon()

                if attack.hit_sound is not None:
                    # * = unpack the elements of the tuple (sound to play, and number of variations) into
                    # arguments to pass to play_sound
                    game.play_sound(*attack.hit_sound)

                if self.hit_sound is not None:
                    # Sound for me being hit (only used by portal)
                    game.play_sound(self.hit_sound)

                # Check for being knocked down due to being out of health or stamina
                # Portals can't fall
                if (self.stamina <= 0 or self.health <= 0) and not isinstance(
                    self, EnemyPortal
                ):
                    self.falling_state = Fighter.FallingState.FALLING
                    self.frame = 0
                    self.hit_timer = 0

                    # If we're knocked down due to being out of stamina, and we're close to death, just die already
                    if self.health < 3:
                        self.health = 0
                        self.use_die_animation = (
                            randint(0, 1) == 0
                        )  # Use die animation 50% of the time

                # If the attacker was using a weapon, tell the weapon that it was used
                # Must check that hitter is a Fighter, as it might be a barrel!
                if isinstance(hitter, Fighter) and hitter.weapon is not None:
                    hitter.weapon.used()

            # Always face towards hitter
            # First check to make sure that hitter and I aren't at the same X position
            if hitter.vpos.x != self.vpos.x:
                self.facing_x = sign(hitter.vpos.x - self.vpos.x)

                if (
                    self.falling_state == Fighter.FallingState.FALLING
                    and not self.use_die_animation
                ):
                    # Get knocked backwards
                    self.vel = Vector(
                        self.vel.x + -self.facing_x * 10, self.vel.y
                    )

    def died(self) -> None:
        # Called when out of lives, can be overridden in cases where subclasses need to know that - e.g.
        # EnemyHoodie may drop stick on death
        pass

    @override
    def draw_at(self, offset: Vector) -> None:
        # Determine sprite to use based on our current action
        self.image = self.determine_sprite()

        super().draw_at(offset)

        if DEBUG_SHOW_HEALTH_AND_STAMINA:
            draw_system_text(f"HP: {self.health}", self.x, self.y - 200)
            draw_system_text(f"STM: {self.stamina}", self.x, self.y - 176)

        if DEBUG_SHOW_HIT_AREA_WIDTH:
            renderer.rect(
                self.x - float(self.half_hit_area.x),
                self.y - float(self.half_hit_area.y),
                float(self.half_hit_area.x) * 2,
                float(self.half_hit_area.y) * 2,
                (255, 255, 255),
            )

        if DEBUG_SHOW_LOGS:
            for i, message in enumerate(reversed(self.logs)):
                draw_system_text(message, self.x, self.y + 10 * i, size=14)

    def determine_sprite(self) -> str:
        show: bool = True

        if self.falling_state == Fighter.FallingState.FALLING:
            if (
                self.frame > 60
                and self.health <= 0
                and (self.frame // 10) % 2 == 0
            ):
                # If we're out of health, flash on and off for a short while
                show = False

            if show:
                # When we fall down, we stay on the last frame (2) for an extended period
                # If we've only just fallen off a scooter, play knocked_off frame 0 before
                # continuing from knockdown frame 1
                if self.just_knocked_off_scooter:
                    # Check if we need to transition to the knockdown stage of the animation
                    if self.frame > 10:
                        self.just_knocked_off_scooter = False

                        # Create the scooter as an independent object
                        game.scooters.append(
                            Scooter(
                                self.vpos, self.facing_x, self.colour_variant
                            )
                        )

                # Now choose the sprite to use this frame
                if self.just_knocked_off_scooter:
                    anim_type: str = "knocked_off"
                    frame: int = 0
                elif self.use_die_animation:
                    anim_type = "die"
                    frame = min(self.frame // 20, 2)
                else:
                    last_frame: int = (
                        3 if isinstance(self, EnemyScooterboy) else 2
                    )
                    anim_type = "knockdown"
                    frame = min(self.frame // 10, last_frame)

        elif self.falling_state == Fighter.FallingState.GETTING_UP:
            anim_type = "getup"
            frame = min(self.frame // 10, 1)

        elif self.falling_state == Fighter.FallingState.GRABBED:
            show = False

        elif self.falling_state == Fighter.FallingState.THROWN:
            anim_type = "thrown"
            frame = min(self.frame // 12, 3)

        elif self.hit_timer > 0:
            frame = self.hit_frame
            anim_type = "hit"

        elif self.pickup_animation is not None:
            # Doing animation for picking up a weapon
            assert self.weapon is not None
            frame = min(self.frame // 12, self.weapon.end_pickup_frame)
            anim_type = f"pickup_{self.pickup_animation}"

        elif self.attack_timer > 0:
            # Currently attacking
            assert self.last_attack is not None
            anim_type = self.last_attack.sprite
            frame = self.get_attack_frame()

        else:
            # Walking or standing
            if self.walking:
                # There are four walk animation frames, we take self.frame (an unbounded number incrementing by 1 each
                # game frame) and divide it by self.anim_update_rate (giving that many frames of delay between
                # switching animation frames), the result of that is MODded 4 to reduce it to the actual animation
                # frame to use in the range 0-3
                anim_type = "walk"
                frame = (
                    self.frame // self.anim_update_rate
                ) % 4  # 4 frames of walking animation
            else:
                # Standing
                frame = 0
                # Use anim_type stand or walk depending on whether we have a weapon - we only have 'walk' sprites
                # for weapons
                anim_type = "walk" if self.weapon is not None else "stand"

            # Add the weapon name to the walking/standing animation
            # This isn't done for weapon attack animations, because barrel is released during the throw animation
            if self.weapon is not None:
                anim_type += f"_{self.weapon.name}"

        if not show:
            return "blank"
        # In sprite filenames, 0 = facing left, 1 = right
        facing_id: int = 1 if self.facing_x == 1 else 0
        image: str = f"{self.sprite}_{anim_type}_{facing_id}_{frame}"
        if self.colour_variant is not None:
            image += f"_{self.colour_variant}"
        return image

    def get_attack_frame(self) -> int:
        # return value of this function is an animation frame, e.g. we are on the third frame of the punch animation
        # self.frame is a game frame, increasing by 1 every 1/60th of a second
        # We use self.last_attack to get the current attack that we're doing, i.e. it's the last attack we started
        # doing, and we're still doing it
        assert self.last_attack is not None
        return min(
            self.frame // self.last_attack.frame_time,
            self.last_attack.frames - 1,
        )

    def override_walking(self) -> bool:
        # Used by subclasses to prevent the usual walking/attacking behaviour
        return False

    def drop_weapon(self) -> None:
        assert self.weapon is not None
        # Stop pickup animation if we're in the middle of one
        self.pickup_animation = None
        self.weapon.dropped()
        self.weapon = None

    def grabbed(self) -> None:
        self.log("Grabbed")
        self.falling_state = Fighter.FallingState.GRABBED
        if self.weapon is not None:
            self.drop_weapon()

    def thrown(self, dir_x: int) -> None:
        self.log("Thrown")
        self.falling_state = Fighter.FallingState.THROWN
        self.vel = Vector(dir_x * PLAYER_THROW_VEL_X, PLAYER_THROW_VEL_Y)
        self.facing_x = -dir_x

        # Shift position for throw animation
        self.vpos = Vector(self.vpos.x + dir_x * 50, self.vpos.y)
        self.height_above_ground = 45

    def apply_movement_boundaries(self, dx: float, dy: float) -> None:
        # A fighter outside the boundary can walk in a direction which will help them get inside the boundary, but not
        # in the direction that will take them further out of it
        if dx < 0 and self.vpos.x < game.boundary.left:
            self.vpos = Vector(game.boundary.left, self.vpos.y)
        elif dx > 0 and self.vpos.x > game.boundary.right:
            self.vpos = Vector(game.boundary.right, self.vpos.y)
        if dy < 0 and self.vpos.y < game.boundary.top:
            self.vpos = Vector(self.vpos.x, game.boundary.top)
        elif dy > 0 and self.vpos.y > game.boundary.bottom:
            self.vpos = Vector(self.vpos.x, game.boundary.bottom)

    # Every class that inherits from Fighter must implement each of the following abstract methods

    @abstractmethod
    def determine_attack(self) -> Attack | None: ...

    @abstractmethod
    def determine_pick_up_weapon(self) -> bool: ...

    @abstractmethod
    def determine_drop_weapon(self) -> bool: ...

    @abstractmethod
    def get_opponents(self) -> Sequence[Fighter]: ...

    @abstractmethod
    def get_move_target(self) -> Vector: ...

    @abstractmethod
    def get_desired_facing(self) -> int | None: ...


class Player(Fighter):
    __slots__ = ("controls", "extra_life_timer")

    def __init__(self, controls: Controls) -> None:
        # Anchor point just above bottom of sprite
        super().__init__(
            spawn_pos=(400, 400),
            spawn_anchor=("center", 256),
            speed=Vector(3, 2),
            sprite="hero",
            health=30,
            lives=3,
            separate_shadow=True,
        )
        self.controls: Controls = controls
        self.extra_life_timer: int = 0

    @override
    def update(self) -> None:
        super().update()

        self.extra_life_timer -= 1

        # Check for collecting powerups
        for powerup in game.powerups:
            if (powerup.vpos - self.vpos).magnitude() < 30:
                powerup.collect(self)

    @override
    def determine_attack(self) -> Attack | None:
        # Do we have a weapon?
        if self.weapon is not None:
            # Ensure we cannot attack during the pickup animation
            if self.pickup_animation is None and self.controls.button_pressed(
                0
            ):
                return ATTACKS[self.weapon.name]

        elif self.controls.button_pressed(0):
            # in combo?
            if (
                self.last_attack is not None
                and self.last_attack.combo_next is not None
                and self.attack_timer >= -30
            ):
                # Get next attack in combo
                # 0 here represents button 0, ideally this code should be made more general, but in practice
                # the only combo we actually have is where you press button 0 three times to do a sequence of punches
                # ending in an uppercut
                if 0 in self.last_attack.combo_next:
                    return ATTACKS[self.last_attack.combo_next[0]]

            # Not in combo, just return default attack
            return ATTACKS["punch"]

        elif self.controls.button_pressed(1):
            return choice((ATTACKS["kick"], ATTACKS["highkick"]))

        elif self.controls.button_pressed(2):
            return ATTACKS["elbow"]

        elif self.controls.button_pressed(3):
            return ATTACKS["flyingkick"]

        return None

    @override
    def determine_pick_up_weapon(self) -> bool:
        return self.controls.button_pressed(0)

    @override
    def determine_drop_weapon(self) -> bool:
        return self.weapon is not None and self.controls.button_pressed(1)

    @override
    def get_opponents(self) -> Sequence[Fighter]:
        return game.enemies

    @override
    def get_move_target(self) -> Vector:
        # Our target position is our current position offset based on control inputs and speed
        return self.vpos + Vector(
            self.controls.get_x() * self.speed.x,
            self.controls.get_y() * self.speed.y,
        )

    @override
    def get_desired_facing(self) -> int | None:
        # Face the way we're pushing (set here, and the caller leaves facing_x alone); keep facing the same
        # direction as before if no X input
        dx: int = self.controls.get_x()
        if dx != 0:
            self.facing_x = sign(dx)
            return None
        return self.facing_x

    @override
    def get_draw_order_offset(self) -> int:
        # Consider player to be in front of another object with the same Y pos
        return 1

    def gain_extra_life(self) -> None:
        self.lives += 1
        self.extra_life_timer = 30


class Enemy(Fighter, ABC):
    # State is an inner class - a class within a class, so its name doesn't clash with the global class State
    class State(Enum):
        APPROACH_PLAYER = 0
        GO_TO_POS = 1
        GO_TO_WEAPON = 2
        PAUSE = 3
        KNOCKED_DOWN = 4
        RIDING_SCOOTER = 5
        PORTAL = 6
        PORTAL_EXPLODE = 7

    __slots__ = (
        "target",
        "target_weapon",
        "state",
        "state_timer",
        "attacks",
        "approach_player_distance",
        "score",
    )

    def __init__(
        self,
        pos: PointLike,
        name: str,
        attacks: tuple[str, ...],
        start_timer: int,
        speed: Vector = DEFAULT_ENEMY_SPEED,
        health: int = 15,
        stamina: int = 500,
        approach_player_distance: int = ENEMY_APPROACH_PLAYER_DISTANCE,
        anchor_y: int = 256,
        half_hit_area: Vector = DEFAULT_HALF_HIT_AREA,
        colour_variant: int | None = None,
        hit_sound: str | None = None,
        score: int = 10,
    ) -> None:
        # Slower animation speed than Hero
        super().__init__(
            spawn_pos=pos,
            spawn_anchor=("center", anchor_y),
            speed=speed,
            sprite=name,
            health=health,
            stamina=stamina,
            anim_update_rate=14,
            half_hit_area=half_hit_area,
            colour_variant=colour_variant,
            hit_sound=hit_sound,
        )

        # Where we're walking to (a frozen vector, so this is a value, not a shared reference)
        self.target: Vector = self.vpos

        self.target_weapon: Weapon | None = None

        # Enemies don't try to target player until their start timer drops to zero
        # e.g. on starting a new stage we might not want them to start targeting the player until they have
        # scrolled onto the screen
        self.state: Enemy.State = Enemy.State.PAUSE
        self.state_timer: int = start_timer

        #: The names of the attacks (in ATTACKS) we choose from
        self.attacks: tuple[str, ...] = attacks
        self.approach_player_distance: int = approach_player_distance
        self.score: int = score

    def spawned(self) -> None:
        # Called when the enemy is added into the game (when its stage is reached)
        pass

    @override
    def update(self) -> None:
        match self.state:
            case Enemy.State.APPROACH_PLAYER:
                player = game.player

                # If player is attacking and we are quite close, chance (each frame) of backing up a little
                if (
                    player.attack_timer > 0
                    and abs(self.vpos.y - player.vpos.y) < 20
                    and abs(self.vpos.x - player.vpos.x) < 200
                    and randint(0, 500) == 0
                ):
                    self.log("Back away from attack")
                    self.target = Vector(
                        self.vpos.x - self.facing_x * 90, self.target.y
                    )
                    self.state = Enemy.State.GO_TO_POS
                else:
                    # Head towards player
                    # If we are holding a barrel, use a larger X offset so we throw from a distance
                    x_offset: int = (
                        ENEMY_APPROACH_PLAYER_DISTANCE_BARREL
                        if isinstance(self.weapon, Barrel)
                        else self.approach_player_distance
                    )
                    self.target = Vector(
                        player.vpos.x
                        + x_offset * sign(self.vpos.x - player.vpos.x),
                        player.vpos.y,
                    )

            case Enemy.State.GO_TO_POS:
                # In this state we just check to see if we've reached the target position, if so we make a new decision
                if self.target == self.vpos:
                    self.make_decision()

            case Enemy.State.GO_TO_WEAPON:
                assert self.target_weapon is not None
                if (
                    not self.target_weapon.can_be_picked_up()
                    or not self.target_weapon.on_screen()
                ):
                    # Weapon no longer available, make a new decision
                    self.target_weapon = None
                    self.make_decision()
                else:
                    self.target = self.target_weapon.vpos
                    if self.target == self.vpos:
                        # Arrived - pick up weapon and make new decision
                        self.log("Pick up weapon")
                        self.pickup_animation = self.target_weapon.name
                        self.frame = 0
                        self.target_weapon.pick_up(Fighter.WEAPON_HOLD_HEIGHT)
                        self.weapon = self.target_weapon
                        self.target_weapon = None
                        self.make_decision()

            case Enemy.State.PAUSE:
                self.state_timer -= 1
                if self.state_timer < 0:
                    self.make_decision()

            case Enemy.State.KNOCKED_DOWN:
                # Check to see if we've got up again, if so switch state
                if self.falling_state == Fighter.FallingState.STANDING:
                    self.make_decision()

            case (
                Enemy.State.RIDING_SCOOTER
                | Enemy.State.PORTAL
                | Enemy.State.PORTAL_EXPLODE
            ):
                pass  # updated by the EnemyScooterboy / EnemyPortal subclasses

            case _:
                raise ValueError(f"unhandled enemy state {self.state!r}")

        if self.state in (
            Enemy.State.APPROACH_PLAYER,
            Enemy.State.GO_TO_POS,
            Enemy.State.GO_TO_WEAPON,
        ):
            # Ensure that target position is within the level boundary
            self.target = Vector(
                min(
                    max(self.target.x, game.boundary.left),
                    game.boundary.right,
                ),
                min(
                    max(self.target.y, game.boundary.top),
                    game.boundary.bottom,
                ),
            )

            # Check to see if another enemy is already heading for the new target pos, or one very close to it.
            # If so, make a new decision
            if any(
                enemy is not self
                and (enemy.target - self.target).magnitude() < 20
                for enemy in game.enemies
            ):
                self.log("Same target")
                self.make_decision()

        # Call through to Fighter class update
        super().update()

    @override
    def draw_at(self, offset: Vector) -> None:
        super().draw_at(offset)

        if DEBUG_SHOW_TARGET_POS:
            renderer.line(
                self.vpos - offset, self.target - offset, (255, 255, 255)
            )

    @override
    def determine_attack(self) -> Attack | None:
        # Allow attacking if we're in APPROACH_PLAYER state, aligned with player on Y axis, both I and player are
        # standing up, and we're within the right range of distances on the X axis, finally a must pass a random chance
        # check of 1 in 20
        # If we're holding a barrel, can be within any distance on the X axis

        # Unpack player pos into more convenient variables
        px, py = game.player.vpos

        holding_barrel: bool = isinstance(self.weapon, Barrel)

        if (
            self.state == Enemy.State.APPROACH_PLAYER
            and game.player.falling_state == Fighter.FallingState.STANDING
            and self.vpos.y == py
            and (
                self.approach_player_distance * 0.9
                < abs(self.vpos.x - px)
                <= self.approach_player_distance * 1.1
                or holding_barrel
            )
            and randint(0, 19) == 0
        ):
            if self.weapon is not None:
                return ATTACKS[self.weapon.name]
            chosen_attack: Attack = ATTACKS[choice(self.attacks)]

            # If the chosen attack is a grab, don't allow it if the player is currently doing a flying kick
            if (
                chosen_attack.grab
                and game.player.last_attack is not None
                and game.player.last_attack.flying_kick
            ):
                return None

            return chosen_attack
        return None

    @override
    def determine_pick_up_weapon(self) -> bool:
        return False

    @override
    def determine_drop_weapon(self) -> bool:
        return False

    @override
    def get_opponents(self) -> Sequence[Fighter]:
        return [game.player]

    @override
    def get_move_target(self) -> Vector:
        # Walk to the target our state machine chose
        return self.target

    @override
    def get_desired_facing(self) -> int:
        # Always face towards player, unless we're on a scooter
        match self.state:
            case Enemy.State.RIDING_SCOOTER:
                return self.facing_x
            case _:
                return 1 if self.vpos.x < game.player.vpos.x else -1

    @override
    def hit(self, hitter: Fighter | Barrel, attack: Attack) -> None:
        if self.state == Enemy.State.KNOCKED_DOWN:
            # Already knocked down
            return

        super().hit(hitter, attack)

        # If we're riding a scooter, then getting hit will always cause us to fall, regardless of stamina
        if self.state == Enemy.State.RIDING_SCOOTER:
            self.falling_state = Fighter.FallingState.FALLING
            self.frame = 0
            self.hit_timer = 0
            self.just_knocked_off_scooter = True

        if self.falling_state == Fighter.FallingState.FALLING:
            # Set state as knocked down
            self.state = Enemy.State.KNOCKED_DOWN
            self.log("Knocked down")

    def make_decision(self) -> None:
        player: Player = game.player

        # If we're not going for a weapon:
        # If we're the only enemy, always move in to attack
        if len(game.enemies) == 1:
            self.log("Only enemy, go to player")
            self.state = Enemy.State.APPROACH_PLAYER
        else:
            # 7/10 chance of going directly to a point where we can attack the player, unless there's another enemy
            # already heading there in which case flank
            # 3/10 chance of going to a random point slightly further from the player
            # 1/10 chance of pausing for a short time

            r: int = randint(0, 9)
            if r < 7:
                # Check to see if another enemy on the same X side of the player is already heading to attack them
                # If so, flank instead
                if any(
                    enemy is not self
                    and enemy.state == Enemy.State.APPROACH_PLAYER
                    and sign(enemy.vpos.x - player.vpos.x)
                    == sign(self.vpos.x - player.vpos.x)
                    for enemy in game.enemies
                ):
                    # Go to opposite side of player, at a Y position offset from them but on the same Y side that
                    # we're on now (e.g. if we're below, stay below). If Y pos is same, choose Y side randomly.
                    self.log("Begin flanking (same target)")
                    self.state = Enemy.State.GO_TO_POS
                    self.target = Vector(
                        player.vpos.x - sign(self.vpos.x - player.vpos.x) * 50,
                        player.vpos.y + sign(self.vpos.y - player.vpos.y) * 50,
                    )
                    if self.target.y == player.vpos.y:
                        self.target = Vector(
                            self.target.x,
                            player.vpos.y + choice((-1, 1)) * 50,
                        )
                else:
                    # Go to player
                    self.log("Go to player")
                    self.state = Enemy.State.APPROACH_PLAYER

            elif r < 9:
                # Go to a random point at a moderate distance from the player
                # Stick to same half of screen on X axis
                self.log("Go to distance from player")
                x_side: int = sign(self.vpos.x - player.vpos.x) or choice(
                    (1, -1)
                )
                x1: int = int(player.vpos.x + (150 * x_side))
                x2: int = int(player.vpos.x + (400 * x_side))
                x: int = randint(min(x1, x2), max(x1, x2))
                y: int = randint(
                    int(game.boundary.top), int(game.boundary.bottom)
                )
                self.target = Vector(x, y)
                self.state = Enemy.State.GO_TO_POS

            else:
                # Pause
                self.log("Pause")
                self.state_timer = randint(50, 100)
                self.state = Enemy.State.PAUSE


class EnemyVax(Enemy):
    __slots__ = ()

    def __init__(self, pos: PointLike, start_timer: int = 20) -> None:
        super().__init__(
            pos,
            "vax",
            ("vax_lpunch", "vax_rpunch", "vax_pound"),
            start_timer=start_timer,
            colour_variant=randint(0, 2),
            score=20,
        )


class EnemyHoodie(Enemy):
    __slots__ = ()

    def __init__(self, pos: PointLike, start_timer: int = 20) -> None:
        super().__init__(
            pos,
            "hoodie",
            ("hoodie_lpunch", "hoodie_rpunch", "hoodie_special"),
            health=12,
            speed=Vector(1.2, 1),
            start_timer=start_timer,
            colour_variant=randint(0, 2),
            score=20,
        )

    @override
    def died(self) -> None:
        super().died()

        # Chance of dropping a stick
        if randint(0, 2) == 0:
            game.weapons.append(Stick(self.vpos))


class EnemyScooterboy(Enemy):
    SCOOTER_SPEED_SLOW: ClassVar[int] = 4
    SCOOTER_SPEED_FAST: ClassVar[int] = 12
    SCOOTER_ACCELERATION: ClassVar[float] = 0.2

    __slots__ = ("scooter_speed", "scooter_target_speed")

    def __init__(self, pos: PointLike, start_timer: int = 20) -> None:
        super().__init__(
            pos,
            "scooterboy",
            ("scooterboy_attack1",),
            start_timer=start_timer,
            approach_player_distance=ENEMY_APPROACH_PLAYER_DISTANCE_SCOOTERBOY,
            colour_variant=randint(0, 2),
            score=30,
        )
        self.state = Enemy.State.RIDING_SCOOTER
        self.scooter_speed: float = EnemyScooterboy.SCOOTER_SPEED_SLOW
        self.scooter_target_speed: float = self.scooter_speed

    @override
    def make_decision(self) -> None:
        # Scooterboy stays on scooter until knocked off
        if self.state != Enemy.State.RIDING_SCOOTER:
            super().make_decision()

    @override
    def determine_sprite(self) -> str:
        # Riding scooter is a state unique to Scooterboy, so it is dealt with here
        match self.state:
            case Enemy.State.RIDING_SCOOTER:
                facing_id: int = 1 if self.facing_x == 1 else 0
                # Frames 1-2 while speeding up
                frame: int = (
                    min(self.frame // 5, 2)
                    if self.scooter_speed < self.scooter_target_speed
                    else 0
                )
                return f"{self.sprite}_ride_{facing_id}_{frame}_{self.colour_variant}"
            case _:
                return super().determine_sprite()

    @override
    def update(self) -> None:
        if self.state == Enemy.State.RIDING_SCOOTER:
            player: Player = game.player

            # Currently accelerating/decelerating?
            if self.scooter_speed != self.scooter_target_speed:
                self.scooter_speed, _ = move_towards(
                    self.scooter_speed,
                    self.scooter_target_speed,
                    EnemyScooterboy.SCOOTER_ACCELERATION,
                )
                self.frame += 1
            elif self.on_screen() and randint(0, 30) == 0:
                # If on screen, random chance of accelerating
                self.scooter_target_speed = EnemyScooterboy.SCOOTER_SPEED_FAST
                self.frame = 0

            # Move forward
            self.target = Vector(
                self.vpos.x + self.facing_x * self.scooter_speed,
                self.target.y,
            )
            self.vpos = Vector(self.target.x, self.vpos.y)

            # Turn around if we've gone off the edge of the screen
            # We check self.x which is the actual screen position as opposed to the position in the scrolling level
            if (self.facing_x > 0 and self.x > WIDTH + 200) or (
                self.facing_x < 0 and self.x < -200
            ):
                self.facing_x = -self.facing_x
                self.target = Vector(self.target.x, player.vpos.y)

                # If player is standing, move to the same Y position as player, otherwise choose a random Y position
                # which is not close to the player Y position (to avoid player getting stunlocked)
                if game.player.falling_state == Fighter.FallingState.STANDING:
                    self.vpos = Vector(self.vpos.x, self.target.y)
                else:
                    while abs(self.vpos.y - self.target.y) < 40:
                        self.vpos = Vector(
                            self.vpos.x, randint(MIN_WALK_Y, HEIGHT - 1)
                        )

                # Also slow down if at high speed
                self.scooter_target_speed = EnemyScooterboy.SCOOTER_SPEED_SLOW
                self.scooter_speed = self.scooter_target_speed

            # Check to see if we hit the player
            if (
                player.falling_state == Fighter.FallingState.STANDING
                and abs(player.vpos.y - self.vpos.y) < 30
                and abs(self.vpos.x - player.vpos.x) < 60
                and player.height_above_ground < 20
            ):
                player.hit(self, ATTACKS["scooter_hit"])

        super().update()

    @override
    def override_walking(self) -> bool:
        return self.state == Enemy.State.RIDING_SCOOTER

    @override
    def died(self) -> None:
        super().died()

        # Low chance of dropping a chain
        if randint(0, 19) == 0:
            game.weapons.append(Chain(self.vpos))


class EnemyBoss(Enemy):
    __slots__ = ()

    def __init__(self, pos: PointLike, start_timer: int = 20) -> None:
        super().__init__(
            pos,
            "boss",
            (
                "boss_lpunch",
                "boss_rpunch",
                "boss_kick",
                "boss_grab_player",
            ),
            speed=Vector(0.9, 0.8),
            health=25,
            stamina=1000,
            start_timer=start_timer,
            anchor_y=280,
            half_hit_area=Vector(30, 20),
            colour_variant=randint(0, 2),
            score=75,
        )

    @override
    def make_decision(self) -> None:
        # Boss can pick up a barrel, if they're not currently holding one
        # Look for a barrel we can walk to. Barrel must not be held by anyone else and must be on the screen
        if self.weapon is None:
            available_barrels: list[Barrel] = [
                weapon
                for weapon in game.weapons
                if isinstance(weapon, Barrel)
                and weapon.can_be_picked_up()
                and weapon.on_screen()
            ]
            # Find a weapon to go to - don't go to a barrel if another enemy is already going to it
            for weapon in available_barrels:
                if not any(
                    enemy is not self and enemy.target_weapon is weapon
                    for enemy in game.enemies
                ):
                    # This weapon is OK to go for
                    self.log("Go to weapon")
                    self.state = Enemy.State.GO_TO_WEAPON
                    self.target_weapon = weapon
                    return

        # If we didn't enter the GO_TO_WEAPON state, call the parent method
        super().make_decision()


class EnemyPortal(Enemy):
    GENERATE_ANIMATION_FRAMES: ClassVar[int] = 6
    GENERATE_ANIMATION_DIVISOR: ClassVar[int] = 16
    GENERATE_ANIMATION_TIME: ClassVar[int] = (
        GENERATE_ANIMATION_FRAMES * GENERATE_ANIMATION_DIVISOR
    )

    __slots__ = (
        "enemies",
        "spawn_interval",
        "spawn_timer",
        "spawn_interval_change",
        "max_spawn_interval",
        "max_enemies",
        "spawning_enemy",
        "spawn_facing",
    )

    def __init__(
        self,
        pos: PointLike,
        enemies: tuple[Callable[[PointLike], Enemy], ...],
        spawn_interval: int,
        spawn_interval_change: int = 0,
        max_spawn_interval: int = 600,
        max_enemies: int = 5,
        start_timer: int = 90,
    ) -> None:
        # Hittable area is larger for portals
        super().__init__(
            pos,
            "portal",
            (),
            start_timer=start_timer,
            anchor_y=340,
            half_hit_area=Vector(50, 50),
            hit_sound="portal_hit",
        )
        #: The enemy classes we spawn, chosen at random
        self.enemies: tuple[Callable[[PointLike], Enemy], ...] = enemies
        self.spawn_interval: int = spawn_interval
        self.spawn_timer: int = spawn_interval
        self.spawn_interval_change: int = spawn_interval_change
        self.max_spawn_interval: int = max_spawn_interval
        self.max_enemies: int = max_enemies
        #: Created when the generate animation starts, put in the level when it ends
        self.spawning_enemy: Enemy | None = None
        self.spawn_facing: int = 0

    @override
    def spawned(self) -> None:
        super().spawned()
        game.play_sound("portal_appear")

    @override
    def make_decision(self) -> None:
        # Like all enemies, portals start in the PAUSE state until their start_timer expires
        self.state = Enemy.State.PORTAL

    @override
    def determine_sprite(self) -> str:
        if self.state == Enemy.State.PAUSE and self.frame // 8 < 4:
            return f"portal_grow_{min(self.frame // 8, 3)}"
        if self.state == Enemy.State.PORTAL_EXPLODE:
            return f"portal_destroyed_{min(self.frame // 6, 7)}"
        if self.spawning_enemy is not None:
            # 3 frames of neutral generate animation, then 3 frames of animation for generating specific enemy
            frame: int = self.frame // EnemyPortal.GENERATE_ANIMATION_DIVISOR
            if frame < 3:
                return f"portal_generate_{frame}"
            return f"portal_generate_{self.spawning_enemy.sprite}_{self.spawn_facing}_{min(frame - 3, 2)}_{self.spawning_enemy.colour_variant}"
        if self.hit_timer > 0:
            return "portal_hit_0"
        return f"portal_idle_{(self.frame // 8) % 8}"

    @override
    def update(self) -> None:
        self.frame += 1

        match self.state:
            case Enemy.State.PORTAL:
                if self.health <= 0:
                    self.state = Enemy.State.PORTAL_EXPLODE
                    self.frame = 0
                    game.play_sound("portal_destroyed")

                else:
                    self.spawn_timer -= 1
                    if (
                        self.spawn_timer <= 0
                        and self.spawning_enemy is not None
                    ):
                        # Animation complete, actually put the enemy in the level
                        game.spawn_enemy(self.spawning_enemy)

                        self.spawning_enemy = None

                        # Reset spawn timer, depending on spawn_interval_change we may spawn less frequently as time goes on
                        self.spawn_interval += self.spawn_interval_change
                        self.spawn_interval = min(
                            self.spawn_interval, self.max_spawn_interval
                        )
                        self.spawn_timer = self.spawn_interval

                    elif (
                        self.spawning_enemy is None
                        and self.spawn_timer
                        <= EnemyPortal.GENERATE_ANIMATION_TIME
                    ):
                        if len(game.enemies) >= self.max_enemies:
                            # Too many enemies to spawn at the moment, try again in one second
                            self.spawn_timer = 60
                        else:
                            # Randomly choose an enemy to spawn from our enemies list
                            chosen_enemy: Callable[[PointLike], Enemy] = choice(
                                self.enemies
                            )

                            # Choose direction for spawned enemy to face (0/1 = left/right)
                            self.spawn_facing = (
                                0 if self.vpos.x > game.player.vpos.x else 1
                            )

                            # Instantiate the enemy, but it won't appear in the level until the animation is complete
                            self.spawning_enemy = chosen_enemy(self.vpos)

                            # Reset frame for spawning animation
                            self.frame = 0

                            game.play_sound("portal_enemy_spawn")

            case Enemy.State.PORTAL_EXPLODE:
                if self.frame > 50:
                    self.lives -= 1
                    self.died()

            case Enemy.State.PAUSE:
                pass  # growing; Enemy.update counts the start timer down

            case _:
                raise ValueError(f"unhandled portal state {self.state!r}")

        super().update()

    @override
    def override_walking(self) -> bool:
        # A portal never walks
        return True


# This is the scooter on its own, with the rider having been knocked off
class Scooter(ScrollHeightActor):
    __slots__ = ("facing_x", "colour_variant", "vel_x", "frame")

    def __init__(
        self, pos: PointLike, facing_x: int, colour_variant: int | None
    ) -> None:
        super().__init__("blank", pos, ("center", 256))
        self.facing_x: int = facing_x
        self.colour_variant: int | None = colour_variant
        self.vel_x: float = -facing_x * 8
        self.frame: int = 0
        game.play_sound("scooter_fall")

    def update(self) -> None:
        self.frame += 1
        self.vpos = Vector(self.vpos.x + self.vel_x, self.vpos.y)
        self.vel_x *= 0.94
        facing_id: int = 1 if self.facing_x > 0 else 0
        self.image = f"scooterboy_bike_{facing_id}_{min(self.frame // 30, 2)}_{self.colour_variant}"

    @override
    def get_draw_order_offset(self) -> int:
        return -1


class Weapon(ScrollHeightActor):
    __slots__ = (
        "name",
        "end_pickup_frame",
        "held",
        "vel",
        "bounciness",
        "ground_friction",
        "air_friction",
    )

    def __init__(
        self,
        name: str,
        sprite: str,
        pos: PointLike,
        end_pickup_frame: int,
        anchor: Anchor = ANCHOR_CENTRE,
        bounciness: float = 0,
        ground_friction: float = 0.5,
        air_friction: float = 0.996,
        separate_shadow: bool = False,
    ) -> None:
        super().__init__(
            sprite, pos, anchor=anchor, separate_shadow=separate_shadow
        )
        self.name: str = name
        self.end_pickup_frame: int = end_pickup_frame
        self.held: bool = False
        self.vel: Vector = Vector(0, 0)
        self.bounciness: float = bounciness
        self.ground_friction: float = ground_friction
        self.air_friction: float = air_friction

    def update(self) -> None:
        if not self.held:
            # If not held, check whether we're above the ground, or if we're moving
            if self.height_above_ground > 0 or self.vel.y != 0:
                # Fall to ground
                self.vel = Vector(self.vel.x, self.vel.y + WEAPON_GRAVITY)
                if self.vel.y > self.height_above_ground:
                    # Bounce if we have bounciness, but stop bouncing if Y velocity is low
                    if self.bounciness > 0 and self.vel.y > 1:
                        # eg bounciness 1, height_above_ground 10, vel y 15, bounce amount should be 5
                        self.height_above_ground = (
                            abs(self.height_above_ground - self.vel.y)
                            * self.bounciness
                        )
                        self.vel = Vector(
                            self.vel.x, -self.vel.y * self.bounciness
                        )
                    else:
                        self.height_above_ground = 0
                        self.vel = Vector(self.vel.x, 0)
                else:
                    # Didn't bounce - apply velocity to Y pos
                    self.height_above_ground -= self.vel.y

                assert self.height_above_ground >= 0

            self.vpos = Vector(self.vpos.x + self.vel.x, self.vpos.y)

            # Friction on X axis, varies depending on whether we're on the ground or in the air
            friction: float = (
                self.ground_friction
                if self.height_above_ground == 0
                else self.air_friction
            )
            self.vel = Vector(self.vel.x * friction, self.vel.y)
            if abs(self.vel.x) < 0.05:
                self.vel = Vector(0, self.vel.y)

    def can_be_picked_up(self) -> bool:
        return not self.held and self.height_above_ground == 0

    def pick_up(self, hold_height: float) -> None:
        assert not self.held
        self.held = True
        self.height_above_ground = hold_height  # for when we are dropped
        self.vel = Vector(0, 0)
        self.image = "blank"

    def dropped(self) -> None:
        # Subclass has the responsibility of setting image to the correct sprite
        assert self.held
        self.held = False

    def used(self) -> None:
        pass

    def is_broken(self) -> bool:
        return False


class Barrel(Weapon):
    __slots__ = ("last_thrower", "frame")

    def __init__(self, pos: PointLike) -> None:
        super().__init__(
            "barrel",
            "barrel_upright",
            pos,
            end_pickup_frame=2,
            anchor=("center", 190),
            bounciness=0.75,
            ground_friction=0.96,
            separate_shadow=True,
        )
        self.last_thrower: Fighter | None = None
        self.frame: int = 0

    @override
    def update(self) -> None:
        # Call parent update
        super().update()

        # If moving, look for people to bash into
        # Won't collide if it can be picked up (if it is moving slowly enough)
        if not self.held and not self.can_be_picked_up() and self.vel.x != 0:
            fighters: list[Fighter] = [game.player, *game.enemies]
            for fighter in fighters:
                # Won't collide with the person who threw it
                # Won't collide with a fighter who is falling (incl. lying on the ground)
                # Must be within 30 pixels on X axis
                # Must be within 30 pixels on Y axis (vpos.y doesn't take height above ground into account, so this
                # is effectively the character's 'depth' in the level)
                # Must hit within the height of the character, taking into account height_above_ground for both the
                # barrel and fighter. The fighter may be able to jump over the barrel. The Y anchor of fighter sprites
                # is at the feet and the Y anchor of the barrel is at its centre.
                # The barrel isn't able to bounce above the head of a fighter (unless we added a really short fighter),
                # so we don't need to check that
                barrel_height: int = 40
                fighter_bottom_height: float = fighter.height_above_ground
                barrel_bottom_height: float = self.height_above_ground - (
                    barrel_height // 2
                )
                barrel_top_height: float = barrel_bottom_height + barrel_height

                if (
                    fighter is not self.last_thrower
                    and fighter.falling_state == Fighter.FallingState.STANDING
                    and abs(fighter.vpos.y - self.vpos.y) < 30
                    and abs(self.vpos.x - fighter.vpos.x) < 30
                    and fighter_bottom_height < barrel_top_height
                ):
                    fighter.hit(self, ATTACKS["barrel"])

            # Update rolling animation
            facing_id: int = 1 if self.vel.x > 0 else 0
            self.frame += 1
            self.image = f"barrel_roll_{facing_id}_{(self.frame // 14) % 4}"

    def throw(self, dir_x: int, thrower: Fighter) -> None:
        self.dropped()
        self.vel = Vector(dir_x * BARREL_THROW_VEL_X, BARREL_THROW_VEL_Y)
        self.last_thrower = thrower

        # Shift position for throw animation
        self.vpos = Vector(self.vpos.x + dir_x * 104, self.vpos.y)

    @override
    def dropped(self) -> None:
        super().dropped()
        self.image = "barrel_roll_0_0"

    @override
    def can_be_picked_up(self) -> bool:
        return super().can_be_picked_up() and self.vel.magnitude() < 1

    @override
    def get_draw_order_offset(self) -> int:
        # Consider barrel to be in front of another object with the same Y pos
        # (including player which has draw offset of 1)
        return 2


class BreakableWeapon(Weapon, ABC):
    __slots__ = ("break_counter",)

    def __init__(self, pos: PointLike, name: str, durability: int) -> None:
        super().__init__(
            name, name, pos, end_pickup_frame=1, anchor=("center", "center")
        )
        self.break_counter: int = durability

    @override
    def dropped(self) -> None:
        super().dropped()
        self.image = self.name

    @override
    def get_draw_order_offset(self) -> int:
        # Used for stick/chain on ground. Default draw order means it is sometimes drawn on top of a character standing on
        # it, but changing Y anchor point also has some undesirable effects
        return -50

    @override
    def used(self) -> None:
        self.break_counter -= 1
        if self.break_counter == 0:
            self.on_break()

    @override
    def is_broken(self) -> bool:
        return self.break_counter <= 0

    @abstractmethod
    def on_break(self) -> None:
        # Can't call this break as that's a keyword in Python!
        ...


class Stick(BreakableWeapon):
    __slots__ = ()

    def __init__(self, pos: PointLike) -> None:
        super().__init__(pos, "stick", durability=randint(12, 16))

    @override
    def on_break(self) -> None:
        game.play_sound("stick_break")


class Chain(BreakableWeapon):
    __slots__ = ()

    def __init__(self, pos: PointLike) -> None:
        super().__init__(pos, "chain", durability=randint(18, 25))

    @override
    def on_break(self) -> None:
        game.play_sound("chain_break")


class Powerup(ScrollHeightActor, ABC):
    __slots__ = ("collected",)

    def __init__(self, pos: PointLike, image: str) -> None:
        super().__init__(image, pos)
        self.collected: bool = False

    def update(self) -> None:
        pass

    @abstractmethod
    def collect(self, collector: Player) -> None:
        self.collected = True


class HealthPowerup(Powerup):
    __slots__ = ()

    def __init__(self, pos: PointLike) -> None:
        super().__init__(pos, "health_pickup")

    @override
    def collect(self, collector: Player) -> None:
        super().collect(collector)

        # Add 20 health to the player who collected us, but don't go over their max health
        collector.health = min(collector.health + 20, collector.start_health)

        game.play_sound("health", 1)


class ExtraLifePowerup(Powerup):
    __slots__ = ("timer",)

    def __init__(self, pos: PointLike) -> None:
        super().__init__(pos, "ingame_life9")
        self.timer: int = 0

    @override
    def update(self) -> None:
        super().update()
        self.timer += 1
        self.image = f"ingame_life{(self.timer // 2) % 10}"

    @override
    def collect(self, collector: Player) -> None:
        super().collect(collector)

        collector.gain_extra_life()

        game.play_sound("health", 1)


# A stage consists of a group of enemies and a level X boundary. When the enemies are
# defeated, the next stage begins
@dataclass(eq=False, slots=True)
class Stage:
    enemies: list[Enemy]
    max_scroll_x: int
    weapons: list[Weapon] = field(default_factory=list)
    powerups: list[Powerup] = field(default_factory=list)


#: Built by setup_stages when a game starts (the enemies are live objects, so a
#: new game needs a fresh set)
STAGES: tuple[Stage, ...]


def setup_stages() -> None:
    global STAGES
    STAGES = (
        Stage(max_scroll_x=300, enemies=[EnemyVax(pos=(1000, 400))]),
        Stage(
            max_scroll_x=600,
            enemies=[EnemyVax(pos=(1400, 400)), EnemyHoodie(pos=(1500, 500))],
            weapons=[Barrel((1600, 400))],
        ),
        Stage(max_scroll_x=600, enemies=[EnemyScooterboy(pos=(200, 400))]),
        Stage(
            max_scroll_x=900,
            enemies=[EnemyBoss(pos=(1800, 400)), EnemyVax(pos=(400, 400))],
        ),
        Stage(
            max_scroll_x=1400,
            enemies=[
                EnemyHoodie(pos=(2100, 380)),
                EnemyHoodie(pos=(2100, 480)),
                EnemyHoodie(pos=(800, 420)),
            ],
            powerups=[HealthPowerup(pos=(2300, MIN_WALK_Y))],
        ),
        Stage(
            max_scroll_x=1900,
            enemies=[
                EnemyVax(pos=(2400, 380)),
                EnemyHoodie(pos=(2500, 480)),
                EnemyScooterboy(pos=(2800, 400)),
            ],
        ),
        Stage(
            max_scroll_x=2500,
            enemies=[
                EnemyScooterboy(pos=(3800, 380)),
                EnemyScooterboy(pos=(3300, 480)),
                EnemyScooterboy(pos=(1200, 400)),
            ],
        ),
        Stage(
            max_scroll_x=3000,
            enemies=[
                EnemyVax(pos=(4000, 380)),
                EnemyVax(pos=(3900, 480)),
                EnemyVax(pos=(4200, 460)),
                EnemyVax(pos=(4200, 450)),
                EnemyHoodie(pos=(3900, 300)),
                EnemyHoodie(pos=(3950, 320)),
            ],
        ),
        Stage(
            max_scroll_x=3600,
            enemies=[
                EnemyVax(pos=(4600, 380)),
                EnemyScooterboy(pos=(1200, 350)),
                EnemyScooterboy(pos=(1400, 350)),
                EnemyScooterboy(pos=(1600, 350)),
                EnemyScooterboy(pos=(1800, 350)),
                EnemyScooterboy(pos=(2000, 350)),
            ],
            powerups=[HealthPowerup(pos=(5100, MIN_WALK_Y))],
        ),
        Stage(
            max_scroll_x=4600,
            enemies=[
                EnemyHoodie(pos=(4800, 380)),
                EnemyHoodie(pos=(4800, 350)),
                EnemyScooterboy(pos=(1200, 350)),
                EnemyScooterboy(pos=(1400, 350)),
                EnemyScooterboy(pos=(4800, 350)),
                EnemyScooterboy(pos=(4800, 400)),
                EnemyScooterboy(pos=(4900, 450)),
            ],
        ),
        Stage(
            max_scroll_x=5500,
            enemies=[EnemyBoss(pos=(6500, 380)), EnemyBoss(pos=(6500, 360))],
            weapons=[Barrel(pos=(6000, 400)), Barrel(pos=(5900, 370))],
        ),
        Stage(
            max_scroll_x=6400,
            enemies=[
                EnemyBoss(pos=(7000, 380)),
                EnemyBoss(pos=(7000, 360)),
                EnemyBoss(pos=(7000, 390)),
            ],
            weapons=[Barrel(pos=(7000, 380))],
        ),
        Stage(
            max_scroll_x=6900,
            enemies=[
                EnemyVax(pos=(7500, 380)),
                EnemyScooterboy(pos=(7500, 350)),
                EnemyScooterboy(pos=(7500, 360)),
            ],
        ),
        Stage(
            max_scroll_x=7550,
            enemies=[
                EnemyHoodie(pos=(8000, 380), start_timer=50),
                EnemyVax(pos=(8200, 340), start_timer=100),
                EnemyHoodie(pos=(8200, 340), start_timer=150),
                EnemyHoodie(pos=(7900, 360), start_timer=200),
                EnemyHoodie(pos=(8300, 390), start_timer=250),
                EnemyVax(pos=(8700, 400), start_timer=300),
                EnemyHoodie(pos=(8800, 400), start_timer=400),
                EnemyHoodie(pos=(8900, 400), start_timer=500),
                EnemyVax(pos=(9000, 320), start_timer=600),
                EnemyVax(pos=(9100, 400), start_timer=700),
                EnemyHoodie(pos=(9100, 450), start_timer=800),
                EnemyVax(pos=(9100, 420), start_timer=900),
                EnemyBoss(pos=(9100, 450), start_timer=1000),
            ],
            powerups=[
                HealthPowerup(pos=(8000, MIN_WALK_Y)),
                ExtraLifePowerup(pos=(8200, MIN_WALK_Y)),
            ],
        ),
        Stage(
            max_scroll_x=8400,
            enemies=[
                EnemyPortal(
                    pos=(8900, 400),
                    enemies=(EnemyVax, EnemyHoodie),
                    spawn_interval=120,
                    spawn_interval_change=30,
                    max_spawn_interval=250,
                    max_enemies=2,
                ),
            ],
        ),
        Stage(
            max_scroll_x=8900,
            enemies=[
                EnemyPortal(
                    pos=(9500, 400),
                    enemies=(EnemyVax, EnemyHoodie),
                    spawn_interval=120,
                    spawn_interval_change=50,
                    max_spawn_interval=250,
                    max_enemies=5,
                ),
                EnemyPortal(
                    pos=(9500, 400),
                    enemies=(EnemyScooterboy,),
                    spawn_interval=160,
                    spawn_interval_change=50,
                    max_spawn_interval=250,
                    max_enemies=5,
                ),
            ],
        ),
        Stage(
            max_scroll_x=9600,
            enemies=[
                EnemyPortal(
                    pos=(10000, 420),
                    enemies=(EnemyVax, EnemyHoodie),
                    spawn_interval=120,
                    spawn_interval_change=50,
                    max_spawn_interval=250,
                    max_enemies=5,
                ),
                EnemyScooterboy(pos=(10500, 320)),
                EnemyScooterboy(pos=(10500, 350)),
                EnemyScooterboy(pos=(10500, 380)),
            ],
        ),
        Stage(
            max_scroll_x=10800,
            enemies=[
                EnemyPortal(
                    pos=(11200, 420),
                    enemies=(EnemyHoodie,),
                    spawn_interval=40,
                    spawn_interval_change=10,
                    max_spawn_interval=250,
                    max_enemies=8,
                ),
            ],
        ),
        Stage(
            max_scroll_x=11400,
            enemies=[
                EnemyPortal(
                    pos=(12100, 340),
                    enemies=(EnemyScooterboy,),
                    spawn_interval=40,
                    spawn_interval_change=20,
                    max_spawn_interval=250,
                    max_enemies=8,
                ),
                EnemyPortal(
                    pos=(11900, 400),
                    enemies=(EnemyScooterboy,),
                    spawn_interval=50,
                    spawn_interval_change=25,
                    max_spawn_interval=250,
                    max_enemies=8,
                ),
            ],
            weapons=[Barrel(pos=(11800, 380))],
            powerups=[
                HealthPowerup(pos=(12000, MIN_WALK_Y)),
                HealthPowerup(pos=(12500, MIN_WALK_Y)),
            ],
        ),
        Stage(
            max_scroll_x=12600,
            enemies=[
                EnemyPortal(
                    pos=(12900, 340),
                    enemies=(EnemyBoss,),
                    spawn_interval=240,
                    spawn_interval_change=20,
                    max_spawn_interval=300,
                    max_enemies=4,
                ),
                EnemyHoodie(pos=(13200, 320)),
                EnemyHoodie(pos=(13200, 330)),
                EnemyVax(pos=(13400, 360)),
            ],
        ),
        Stage(
            max_scroll_x=13400,
            enemies=[
                EnemyPortal(
                    pos=(13600, 320),
                    enemies=(EnemyVax,),
                    spawn_interval=230,
                    spawn_interval_change=20,
                    max_spawn_interval=300,
                    max_enemies=10,
                ),
                EnemyPortal(
                    pos=(13600, 435),
                    enemies=(EnemyHoodie,),
                    spawn_interval=240,
                    spawn_interval_change=20,
                    max_spawn_interval=300,
                    max_enemies=10,
                ),
                EnemyPortal(
                    pos=(14000, 320),
                    enemies=(EnemyScooterboy,),
                    spawn_interval=250,
                    spawn_interval_change=30,
                    max_spawn_interval=300,
                    max_enemies=10,
                ),
                EnemyPortal(
                    pos=(14000, 435),
                    enemies=(EnemyBoss,),
                    spawn_interval=260,
                    spawn_interval_change=30,
                    max_spawn_interval=300,
                    max_enemies=10,
                ),
            ],
        ),
        Stage(
            max_scroll_x=14700,
            enemies=[
                EnemyPortal(
                    pos=(14900, 320),
                    enemies=(EnemyVax,),
                    spawn_interval=220,
                    spawn_interval_change=20,
                    max_spawn_interval=300,
                    max_enemies=8,
                ),
                EnemyPortal(
                    pos=(14900, 435),
                    enemies=(EnemyHoodie,),
                    spawn_interval=230,
                    spawn_interval_change=20,
                    max_spawn_interval=300,
                    max_enemies=8,
                ),
                EnemyPortal(
                    pos=(15300, 320),
                    enemies=(EnemyScooterboy,),
                    spawn_interval=240,
                    spawn_interval_change=20,
                    max_spawn_interval=300,
                    max_enemies=8,
                ),
                EnemyPortal(
                    pos=(15300, 435),
                    enemies=(EnemyBoss,),
                    spawn_interval=250,
                    spawn_interval_change=20,
                    max_spawn_interval=300,
                    max_enemies=8,
                ),
            ],
            powerups=[
                HealthPowerup(pos=(14650, 350)),
            ],
        ),
        Stage(
            max_scroll_x=15400,
            enemies=[
                EnemyPortal(
                    pos=(15800, 350),
                    enemies=(EnemyVax, EnemyHoodie, EnemyScooterboy),
                    spawn_interval=60,
                    spawn_interval_change=20,
                    max_spawn_interval=300,
                    max_enemies=8,
                ),
            ],
            powerups=[
                HealthPowerup(pos=(16000, MIN_WALK_Y)),
            ],
        ),
        Stage(
            max_scroll_x=16600,
            enemies=[
                EnemyVax(pos=(17600, 300)),
                EnemyVax(pos=(17900, 320)),
                EnemyVax(pos=(17600, 340)),
                EnemyVax(pos=(17900, 360)),
                EnemyVax(pos=(17600, 380)),
                EnemyVax(pos=(17900, 400)),
                EnemyVax(pos=(17600, 420)),
            ],
            powerups=[
                HealthPowerup(pos=(17000, MIN_WALK_Y)),
            ],
            weapons=[Barrel(pos=(17000, 380))],
        ),
        Stage(
            max_scroll_x=17400,
            enemies=[
                EnemyBoss(pos=(17800, MIN_WALK_Y)),
                EnemyScooterboy(pos=(18500, 380)),
                EnemyScooterboy(pos=(18600, 380)),
                EnemyScooterboy(pos=(18700, 380)),
                EnemyScooterboy(pos=(18800, 380)),
                EnemyScooterboy(pos=(19000, 380)),
            ],
            weapons=[Stick(pos=(18000, 340))],
        ),
        Stage(
            max_scroll_x=18500,
            enemies=[
                EnemyBoss(pos=(18800, 320)),
                EnemyPortal(
                    pos=(18900, 390),
                    enemies=(EnemyVax, EnemyHoodie),
                    start_timer=400,
                    spawn_interval=30,
                    spawn_interval_change=5,
                    max_enemies=10,
                ),
            ],
        ),
        Stage(
            max_scroll_x=19300,
            enemies=[EnemyScooterboy(pos=(19900, 340))],
            weapons=[Barrel(pos=(19400, 340))],
            powerups=[
                HealthPowerup(pos=(19600, MIN_WALK_Y)),
            ],
        ),
        # Final battles
        Stage(
            max_scroll_x=20500,
            enemies=[
                EnemyHoodie(pos=(20900, 380), start_timer=500),
                EnemyBoss(pos=(21500, 330)),
                EnemyBoss(pos=(21500, 350)),
                EnemyBoss(pos=(21500, 370)),
                EnemyBoss(pos=(21500, 390)),
                EnemyBoss(pos=(18200, 320)),
                EnemyBoss(pos=(17800, 390)),
            ],
            powerups=[ExtraLifePowerup(pos=(20900, MIN_WALK_Y))],
        ),
        Stage(
            max_scroll_x=20500,
            enemies=[
                EnemyPortal(
                    pos=(20700, 315),
                    enemies=(EnemyVax,),
                    start_timer=600,
                    spawn_interval=60,
                    spawn_interval_change=5,
                    max_enemies=20,
                ),
                EnemyPortal(
                    pos=(20700, 440),
                    enemies=(EnemyHoodie,),
                    start_timer=600,
                    spawn_interval=60,
                    spawn_interval_change=10,
                    max_enemies=20,
                ),
                EnemyPortal(
                    pos=(21100, 315),
                    enemies=(EnemyScooterboy,),
                    start_timer=600,
                    spawn_interval=60,
                    spawn_interval_change=15,
                    max_enemies=20,
                ),
                EnemyPortal(
                    pos=(21100, 440),
                    enemies=(EnemyBoss,),
                    start_timer=600,
                    spawn_interval=60,
                    spawn_interval_change=20,
                    max_enemies=20,
                ),
            ],
        ),
    )


@dataclass(eq=False, slots=True)
class Game:
    #: The input that started the game (there is always a player)
    controls: InitVar[Controls]
    player: Player = field(init=False)
    enemies: list[Enemy] = field(default_factory=list, init=False)
    weapons: list[Weapon] = field(default_factory=list, init=False)
    scooters: list[Scooter] = field(default_factory=list, init=False)
    powerups: list[Powerup] = field(default_factory=list, init=False)
    stage_index: int = field(default=-1, init=False)
    timer: int = field(default=0, init=False)
    score: int = field(default=0, init=False)
    #: How far the level has scrolled; the world position of the screen's left edge
    scroll_offset: Vector = field(
        default_factory=lambda: Vector(0, 0), init=False
    )
    max_scroll_offset_x: int = field(default=0, init=False)
    scrolling: bool = field(default=False, init=False)
    #: Where fighters may walk, in world space; scrolling moves it right
    boundary: Rect = field(init=False)
    #: Showing the intro or outro text
    text_active: bool = field(default=INTRO_ENABLED, init=False)
    intro_text: str = field(init=False)
    outro_text: str = field(init=False)
    current_text: str = field(init=False)
    #: The teletyped prefix of current_text shown so far
    displayed_text: str = field(default="", init=False)

    def __post_init__(self, controls: Controls) -> None:
        self.player = Player(controls)

        self.boundary = Rect(0, MIN_WALK_Y, WIDTH - 1, HEIGHT - MIN_WALK_Y)

        setup_stages()

        # Set up intro text, selecting randomly from one of several stolen items
        stolen_items: tuple[str, ...] = (
            "A SHIPMENT OF RASPBERRY\nPIS",
            "YOUR COPY OF CODE THE\nCLASSICS VOL 2",
            "THE COMPLETE WORKS OF\nSHAKESPEARE",
            "THE BLOCKCHAIN",
            "THE WORLD'S ENTIRE SUPPLY\nOF COVID VACCINES",
            "ALL OF YOUR SAVED GAME\nFILES",
            "YOUR DOG'S FLEA MEDICINE",
        )

        self.intro_text = (
            "THE NOTORIOUS CRIME BOSS\nEBEN UPTON HAS STOLEN\n"
            + choice(stolen_items)
            + "\n\n\nFIGHT TO RECLAIM WHAT\nHAS BEEN TAKEN!"
        )
        self.outro_text = (
            "FOLLOWING THE DEFEAT OF\n"
            "THE EVIL GANG, HUMANITY\n"
            "ENTERED A NEW GOLDEN AGE\n"
            "IN WHICH CRIME BECAME A\n"
            "THING OF THE PAST. THE\n"
            "WORD ITSELF WAS SOON\n"
            "FORGOTTEN AND EVERYONE\n"
            "HAD A BIG PARTY IN YOUR\n"
            "HONOUR.\n"
            "\nNICE JOB!"
        )
        self.current_text = self.intro_text

    def next_stage(self) -> None:
        # A stage is over when we've scrolled to its max_scroll_x and there are no enemies left
        # Enemies are created when we start scrolling (or here, if no scrolling is to take place or is already taking place)
        self.stage_index += 1
        if self.stage_index < len(STAGES):
            stage: Stage = STAGES[self.stage_index]
            self.max_scroll_offset_x = stage.max_scroll_x
            if (
                self.scrolling
                or self.max_scroll_offset_x <= self.scroll_offset.x
            ):
                # No scrolling or already scrolling - create stage objects
                self.create_stage_objects(stage)
        else:
            # If stage_index has reached len(STAGES), we go into the outro state (like intro text, but with different text)
            # After that, check_won() will return True and the game state code will pick up on this and end the game
            if not self.text_active:
                self.text_active = True
                self.current_text = self.outro_text
                self.displayed_text = ""
                self.timer = 0

    def check_won(self) -> bool:
        # Have we been through all stages, and has the outro text finished?
        return self.stage_index >= len(STAGES) and not self.text_active

    def create_stage_objects(self, stage: Stage) -> None:
        # Copy the enemies list from the stage, and tell them that they've been spawned
        self.enemies = stage.enemies.copy()
        for enemy in self.enemies:
            enemy.spawned()

        # Add the weapons and powerups from the stage to the game
        self.weapons.extend(stage.weapons)
        self.powerups.extend(stage.powerups)

    def spawn_enemy(self, enemy: Enemy) -> None:
        # Called by Portal
        self.enemies.append(enemy)
        enemy.spawned()

    def update(self) -> None:
        if DEBUG_PROFILING:
            p: Profiler = Profiler()

        self.timer += 1

        if self.text_active:
            # Every 6 frames, update the displayed text to display an extra character, and make a sound if the
            # new character is visible (as opposed to a space or new line)
            if self.timer % 6 == 0 and len(self.displayed_text) < len(
                self.current_text
            ):
                length_to_display: int = min(
                    self.timer // 6, len(self.current_text)
                )
                self.displayed_text = self.current_text[:length_to_display]
                if not self.displayed_text[-1].isspace():
                    self.play_sound("teletype")

            # Allow player to skip/leave text
            for button in range(4):
                if self.player.controls.button_pressed(button):
                    self.text_active = False
                    self.timer = 0

            return

        if DEBUG_SHOW_ATTACKS:
            debug_drawcalls.clear()

        # Update all objects
        objects: list[ScrollObject] = [
            self.player,
            *self.enemies,
            *self.weapons,
            *self.scooters,
            *self.powerups,
        ]
        for obj in objects:
            obj.update()

        if self.scrolling:
            if self.scroll_offset.x < self.max_scroll_offset_x:
                # How far are we from reaching the new max scroll offset?
                diff: float = float(
                    self.max_scroll_offset_x - self.scroll_offset.x
                )
                # Scroll at 1-4px per frame depending on player's distance from right edge
                scroll_speed: float = min(diff, self.player.x / (WIDTH / 4))
                self.scroll_offset = Vector(
                    self.scroll_offset.x + scroll_speed, self.scroll_offset.y
                )
                # (moving boundary.left moves the whole rect)
                self.boundary.left = float(self.scroll_offset.x)
            else:
                # Scrolling is complete
                self.scrolling = False
        else:
            # Start scrolling if player is near right hand edge of screen and max_scroll_offset_x allows to to scroll
            begin_scroll_boundary: int = WIDTH - 300
            if (
                self.player.vpos.x - self.scroll_offset.x
                > begin_scroll_boundary
                and self.scroll_offset.x < self.max_scroll_offset_x
            ):
                self.scrolling = True

                # When we start scrolling, create enemies for the current stage
                if self.stage_index < len(STAGES):
                    self.create_stage_objects(STAGES[self.stage_index])

        # Remove expired enemies and gain score
        self.score += sum(
            enemy.score for enemy in self.enemies if enemy.lives <= 0
        )
        self.enemies = [enemy for enemy in self.enemies if enemy.lives > 0]

        # Remove expired scooters
        self.scooters = [
            scooter for scooter in self.scooters if scooter.frame < 200
        ]

        # Remove broken weapons and ones which are off the left of the screen
        self.weapons = [
            weapon
            for weapon in self.weapons
            if not weapon.is_broken() and weapon.x > -200
        ]

        # Remove collected powerups, and ones off the left of the screen
        self.powerups = [
            powerup
            for powerup in self.powerups
            if not powerup.collected and powerup.x > -200
        ]

        # If no enemies and we've fully scrolled to the current stage's max_scroll_x, start the next stage
        if (
            not self.enemies
            and self.scroll_offset.x == self.max_scroll_offset_x
        ):
            self.next_stage()

        if DEBUG_PROFILING:
            print(f"update: {p.get_ms()}")

    def draw(self) -> None:
        # Draw background
        self.draw_background()

        # Draw all objects, lowest on screen first
        # Y pos used is modified by result of get_draw_order_offset, for certain cases where we need more nuance than
        # just "lowest on screen first"
        p: Profiler = Profiler()
        all_objs: list[ScrollObject] = [
            self.player,
            *self.enemies,
            *self.weapons,
            *self.scooters,
            *self.powerups,
        ]
        all_objs.sort(key=lambda obj: obj.vpos.y + obj.get_draw_order_offset())
        for obj in all_objs:
            obj.draw_at(self.scroll_offset)
        if DEBUG_PROFILING:
            print(f"objs: {p.get_ms()}")

        p = Profiler()

        # If player can scroll the level, show flashing arrow
        if (
            self.scroll_offset.x < self.max_scroll_offset_x
            and (self.timer // 30) % 2 == 0
        ):
            blit("arrow", WIDTH - 450, 120)

        self.draw_ui()

        if DEBUG_PROFILING:
            print(f"icons: {p.get_ms()}")
            p = Profiler()

        # During the intro we show a black background, immediately after the intro we fade it away
        # Draw a black image with gradually decreasing opacity
        # An alpha value of 255 is fully opaque, 0 is fully transparent
        # (fill resets the surface to opaque black, then set_alpha scales its alpha down to the fade level)
        if self.text_active or self.timer < 255:
            alpha: int = 255 if self.text_active else max(0, 255 - self.timer)
            fullscreen_black_bmp.fill((0, 0, 0, 255))
            fullscreen_black_bmp.set_alpha(alpha)
            renderer.draw_image(fullscreen_black_bmp, (0, 0))

        # Show intro text
        if self.text_active:
            draw_text(self.displayed_text, 50, 50)

        # Debug
        if DEBUG_SHOW_SCROLL_POS:
            draw_system_text(
                f"{self.scroll_offset} {self.max_scroll_offset_x}", 0, 25
            )
            draw_system_text(str(self.boundary.left), 0, 45)

        if DEBUG_SHOW_BOUNDARY:
            renderer.rect(
                self.boundary.left - float(self.scroll_offset.x),
                self.boundary.top,
                self.boundary.width,
                self.boundary.height,
                (255, 255, 255),
            )

        # If there are any debug draw calls, execute them - used by DEBUG_SHOW_ATTACKS
        for func in debug_drawcalls:
            func()

        if DEBUG_PROFILING:
            # Show profiler timing for everything not in another category
            print(f"rest: {p.get_ms()}")

    def draw_ui(self) -> None:
        # Show status bar and player health, stamina and lives. The bars are the left part of their images, cut to
        # the current fraction
        health_bar_w: int = int(
            (self.player.health / self.player.start_health)
            * HEALTH_STAMINA_BAR_WIDTH
        )
        renderer.draw_image_region(
            images.load("health"),
            (48, 11),
            IntRect(0, 0, health_bar_w, HEALTH_STAMINA_BAR_HEIGHT),
        )
        stamina_bar_w: int = int(
            (self.player.stamina / self.player.max_stamina)
            * HEALTH_STAMINA_BAR_WIDTH
        )
        renderer.draw_image_region(
            images.load("stamina"),
            (517, 11),
            IntRect(0, 0, stamina_bar_w, HEALTH_STAMINA_BAR_HEIGHT),
        )

        blit("status", 0, 0)

        # Lives; a newly gained one animates in
        for i in range(self.player.lives):
            sprite_idx: int = (
                9
                if self.player.extra_life_timer <= 0
                or i < self.player.lives - 1
                else min(9, (30 - self.player.extra_life_timer) // 3)
            )
            blit(f"status_life{sprite_idx}", i * 46 - 55, -35)

        # Show score
        draw_text(f"{self.score:04}", WIDTH // 2, 0, True)

    def draw_background(self) -> None:
        # Draw two copies of road background
        p: Profiler = Profiler()
        road1_x: float = -(float(self.scroll_offset.x) % WIDTH)
        blit("road", road1_x, 0)
        blit("road", road1_x + WIDTH, 0)
        if DEBUG_PROFILING:
            print(f"road {p.get_ms()}")

        # Set initial position for background tiles
        # Due to isometric nature of background, each background tile includes a transparent part - the second line
        # skips that part for the first tile
        pos: Vector = -self.scroll_offset
        pos = Vector(pos.x - BACKGROUND_TILE_SPACING, pos.y)

        # Draw background tiles
        p = Profiler()
        for tile in BACKGROUND_TILES:
            # Don't bother drawing tile if it's off the left of the screen
            visible: bool = pos.x + 417 >= 0
            if visible:
                blit(tile, *xy(pos))
            pos = Vector(pos.x + BACKGROUND_TILE_SPACING, pos.y)
            if visible and pos.x >= WIDTH:
                # Stop once we've reached or gone past the right edge of the screen
                break
        if DEBUG_PROFILING:
            print(f"bg {p.get_ms()}")

    def shutdown(self) -> None:
        # When the game is over, tell the enemies they died (upstream needed this to stop the scooter engine
        # sound; a dying enemy may also drop its weapon, so a finished game's state is left as it was)
        for enemy in self.enemies:
            enemy.died()

    def play_sound(self, name: str, count: int = 1) -> None:
        # Some sounds have multiple varieties, named "name0", "name1", ... If count > 1, we'll randomly choose one
        try:
            sounds.load(f"{name}{randint(0, count - 1)}").play()
        except Exception as e:
            # If no sound file of that name was found, print the error, which includes the filename.
            # Also occurs if sound fails to play for another reason (e.g. if this machine has no sound hardware)
            print(e)


# From Eggzy
def get_char_image_and_width(char: str) -> tuple[Image | None, int]:
    # Return the image and width of the given character. ord() gives the Unicode code for the given character; the
    # controller button symbols have their own images
    if char == " ":
        return None, 22
    image: Image = images.load(
        SPECIAL_FONT_SYMBOLS_INVERSE.get(char, f"font0{ord(char)}")
    )
    return image, image.width


def text_width(text: str) -> int:
    return sum(get_char_image_and_width(c)[1] for c in text)


def draw_text(text: str, x: int, y: int, centre: bool = False) -> None:
    # Note that the centre option does not work correctly for text with line breaks
    if centre:
        x -= text_width(text) // 2

    start_x: int = x

    for char in text:
        if char == "\n":
            # New line
            y += 35
            x = start_x
        else:
            image, width = get_char_image_and_width(char)
            if image is not None:
                renderer.draw_image(image, (x, y))
            x += width


# Set up controls
joystick_controls: JoystickControls | None


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
    CONTROLS = 2
    PLAY = 3
    GAME_OVER = 4


def update() -> None:
    global state, game, total_frames

    total_frames += 1

    update_controls()

    def button_pressed_controls(button_num: int) -> Controls | None:
        # Local function for detecting button 0 being pressed on either keyboard or controller, returns the controls
        # object which was used to press it, or None if button was not pressed
        for controls in (keyboard_controls, joystick_controls):
            # Check for fire button being pressed on each controls object
            # joystick_controls will be None if there no controller was connected on game startup,
            # so must check for that
            if controls is not None and controls.button_pressed(button_num):
                return controls
        return None

    match state:
        case State.TITLE:
            # Check for start game
            if button_pressed_controls(0) is not None:
                state = State.CONTROLS

        case State.CONTROLS:
            # Check for player starting game with either keyboard or controller
            controls: Controls | None = button_pressed_controls(0)
            if controls is not None:
                # Switch to play state, and create a new Game object, passing it the controls object which was used to start the game
                state = State.PLAY
                game = Game(controls)

        case State.PLAY:
            game.update()
            if game.player.lives <= 0 or game.check_won():
                # Need to call game.shutdown to turn off scooter engine sound
                game.shutdown()
                state = State.GAME_OVER

        case State.GAME_OVER:
            if button_pressed_controls(0) is not None:
                # Go back into title screen mode (the finished game lingers, untouched, until a new one
                # replaces it - the menus never look at it)
                state = State.TITLE

        case _:
            raise ValueError(f"unhandled game state {state!r}")


def draw() -> None:
    match state:
        case State.TITLE:
            # Draw logo, flashing between its two frames
            logo: Image = images.load(f"title{total_frames // 20 % 2}")
            renderer.draw_image(
                logo,
                (WIDTH // 2 - logo.width // 2, HEIGHT // 2 - logo.height // 2),
            )

            draw_text(
                f"PRESS {SPECIAL_FONT_SYMBOLS['xb_a']} OR Z",
                WIDTH // 2,
                HEIGHT - 50,
                True,
            )

        case State.CONTROLS:
            # (the frame is already cleared to black)
            blit("menu_controls", 0, 0)

        case State.PLAY:
            game.draw()

        case State.GAME_OVER:
            # Draw game over screen. Did player win or lose?
            img: Image = images.load(
                "status_win" if game.check_won() else "status_lose"
            )
            renderer.draw_image(
                img,
                (WIDTH // 2 - img.width // 2, HEIGHT // 2 - img.height // 2),
            )

        case _:
            raise ValueError(f"unhandled game state {state!r}")


##############################################################################

# Start the music (with no sound device the game simply plays silently)
music.play("theme")
music.set_volume(0.3)

total_frames: int = 0

# Set up controls
keyboard_controls: KeyboardControls = KeyboardControls()
setup_joystick_controls()

# Set the initial game state
state: State = State.TITLE

# No game object to begin with: one is created when a game starts, and nothing
# touches it on the menus (declared here, bound at the first start)
game: Game

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

# Fixed 60 Hz timestep -- beatstreets' update() takes no dt. PGZERO_MAX_FRAMES=N
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
