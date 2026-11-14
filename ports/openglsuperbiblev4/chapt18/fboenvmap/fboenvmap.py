# fboenvmap.py
# Dynamic environment mapping with cube maps. Each frame the scene is
# re-rendered six times (once per cube face) into a cubemap texture.
# Then the main pass draws the reflective center object using
# GL_REFLECTION_MAP texgen so it picks up the surrounding scene.
# Toggling FBO mode either renders straight to the cube map's faces
# (fast) or draws to the back buffer and copies it (slow).
#
# Keys: X/Y/Z + shift or arrows to move; Esc to quit. Env-mapping,
# show-env-map, and FBO toggles live on an imgui panel. Teapot
# replaced with a sphere.
#
# OpenGL SuperBible, Chapter 18
# Python port of fboenvmap.cpp by Benjamin Lipchak

import dataclasses
import os
import sys
import time
import typing
from typing import Any

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer
from OpenGL.constant import Constant

PWD: str = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402
import _primitives  # noqa: E402

ambient_light: list[float] = [0.4, 0.4, 0.4, 1.0]
diffuse_light: list[float] = [0.6, 0.6, 0.6, 1.0]
specular_light: list[float] = [1.0, 1.0, 1.0, 1.0]
light_pos: list[float] = [0.0, 125.0, 0.0, 1.0]


camera_zoom: float = 1.5


@dataclasses.dataclass
class AppState:
    """The app's mutable state; the one instance is ``state`` below."""

    window: typing.Any = None  # glfw window handle; set in main(), used by Quit
    window_width: int = 512
    window_height: int = 512
    env_map_size: int = 512

    use_env_map: bool = True
    show_env_map: bool = False
    use_fbo: bool = False

    wall_texture_id: list[int] = dataclasses.field(
        default_factory=lambda: [0] * 5
    )
    env_map_texture_id: int = 0
    framebuffer_id: int = 0
    renderbuffer_id: int = 0
    max_cube_tex_size: int = 0

    camera_pos: list[float] = dataclasses.field(
        default_factory=lambda: [50.0, 50.0, 100.0, 1.0]
    )
    animation_angle: float = 0.0


state: AppState = AppState()


SPHERE_CENTER: _primitives.Mesh = _primitives.build_sphere(20.0, 32, 32)
SPHERE: _primitives.Mesh = _primitives.build_sphere(25.0, 50, 50)
CONE: _primitives.Mesh = _primitives.build_cone(25.0, 50.0, 50)
TORUS: _primitives.Mesh = _primitives.build_torus(16.0, 8.0, 50, 50)


def draw_solid_octahedron() -> None:
    verts: list[tuple[int, int, int]] = [
        (1, 0, 0),
        (-1, 0, 0),
        (0, 1, 0),
        (0, -1, 0),
        (0, 0, 1),
        (0, 0, -1),
    ]
    faces: list[tuple[int, int, int]] = [
        (0, 2, 4),
        (0, 4, 3),
        (0, 3, 5),
        (0, 5, 2),
        (1, 4, 2),
        (1, 3, 4),
        (1, 5, 3),
        (1, 2, 5),
    ]
    GL.glBegin(GL.GL_TRIANGLES)
    i: int
    j: int
    k: int
    for i, j, k in faces:
        a: tuple[int, int, int] = verts[i]
        b: tuple[int, int, int] = verts[j]
        c: tuple[int, int, int] = verts[k]
        GL.glNormal3f(*a)
        GL.glVertex3f(*a)
        GL.glNormal3f(*b)
        GL.glVertex3f(*b)
        GL.glNormal3f(*c)
        GL.glVertex3f(*c)
    GL.glEnd()


def draw_models(draw_center: bool) -> None:
    GL.glColor3f(0.0, 0.0, 0.90)
    GL.glNormal3f(0.0, 1.0, 0.0)
    GL.glBegin(GL.GL_QUADS)
    GL.glVertex3f(-100.0, -25.0, -100.0)
    GL.glVertex3f(-100.0, -25.0, 100.0)
    GL.glVertex3f(100.0, -25.0, 100.0)
    GL.glVertex3f(100.0, -25.0, -100.0)
    GL.glEnd()

    GL.glEnable(GL.GL_TEXTURE_2D)
    walls: list[tuple[Any, ...]] = [
        (
            state.wall_texture_id[0],
            (1.0, 0.0, 0.0),
            [
                (-100, -25, 100),
                (-100, 125, 100),
                (-100, 125, -100),
                (-100, -25, -100),
            ],
        ),
        (
            state.wall_texture_id[2],
            (-1.0, 0.0, 0.0),
            [
                (100, -25, -100),
                (100, 125, -100),
                (100, 125, 100),
                (100, -25, 100),
            ],
        ),
        (
            state.wall_texture_id[1],
            (0.0, 0.0, 1.0),
            [
                (-100, -25, -100),
                (-100, 125, -100),
                (100, 125, -100),
                (100, -25, -100),
            ],
        ),
        (
            state.wall_texture_id[3],
            (0.0, 0.0, -1.0),
            [
                (100, -25, 100),
                (100, 125, 100),
                (-100, 125, 100),
                (-100, -25, 100),
            ],
        ),
    ]
    GL.glColor3f(1.0, 1.0, 1.0)
    uvs: list[tuple[float, float]] = [
        (0.0, 0.0),
        (0.0, 1.0),
        (1.0, 1.0),
        (1.0, 0.0),
    ]
    tex: int
    nx: float
    ny: float
    nz: float
    verts: list[tuple[int, int, int]]
    for tex, (nx, ny, nz), verts in walls:
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
        GL.glNormal3f(nx, ny, nz)
        GL.glBegin(GL.GL_QUADS)
        k: int
        v: tuple[int, int, int]
        for k, v in enumerate(verts):
            GL.glTexCoord2f(*uvs[k])
            GL.glVertex3f(*v)
        GL.glEnd()
    GL.glDisable(GL.GL_TEXTURE_2D)

    GL.glColor3f(1.0, 0.6, 0.6)
    GL.glNormal3f(0.0, -1.0, 0.0)
    GL.glBegin(GL.GL_QUADS)
    GL.glVertex3f(-100.0, 125.0, -100.0)
    GL.glVertex3f(-100.0, 125.0, 100.0)
    GL.glVertex3f(100.0, 125.0, 100.0)
    GL.glVertex3f(100.0, 125.0, -100.0)
    GL.glEnd()

    if draw_center:
        # The reflective object: replaced glutSolidTeapot with a sphere.
        GL.glColor3f(1.0, 0.6, 0.4)
        if state.use_env_map:
            mv: np.ndarray = np.array(
                GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX), dtype=np.float32
            ).reshape((4, 4))
            inv_mv: np.ndarray = np.identity(4, dtype=np.float32)
            inv_mv[:3, :3] = mv[:3, :3].T
            GL.glEnable(GL.GL_TEXTURE_CUBE_MAP)
            GL.glEnable(GL.GL_TEXTURE_GEN_S)
            GL.glEnable(GL.GL_TEXTURE_GEN_T)
            GL.glEnable(GL.GL_TEXTURE_GEN_R)
            GL.glMatrixMode(GL.GL_TEXTURE)
            GL.glPushMatrix()
            GL.glLoadMatrixf(inv_mv.T.flatten())
            GL.glMatrixMode(GL.GL_MODELVIEW)
        _primitives.draw_mesh(SPHERE_CENTER)
        if state.use_env_map:
            GL.glDisable(GL.GL_TEXTURE_CUBE_MAP)
            GL.glDisable(GL.GL_TEXTURE_GEN_S)
            GL.glDisable(GL.GL_TEXTURE_GEN_T)
            GL.glDisable(GL.GL_TEXTURE_GEN_R)
            GL.glMatrixMode(GL.GL_TEXTURE)
            GL.glPopMatrix()
            GL.glMatrixMode(GL.GL_MODELVIEW)

    GL.glColor3f(0.0, 1.0, 0.0)
    GL.glPushMatrix()
    GL.glRotatef(state.animation_angle, 0.0, 1.0, 0.0)
    GL.glTranslatef(-60.0, 0.0, 0.0)
    _primitives.draw_mesh(SPHERE)
    GL.glPopMatrix()
    GL.glColor3f(1.0, 1.0, 0.0)
    GL.glPushMatrix()
    GL.glRotatef(state.animation_angle, 0.0, 1.0, 0.0)
    GL.glRotatef(-90.0, 1.0, 0.0, 0.0)
    GL.glTranslatef(60.0, 0.0, -24.0)
    _primitives.draw_mesh(CONE, flat=True)
    GL.glPopMatrix()
    GL.glColor3f(1.0, 0.0, 1.0)
    GL.glPushMatrix()
    GL.glRotatef(state.animation_angle, 0.0, 1.0, 0.0)
    GL.glTranslatef(0.0, 0.0, 60.0)
    _primitives.draw_mesh(TORUS)
    GL.glPopMatrix()
    GL.glColor3f(0.0, 1.0, 1.0)
    GL.glPushMatrix()
    GL.glRotatef(state.animation_angle, 0.0, 1.0, 0.0)
    GL.glTranslatef(0.0, 0.0, -60.0)
    GL.glScalef(25.0, 25.0, 25.0)
    draw_solid_octahedron()
    GL.glPopMatrix()


CUBE_FACES: list[tuple[Constant, tuple[int, int, int, int, int, int]]] = [
    (GL.GL_TEXTURE_CUBE_MAP_POSITIVE_X, (1, 0, 0, 0, -1, 0)),
    (GL.GL_TEXTURE_CUBE_MAP_NEGATIVE_X, (-1, 0, 0, 0, -1, 0)),
    (GL.GL_TEXTURE_CUBE_MAP_POSITIVE_Y, (0, 1, 0, 0, 0, 1)),
    (GL.GL_TEXTURE_CUBE_MAP_NEGATIVE_Y, (0, -1, 0, 0, 0, -1)),
    (GL.GL_TEXTURE_CUBE_MAP_POSITIVE_Z, (0, 0, 1, 0, -1, 0)),
    (GL.GL_TEXTURE_CUBE_MAP_NEGATIVE_Z, (0, 0, -1, 0, -1, 0)),
]


def regenerate_env_map() -> None:
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(90.0, 1.0, 1.0, 125.0)
    GL.glViewport(0, 0, state.env_map_size, state.env_map_size)
    if state.use_fbo:
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, state.framebuffer_id)
    face: Constant
    cx: int
    cy: int
    cz: int
    ux: int
    uy: int
    uz: int
    for face, (cx, cy, cz, ux, uy, uz) in CUBE_FACES:
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GLU.gluLookAt(0.0, 0.0, 0.0, cx, cy, cz, ux, uy, uz)
        if state.use_fbo:
            GL.glFramebufferTexture2D(
                GL.GL_FRAMEBUFFER,
                GL.GL_COLOR_ATTACHMENT0,
                face,
                state.env_map_texture_id,
                0,
            )
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        draw_models(False)
        if not state.use_fbo:
            GL.glCopyTexImage2D(
                face,
                0,
                GL.GL_RGBA8,
                0,
                0,
                state.env_map_size,
                state.env_map_size,
                0,
            )
    if state.use_fbo:
        GL.glGenerateMipmap(GL.GL_TEXTURE_CUBE_MAP)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)


def render_scene() -> None:
    state.animation_angle = (state.animation_angle + 1.0) % 360.0
    if state.use_env_map:
        regenerate_env_map()

    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    if state.window_width > state.window_height:
        ar: float = float(state.window_width) / float(state.window_height)
        GL.glFrustum(
            -ar * camera_zoom,
            ar * camera_zoom,
            -camera_zoom,
            camera_zoom,
            2.0,
            1000.0,
        )
    else:
        ar = float(state.window_height) / float(state.window_width)
        GL.glFrustum(
            -camera_zoom,
            camera_zoom,
            -ar * camera_zoom,
            ar * camera_zoom,
            2.0,
            1000.0,
        )
    state.camera_pos[0] = max(-99.0, min(99.0, state.camera_pos[0]))
    state.camera_pos[1] = max(-20.0, min(120.0, state.camera_pos[1]))
    state.camera_pos[2] = max(-99.0, min(99.0, state.camera_pos[2]))
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GLU.gluLookAt(
        state.camera_pos[0],
        state.camera_pos[1],
        state.camera_pos[2],
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
    )
    GL.glViewport(0, 0, state.window_width, state.window_height)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    if state.show_env_map:
        # Show the 6 cube faces tiled on a 3x2 grid.
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, state.wall_texture_id[4])
        GL.glDisable(GL.GL_LIGHTING)
        GL.glColor4f(1.0, 1.0, 1.0, 1.0)
        offsets: list[tuple[float, float]] = [
            (0.25, 0.0),
            (-0.75, 0.0),
            (-0.25, -0.5),
            (-0.25, 0.5),
            (-0.25, 0.0),
            (0.75, 0.0),
        ]
        face: Constant
        ox: float
        oy: float
        for (face, _), (ox, oy) in zip(CUBE_FACES, offsets):
            texels: np.ndarray = GL.glGetTexImage(
                face, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE
            )
            GL.glTexImage2D(
                GL.GL_TEXTURE_2D,
                0,
                GL.GL_RGBA8,
                state.env_map_size,
                state.env_map_size,
                0,
                GL.GL_RGBA,
                GL.GL_UNSIGNED_BYTE,
                texels,
            )
            GL.glPushMatrix()
            GL.glTranslatef(ox, oy, 0.0)
            GL.glScalef(0.25, 0.25, 0.25)
            GL.glBegin(GL.GL_QUADS)
            GL.glTexCoord2f(0, 0)
            GL.glVertex2f(-1, -1)
            GL.glTexCoord2f(1, 0)
            GL.glVertex2f(1, -1)
            GL.glTexCoord2f(1, 1)
            GL.glVertex2f(1, 1)
            GL.glTexCoord2f(0, 1)
            GL.glVertex2f(-1, 1)
            GL.glEnd()
            GL.glPopMatrix()
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_MODELVIEW)
    else:
        draw_models(True)


def setup_textures() -> None:
    state.wall_texture_id = list(GL.glGenTextures(5))
    files: list[str] = ["WRHS.tga", "MAMS.tga", "WPI.tga", "Babson.tga"]
    i: int
    name: str
    for i, name in enumerate(files):
        img: np.ndarray = iio.imread(os.path.join(PWD, name))
        img = np.flipud(img)
        if img.ndim == 3 and img.shape[2] == 4:
            img = img[:, :, :3]
        img = np.ascontiguousarray(img, dtype=np.uint8)
        img_shape: tuple[int, ...] = img.shape[:2]
        GL.glBindTexture(GL.GL_TEXTURE_2D, state.wall_texture_id[i])
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_GENERATE_MIPMAP, 1)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGB8,
            img_shape[1],
            img_shape[0],
            0,
            GL.GL_RGB,
            GL.GL_UNSIGNED_BYTE,
            img,
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D,
            GL.GL_TEXTURE_MIN_FILTER,
            GL.GL_LINEAR_MIPMAP_LINEAR,
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE
        )

    GL.glBindTexture(GL.GL_TEXTURE_2D, state.wall_texture_id[4])
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_GENERATE_MIPMAP, 1)
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE
    )
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE
    )
    GL.glTexParameteri(
        GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR
    )
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)

    state.env_map_texture_id = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, state.env_map_texture_id)
    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_GENERATE_MIPMAP, 1)
    p: Constant
    for p in (GL.GL_TEXTURE_WRAP_S, GL.GL_TEXTURE_WRAP_T):
        GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, p, GL.GL_CLAMP_TO_EDGE)
    GL.glTexParameteri(
        GL.GL_TEXTURE_CUBE_MAP,
        GL.GL_TEXTURE_MIN_FILTER,
        GL.GL_LINEAR_MIPMAP_LINEAR,
    )
    GL.glTexParameteri(
        GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR
    )
    axis: Constant
    for axis in (GL.GL_S, GL.GL_T, GL.GL_R):
        GL.glTexGeni(axis, GL.GL_TEXTURE_GEN_MODE, GL.GL_REFLECTION_MAP)
    face: Constant
    for face, _ in CUBE_FACES:
        GL.glTexImage2D(
            face,
            0,
            GL.GL_RGBA8,
            state.env_map_size,
            state.env_map_size,
            0,
            GL.GL_RGBA,
            GL.GL_UNSIGNED_BYTE,
            None,
        )


def setup_rc() -> None:
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glDepthFunc(GL.GL_LEQUAL)
    GL.glShadeModel(GL.GL_SMOOTH)
    GL.glLightModeli(GL.GL_LIGHT_MODEL_LOCAL_VIEWER, 1)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, ambient_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, diffuse_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, specular_light)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, specular_light)
    GL.glMateriali(GL.GL_FRONT, GL.GL_SHININESS, 128)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glEnable(GL.GL_NORMALIZE)
    GL.glEnable(GL.GL_LIGHT0)

    state.max_cube_tex_size = min(
        GL.glGetIntegerv(GL.GL_MAX_CUBE_MAP_TEXTURE_SIZE),
        GL.glGetIntegerv(GL.GL_MAX_RENDERBUFFER_SIZE),
    )
    setup_textures()

    state.framebuffer_id = GL.glGenFramebuffers(1)
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, state.framebuffer_id)
    state.renderbuffer_id = GL.glGenRenderbuffers(1)
    GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, state.renderbuffer_id)
    GL.glRenderbufferStorage(
        GL.GL_RENDERBUFFER,
        GL.GL_DEPTH_COMPONENT32,
        state.env_map_size,
        state.env_map_size,
    )
    GL.glFramebufferRenderbuffer(
        GL.GL_FRAMEBUFFER,
        GL.GL_DEPTH_ATTACHMENT,
        GL.GL_RENDERBUFFER,
        state.renderbuffer_id,
    )
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)


def change_size(w: int, h: int) -> None:
    orig: int = state.env_map_size
    state.window_width = w
    state.window_height = h
    state.env_map_size = state.max_cube_tex_size if state.use_fbo else min(w, h)
    if state.env_map_size > state.max_cube_tex_size:
        state.env_map_size = state.max_cube_tex_size
    if state.env_map_size != orig and state.renderbuffer_id != 0:
        GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, state.renderbuffer_id)
        GL.glRenderbufferStorage(
            GL.GL_RENDERBUFFER,
            GL.GL_DEPTH_COMPONENT32,
            state.env_map_size,
            state.env_map_size,
        )
        GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, state.env_map_texture_id)
        face: Constant
        for face, _ in CUBE_FACES:
            GL.glTexImage2D(
                face,
                0,
                GL.GL_RGBA8,
                state.env_map_size,
                state.env_map_size,
                0,
                GL.GL_RGBA,
                GL.GL_UNSIGNED_BYTE,
                None,
            )


def on_framebuffer_size(_window: typing.Any, w: int, h: int) -> None:
    change_size(w, h)


def _nudge_cam(axis: int, d: float) -> None:
    state.camera_pos[axis] += d


def _set_use_env_map(v: bool) -> None:
    # The old E key cleared show_env_map. Preserve that coupling.
    state.use_env_map = v
    state.show_env_map = False


def _set_show_env_map(v: bool) -> None:
    # The old S key forced use_env_map on. Preserve that coupling.
    state.show_env_map = v
    state.use_env_map = True


def _set_use_fbo(v: bool) -> None:
    state.use_fbo = v
    change_size(state.window_width, state.window_height)


def imgui_menubar() -> None:
    # All controls live in the top menubar. Movement items run once per click
    # and show their key in the shortcut column; hold the key for continuous
    # motion.
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action(
            "Quit",
            "Esc",
            lambda: glfw.set_window_should_close(state.window, True),
        )
        imgui.end_menu()
    _common.draw_view_menu(state.window)
    if imgui.begin_menu("Options", True):
        env_map_item: tuple[bool, bool] = imgui.menu_item(
            "Env mapping", "", state.use_env_map, True
        )
        if env_map_item[0]:
            _set_use_env_map(env_map_item[1])
        show_env_map_item: tuple[bool, bool] = imgui.menu_item(
            "Show env map", "", state.show_env_map, True
        )
        if show_env_map_item[0]:
            _set_show_env_map(show_env_map_item[1])
        fbo_item: tuple[bool, bool] = imgui.menu_item(
            "Use FBO", "", state.use_fbo, True
        )
        if fbo_item[0]:
            _set_use_fbo(fbo_item[1])
        imgui.end_menu()
    if imgui.begin_menu("Controls", True):
        _common.menu_action("Camera +X", "X", lambda: _nudge_cam(0, 1.0))
        _common.menu_action("Camera -X", "Shift+X", lambda: _nudge_cam(0, -1.0))
        _common.menu_action("Camera +Y", "Y", lambda: _nudge_cam(1, 1.0))
        _common.menu_action("Camera -Y", "Shift+Y", lambda: _nudge_cam(1, -1.0))
        _common.menu_action("Camera +Z", "Z", lambda: _nudge_cam(2, 1.0))
        _common.menu_action("Camera -Z", "Shift+Z", lambda: _nudge_cam(2, -1.0))
        imgui.separator()
        _common.menu_action("Camera left", "Left", lambda: _nudge_cam(0, -1.0))
        _common.menu_action("Camera right", "Right", lambda: _nudge_cam(0, 1.0))
        _common.menu_action("Camera forward", "Up", lambda: _nudge_cam(2, -1.0))
        _common.menu_action("Camera back", "Down", lambda: _nudge_cam(2, 1.0))
        imgui.end_menu()
    imgui.end_main_menu_bar()


def on_key(
    window: typing.Any, key: int, _scancode: int, action: int, mods: int
) -> None:
    # Render-option toggles moved to the imgui panel; keys are navigation only.
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)
        return
    delta: float = -1.0 if (mods & glfw.MOD_SHIFT) else 1.0
    if key == glfw.KEY_X:
        state.camera_pos[0] += delta
    elif key == glfw.KEY_Y:
        state.camera_pos[1] += delta
    elif key == glfw.KEY_Z:
        state.camera_pos[2] += delta
    elif key == glfw.KEY_LEFT:
        state.camera_pos[0] -= 1.0
    elif key == glfw.KEY_RIGHT:
        state.camera_pos[0] += 1.0
    elif key == glfw.KEY_UP:
        state.camera_pos[2] -= 1.0
    elif key == glfw.KEY_DOWN:
        state.camera_pos[2] += 1.0


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    window: typing.Any = glfw.create_window(  # glfw window handle
        state.window_width,
        state.window_height,
        "FBO Environment Mapping Demo",
        None,
        None,
    )
    if not window:
        glfw.terminate()
        sys.exit(1)
    state.window = window
    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl: GlfwRenderer = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw key
    # callback that doesn't chain, so navigation/Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    print("FBO Environment Mapping Demo")
    print("  X/Y/Z + shift, arrows: move camera   Esc: quit")

    setup_rc()
    size: tuple[int, int] = glfw.get_framebuffer_size(window)
    change_size(size[0], size[1])

    frame_count: int = 0
    last_t: float = time.time()
    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        render_scene()
        imgui.new_frame()
        imgui_menubar()
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)
        frame_count += 1
        if frame_count == 100:
            now: float = time.time()
            fps: float = 100.0 / (now - last_t)
            label: str = "with FBOs" if state.use_fbo else "without FBOs"
            glfw.set_window_title(window, f"Draw scene {label} {fps:.1f} fps")
            last_t = now
            frame_count = 0
    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
