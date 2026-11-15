# Copyright (c) 2026 William Emerison Six
# SPDX-License-Identifier: LGPL-2.1-only
# Full license text: src/modelviewprojection/pgzero_gl/LICENSE.

"""Sound effects and a music track, mixed in software on ONE miniaudio device.

Every effect is decoded into memory once, each play is a "voice" over that
buffer, the music streams from disk in chunks, and the device's callback sums
the live voices. Starting or stopping a voice is a flag flip -- zero device
operations after startup. (One OS stream per voice, the earlier design,
audibly clunked and eventually froze a game once the audio client slots ran
out; see tasks/archive/2026/07/09/leadingedge-audio-clunk-and-freeze.md.)

Audio is BEST EFFORT: if miniaudio can't be imported or no device opens,
every call is a no-op and the game plays silently (as it does headless).

A game calls down into it::

    sounds: Loader[Sound] = Loader(ASSET_ROOT, "sounds", ("ogg",), Sound)
    sounds.load("hit0").play()
    music: Music = Music(ASSET_ROOT)
    music.play("theme")
    ...
    shutdown_audio()  # once, after the game's loop ends
"""

from __future__ import annotations

import os
import threading
from collections.abc import Generator, Iterator
from dataclasses import InitVar, dataclass, field
from typing import TYPE_CHECKING, Any, TypeAlias, cast

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    import miniaudio

#: interleaved float32 PCM at the mixing format
_PCM: TypeAlias = NDArray[np.float32]

# the miniaudio module, or None if it isn't installed (Any: the sentinel
# and the module share a type)
_ma: Any = None
try:
    import miniaudio as _miniaudio

    _ma = _miniaudio
except Exception:  # pragma: no cover - depends on runtime env
    pass

# One mixing format for everything; decode/stream converts to it.
_SAMPLE_RATE: int = 44100
_CHANNELS: int = 2

# Cap the concurrent voices per effect so a rapidly re-fired sound (the
# ball hitting a bat) recycles its oldest voice instead of piling up.
_MAX_VOICES_PER_SOUND: int = 8


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
        """Ramp this voice to silence over ``ms`` milliseconds, then stop it."""
        frames: float = max(_SAMPLE_RATE * ms / 1000.0, 1.0)
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
            device: miniaudio.PlaybackDevice = _ma.PlaybackDevice(
                output_format=_ma.SampleFormat.FLOAT32,
                nchannels=_CHANNELS,
                sample_rate=_SAMPLE_RATE,
            )
            gen: Generator[_PCM, int, None] = self._mixer()
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
        required: int = yield np.zeros(0, dtype=np.float32)
        while True:
            out: _PCM = np.zeros(required * _CHANNELS, dtype=np.float32)
            with self._lock:
                voices: list[_Voice] = list(self._voices)
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
        filled: int = 0
        while filled < frames and not v.done:
            if v.stream is not None:
                chunk: _PCM | None = self._next_stream_chunk(v)
                if chunk is None:
                    v.done = True
                    break
                take: int = min(frames - filled, len(chunk) // _CHANNELS)
                seg: _PCM = chunk[: take * _CHANNELS]
                # stash any remainder for the next pull
                rest: _PCM = chunk[take * _CHANNELS :]
                v.samples = rest if len(rest) else None
            else:
                assert v.samples is not None
                total: int = len(v.samples) // _CHANNELS
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
                ramp: _PCM = v.fade_gain + v.fade_step * np.arange(
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
            sl: slice = slice(filled * _CHANNELS, (filled + take) * _CHANNELS)
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
        self,
        samples: _PCM,
        volume: float,
        looping: bool = False,
        fade_in_ms: float = 0.0,
    ) -> _Voice | None:
        """Start a voice over a decoded effect; ``None`` when audio is off."""
        if not self._ensure_device():
            return None
        v: _Voice = _Voice(samples, None, volume, looping, fade_in_ms)
        with self._lock:
            self._voices.append(v)
        return v

    def play_stream(
        self, stream: Iterator[Any], volume: float
    ) -> _Voice | None:
        """Start a voice over a chunk stream; ``None`` when audio is off."""
        if not self._ensure_device():
            return None
        v: _Voice = _Voice(None, stream, volume, False, 0.0)
        with self._lock:
            self._voices.append(v)
        return v

    def stop_voice(self, v: _Voice) -> None:
        """Mark ``v`` finished; the mixer drops it on its next callback."""
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
            device: miniaudio.PlaybackDevice | None = self._device
            self._device = None
        if device is not None:
            try:
                device.close()
            except Exception:
                pass


#: The one mixer every Sound and Music plays through.
_engine: _Engine = _Engine()


def shutdown_audio() -> None:
    """Tear down the audio backend at game exit (see :meth:`_Engine.shutdown`)."""
    _engine.shutdown()


def _decode(path: str) -> _PCM:
    decoded: Any = _ma.decode_file(  # miniaudio DecodedSoundFile
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
        """Play the effect, overlapping any prior plays.

        Args:
            loops: ``-1`` (any non-zero value) loops it until :meth:`stop`.
            fade_ms: Ramp this play up from silence over this many ms.
            volume: Override this effect's volume for THIS play only.
        """
        if _ma is None:
            return
        buf: _PCM | None = self._buffer()
        if buf is None:
            return
        live: list[_Voice] = self._live()
        if len(live) >= _MAX_VOICES_PER_SOUND:
            _engine.stop_voice(live[0])  # oldest voice yields its budget
        v: _Voice | None = _engine.play_buffer(
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
class Music:
    """The single streamed, looping background track of one game."""

    #: The game's asset directory; tracks are looked up under ``music/``.
    root: str
    #: The playing track's voice, or None when stopped.
    _voice: _Voice | None = None
    _volume: float = 1.0
    #: Read by the stream generator at the end of each pass through the file.
    _looping: bool = False

    def _path(self, name: str) -> str | None:
        """Resolve a track ``name`` to a file under ``music/``, or ``None``."""
        base: str = os.path.join(self.root, "music", name)
        if os.path.isfile(base):
            return base
        for ext in ("ogg", "mp3", "wav"):
            p: str = base + "." + ext
            if os.path.exists(p):
                return p
        return None

    def _stream(self, path: str) -> Iterator[Any]:
        outer: Music = self

        def gen() -> Iterator[Any]:
            # music streams from disk (a decoded multi-minute track would be
            # tens of MB); looping restarts the stream, so the loop seam
            # lands on a chunk boundary.
            while True:
                inner: Any = _ma.stream_file(  # miniaudio stream iterator
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
