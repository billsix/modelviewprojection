# Code the Classics port: avenger, with its rendering engine inlined.
#
# Game code derived from Raspberry Pi Press's "Code the Classics" (vol 2):
#   Copyright (c) 2024 Eben Upton <eben@raspberrypi.com>
# Inlined engine (audio, images, renderer, keyboard, loop):
#   Copyright (c) 2026 William Emerison Six
# SPDX-License-Identifier: BSD-2-Clause
# Full license text: ports/codetheclassics/LICENSE.
"""avenger -- Defender style side-scrolling shooter with abductable humans,
from Code the Classics vol. 2, on GLFW + OpenGL 3.3 core.

One self-contained file, read top to bottom like the course's demos: first
the small engine this game needs (a software audio mixer with looping,
fading and per-shot volume, an image loader and a terrain mask, a
textured-quad renderer with a scissor clip and debug lines, the anchored
Actor sprite, keyboard and gamepad state), then the game, then the loop the
game itself owns.
"""

from __future__ import annotations

import math
import os
import signal
import sys
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Generator, Iterator
from dataclasses import InitVar, dataclass, field
from enum import Enum, IntEnum
from random import randint, uniform
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, cast, override

import gacalc.g3 as g3
import glfw
import numpy as np
import OpenGL.GL as GL
import sympy
from gacalc.g2 import Vector
from gacalc.transforms import (
    MatrixTemplate,
    compose,
    scale_non_uniform,
    to_matrix,
    translate,
)
from numpy.typing import NDArray
from PIL import Image as PILImage

# ===== engine: shared state =====

WIDTH: int = 960
HEIGHT: int = 540
TITLE: str = "Avenger"

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
class Mask:
    """A per-pixel opacity grid (True where opaque), for terrain collision.
    Built by :meth:`Mask.from_image`."""

    opaque: NDArray[np.bool_]

    @property
    def width(self) -> int:
        return int(self.opaque.shape[1])

    @property
    def height(self) -> int:
        return int(self.opaque.shape[0])

    def get_at(self, pos: PointLike) -> bool:
        """Return whether the pixel at ``pos`` is opaque (False out of bounds)."""
        px, py = pos
        x, y = int(px), int(py)
        return (
            0 <= x < self.width
            and 0 <= y < self.height
            and bool(self.opaque[y, x])
        )

    @classmethod
    def from_image(cls, image: Image, threshold: int = 127) -> Mask:
        """The mask of ``image``: pixels with alpha above ``threshold`` are opaque."""
        return cls(image.rgba[..., 3] > threshold)


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


_TX, _TY, _W, _H = sympy.symbols("tx ty w h")
#: The model matrix: scale the unit quad to (w, h), then translate to (tx, ty);
#: ``MODEL.fill(tx, ty, w, h)``
MODEL: MatrixTemplate = compose(
    [
        translate(b=_TX * g3.Vector.e_1 + _TY * g3.Vector.e_2),
        scale_non_uniform(_W, _H, 1),
    ]
).to_matrix_template(g3.Vector, (_TX, _TY, _W, _H))


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
# each frame -- they are the only keys avenger reads.

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

LEVEL_WIDTH: int = 4096
LEVEL_HEIGHT: int = 640

WAVE_COMPLETE_SCREEN_DURATION: int = 320

SHOW_DEBUG_LINES: bool = False

# These positions are all relative to the terrain image, which is displayed with an offset from the top of the game world
HUMAN_START_POS = (
    (204, 410),
    (489, 209),
    (865, 374),
    (1262, 405),
    (1937, 263),
    (2193, 278),
    (2601, 405),
    (2846, 347),
    (3317, 193),
    (3646, 233),
)

TERRAIN_OFFSET_Y: int = 160

# Utility functions


def sign(x: float) -> int:
    # Returns 1, 0 or -1 depending on whether number is positive, zero or negative
    return 0 if x == 0 else -1 if x < 0 else 1


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


# For animations which should run from the first frame to the last frame and then backwards through those frames
# before repeating
def forward_backward_animation_frame(frame: int, num_frames: int) -> int:
    # With 4 frames, the repeating sequence should be 0, 1, 2, 3, 2, 1
    if num_frames < 2:
        return 0
    frame %= (num_frames * 2) - 2
    if frame >= num_frames:
        frame = (num_frames - 1) * 2 - frame
    return frame


class GameObject(Protocol):
    """What Game.update and Game.draw need of the scrolling objects: a per-frame
    update and a draw at a scroll offset. Every WrapActor subclass below
    satisfies it structurally (deliberately not by subclassing the protocol --
    an explicit subclass inherits the stub members, so a missing method would
    go unreported).
    """

    def update(self) -> bool | None: ...

    def draw_at(self, offset_x: float, offset_y: float) -> None: ...


# ABC = abstract base class - a class which is only there to serve as a base class, not to be instantiated directly
class Controls(ABC):
    NUM_BUTTONS: ClassVar[int] = 1

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
    def get_x(self) -> int:
        # Overridden by subclasses
        pass

    @abstractmethod
    def get_y(self) -> int:
        # Overridden by subclasses
        pass

    @abstractmethod
    def button_down(self, button: int) -> bool:
        # Overridden by subclasses
        pass

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
        return button == 0 and keyboard.space


class JoystickControls(Controls):
    __slots__ = ("joystick",)

    def __init__(self, joystick: Joystick) -> None:
        super().__init__()
        self.joystick: Joystick = joystick

    def get_axis(self, axis_num: int) -> int:
        # First check if there is an input on the dpad for the X axis. The dpad is classified here as a joystick 'hat'
        if (
            self.joystick.get_numhats() > 0
            and self.joystick.get_hat(0)[axis_num] != 0
        ):
            # For some reason, dpad up/down are inverted when getting inputs from
            # an Xbox controller, so need to negate the value if axis_num is 1
            return self.joystick.get_hat(0)[axis_num] * (
                -1 if axis_num == 1 else 1
            )

        # If no input on the dpad, check for analogue left/right input, with a dead-zone, as digital movement
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


# This class encapsulates the concept of an object in a scrolling game world that wraps around at the edges
class WrapActor(Actor):
    __slots__ = ()

    def __init__(self, image: str, pos: PointLike) -> None:
        super().__init__(image, pos)

    def update(self) -> bool | None:
        # subclasses that return a destroy-flag narrow this to ``bool``;
        # the base (and most subclasses) return None.
        # If the actor goes off the left or right edge of the game world, relative to the player,
        # wrap it back round to the other side
        while self.x - game.player.x < -LEVEL_WIDTH / 2:
            self.relocate(LEVEL_WIDTH)
        while self.x - game.player.x > LEVEL_WIDTH / 2:
            self.relocate(-LEVEL_WIDTH)

    def draw_at(self, offset_x: float, offset_y: float) -> None:
        # offset_x/y are for scrolling. Not an override of Actor.draw: it takes
        # the offsets, so it has its own name.
        # Before drawing the sprite, we adjust the actor's position to take account of scrolling,
        # moving it into screen space
        self.pos = (self.x + offset_x, self.y + offset_y)

        self.draw()

        # After drawing, we shift the actor's position back into world space
        self.pos = (self.x - offset_x, self.y - offset_y)

    def relocate(self, delta: float) -> None:
        self.x += delta


# A bullet fired by an enemy
# (eq=False on these Actor dataclasses keeps identity comparison/hashing --
# the generated __eq__ would compare fields and set __hash__ to None; slots=True
# fixes each object's attribute set to its declared fields, so every attribute
# an object ever gets is declared below)
@dataclass(eq=False, slots=True)
class Bullet(WrapActor):
    #: named spawn_pos, NOT pos: pos is an Actor property, and a dataclass
    #: would treat the property object as this field's default value
    spawn_pos: InitVar[PointLike]
    velocity: Vector

    def __post_init__(self, spawn_pos: PointLike) -> None:
        super().__init__("blank", spawn_pos)
        distance: float = float(
            (Vector(*spawn_pos) - game.player.pos).magnitude()
        )
        volume: float = remap_clamp(distance, 400, 2500, 1, 0)
        game.play_sound("enemy_laser", volume=volume)

    def update(self) -> bool:
        super().update()

        self.pos = self.pos + self.velocity

        # Update sprite animation
        self.image = f"bullet{(game.timer // 4) % 2}"

        # Return True or False depending on whether we want the bullet to be destroyed, either when it's hit something,
        # or because it's gone too far from the player.
        too_far: bool = (
            self.x < game.player.x - WIDTH or self.x > game.player.x + WIDTH
        )
        return game.player.hit_test(self.pos) or too_far


# A laser fired by the player
# Not a dataclass: the super-args (image, pos) are computed from vel_x/x/y.
class Laser(WrapActor):
    __slots__ = ("vel_x", "anim_timer")

    def __init__(self, x: float, y: float, vel_x: float) -> None:
        facing_idx: int = 0 if vel_x > 0 else 1
        image: str = f"laser_{facing_idx}_0"
        super().__init__(image, pos=(x + vel_x, y))
        self.vel_x: float = vel_x
        self.anim_timer: int = 0
        game.play_sound("player_shoot")

    @override
    def update(self) -> bool:
        super().update()

        # Update position
        self.x += self.vel_x

        # Update sprite
        self.anim_timer += 1
        facing_idx: int = 0 if self.vel_x > 0 else 1
        self.image = f"laser_{facing_idx}_{min(1, self.anim_timer // 8)}"

        # For Laser and Bullet, the update methods return True or False depending on whether we want them to be
        # destroyed. This is either because they've hit something, or because they've gone too far from the player.
        too_far: bool = abs(self.x - game.player.x) > 800

        # This list comprehension calls laser_hit_test with this laser's position for each enemy and human in the level.
        # We end up with a list of boolean (True or False) values. By getting the sum of the resulting list, we can
        # tell how many collisions occurred. This works because when converting a boolean to an integer in Python,
        # True is equivalent to 1 and False is equivalent to 0.
        # This will also kill any enemy of human that collides with the laser
        targets: list[Enemy | Human] = [*game.enemies, *game.humans]
        collisions: list[bool] = [
            obj.laser_hit_test(self.pos) for obj in targets
        ]

        return too_far or sum(collisions) > 0


@dataclass(eq=False, slots=True)
class Player(WrapActor):
    # Drag for X and Y axes - closer to 1 = less drag, higher top speed
    DRAG: ClassVar[Vector] = Vector(0.98, 0.9)

    # Force for X and Y axes - higher numbers = more acceleration, higher top speed
    FORCE: ClassVar[Vector] = Vector(0.2, 0.5)

    # Number of frames for which the player ship plays its explode animation
    EXPLODE_ANIM_SPEED: ClassVar[int] = 4
    EXPLODE_FRAMES: ClassVar[int] = 18 * EXPLODE_ANIM_SPEED

    class Timer(IntEnum):
        HURT = 0
        FIRE = 1
        ANIM = 2
        EXPLODE = 3

    controls: Controls
    velocity: Vector = field(default_factory=lambda: Vector(0, 0))
    lives: int = 5
    shields: int = 5
    extra_life_tokens: int = 0
    facing_x: int = 1
    tilt_y: int = 0
    #: We store and update the timers as a list of four numbers, the indices corresponding to the values in the
    #: Timer enum above
    timers: list[int] = field(default_factory=lambda: [0, 0, 0, 0])
    frame: int = 0
    carried_human: Human | None = None
    #: Our radar blip
    blip: Actor = field(default_factory=lambda: Actor("dot-white"))
    #: Thrust sprite
    thrust_sprite: WrapActor = field(
        default_factory=lambda: WrapActor("blank", (0, 0))
    )
    thrust_sound_playing: bool = False
    #: The looping thrust sound, loaded in __post_init__ (None if it can't be)
    thrust_sound: Sound | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        super().__init__("blank", (WIDTH / 2, LEVEL_HEIGHT / 2))

        # Load thrust sound. This is not played with Game.play_sound as it requires custom behaviour - looping and
        # fading in/out. Enclosed in a try/except section to deal with the case where the sound file can't be loaded,
        # which can occur if there is no sound hardware or sound is disabled
        try:
            self.thrust_sound = sounds.load("thrust0")
        except Exception:
            self.thrust_sound = None

    def hit_test(self, pos: PointLike) -> bool:
        # Check if the given position falls within the bounds of the player sprite

        # If we're dead or in the explode animation, always return false
        if self.lives == 0 or self.timers[Player.Timer.EXPLODE] > 0:
            return False

        # As the sprite's rectangle is bigger than the actual visible part of the sprite (see e.g. ship0.png),
        # instead of calling self.colliderect, we just check to see whether the given position is within 40 pixels
        # of the centre of the sprite on the X axis, and within 15 pixels of the centre on the Y axis
        px, py = pos  # tuple OR gacalc vector
        if abs(px - self.x) < 40 and abs(py - self.y) < 15:
            # If there's a collision, set the 'hurt' timer so that we glow to indicate damage, and decrease shields
            # by 1
            self.timers[Player.Timer.HURT] = 60
            self.shields -= 1

            game.play_sound("player_hit")

            if self.shields == 0:
                # Lose a life
                self.lives -= 1

                # If it's game over and we're playing the thrust sound, stop it
                if self.lives == 0 and self.thrust_sound_playing:
                    if self.thrust_sound is not None:
                        self.thrust_sound.fadeout(200)
                    self.thrust_sound_playing = False

                # Explode, later we will respawn in a random position
                game.play_sound("player_explode")
                self.timers[Player.Timer.EXPLODE] = Player.EXPLODE_FRAMES

                # Any human we're carrying when we lose a life will be dropped
                if self.carried_human is not None:
                    self.carried_human.dropped()
                    self.carried_human = None

            return True
        else:
            return False

    @override
    def update(self) -> None:
        # Decrease all timer values by 1
        self.timers = [i - 1 for i in self.timers]

        # If we're currently exploding, don't do any of the normal behaviour, just set our sprite to the appropriate
        # frame, then randomise our position when the timer runs out
        if self.timers[Player.Timer.EXPLODE] > 0:
            # Work out animation frame and set sprite image
            frame: int = (
                Player.EXPLODE_FRAMES - self.timers[Player.Timer.EXPLODE]
            ) // Player.EXPLODE_ANIM_SPEED
            self.image = f"ship_explode{frame}"

            # No thrust sprite while exploding
            self.thrust_sprite.image = "blank"

            # Respawn in new location if timer is about to run out, unless we're out of lives
            if self.timers[Player.Timer.EXPLODE] == 1 and self.lives > 0:
                self.respawn()

        elif self.lives == 0:
            # If we're not exploding but out of lives, hide the sprite and don't do anything else
            self.image = "blank"
            self.thrust_sprite.image = "blank"

        else:
            # Not exploding or dead
            x_input: int = self.controls.get_x()
            y_input: int = self.controls.get_y()

            move: Vector = Vector(x_input, y_input)

            self.tilt_y = y_input

            if x_input != 0:
                self.facing_x = sign(x_input)

            # Only apply movement force on X axis if player facing the same direction they're trying to accelerate in,
            # and the ship has fully animated to that facing direction
            if self.frame % 8 != 0 or sign(self.facing_x) != sign(
                float(move.x)
            ):
                move = Vector(0, move.y)

            self.velocity = Vector(
                self.velocity.x * Player.DRAG.x + move.x * Player.FORCE.x,
                self.velocity.y * Player.DRAG.y + move.y * Player.FORCE.y,
            )

            # Apply velocity to position
            self.pos = self.pos + self.velocity

            # Limit Y position
            self.y = max(0, min(LEVEL_HEIGHT, self.y))

            # Update radar blip position
            self.blip.pos = game.radar.radar_pos(self.pos)

            # Check to see if we can pick up a falling human
            if self.carried_human is None:
                for human in game.humans:
                    if (
                        human.can_be_picked_up_by_player()
                        and (human.pos - self.pos).magnitude() < 40
                    ):
                        human.picked_up(self)
                        self.carried_human = human
                        break
            else:
                # If we're carrying a human, update their position and check if are they in a place where they can be
                # safely deposited on the ground
                self.carried_human.pos = self.pos + Vector(0, 50)
                if self.carried_human.terrain_check():
                    self.carried_human.dropped()
                    self.carried_human = None
                    game.play_sound("rescue_prisoner")

            # The last part of this method deals with deciding which sprite to display, and if we're on an appropriate
            # animation frame, also checks to see if the player wants to fire

            # Ship sprites start with either "ship" or "hurt"
            # Frames 0 and 8 are the ship facing right and left. There are variations for these frames for the ship
            # tilting up and down - e.g. ship0d, used when moving down
            # Frames 1 to 7 and 9 to 15 are for when the ship flips over to change its facing direction. These do not
            # have tilted up/down variations.
            target: int = 8 if self.facing_x < 0 else 0

            if self.frame == target:
                # If we're on our target frame, and we haven't fired too recently, we're allowed to fire
                if (
                    self.controls.button_down(0)
                    and self.timers[Player.Timer.FIRE] <= 0
                ):
                    self.timers[Player.Timer.FIRE] = 10
                    # Create a laser with the appropriate offset from the player
                    laser_vel_x: float = self.velocity.x + 20 * self.facing_x
                    laser_x: float = self.x + 40 * self.facing_x
                    laser_y: float = self.y + self.get_laser_fire_y_offset()
                    game.lasers.append(Laser(laser_x, laser_y, laser_vel_x))
            else:
                # If we're not on our target frame, animate towards it every three game frames
                if self.timers[Player.Timer.ANIM] <= 0:
                    self.timers[Player.Timer.ANIM] = 3
                    #  We always animate forward through the frames, wrapping back to zero when we hit 16
                    self.frame = (self.frame + 1) % 16

            # Fade thrust sound in or out depending on whether we're thrusting
            # Ship must be fully facing in the direction player is trying to move in, for the thrust to occur
            if self.thrust_sound is not None:
                if (
                    move.x != 0
                    and self.frame == target
                    and not self.thrust_sound_playing
                ):
                    self.thrust_sound.set_volume(0.3)
                    # Loop indefinitely, fade in
                    self.thrust_sound.play(loops=-1, fade_ms=200)
                    self.thrust_sound_playing = True
                elif (
                    move.x == 0 or self.frame != target
                ) and self.thrust_sound_playing:
                    self.thrust_sound.fadeout(200)
                    self.thrust_sound_playing = False

            anim_type: str = (
                "ship" if self.timers[Player.Timer.HURT] <= 0 else "hurt"
            )
            tilt: str = (
                ("u" if self.tilt_y < 0 else "d")
                if self.frame % 8 == 0 and self.tilt_y != 0
                else ""
            )

            # Set sprite
            self.image = f"{anim_type}{self.frame}{tilt}"

            # Set thrust sprite
            if self.frame % 8 != 0 or move.x == 0:
                self.thrust_sprite.image = "blank"
            else:
                direction: int = 0 if move.x > 0 else 1
                frame = (game.timer // 3) % 2
                self.thrust_sprite.image = f"boost_{direction}_{frame}"
                x_offset: int = 66
                y_offset: int = -3
                self.thrust_sprite.pos = self.pos + Vector(
                    x_offset * -move.x, y_offset
                )

    def respawn(self) -> None:
        # Restore shields
        self.shields = 5

        def wrap_distance(x1: float, x2: float) -> float:
            # Return the distance between two X positions, taking the wrapping nature of the level
            # into account
            dist: float = abs(
                x1 % LEVEL_WIDTH - x2 % LEVEL_WIDTH
            )  # distance without wrapping
            return dist if dist < LEVEL_WIDTH / 2 else LEVEL_WIDTH - dist

        # Try several random positions and assign a score to each one, choosing the one which is furthest from
        # any one enemy on the X axis
        best_score: float = 0
        for _ in range(20):
            random_pos: Vector = Vector(
                uniform(0, LEVEL_WIDTH - 1), uniform(150, 300)
            )
            if not game.enemies:
                # If there are no enemies, just go with the first random position
                self.pos = random_pos
                break
            else:
                # If there are enemies, score the random position based on how far away the closest
                # enemy is on the X axis - the further the better
                all_distances: list[float] = [
                    wrap_distance(enemy.x, float(random_pos.x))
                    for enemy in game.enemies
                ]
                score: float = min(all_distances)
                if score >= best_score:
                    self.pos = random_pos
                    best_score = score

    def flash(self, offset_x: float, offset_y: float) -> None:
        # Displays a flash sprite at the point where a laser turret fires. Only allowed if we're on an appropriate
        # animation frame, and if we've just fired within the last few frames
        # offset_x/y are for scrolling
        if self.frame % 8 == 0 and self.timers[Player.Timer.FIRE] > 5:
            # flash0 is for when the ship is facing right (frame 0), flash1 for facing left (frame 8), so by doing
            # an integer division of self.frame by 8 we get the correct flash frame number
            blit(
                f"flash{self.frame // 8}",
                self.x + offset_x - 25,
                self.y + offset_y - 13 + self.get_laser_fire_y_offset(),
            )

    def get_laser_fire_y_offset(self) -> int:
        # The starting Y position of the laser should vary by a few pixels depending on how the ship is tilted
        # We can achieve this using a list of three values and then indexing into that list using the ship's
        # tilt_y (which will be either -1, 0 or 1)
        return [-1, 3, 2][self.tilt_y + 1]

    @override
    def draw_at(self, offset_x: float, offset_y: float) -> None:
        # Draw the sprite with the given offset to account for scrolling, and with laser firing flash if required

        # Depending on the tilt of the ship, we draw the laser firing flash either before or after the ship itself
        # This is because the laser is fired from the underside of the ship, if the ship was tilting down and we
        # displayed the laser after the ship, it would display through the ship.
        if self.tilt_y == 1:
            self.flash(offset_x, offset_y)

        # Call the WrapActor draw method
        super().draw_at(offset_x, offset_y)

        # Draw thrust sprite (blip is done in Game.draw_ui)
        self.thrust_sprite.draw_at(offset_x, offset_y)

        if self.tilt_y != 1:
            self.flash(offset_x, offset_y)

    def is_carrying_human(self) -> bool:
        return self.carried_human is not None

    def level_ended(
        self, shield_restore_amount: int, humans_saved: int
    ) -> None:
        self.shields = min(self.shields + shield_restore_amount, 5)

        # Earn an extra life token if all humans were saved
        if humans_saved == 10:
            self.extra_life_tokens += 1
            # Get an extra life if we get 3 life tokens
            if self.extra_life_tokens >= 3:
                self.lives += 1
                self.extra_life_tokens -= 3


class Radar(Actor):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("radar", pos=(WIDTH / 2, 4), anchor=("center", "top"))

    def radar_pos(self, pos: PointLike) -> tuple[float, float]:
        # Converts a position in world space into a position on the radar in screen space
        px, py = pos  # tuple OR gacalc vector
        return (
            self.left + ((int(px) % LEVEL_WIDTH) / 11.5),
            self.y + (int(py) // 11),
        )


class EnemyState(Enum):
    START = 0
    ALIVE = 1
    EXPLODING = 2
    DEAD = 3


class EnemyType(Enum):
    LANDER = 0
    MUTANT = 1
    BAITER = 2
    POD = 3
    SWARMER = 4


# Not a dataclass: init branches on type for speeds/state, and generates a
# random position/target in a fixed RNG order -- the init logic is the
# interesting part.
class Enemy(WrapActor):
    __slots__ = (
        "type",
        "max_speed",
        "acceleration",
        "target_pos",
        "update_target_timer",
        "velocity",
        "state",
        "state_timer",
        "target_human",
        "carrying",
        "bullet_timer",
        "fire_angle",
        "blip",
        "anim_timer",
    )

    def __init__(
        self,
        start_timer: int = 0,
        type: EnemyType = EnemyType.LANDER,
        pos: PointLike | None = None,
        start_vel: Vector | None = None,
    ) -> None:
        # Varying start_timer allows the creation of enemies which wait a while before beginning their 'appear'
        # animation, the default value of zero means the appear animation will start immediately.

        # If no position has been supplied, generate a random position
        if pos is None:
            pos = (randint(0, LEVEL_WIDTH - 1), randint(32, LEVEL_HEIGHT - 32))

        # Call Actor constructor
        super().__init__("blank", pos)

        self.type: EnemyType = type

        match self.type:
            case EnemyType.LANDER:
                self.max_speed: int = 5
                self.acceleration: float = 0.1
            case EnemyType.MUTANT:
                self.max_speed = 9
                self.acceleration = 0.5
            case EnemyType.BAITER:
                self.max_speed = 9
                self.acceleration = 0.01
            case EnemyType.POD:
                self.max_speed = 10
                self.acceleration = 0.03
            case EnemyType.SWARMER:
                self.max_speed = 8
                self.acceleration = 1
            case _:
                raise ValueError(f"unhandled enemy type {self.type!r}")

        # Select a target position which the enemy will oscillate around. If the enemy is within a particular
        # distance of the player, this will be updated to a random offset from the player's current position, unless
        # the target pos is already close to the player
        self.target_pos: Vector = Vector(
            self.x + uniform(-100, 100), self.y + uniform(-100, 100)
        )
        self.update_target_timer: int = 0

        self.velocity: Vector = (
            start_vel if start_vel is not None else Vector(0, 0)
        )

        # Most enemies start in 'start' state where they play an animation to appear. Swarmers just appear immediately
        match self.type:
            case EnemyType.SWARMER:
                self.state: EnemyState = EnemyState.ALIVE
                self.state_timer: int = 0
            case _:
                self.state = EnemyState.START
                self.state_timer = start_timer

        # Enemies will sometimes pick up humans and carry them into the sky, turning them into mutants
        self.target_human: Human | None = None
        self.carrying: bool = False

        # Counts down, allowed to shoot when zero or lower
        self.bullet_timer: int = randint(30, 90)

        # This is only used for baiter enemies, which fire in a fixed pattern of ever-increasing angles
        self.fire_angle: float = 0

        # Create our radar blip
        self.blip: Actor = Actor("dot-red")

        self.anim_timer: int = randint(0, 47)

    @override
    def relocate(self, delta: float) -> None:
        super().relocate(delta)

        self.target_pos += Vector(delta, 0)

    def laser_hit_test(self, pos: PointLike) -> bool:
        # Given a position, see if it falls within this sprite's rectangle (but only if we're in the alive state)
        # Kill the enemy if it is touching this position
        if not (self.collidepoint(pos) and self.state == EnemyState.ALIVE):
            return False

        self.state = EnemyState.EXPLODING
        self.state_timer = 0
        self.anim_timer = 0
        if self.target_human is not None:
            if self.carrying:
                self.target_human.dropped()
            self.target_human = None
            self.carrying = False
        game.play_sound("enemy_explode", 6)

        # If we're a pod, release several swarmers
        if self.type == EnemyType.POD:
            for _ in range(3):
                start_vel: Vector = Vector(uniform(-25, 25), uniform(-25, 25))
                game.enemies.append(Enemy(0, EnemyType.SWARMER, pos, start_vel))

        return True

    @override
    def update(self) -> None:
        super().update()

        match self.state:
            case EnemyState.START:
                self.state_timer += 1
                # When state timer hits 1, that means our appear animation has just started
                if self.state_timer == 1:
                    match self.type:
                        case EnemyType.MUTANT:
                            game.play_sound("enemy_appear_mutant")
                        case EnemyType.LANDER:
                            game.play_sound("enemy_appear_normal")
                        case EnemyType.BAITER:
                            game.play_sound("enemy_appear_ufo")
                        case EnemyType.POD | EnemyType.SWARMER:
                            pass  # appear silently

                # When state timer hits 33, we've finished the appear animation, so we switch to the alive state
                if self.state_timer == 33:
                    self.state = EnemyState.ALIVE

                elif self.state_timer >= 0:
                    # Play appear animation
                    self.image = f"appear{self.state_timer // 3}"

            case EnemyState.ALIVE:
                # Enemy is alive
                max_speed: float = self.max_speed

                # If we're targeting or carrying a human, check to see if they were shot by the player
                if self.target_human is not None and self.target_human.dead:
                    self.target_human = None
                    self.carrying = False

                # Should we start heading for a human to pick up?
                if (
                    self.target_human is None
                    and self.type == EnemyType.LANDER
                    and uniform(0, 1) < 0.001
                ):
                    # Find a human who isn't currently being carried, and isn't being targeted by another enemy
                    targeted_humans: list[Human] = [
                        enemy.target_human
                        for enemy in game.enemies
                        if enemy.target_human is not None
                    ]
                    available_humans: list[Human] = [
                        human
                        for human in game.humans
                        if human not in targeted_humans
                        and human.can_be_picked_up_by_enemy()
                    ]
                    if available_humans:
                        # Choose nearest human - i.e. the human with the minimum distance
                        # We use length_squared in this case to get the distance, instead of length, because length_squared
                        # is faster, and we don't care about what the actual distance is, just which distance is shortest
                        self.target_human = min(
                            available_humans,
                            key=lambda human: (
                                human.pos - self.pos
                            ).magnitude_squared(),
                        )

                # Try to move towards a target position. This will either be the player position, a human we're about to
                # pick up, the top of the sky (if we're carrying a human), or the previously determined target pos, which
                # is initially an offset from the starting position
                if self.target_human is not None:
                    if self.carrying:
                        # Carrying a human into the sky - target pos will be our current pos on the X axis
                        # and close to the top of the screen on the Y axis
                        self.target_pos = Vector(self.x, 64)
                        max_speed = 0.5

                        # If we reach the top of the screen, turn the captured human into a mutant enemy
                        if abs(self.y - self.target_pos.y) < 10:
                            game.enemies.append(
                                Enemy(
                                    type=EnemyType.MUTANT,
                                    pos=self.target_human.pos,
                                )
                            )
                            self.target_human.die()
                            self.target_human = None
                            self.carrying = False
                    else:
                        # If we're going to a human, we initially go to a position above them, then go down to pick
                        # them up. If our position on the X axis is sufficiently different from the human's, we're in
                        # the first phase. As we get closer, we reduce our max speed to ensure we don't overshoot
                        x_distance: float = abs(self.x - self.target_human.x)
                        if x_distance < 80:
                            # Slow down as we approach the human so we don't overshoot
                            max_speed = 1
                        if x_distance > 100:
                            # Set target pos to be above our target human's pos
                            self.target_pos = self.target_human.pos - Vector(
                                0, 200
                            )
                        else:
                            # Set target pos to our target human's pos. Start carrying them when we get within 55 pixels
                            self.target_pos = self.target_human.pos
                            distance: float = float(
                                (self.pos - self.target_pos).magnitude()
                            )
                            if distance < 55:
                                self.carrying = True
                                self.target_human.picked_up(self)
                else:
                    # No target human - go for our target position, and update target position every so often
                    self.update_target_timer -= 1
                    if self.update_target_timer <= 0:
                        # Update target pos
                        self.update_target_timer = 60

                        # Get player pos as a Vector
                        player_pos: Vector = game.player.pos

                        # Landers go for the player if they're nearby, other enemies will always go for
                        # the player regardless of distance
                        max_player_distance: int = (
                            500
                            if self.type == EnemyType.LANDER
                            else LEVEL_WIDTH
                        )

                        if (
                            self.pos - player_pos
                        ).magnitude() < max_player_distance:
                            # Go for the player
                            self.target_pos = player_pos

                        # In either case, we add a random offset to our target position. Baiter enemies have quite a large
                        # random variation
                        x_range: int = (
                            800 if self.type == EnemyType.BAITER else 100
                        )
                        y_range: int = (
                            300 if self.type == EnemyType.BAITER else 100
                        )
                        self.target_pos = self.target_pos + Vector(
                            uniform(-x_range, x_range),
                            uniform(-y_range, y_range),
                        )

                # Get a unit vector (i.e. a vector of length 1) from our current pos in the direction of the target
                # pos (can't call normalize() on a zero-length vector). This is used to determine the force applied
                # to our velocity
                distance = float((self.target_pos - self.pos).magnitude())
                vec: Vector = (
                    (self.target_pos - self.pos).normalize()
                    if distance > 0
                    else Vector(0, 0)
                )

                # The force we apply each frame will be a fraction of the unit vector (depending on accleration attribute)
                force: Vector = vec * self.acceleration

                # If we're near the top or bottom of the game world, apply an additional force
                # to push us away from the edge
                if self.y < 64:
                    force = Vector(force.x, force.y + 0.2)
                if self.y > LEVEL_HEIGHT - 64:
                    force = Vector(force.x, force.y - 0.2)

                # Apply force to velocity
                self.velocity += force

                # Limit max speed
                if self.velocity.magnitude() > max_speed:
                    # If we're over our max speed, slow down gradually over several frames, rather than slowing
                    # down suddenly. This is most relevant when max speed drastically decreases when we pick up a human.
                    self.velocity = self.velocity.normalize() * max(
                        self.velocity.magnitude() * 0.9, max_speed
                    )

                # Apply velocity to position
                self.pos = self.pos + self.velocity

                # If carrying, update carried human pos
                if self.carrying:
                    # carrying implies a target: make the invariant explicit
                    assert self.target_human is not None
                    self.target_human.pos = self.pos + Vector(0, 50)

                # Count down bullet timer, if it's zero or lower and enemy is near player (but not too near!),
                # fire a bullet
                self.bullet_timer -= 1
                if self.bullet_timer <= 0:
                    if self.type == EnemyType.BAITER:
                        # Baiters have their own firing pattern and don't care about the position of the player
                        velocity: Vector = (
                            Vector(
                                math.cos(self.fire_angle),
                                math.sin(self.fire_angle),
                            )
                            * 3
                        )
                        game.bullets.append(Bullet(self.pos, velocity))
                        self.bullet_timer = 8
                        self.fire_angle += 0.3

                    elif game.player.lives > 0:
                        # Other enemy types only fire if the player is alive
                        player_vec: Vector = game.player.pos - self.pos
                        player_distance: float = float(player_vec.magnitude())
                        if 100 < player_distance < 300:
                            # Fire bullet at the player, with a bit of random inaccuracy. The bullet speed will average 6 pixels
                            # per frame, although due to the way the random inaccuracy is added, this will vary
                            # Normalise player_vec (vector from us to player) to a unit vector
                            player_vec = player_vec.normalize()
                            velocity = (
                                Vector(
                                    player_vec.x + uniform(-0.5, 0.5),
                                    player_vec.y + uniform(-0.5, 0.5),
                                )
                                * 6
                            )
                            game.bullets.append(Bullet(self.pos, velocity))

                            # Non-baiter enemies fire at a random interval, with mutants firing more often
                            upper_limit: int = (
                                30 if self.type == EnemyType.MUTANT else 90
                            )
                            self.bullet_timer = randint(20, upper_limit)

                # Update sprite/animation
                match self.type:
                    case EnemyType.LANDER:
                        # Frame 0 if not picking up a human
                        # Frame 1 if close to picking up a human
                        # Frame 2 if picked up a human
                        frame: int = 0
                        if self.target_human is not None:
                            if self.carrying:
                                frame = 2
                            elif (
                                float(
                                    (
                                        self.pos - self.target_human.pos
                                    ).magnitude()
                                )
                                < 90
                            ):
                                frame = 1
                        self.image = f"lander{frame}"
                    case EnemyType.MUTANT:
                        self.anim_timer += 1
                        self.image = f"mutant{(self.anim_timer // 6) % 4}"
                    case EnemyType.BAITER:
                        self.anim_timer += 1
                        self.image = f"baiter{(self.anim_timer // 3) % 8}"
                    case EnemyType.POD:
                        # Frames 0 to 2 = left, 3 to 5 = right
                        self.anim_timer += 1
                        frame = forward_backward_animation_frame(
                            self.anim_timer // 6, 3
                        )
                        if self.velocity.x > 0:
                            frame += 3
                        self.image = f"pod{frame}"
                    case EnemyType.SWARMER:
                        self.anim_timer += 1
                        self.image = f"swarmer{(self.anim_timer // 6) % 8}"
                    case _:
                        raise ValueError(f"unhandled enemy type {self.type!r}")

            case EnemyState.EXPLODING:
                # There are 10 frames of the 'explode' animation
                # Update animation frame every 2 game frames. There are 10 frames of animation numbered from 0 to 9
                self.anim_timer += 1
                frame = self.anim_timer // 2
                self.image = f"enemy_explode{min(9, frame)}"

                if frame == 10:
                    # Animation finished, the enemy is now officially dead
                    self.state = EnemyState.DEAD

            case EnemyState.DEAD:
                pass  # waiting to be removed from the list

            case _:
                raise ValueError(f"unhandled enemy state {self.state!r}")

        # Update radar blip pos
        self.blip.pos = game.radar.radar_pos(self.pos)

    @override
    def draw_at(self, offset_x: float, offset_y: float) -> None:
        super().draw_at(offset_x, offset_y)

        # Debug
        if SHOW_DEBUG_LINES:
            renderer.line(
                self.pos + Vector(offset_x, offset_y),
                self.target_pos + Vector(offset_x, offset_y),
                (255, 255, 255),
            )


@dataclass(eq=False, slots=True)
class Human(WrapActor):
    spawn_pos: InitVar[PointLike]
    y_velocity: float = 0
    #: Our radar blip
    blip: Actor = field(default_factory=lambda: Actor("dot-green"))
    anim_timer: int = 0
    waving: bool = False
    dead: bool = False
    exploding: bool = False
    #: Who is carrying us: the player (to safety) or an enemy (to the sky)
    carrier: Player | Enemy | None = None
    falling: bool = False

    def __post_init__(self, spawn_pos: PointLike) -> None:
        super().__init__("blank", spawn_pos)

    def laser_hit_test(self, pos: PointLike) -> bool:
        # Given a position, see if it falls within this sprite's rectangle
        if self.exploding or not self.collidepoint(pos):
            return False
        self.die()
        return True

    @override
    def update(self) -> None:
        super().update()

        self.anim_timer += 1

        if self.exploding:
            # Play explode animation
            frame: int = self.anim_timer // 2
            if frame >= 10:
                self.dead = True
            else:
                # Switch to explosion sprites. We must store the current position and then re-set it after
                # changing the anchor position, so that the new anchor position correctly affects the sprite position
                pos: Vector = self.pos
                self.anchor = (175, 172)
                self.image = f"human_explode{frame}"
                self.pos = pos
            return

        # If not being carried, check to see if we're on the ground. If not, fall.
        if self.carrier is None:
            self.falling = not self.terrain_check()
            if not self.falling and self.y_velocity > 3:
                self.die()

            if self.falling:
                self.y_velocity += 0.05
                self.y_velocity = min(self.y_velocity, 4)
                self.y += self.y_velocity

        # Update radar blip pos
        self.blip.pos = game.radar.radar_pos(self.pos)

        # Set sprite image
        # Animations need to run forwards and backwards (at least stand)
        frame = self.anim_timer // 7
        num_frames: int = 4
        if self.carrier == game.player:
            sprite: str = "saved"
            num_frames = 1
        elif self.carrier is not None:
            sprite = "abducted"
        elif self.falling:
            sprite = "fall"
            num_frames = 2
        elif self.waving:
            sprite = "wave"
            num_frames = 3
            if self.anim_timer > 100:
                self.waving = False
        else:
            sprite = "stand"
            num_frames = 1
            # Sometimes start wave animation
            if randint(0, 200) == 0:
                self.waving = True
                self.anim_timer = 0

        self.image = f"human_{sprite}{forward_backward_animation_frame(frame, num_frames)}"

    def can_be_picked_up_by_player(self) -> bool:
        # Player can only pick up a human if they're falling
        return self.carrier is None and self.falling and not self.dead

    def can_be_picked_up_by_enemy(self) -> bool:
        # Enemies won't pick up a falling human
        return self.carrier is None and not self.falling and not self.dead

    def picked_up(self, carrier: Player | Enemy) -> None:
        self.carrier = carrier
        self.falling = False

    def dropped(self) -> None:
        self.carrier = None
        self.falling = not self.terrain_check()
        self.y_velocity = 0

    def terrain_check(self) -> bool:
        # To find out if we're on the ground, we need to work out where we're at on the terrain image
        # Convert world pos to pixel pos on terrain image
        pos_terrain: tuple[int, int] = (
            int(self.x % LEVEL_WIDTH),
            int(self.y - TERRAIN_OFFSET_Y),
        )
        mask: Mask = game.terrain_mask
        if (
            0 <= pos_terrain[0] < mask.width
            and 0 <= pos_terrain[1] < mask.height
        ):
            # Use the terrain mask to tell if there's an opaque pixel there
            return mask.get_at(pos_terrain)

        # If we're somehow off the bottom of the terrain, treat that as being on the terrain, otherwise we'd fall
        # off the bottom of the game world
        return pos_terrain[1] >= mask.height

    def die(self) -> None:
        # Start explode animation, finished_dying will be set to True when it's done
        self.exploding = True
        self.anim_timer = 0
        game.play_sound("prisoner_die")


@dataclass(eq=False, slots=True)
class Game:
    player: Player
    radar: Radar = field(default_factory=Radar, init=False)
    enemies: list[Enemy] = field(default_factory=list, init=False)
    humans: list[Human] = field(default_factory=list, init=False)
    lasers: list[Laser] = field(default_factory=list, init=False)
    bullets: list[Bullet] = field(default_factory=list, init=False)
    score: int = field(default=0, init=False)
    #: Wave 1 is first wave, we start it at zero here because new_wave() increments self.wave
    wave: int = field(default=0, init=False)
    #: Counts up during a wave; negative while the "wave complete" message shows
    wave_timer: int = field(default=0, init=False)
    timer: int = field(default=0, init=False)
    #: Defines the point on the screen at which the player appears - 0 would mean they would be on the
    #: left-hand edge of the screen
    player_camera_offset_x: float = field(init=False)
    #: The terrain image, and its opacity mask for "is this pixel ground?"
    terrain_surface: Image = field(init=False)
    terrain_mask: Mask = field(init=False)

    def __post_init__(self) -> None:
        self.player_camera_offset_x = WIDTH / 3

        self.terrain_surface = images.load("terrain")
        self.terrain_mask = Mask.from_image(self.terrain_surface)

        self.new_wave()

        music.play("ambience")

    def new_wave(self) -> None:
        # Add 6 lander enemies to the list for the first wave, and an additional one lander for each subsequent wave
        # From wave 4, add a pod enemy, and add an extra pod every two waves
        # Every 5th wave has baiters and mutants at the start instead of pods/landers
        # Every 10th wave has swarmers instead of mutants
        self.wave += 1
        num_landers: int = 4 + self.wave
        num_pods: int = -1 + self.wave // 2
        num_baiters: int = 0
        num_mutants: int = 0
        num_swarmers: int = 0
        if self.wave % 5 == 0:
            num_landers = 0
            num_pods = 0
            num_baiters = self.wave
            if self.wave % 10 == 0:
                num_swarmers = self.wave // 2
            else:
                num_mutants = self.wave // 2
        self.enemies += [
            Enemy(-i * 20, EnemyType.LANDER) for i in range(num_landers)
        ]
        self.enemies += [Enemy(-i * 50, EnemyType.POD) for i in range(num_pods)]
        self.enemies += [
            Enemy(-i * 100, EnemyType.BAITER) for i in range(num_baiters)
        ]
        self.enemies += [
            Enemy(-i * 10, EnemyType.MUTANT) for i in range(num_mutants)
        ]
        self.enemies += [
            Enemy(-i * 10, EnemyType.SWARMER) for i in range(num_swarmers)
        ]

        # Create humans
        self.humans = [
            Human((x, y + TERRAIN_OFFSET_Y)) for x, y in HUMAN_START_POS
        ]

        self.play_sound("new_wave")

    def update(self) -> None:
        # Wave timer starts at 0 at the beginning of the game, and counts up each frame
        # At the end of a wave it's set to a negative number, indicating to display the "wave complete" message
        # for that many frames before starting the next wave
        self.wave_timer += 1
        if self.wave_timer == 0:
            self.new_wave()

        self.timer += 1

        # Make a baiter enemy every 30 seconds, if the player is alive
        if (
            self.wave_timer > 0
            and self.wave_timer % (30 * 60) == 0
            and self.player.lives > 0
        ):
            self.enemies.append(Enemy(type=EnemyType.BAITER))

        self.player.update()

        # Update lasers and bullets, remove expired ones from the lists (update returns False when they want to expire)
        self.lasers = [laser for laser in self.lasers if not laser.update()]
        self.bullets = [b for b in self.bullets if not b.update()]

        wrappers: list[Enemy | Human] = [*self.enemies, *self.humans]
        for obj in wrappers:
            obj.update()

        # Remove dead humans
        self.humans = [h for h in self.humans if not h.dead]

        # Remove dead enemies who have finished their explode animations
        prev_num_enemies: int = len(self.enemies)
        self.enemies = [e for e in self.enemies if e.state != EnemyState.DEAD]

        # If there are fewer enemies this frame than there were last frame, gain score
        difference: int = prev_num_enemies - len(self.enemies)
        if difference > 0:
            self.score += 150 * difference

        # Start next level if there are no enemies and no falling humans, and the player is not carrying a human
        if (
            self.wave_timer > 0
            and not self.enemies
            and not any(human.falling for human in self.humans)
            and not self.player.is_carrying_human()
        ):
            self.wave_timer = -WAVE_COMPLETE_SCREEN_DURATION

            # Tell the player how many shields to restore and how many humans were saved, if they save
            # all ten they get an extra life token
            self.player.level_ended(
                self.get_shield_restore_amount(), self.get_humans_saved()
            )

            self.play_sound("wave_complete")

    def draw(self) -> None:
        # Shift the target camera position based on which way the player is facing: facing right, the camera is
        # positioned so that the ship is 1/3rd screen width from left; facing left, 2/3rds
        target_camera_offset_x: float = (
            WIDTH / 3 if self.player.facing_x > 0 else 2 * WIDTH / 3
        )

        # Also shift camera target pos based on player velocity - look further ahead if moving fast
        target_camera_offset_x -= self.player.velocity.x * 15

        # If target_camera_offset_x is different from the current camera offset, we want to transition to
        # the new offset over a series of frames, not just snap to the new offset. We'll transition faster
        # when the difference is bigger, but at a maximum of 8 pixels per frame
        camera_offset_delta: float = min(
            8,
            max(
                -8, (target_camera_offset_x - self.player_camera_offset_x) / 20
            ),
        )

        # Update player camera offset - math.floor ensures the result will always be a whole number
        self.player_camera_offset_x = math.floor(
            self.player_camera_offset_x + camera_offset_delta
        )

        # Calculate where to display background, terrain and objects, based on player position and player camera offset
        # If left of level was at the left hand edge of the screen, and then camera scrolled 100 pixels to the right,
        # that means we want to display everything shifted 100 pixels to the left. Think of scrolling not as the
        # camera moving, but everything in the game moving in the opposite direction
        # Top won't go lower than -100, to prevent seeing off the bottom of the terrain
        left: int = -(
            int(self.player.x - self.player_camera_offset_x) % LEVEL_WIDTH
        )
        top: int = max(-int(self.player.y / 4), -100)

        # Draw background five times - four because the level is four times wider than the background, and another
        # for when we're near the right-hand side of the level, just before the level wraps around
        # We divide the x/y values by 2 so that it moves slower than the foreground terrain - this is known
        # as parallax scrolling
        bg_width: int = images.load("background").width
        for i in range(5):
            blit("background", left // 2 + bg_width * i, top // 2)

        # Draw terrain twice, second one is for when we're near the right-hand side of the level, just before
        # the level wraps back around to the left
        renderer.draw_image(
            self.terrain_surface, (left, top + TERRAIN_OFFSET_Y)
        )
        renderer.draw_image(
            self.terrain_surface, (left + LEVEL_WIDTH, top + TERRAIN_OFFSET_Y)
        )

        offset_x: float = -(self.player.x - self.player_camera_offset_x)

        # Draw all objects
        # The order of drawing the player and the lasers that they fire varies depending on the tilt of the ship
        # The laser is fired from the underside of the ship, unless the ship is tilting up the turret is
        # obscured by the ship
        player_and_lasers: list[GameObject] = (
            [*self.lasers, self.player]
            if self.player.tilt_y == 1
            else [self.player, *self.lasers]
        )
        objects: list[GameObject] = [
            *self.bullets,
            *self.humans,
            *self.enemies,
            *player_and_lasers,
        ]
        for obj in objects:
            # Pass through the offset for scrolling
            obj.draw_at(offset_x, top)

        self.draw_ui()

    def draw_ui(self) -> None:
        # Draw user interface

        # Draw radar background
        self.radar.draw()

        # Draw radar blips. We first set a clipping zone, which ensures no graphics can be drawn outside
        # the boundaries of the radar. This ensures that the small circles of the radar blips don't extend
        # beyond the radar when they are right on its edge
        renderer.set_clip(
            (
                self.radar.x - self.radar.width / 2,
                self.radar.y,
                self.radar.width,
                self.radar.height,
            )
        )

        for enemy in self.enemies:
            if enemy.state == EnemyState.ALIVE:
                enemy.blip.draw()

        for human in self.humans:
            human.blip.draw()

        self.player.blip.draw()

        # Unset clipping zone, so we can again draw anywhere on the screen
        renderer.set_clip(None)

        # Show lives
        for i in range(self.player.lives):
            blit("life", 20 + 20 * i, 21)

        # Show shields
        for i in range(self.player.shields):
            blit("armor", 20 + 20 * i, 52)

        # Show extra life tokens
        for i in range(self.player.extra_life_tokens):
            blit(f"token{((self.timer // 6) + i) % 8}", 20 + 20 * i, 83)

        # Show score using the status font
        score_text: str = str(self.score)
        score_width: int = text_width(score_text, font="font_status")
        draw_text(score_text, WIDTH - score_width - 20, 28, font="font_status")

        # Show wave end text if wave is ending
        if self.wave_timer < 0:
            for i, line in enumerate(self.get_wave_end_text()):
                draw_text(line, WIDTH // 2, (HEIGHT // 2) - 140 + 65 * i, True)

    def get_wave_end_text(self) -> list[str]:
        # Return a list of strings where each string within the list is one line of the level end text.
        # As wave_timer increases we display more lines of text
        humans_saved: int = self.get_humans_saved()
        i: int = (self.wave_timer + WAVE_COMPLETE_SCREEN_DURATION) // (
            WAVE_COMPLETE_SCREEN_DURATION // 4
        )
        lines: list[str] = [f"WAVE {self.wave} COMPLETE"]
        if i >= 1:
            lines.append(
                f"{humans_saved} HUMAN{'' if humans_saved == 1 else 'S'} SAVED"
            )
        if i >= 2:
            num_shields_restored: int = self.get_shield_restore_amount()
            lines.append(
                f"{num_shields_restored} SHIELD{'' if num_shields_restored == 1 else 'S'} RESTORED"
            )
        if i >= 3 and humans_saved == 10:
            # If we saved 10 humans but have no extra life tokens, that must mean we just got 3 extra life tokens,
            # which gains an extra life and resets the tokens to zero, therefore display that we got an extra life
            lines.append(
                "EXTRA LIFE"
                if self.player.extra_life_tokens == 0
                else "LIFE TOKEN GAINED"
            )
        return lines

    def get_shield_restore_amount(self) -> int:
        # Player gets 1 shield restored for every 2 humans saved
        return min(self.get_humans_saved() // 2, 5)

    def get_humans_saved(self) -> int:
        return sum(not human.exploding for human in self.humans)

    def play_sound(self, name: str, count: int = 1, volume: float = 1) -> None:
        # Some sounds have multiple varieties. If count > 1, we'll randomly choose one from those
        # Don't bother playing the sound if the volume is 0 or less
        # Also don't create the sound if it's game over and the player has been dead for a while
        if volume <= 0 or (
            self.player.lives == 0
            and self.player.timers[Player.Timer.HURT] < -1000
        ):
            return
        try:
            # Sounds with several varieties are named "name0", "name1", ... The volume applies to this play only,
            # so a quiet distant shot doesn't quieten the same sound already playing nearby
            sounds.load(f"{name}{randint(0, count - 1)}").play(volume=volume)
        except Exception as e:
            # If no sound file of that name was found, print the error, which includes the filename.
            # Also occurs if sound fails to play for another reason (e.g. if this machine has no sound hardware)
            print(e)


def get_char_image_and_width(char: str, font: str) -> tuple[Image | None, int]:
    # Return the image and width of given character. ord() gives the ASCII/Unicode code for the given character.
    if char == " ":
        return None, 22
    image: Image = images.load(f"{font}0{ord(char)}")
    return image, image.width


def text_width(text: str, font: str = "font") -> int:
    return sum(get_char_image_and_width(c, font)[1] for c in text)


def draw_text(
    text: str, x: float, y: float, centre: bool = False, font: str = "font"
) -> None:
    if centre:
        x -= text_width(text) // 2

    for char in text:
        image, width = get_char_image_and_width(char, font)
        if image is not None:
            renderer.draw_image(image, (x, y))
        x += width


class State(Enum):
    TITLE = 1
    PLAY = 2
    GAME_OVER = 3


# Set up controls
def setup_joystick_controls() -> None:
    # We call this on startup, and keep calling it if there was no controller present on startup,
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


def update() -> None:
    global state, game, state_timer

    update_controls()

    state_timer += 1

    match state:
        case State.TITLE:
            # Check for start game
            for controls in (keyboard_controls, joystick_controls):
                # Check for button 0 being pressed on each controls object
                # joystick_controls will be None if there was no controller was connected on game startup,
                # so must check for that
                if controls is not None and controls.button_pressed(0):
                    # Switch to play state, and create a new Game object, passing it a new Player object to use
                    state = State.PLAY
                    state_timer = 0
                    game = Game(Player(controls))
                    break

        case State.PLAY:
            if game.player.lives <= 0:
                state = State.GAME_OVER
                state_timer = 0
            else:
                game.update()

        case State.GAME_OVER:
            # The game carries on updating in the background of the game over screen
            game.update()

            # Don't allow the player to press a button to go back to the main menu until one second has passed
            # This prevents the issue of accidentally skipping the game over screen because the player was just starting
            # to press the fire button as the game ended
            if state_timer > 60:
                # Check for button 0 being pressed
                for controls in (keyboard_controls, joystick_controls):
                    if controls is not None and controls.button_pressed(0):
                        # Switch to title screen state (the finished game lingers, untouched, until a new one
                        # replaces it - the title screen never looks at it)
                        state = State.TITLE
                        state_timer = 0
                        music.play("menu_theme")

        case _:
            raise ValueError(f"unhandled game state {state!r}")


def draw() -> None:
    match state:
        case State.TITLE:
            blit("title", 0, 0)
            blit(f"start{(state_timer // 4) % 14}", WIDTH // 2 - 350 // 2, 450)

        case State.PLAY:
            game.draw()

        case State.GAME_OVER:
            game.draw()
            draw_text("GAME OVER", WIDTH // 2, (HEIGHT // 2) - 100, True)

        case _:
            raise ValueError(f"unhandled game state {state!r}")


# Start the music (with no sound device the game simply plays silently)
music.play("menu_theme")

# Set up controls
keyboard_controls: KeyboardControls = KeyboardControls()
joystick_controls: JoystickControls | None
setup_joystick_controls()

# Set the initial game state
state: State = State.TITLE

# No game object to begin with: one is created when a game starts, and nothing
# touches it on the title screen (declared here, bound at the first start)
game: Game

# How long have we been in the current state?
state_timer: int = 0

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

# Fixed 60 Hz timestep -- avenger's update() takes no dt. PGZERO_MAX_FRAMES=N
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
