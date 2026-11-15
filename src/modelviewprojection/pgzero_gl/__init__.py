# Copyright (c) 2026 William Emerison Six
# SPDX-License-Identifier: LGPL-2.1-only
# Full license text: src/modelviewprojection/pgzero_gl/LICENSE.

"""``pgzero_gl`` -- the engine pieces the Code-the-Classics ports share.

The ports under ``ports/codetheclassics/`` are faithful GLFW + OpenGL 3.3
core ports of Raspberry Pi Press's "Code the Classics" games (originally
PyGame Zero). Each game owns its loop, renderer, sprites and input, and
calls down into these modules for the parts that are the same in every game
and teach nothing about the game itself:

* :mod:`.audio` -- the one-device software mixer: ``Sound``, ``Music``,
  ``shutdown_audio``;
* :mod:`.resources` -- ``Image`` (CPU pixels, lazy GL texture) and the
  cached per-folder ``Loader``;
* :mod:`.gl` -- shader compile/link, a 2-D position VAO + VBO, and the
  pixel-space orthographic projection.

It is a library, not a framework: nothing here calls back into a game.
"""
