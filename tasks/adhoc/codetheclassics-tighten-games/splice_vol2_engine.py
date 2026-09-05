#!/usr/bin/env python3
# Copyright (c) 2026 William Emerison Six
#
# Build the tightened ENGINE half of a vol2 game (kinetix, avenger, eggzy,
# leadingedge, beatstreets) = the vol1 family engine (splice_vol1_engine.py:
# boing's tightened engine + Rect + Actor) plus the vol2-only sections each game
# opts into with a flag:
#
#   surface   -- Surface, an Image the game can fill()/blit() into on the CPU
#                (kinetix's brick + shadow layers, the vol2 fade overlays),
#                built by make_surface(); the renderer draws it like any Image
#   joystick  -- Joystick (GLFW gamepad: hats, axes, buttons) + joystick_count()
#   clip      -- Renderer.set_clip(rect) -> glScissor (screen.surface.set_clip)
#   sound     -- the full sound API: looping plays, per-effect and per-play
#                volume, stop, fade-in/fade-out ramps, music.fadeout (avenger's
#                thrust loop and distance-attenuated shots, leadingedge's engine
#                crossfades)
#   mask      -- Mask, a per-pixel opacity grid from an image's alpha, built by
#                mask_from_image() (avenger's terrain collision)
#   lines     -- Renderer.line for flag-gated debug overlays
#
# Usage: python splice_vol2_engine.py <name> <Title> <keys|-> <WxH> <flag,flag,...>
#   e.g. python splice_vol2_engine.py kinetix Kinetix left,right,space 640x640 surface,joystick,clip

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from splice_vol1_engine import build_engine  # noqa: E402

SURFACE = '''

@dataclass(slots=True, eq=False)
class Surface(Image):
    """An Image the game draws INTO on the CPU (``fill``/``blit`` composite
    into ``rgba``); the GL texture is re-uploaded lazily when dirty. Built by
    :func:`make_surface`. These change rarely (e.g. when a brick breaks), so
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


def make_surface(width: int, height: int, transparent: bool) -> Surface:
    """A ``width`` x ``height`` surface, fully transparent or opaque black."""
    rgba: NDArray[np.uint8] = np.zeros((height, width, 4), dtype=np.uint8)
    if not transparent:
        rgba[..., 3] = 255
    return Surface(rgba)
'''

JOYSTICK = '''

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
'''

CLIP_METHOD = '''
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
'''
SOUND_PATCHES = [
    ('''    samples: _PCM | None
    stream: Iterator[Any] | None
    volume: float
    #: frame offset into ``samples`` (buffer voices only)
    pos: int = field(default=0, init=False)
    done: bool = field(default=False, init=False)
''', '''    samples: _PCM | None
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
'''),
    ('''                if v.pos >= total:
                    v.done = True
                    break
''', '''                if v.pos >= total:
                    if v.looping:
                        v.pos = 0  # gapless wraparound
                        continue
                    v.done = True
                    break
'''),
    ('''            sl = slice(filled * _CHANNELS, (filled + take) * _CHANNELS)
            out[sl] += seg * v.volume
            filled += take
''', '''            gain: _PCM | float
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
'''),
    ('''    def play_buffer(self, samples: _PCM, volume: float) -> _Voice | None:
        if not self._ensure_device():
            return None
        v = _Voice(samples, None, volume)
''', '''    def play_buffer(
        self, samples: _PCM, volume: float, looping: bool, fade_in_ms: float
    ) -> _Voice | None:
        if not self._ensure_device():
            return None
        v = _Voice(samples, None, volume, looping, fade_in_ms)
'''),
    ("        v = _Voice(None, stream, volume)\n", "        v = _Voice(None, stream, volume, False, 0.0)\n"),
    ('''    path: str
    #: The decoded PCM, filled on the first play.
    _samples: _PCM | None = field(default=None, init=False)
    #: This effect's live voices (capped at ``_MAX_VOICES_PER_SOUND``).
    _voices: list[_Voice] = field(default_factory=list, init=False)
''', '''    path: str
    #: The decoded PCM, filled on the first play.
    _samples: _PCM | None = field(default=None, init=False)
    #: Volume (0.0-1.0) for current and future plays.
    _volume: float = field(default=1.0, init=False)
    #: This effect's live voices (capped at ``_MAX_VOICES_PER_SOUND``).
    _voices: list[_Voice] = field(default_factory=list, init=False)
'''),
    ('''    def play(self) -> None:
        """Play the effect, overlapping any prior plays still sounding."""
        if _ma is None:''', '''    def play(
        self, loops: int = 0, fade_ms: int = 0, volume: float | None = None
    ) -> None:
        """Play the effect, overlapping any prior plays; ``loops=-1`` loops it
        until :meth:`stop`; ``fade_ms`` ramps this play up from silence;
        ``volume`` overrides this effect's volume for THIS play only (the
        distance-attenuated shots)."""
        if _ma is None:'''),
    ('''        v = _engine.play_buffer(buf, 1.0)
        if v is not None:
            self._voices.append(v)
''', '''        v = _engine.play_buffer(
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
'''),
    ('''    def stop(self) -> None:
        """Stop the current track."""
        self._looping = False
        if self._voice is not None:
            _engine.stop_voice(self._voice)
            self._voice = None
''', '''    def stop(self) -> None:
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
'''),
]

MASK = '''

@dataclass(slots=True, eq=False)
class Mask:
    """A per-pixel opacity grid (True where opaque), for terrain collision.
    Built by :func:`mask_from_image`."""

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
        return 0 <= x < self.width and 0 <= y < self.height and bool(self.opaque[y, x])


def mask_from_image(image: Image, threshold: int = 127) -> Mask:
    """The mask of ``image``: pixels with alpha above ``threshold`` are opaque."""
    return Mask(image.rgba[..., 3] > threshold)
'''

LINE_METHOD = '''
    def line(
        self, start: Vector, end: Vector, color: tuple[int, int, int]
    ) -> None:
        """Draw a one-pixel line segment (the debug overlays)."""
        verts: NDArray[np.float32] = np.array(
            [*start, *end], dtype=np.float32
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
        GL.glDrawArrays(GL.GL_LINES, 0, 2)
'''
LINE_PROTOCOL = '''

    def line(
        self, start: Vector, end: Vector, color: tuple[int, int, int]
    ) -> None: ...'''

CLIP_PROTOCOL = '''

    def set_clip(
        self, rect: tuple[float, float, float, float] | None
    ) -> None: ...'''

RECTLIKE_PROTOCOL = '''
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


'''

RECT_COLLIDERECT = '''
    def colliderect(self, o: RectLike) -> bool:
        """Return whether this rect and ``o`` overlap (touching edges don't)."""
        return (
            self.left < o.right
            and self.right > o.left
            and self.top < o.bottom
            and self.bottom > o.top
        )
'''

INTRECT = '''


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
'''

ACTOR_COLLIDE = '''
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
'''

FILL_METHOD = '''
    def fill(self, color: tuple[int, int, int]) -> None:
        """Clear the whole frame to ``color``."""
        r, g, b = color
        GL.glClearColor(r / 255.0, g / 255.0, b / 255.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
'''
FILL_PROTOCOL = '''

    def fill(self, color: tuple[int, int, int]) -> None: ...'''

RECT_METHODS = '''
    def filled_rect(
        self, x: float, y: float, w: float, h: float, color: tuple[int, int, int]
    ) -> None:
        """Draw a filled rectangle at ``(x, y)`` of size ``(w, h)``."""
        model: NDArray[np.float32] = _translate(x=x, y=y) @ _scale(sx=w, sy=h)
        GL.glBindVertexArray(self.quad.vao)
        GL.glUniformMatrix4fv(self.uniforms.model, 1, GL.GL_TRUE, model)
        GL.glUniform1i(self.uniforms.use_tex, 0)
        r, g, b = color
        GL.glUniform4f(self.uniforms.tint, r / 255.0, g / 255.0, b / 255.0, 1.0)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)

    def rect(
        self, x: float, y: float, w: float, h: float, color: tuple[int, int, int]
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
'''
RECT_PROTOCOL = '''

    def filled_rect(
        self, x: float, y: float, w: float, h: float, color: tuple[int, int, int]
    ) -> None: ...

    def rect(
        self, x: float, y: float, w: float, h: float, color: tuple[int, int, int]
    ) -> None: ...'''

REGION_METHOD = '''
    def draw_image_region(
        self, image: Image, topleft: tuple[float, float], region: IntRect
    ) -> None:
        """Draw only ``region`` (a pixel rect within ``image``, e.g. one tile of
        a tileset) with its top-left at ``topleft``."""
        tx, ty = topleft
        model: NDArray[np.float32] = _translate(x=tx, y=ty) @ _scale(
            sx=region.width, sy=region.height
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
'''
REGION_PROTOCOL = '''

    def draw_image_region(
        self, image: Image, topleft: tuple[float, float], region: IntRect
    ) -> None: ...'''

SCALE_FUNC = '''


def scale_image(image: Image, width: int, height: int) -> Image:
    """A copy of ``image`` resized to ``width`` x ``height`` pixels (nearest
    neighbour, so pixel art stays crisp), as a new Image with its own texture."""
    pil = PILImage.fromarray(image.rgba).resize(
        (max(1, width), max(1, height)), PILImage.Resampling.NEAREST
    )
    return image_from_rgba(np.array(pil.convert("RGBA")))
'''

POLYGON_METHOD = '''
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
'''
POLYGON_PROTOCOL = '''

    def polygon(
        self,
        points: Sequence[PointLike],
        color: tuple[int, int, int],
        filled: bool,
    ) -> None: ...'''

TEXT = '''


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
        _text_cache[key] = image_from_rgba(np.array(surf))
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
'''

CIRCLE_METHOD = '''
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
'''
CIRCLE_PROTOCOL = '''

    def circle(
        self, pos: PointLike, radius: float, color: tuple[int, int, int]
    ) -> None: ...'''


def build_vol2_engine(name: str, title: str, keys: list[str], size: str, flags: set[str]) -> str:
    s = build_engine(name, title, keys, size)

    def rep(old: str, new: str) -> None:
        nonlocal s
        assert s.count(old) == 1, old[:60]
        s = s.replace(old, new)

    def add_protocol(text: str) -> None:
        nonlocal s
        ps = s.index("class SpriteRenderer(Protocol):")
        pe = s.index("\n\n\n", ps)
        s = s[:pe] + text + s[pe:]

    def add_renderer_method(text: str) -> None:
        # after draw_image's last line in the Renderer class
        nonlocal s
        anchor = "        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)\n"
        i = s.index(anchor) + len(anchor)
        s = s[:i] + text + s[i:]

    def ensure_prim() -> None:
        # the renderer's dynamic buffer for lines/outlines: field, construction
        if "    prim: GLBuffer\n" in s:
            return
        rep("    #: The unit quad [0,1]x[0,1] as two triangles -- every sprite's geometry\n    quad: GLBuffer\n",
            "    #: The unit quad [0,1]x[0,1] as two triangles -- every sprite's geometry\n    quad: GLBuffer\n    #: A dynamic buffer the debug overlays fill per draw\n    prim: GLBuffer\n")
        rep("    quad = _make_buffer(quad_verts)\n", "    quad = _make_buffer(quad_verts)\n    prim = _make_buffer(None)\n")
        rep("        uniforms,\n        quad,\n    )", "        uniforms,\n        quad,\n        prim,\n    )")

    def ensure_intrect() -> None:
        # RectLike protocol before the float Rect, Rect.colliderect, IntRect after it
        if "class IntRect:" in s:
            return
        rep("@dataclass(slots=True)\nclass Rect:", RECTLIKE_PROTOCOL + "@dataclass(slots=True)\nclass Rect:")
        anchor = "        return self.left <= px < self.right and self.top <= py < self.bottom\n"
        i = s.index(anchor) + len(anchor)
        s_ = s[:i] + RECT_COLLIDERECT + INTRECT.rstrip("\n") + s[i:]
        s_set(s_)

    def s_set(new: str) -> None:
        nonlocal s
        s = new

    if "surface" in flags:
        anchor = "def image_from_rgba(arr: NDArray[Any]) -> Image:"
        i = s.index(anchor)
        j = s.index("\n\n\n", i)
        s = s[:j] + SURFACE.rstrip("\n") + s[j:]
    if "clip" in flags:
        ps = s.index("class SpriteRenderer(Protocol):")
        pe = s.index("\n\n\n", ps)
        s = s[:pe] + CLIP_PROTOCOL + s[pe:]
        # after draw_image's last line in the Renderer class
        anchor = "        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)\n"
        i = s.index(anchor) + len(anchor)
        s = s[:i] + CLIP_METHOD + s[i:]
    if "sound" in flags:
        for old, new in SOUND_PATCHES:
            rep(old, new)
    if "mask" in flags:
        anchor = "def image_from_rgba(arr: NDArray[Any]) -> Image:"
        i = s.index(anchor)
        j = s.index("\n\n\n", i)
        s = s[:j] + MASK.rstrip("\n") + s[j:]
    if "lines" in flags:
        ps = s.index("class SpriteRenderer(Protocol):")
        pe = s.index("\n\n\n", ps)
        s = s[:pe] + LINE_PROTOCOL + s[pe:]
        anchor = "        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)\n"
        i = s.index(anchor) + len(anchor)
        s = s[:i] + LINE_METHOD + s[i:]
        ensure_prim()
    if "collide" in flags:
        ensure_intrect()
        anchor = "        return self._rect.collidepoint(p)\n"
        i = s.index(anchor) + len(anchor)
        s = s[:i] + ACTOR_COLLIDE + s[i:]
    if "fill" in flags:
        add_protocol(FILL_PROTOCOL)
        add_renderer_method(FILL_METHOD)
    if "rect" in flags:
        add_protocol(RECT_PROTOCOL)
        add_renderer_method(RECT_METHODS)
        ensure_prim()
    if "region" in flags:
        ensure_intrect()
        add_protocol(REGION_PROTOCOL)
        add_renderer_method(REGION_METHOD)
    if "scale" in flags:
        anchor = "def image_from_rgba(arr: NDArray[Any]) -> Image:"
        i = s.index(anchor)
        j = s.index("\n\n\n", i)
        s = s[:j] + SCALE_FUNC.rstrip("\n") + s[j:]
    if "polygon" in flags:
        add_protocol(POLYGON_PROTOCOL)
        add_renderer_method(POLYGON_METHOD)
        ensure_prim()
    if "text" in flags:
        rep("from PIL import Image as PILImage\n",
            "from PIL import Image as PILImage\nfrom PIL import ImageDraw, ImageFont\n")
        # after the window section (renderer exists), before the keyboard
        anchor = "\n\n# ===== engine: rectangles and sprites ====="
        i = s.index(anchor)
        s = s[:i] + TEXT.rstrip("\n") + s[i:]
    if "circle" in flags:
        add_protocol(CIRCLE_PROTOCOL)
        add_renderer_method(CIRCLE_METHOD)
        ensure_prim()
    if "joystick" in flags:
        anchor = "\n\n# ===== game code ====="
        s = s.replace(anchor, JOYSTICK.rstrip("\n") + anchor) if anchor in s else s + JOYSTICK
    return s


if __name__ == "__main__":
    name, title = sys.argv[1], sys.argv[2]
    keys = [] if sys.argv[3] == "-" else sys.argv[3].split(",")
    size = sys.argv[4]
    flags = set(sys.argv[5].split(",")) if len(sys.argv) > 5 else set()
    sys.stdout.write(build_vol2_engine(name, title, keys, size, flags))
