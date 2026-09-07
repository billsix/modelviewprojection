# Code the Classics port: eggzy, with its rendering engine inlined.
#
# Game code derived from Raspberry Pi Press's "Code the Classics" (vol 2):
#   Copyright (c) 2024 Eben Upton <eben@raspberrypi.com>
# Inlined engine (audio, images, renderer, keyboard, loop):
#   Copyright (c) 2026 William Emerison Six
# SPDX-License-Identifier: BSD-2-Clause
# Full license text: ports/codetheclassics/LICENSE.
"""eggzy -- a beat-the-clock platformer of gems, dashes and wall jumps, from
Code the Classics vol. 2, on GLFW + OpenGL 3.3 core.

One self-contained file, read top to bottom like the course's demos: first
the small engine this game needs (a software audio mixer, an image loader, a
textured-quad renderer that can also draw one tile of a tileset, flat fills
and debug outlines, the anchored Actor sprite with rect collision, keyboard
and gamepad state), then the game -- levels come from Tiled ``.tmx`` maps --
then the loop the game itself owns.
"""

from __future__ import annotations

import os
import signal
import sys
import threading
import time
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from collections.abc import Callable, Generator, Iterator
from dataclasses import InitVar, dataclass, field
from enum import Enum
from random import randint
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
    identity,
    scale_non_uniform,
    to_matrix,
    translate,
)
from numpy.typing import NDArray
from PIL import Image as PILImage

# ===== engine: shared state =====

WIDTH: int = 825
HEIGHT: int = 550
TITLE: str = "Eggzy"

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


#: The 4x4 identity model matrix, built once at import through gacalc --
#: the same machinery as ``ortho_pixels`` / ``MODEL``.
_IDENTITY: NDArray[np.float32] = np.asarray(
    to_matrix(identity(), g3.Vector), dtype=np.float32
)


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
        GL.glUniformMatrix4fv(self.uniforms.model, 1, GL.GL_TRUE, _IDENTITY)
        GL.glUniform1i(self.uniforms.use_tex, 0)
        r, g, b = color
        GL.glUniform4f(self.uniforms.tint, r / 255.0, g / 255.0, b / 255.0, 1.0)
        GL.glDrawArrays(GL.GL_LINE_LOOP, 0, 5)

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

    @property
    def centerx(self) -> float:
        return self._rect.centerx

    @property
    def centery(self) -> float:
        return self._rect.centery

    def colliderect(self, other: RectLike) -> bool:
        """Return whether this sprite's rect overlaps ``other`` (a rect or a sprite)."""
        return self._rect.colliderect(other)

    def distance_to(self, target: Actor) -> float:
        """Return the distance from this sprite's position to ``target``'s."""
        return float((target.pos - self.pos).magnitude())


# ===== engine: keyboard =====
#
# ``keyboard.<name>`` is True while that key is held. The GLFW key callback
# below feeds presses and releases in; the game polls the names in the table
# each frame -- they are the only keys eggzy reads.

_NAME_TO_KEY: dict[str, int] = {
    "left": glfw.KEY_LEFT,
    "right": glfw.KEY_RIGHT,
    "up": glfw.KEY_UP,
    "down": glfw.KEY_DOWN,
    "space": glfw.KEY_SPACE,
    "z": glfw.KEY_Z,
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

LEVEL_SEQUENCE: tuple[str, ...] = (
    "starter1.tmx",
    "starter2.tmx",
    "starter3.tmx",
    "starter4.tmx",
    "forest1.tmx",
    "forest2.tmx",
    "forest3.tmx",
    "forest4.tmx",
    "forest9.tmx",
    "castle1.tmx",
    "castle2.tmx",
    "castle3.tmx",
    "castle4.tmx",
    "castle5.tmx",
    "castle6.tmx",
    "castle7.tmx",
    "castle8.tmx",
    "forest5.tmx",
    "forest6.tmx",
    "forest7.tmx",
    "forest8.tmx",
)

GRID_BLOCK_SIZE: int = 25
LEVEL_Y_BOUNDARY: int = -100

# Change to 1, 2 or 3 to start with enemies/more enemies and less bonus time for gems
INITIAL_LEVEL_CYCLE: int = 0

INITIAL_TIME_REMAINING: int = 15
INITIAL_PICKUP_TIME_BONUS: int = 2
STOMP_ENEMY_TIME_BONUS: int = 3

# Constants affecting player movement
COYOTE_TIME: int = 6
JUMP_VEL_Y: int = -10
WALL_JUMP_X_VEL: int = 8
WALL_JUMP_COYOTE_TIME: int = 15
CACHE_JUMP_INPUT_TIME: int = 5
PLAYER_WIDTH: int = 20  # Width of player for the purpose of collisions - slightly smaller than the bounds of the sprite
PLAYER_HEIGHT: int = 40  # For player head collision with ceilings

ANCHOR_CENTRE: Anchor = ("center", "center")
ANCHOR_CENTRE_BOTTOM: Anchor = ("center", "bottom")
ANCHOR_PLAYER: Anchor = (
    "center",
    60,
)  # Feet of player sprite are not at the bottom
ANCHOR_FLAME: Anchor = ("center", 78)
ANCHOR_FLAME_DASH: Anchor = ("center", 130)


class Biome(Enum):
    FOREST = 0
    CASTLE = 1


# There are eight types of enemy - four per biome. Some properties are the same between the forest/castle equivalents,
# some are different

ENEMY_SPRITE_NAMES: dict[Biome, list[str]] = {
    Biome.CASTLE: ["robot0", "robot1", "robot2", "robot3"],
    Biome.FOREST: ["fly", "mghost", "triffid", "bigbloom"],
}

ENEMY_TYPES_FLYING: dict[Biome, list[bool]] = {
    Biome.CASTLE: [True, True, False, False],
    Biome.FOREST: [True, True, False, True],
}

ENEMY_TYPES_WIDTH_OVERRIDES: dict[Biome, list[int]] = {
    Biome.CASTLE: [30, 50, 48, 50],
    Biome.FOREST: [30, 50, 50, 50],
}
ENEMY_TYPES_HEIGHT_OVERRIDES: dict[Biome, list[int]] = {
    Biome.CASTLE: [40, 40, 60, 120],
    Biome.FOREST: [30, 65, 70, 90],
}

ENEMY_TYPES_ANCHOR_POINTS: dict[Biome, list[Anchor]] = {
    Biome.CASTLE: [
        ("center", 40),
        ("center", 40),
        ("center", 95),
        ("center", "bottom"),
    ],
    Biome.FOREST: [
        ("center", 60),
        ("center", "bottom"),
        ("center", "bottom"),
        ("center", "bottom"),
    ],
}

ENEMY_TYPES_HEALTH: list[int] = [1, 3, 1, 3]
ENEMY_TYPES_SPEED: list[int] = [2, 1, 2, 1]

REPLAY_FILENAME: str = "eggzy-replays"
MAX_REPLAYS: int = 10

DEBUG_SHOW_PLAYER_COLLISION_RECT: bool = False
DEBUG_SHOW_ENEMY_COLLISION_RECTS: bool = False
DEBUG_SHOW_BLOCK_COLLISION_RECTS: bool = False
DEBUG_SHOW_FRAME_NUMBER: bool = False
DEBUG_MOVEMENT: bool = False
DEBUG_SLOWMO: int = (
    1  # Set to 2 or higher to run in slow motion, useful for testing animations
)

# These symbols substitute for the controller button images when displaying text.
# The symbols representing these images must be ones that aren't actually used themselves, e.g. we don't use the
# percent sign in text
SPECIAL_FONT_SYMBOLS: dict[str, str] = {"xb_a": "%", "xb_b": "#"}

# Create a version of SPECIAL_FONT_SYMBOLS where the keys and values are swapped
SPECIAL_FONT_SYMBOLS_INVERSE: dict[str, str] = {
    v: k for k, v in SPECIAL_FONT_SYMBOLS.items()
}

#: One recorded game: per frame, the player's position, level number and sprite
#: (replayed on later games as a ghost)
type Replay = list[tuple[PointLike, int, str]]


def move_towards(n: int, target: int, speed: int) -> int:
    return min(n + speed, target) if n < target else max(n - speed, target)


def sign(x: float) -> int:
    # Returns 1, 0 or -1 depending on whether number is positive, zero or negative
    return 0 if x == 0 else -1 if x < 0 else 1


class GameObject(Protocol):
    """What Game.update and Game.draw need of the things in a level: a
    per-frame update and a draw. Every Actor subclass below satisfies it
    structurally (deliberately not by subclassing the protocol -- an explicit
    subclass inherits the stub members, so a missing method would go
    unreported).
    """

    def update(self) -> None: ...

    def draw(self) -> None: ...


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
    def get_x(self) -> int: ...

    @abstractmethod
    def get_y(self) -> int: ...

    @abstractmethod
    def button_down(self, button: int) -> bool: ...

    def button_pressed(self, button: int) -> bool:
        return self.is_button_pressed[button]

    @abstractmethod
    def button_name(self, button: str) -> str:
        """The label the tutorial text shows for the "dash" or "jump" button."""
        ...


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
        return keyboard.space if button == 0 else keyboard.z

    @override
    def button_name(self, button: str) -> str:
        match button:
            case "dash":
                return "Z"
            case "jump":
                return "SPACE"
            case _:
                return "?"


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
            print("Warning: controller does not have enough buttons!")
            return False
        return self.joystick.get_button(button) != 0

    @override
    def button_name(self, button: str) -> str:
        match button:
            case "dash":
                return SPECIAL_FONT_SYMBOLS["xb_b"]
            case "jump":
                return SPECIAL_FONT_SYMBOLS["xb_a"]
            case _:
                return "?"


# Class for gem pickups
# (eq=False on these Actor dataclasses keeps identity comparison/hashing --
# the generated __eq__ would compare fields and set __hash__ to None; slots=True
# fixes each object's attribute set to its declared fields, so every attribute
# an object ever gets is declared below)
@dataclass(eq=False, slots=True)
class Gem(Actor):
    #: This is a class variable, equivalent to what is known in other languages as a static variable
    #: The variable belongs to the class as a whole rather than any one particular instance (object) of the class
    #: (ClassVar keeps it out of the dataclass's instance fields/__init__)
    next_type: ClassVar[int] = 1

    #: named spawn_pos, NOT pos: pos is an Actor property, and a dataclass
    #: would treat the property object as this field's default value
    spawn_pos: InitVar[PointLike]
    collected: bool = False
    #: Which of the four gem sprites we are, dealt round-robin from next_type
    type: int = field(init=False)

    def __post_init__(self, spawn_pos: PointLike) -> None:
        super().__init__("blank", spawn_pos, ANCHOR_CENTRE_BOTTOM)

        # Choose which type of gem we're going to be, and set the type of the next gem (1 to 4, cycling)
        self.type = Gem.next_type
        Gem.next_type = Gem.next_type % 4 + 1

    def update(self) -> None:
        # Does the player exist, and are they colliding with us?
        if game.player is not None and game.player.collidepoint(self.center):
            game.gain_time(game.time_pickup_bonus, self.centerx, self.centery)
            game.play_sound("collect")
            self.collected = True  # Disappear

        self.image = f"gem{self.type}_{(game.timer // 6) % 4}"

    @staticmethod
    def new_game() -> None:
        Gem.next_type = 1


# The door prevents the player from leaving a level until all gems have been collected
@dataclass(eq=False, slots=True)
class Door(Actor):
    spawn_pos: InitVar[PointLike]
    biome: str = "castle"
    #: The door's look within its biome, as named in the level file
    variant: str | int = 0
    already_open: InitVar[bool] = False
    opening: bool = field(init=False)
    last_frame: int = field(init=False)
    frame: int = field(init=False)

    def __post_init__(self, spawn_pos: PointLike, already_open: bool) -> None:
        self.opening = already_open
        self.last_frame = 15 if self.biome == "castle" else 13
        self.frame = self.last_frame if already_open else 0
        super().__init__(
            f"door_{self.biome}_{self.variant}_{self.frame}",
            spawn_pos,
            anchor=(0, 0),
        )

    def update(self) -> None:
        if (
            self.opening
            and self.frame < self.last_frame
            and game.timer % 3 == 0
        ):
            self.frame += 1
            self.image = f"door_{self.biome}_{self.variant}_{self.frame}"

    def open(self) -> None:
        self.opening = True

    def is_fully_open(self) -> bool:
        return self.frame == self.last_frame


# Used for animations such as those that appear when you pick up a gem or lose a life
class Animation(Actor):
    __slots__ = (
        "image_format_str",
        "num_frames",
        "frame_interval",
        "timer",
        "rise_time",
    )

    def __init__(
        self,
        pos: PointLike,
        image_format_str: str,
        num_frames: int,
        frame_interval: int,
        anchor: Anchor = ANCHOR_CENTRE,
        initial_delay: int = 0,
        rise_time: int = -1,
    ) -> None:
        super().__init__("blank", pos, anchor)
        self.image_format_str: str = image_format_str
        self.num_frames: int = num_frames
        self.frame_interval: int = frame_interval
        self.timer: int = -initial_delay
        self.rise_time: int = rise_time
        self.update_image()

    def update(self) -> None:
        self.timer += 1
        self.update_image()

        # Some animations start rising up after a certain time
        if self.rise_time > -1 and self.timer > self.rise_time:
            self.y -= 1

    def update_image(self) -> None:
        self.image = (
            "blank"
            if self.timer < 0
            else self.image_format_str.format(
                min(self.timer // self.frame_interval, self.num_frames - 1)
            )
        )

    def finished(self) -> bool:
        return self.timer // self.frame_interval >= self.num_frames


class DashTrail(Animation):
    __slots__ = ()

    def __init__(self, pos: PointLike, image: str) -> None:
        # Receives the player's current sprite, uses the trail version of that sprite
        super().__init__(pos, f"{image}_trail_{{0}}", 6, 5, ANCHOR_PLAYER)


# Base class for objects which move around the level and collide with walls, such as the player and enemies
class CollideActor(Actor):
    __slots__ = ()

    def __init__(self, pos: PointLike, anchor: Anchor = ANCHOR_CENTRE) -> None:
        super().__init__("blank", pos, anchor)

    def move(self, dx: int, dy: int, speed: int) -> bool:
        # Returns true if move was blocked
        # One of dx or dy will be 0

        new_x, new_y = self.x, self.y

        # Movement is done 1 pixel at a time, which ensures we don't get embedded into a wall we're moving towards
        for _i in range(speed):
            new_x, new_y = new_x + dx, new_y + dy

            # Get the player rectangle as it would be if the position were changed to new_x, new_y
            rect: IntRect = self.get_rect(new_x, new_y)

            # Does this proposed new position overlap with any of the collidable tiles, or the exit door?
            if game.position_blocked(rect):
                return True

            # We only update the object's position if there wasn't a block there.
            self.pos = new_x, new_y

        # Didn't collide with anything
        return False

    def get_rect(
        self, centre_x: float | None = None, bottom_y: float | None = None
    ) -> IntRect:
        # Returns a rectangle representing this actor, assuming it were positioned at the specified x and y coordinates
        # (If None, we default to the actual X/Y pos of the actor)
        # We don't use the sprite bounds as the rectangle, as for the player and enemies we want the collidable size
        # to be a bit smaller than the sprite. Whole pixels, truncated like pygame's Rect.
        if centre_x is None:
            centre_x = self.x
        if bottom_y is None:
            bottom_y = self.y
        w, h = self.get_collidable_width(), self.get_collidable_height()
        return IntRect(int(centre_x - (w // 2)), int(bottom_y - h), w, h)

    def get_collidable_width(self) -> int:
        # Overridden for Player and Enemy
        return images.load(self.image).width

    def get_collidable_height(self) -> int:
        # Overridden for Player and Enemy
        return images.load(self.image).height


# An actor who is subject to gravity, this includes the player and non-flying enemies
# The flying enemies do actually use this too, but disable it by setting gravity_enabled to false,
# demonstrating a drawback of inheritance in object-oriented programming! In a component-based
# system such as Unity, objects which want gravity could instead have a gravity component.
class GravityActor(CollideActor):
    MAX_FALL_SPEED: ClassVar[int] = 7

    class FallState(Enum):
        LANDED = 0
        FALLING = 1
        JUMPING = 2
        WALL_JUMPING = 3

    __slots__ = (
        "gravity_enabled",
        "vel_y",
        "fall_state",
        "lower_gravity_timer",
    )

    def __init__(
        self,
        pos: PointLike,
        gravity_enabled: bool = True,
        anchor: Anchor = ANCHOR_CENTRE_BOTTOM,
    ) -> None:
        super().__init__(pos, anchor)

        self.gravity_enabled: bool = gravity_enabled
        self.vel_y: int = 0
        self.fall_state: GravityActor.FallState = GravityActor.FallState.FALLING
        self.lower_gravity_timer: int = 0

    def fall(self, detect: bool) -> None:
        # The per-frame gravity step; each subclass's update() calls it first
        if not self.gravity_enabled:
            return

        self.lower_gravity_timer -= 1

        # Apply change to Y velocity
        if game.timer % (3 if self.lower_gravity_timer > 0 else 2) == 0:
            self.vel_y = min(self.vel_y + 1, GravityActor.MAX_FALL_SPEED)

        # Apply gravity, without going over the maximum fall speed
        # The detect parameter indicates whether we should check for collisions with blocks as we fall. Normally we
        # want this to be the case. If the player is in the process of losing a life, however, we want them to just
        # fall out of the level, so False is passed in this case.
        if detect and self.vel_y != 0:
            # Move vertically in the appropriate direction, at the appropriate speed
            # Set landed to false, if we're on the floor it'll be set to true again below, otherwise it will remain
            # false
            if DEBUG_MOVEMENT:
                print(f"{game.timer} detect: landed false, {self.vel_y}")
            if self.fall_state == GravityActor.FallState.LANDED:
                self.fall_state = GravityActor.FallState.FALLING
            if self.move(0, sign(self.vel_y), abs(self.vel_y)):
                if DEBUG_MOVEMENT:
                    print("move returned true")
                # If move returned True, we must have either landed or hit our head on the ceiling
                if self.vel_y > 0:
                    self.vel_y = 0
                    self.fall_state = GravityActor.FallState.LANDED
                    if DEBUG_MOVEMENT:
                        print("detect: landed true")

        else:
            # Collision detection disabled - just update the Y coordinate without any further checks
            self.y += self.vel_y

    def landed(self) -> bool:
        return self.fall_state == GravityActor.FallState.LANDED


@dataclass(eq=False, slots=True)
class Player(GravityActor):
    DASH_TIME: ClassVar[int] = 18
    DASH_SPEED: ClassVar[int] = 10
    DASH_PAUSE_TIME: ClassVar[int] = 5
    DASH_TRAIL_INTERVAL: ClassVar[int] = 3
    DASH_TIMER_TRAIL_CUTOFF: ClassVar[int] = -10
    MAX_X_RUN_SPEED: ClassVar[int] = 5

    controls: Controls
    vel_x: int = 0
    #: -1 = left, 1 = right
    facing_x: int = 1
    hurt: bool = False
    #: Counts down
    dash_timer: int = DASH_TIMER_TRAIL_CUTOFF
    #: Counts up
    dash_animation_timer: int = 0
    dash_allowed: bool = False
    #: -1/1 while sliding down the wall on that side, 0 otherwise
    grabbed_wall: int = 0
    coyote_time: int = 0
    #: Number of frames since we started falling or jumping
    fall_timer: int = 0
    wall_jump_coyote_time: int = 0
    cached_jump_input_timer: int = 0
    enemy_stomped_timer: int = 0
    change_direction_timer: int = 0
    #: Used for dash trails
    last_dash_sprite: str = "dash_horizontal_0_0"
    replay_data: Replay = field(default_factory=list)
    #: Whether we stomped an enemy last frame (a stomp bounces us up into it again)
    stomped_last_frame: bool = False
    #: The wall we last let go of, for the coyote-time wall jump
    previous_grabbed_wall: int = 0
    #: Where this level starts us, set by Game.next_level
    start_pos: PointLike = field(init=False)
    #: Actor for the flame on the character's head (positioned from our own pos,
    #: so created after super().__init__ has set it)
    flame: Actor = field(init=False)

    def __post_init__(self) -> None:
        # Call constructor of parent class. Initial pos is 0,0 but Game.next_level will set the actual starting position
        super().__init__((0, 0), anchor=ANCHOR_PLAYER)

        self.flame = Actor("flame_stand_0", self.pos, anchor=ANCHOR_FLAME)

    def new_level(self, start_pos: PointLike) -> None:
        self.start_pos = start_pos
        self.reset()

    def reset(self) -> None:
        self.pos = self.start_pos
        self.vel_x = 0
        self.vel_y = 0
        self.facing_x = 1
        self.hurt = False
        self.dash_timer = Player.DASH_TIMER_TRAIL_CUTOFF
        self.gravity_enabled = True
        self.grabbed_wall = 0
        self.coyote_time = 0
        self.wall_jump_coyote_time = 0
        self.cached_jump_input_timer = 0
        self.enemy_stomped_timer = 0

        # Ensure that when we spawn or respawn, there are no enemies at or near that position - treat it
        # as if we'd stomped on their heads
        # Need to check that a game exists, because the player is constructed during Game construction, and the
        # game global isn't bound until construction is complete (on a later game it is still the previous one)
        if "game" in globals():
            for enemy in game.enemies:
                if (
                    self.distance_to(enemy) < 150
                ):  # 150 pixel radius, to be safe
                    enemy.destroy()
                    game.play_sound("enemy_death", 5)

    def hit_test(self, other: Enemy) -> bool:
        # Check for collision between player and enemy - called from Player.update
        return (
            self.get_rect(self.x, self.y).colliderect(other.get_rect())
            and not self.hurt
        )

    def get_colliding_enemies(self) -> list[Enemy]:
        return [
            enemy
            for enemy in game.enemies
            if not enemy.dying and self.hit_test(enemy)
        ]

    def update(self) -> None:
        # Apply gravity first - collision detection as we fall, unless we're hurt and dropping out of the level
        was_landed: bool = self.landed()
        self.fall(detect=not self.hurt)

        if was_landed and not self.landed():
            # We must have walked off a platform. Set coyote time timer
            self.coyote_time = COYOTE_TIME
            self.fall_timer = 0

        if self.top >= HEIGHT:
            self.reset()

        # Check for collisions with enemies, including landing on their heads
        stomped_any: bool = False
        for enemy in self.get_colliding_enemies():
            # Die or stomp? Are we within the top 20% of the enemy collision rectangle?
            # If we're moving downward, increase the threshold to the top 50% of the collision rectangle
            # We're fairly forgiving about this - otherwise some of the deaths seem unfair
            enemy_rect: IntRect = enemy.get_rect()
            threshold: float = enemy_rect.top + (
                enemy_rect.bottom - enemy_rect.top
            ) * (0.5 if self.vel_y > 0 else 0.2)
            # If the player stomps an enemy due to downward motion they'll now be moving up, so unless they're within
            # the top 20% of the sprite, they'll get hit by it on the next frame. Prevent this using stomped_last_frame
            if self.y < threshold or self.stomped_last_frame:
                enemy.stomped()
                stomped_any = True
                self.vel_y = -6
                self.enemy_stomped_timer = 3
                self.dash_allowed = True
                if DEBUG_MOVEMENT:
                    print(game.timer, "stomp", self.y, threshold)
            else:
                # Die and respawn
                self.hurt = True
                self.vel_y = -12
                self.fall_state = GravityActor.FallState.FALLING
                self.fall_timer = 0
                self.dash_timer = Player.DASH_TIMER_TRAIL_CUTOFF
                game.play_sound("player_death")
                game.animations.append(
                    Animation(self.pos, "loselife_{0}", 8, 4)
                )
                if DEBUG_MOVEMENT:
                    print(game.timer, "DIE", self.y, threshold)
                break

        self.stomped_last_frame = stomped_any

        if self.landed():
            self.dash_allowed = True

        self.dash_timer -= 1
        self.dash_animation_timer += 1
        self.cached_jump_input_timer -= 1
        self.coyote_time -= 1
        self.wall_jump_coyote_time -= 1

        if (
            self.dash_timer > Player.DASH_TIMER_TRAIL_CUTOFF
            and self.dash_timer % Player.DASH_TRAIL_INTERVAL == 0
        ):
            game.animations.append(DashTrail(self.pos, self.last_dash_sprite))

        dx: int = 0  # X direction we tried to move this frame, zero if we are standing still

        jump_pressed: bool = self.controls.button_pressed(0)

        if jump_pressed and DEBUG_MOVEMENT:
            print(game.timer, "jump pressed")

        if self.hurt:
            # We've just been hurt. We're dropping out of the level, so check for our sprite reaching a certain Y
            # coordinate before setting hurt to False. Code further down will make the player respawn.
            self.gravity_enabled = True
            if self.top >= HEIGHT:
                self.hurt = False

        elif self.dash_timer > 0:
            # Update dash
            # For first few frames of dash, equating to dash_timer being above DASH_TIME, player doesn't move
            if self.dash_timer < Player.DASH_TIME:
                if self.dash_timer % Player.DASH_TRAIL_INTERVAL == 0:
                    game.animations.append(
                        DashTrail(self.pos, self.last_dash_sprite)
                    )

                # A dash may be vertical, horizontal or diagonal
                # The horizontal and vertical components of the velocity are applied separately, to improve how
                # collision detection works

                # Apply vertical component of dash
                self.move(0, sign(self.vel_y), abs(self.vel_y))

                # Apply horizontal component of dash
                if (
                    self.move(sign(self.vel_x), 0, abs(self.vel_x))
                    and self.vel_y >= 0
                ):
                    # If we hit a wall, and are not travelling up, end the dash
                    self.dash_timer = 0
                    self.grabbed_wall = self.facing_x

        else:
            # We're not hurt or dashing
            # We're either on a wall, jumping/falling or walking

            # Get keyboard input. dx represents the direction the player is facing
            dx = self.controls.get_x()

            def jump() -> None:
                if DEBUG_MOVEMENT:
                    print(game.timer, "JUMP")
                self.vel_y = JUMP_VEL_Y
                self.fall_state = GravityActor.FallState.JUMPING
                self.coyote_time = 0
                self.cached_jump_input_timer = 0
                self.lower_gravity_timer = 5
                self.fall_timer = 0
                game.play_sound("jump")

            def wall_jump(wall_direction: int) -> None:
                if DEBUG_MOVEMENT:
                    print(game.timer, "WALL JUMP", wall_direction)
                self.vel_y = JUMP_VEL_Y
                self.fall_state = GravityActor.FallState.WALL_JUMPING
                self.vel_x = -wall_direction * WALL_JUMP_X_VEL
                self.facing_x = -wall_direction
                self.grabbed_wall = 0
                self.previous_grabbed_wall = 0
                self.wall_jump_coyote_time = 0
                self.cached_jump_input_timer = 0
                self.fall_timer = 0
                game.play_sound("jump")

            # Non-zero means we're grabbing a wall
            if self.grabbed_wall != 0:
                # Wall slide
                self.gravity_enabled = False

                # Check for wall jump
                if jump_pressed or self.cached_jump_input_timer > 0:
                    if DEBUG_MOVEMENT:
                        print(game.timer, "wall jump", self.vel_x)
                    wall_jump(self.grabbed_wall)

                # Check if player is pushing away from the wall
                elif dx == -self.grabbed_wall:
                    if DEBUG_MOVEMENT:
                        print(game.timer, "ungrab wall", self.grabbed_wall)
                    self.previous_grabbed_wall = self.grabbed_wall
                    self.wall_jump_coyote_time = WALL_JUMP_COYOTE_TIME
                    self.grabbed_wall = 0

                else:
                    # Slowly slide down wall, stop grabbing if we hit the floor or the wall is no longer there (because
                    # we slid off the bottom of it)
                    if DEBUG_MOVEMENT:
                        print(game.timer, "slide", self.grabbed_wall)

                    rect: IntRect = self.get_rect(
                        self.x + self.grabbed_wall, self.y
                    )

                    if self.move(0, 1, 1) or not game.position_blocked(rect):
                        self.grabbed_wall = 0
                        if DEBUG_MOVEMENT:
                            print(game.timer, "slide landed or wall gone")

            else:
                # Not grabbing a wall
                # Check for coyote time wall jump, i.e. a wall jump just after we let go of the wall

                # debug
                if DEBUG_MOVEMENT and self.wall_jump_coyote_time > 0:
                    print(
                        game.timer,
                        "remaining wall_jump_coyote_time",
                        self.wall_jump_coyote_time,
                    )

                if jump_pressed and self.wall_jump_coyote_time > 0:
                    if DEBUG_MOVEMENT:
                        print(game.timer, "coyote wall jump")
                    wall_jump(self.previous_grabbed_wall)

                else:
                    # Normal movement
                    self.gravity_enabled = True
                    if dx == 0:
                        # No horizontal input - come to a halt over several frames
                        self.vel_x = move_towards(self.vel_x, 0, 1)
                    else:
                        # Horizontal input - apply to x velocity
                        self.facing_x = dx
                        self.vel_x = move_towards(
                            self.vel_x, Player.MAX_X_RUN_SPEED * dx, 1
                        )

                    # Apply x velocity
                    # Start grabbing wall if we hit a wall and our y velocity is downwards
                    # Note: order of checks matters, self.move may cause us to move so must come before vel_y check
                    if (
                        self.vel_x != 0
                        and self.move(sign(self.vel_x), 0, abs(self.vel_x))
                        and self.vel_y > 0
                    ):
                        if DEBUG_MOVEMENT:
                            print(game.timer, "grab")
                        self.grabbed_wall = sign(self.vel_x)

                        # Cancel horizontal velocity on hitting wall
                        self.vel_x = 0

                    if (jump_pressed or self.cached_jump_input_timer > 0) and (
                        self.landed() or self.coyote_time > 0
                    ):
                        # Jump
                        if DEBUG_MOVEMENT:
                            if not jump_pressed:
                                print(game.timer, "cached jump")
                            if not self.landed():
                                print(
                                    game.timer,
                                    f"coyote time jump {self.coyote_time}",
                                )
                        jump()

                    elif jump_pressed and not self.landed():
                        # Cache jump input for a few frames, so that if the player lands just after pressing jump,
                        # a jump will be initiated
                        self.cached_jump_input_timer = CACHE_JUMP_INPUT_TIME

                    elif (
                        not self.landed()
                        and self.vel_y < 0
                        and not self.controls.button_down(0)
                        and self.dash_timer < -10
                        and self.enemy_stomped_timer <= 0
                    ):
                        # In the air and moving up, haven't finished dashing in last few frames
                        # Upward velocity drops off faster if player has let go of the jump button (unless they just
                        # stomped an enemy)
                        self.vel_y = min(self.vel_y + 1, 0)

                    if self.dash_allowed and self.controls.button_pressed(1):
                        # Dash
                        dy: int = self.controls.get_y()
                        if dx != 0 or dy != 0:
                            if DEBUG_MOVEMENT:
                                print(game.timer, "dash")
                            v: Vector = (
                                Vector(dx, dy).normalize() * Player.DASH_SPEED
                            )
                            self.vel_x = int(v.x)
                            self.vel_y = int(v.y)
                            self.gravity_enabled = False
                            self.dash_allowed = False
                            self.dash_timer = (
                                Player.DASH_TIME + Player.DASH_PAUSE_TIME
                            )
                            self.dash_animation_timer = 0
                            self.fall_state = GravityActor.FallState.FALLING
                            self.wall_jump_coyote_time = 0
                            game.play_sound("jump_long", 5)

        # When we change direction, our X velocity will be different from our facing direction (dx)
        # We set a change direction timer which then counts down, while it's above zero we play the change
        # direction animation
        if sign(dx) != sign(self.vel_x) and self.dash_timer <= 0:
            self.change_direction_timer = 5
        else:
            self.change_direction_timer -= 1

        # Update sprite
        self.determine_sprite(dx)

        # Update fall timer after choosing sprite so that we don't just skip frame 0
        # Don't increase fall timer if we're dashing
        if not self.landed() and self.dash_timer <= 0:
            self.fall_timer += 1

        # Update replay data
        self.replay_data.append((self.pos, game.level_index, self.image))

    def determine_sprite(self, dx: int) -> None:
        # Set sprite image. If we're currently hurt, the sprite will flash on and off on alternate frames.
        # dx is X direction we tried to move this frame, zero if there was no control input
        self.image = self.flame.image = "blank"
        # Flame has different anchor point depending on whether we're dashing
        self.flame.anchor = ANCHOR_FLAME
        if not self.hurt or game.timer % 2 == 1:
            # Example sprite name: "run_0_3" - first number is direction (0 right, 1 left), second is the frame number
            dir_index: str = "1" if self.facing_x < 0 else "0"
            if self.hurt:
                # no flame for this animation (it was blanked above)
                self.image = f"die_{min(self.fall_timer // 8, 5)}"

            elif self.grabbed_wall != 0 and self.vel_y >= 0:
                # We don't do wall slide animation if we're moving upward
                self.image = f"climb_{dir_index}_1"
                self.flame.image = f"flame_climb_{dir_index}_1"

            elif not self.landed():
                # In air
                if self.fall_state == GravityActor.FallState.JUMPING:
                    frame: int = min(self.fall_timer // 3, 5)
                    flame_frame: int = min(self.fall_timer // 3, 5) + 1
                    self.image = f"jump_{dir_index}_{frame}"
                    self.flame.image = f"flame_jump_{dir_index}_{flame_frame}"
                elif self.fall_state == GravityActor.FallState.WALL_JUMPING:
                    frame = min(self.fall_timer // 8, 2)
                    flame_frame = min(self.fall_timer // 4, 6)
                    self.image = f"wall_jump_{dir_index}_{frame}"
                    self.flame.image = (
                        f"flame_wall_jump_{dir_index}_{flame_frame}"
                    )
                elif self.dash_timer > 0:
                    # Choose a dash sprite and update self.last_dash_image
                    # Initially all dash directions use dash_start_0/1 (depending on facing direction), before
                    # switching to specific frames for different dash directions
                    if self.dash_animation_timer < 4:
                        flame_frame = self.dash_animation_timer // 2
                        self.image = self.last_dash_sprite = (
                            "dash_start_" + dir_index
                        )
                        self.flame.image = (
                            f"flame_dash_start_{dir_index}_{flame_frame}"
                        )
                        self.flame.anchor = ANCHOR_FLAME
                    else:
                        timer: int = self.dash_animation_timer - 4
                        frame = min(timer // 3, 2)
                        flame_frame = min(timer // 3, 7)
                        vertical: str = (
                            "up_"
                            if self.vel_y < 0
                            else "down_"
                            if self.vel_y > 0
                            else ""
                        )
                        horizontal: str = (
                            "horizontal_" if self.vel_x != 0 else ""
                        )
                        sprite: str = f"dash_{vertical}{horizontal}"
                        self.image = self.last_dash_sprite = (
                            f"{sprite}{dir_index}_{frame}"
                        )
                        self.flame.image = (
                            f"flame_{sprite}{dir_index}_{flame_frame}"
                        )
                        self.flame.anchor = ANCHOR_FLAME_DASH
                else:
                    # For flame, use frames 4 and 5 of wall jump
                    frame = min(self.fall_timer // 8, 1)
                    flame_frame = min(self.fall_timer // 8, 1) + 4
                    self.image = f"fall_{dir_index}_{frame}"
                    self.flame.image = (
                        f"flame_wall_jump_{dir_index}_{flame_frame}"
                    )

            elif dx == 0:
                self.image = "stand_front"
                self.flame.image = f"flame_stand_{(game.timer // 4) % 8}"

            elif self.change_direction_timer > 0:
                # If change_direction_timer is positive, use change direction frame
                self.image = f"change_dir_{dir_index}_0"
                self.flame.image = (
                    f"flame_change_dir_{dir_index}_{(game.timer // 4) % 3}"
                )
            else:
                # 8 frames of the run animation, switch animation frame every 4 game frames
                frame = (game.timer // 4) % 8
                self.image = f"run_{dir_index}_{frame}"
                self.flame.image = (
                    f"flame_run_{dir_index}_{(game.timer // 4) % 8}"
                )

    @override
    def draw(self) -> None:
        super().draw()

        self.flame.pos = self.pos
        self.flame.draw()

        if DEBUG_SHOW_PLAYER_COLLISION_RECT:
            # Show collision rectangle
            r: IntRect = self.get_rect()
            renderer.rect(r.left, r.top, r.width, r.height, (255, 255, 255))

    @override
    def get_collidable_width(self) -> int:
        return PLAYER_WIDTH

    @override
    def get_collidable_height(self) -> int:
        return PLAYER_HEIGHT


@dataclass(eq=False, slots=True)
class GhostPlayer(Actor):
    replay_data: Replay
    replay_frame: int = 0
    #: The level the recorded player was on; drawn only while it matches ours
    level: int = 0

    def __post_init__(self) -> None:
        super().__init__("blank", self.replay_data[0][0], ANCHOR_PLAYER)

    def update(self) -> None:
        self.replay_frame += 1
        if self.replay_frame < len(self.replay_data):
            self.pos, self.level, sprite = self.replay_data[self.replay_frame]
            self.image = "blank" if sprite == "blank" else f"ghost_{sprite}"

    @override
    def draw(self) -> None:
        # Only draw if we're on the same level as the actual player
        if self.level == game.level_index:
            super().draw()


# Not a dataclass: the super-kwargs and half the attributes are derived from
# the ENEMY_TYPES_* lookup tables -- the init logic is the interesting part.
class Enemy(GravityActor):
    __slots__ = (
        "direction_x",
        "type",
        "biome",
        "health",
        "speed",
        "direction_y",
        "use_directional_sprites",
        "dying",
        "stomped_timer",
    )

    def __init__(
        self,
        pos: PointLike,
        type: int,
        biome: Biome,
        direction_x: int = 1,
        appearance_count: int = 1,
    ) -> None:
        # Type must be a number from 0 to 3. 0 and 1 are both flying robots which don't have different frames for facing
        # left or right. 2 and 3 are non-flying robots which do have left/right facing frames.

        super().__init__(
            pos,
            gravity_enabled=not ENEMY_TYPES_FLYING[biome][type],
            anchor=ENEMY_TYPES_ANCHOR_POINTS[biome][type],
        )

        self.direction_x: int = direction_x
        self.type: int = type
        self.biome: Biome = biome

        self.health: int = ENEMY_TYPES_HEALTH[type]
        self.speed: int = ENEMY_TYPES_SPEED[type]

        # Flying enemies which are on their third appearance will move diagonally
        self.direction_y: int = (
            1 if appearance_count >= 3 and not self.gravity_enabled else 0
        )

        # Robot types 2 and 3, and fly/ghost have different sprites for facing left/right
        self.use_directional_sprites: bool = (
            self.biome == Biome.CASTLE and self.type >= 2
        ) or (self.biome == Biome.FOREST and self.type < 2)

        self.dying: bool = False
        self.stomped_timer: int = 0

    def update(self) -> None:
        # Apply gravity first - a dying enemy falls out of the level without collision detection
        self.fall(detect=not self.dying)

        if not self.dying:
            self.stomped_timer -= 1

            # Don't move on x axis if falling. Flying enemies are always counted as falling by GravityActor, they
            # should move regardless.
            if (
                not self.gravity_enabled
                or self.fall_state != GravityActor.FallState.FALLING
            ):
                # Move in current direction - turn around if we hit a wall
                if self.move(self.direction_x, 0, self.speed):
                    self.direction_x = -self.direction_x
                if self.direction_y != 0 and self.move(
                    0, self.direction_y, self.speed
                ):
                    self.direction_y = -self.direction_y

        # Choose and set sprite image
        image: str = ENEMY_SPRITE_NAMES[self.biome][self.type]
        if self.use_directional_sprites:
            image += "_1" if self.direction_x > 0 else "_0"
        image += f"_{(game.timer // 4) % 8}"  # 8 frames of animation
        if self.stomped_timer > 0 or self.dying:
            image += "_hit"
        self.image = image

    def stomped(self) -> None:
        # Don't lose health or play sound effect if we're being stomped multiple frames in a row
        if self.stomped_timer <= 0:
            self.health -= 1
            if self.health <= 0:
                self.destroy()
                game.play_sound("enemy_death", 5)
            else:
                game.play_sound("enemy_take_damage", 5)
        self.stomped_timer = 2

    def destroy(self) -> None:
        self.dying = True
        self.gravity_enabled = True

        # Create explosion animation. Do this before gain_time so it appears underneath gain time animation
        explosion_sprite: str = (
            "explosion" if self.type > 1 else "air_explosion"
        )
        game.animations.append(
            Animation(
                self.pos,
                f"{explosion_sprite}_{{0}}",
                12,
                4,
                ANCHOR_CENTRE_BOTTOM,
            )
        )

        # Destroying an enemy always gains 3 seconds of time
        game.gain_time(STOMP_ENEMY_TIME_BONUS, self.centerx, self.centery)

    @override
    def get_collidable_width(self) -> int:
        return ENEMY_TYPES_WIDTH_OVERRIDES[self.biome][self.type]

    @override
    def get_collidable_height(self) -> int:
        return ENEMY_TYPES_HEIGHT_OVERRIDES[self.biome][self.type]

    @override
    def draw(self) -> None:
        super().draw()

        if DEBUG_SHOW_ENEMY_COLLISION_RECTS:
            # Show collision rectangle
            r: IntRect = self.get_rect()
            renderer.rect(r.left, r.top, r.width, r.height, (255, 255, 255))


def _find(node: ET.Element, path: str) -> ET.Element:
    # The first element matching path under node; a level file without it is malformed
    found: ET.Element | None = node.find(path)
    if found is None:
        raise ValueError(f"level file is missing <{path}>")
    return found


@dataclass(eq=False, slots=True)
class Game:
    #: None only for a game with nobody playing (there is none today: every Game gets a Player)
    player: Player | None = None
    #: Earlier games' recordings, replayed as ghosts
    replays: InitVar[list[Replay] | None] = None
    ghost_players: list[GhostPlayer] = field(init=False)
    timer: int = field(default=0, init=False)
    #: In frames (60 per second); gems and stomps add to it
    time_remaining: float = field(
        default=INITIAL_TIME_REMAINING * 60, init=False
    )
    #: Seconds a gem is worth, shrinking each time round the level sequence
    time_pickup_bonus: float = field(
        default=INITIAL_PICKUP_TIME_BONUS, init=False
    )
    gained_time_timer: int = field(default=0, init=False)
    level_index: int = field(
        default=(INITIAL_LEVEL_CYCLE * len(LEVEL_SEQUENCE)) - 1, init=False
    )
    level_text: str = field(default="", init=False)
    #: These are set during load_level (tile ids per row, -1 for empty)
    grid: list[list[int]] = field(init=False)
    tileset_image: Image = field(init=False)
    background_image: str = field(init=False)
    background_y_offset: int = field(default=0, init=False)
    collision_tiles: set[int] = field(init=False)
    #: And these during next_level
    block_rects: list[IntRect] = field(init=False)
    doors: list[Door] = field(init=False)
    gems: list[Gem] = field(init=False)
    enemies: list[Enemy] = field(init=False)
    animations: list[Animation] = field(init=False)
    exit_open: bool = field(init=False)

    def __post_init__(self, replays: list[Replay] | None) -> None:
        # Gem class is told via a static method that a new game has started, so it can reset the next gem type variable
        Gem.new_game()

        self.ghost_players = [GhostPlayer(replay) for replay in replays or []]

        self.next_level()

    def next_level(self) -> None:
        self.level_index += 1

        # If the new level is a repeat of the first level, reduce self.time_pickup_bonus by 1 (to a minimum of 0.5)
        if (
            self.level_index != 0
            and self.level_index % len(LEVEL_SEQUENCE) == 0
        ):
            if self.time_pickup_bonus > 1:
                self.time_pickup_bonus -= 1
            elif self.time_pickup_bonus == 1:
                self.time_pickup_bonus = 0.5

        self.block_rects = []
        self.doors = []
        self.gems = []
        self.enemies = []
        self.animations = []
        self.level_text = ""

        # Set up level
        level_filename: str = LEVEL_SEQUENCE[
            self.level_index % len(LEVEL_SEQUENCE)
        ]
        player_start_pos: tuple[float, float] = self.load_level(level_filename)

        self.exit_open = False

        if self.player is not None:
            self.player.new_level(player_start_pos)

        # Generate collidable areas
        self.generate_block_rects()

        if self.player is not None:
            self.player.reset()

        self.play_sound("new_wave")

    def load_level(self, filename: str) -> tuple[float, float]:
        # Returns player start pos, or (0,0) if none is found
        player_start_pos: tuple[float, float] = (0, 0)

        # 0 for first time through the levels, 1 for second, etc
        level_cycle: int = self.level_index // len(LEVEL_SEQUENCE)

        # sys.path[0] gets the folder containing the Python file we're running
        # This is necessary because we could be running in an IDE where the default working folders is not the script
        # folder but is instead the parent folder, or we could be running preinstalled on a Raspberry Pi in which case
        # the current working folder is the user's home folder
        path: str = os.path.join(sys.path[0], "tilemaps")

        # The map and tileset files are XML files. We're using Python's built in ElementTree module (aliased here as ET)
        # to access the tags/nodes within the XML files.
        map_root: ET.Element = ET.parse(os.path.join(path, filename)).getroot()

        # Load background
        properties_node: ET.Element = _find(map_root, "properties")
        self.background_image = _find(
            properties_node, "./property[@name='Background']"
        ).attrib["value"]
        bg_offset_node: ET.Element | None = properties_node.find(
            "./property[@name='Background Offset Y']"
        )
        self.background_y_offset = (
            int(bg_offset_node.attrib["value"])
            if bg_offset_node is not None
            else 0
        )

        # Load biome (used for determining which types of enemies and doors to generate)
        biome_node: ET.Element | None = properties_node.find(
            "./property[@name='biome']"
        )
        biome_name: str = (
            biome_node.attrib["value"] if biome_node is not None else ""
        )
        biome: Biome = Biome[biome_name.upper()]

        # Default level name text - may be replaced by tutorial text below
        self.level_text = f"LEVEL {self.level_index + 1}"

        # Set up level tutorial text - only the first time we go round the levels.
        # Some text will have parts which we need to substitute
        # Use blank level text if there is no player object (i.e. we're on the main menu)
        tutorial_text_node: ET.Element | None = properties_node.find(
            "./property[@name='TutorialText']"
        )
        if self.player is not None and tutorial_text_node is not None:
            tutorial_text: str = tutorial_text_node.attrib["value"]
            if level_cycle == 0 and tutorial_text:
                self.level_text = tutorial_text.replace(
                    "{DASH}", self.player.controls.button_name("dash")
                ).replace("{JUMP}", self.player.controls.button_name("jump"))

        # The map data consists of a comma-separated list of integers specifying tile IDs
        # The XML path is map/layer/data
        layer_node: ET.Element = _find(map_root, "layer")
        map_width: int = int(layer_node.attrib["width"])
        map_height: int = int(layer_node.attrib["height"])
        map_text: str | None = _find(layer_node, "data").text
        if map_text is None:
            raise ValueError(f"empty map data in {filename}")
        map_data: list[str] = map_text.split(",")

        # Convert map data from CSV into a 2D list of ints, one list per row
        # We subtract 1 from each tile ID because we want the tile IDs to start from 0 (signifying the top left of the
        # tileset image) rather than 1. This means that empty tile will now have an ID of -1
        self.grid = [
            [
                int(tile) - 1
                for tile in map_data[row * map_width : (row + 1) * map_width]
            ]
            for row in range(map_height)
        ]

        # Read object layer, which specifies things like the player start position, gems and enemies
        object_group_node: ET.Element | None = map_root.find("objectgroup")
        if object_group_node is not None:
            for object_node in object_group_node.findall("object"):
                object_name: str = object_node.attrib["name"]

                # Extract the object position. Why do we write 'int(float(...))'? Because the number is read from the
                # file as a string, and we'd like it as an int, but we also want to ignore anything after the
                # decimal point, which we don't care about. We can't convert directly from string to int because
                # that would fail when it encountered a number with a decimal point.
                object_pos: tuple[int, int] = (
                    int(float(object_node.attrib["x"])),
                    int(float(object_node.attrib["y"])),
                )
                match object_name:
                    case "PlayerStart":
                        player_start_pos = object_pos

                    case "Gem":
                        self.gems.append(Gem(object_pos))

                    case name if "Enemy" in name:
                        # Enemies have names such as "EnemyR00" where L/R indicate their initial facing direction, the
                        # first number indicates the enemy type (0 to 3), and the final number indicates the level
                        # cycle during which they first show up. Some enemies only show up on the second or third
                        # cycle through the levels
                        enemy_level_cycle: int = int(name[-1])
                        appearance_count: int = (
                            level_cycle - enemy_level_cycle + 1
                        )
                        if appearance_count >= 1:
                            facing: int = 1 if name[-3] == "R" else -1
                            enemy_type: int = int(name[-2])
                            self.enemies.append(
                                Enemy(
                                    object_pos,
                                    enemy_type,
                                    biome,
                                    facing,
                                    appearance_count,
                                )
                            )

                    case name if "Door" in name:
                        variant_node: ET.Element | None = object_node.find(
                            "./properties/property[@name='Variant']"
                        )
                        door_biome_node: ET.Element | None = object_node.find(
                            "./properties/property[@name='Biome']"
                        )
                        variant: str | int = (
                            variant_node.attrib["value"]
                            if variant_node is not None
                            else 0
                        )
                        door_biome_name: str = (
                            door_biome_node.attrib["value"]
                            if door_biome_node is not None
                            else biome_name
                        )
                        self.doors.append(
                            Door(
                                object_pos,
                                door_biome_name,
                                variant,
                                already_open="Entrance" in name,
                            )
                        )

                    case _:
                        raise ValueError(
                            f"unknown object {object_name!r} in {filename}"
                        )

        # For the purpose of simplicity we assume that each map file only uses one tileset, which will be either the
        # forest or castle tileset. The tileset filename is specified in the 'tileset' tag within the root node
        tileset_filename: str = _find(map_root, "tileset").attrib["source"]

        # Read tileset file, which specifies which tiles are collidable
        # For now we'll just assume that any tile which has a node, has collision
        tileset_root: ET.Element = ET.parse(
            os.path.join(path, tileset_filename)
        ).getroot()
        self.collision_tiles = {
            int(tile_node.attrib["id"])
            for tile_node in tileset_root.findall("tile")
        }

        # Load tileset image (if we haven't loaded it already)
        tileset_image_filename: str = _find(tileset_root, "image").attrib[
            "source"
        ]
        if tileset_image_filename not in tileset_images:
            tileset_images[tileset_image_filename] = Image.load(
                os.path.join(path, tileset_image_filename)
            )
        self.tileset_image = tileset_images[tileset_image_filename]

        return player_start_pos

    def generate_block_rects(self) -> None:
        self.block_rects = []
        current_rect: IntRect | None = None

        def add() -> None:
            nonlocal current_rect
            assert current_rect is not None
            self.block_rects.append(current_rect)
            current_rect = None

        # Horizontal rows
        for gy, row in enumerate(self.grid):
            for gx, tile in enumerate(row):
                if tile in self.collision_tiles:
                    # Is this the start of a new block rect?
                    if current_rect is None:
                        current_rect = IntRect(
                            gx * GRID_BLOCK_SIZE,
                            gy * GRID_BLOCK_SIZE,
                            GRID_BLOCK_SIZE,
                            GRID_BLOCK_SIZE,
                        )
                    else:
                        # Continue existing rect
                        current_rect.width += GRID_BLOCK_SIZE

                elif current_rect is not None:
                    add()
            if current_rect is not None:
                add()

        # Now consolidate vertically
        # Keep joining rectangles with rectangles of equal width directly below, until there are no more such
        # matches

        def find_equal_width_block_below(current: IntRect) -> IntRect | None:
            # Returns a block with the same X coordinate and width, which is immediately below the current block,
            # or None if no such block exists
            return next(
                (
                    rect
                    for rect in self.block_rects
                    if rect.left == current.left
                    and rect.width == current.width
                    and rect.top == current.bottom
                ),
                None,
            )

        any_found: bool = True
        while any_found:
            any_found = False
            for current in self.block_rects:
                equal_below: IntRect | None = find_equal_width_block_below(
                    current
                )
                if equal_below is not None:
                    # Extend the height of the current block and remove the one below
                    current.height += equal_below.height
                    self.block_rects.remove(equal_below)
                    any_found = True
                    break

        # Final step: any block rects aligning with the top of the level have their height increased so it extends
        # above the level, to prevent standing on top of the trees off the top of the screen
        for rect in self.block_rects:
            if rect.top == 0:
                rect.top = LEVEL_Y_BOUNDARY
                rect.height -= LEVEL_Y_BOUNDARY

    def update(self) -> None:
        self.timer += 1
        self.gained_time_timer -= 1

        if self.time_remaining > 0:
            self.time_remaining -= 1

        # Update all objects, in this order
        objects: list[GameObject] = [
            *([] if self.player is None else [self.player]),
            *self.doors,
            *self.animations,
            *self.gems,
            *self.enemies,
            *self.ghost_players,
        ]
        for obj in objects:
            obj.update()

        # Remove expired enemies, dash trails, gems and animations
        self.enemies = [enemy for enemy in self.enemies if enemy.top < HEIGHT]
        self.animations = [
            anim for anim in self.animations if not anim.finished()
        ]
        self.gems = [gem for gem in self.gems if not gem.collected]

        # Check stuff to do with opening exit door and exiting level (but not if we're on the main menu)
        if self.player is not None:
            if self.exit_open:
                # Check for the player leaving the level
                if self.player.centerx >= WIDTH:
                    self.next_level()

            elif not self.gems:
                # All gems collected, open the exit door
                self.exit_open = True
                for door in self.doors:
                    door.open()

    def draw(self) -> None:
        # Draw appropriate background for this level
        blit(self.background_image, 0, self.background_y_offset)

        # Draw level tiles: each tile ID picks one 25x25 region of the tileset image
        tileset_grid_w: int = self.tileset_image.width // GRID_BLOCK_SIZE
        for row_y, row in enumerate(self.grid):
            for column, tile in enumerate(row):
                if tile >= 0:
                    renderer.draw_image_region(
                        self.tileset_image,
                        (column * GRID_BLOCK_SIZE, row_y * GRID_BLOCK_SIZE),
                        IntRect(
                            (tile % tileset_grid_w) * GRID_BLOCK_SIZE,
                            (tile // tileset_grid_w) * GRID_BLOCK_SIZE,
                            GRID_BLOCK_SIZE,
                            GRID_BLOCK_SIZE,
                        ),
                    )

        # Draw all objects, in this order
        objects: list[GameObject] = [
            *self.ghost_players,
            *self.doors,
            *self.animations,
            *([] if self.player is None else [self.player]),
            *self.gems,
            *self.enemies,
        ]
        for obj in objects:
            obj.draw()

        # DEBUG - draw block rects
        if DEBUG_SHOW_BLOCK_COLLISION_RECTS:
            for rect in self.block_rects:
                renderer.rect(
                    rect.left,
                    rect.top,
                    rect.width,
                    rect.height,
                    (255, 255, 255),
                )

        self.draw_ui()

    def draw_ui(self) -> None:
        # Display level text and background
        renderer.filled_rect(0, 500, WIDTH, 50, (0, 54, 255))
        blit("text_area_frame", 0, 500)
        draw_text(self.level_text, WIDTH // 2, 508, align=TextAlign.CENTRE)

        # Show background sprite for time remaining
        blit("status_back", WIDTH // 2 - 297 // 2, 0)

        # Show time remaining
        # Use bright font if player has just gained time
        font: str = "font" if self.gained_time_timer < 0 else "fontbr"
        draw_text(
            f"{self.time_remaining / 60:.1f}",
            WIDTH // 2,
            10,
            align=TextAlign.CENTRE,
            font=font,
        )

        if DEBUG_SHOW_FRAME_NUMBER:
            draw_text(str(game.timer), WIDTH // 2, 0, align=TextAlign.CENTRE)

    def gain_time(self, time: float, x: float, y: float) -> None:
        self.time_remaining += time * 60
        # The "+2" style images are named by the whole seconds gained, "half" for 0.5
        time_added_id: str = "half" if time == 0.5 else str(time)
        self.animations.append(
            Animation(
                (x, y),
                f"timer_plus_{time_added_id}_{{0}}",
                14,
                4,
                initial_delay=5,
                rise_time=34,
            )
        )
        self.animations.append(Animation((x, y), "pickup_{0}", 8, 4))
        self.gained_time_timer = 20

    def position_blocked(self, rect: IntRect) -> bool:
        # Blocked by a block tile, a door that isn't fully open, the left side of the screen or the vertical
        # boundary above. We do need to allow the player to go off the right side of the screen so they can go
        # through the exit door
        return (
            any(rect.colliderect(block_rect) for block_rect in self.block_rects)
            or any(
                not door.is_fully_open() and door.colliderect(rect)
                for door in self.doors
            )
            or rect.left <= 0
            or rect.top < LEVEL_Y_BOUNDARY
        )

    def play_sound(self, name: str, count: int = 1) -> None:
        # Some sounds have multiple varieties, named "name0", "name1", ... If count > 1, we'll randomly choose one
        # We don't play any sounds if there is no player (e.g. if we're on the menu)
        if self.player is not None:
            try:
                sounds.load(f"{name}{randint(0, count - 1)}").play()
            except Exception as e:
                # If no sound file of that name was found, print the error, which includes the filename.
                # Also occurs if sound fails to play for another reason (e.g. if this machine has no sound hardware)
                print(e)


def get_char_image_and_width(char: str, font: str) -> tuple[Image | None, int]:
    # Return the image and width of the given character. ord() gives the Unicode code for the given character.
    # Character images are named by the code formatted to always be 3 digits, with zeroes on the left - e.g. 65
    # becomes 065 - except the controller button symbols, which have their own images
    if char == " ":
        return None, 22
    image: Image = images.load(
        SPECIAL_FONT_SYMBOLS_INVERSE.get(char, f"{font}{ord(char):03d}")
    )
    return image, image.width


def text_width(text: str, font: str) -> int:
    return sum(get_char_image_and_width(c, font)[1] for c in text)


class TextAlign(Enum):
    LEFT = 0
    CENTRE = 1
    RIGHT = 2


def draw_text(
    text: str,
    x: float,
    y: float,
    align: TextAlign = TextAlign.LEFT,
    font: str = "font",
) -> None:
    match align:
        case TextAlign.CENTRE:
            x -= text_width(text, font) // 2
        case TextAlign.RIGHT:
            x -= text_width(text, font)
        case TextAlign.LEFT:
            pass
        case _:
            raise ValueError(f"unhandled text alignment {align!r}")

    for char in text:
        image, width = get_char_image_and_width(char, font)
        if image is not None:
            renderer.draw_image(image, (x, y))
        x += width


class State(Enum):
    TITLE = 1
    CONTROLS = 2
    PLAY = 3
    GAME_OVER = 4


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


def get_save_folder() -> str:
    # By default, we save to the same folder as the Python file
    # But if the current working folder is the same as the user's home folder, write save data to a subfolder of that,
    # because the folder containing the Python file may not be writeable. This is relevant when the games are run from
    # the pre-installed versions which come with Raspberry Pi OS
    # On Windows, the home folder is C:\Users\<username>\
    if os.getcwd() != os.path.expanduser("~"):
        return sys.path[0]
    # Get a location within the user's home folder, then ensure the folder exists
    path: str = os.path.expanduser("~/.code-the-classics-vol-2")
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def save_replays(replays: list[Replay]) -> None:
    # We'll save one replay per line. Each entry consists of a position (X and Y), level number and sprite; we
    # separate the items using commas and the entries using semicolons. It doesn't matter what the symbols are as
    # long as they don't occur within the data. Open the replays file to see what it looks like!
    try:
        with open(
            os.path.join(get_save_folder(), REPLAY_FILENAME), "w"
        ) as file:
            for replay in replays:
                line: str = ";".join(
                    f"{int(px)},{int(py)},{level},{sprite}"
                    for (px, py), level, sprite in replay
                )
                file.write(line + "\n")
    except Exception as e:
        print(f"Error while saving replays: {e}")


def load_replays() -> tuple[list[Replay], int]:
    # Returns list of replays and high score
    replays: list[Replay] = []
    try:
        path: str = os.path.join(get_save_folder(), REPLAY_FILENAME)
        if os.path.exists(path):
            with open(path) as file:
                for line in file:
                    # One replay per line, entries separated by semicolons, items by commas (see save_replays)
                    current_replay: Replay = []
                    for entry in line.rstrip().split(";"):
                        x, y, level, sprite = entry.split(",")
                        current_replay.append(
                            ((float(x), float(y)), int(level), sprite)
                        )
                    replays.append(current_replay)

    except Exception as e:
        # In case of error (eg missing file or formatting error), just return an empty list, and high score of zero
        print(f"Error while loading replays: '{e}'. Replay data will be reset")
        return [], 0

    # The high score is stored as the total number of frames of data in the replay with the longest length
    high_score: int = max((len(replay) for replay in replays), default=0)

    return replays, high_score


def update() -> None:
    global \
        state, \
        game, \
        high_score, \
        game_over_state_timer, \
        all_replays, \
        total_frames

    # Run in slow motion if DEBUG_SLOWMO is higher than 1
    total_frames += 1
    if total_frames % DEBUG_SLOWMO != 0:
        return

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
            if button_pressed_controls(0) is not None:
                state = State.CONTROLS

        case State.CONTROLS:
            # Check for start game
            controls: Controls | None = button_pressed_controls(0)
            if controls is not None:
                # Switch to play state, and create a new Game object, passing it a new Player object to use
                state = State.PLAY
                game = Game(Player(controls), all_replays)
                play_music("ingame_theme", 0.2)

        case State.PLAY:
            if game.time_remaining <= 0:
                game.play_sound("gameover")
                state = State.GAME_OVER
                game_over_state_timer = 0

                # Add the replay data for this game to all_replays (a game in the PLAY state always has a player)
                assert game.player is not None
                all_replays.append(game.player.replay_data)

                # Ensure that all_replays never has more than 10 replays, otherwise there could be performance issues
                if len(all_replays) > MAX_REPLAYS:
                    # Keep only the 10 longest
                    all_replays.sort(key=len, reverse=True)
                    all_replays = all_replays[:MAX_REPLAYS]

                save_replays(all_replays)
            else:
                game.update()

        case State.GAME_OVER:
            # Don't allow the player to press a button to go back to the main menu until one second has passed
            # This prevents the issue of accidentally skipping the game over screen because the player was just starting
            # to press the jump button as the time ran out
            game_over_state_timer += 1
            if (
                game_over_state_timer > 60
                and button_pressed_controls(0) is not None
            ):
                # Update high score variable at this point
                high_score = max(high_score, game.timer)

                # Switch to title screen state
                state = State.TITLE
                play_music("title_theme")

        case _:
            raise ValueError(f"unhandled game state {state!r}")


def draw() -> None:
    match state:
        case State.TITLE:
            # Draw title screen
            blit("title", 0, 0)
            blit("press_to_start", 0, 0)

            # Draw "start" animation, which has 11 frames numbered 0 to 10
            blit(f"start{(total_frames // 6) % 11}", WIDTH // 2 - 150, 360)

        case State.CONTROLS:
            # (the frame is already cleared to black)
            blit("controls", 0, 0)

        case State.PLAY:
            game.draw()

        case State.GAME_OVER:
            renderer.fill((0, 54, 255))

            # Display "Game Over" images
            # 625 is the width of the game over images
            blit(
                f"gameover{(total_frames // 5) % 14}",
                WIDTH // 2 - 625 // 2,
                100,
            )

            seconds: int = int(game.timer / 60)
            if seconds >= 60:
                blit("survived_for_mins_seconds", 0, 0)
                draw_text(
                    f"{seconds // 60}",
                    180,
                    270,
                    align=TextAlign.RIGHT,
                    font="fontlrg",
                )
                draw_text(
                    f"{seconds % 60}",
                    470,
                    270,
                    align=TextAlign.CENTRE,
                    font="fontlrg",
                )
            else:
                blit("survived_for_seconds", 0, 0)
                draw_text(
                    f"{seconds}",
                    300,
                    310,
                    align=TextAlign.RIGHT,
                    font="fontlrg",
                )

            if game.timer > high_score:
                # Show "NEW RECORD!"
                # 575 is the width of the new record images
                blit(
                    f"newrecord{(total_frames // 5) % 8}",
                    WIDTH // 2 - 575 // 2,
                    380,
                )

        case _:
            raise ValueError(f"unhandled game state {state!r}")


def play_music(name: str, volume: float = 0.3) -> None:
    music.play(name)
    music.set_volume(volume)


##############################################################################

# Start the music (with no sound device the game simply plays silently)
play_music("title_theme")

# Dictionary mapping tileset image filename to the loaded images, will be filled in as we load levels
tileset_images: dict[str, Image] = {}

# Set up controls
keyboard_controls: KeyboardControls = KeyboardControls()
joystick_controls: JoystickControls | None
setup_joystick_controls()

all_replays: list[Replay]
all_replays, high_score = load_replays()

# Set the initial game state
state: State = State.TITLE

# No game object to begin with: one is created when a game starts, and nothing
# touches it on the menus (declared here, bound at the first start)
game: Game

# How long have we been in the game over state?
game_over_state_timer: int = 0

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

# Fixed 60 Hz timestep -- eggzy's update() takes no dt. PGZERO_MAX_FRAMES=N
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
