# Code the Classics port: leadingedge, with its rendering engine inlined.
#
# Game code derived from Raspberry Pi Press's "Code the Classics" (vol 2):
#   Copyright (c) 2024 Eben Upton <eben@raspberrypi.com>
# Inlined engine (audio, images, renderer, keyboard, loop):
#   Copyright (c) 2026 William Emerison Six
# SPDX-License-Identifier: BSD-2-Clause
# Full license text: ports/codetheclassics/LICENSE.
"""leadingedge -- a pseudo-3D racer of scaled sprites and perspective-projected
track polygons, from Code the Classics vol. 2, on GLFW + OpenGL 3.3 core.

One self-contained file, read top to bottom like the course's demos: first
the small engine this game needs (a software audio mixer with looping,
fading engine and skid sounds, an image loader with nearest-neighbour
scaling and a CPU-drawn surface for the fade, a textured-quad renderer that
also fills the frame and draws flat polygons, the anchored Actor sprite,
keyboard and gamepad state), then the game -- whose draw() projects the
track through the course's own world-to-camera transform -- then the loop
the game itself owns, which passes each frame's delta into update().
"""

from __future__ import annotations

import math
import os
import platform
import signal
import sys
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Generator, Iterator, Sequence
from dataclasses import InitVar, dataclass, field
from enum import Enum
from random import choice, randint, uniform
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, cast, override

import gacalc.g2 as g2
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

WIDTH: int = 960
HEIGHT: int = 540
TITLE: str = "Leading Edge"

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

    def fill(self, color: tuple[int, int, int]) -> None: ...

    def polygon(
        self,
        points: Sequence[PointLike],
        color: tuple[int, int, int],
        filled: bool,
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
    #: fade-in duration; consumed by __post_init__ into the ramp fields
    fade_in_ms: InitVar[float]
    #: frame offset into ``samples`` (buffer voices only)
    pos: int = field(default=0, init=False)
    #: fade_gain multiplies volume and moves by fade_step per FRAME (a fade-in
    #: ramps up to 1; a fade-out ramps down and then stops the voice)
    fade_gain: float = field(default=1.0, init=False)
    fade_step: float = field(default=0.0, init=False)
    stop_when_faded: bool = field(default=False, init=False)
    done: bool = field(default=False, init=False)

    def __post_init__(self, fade_in_ms: float) -> None:
        if fade_in_ms > 0:
            self.fade_gain = 0.0
            self.fade_step = 1.0 / (_SAMPLE_RATE * fade_in_ms / 1000.0)

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
                # a per-frame linear ramp while fading (in or out)
                ramp = v.fade_gain + v.fade_step * np.arange(
                    1, take + 1, dtype=np.float32
                )
                np.clip(ramp, 0.0, 1.0, out=ramp)
                v.fade_gain = float(ramp[-1])
                if v.fade_step > 0 and v.fade_gain >= 1.0:
                    v.fade_gain, v.fade_step = 1.0, 0.0
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
        self, samples: _PCM, volume: float, looping: bool, fade_in_ms: float
    ) -> _Voice | None:
        if not self._ensure_device():
            return None
        v = _Voice(samples, None, volume, looping, fade_in_ms)
        with self._lock:
            self._voices.append(v)
        return v

    def play_stream(
        self, stream: Iterator[Any], volume: float
    ) -> _Voice | None:
        if not self._ensure_device():
            return None
        v = _Voice(None, stream, volume, False, 0.0)
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

    def play(
        self, loops: int = 0, fade_ms: int = 0, volume: float | None = None
    ) -> None:
        """Play the effect, overlapping any prior plays; ``loops=-1`` loops it
        until :meth:`stop`; ``fade_ms`` ramps this play up from silence;
        ``volume`` overrides this effect's volume for THIS play only (the
        distance-attenuated shots)."""
        if _ma is None:
            return
        buf = self._buffer()
        if buf is None:
            return
        live = self._live()
        if len(live) >= _MAX_VOICES_PER_SOUND:
            _engine.stop_voice(live[0])  # oldest voice yields its budget
        v = _engine.play_buffer(
            buf,
            self._volume if volume is None else volume,
            looping=loops != 0,
            fade_in_ms=fade_ms,
        )
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

    def fadeout(self, time: int = 0) -> None:
        """Ramp all playing instances to silence over ``time`` ms, then stop
        them (the ramp runs per-frame inside the mixer). ``time <= 0`` stops
        immediately."""
        if time <= 0:
            self.stop()
            return
        for v in self._live():
            v.start_fadeout(time)


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


def scale_image(image: Image, width: int, height: int) -> Image:
    """A copy of ``image`` resized to ``width`` x ``height`` pixels (nearest
    neighbour, so pixel art stays crisp), as a new Image with its own texture."""
    pil = PILImage.fromarray(image.rgba).resize(
        (max(1, width), max(1, height)), PILImage.Resampling.NEAREST
    )
    return Image.from_rgba(np.array(pil.convert("RGBA")))


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

    def polygon(
        self,
        points: Sequence[PointLike],
        color: tuple[int, int, int],
        filled: bool,
    ) -> None:
        """Draw a polygon through ``points`` (a filled fan, or a one-pixel outline)."""
        verts: NDArray[np.float32] = np.array(
            [float(c) for p in points for c in p], dtype=np.float32
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
        GL.glDrawArrays(
            GL.GL_TRIANGLE_FAN if filled else GL.GL_LINE_LOOP, 0, len(points)
        )

    def fill(self, color: tuple[int, int, int]) -> None:
        """Clear the whole frame to ``color``."""
        r, g, b = color
        GL.glClearColor(r / 255.0, g / 255.0, b / 255.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

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
# each frame -- they are the only keys leadingedge reads.

_NAME_TO_KEY: dict[str, int] = {
    "left": glfw.KEY_LEFT,
    "right": glfw.KEY_RIGHT,
    "lctrl": glfw.KEY_LEFT_CONTROL,
    "z": glfw.KEY_Z,
    "lshift": glfw.KEY_LEFT_SHIFT,
    "x": glfw.KEY_X,
    "escape": glfw.KEY_ESCAPE,
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


def with_x(vector: g3.Vector, x: float) -> g3.Vector:
    """Return ``vector`` with its x coordinate replaced by ``x``."""
    return g3.Vector(x, vector.y, vector.z)


def with_z(vector: g3.Vector, z: float) -> g3.Vector:
    """Return ``vector`` with its z coordinate replaced by ``z``."""
    return g3.Vector(vector.x, vector.y, z)


# Set to True improve frame rate by turning off scenery, drawing unfilled polygons and changing the draw distance
PERFORMANCE_MODE: bool = False

if not PERFORMANCE_MODE:
    SHOW_SCENERY: bool = True
    SHOW_TRACKSIDE: bool = True
    SHOW_RUMBLE_STRIPS: bool = True
    SHOW_YELLOW_LINES: bool = True
    OUTLINE_W: int = (
        0  # Change to 1 for unfilled polygons, which are a bit faster to draw
    )
    VIEW_DISTANCE: int = 200  # This is in units of number of track pieces, try 60 for a better frame rate, try 2000 for a bad frame rate but impressive draw distance
else:
    SHOW_SCENERY = False
    SHOW_TRACKSIDE = False
    SHOW_RUMBLE_STRIPS = False
    SHOW_YELLOW_LINES = False
    OUTLINE_W = (
        1  # Change to 1 for unfilled polygons, which are a bit faster to draw
    )
    VIEW_DISTANCE = 150  # This is in units of number of track pieces, try 60 for a better frame rate, try 2000 for a bad frame rate but impressive draw distance

CLIPPING_PLANE: float = -0.25  # too close to 0 = frame rate issues (drawing huge polygons which are mostly off-screen), too far = stuff just in front of camera not being drawn
CLIPPING_PLANE_CARS: float = -0.08  # bring closer to zero to fix occasional flickering of CPU cars when very close to the camera, at the potential cost of frame rate
MAX_SCENERY_SCALED_WIDTH: int = (
    WIDTH * 2
)  # When scaling scenery based on distance from camera, don't try to draw anything that would be scaled to wider than this
MAX_CAR_SCALED_WIDTH: int = WIDTH * 1  # As above but for cars

# Constants for track
SPACING: int = 1
TRACK_W: int = 3000
HALF_STRIPE_W: int = 25
HALF_RUMBLE_STRIP_W: int = 250
HALF_YELLOW_LINE_W: int = 80
YELLOW_LINE_DISTANCE_FROM_EDGE: int = 150
type Colour = tuple[int, int, int]

TRACK_COLOUR: Colour = (35, 96, 198)
TRACKSIDE_COLOUR_1: Colour = (0, 77, 180)
TRACKSIDE_COLOUR_2: Colour = (50, 77, 170)
STRIPE_COLOUR: Colour = (70, 192, 255)
# Yes, it's actually green, not yellow. It looks yellow because it's night.
YELLOW_LINE_COL: Colour = (0, 161, 88)
RUMBLE_COLOUR_1: Colour = (0, 116, 255)
RUMBLE_COLOUR_2: Colour = (0, 58, 135)
SECTION_VERY_SHORT: int = 25
SECTION_SHORT: int = 50
SECTION_MEDIUM: int = 100
SECTION_LONG: int = 200
LAMP_X: int = TRACK_W // 2 + 300
BILLBOARD_X: int = TRACK_W // 2 + 600

CAMERA_FOLLOW_DISTANCE: int = 2

# Player car gameplay settings
LOSE_GRIP_SPEED: int = 50
ZERO_GRIP_SPEED: int = 100
PLAYER_ACCELERATION_MAX: int = 20
PLAYER_ACCELERATION_MIN: int = 10
HIGH_ACCEL_THRESHOLD: int = 30
CORNER_OFFSET_MULTIPLIER: float = 5.8  # Higher = harder to corner
STEERING_STRENGTH: int = 72  # Higher = steering has a stronger effect

# Min/max CPU car target speeds - see also track generation, some track pieces have target speed overrides set
CPU_CAR_MIN_TARGET_SPEED: int = 40
CPU_CAR_MAX_TARGET_SPEED: int = 65

NUM_LAPS: int = 5
NUM_CARS: int = 20

GRID_CAR_SPACING: float = (
    0.55  # How spaced out the cars are on the starting grid
)

# Half-width and height used during point transform, to save having to calculate them each time
HALF_WIDTH: int = WIDTH // 2
HALF_HEIGHT: int = HEIGHT // 2

# Skid sound starts fading in when grip goes below this level
SKID_SOUND_START_GRIP: float = 0.8

# Debug options
SHOW_TRACK_PIECE_INDEX: bool = False
SHOW_TRACK_PIECE_OFFSETS: bool = False
SHOW_CPU_CAR_SPEEDS: bool = False
SHOW_DEBUG_TEXT: bool = False
SHOW_PROFILE_TIMINGS: bool = False

FIXED_TIMESTEP: float = 1 / 60

# These symbols substitute for the controller button images when displaying text.
# The symbols representing these images must be ones that aren't actually used themselves, e.g. we don't use the
# percent sign in text
SPECIAL_FONT_SYMBOLS: dict[str, str] = {"xb_a": "%"}

# Create a version of SPECIAL_FONT_SYMBOLS where the keys and values are swapped
SPECIAL_FONT_SYMBOLS_INVERSE: dict[str, str] = {
    v: k for k, v in SPECIAL_FONT_SYMBOLS.items()
}

# A black image whose alpha (transparency) we vary, to fade the screen to black during the title screen
fade_to_black_image: Surface = Surface.create(WIDTH, HEIGHT, transparent=False)


def xy(v: g2.Vector) -> tuple[float, float]:
    # A screen-space vector as the pixel pair the renderer takes
    return (float(v.x), float(v.y))


# Class used for timing how long certain bits of code take to run
@dataclass(slots=True)
class Profiler:
    name: str = ""
    #: When this profiler was created
    start_time: float = field(default_factory=time.perf_counter)

    def get_ms(self) -> float:
        return (time.perf_counter() - self.start_time) * 1000

    def __str__(self) -> str:
        return f"{self.name}: {self.get_ms()}ms"


# Utility functions


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


def inverse_lerp(a: float, b: float, value: float) -> float:
    # Lerp (linear interpolate) returns the number that is 'value' between a and b, where value is a
    # number typically between 0 and 1, 0 means return a, 1 means return b, 0.5 means return a number halfway between
    # a and b, etc.
    # Inverse lerp does the opposite, returning a number which indicates where 'value' falls between a and b
    # e.g. if a is 10 and b is 20 and value is 15, it returns 0.5 as 15 is halfway between 10 and 20
    return min(1, max(0, (value - a) / (b - a))) if a != b else 0


def sign(x: float) -> int:
    # Returns 1, 0 or -1 depending on whether number is positive, zero or negative
    return 0 if x == 0 else -1 if x < 0 else 1


def move_towards(n: float, target: float, speed: float) -> float:
    return min(n + speed, target) if n < target else max(n - speed, target)


def format_time(seconds: float) -> str:
    # Return time string in the form "minutes:seconds.milliseconds"
    # 06.3f ensures that we always show 2 digits for the whole part of the seconds
    # 6 refers to the total number of characters including the decimal point
    # We want to display times like "1:05.123" not "1:5.123"
    return f"{int(seconds // 60)}:{seconds % 60:06.3f}"


def get_char_image_and_width(char: str, font: str) -> tuple[Image | None, int]:
    # Return the image and width of the given character. ord() gives the Unicode code for the given character;
    # the controller button symbols have their own images
    if char == " ":
        return None, 30
    image: Image = images.load(
        SPECIAL_FONT_SYMBOLS_INVERSE.get(char, f"{font}0{ord(char)}")
    )
    return image, image.width


TEXT_GAP_X: dict[str, int] = {
    "font": -6,
    "status1b_": 0,
    "status2_": 0,
}  # Characters in main font are italic so should overlap a little


def text_width(text: str, font: str) -> int:
    return sum(get_char_image_and_width(c, font)[1] for c in text) + TEXT_GAP_X[
        font
    ] * (len(text) - 1)


def draw_text(
    text: str, x: float, y: float, centre: bool = False, font: str = "font"
) -> None:
    if centre:
        x -= text_width(text, font) // 2

    for char in text:
        image, width = get_char_image_and_width(char, font)
        if image is not None:
            renderer.draw_image(image, (x, y))
        x += width + TEXT_GAP_X[font]


# ABC = abstract base class - a class which is only there to serve as a base class, not to be instantiated directly
class Controls(ABC):
    NUM_BUTTONS: ClassVar[int] = 2

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
    def get_x(self) -> float: ...

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
    def button_down(self, button: int) -> bool:
        # Button 0 accelerates, 1 brakes; there are no other buttons
        match button:
            case 0:
                return keyboard.lctrl or keyboard.z
            case 1:
                return keyboard.lshift or keyboard.x
            case _:
                return False


class JoystickControls(Controls):
    __slots__ = ("joystick",)

    def __init__(self, joystick: Joystick) -> None:
        super().__init__()
        self.joystick: Joystick = joystick

    def get_axis(self, axis_num: int) -> float:
        if (
            self.joystick.get_numhats() > 0
            and self.joystick.get_hat(0)[axis_num] != 0
        ):
            # For some reason, dpad up/down are inverted when getting inputs from
            # an Xbox controller, so need to negate the value if axis_num is 1
            return self.joystick.get_hat(0)[axis_num] * (
                -1 if axis_num == 1 else 1
            )

        # Analogue input, with a dead-zone
        axis_value: float = self.joystick.get_axis(axis_num)
        return 0 if abs(axis_value) < 0.6 else axis_value

    @override
    def get_x(self) -> float:
        return self.get_axis(0)

    @override
    def button_down(self, button: int) -> bool:
        # Before checking button, check to make sure that the controller actually has enough buttons
        # There are some weird devices out there which could cause a crash if this check were not present
        if self.joystick.get_numbuttons() <= button:
            print("Warning: main controller does not have enough buttons!")
            return False
        return self.joystick.get_button(button) != 0


# (eq=False on these dataclasses keeps identity comparison/hashing -- the
# generated __eq__ would compare fields and set __hash__ to None; slots=True
# fixes each object's attribute set to its declared fields)
@dataclass(eq=False, slots=True)
class Scenery:
    #: Sideways position; positive is left from the camera's point of view
    x: float
    image: Image
    #: In track pieces from the camera
    min_draw_distance: float = 0
    max_draw_distance: float = VIEW_DISTANCE // 2
    scale: float = 1
    #: Ranges of x (relative to ours) the player crashes in
    collision_zones: tuple[tuple[float, float], ...] = ()

    def get_image(self) -> Image:
        return self.image


class StartGantry(Scenery):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(
            0,
            images.load("start0"),
            min_draw_distance=1,
            max_draw_distance=VIEW_DISTANCE,
            scale=4,
            collision_zones=((-3000, -2400), (2400, 3000)),
        )

    @override
    def get_image(self) -> Image:
        # Before we draw, update our billboard image to the appropriate one based on the game's start timer
        # Images go from start0 to start4, then we alternate between start4 and start5 every half second
        index: int = (
            int(remap(game.start_timer, 4, 0, 0, 4))
            if game.start_timer > 0
            else 4
            if int(game.timer * 2) % 2 == 0
            else 5
        )
        self.image = images.load(f"start{index}")
        return self.image


class Billboard(Scenery):
    __slots__ = ()

    def __init__(self, x: float, image: Image) -> None:
        half_width: float = image.width / 2
        scale: int = 2
        super().__init__(
            x,
            image,
            scale=scale,
            collision_zones=((-half_width * scale, half_width * scale),),
        )


class LampLeft(Scenery):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(
            LAMP_X,
            images.load("left_light"),
            scale=2,
            collision_zones=((350, 1200),),
        )


class LampRight(Scenery):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(
            -LAMP_X,
            images.load("right_light"),
            scale=2,
            collision_zones=((-1200, -350),),
        )


# The track is defined as list of track pieces. A track piece is technically just a line, but a polygon will be
# drawn to connect it to the next piece. So being 'on' a track piece means being in between that track piece and the
# next one. Each track piece has X and Y offsets, which define how its position differs from the previous piece.
# When the track is drawn, the changes in offset accumulate, so that a series of track pieces with X offsets of 10
# will lead to a curve to the left, from the camera's point of view. (Left rather than right because the camera
# points along the negative Z axis)
# The X and Y offsets are the offsets from the previous track piece, so if, for example, track pieces 0 to 5 have an
# X offset of zero and track piece 6 has a very large offset of 1000, it's while moving from 5 to 6 that the car
# will start to move to the left
@dataclass(eq=False, slots=True)
class TrackPiece:
    scenery: Sequence[Scenery] = ()
    #: How this piece's position differs from the previous piece's
    offset_x: float = 0
    offset_y: float = 0
    #: CPU cars slow to this on sharp corners (None: no limit)
    cpu_max_target_speed: float | None = None
    col: Colour = TRACK_COLOUR
    width: float = TRACK_W
    #: Cars currently on this track piece
    cars: list[Car] = field(default_factory=list)


class TrackPieceStartLine(TrackPiece):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(scenery=[StartGantry()], col=(255, 255, 255))


@dataclass(eq=False, slots=True)
class Car:
    pos: g3.Vector
    #: Selects the sprite set: "a" is the player's car
    car_letter: str
    speed: float = 0
    grip: float = 1
    track_piece: TrackPiece | None = None
    tyre_rotation: float = 0
    #: The current sprite, chosen by update_sprite
    image: str = field(init=False)

    def __post_init__(self) -> None:
        self.image = f"car_{self.car_letter}_0_0"

    def update(self, delta_time: float) -> None:
        self.pos = with_z(self.pos, self.pos.z - self.speed * delta_time)
        self.update_current_track_piece()
        self.tyre_rotation += delta_time * self.speed * 0.75

    def update_current_track_piece(self) -> None:
        # Which track piece are we on?
        current_track_piece: TrackPiece | None = self.track_piece
        idx: int | None = game.get_track_piece_for_z(float(self.pos.z))
        if idx is not None:
            self.track_piece = game.track[idx]
            if self.track_piece is not current_track_piece:
                # Remove myself from the old track piece, add myself to the new one
                if current_track_piece is not None:
                    current_track_piece.cars.remove(self)
                self.track_piece.cars.append(self)

    def update_sprite(
        self, angle: int, braking: bool, boost: bool = False
    ) -> None:
        # Frames 1-2 roll the tyres, 4-5 the same with the boost flame, 3 is braking
        frame: int = (
            0
            if self.speed == 0
            else 3
            if braking
            else int(self.tyre_rotation % 2) + (4 if boost else 1)
        )
        self.image = f"car_{self.car_letter}_{angle}_{frame}"


# Not a dataclass: Car (the base) is one, and dataclass-over-dataclass merges
# inherited fields into the subclass __init__ signature; also the car letter is
# chosen randomly for the super() call.
class CPUCar(Car):
    __slots__ = (
        "accel",
        "target_speed",
        "target_x",
        "steering",
        "change_speed_timer",
    )

    def __init__(self, pos: g3.Vector, accel: float, speed: float) -> None:
        super().__init__(pos, choice(("b", "c", "d", "e")))

        # CPU cars accelerate faster than player but have a lower top speed
        self.accel: float = PLAYER_ACCELERATION_MAX * accel
        self.target_speed: float = speed
        self.target_x: float = float(pos.x)

        # Set based on track curvature, so we can display an angled variant of the car sprite
        self.steering: float = 0

        self.change_speed_timer: float = uniform(2, 4)

    @override
    def update(self, delta_time: float) -> None:
        if game.race_complete:
            # (only a game with a player can complete a race)
            assert game.player_car is not None
            self.target_speed = game.player_car.speed

        self.speed = move_towards(
            self.speed, self.target_speed, self.accel * delta_time
        )
        self.pos = with_x(
            self.pos,
            move_towards(float(self.pos.x), self.target_x, 400 * delta_time),
        )

        super().update(delta_time)

        track_piece_idx, _ = game.get_first_track_piece_ahead(float(self.pos.z))
        if track_piece_idx is not None:
            self.steering = game.track[track_piece_idx].offset_x

        # Every few seconds we'll change target speed by a random amount, but upwards on average, so that slow cars
        # have a chance to catch up, and so that we can see CPU cars overtaking each other
        self.change_speed_timer -= delta_time
        if self.change_speed_timer <= 0 and not game.race_complete:
            self.target_speed += uniform(-4, 6)
            self.target_speed = min(
                max(self.target_speed, CPU_CAR_MIN_TARGET_SPEED),
                CPU_CAR_MAX_TARGET_SPEED,
            )

            # If we're on a sharp corner and speed is above a certain level, reduce target speed
            if track_piece_idx is not None:
                target_speed_override: float | None = game.track[
                    track_piece_idx
                ].cpu_max_target_speed
                if (
                    target_speed_override is not None
                    and self.target_speed > target_speed_override
                ):
                    # Make it slightly random
                    self.target_speed = uniform(
                        target_speed_override - 3, target_speed_override
                    )

            # Also change target X pos to a random value
            # Ensure not too close to values for nearby cars, to avoid cars driving through each other

            def is_target_x_too_close_to_nearby_cars() -> bool:
                return any(
                    car is not self
                    and abs(self.pos.z - car.pos.z) < 20
                    and abs(self.target_x - car.pos.x) < 300
                    for car in game.cars
                )

            # Limit number of attempts to ensure no chance of infinite loop
            for _ in range(20):
                self.target_x = uniform(-1000, 1000)
                if not is_target_x_too_close_to_nearby_cars():
                    break

            # Reset timer
            self.change_speed_timer = uniform(2, 4)


# Not a dataclass: same reason as CPUCar (Car is a dataclass base).
class PlayerCar(Car):
    __slots__ = (
        "controls",
        "offset_x_change",
        "resetting",
        "explode_timer",
        "last_checkpoint_idx",
        "lap",
        "lap_time",
        "race_time",
        "fastest_lap",
        "last_lap_was_fastest",
        "braking",
        "engine_sounds",
        "skid_sound",
        "current_engine_sound",
        "current_engine_sound_idx",
        "skid_sound_playing",
        "grass_sound_repeat_timer",
        "on_grass",
        "prev_position",
    )

    def __init__(self, pos: g3.Vector, controls: Controls) -> None:
        super().__init__(pos, "a")
        self.controls: Controls = controls
        self.offset_x_change: float = 0
        self.resetting: bool = False
        self.explode_timer: int | None = None
        self.last_checkpoint_idx: int | None = None
        self.lap: int = 1
        self.lap_time: float = 0
        self.race_time: float = 0
        self.fastest_lap: float | None = None
        self.last_lap_was_fastest: bool = False
        self.braking: bool = False

        # Load engine and skid sounds. These are not played with Game.play_sound as they require custom behaviour.
        # Enclosed in a try/except section to deal with the case where the sound files can't be loaded
        try:
            self.engine_sounds: list[Sound] = [
                sounds.load(f"engine_short{i}") for i in range(40)
            ]
            self.skid_sound: Sound | None = sounds.load("skid_loop0")
        except Exception:
            self.engine_sounds = []
            self.skid_sound = None

        self.current_engine_sound: Sound | None = None
        self.current_engine_sound_idx: int = -1
        self.update_engine_sound()

        self.skid_sound_playing: bool = False

        self.grass_sound_repeat_timer: float = 0
        self.on_grass: bool = False

        # Last known position in the race, indexed from 0 - used to decide when to play overtaking sounds
        self.prev_position: int = NUM_CARS - 1

    def stop_engine_sound(self) -> None:
        if self.current_engine_sound is not None:
            self.current_engine_sound.stop()

    @override
    def update(self, delta_time: float) -> None:
        if not game.race_complete:
            self.lap_time += delta_time
            self.race_time += delta_time

        self.grass_sound_repeat_timer -= delta_time

        self.update_engine_sound()

        # Play overtaking sounds? See if our position in the race has changed since last frame
        current_position: int = game.cars.index(self)
        if current_position != self.prev_position:
            # Only play sound if speed difference is high enough
            if abs(self.speed - game.cars[self.prev_position].speed) > 4:
                game.play_sound("overtake", 6)

            self.prev_position = current_position

        if self.resetting:
            if self.explode_timer is not None:
                self.explode_timer += 1
                if self.explode_timer > 31:
                    self.explode_timer = None
            else:
                # Reset player to centre of track over about 2 seconds
                self.pos = with_x(
                    self.pos,
                    move_towards(float(self.pos.x), 0, 2000 * delta_time),
                )
                self.resetting = self.pos.x != 0

        x_move: float = 0
        accel: float = 0

        if not self.resetting:
            # Not resetting - do normal movement & controls

            self.braking = False

            # Only get control inputs if race is not complete
            if not game.race_complete:
                self.controls.update()
                if self.controls.button_down(0):
                    accel = (
                        PLAYER_ACCELERATION_MAX
                        if self.speed < HIGH_ACCEL_THRESHOLD
                        else PLAYER_ACCELERATION_MIN
                    )
                    self.speed += accel * delta_time
                elif self.controls.button_down(1):
                    # Brake
                    self.braking = True
                    self.speed = max(0, self.speed - delta_time * 10)

            # Apply drag in a frame-rate independent way
            drag_factor: float = 0.9975
            if self.on_grass:
                # More drag on grass
                drag_factor -= 0.0025

            # Apply drag to speed. ** = power, e.g. 3 ** 5 is 3 to the power of 5
            # Check out this superb video which explains the uses and misuses of delta times, including more advanced
            # uses as seen in this case: https://www.youtube.com/watch?v=yGhfUcPjXuE
            self.speed *= drag_factor ** (delta_time / (1 / 60))

            # If we're going round a corner, shift X pos so that failing to steer will take you off the track
            # This is necessary because in this game, the corners are just illusions!
            if self.offset_x_change != 0:
                # We also set self.grip to less than 1 if we're cornering at high speed (but only if we're steering
                # in same direction as corner)
                if self.speed > LOSE_GRIP_SPEED and sign(
                    self.get_x_input()
                ) == -sign(self.offset_x_change):
                    self.grip = remap_clamp(
                        self.speed, LOSE_GRIP_SPEED, ZERO_GRIP_SPEED, 1, 0
                    )
                else:
                    self.grip = 1

                # Apply corner offset - grip will be used to alter steering movement in Car.update
                # We don't multiply by delta_time here as offset_x_change is partly based on the total amount of forward
                # motion that has taken place since the previous frame, which already takes delta_time into account
                # We don't do this if the race is complete - just let car go around the corners with no steering needed
                if not game.race_complete:
                    self.pos = with_x(
                        self.pos,
                        self.pos.x
                        - self.offset_x_change * CORNER_OFFSET_MULTIPLIER,
                    )

            else:
                # Not going around a corner
                self.grip = 1

            # Get track piece we were on before forward motion was applied
            previous_track_piece_idx, _ = game.get_first_track_piece_ahead(
                float(self.pos.z)
            )
            assert (
                previous_track_piece_idx is not None
            )  # we never leave the track

            # Apply steering
            if self.speed > 0 and not game.race_complete:
                x_move = (
                    self.get_x_input()
                    * self.speed
                    * STEERING_STRENGTH
                    * self.grip
                    * delta_time
                )
                self.pos = with_x(self.pos, self.pos.x - x_move)

            # Call parent (Car) update method, which includes applying motion
            super().update(delta_time)

            # Check for collisions with other cars
            for car in game.cars:
                if car is not self:
                    # Note - axes are not uniform in scale (1 unit in X axis is much smaller than 1 unit in Z axis),
                    # so we can't do a normal distance calculation.
                    # Instead we just check X and Z differences separately (Y is irrelevant as cars are always
                    # on the ground)
                    vec: g3.Vector = self.pos - car.pos
                    collide_front_distance_z: float = 0.6
                    collide_back_distance_z: float = 1.2
                    if (
                        abs(vec.x) < 260
                        and vec.z < collide_front_distance_z
                        and vec.z > -collide_back_distance_z
                    ):
                        midpoint: float = (
                            self.pos.z - car.pos.z
                        ) / 2 + car.pos.z
                        # Which side did we collide on?
                        # An alternative way to do this would be to use the speed difference, e.g. if player speed
                        # is faster, we hit the car in front
                        if abs(vec.z) < 0.2:
                            # Side collision
                            self.pos = with_x(
                                self.pos, self.pos.x + sign(float(vec.x)) * 50
                            )
                            car.pos = with_x(
                                car.pos, car.pos.x - sign(float(vec.x)) * 50
                            )

                        elif vec.z > 0:
                            # Colliding with the back of the car in front
                            self.speed = max(car.speed - 3, 0)
                            car.speed = max(car.speed, self.speed + 3)
                            # (the collided-with car is always a CPU car: the player is self)
                            if isinstance(car, CPUCar):
                                car.target_speed = car.speed

                            # Shift us back and other car forward so we're not longer overlapping
                            self.pos = with_z(
                                self.pos,
                                midpoint + collide_front_distance_z * 0.6,
                            )
                            car.pos = with_z(
                                car.pos,
                                midpoint - collide_front_distance_z * 0.6,
                            )

                            game.play_sound("bump", 6)

                        else:
                            # Car behind collided with us - get a speed boost
                            self.speed = max(self.speed, car.speed + 3)
                            car.speed = max(self.speed - 3, 0)

                            # Shift other car back and us forward so we're not longer overlapping
                            self.pos = with_z(
                                self.pos,
                                midpoint - collide_back_distance_z * 0.6,
                            )
                            car.pos = with_z(
                                car.pos,
                                midpoint + collide_back_distance_z * 0.6,
                            )

                            game.play_sound("bump_behind")

            # Check for collisions with scenery, driving on grass and passing a checkpoint
            track_piece_idx, _ = game.get_first_track_piece_ahead(
                float(self.pos.z)
            )
            if track_piece_idx is not None:
                track_piece: TrackPiece = game.track[track_piece_idx]

                for scenery in track_piece.scenery:
                    for zone_left, zone_right in scenery.collision_zones:
                        if (
                            scenery.x + zone_left
                            < self.pos.x
                            < scenery.x + zone_right
                        ):
                            self.speed = 0
                            self.resetting = True
                            self.explode_timer = 0  # Start explosion animation
                            game.play_sound("explosion")

                # Are we on, or have we passed, a checkpoint?
                for i in range(previous_track_piece_idx, track_piece_idx + 1):
                    if isinstance(game.track[i], TrackPieceStartLine):
                        # It's a checkpoint. If it's the first one, ignore it (passing the start line at the start of
                        # the race is not of interest). If we've already dealt with this checkpoint, ignore it.
                        # Otherwise update lap count and lap time
                        if (
                            self.last_checkpoint_idx is not None
                            and self.last_checkpoint_idx != i
                        ):
                            self.lap += 1

                            # Was this the fastest lap?
                            if (
                                self.fastest_lap is None
                                or self.lap_time < self.fastest_lap
                            ):
                                self.fastest_lap = self.lap_time
                                self.last_lap_was_fastest = True
                                game.play_sound("fastlap")
                            else:
                                self.last_lap_was_fastest = False

                            # Play final lap sound effect?
                            if self.lap == NUM_LAPS:
                                game.play_sound("final_lap")

                            # Set lap time back to 0 for new lap
                            self.lap_time = 0

                        self.last_checkpoint_idx = i

                # Are we on the grass?
                if abs(self.pos.x) + 100 > track_piece.width / 2:
                    self.on_grass = True
                    if self.grass_sound_repeat_timer <= 0:
                        game.play_sound("hit_grass")
                        self.grass_sound_repeat_timer = 0.15

                    # Are we way too far off the track? Reset if so
                    if abs(self.pos.x) > 6000:
                        self.speed = 0
                        self.resetting = True
                else:
                    self.on_grass = False

            # End of "if not self.resetting" block

        # Depending on grip, turn skid sound on/off or vary volume
        if self.skid_sound is not None:
            # Determine volume to play skid sound at
            if (
                self.resetting
                or self.grip >= SKID_SOUND_START_GRIP
                or self.get_x_input() == 0
            ):
                volume: float = 0

            else:
                volume = remap_clamp(
                    self.grip, SKID_SOUND_START_GRIP, 0.5, 0, 1
                )

                # Scale volume based on track curvature - higher volume for tighter corners
                if track_piece_idx is not None:
                    track_piece = game.track[track_piece_idx]
                    volume *= remap_clamp(
                        abs(track_piece.offset_x), 0, 15, 0, 1
                    )

            if volume > 0:
                if not self.skid_sound_playing:
                    self.skid_sound.play(
                        loops=-1, fade_ms=100
                    )  # Loop indefinitely
                    self.skid_sound_playing = True

                self.skid_sound.set_volume(volume)
            else:
                self.skid_sound_playing = False
                self.skid_sound.fadeout(250)

        # Set sprite
        if self.explode_timer is not None:
            self.image = f"explode{self.explode_timer // 2:02}"
        else:
            boost: bool = accel > 0 and 0 < self.speed < HIGH_ACCEL_THRESHOLD
            self.update_sprite(sign(x_move), self.braking, boost)

    def update_engine_sound(self) -> None:
        # The engine note is one of 40 looping samples chosen by speed; crossfade when it changes
        sound_index: int = min(
            int(self.speed * 0.6), len(self.engine_sounds) - 1
        )
        if sound_index != self.current_engine_sound_idx:
            self.current_engine_sound_idx = sound_index
            old_sound: Sound | None = self.current_engine_sound
            self.current_engine_sound = self.engine_sounds[sound_index]
            self.current_engine_sound.set_volume(0.3)

            if old_sound is not None:
                old_sound.fadeout(150)
            self.current_engine_sound.play(loops=-1, fade_ms=100)

    def get_x_input(self) -> float:
        return self.controls.get_x()

    def set_offset_x_change(self, value: float) -> None:
        self.offset_x_change = value


def generate_scenery(
    track_i: int,
    image: Image | None = None,
    interval: int = 40,
    lamps: bool = True,
) -> list[Scenery]:
    if image is None:
        image = images.load("billboard00")
    if track_i % interval == 0:
        # Billboards
        return [Billboard(BILLBOARD_X, image), Billboard(-BILLBOARD_X, image)]
    elif lamps and track_i % 30 == 0:
        # Lamps
        return [LampLeft(), LampRight()]
    else:
        return []


def make_track() -> list[TrackPiece]:
    # Each track piece in the list represents a line with a particular width, with optional attached scenery.
    # When the track is drawn, we draw a polygon for each track piece, connecting this line with the line of the
    # previous track piece.
    track: list[TrackPiece] = []
    for _lap in range(NUM_LAPS + 1):
        track.extend(
            [
                TrackPiece(
                    scenery=generate_scenery(i, images.load("billboard02"))
                )
                for i in range(15)
            ]
        )

        # Start gantry
        track.append(TrackPieceStartLine())

        track.extend([TrackPiece() for _ in range(SECTION_SHORT)])

        # Because the camera is pointing down the negative Z axis, negative/positive X mean right/left from
        # camera's perspective

        # Mild right turn followed by short straight
        track.extend(
            [
                TrackPiece(offset_x=-4, offset_y=0, scenery=generate_scenery(i))
                for i in range(SECTION_MEDIUM)
            ]
        )
        track.extend(
            [
                TrackPiece(
                    scenery=generate_scenery(i, images.load("billboard01"))
                )
                for i in range(SECTION_SHORT)
            ]
        )

        # Slight downward slope, going into moderate right hand turn
        track.extend(
            [
                TrackPiece(offset_x=0, offset_y=-1, scenery=generate_scenery(i))
                for i in range(SECTION_VERY_SHORT)
            ]
        )
        track.extend(
            [
                TrackPiece(offset_x=0, offset_y=-2, scenery=generate_scenery(i))
                for i in range(SECTION_VERY_SHORT)
            ]
        )
        track.extend(
            [
                TrackPiece(
                    offset_x=-2, offset_y=-1, scenery=generate_scenery(i)
                )
                for i in range(SECTION_VERY_SHORT)
            ]
        )
        track.extend(
            [
                TrackPiece(
                    offset_x=-5,
                    offset_y=0,
                    scenery=generate_scenery(i, images.load("billboard03")),
                )
                for i in range(SECTION_VERY_SHORT)
            ]
        )
        track.extend(
            [
                TrackPiece(
                    offset_x=-10,
                    offset_y=0,
                    scenery=generate_scenery(i, images.load("billboard03")),
                )
                for i in range(SECTION_MEDIUM)
            ]
        )

        # Short straight
        track.extend(
            [
                TrackPiece(scenery=generate_scenery(i))
                for i in range(SECTION_SHORT)
            ]
        )

        # Medium-sharp turn left, slight upward slope
        track.extend(
            [
                TrackPiece(
                    offset_x=13,
                    offset_y=1,
                    scenery=generate_scenery(
                        i, images.load("arrow_left"), interval=10
                    ),
                )
                for i in range(SECTION_MEDIUM)
            ]
        )

        track.extend(
            [
                TrackPiece(
                    offset_x=0,
                    offset_y=0,
                    scenery=generate_scenery(i, images.load("billboard02")),
                )
                for i in range(SECTION_MEDIUM)
            ]
        )

        # Small hill
        track.extend(
            [
                TrackPiece(
                    offset_x=0,
                    offset_y=2,
                    scenery=generate_scenery(i, images.load("billboard02")),
                )
                for i in range(SECTION_MEDIUM)
            ]
        )

        # Slightly down and to the right
        track.extend(
            [
                TrackPiece(
                    offset_x=-3,
                    offset_y=-1,
                    scenery=generate_scenery(i, images.load("billboard01")),
                )
                for i in range(SECTION_LONG)
            ]
        )

        # Crazy downward curve
        track.extend(
            [
                TrackPiece(offset_x=0, offset_y=-4, scenery=generate_scenery(i))
                for i in range(SECTION_MEDIUM)
            ]
        )

        # Upward slope
        track.extend(
            [
                TrackPiece(
                    offset_x=0,
                    offset_y=2,
                    scenery=generate_scenery(i, images.load("billboard03")),
                )
                for i in range(SECTION_LONG)
            ]
        )

        # Turn to left and up, gradually increasing curve
        for j in range(1, 10):
            track.extend(
                [
                    TrackPiece(
                        offset_x=j, offset_y=j, scenery=generate_scenery(i)
                    )
                    for i in range(SECTION_VERY_SHORT)
                ]
            )

        # Downward curve, increasing then decreasing in intensity
        for j in range(1, 10):
            track.extend(
                [
                    TrackPiece(
                        offset_x=0, offset_y=-j, scenery=generate_scenery(i)
                    )
                    for i in range(SECTION_VERY_SHORT)
                ]
            )

        # straight with chevron billboards at end, CPU cars will slow down in this section
        track.extend(
            [
                TrackPiece(cpu_max_target_speed=60, scenery=[])
                for _ in range(SECTION_MEDIUM)
            ]
        )
        track.extend(
            [
                TrackPiece(
                    cpu_max_target_speed=58,
                    scenery=generate_scenery(
                        i, images.load("arrow_right"), interval=10, lamps=False
                    ),
                )
                for i in range(SECTION_SHORT)
            ]
        )
        track.extend(
            [
                TrackPiece(
                    cpu_max_target_speed=58,
                    scenery=generate_scenery(
                        i, images.load("arrow_right"), interval=10, lamps=False
                    ),
                )
                for i in range(SECTION_SHORT)
            ]
        )

        # sharp turn right, easing off slightly at end
        track.extend(
            [
                TrackPiece(
                    offset_x=-15,
                    cpu_max_target_speed=55,
                    scenery=generate_scenery(
                        i, images.load("arrow_right"), interval=10, lamps=False
                    ),
                )
                for i in range(SECTION_SHORT)
            ]
        )
        track.extend(
            [
                TrackPiece(
                    offset_x=-13,
                    cpu_max_target_speed=57,
                    scenery=generate_scenery(
                        i, images.load("arrow_right"), interval=10, lamps=False
                    ),
                )
                for i in range(SECTION_SHORT)
            ]
        )
        track.extend(
            [
                TrackPiece(
                    offset_x=-11, offset_y=0, scenery=generate_scenery(i)
                )
                for i in range(SECTION_SHORT)
            ]
        )
        track.extend(
            [
                TrackPiece(offset_x=-9, offset_y=0, scenery=generate_scenery(i))
                for i in range(SECTION_SHORT)
            ]
        )

        # straight
        track.extend(
            [
                TrackPiece(offset_x=0, offset_y=0, scenery=generate_scenery(i))
                for i in range(SECTION_MEDIUM)
            ]
        )

        # cosine hills
        track.extend(
            [
                TrackPiece(
                    offset_y=math.cos(i / 20) * 5, scenery=generate_scenery(i)
                )
                for i in range(SECTION_LONG)
            ]
        )

        # Mild upward slope - the purpose is to reset the Y scrolling of the background so it roughly matches the
        # background position at the start of the lap
        track.extend(
            [
                TrackPiece(
                    offset_x=0,
                    offset_y=0.25,
                    scenery=generate_scenery(i, images.load("billboard03")),
                )
                for i in range(SECTION_LONG)
            ]
        )

        # short straight
        track.extend(
            [
                TrackPiece(
                    offset_x=0,
                    offset_y=0,
                    scenery=generate_scenery(i, images.load("billboard03")),
                )
                for i in range(SECTION_SHORT)
            ]
        )

    return track


@dataclass(frozen=True, slots=True)
class TrackPieceScreen:
    """Where one track piece's edge points landed on screen this frame, in the
    order Game.draw projects them: the track's left and right edges, the
    central stripe, the rumble strips' outer edges and the yellow lines'
    outer and inner edges. Each polygon joins these to the previous piece's.
    """

    left: g2.Vector
    right: g2.Vector
    stripe_left: g2.Vector
    stripe_right: g2.Vector
    rumble_left_outer: g2.Vector
    rumble_right_outer: g2.Vector
    yellow_left_outer: g2.Vector
    yellow_left_inner: g2.Vector
    yellow_right_outer: g2.Vector
    yellow_right_inner: g2.Vector


@dataclass(eq=False, slots=True)
class Game:
    #: The player's input, or None for the title screen's demo race (no player car)
    controls: InitVar[Controls | None] = None
    track: list[TrackPiece] = field(init=False)
    #: We only create a player car (in setup_cars) when there is a controls object
    player_car: PlayerCar | None = field(default=None, init=False)
    #: The player's car, or the demo race's leading CPU car
    camera_follow_car: Car = field(init=False)
    #: Kept in sorted order of race position
    cars: list[Car] = field(init=False)
    camera: g3.Vector = field(init=False)
    background: Image = field(init=False)
    #: Where the background image is drawn; corners scroll it sideways
    bg_offset: g2.Vector = field(init=False)
    first_frame: bool = field(default=True, init=False)
    on_screen_debug_strs: list[str] = field(default_factory=list, init=False)
    frame_counter: int = field(default=0, init=False)
    timer: float = field(default=0, init=False)
    race_complete: bool = field(default=False, init=False)
    time_up: bool = field(default=False, init=False)
    #: Seconds of the start countdown left; the demo race starts at once
    start_timer: float = field(init=False)

    def __post_init__(self, controls: Controls | None) -> None:
        self.track = make_track()

        self.setup_cars(controls)

        self.camera = g3.Vector(0, 400, 0)

        self.background = images.load("background")
        self.bg_offset = g2.Vector(-self.background.width // 2, 30)

        if self.player_car is not None:
            self.start_timer = 3.999
            music.play("engines_startline")
        else:
            # Race starts immediately on title screen
            self.start_timer = 0

    def setup_cars(self, controls: Controls | None) -> None:
        self.cars = []
        for i in range(NUM_CARS):
            z: float = -3 - i * GRID_CAR_SPACING
            x: int = -400 if i % 2 == 0 else 400
            if i == 0 and controls is not None:
                # Don't create player car on title screen
                self.player_car = PlayerCar(g3.Vector(x, 0, z), controls)
                self.cars.append(self.player_car)
            else:
                target_speed: float = remap(
                    i,
                    0,
                    NUM_CARS - 1,
                    CPU_CAR_MIN_TARGET_SPEED,
                    CPU_CAR_MAX_TARGET_SPEED,
                )
                accel: float = remap(i, 0, NUM_CARS - 1, 1.5, 2)
                self.cars.append(
                    CPUCar(g3.Vector(x, 0, z), speed=target_speed, accel=accel)
                )

        self.camera_follow_car = (
            self.player_car if self.player_car is not None else self.cars[0]
        )

    def update(self, delta_time: float) -> None:
        self.timer += delta_time
        self.frame_counter += 1

        # Race start sequence
        if self.start_timer > 0:
            # Ensure cars are added to the appropriate track piece's car list, so that
            # they're displayed during the start countdown (during which time their update is not called)
            for car in self.cars:
                car.update_current_track_piece()
            timer_old: float = self.start_timer
            self.start_timer = max(0, self.start_timer - delta_time)
            # Every second of the countdown, make a sound effect
            if self.start_timer == 0:
                # Go!
                # Ambience is stereo so is treated as music
                music.play("ambience")
                self.play_sound("gobeep")

            elif int(timer_old) != int(self.start_timer):
                self.play_sound("startbeep")

        old_camera_z: float = float(self.camera.z)
        prev_ahead, _ = self.get_first_track_piece_ahead(old_camera_z)
        assert prev_ahead is not None  # the camera never leaves the track

        # If race has started, update all cars
        if self.start_timer == 0:
            for car in self.cars:
                car.update(delta_time)

        # Is the race complete?
        if not self.race_complete and self.player_car is not None:
            # End the game if lap time reaches 4 mins
            # This serves two purposes:
            # 1) Prevent lap time text from overflowing its area (would happen after 10 mins)
            # 2) If the game is being demoed in public, and someone starts playing and then leaves before finishing
            #    a race, the game will eventually end so that the next player can start a fresh race without having
            #    to quit and re-run the game
            # Also allow player to end the game by pressing Escape
            if self.player_car.lap_time >= 60 * 4 or keyboard.escape:
                music.stop()
                self.time_up = True
                self.race_complete = True

            elif self.player_car.lap > NUM_LAPS:
                music.stop()
                self.race_complete = True

                self.play_sound("game_complete")

            # Sort cars in the list based on race positions
            self.cars.sort(key=lambda car: car.pos.z)

        # Update camera position to follow player car
        self.camera = g3.Vector(
            self.camera_follow_car.pos.x,
            self.camera.y,
            self.camera_follow_car.pos.z + CAMERA_FOLLOW_DISTANCE,
        )

        # As camera moves around corners, add to bg_offset and shift car X position so that steering is required on corners

        # Get the new camera pos and determine which track piece it's on. The logic is different depending on whether
        # the position change goes from one track piece to the next, or is within one track piece
        new_camera_z: float = float(self.camera.z)
        new_ahead, _ = self.get_first_track_piece_ahead(new_camera_z)
        assert new_ahead is not None

        # We need to deal with not just interpolating during movement within one track piece, but also when we pass the
        # boundary of a track piece.
        # We need to know how far the camera has travelled since the start of the frame and work out which portion of the
        # movement covers which track piece.
        # It's also possible for the movement to be across more than two track pieces.

        # Example
        # track i   z   offset_x
        # 5         -5  0
        # 6         -6  1000
        # 7         -7  0

        # Car start Z = -5      First track piece ahead = 5 (offset 0)
        # Car end Z = -5.5      First track piece ahead = 6 (offset 1000)
        # Offset change = 500

        # Car start Z = -5.4    First track piece ahead = 6 (offset 1000)
        # Car end Z = -5.5      First track piece ahead = 6 (offset 1000)
        # Offset change = 100

        # Car start Z = -5      First track piece ahead = 5 (offset 0)
        #                       Spans whole of piece 6 (offset 1000)
        # Car end Z = -6.1      First track piece ahead = 7 (offset 0)
        # Offset change = 1000

        # Car start Z = -5.001  First track piece ahead = 6 (offset 1000)
        # Car end Z = -6.1      First track piece ahead = 7 (offset 0)
        # Offset change = 999.9

        # Get distance from here to next SPACING increment or new camera z, whichever is a smaller change (higher number)
        # Ignore if camera moved backwards (debug camera only), or the camera is before the start of the track
        # Don't do this on first frame, as camera won't have its correct initial Z position at the beginning of the frame
        distance: float = old_camera_z - new_camera_z
        offset_change: g2.Vector = g2.Vector(0, 0)
        if (
            distance > 0
            and not self.first_frame
            and prev_ahead >= 0
            and new_ahead >= 0
        ):
            old_z_next_spacing_boundary: float = (
                old_camera_z // SPACING
            ) * SPACING
            new_z_prev_spacing_boundary: float = (
                (new_camera_z // SPACING) * SPACING
            ) + SPACING
            prev_track: TrackPiece = self.track[prev_ahead]
            new_track: TrackPiece = self.track[new_ahead]
            if new_ahead > prev_ahead:
                # Movement touches at least two track pieces
                # Figure out how much of the movement was within the old and new track pieces, plus whether there
                # are any intermediate track pieces between them (whose offsets will be fully applied)

                # What proportion of the old and new track pieces have we covered?
                distance_first: float = (
                    old_camera_z - old_z_next_spacing_boundary
                )
                distance_last: float = (
                    new_z_prev_spacing_boundary - new_camera_z
                )
                fraction_first: float = distance_first / SPACING
                fraction_last: float = distance_last / SPACING

                # assert stops the program with an AssertionError if the specified condition is false. Both fractions
                # should always be between zero and one, and if they aren't then we want to know about it. This assertion
                # may trigger with very low values of SPACING, possibly due to floating point inaccuracy.
                assert 0 <= fraction_first <= 1 and 0 <= fraction_last <= 1

                offset_change = (
                    g2.Vector(prev_track.offset_x, prev_track.offset_y)
                    * fraction_first
                    + g2.Vector(new_track.offset_x, new_track.offset_y)
                    * fraction_last
                )

                # If difference between prev_ahead and new_ahead is more than 1, that means the movement involves
                # three or more track pieces. We will have passed 100% of each of the in-between track pieces, so we
                # fully add their offsets
                if new_ahead - prev_ahead > 1:
                    for i in range(prev_ahead + 1, new_ahead):
                        piece: TrackPiece = self.track[i]
                        offset_change += g2.Vector(
                            piece.offset_x, piece.offset_y
                        )

            else:
                # Movement was just within one track piece
                fraction: float = distance / SPACING
                assert 0 <= fraction <= 1
                offset_change = (
                    g2.Vector(prev_track.offset_x, prev_track.offset_y)
                    * fraction
                )

            # Shift background by the calculated offset
            self.bg_offset += offset_change

            # Keep bg_offset.x within the range -backgroundwidth to +backgroundwidth
            while self.bg_offset.x < -self.background.width:
                self.bg_offset = g2.Vector(
                    self.bg_offset.x + self.background.width, self.bg_offset.y
                )
            while self.bg_offset.x > self.background.width:
                self.bg_offset = g2.Vector(
                    self.bg_offset.x - self.background.width, self.bg_offset.y
                )

        # Shift player car's X offset - this means the car will go off the track if you go around a corner without
        # steering. Without this, the car would magically stick to the track as if the corner wasn't there - because
        # the curvature is really just a visual effect!
        if self.player_car is not None:
            self.player_car.set_offset_x_change(float(offset_change.x))

        # This deals with moving the background when the camera is moving backwards, which will only happen if the
        # player uses the down arrow key debug mode
        if new_ahead < prev_ahead:
            self.bg_offset = g2.Vector(
                self.bg_offset.x - self.track[prev_ahead].offset_x,
                self.bg_offset.y - self.track[prev_ahead].offset_y,
            )

        self.first_frame = False

    def draw(self) -> None:
        # Fill background with single colour
        # We use a different background colour depending on the Y offset of the background image, because
        # the top and bottom of that image are different colours
        renderer.fill((0, 20, 117) if self.bg_offset.y > 0 else (0, 77, 180))

        # Profiling times
        times: dict[str, float] = {
            "scenery_scale": 0,
            "car_scale": 0,
            "prepare_draw_cars": 0,
        }

        # Draw background
        # Need to draw either one or two backgrounds - second copy is for wrapping (when bg_offset.x changes enough that
        # we'd see the edge of the image)
        profile_bg: Profiler = Profiler()
        self.on_screen_debug_strs.append(str(self.bg_offset))
        bg_width: g2.Vector = g2.Vector(self.background.width, 0)
        renderer.draw_image(self.background, xy(self.bg_offset))
        if self.bg_offset.x > 0:
            renderer.draw_image(self.background, xy(self.bg_offset - bg_width))
        if self.bg_offset.x + self.background.width < WIDTH:
            renderer.draw_image(self.background, xy(self.bg_offset + bg_width))
        times["bg"] = profile_bg.get_ms()

        # The camera as an INVERSE transformation (mvp course, ch16/ch19+): the
        # camera sits at self.camera in world space, so bringing a world point
        # into camera space is the INVERSE of that placement -- translate(camera)
        # undone. world_to_camera(p) is exactly `p - self.camera`. (The
        # perspective divide inside transform() is a projection, deliberately NOT
        # an InvertibleFunction -- it discards depth and is not invertible, which
        # is why only this world->camera step becomes a course transform.)
        world_to_camera: InvertibleFunction[g3.Vector] = inverse(
            translate(b=self.camera)
        )

        def project(
            point_v3: g3.Vector, clipping_plane: float = CLIPPING_PLANE
        ) -> g2.Vector | None:
            # Transform a world point into a g2.Vector point in screen space: camera space, then perspective, centred
            # on the screen. None if the point is behind the clipping plane
            newpoint: g3.Vector = world_to_camera(point_v3)
            if newpoint.z > clipping_plane:
                return None
            return g2.Vector(
                (newpoint.x / newpoint.z) + HALF_WIDTH,
                (newpoint.y / newpoint.z) + HALF_HEIGHT,
            )

        def project_sprite(
            point_v3: g3.Vector,
            w: float,
            h: float,
            clipping_plane: float = CLIPPING_PLANE,
        ) -> tuple[g2.Vector, float, float] | None:
            # As project, for a car or scenery sprite of original size w x h: also returns the scaled width and
            # height, based on the distance from the camera
            newpoint: g3.Vector = world_to_camera(point_v3)
            if newpoint.z > clipping_plane:
                return None
            point_v2: g2.Vector = g2.Vector(
                (newpoint.x / newpoint.z) + HALF_WIDTH,
                (newpoint.y / newpoint.z) + HALF_HEIGHT,
            )
            return point_v2, w / -newpoint.z, h / -newpoint.z

        # offset and offset_delta keep track of the cumulative changes in track offsets (X and Y - Z remains as 0), so
        # that each track piece is drawn in the correct position
        offset: g3.Vector = g3.Vector(0, 0, 0)
        offset_delta: g3.Vector = g3.Vector(0, 0, 0)

        # The previous track piece's screen positions: each polygon joins a piece's edges to the previous piece's,
        # so we remember them rather than recalculate them
        prev: TrackPieceScreen | None = None

        # Instead of drawing track pieces etc as we come across them, we store draw calls in this list. Then we once
        # we've finished going through track pieces, we execute the draw calls in reverse order, so that track
        # pieces, cars and scenery in the distance are drawn before things which are closer
        draw_list: list[tuple[Callable[[], None], str]] = []

        def add_to_draw_list(
            drawcall: Callable[[], None], type: str = "?"
        ) -> None:
            draw_list.append((drawcall, type))

        def draw_points(
            points: Sequence[PointLike], col: Colour, id: str
        ) -> None:
            # Queue a polygon, if any of its points is above the bottom of the screen
            if any(y < HEIGHT for _, y in points):
                add_to_draw_list(
                    lambda: renderer.polygon(
                        points, col, filled=OUTLINE_W == 0
                    ),
                    id,
                )

        is_first_track_piece_ahead: bool = True

        prof_track: Profiler = Profiler("track")

        # Get index of first track piece that starts at or just in front of the camera Z position
        # This means the track piece we're currently part-way through won't be displayed, but that doesn't matter
        # as it would be off the bottom of the camera.
        first_track_piece_idx, current_piece_z = (
            self.get_first_track_piece_ahead(float(self.camera.z))
        )
        assert (
            first_track_piece_idx is not None
        )  # the camera never leaves the track

        # Index of the track piece that we're drawing, relative to first_track_piece_idx
        track_ahead_i: int = 0

        # At the start of the loop body below, we subtract SPACING from current_piece_z. Therefore we must add SPACING
        # before the loop so that current_piece_z is correct for the first track piece.
        current_piece_z += SPACING

        # Go through each track piece ahead
        for i in range(first_track_piece_idx, len(self.track)):
            # Stop when we've displayed VIEW_DISTANCE number of track pieces
            track_ahead_i += 1
            if track_ahead_i > VIEW_DISTANCE:
                break

            track_piece: TrackPiece = self.track[i]
            current_piece_z -= SPACING

            # Because the camera is pointing down the negative Z axis, negative/positive X mean right/left from
            # camera's perspective
            left: g3.Vector = g3.Vector(
                track_piece.width / 2, 0, current_piece_z
            )
            right: g3.Vector = g3.Vector(
                -track_piece.width / 2, 0, current_piece_z
            )

            # Interpolate for X offset between first and next track piece. Without this, going around corners would
            # look very juddery
            if is_first_track_piece_ahead:
                # Get fraction between this and next
                # Current track piece is actually the first track piece IN FRONT of Z
                # And next is the one after that
                # So to find the fraction we need to add spacing
                adjusted_camera_z: float = self.camera.z - SPACING
                fraction: float = inverse_lerp(
                    current_piece_z - SPACING,
                    current_piece_z,
                    adjusted_camera_z,
                )
                offset_delta = g3.Vector(
                    fraction * track_piece.offset_x,
                    fraction * track_piece.offset_y,
                    0,
                )
            else:
                offset_delta += g3.Vector(
                    track_piece.offset_x, track_piece.offset_y, 0
                )

            is_first_track_piece_ahead = False

            offset += offset_delta

            left += offset
            right += offset

            # Calculate screen positions of the track boundaries, the central stripe (always worked out, even for
            # pieces which don't draw one, because the next track piece may connect up to it), the outer parts of the
            # left/right rumble strips (the inner parts are the track edges), and the left and right yellow lines,
            # which are just inside the outer edges of the track. All share this piece's Z, so either all of them
            # are in front of the clipping plane, or none is
            edge_offset: g3.Vector = g3.Vector(
                YELLOW_LINE_DISTANCE_FROM_EDGE, 0, 0
            )
            line_width: g3.Vector = g3.Vector(HALF_YELLOW_LINE_W, 0, 0)
            rumble_width: g3.Vector = g3.Vector(HALF_RUMBLE_STRIP_W, 0, 0)
            world_points: tuple[g3.Vector, ...] = (
                left,
                right,
                g3.Vector(HALF_STRIPE_W, 0, current_piece_z) + offset,
                g3.Vector(-HALF_STRIPE_W, 0, current_piece_z) + offset,
                left + rumble_width,
                right - rumble_width,
                left - edge_offset,
                left - edge_offset - line_width,
                right + edge_offset,
                right + edge_offset + line_width,
            )
            projected: list[g2.Vector | None] = [
                project(p) for p in world_points
            ]
            screen_points: list[g2.Vector] = [
                p for p in projected if p is not None
            ]

            # Only draw if the points are in front of the clipping plane
            if len(screen_points) == len(world_points):
                current: TrackPieceScreen = TrackPieceScreen(*screen_points)

                # To draw, there must be a previous track piece that we can connect to
                if prev is not None:
                    # Draw stripe (3m on/off)
                    if i // 3 % 2 == 0:
                        draw_points(
                            (
                                current.stripe_left,
                                current.stripe_right,
                                prev.stripe_right,
                                prev.stripe_left,
                            ),
                            STRIPE_COLOUR,
                            "stripe",
                        )

                    # Draw yellow lines
                    # This is before the drawing of the track as we want to draw on top of the track, and items in the
                    # draw list are drawn in reverse order
                    if SHOW_YELLOW_LINES:
                        draw_points(
                            (
                                prev.yellow_left_outer,
                                current.yellow_left_outer,
                                current.yellow_left_inner,
                                prev.yellow_left_inner,
                            ),
                            YELLOW_LINE_COL,
                            "yellow line L",
                        )
                        draw_points(
                            (
                                prev.yellow_right_outer,
                                current.yellow_right_outer,
                                current.yellow_right_inner,
                                prev.yellow_right_inner,
                            ),
                            YELLOW_LINE_COL,
                            "yellow line R",
                        )

                    # Draw track
                    draw_points(
                        (prev.left, current.left, current.right, prev.right),
                        track_piece.col,
                        "track",
                    )

                    # Draw rumble strip
                    # This is before trackside as it draws on top of trackside, and items in the draw list are drawn
                    # in reverse order
                    if SHOW_RUMBLE_STRIPS:
                        # Alternating colours
                        rumble_col: Colour = (
                            RUMBLE_COLOUR_1
                            if (i // 2) % 2 == 0
                            else RUMBLE_COLOUR_2
                        )
                        draw_points(
                            (
                                prev.rumble_left_outer,
                                prev.left,
                                current.left,
                                current.rumble_left_outer,
                            ),
                            rumble_col,
                            "rumble L",
                        )
                        draw_points(
                            (
                                prev.rumble_right_outer,
                                prev.right,
                                current.right,
                                current.rumble_right_outer,
                            ),
                            rumble_col,
                            "rumble R",
                        )

                    # Draw trackside, out to the screen edges
                    if SHOW_TRACKSIDE:
                        # Alternating colours
                        trackside_col: Colour = (
                            TRACKSIDE_COLOUR_1
                            if (i // 5) % 2 == 0
                            else TRACKSIDE_COLOUR_2
                        )
                        draw_points(
                            (
                                current.right,
                                prev.right,
                                (0, float(prev.right.y)),
                                (0, float(current.right.y)),
                            ),
                            trackside_col,
                            "trackside left",
                        )
                        draw_points(
                            (
                                prev.left,
                                current.left,
                                (WIDTH - 1, float(current.left.y)),
                                (WIDTH - 1, float(prev.left.y)),
                            ),
                            trackside_col,
                            "trackside right",
                        )

                # Store screen positions of various parts of the track, as they form half of the polygon for the next
                # track piece
                prev = current

                # Show debug info for this track piece
                if SHOW_TRACK_PIECE_INDEX or SHOW_TRACK_PIECE_OFFSETS:
                    items: list[str] = []
                    if SHOW_TRACK_PIECE_INDEX:
                        items.append(str(i))
                    if SHOW_TRACK_PIECE_OFFSETS:
                        items.extend(
                            [
                                str(track_piece.offset_x),
                                str(track_piece.offset_y),
                            ]
                        )
                    text: str = ",".join(items)
                    label_at: tuple[float, float] = xy(current.left)
                    add_to_draw_list(
                        lambda label_at=label_at, text=text: draw_system_text(
                            text, label_at[0], label_at[1] - 30
                        )
                    )

            # Draw scenery for the current track piece
            if SHOW_SCENERY:
                for obj in track_piece.scenery:
                    if track_ahead_i * SPACING < obj.max_draw_distance:
                        pos_v3: g3.Vector = (
                            g3.Vector(obj.x, 0, current_piece_z) + offset
                        )
                        if (
                            self.camera.z - current_piece_z
                            > obj.min_draw_distance
                        ):
                            billboard: Image = obj.get_image()
                            sprite = project_sprite(
                                pos_v3,
                                billboard.width * obj.scale,
                                billboard.height * obj.scale,
                            )
                            # If a piece of scenery is very close to the camera, the scaled size may become enormous.
                            # Don't try to draw such scenery, due to memory and frame rate issues
                            if (
                                sprite is not None
                                and sprite[1] < MAX_SCENERY_SCALED_WIDTH
                            ):
                                pos, scaled_w, scaled_h = sprite
                                # Anchor point at bottom
                                pos -= g2.Vector(scaled_w // 2, scaled_h)
                                try:
                                    profile_scale: Profiler = Profiler()
                                    scaled: Image = scale_image(
                                        billboard, int(scaled_w), int(scaled_h)
                                    )
                                    times["scenery_scale"] += (
                                        profile_scale.get_ms()
                                    )
                                    add_to_draw_list(
                                        lambda scaled=scaled, pos=pos: (
                                            renderer.draw_image(scaled, xy(pos))
                                        ),
                                        "scenery_draw",
                                    )
                                except Exception:
                                    # Have experienced out of memory errors with a too-small clipping plane, due to trying
                                    # to scale to too big a size. In extreme cases this may try to allocate bitmaps over
                                    # 1GB in size!
                                    print(
                                        f"SCALE ERROR, w/h: {scaled_w} {scaled_h}"
                                    )

            # Draw cars
            profile_prepare_draw_cars: Profiler = Profiler()
            # (z, draw call) pairs, sorted and queued once the whole piece is known
            cars_to_draw: list[tuple[float, Callable[[], None]]] = []
            for car in track_piece.cars:
                # Each car needs to be drawn during the track piece it is on, but with an additional offset interpolated
                # towards the next track piece, so that it starts turning a corner as it reaches the piece
                # Also, the order of  drawing needs to be correct if there is more than one car per track piece
                car_offset: g3.Vector = offset
                if car.pos.z % SPACING != 0:
                    # Interpolate offset between this and next track piece
                    # Note that "Interpolate for X offset between first and next track piece"
                    # will already have happened! Does that matter?

                    # The following lines deal with the car when it's moving onto a track piece with an offset
                    fraction = inverse_lerp(
                        current_piece_z,
                        current_piece_z - SPACING,
                        float(car.pos.z),
                    )
                    next_track_piece: TrackPiece = self.track[i + 1]
                    car_offset += g3.Vector(
                        fraction * next_track_piece.offset_x,
                        fraction * next_track_piece.offset_y,
                        -fraction * SPACING,
                    )

                    # This ensures that the car's forward motion is correct on pieces following a piece with an offset
                    car_offset += offset_delta * fraction

                # The rules for drawing the player car (or whichever car the camera is following, in demo mode) are
                # a bit different. If we drew it in the same way, its position on the screen would be a bit off as
                # it would start going around corners before the camera does. So don't apply any offset.
                # (For Y offset, you can achieve an interesting effect by changing 0 to -car_offset.y / 2, but
                # it is a bit glitchy sometimes so we've left it at zero)
                if car is self.camera_follow_car:
                    car_offset = g3.Vector(0, 0, car_offset.z)

                pos_v3 = g3.Vector(car.pos.x, 0, current_piece_z) + car_offset
                scale: int = 2
                sprite_pos: g2.Vector

                # For CPU cars, choose the sprite to use based on the car's angle in relation to the camera
                if isinstance(car, CPUCar):
                    # Approximate the angle we're seeing the car from, to determine the sprite
                    # The further the car is ahead, the smaller the effect
                    # The car sprite filenames end in a number in the range -4 to 4, where 0 is the car not turning,
                    # -1 is the car turning slightly to the left, 1 is turning slightly to the right, etc
                    z_distance: float = max(1, -(pos_v3.z - self.camera.z))
                    offset_for_angle: float = (
                        pos_v3.x - self.camera.x
                    ) / z_distance
                    offset_for_angle += -car.steering * 10
                    angle_sprite_idx: int = int(
                        remap_clamp(offset_for_angle, -200, 200, -4, 4)
                    )

                    # If this is the camera follow car (which for a CPU car will only be the case during
                    # the title screen), limit to only the shallowest angles (-1 to 1), as this car is a stand-in
                    # for the plyaer car and the player car only uses angles between -1 and 1
                    if car is self.camera_follow_car:
                        angle_sprite_idx = min(max(angle_sprite_idx, -1), 1)

                    car.update_sprite(angle_sprite_idx, braking=False)

                # Calculate screen pos and scaled sprite size for car
                img: Image = images.load(car.image)
                sprite = project_sprite(
                    pos_v3,
                    img.width * scale,
                    img.height * scale,
                    clipping_plane=CLIPPING_PLANE_CARS,
                )

                if sprite is not None and sprite[1] < MAX_CAR_SCALED_WIDTH:
                    sprite_pos, scaled_w, scaled_h = sprite
                    # Anchor point at bottom, centre
                    sprite_pos -= g2.Vector(scaled_w // 2, scaled_h)
                    profile_scale = Profiler()
                    scaled = scale_image(img, int(scaled_w), int(scaled_h))
                    times["car_scale"] += profile_scale.get_ms()

                    # We can't send it to the draw list just yet as there might be more than one car on this track
                    # piece and we need to draw them in order starting from the one furthest from the camera.
                    # So we'll add it to a list to sort and draw later
                    cars_to_draw.append(
                        (
                            float(car.pos.z),
                            lambda scaled=scaled, pos=sprite_pos: (
                                renderer.draw_image(scaled, xy(pos))
                            ),
                        )
                    )

                    if SHOW_CPU_CAR_SPEEDS and isinstance(car, CPUCar):
                        output: str = f"{car.target_speed:.0f}"
                        label_at = xy(sprite_pos)
                        add_to_draw_list(
                            lambda pos=label_at, output=output: draw_text(
                                output, pos[0], pos[1] - 40
                            )
                        )

            times["prepare_draw_cars"] += profile_prepare_draw_cars.get_ms()

            # Draw the cars that are on the current track piece,starting from the one with the lowest Z position
            cars_to_draw.sort(key=lambda entry: entry[0], reverse=True)
            for _, drawcall in cars_to_draw:
                add_to_draw_list(drawcall, "cars")

        # Draw everything in draw_list, in reverse order - so that items furthest ahead are drawn first
        for draw_call, type in reversed(draw_list):
            profiler: Profiler = Profiler()
            draw_call()
            times[type] = times.get(type, 0) + profiler.get_ms()

        # Is there an actual player car, or are we in demo mode?
        if self.player_car is not None:
            # Show info text
            # Adapt to varying window widths by using fractions of WIDTH instead of absolute coordinates

            player_pos: int = self.cars.index(self.player_car) + 1

            # Show race complete or time up screens if relevant
            if self.time_up:
                draw_text("TIME UP!", WIDTH // 2, HEIGHT * 0.4, centre=True)

            elif self.race_complete:
                # (a race can only be completed by finishing laps, so a fastest lap exists)
                assert self.player_car.fastest_lap is not None
                draw_text(
                    "RACE COMPLETE!", WIDTH // 2, HEIGHT * 0.15, centre=True
                )
                draw_text("POSITION", WIDTH // 2, HEIGHT * 0.3, centre=True)
                draw_text(
                    str(player_pos), WIDTH // 2, HEIGHT * 0.42, centre=True
                )
                draw_text(
                    "FASTEST LAP", WIDTH * 0.25, HEIGHT * 0.55, centre=True
                )
                draw_text(
                    format_time(self.player_car.fastest_lap),
                    WIDTH * 0.25,
                    HEIGHT * 0.68,
                    centre=True,
                )
                draw_text("RACE TIME", WIDTH * 0.75, HEIGHT * 0.55, centre=True)
                draw_text(
                    format_time(self.player_car.race_time),
                    WIDTH * 0.75,
                    HEIGHT * 0.68,
                    centre=True,
                )

            else:
                # Race not complete - show status text at top of screen

                # Show status background
                status_x: float = (WIDTH / 2) - (565 / 2)
                blit("status", status_x, 0)

                # Show lap
                draw_text(
                    f"{self.player_car.lap:02}",
                    status_x + 30,
                    37,
                    font="status1b_",
                )

                # Show position
                draw_text(
                    f"{player_pos:02}", status_x + 116, 37, font="status1b_"
                )

                # Show speed
                draw_text(
                    f"{int(self.player_car.speed):03}",
                    status_x + 197,
                    37,
                    font="status1b_",
                )

                # Show lap time
                draw_text(
                    format_time(self.player_car.lap_time),
                    status_x + 299,
                    37,
                    font="status2_",
                )

                # Show fastest lap
                if (
                    self.player_car.last_lap_was_fastest
                    and self.player_car.lap_time < 4
                ):
                    assert self.player_car.fastest_lap is not None
                    y: float = HEIGHT * 0.4
                    draw_text("FASTEST LAP!", WIDTH // 2, y, centre=True)
                    draw_text(
                        format_time(self.player_car.fastest_lap),
                        WIDTH // 2,
                        y + 60,
                        centre=True,
                    )

                # Show final lap text
                # If we're currently showing fastest lap text, wait for that to disappear before showing the final
                # lap text
                if self.player_car.last_lap_was_fastest:
                    begin_time, end_time = 4, 8
                else:
                    begin_time, end_time = 0, 4
                if (
                    self.player_car.lap == NUM_LAPS
                    and begin_time < self.player_car.lap_time < end_time
                ):
                    y = HEIGHT * 0.4
                    draw_text("FINAL LAP!", WIDTH // 2, y, centre=True)

        # Show debug text
        if SHOW_DEBUG_TEXT:
            for i, line in enumerate(self.on_screen_debug_strs):
                draw_system_text(line, 0, 50 + i * 20)
        self.on_screen_debug_strs.clear()

        if SHOW_PROFILE_TIMINGS:
            print(prof_track, sum(times.values()))
            print(self.frame_counter, times)

    # Returns index of track piece at the specified Z position, or None if the specified position is off the end
    # of the track
    # e.g. track piece 0 goes from Z 0 to -0.999, etc
    def get_track_piece_for_z(self, z: float) -> int | None:
        idx: int = -int(z / SPACING)
        return None if idx >= len(self.track) else idx

    # Returns index and Z position of first track piece ahead of or exactly at the specified Z position, or None and
    # that Z if the specified position is off the end of the track
    def get_first_track_piece_ahead(self, z: float) -> tuple[int | None, float]:
        idx: int = -int(math.floor(z / SPACING))
        first_piece_z: float = -idx * SPACING
        return (None if idx >= len(self.track) else idx), first_piece_z

    def play_sound(self, name: str, count: int = 1) -> None:
        # Some sounds have multiple varieties, named "name0", "name1", ... If count > 1, we'll randomly choose one
        try:
            sounds.load(f"{name}{randint(0, count - 1)}").play()
        except Exception as e:
            # If no sound file of that name was found, print the error, which includes the filename.
            # Also occurs if sound fails to play for another reason (e.g. if this machine has no sound hardware)
            print(e)


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


def update(delta_time: float) -> None:
    # delta_time is the time passed (in seconds) since the previous frame
    global state, game, accumulated_time, demo_reset_timer, demo_start_timer

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
            # Check for player starting game with either keyboard or controller
            controls: Controls | None = button_pressed_controls(0)
            if controls is not None:
                # Switch to play state, and create a new Game object, passing it a controls object
                state = State.PLAY
                game = Game(controls)

            # If the demo race has been running for a while, reset it, otherwise the AI cars will run out of track!
            demo_reset_timer -= delta_time
            demo_start_timer += delta_time
            if demo_reset_timer <= 0:
                game = Game()
                demo_reset_timer = 60 * 2
                demo_start_timer = 0

        case State.PLAY:
            if game.race_complete:
                state = State.GAME_OVER

        case State.GAME_OVER:
            if button_pressed_controls(0) is not None:
                # Go back into demo/title screen mode - create a new Game object without a player
                # First stop the player car's engine sound (a finished game always has a player car)
                assert game.player_car is not None
                game.player_car.stop_engine_sound()

                state = State.TITLE
                game = Game()
                music.play("title_theme")

        case _:
            raise ValueError(f"unhandled game state {state!r}")

    # Call game.update each time while accumulated_time is above FIXED_TIMESTEP. If it is double or more of FIXED_TIMESTEP,
    # which would occur if the frame rate is low, we call game.update two or more times per frame
    accumulated_time += delta_time
    while accumulated_time >= FIXED_TIMESTEP:
        accumulated_time -= FIXED_TIMESTEP
        game.update(FIXED_TIMESTEP)


def draw() -> None:
    game.draw()

    if state == State.TITLE:
        if demo_reset_timer < 1 or demo_start_timer < 1:
            # Fade out screen prior to resetting demo game, and fade in whenever demo (re)starts
            # Draw a black image with gradually increasing/decreasing opacity
            # An alpha value of 255 is fully opaque, 0 is fully transparent
            value: float = (
                demo_reset_timer if demo_reset_timer < 1 else demo_start_timer
            )
            alpha: float = min(255, 255 - (value * 255))
            # Fill resets the surface to opaque black, then set_alpha scales its alpha down to the fade level
            fade_to_black_image.fill((0, 0, 0, 255))
            fade_to_black_image.set_alpha(alpha)
            renderer.draw_image(fade_to_black_image, (0, 0))

        # Construct start game text
        # On macOS, encourage the user to use Z instead of left control to accelerate, because
        # Ctrl+arrow is the keyboard shortcut to switch desktop
        text: str = f"PRESS {SPECIAL_FONT_SYMBOLS['xb_a']} OR {'Z' if 'Darwin' in platform.version() else 'LEFT CONTROL'}"

        # Draw start game text
        draw_text(text, WIDTH // 2, HEIGHT - 82, True)

        # Draw logo - centred on X axis, centred on top third of the screen on Y axis
        logo: Image = images.load("logo")
        renderer.draw_image(
            logo, (WIDTH // 2 - logo.width // 2, HEIGHT // 3 - logo.height // 2)
        )


##############################################################################

# Start the music (with no sound device the game simply plays silently)
music.play("title_theme")

# Set up controls
keyboard_controls: KeyboardControls = KeyboardControls()
joystick_controls: JoystickControls | None
setup_joystick_controls()

# Set up initial state and Game object
state: State = State.TITLE
game: Game = Game()

demo_reset_timer: float = 2 * 60  # Demo race resets after 2 mins
demo_start_timer: float = 0

accumulated_time: float = 0

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

# Fixed 60 Hz timestep -- update(dt) accumulates it into fixed steps. PGZERO_MAX_FRAMES=N
# (set by the headless frame-capture harness) stops after N frames.
_max_frames = int(os.environ.get("PGZERO_MAX_FRAMES", "0") or 0)
_dt = 1.0 / 60.0
_next_t = time.perf_counter()
_frame_count = 0
try:
    while not glfw.window_should_close(window):
        glfw.poll_events()
        update(_dt)
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
