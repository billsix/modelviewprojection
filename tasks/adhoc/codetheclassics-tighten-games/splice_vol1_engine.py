#!/usr/bin/env python3
# Copyright (c) 2026 William Emerison Six
#
# Build the tightened ENGINE half of a vol1-minimal-family game (cavern,
# myriapod) by splicing boing's already-tightened engine
# (ports/codetheclassics/vol1/boing/boing.py, the pilot that set the standard)
# and adding back the two sections those games need that boing does not: a
# float Rect and the anchored Actor sprite class. Per tasks/reference/
# code-the-classics-tightening.md section 3: the inlined engines are identical
# within a family, so the engine is tightened ONCE here and hand-tightening is
# reserved for each game's own half. The per-game differences the engine has
# are parameters: the game name (header/docstring), window title, and the
# keyboard names the game reads.
#
# Usage: python splice_vol1_engine.py <name> <Title> <key,names,...> [WxH] > engine.py
#   e.g. python splice_vol1_engine.py cavern Cavern left,right,up,space 800x480
#        python splice_vol1_engine.py myriapod Myriapod left,right,up,down,space 480x800

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BOING = REPO / "ports/codetheclassics/vol1/boing/boing.py"

RECT_AND_ACTOR = '''
# ===== engine: rectangles and sprites =====
#
# An Actor is an image positioned by an anchor (default: its centre) in the
# top-left-origin pixel space, backed by a float rectangle so movement at
# non-integer speeds keeps its sub-pixel position. The game's objects subclass
# Actor: ``actor.image = "name"`` swaps the sprite keeping the anchor position,
# and ``.pos`` / ``.x`` / ``.y`` are the anchor position (``.pos`` as a gacalc
# vector, so game code adds velocities and takes differences directly).

#: A position the engine accepts: a pair, or a gacalc vector (both unpack).
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

'''


# pygame key names whose GLFW constant is not just the upper-cased name
_KEY_ALIASES: dict[str, str] = {
    "lctrl": "LEFT_CONTROL",
    "rctrl": "RIGHT_CONTROL",
    "lshift": "LEFT_SHIFT",
    "rshift": "RIGHT_SHIFT",
    "lalt": "LEFT_ALT",
    "ralt": "RIGHT_ALT",
}


def build_engine(
    name: str, title: str, key_names: list[str], size: str = "800x480"
) -> str:
    src = BOING.read_text()
    engine = src[: src.index("# ===== game code =====")]

    def rep(old: str, new: str) -> None:
        nonlocal engine
        assert engine.count(old) == 1, old[:60]
        engine = engine.replace(old, new)

    rep("# Code the Classics port: boing, with its rendering engine inlined.",
        f"# Code the Classics port: {name}, with its rendering engine inlined.")
    # the module docstring is the game's own; the caller supplies it
    doc_start = engine.index('"""')
    doc_end = engine.index('"""', doc_start + 3) + 3
    engine = engine[:doc_start] + "@@DOCSTRING@@" + engine[doc_end:]
    rep("import random\n", "from random import choice, randint, random, shuffle\n")
    rep("from enum import Enum\n", "from enum import Enum, IntEnum\n")
    rep("from typing import TYPE_CHECKING, Any, Protocol, cast\n",
        "from typing import TYPE_CHECKING, Any, ClassVar, Protocol, cast, override\n")
    width, height = size.split("x")
    rep("WIDTH: int = 800\nHEIGHT: int = 480\n", f"WIDTH: int = {width}\nHEIGHT: int = {height}\n")
    rep('TITLE: str = "Boing!"', f'TITLE: str = "{title}"')
    rep('''    boing.py implements it with OpenGL 3.3 core + shaders (``Renderer``);
    boing_gl1.py with fixed-function OpenGL 1.x (``Renderer1x``) -- the same
    interface, the same pixels, so the game code is identical in both files.
''', '''    ``Renderer`` below implements it with OpenGL 3.3 core + shaders (see
    boing_gl1.py for the fixed-function OpenGL 1.x rendering of the same
    interface).
''')
    # sprite drawing: this family draws through Actor; only blit() stays
    rep('''# ===== engine: sprite drawing =====
# boing draws sprites by name: two module functions look up a sprite's
# texture and draw its quad -- the course's function-and-struct style, no
# sprite-object manager.


def blit(name: str, x: float, y: float) -> None:
    """Draw sprite ``name`` with its TOP-LEFT at ``(x, y)`` -- backgrounds and UI."""
    renderer.draw_image(images.load(name), (x, y))


def draw_sprite(name: str, cx: float, cy: float) -> None:
    """Draw sprite ``name`` CENTRED on ``(cx, cy)`` -- the ball, bats, impacts."""
    img: Image = images.load(name)
    renderer.draw_image(img, (cx - img.width / 2, cy - img.height / 2))
''', '''# ===== engine: sprite drawing =====
# Backgrounds, blocks, text and status icons are drawn by name at a top-left
# pixel position; the moving objects are Actors (next section).


def blit(name: str, x: float, y: float) -> None:
    """Draw sprite ``name`` with its TOP-LEFT at ``(x, y)``."""
    renderer.draw_image(images.load(name), (x, y))
''' + RECT_AND_ACTOR)
    rep('''# ``keyboard.<name>`` is True while that key is held. The main block's GLFW
# key callback feeds presses and releases in; the game polls the names below
# each frame -- they are the only keys boing reads.
''', f'''# ``keyboard.<name>`` is True while that key is held. The GLFW key callback
# below feeds presses and releases in; the game polls the names in the table
# each frame -- they are the only keys {name} reads.
''')
    table_start = engine.index("_NAME_TO_KEY: dict[str, int] = {")
    table_end = engine.index("}\n", table_start) + 2
    if key_names:
        table = "_NAME_TO_KEY: dict[str, int] = {\n" + "".join(
            f'    "{k}": glfw.KEY_{_KEY_ALIASES.get(k, k.upper())},\n'
            for k in key_names
        ) + "}\n"
        engine = engine[:table_start] + table + engine[table_end:]
        return engine
    # No key names: the game reads keys by GLFW code (``keyboard[code]``),
    # so there is no name table and ``__getitem__`` replaces ``__getattr__``.
    engine = engine[:table_start] + engine[table_end:].lstrip("\n")
    rep(
        "# ``keyboard.<name>`` is True while that key is held. The GLFW key callback\n"
        "# below feeds presses and releases in; the game polls the names in the table\n"
        f"# each frame -- they are the only keys {name} reads.\n",
        "# ``keyboard[code]`` is True while that GLFW key is held. The GLFW key\n"
        "# callback below feeds presses and releases in; the game polls the codes\n"
        "# it needs each frame.\n",
    )
    rep(
        '    """``keyboard.<name>`` is True while that key is held."""',
        '    """``keyboard[code]`` is True while that GLFW key is held."""',
    )
    rep(
        "    def __getattr__(self, name: str) -> bool:\n"
        '        """Return whether the named key (``keyboard.space``, ...) is held."""\n'
        "        code: int | None = _NAME_TO_KEY.get(name)\n"
        "        if code is None:\n"
        "            raise AttributeError(name)\n"
        "        return code in self._pressed\n",
        "    def __getitem__(self, code: int) -> bool:\n"
        '        """Return whether the GLFW key ``code`` is currently held."""\n'
        "        return code in self._pressed\n",
    )
    return engine


if __name__ == "__main__":
    name, title = sys.argv[1], sys.argv[2]
    keys = [] if sys.argv[3] == "-" else sys.argv[3].split(",")
    size = sys.argv[4] if len(sys.argv) > 4 else "800x480"
    sys.stdout.write(build_engine(name, title, keys, size))
