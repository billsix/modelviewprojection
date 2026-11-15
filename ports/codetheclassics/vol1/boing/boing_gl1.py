# Code the Classics port: boing_gl1, with its rendering engine inlined.
#
# Game code derived from Raspberry Pi Press's "Code the Classics" (vol 1):
#   Copyright (c) 2019 Eben Upton <eben@raspberrypi.org>
# Inlined engine (audio, images, renderer, keyboard, loop):
#   Copyright (c) 2026 William Emerison Six
# SPDX-License-Identifier: BSD-2-Clause
# Full license text: ports/codetheclassics/LICENSE.
"""boing_gl1 -- the OpenGL 1.x (fixed-function) rendering of boing.

A study companion to boing.py: the SAME game, drawn with the OpenGL 1.x
fixed-function pipeline (a 2.1 compatibility context + glOrtho + glBegin/glEnd
immediate mode + fixed-function texturing) instead of 3.3 core + shaders. Diff
this file against boing.py to see exactly what changes between the two
pipelines -- the game logic is identical; only the renderer (Renderer1x,
below) and the window/context setup differ. The fixed-function era here is
the one the book introduces at demo19 (glMatrixMode / glOrtho / glBegin /
glEnable(GL_TEXTURE_2D)).
"""

from __future__ import annotations

import os
import random
import signal
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import InitVar, dataclass, field
from enum import Enum
from typing import Any, Protocol

import glfw
import OpenGL.GL as GL
from gacalc.g2 import Vector

from modelviewprojection.pgzero_gl.audio import Music, Sound, shutdown_audio
from modelviewprojection.pgzero_gl.resources import Image, Loader

# ===== engine: shared state =====

WIDTH: int = 800
HEIGHT: int = 480
TITLE: str = "Boing!"

#: The directory holding this game's ``images/``, ``sounds/`` and ``music/``.
ASSET_ROOT: str = os.path.dirname(os.path.abspath(__file__))


class SpriteRenderer(Protocol):
    """What the game needs of a rendering pipeline: start a frame, then draw
    textured sprites into pixel space.

    boing.py implements it with OpenGL 3.3 core + shaders (``Renderer``);
    boing_gl1.py with fixed-function OpenGL 1.x (``Renderer1x``) -- the same
    interface, the same pixels, so the game code is identical in both files.
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


# ===== engine: audio =====
#
# Sound effects and the music track play through the shared software mixer,
# modelviewprojection.pgzero_gl.audio (one miniaudio device, best effort:
# silent when no device opens). The game only says where its music/ is.

music: Music = Music(ASSET_ROOT)


# ===== engine: images and sounds =====
#
# ``images.load("ball")`` reads ``images/ball.png`` once and caches it;
# ``sounds.load("hit0")`` does the same under ``sounds/``. An image decodes to
# a CPU RGBA array immediately, so its size is known before the window exists
# (game objects are built at import time), but its GL texture is uploaded
# lazily on first draw, because the GL context doesn't exist yet at import.


images: Loader[Image] = Loader(
    ASSET_ROOT, "images", ("png", "gif", "jpg", "jpeg", "bmp"), Image.load
)
sounds: Loader[Sound] = Loader(
    ASSET_ROOT, "sounds", ("ogg", "wav", "oga"), Sound
)

# ===== engine: renderer (fixed-function OpenGL 1.x) =====
#
# The game positions its sprites in a top-left-origin, y-down pixel space. A
# fixed-function orthographic projection (glOrtho) maps that space to NDC, and
# every sprite is an immediate-mode textured quad (glBegin/glEnd +
# glTexCoord2f/glVertex2f), translated and scaled into place on the modelview
# stack. No shaders, no VAO -- the pipeline the book introduces at demo19. The
# interface is identical to boing.py's 3.3-core Renderer, so blit(),
# draw_sprite() and all the game code below are unchanged, and the two files
# draw the same pixels.


@dataclass(slots=True, eq=False)
class Renderer1x:
    """Fixed-function (OpenGL 1.x) renderer; the same interface as boing.py's
    ``Renderer``. Build one with
    :meth:`Renderer1x.create` once the GL context exists; the constructor takes
    already-linked GL objects (tests, or another backend, may pass their own).
    """

    #: logical (game) pixels
    width: int
    height: int
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
        """Start a frame: update framebuffer size, clear, set the pixel-space ortho."""
        if fb_width and fb_height:
            self.fb_width = fb_width
            self.fb_height = fb_height
        GL.glDisable(GL.GL_SCISSOR_TEST)
        GL.glViewport(0, 0, self.fb_width, self.fb_height)
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        # Pixel-space projection: (0,0) top-left .. (W,H) bottom-right.
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(0.0, self.width, self.height, 0.0, -1.0, 1.0)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

    def draw_image(self, image: Image, topleft: tuple[float, float]) -> None:
        """Draw ``image`` as a textured quad with its top-left at ``topleft``."""
        tx, ty = topleft
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, image.gl_texture())
        # Sprites draw untinted: GL_MODULATE multiplies the texture by glColor.
        GL.glColor4f(1.0, 1.0, 1.0, 1.0)

        GL.glPushMatrix()
        GL.glTranslatef(tx, ty, 0.0)
        GL.glScalef(image.width, image.height, 1.0)
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 0.0)
        GL.glVertex2f(0.0, 0.0)
        GL.glTexCoord2f(1.0, 0.0)
        GL.glVertex2f(1.0, 0.0)
        GL.glTexCoord2f(1.0, 1.0)
        GL.glVertex2f(1.0, 1.0)
        GL.glTexCoord2f(0.0, 1.0)
        GL.glVertex2f(0.0, 1.0)
        GL.glEnd()
        GL.glPopMatrix()

    @classmethod
    def create(cls, width: int, height: int) -> Renderer1x:
        """Build the renderer for a ``width`` x ``height`` pixel game: set the
        blend state and the fixed-function texture environment (texture * glColor,
        matching the 3.3 path's frag = texture * uTint). Needs a current GL
        context."""
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
        return cls(width, height)


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
# OpenGL 2.1 compatibility context: 2.1 predates the core/compat profile
# split, so request version 2.1 with the default (ANY) profile and no
# forward-compat. The fixed-function pipeline this game draws with (glOrtho
# + glBegin) is not available in a 3.3 core context -- that is the whole
# point of this GL 1.x variant. See boing.py for the 3.3-core original.
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
window: Any = glfw.create_window(  # GLFW window handle
    WIDTH, HEIGHT, TITLE, None, None
)
if not window:
    glfw.terminate()
    raise RuntimeError("glfw.create_window() failed")
glfw.make_context_current(window)
glfw.swap_interval(1)
# No VAO: the fixed-function pipeline needs none (VAOs are a 3.0+ construct).
renderer: SpriteRenderer = Renderer1x.create(WIDTH, HEIGHT)

# ===== engine: sprite drawing =====
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


# ===== engine: keyboard =====
#
# ``keyboard.<name>`` is True while that key is held. The main block's GLFW
# key callback feeds presses and releases in; the game polls the names below
# each frame -- they are the only keys boing reads.

_NAME_TO_KEY: dict[str, int] = {
    "a": glfw.KEY_A,
    "z": glfw.KEY_Z,
    "k": glfw.KEY_K,
    "m": glfw.KEY_M,
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


keyboard: Keyboard = Keyboard()


def _key_cb(win: Any, key: int, scancode: int, action: int, mods: int) -> None:
    if action == glfw.PRESS:
        keyboard.press(key)
        if key == glfw.KEY_ESCAPE:  # Esc always quits (no title-bar needed)
            glfw.set_window_should_close(win, True)
    elif action == glfw.RELEASE:
        keyboard.release(key)


glfw.set_key_callback(window, _key_cb)

# ===== game code =====

HALF_WIDTH: int = WIDTH // 2
HALF_HEIGHT: int = HEIGHT // 2

PLAYER_SPEED: int = 6
MAX_AI_SPEED: int = 6


class Sprite(Protocol):
    """What the game loop needs of anything that moves and draws: a centre
    position, the name of the sprite to draw there, and a per-frame update.
    Bat, Ball and Impact implement it. Protocols are structural: having the
    members IS implementing it, and the checker verifies each class where it
    flows into a ``Sprite`` (``Game.sprites``). Deliberately NOT declared by
    subclassing the protocol -- an explicit subclass inherits the stub members,
    so a missing method would go unreported.
    """

    x: float
    y: float
    image: str

    def update(self) -> None: ...


# Class for an animation which is displayed briefly whenever the ball bounces
# (eq=False on these dataclasses keeps identity comparison/hashing -- the
# generated __eq__ would compare fields and set __hash__ to None; slots=True
# fixes each object's attribute set to its declared fields)
@dataclass(eq=False, slots=True)
class Impact:
    #: The impact's CENTRE (where the ball bounced).
    x: float
    y: float
    #: Frames since the bounce; the sprite changes every 2 and the effect is
    #: removed at 10 (see Game.update).
    time: int = 0
    image: str = "blank"

    def update(self) -> None:
        # There are 5 impact sprites numbered 0 to 4. We update to a new sprite every 2 frames.
        self.image = "impact" + str(self.time // 2)

        # The Game class maintains a list of Impact instances. In Game.update, if the timer for an object
        # has gone beyond 10, the object is removed from the list.
        self.time += 1


@dataclass(eq=False, slots=True)
class Ball:
    #: The direction in which the ball is moving, as a unit vector. For
    #: example, if dir is (1, 0), the ball is moving to the right, with no
    #: movement up or down; if both components are negative, the ball is
    #: moving left and up, with the angle depending on their relative values.
    #: (The book's original uses two floats, dx and dy, and explains them as a
    #: vector; here it IS one -- a gacalc grade-1 vector of the plane's
    #: geometric algebra.)
    dir: Vector
    #: The ball's CENTRE, starting in the middle of the screen.
    x: float = HALF_WIDTH
    y: float = HALF_HEIGHT
    #: Pixels moved per frame, in unit steps; grows with every bat hit.
    speed: int = 5
    #: The sprite drawn at the centre.
    image: str = "ball"

    def update(self) -> None:
        # Each frame, we move the ball in a series of small steps - the number of steps being based on its speed attribute
        for _ in range(self.speed):
            # Store the previous x position
            original_x: float = self.x

            # Move the ball based on its direction vector
            self.x += self.dir.x
            self.y += self.dir.y

            # Check to see if ball needs to bounce off a bat

            # To determine whether the ball might collide with a bat, we first measure the horizontal distance from the
            # ball to the centre of the screen, and check to see if its edge has gone beyond the edge of the bat.
            # The centre of each bat is 40 pixels from the edge of the screen, or to put it another way, 360 pixels
            # from the centre of the screen. The bat is 18 pixels wide and the ball is 14 pixels wide. Given that these
            # sprites are anchored from their centres, when determining if they overlap or touch, we need to look at
            # their half-widths - 9 and 7. Therefore, if the centre of the ball is 344 pixels from the centre of the
            # screen, it can bounce off a bat (assuming the bat is in the right position on the Y axis - checked
            # shortly afterwards).
            # We also check the previous X position to ensure that this is the first frame in which the ball crossed the threshold.
            if (
                abs(self.x - HALF_WIDTH) >= 344
                and abs(original_x - HALF_WIDTH) < 344
            ):
                # Now that we know the edge of the ball has crossed the threshold on the x-axis, we need to check to
                # see if the bat on the relevant side of the arena is at a suitable position on the y-axis for the
                # ball collide with it.

                if self.x < HALF_WIDTH:
                    new_dir_x: int = 1
                    bat: Bat = game.bats[0]
                else:
                    new_dir_x = -1
                    bat = game.bats[1]

                difference_y: float = self.y - bat.y

                if difference_y > -64 and difference_y < 64:
                    # Ball has collided with bat - calculate new direction vector

                    # To understand the maths used below, we first need to consider what would happen with this kind of
                    # collision in the real world. The ball is bouncing off a perfectly vertical surface. This makes for a
                    # pretty simple calculation. Let's take a ball which is travelling at 1 metre per second to the right,
                    # and 2 metres per second down. Imagine this is taking place in space, so gravity isn't a factor.
                    # After the ball hits the bat, it's still going to be moving at 2 m/s down, but it's now going to be
                    # moving 1 m/s to the left instead of right. So its speed on the y-axis hasn't changed, but its
                    # direction on the x-axis has been reversed. This is extremely easy to code - "self.dir.x = -self.dir.x".
                    # However, games don't have to perfectly reflect reality.
                    # In Pong, hitting the ball with the upper or lower parts of the bat would make it bounce diagonally
                    # upwards or downwards respectively. This gives the player a degree of control over where the ball
                    # goes. To make for a more interesting game, we want to use realistic physics as the starting point,
                    # but combine with this the ability to influence the direction of the ball. When the ball hits the
                    # bat, we're going to deflect the ball slightly upwards or downwards depending on where it hit the
                    # bat. This gives the player a bit of control over where the ball goes.

                    # Bounce the opposite way on the X axis
                    self.dir = Vector(-self.dir.x, self.dir.y)

                    # Deflect slightly up or down depending on where ball hit bat
                    self.dir = Vector(
                        self.dir.x, self.dir.y + difference_y / 128
                    )

                    # Limit the Y component of the vector so we don't get into a situation where the ball is bouncing
                    # up and down too rapidly
                    self.dir = Vector(
                        self.dir.x, min(max(float(self.dir.y), -1), 1)
                    )

                    # Ensure our direction vector is a unit vector, i.e. represents a distance of the equivalent of
                    # 1 pixel regardless of its angle. (A zero vector would
                    # raise, but dir.x is always +/-1 here.)
                    self.dir = self.dir.normalize()

                    # Create an impact effect
                    game.impacts.append(Impact(self.x - new_dir_x * 10, self.y))

                    # Increase speed with each hit
                    self.speed += 1

                    # Add an offset to the AI player's target Y position, so it won't aim to hit the ball exactly
                    # in the centre of the bat
                    game.ai_offset = random.randint(-10, 10)

                    # Bat glows for 10 frames
                    bat.timer = 10

                    # Play hit sounds, with more intense sound effects as the ball gets faster
                    game.play_sound("hit", 5)  # play every time in addition to:
                    if self.speed <= 10:
                        game.play_sound("hit_slow", 1)
                    elif self.speed <= 12:
                        game.play_sound("hit_medium", 1)
                    elif self.speed <= 16:
                        game.play_sound("hit_fast", 1)
                    else:
                        game.play_sound("hit_veryfast", 1)

            # The top and bottom of the arena are 220 pixels from the centre
            if abs(self.y - HALF_HEIGHT) > 220:
                # Invert vertical direction and apply new dy to y so that the ball is no longer overlapping with the
                # edge of the arena
                self.dir = Vector(self.dir.x, -self.dir.y)
                self.y += self.dir.y

                # Create impact effect
                game.impacts.append(Impact(self.x, self.y))

                # Sound effect
                game.play_sound("bounce", 5)
                game.play_sound("bounce_synth", 1)

    def out(self) -> bool:
        # Has ball gone off the left or right edge of the screen?
        return self.x < 0 or self.x > WIDTH


@dataclass(eq=False, slots=True)
class Bat:
    #: 0 = the left-hand bat, 1 = the right-hand bat.
    player: int
    #: A function we may or may not have been passed by the code which created this object. If this bat
    #: is meant to be player controlled, it is a function that when called, returns a number indicating
    #: the direction and speed in which the bat should move, based on the keys the player is currently pressing.
    #: If None, this indicates that this bat should instead be controlled by the AI method
    #: (resolved into move_func in __post_init__, where self.ai exists).
    move_func_init: InitVar[Callable[[], float] | None] = None
    score: int = 0
    #: Each bat has a timer which starts at zero and counts down by one every frame. When a player concedes a point,
    #: their timer is set to 20, which causes the bat to display a different animation frame. It is also used to
    #: decide when to create a new ball in the centre of the screen - see comments in Game.update for more on this.
    #: Finally, it is used in Game.draw to determine when to display a visual effect over the top of the background
    timer: int = 0
    image: str = "blank"
    #: The bat's CENTRE, fixed by `player` in __post_init__.
    x: float = field(init=False)
    y: float = field(init=False)
    #: The movement function actually used: the player's, or this bat's own AI.
    move_func: Callable[[], float] = field(init=False)

    def __post_init__(self, move_func_init: Callable[[], float] | None) -> None:
        self.x = 40.0 if self.player == 0 else 760.0
        self.y = float(HALF_HEIGHT)
        self.move_func = move_func_init or self.ai

    def update(self) -> None:
        self.timer -= 1

        # Our movement function tells us how much to move on the Y axis
        y_movement: float = self.move_func()

        # Apply y_movement to y position, ensuring bat does not go through the side walls
        self.y = min(400, max(80, self.y + y_movement))

        # Choose the appropriate sprite. There are 3 sprites per player - e.g. bat00 is the left-hand player's
        # standard bat sprite, bat01 is the sprite to use when the ball has just bounced off the bat, and bat02
        # is the sprite to use when the bat has just missed the ball and the ball has gone out of bounds.
        # bat10, 11 and 12 are the equivalents for the right-hand player

        frame: int = (2 if game.ball.out() else 1) if self.timer > 0 else 0
        self.image = f"bat{self.player}{frame}"

    def ai(self) -> float:
        # Returns a number indicating how the computer player will move - e.g. 4 means it will move 4 pixels down
        # the screen.

        # To decide where we want to go, we first check to see how far we are from the ball.
        x_distance: float = abs(game.ball.x - self.x)

        # If the ball is far away, we move towards the centre of the screen (HALF_HEIGHT), on the basis that we don't
        # yet know whether the ball will be in the top or bottom half of the screen when it reaches our position on
        # the X axis. By waiting at a central position, we're as ready as it's possible to be for all eventualities.
        target_y_1: int = HALF_HEIGHT

        # If the ball is close, we want to move towards its position on the Y axis. We also apply a small offset which
        # is randomly generated each time the ball bounces. This is to make the computer player slightly less robotic
        # - a human player wouldn't be able to hit the ball right in the centre of the bat each time.
        target_y_2: float = game.ball.y + game.ai_offset

        # The final step is to work out the actual Y position we want to move towards. We use what's called a weighted
        # average - taking the average of the two target Y positions we've previously calculated, but shifting the
        # balance towards one or the other depending on how far away the ball is. If the ball is more than 400 pixels
        # (half the screen width) away on the X axis, our target will be half the screen height (target_y_1). If the
        # ball is at the same position as us on the X axis, our target will be target_y_2. If it's 200 pixels away,
        # we'll aim for halfway between target_y_1 and target_y_2. This reflects the idea that as the ball gets closer,
        # we have a better idea of where it's going to end up.
        weight1: float = min(1, x_distance / HALF_WIDTH)
        weight2: float = 1 - weight1

        target_y: float = (weight1 * target_y_1) + (weight2 * target_y_2)

        # Subtract target_y from our current Y position, then make sure we can't move any further than MAX_AI_SPEED
        # each frame
        return min(MAX_AI_SPEED, max(-MAX_AI_SPEED, target_y - self.y))


@dataclass(eq=False, slots=True)
class Game:
    #: The two players' control-input functions (or None for an AI player);
    #: __post_init__ hands them to the bats.
    controls: InitVar[Sequence[Callable[[], int] | None]] = (None, None)
    #: The two bats, each given a player number and its control function
    bats: list[Bat] = field(init=False)
    ball: Ball = field(init=False)
    #: The currently playing impact animations - these are displayed for a
    #: short time every time the ball bounces
    impacts: list[Impact] = field(default_factory=list, init=False)
    #: An offset added to the AI player's target Y position, so it won't aim
    #: to hit the ball exactly in the centre of the bat
    ai_offset: int = field(default=0, init=False)

    def __post_init__(
        self, controls: Sequence[Callable[[], int] | None]
    ) -> None:
        self.bats = [Bat(0, controls[0]), Bat(1, controls[1])]
        self.ball = Ball(Vector(-1, 0))

    def sprites(self) -> list[Sprite]:
        """Everything that moves and draws, in update-and-draw order: the two
        bats, the ball, then the impact effects."""
        return [*self.bats, self.ball, *self.impacts]

    def update(self) -> None:
        # Update all active objects
        for sprite in self.sprites():
            sprite.update()

        # Remove any expired impact effects - those whose time has reached 10
        self.impacts = [i for i in self.impacts if i.time < 10]

        # Has ball gone off the left or right edge of the screen?
        if self.ball.out():
            # Work out which player gained a point, based on whether the ball
            # was on the left or right-hand side of the screen
            scoring_player: int = 1 if self.ball.x < WIDTH // 2 else 0
            losing_player: int = 1 - scoring_player

            # We use the timer of the player who has just conceded a point to decide when to create a new ball in the
            # centre of the level. This timer starts at zero at the beginning of the game and counts down by one every
            # frame. Therefore, on the frame where the ball first goes off the screen, the timer will be less than zero.
            # We set it to 20, which means that this player's bat will display a different animation frame for 20
            # frames, and a new ball will be created after 20 frames
            if self.bats[losing_player].timer < 0:
                self.bats[scoring_player].score += 1

                game.play_sound("score_goal", 1)

                self.bats[losing_player].timer = 20

            elif self.bats[losing_player].timer == 0:
                # After 20 frames, create a new ball, heading in the direction of the player who just missed the ball
                direction: int = -1 if losing_player == 0 else 1
                self.ball = Ball(Vector(direction, 0))

    def draw(self) -> None:
        # Draw background
        blit("table", 0, 0)

        # Draw 'just scored' effects, if required
        for p in (0, 1):
            if self.bats[p].timer > 0 and game.ball.out():
                blit(f"effect{p}", 0, 0)

        # Draw bats, ball and impact effects - in that order
        for sprite in self.sprites():
            draw_sprite(sprite.image, sprite.x, sprite.y)

        # Display scores - outer loop goes through each player
        for p in (0, 1):
            # Convert score into a string of 2 digits (e.g. "05") so we can later get the individual digits
            score: str = f"{self.bats[p].score:02d}"
            # Inner loop goes through each digit
            for i in (0, 1):
                # Digit sprites are numbered 00 to 29, where the first digit is the colour (0 = grey,
                # 1 = blue, 2 = green) and the second digit is the digit itself
                # Colour is usually grey but turns red or green (depending on player number) when a
                # point has just been scored
                just_scored: bool = (
                    self.bats[1 - p].timer > 0 and game.ball.out()
                )
                colour: str = ("2" if p == 0 else "1") if just_scored else "0"
                blit(f"digit{colour}{score[i]}", 255 + (160 * p) + (i * 55), 46)

    def play_sound(
        self, name: str, count: int = 1, menu_sound: bool = False
    ) -> None:
        # Some sounds have multiple varieties. If count > 1, we'll randomly choose one from those
        # We don't play any in-game sound effects if player 0 is an AI player - as this means we're on the menu
        # (menu_sound lets the menu's own sounds through that check). A sound
        # that fails to load or play is skipped rather than stopping the game.
        if self.bats[0].move_func != self.bats[0].ai or menu_sound:
            try:
                sounds.load(f"{name}{random.randint(0, count - 1)}").play()
            except Exception:
                pass


def p1_controls() -> int:
    if keyboard.z or keyboard.down:
        return PLAYER_SPEED
    if keyboard.a or keyboard.up:
        return -PLAYER_SPEED
    return 0


def p2_controls() -> int:
    if keyboard.m:
        return PLAYER_SPEED
    if keyboard.k:
        return -PLAYER_SPEED
    return 0


class State(Enum):
    MENU = 1
    PLAY = 2
    GAME_OVER = 3


num_players: int = 1

# Is space currently being held down?
space_down: bool = False


# The game loop at the bottom of this file calls update() then draw() once
# per frame.


def update() -> None:
    global state, game, num_players, space_down

    # Work out whether the space key has just been pressed - i.e. in the previous frame it wasn't down,
    # and in this frame it is.
    space_pressed: bool = keyboard.space and not space_down
    space_down = keyboard.space

    match state:
        case State.MENU:
            if space_pressed:
                # Switch to play state, and create a new Game object, passing it the controls function for
                # player 1, and if we're in 2 player mode, the controls function for player 2 (otherwise the
                # 'None' value indicating this player should be computer-controlled)
                state = State.PLAY
                game = Game(
                    (p1_controls, p2_controls if num_players == 2 else None)
                )
            else:
                # Detect up/down keys
                if num_players == 2 and keyboard.up:
                    game.play_sound("up", menu_sound=True)
                    num_players = 1
                elif num_players == 1 and keyboard.down:
                    game.play_sound("down", menu_sound=True)
                    num_players = 2

                # Update the 'attract mode' game in the background (two AIs playing each other)
                game.update()

        case State.PLAY:
            # Has anyone won?
            if max(game.bats[0].score, game.bats[1].score) > 9:
                state = State.GAME_OVER
            else:
                game.update()

        case State.GAME_OVER:
            if space_pressed:
                # Reset to menu state
                state = State.MENU
                num_players = 1

                # Create a new Game object, without any players
                game = Game()

        case _:
            raise ValueError(f"unhandled game state {state!r}")


def draw() -> None:
    game.draw()

    match state:
        case State.MENU:
            menu_image: str = "menu" + str(num_players - 1)
            blit(menu_image, 0, 0)

        case State.PLAY:
            pass  # nothing drawn over the game while playing

        case State.GAME_OVER:
            blit("over", 0, 0)

        case _:
            raise ValueError(f"unhandled game state {state!r}")


# Start the music (with no sound device the game simply plays silently)
music.play("theme")
music.set_volume(0.3)

# Set the initial game state
state: State = State.MENU

# Create a new Game object, without any players
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

# Fixed 60 Hz timestep -- boing's update() takes no dt. PGZERO_MAX_FRAMES=N
# (set by the headless frame-capture harness) stops after N frames.
_max_frames: int = int(os.environ.get("PGZERO_MAX_FRAMES", "0") or 0)
_dt: float = 1.0 / 60.0
_next_t: float = time.perf_counter()
_frame_count: int = 0
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
        _sleep: float = _next_t - time.perf_counter()
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
