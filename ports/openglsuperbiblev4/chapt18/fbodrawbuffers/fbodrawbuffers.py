# fbodrawbuffers.py
# Multiple render targets via FBO + glDrawBuffers. Pass 1 renders the
# scene into render-texture #0. Pass 2 reads that texture and writes
# four post-processed copies (blur, laplacian, grayscale, color
# invert) into render-textures #1..#4 — either in one draw with a
# multi-output shader, or in four separate draws with single-output
# shaders. Pass 3 tiles those four results back to the window.
#
# Keys: arrows or X/Y/Z + shift to move camera; Esc to quit. Draw
# buffers (MRT) and post-processing toggles live on an imgui panel.
#
# OpenGL SuperBible, Chapter 18
# Python port of fbodrawbuffers.cpp by Benjamin Lipchak

import os
import sys

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GL.shaders as shaders_mod
import OpenGL.GLU as GLU
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PWD)))
import _common  # noqa: E402
import _primitives  # noqa: E402

_window = None  # set in main(); used by the Quit control button
window_width: int = 512
window_height: int = 512
fbo_width: int = 512
fbo_height: int = 512

use_draw_buffers: bool = True
do_processing: bool = True

TOTAL_SHADERS = 6
shader_names = [
    "multirender",
    "combine",
    "blur",
    "laplacian",
    "grayscale",
    "colorinvert",
]
f_shader = [0] * TOTAL_SHADERS
prog_obj = [0] * TOTAL_SHADERS

wall_texture_id = [0, 0, 0, 0]
render_texture_id = [0, 0, 0, 0, 0]
framebuffer_id = [0, 0]
renderbuffer_id: int = 0
max_tex_size: int = 0
max_draw_buffers: int = 4
tex_coord_offsets = np.zeros(18, dtype=np.float32)

ambient_light = [0.4, 0.4, 0.4, 1.0]
diffuse_light = [0.6, 0.6, 0.6, 1.0]
specular_light = [1.0, 1.0, 1.0, 1.0]
light_pos = [0.0, 125.0, 0.0, 1.0]
camera_pos = [50.0, 50.0, 100.0, 1.0]
camera_zoom: float = 1.5
animation_angle: float = 0.0


SPHERE_CENTER = _primitives.build_sphere(20.0, 32, 32)
SPHERE = _primitives.build_sphere(25.0, 50, 50)
CONE = _primitives.build_cone(25.0, 50.0, 50)
TORUS = _primitives.build_torus(16.0, 8.0, 50, 50)


def draw_solid_octahedron() -> None:
    verts = [
        (1, 0, 0),
        (-1, 0, 0),
        (0, 1, 0),
        (0, -1, 0),
        (0, 0, 1),
        (0, 0, -1),
    ]
    faces = [
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
    for i, j, k in faces:
        a, b, c = verts[i], verts[j], verts[k]
        nx = (b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1])
        ny = (b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2])
        nz = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        GL.glNormal3f(nx, ny, nz)
        GL.glVertex3f(*a)
        GL.glVertex3f(*b)
        GL.glVertex3f(*c)
    GL.glEnd()


def draw_models(_draw_teapot: bool) -> None:
    GL.glColor3f(0.0, 0.0, 0.90)
    GL.glNormal3f(0.0, 1.0, 0.0)
    GL.glBegin(GL.GL_QUADS)
    GL.glVertex3f(-100.0, -25.0, -100.0)
    GL.glVertex3f(-100.0, -25.0, 100.0)
    GL.glVertex3f(100.0, -25.0, 100.0)
    GL.glVertex3f(100.0, -25.0, -100.0)
    GL.glEnd()

    GL.glEnable(GL.GL_TEXTURE_2D)
    walls = [
        (
            wall_texture_id[0],
            (1.0, 0.0, 0.0),
            [
                (-100, -25, 100),
                (-100, 125, 100),
                (-100, 125, -100),
                (-100, -25, -100),
            ],
        ),
        (
            wall_texture_id[2],
            (-1.0, 0.0, 0.0),
            [
                (100, -25, -100),
                (100, 125, -100),
                (100, 125, 100),
                (100, -25, 100),
            ],
        ),
        (
            wall_texture_id[1],
            (0.0, 0.0, 1.0),
            [
                (-100, -25, -100),
                (-100, 125, -100),
                (100, 125, -100),
                (100, -25, -100),
            ],
        ),
        (
            wall_texture_id[3],
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
    uvs = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]
    for tex, (nx, ny, nz), verts in walls:
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
        GL.glNormal3f(nx, ny, nz)
        GL.glBegin(GL.GL_QUADS)
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

    # C++ used glutSolidTeapot here; substituting another sphere.
    GL.glColor3f(1.0, 0.6, 0.4)
    GL.glPushMatrix()
    _primitives.draw_mesh(SPHERE_CENTER)
    GL.glPopMatrix()

    GL.glColor3f(0.0, 1.0, 0.0)
    GL.glPushMatrix()
    GL.glRotatef(animation_angle, 0.0, 1.0, 0.0)
    GL.glTranslatef(-60.0, 0.0, 0.0)
    _primitives.draw_mesh(SPHERE)
    GL.glPopMatrix()
    GL.glColor3f(1.0, 1.0, 0.0)
    GL.glPushMatrix()
    GL.glRotatef(animation_angle, 0.0, 1.0, 0.0)
    GL.glRotatef(-90.0, 1.0, 0.0, 0.0)
    GL.glTranslatef(60.0, 0.0, -24.0)
    _primitives.draw_mesh(CONE, flat=True)
    GL.glPopMatrix()
    GL.glColor3f(1.0, 0.0, 1.0)
    GL.glPushMatrix()
    GL.glRotatef(animation_angle, 0.0, 1.0, 0.0)
    GL.glTranslatef(0.0, 0.0, 60.0)
    _primitives.draw_mesh(TORUS)
    GL.glPopMatrix()
    GL.glColor3f(0.0, 1.0, 1.0)
    GL.glPushMatrix()
    GL.glRotatef(animation_angle, 0.0, 1.0, 0.0)
    GL.glTranslatef(0.0, 0.0, -60.0)
    GL.glScalef(25.0, 25.0, 25.0)
    draw_solid_octahedron()
    GL.glPopMatrix()


def prepare_shader(n: int) -> None:
    fname = os.path.join(PWD, "shaders", f"{shader_names[n]}.fs")
    with open(fname) as f:
        fs_src = f.read()
    f_shader[n] = shaders_mod.compileShader(fs_src, GL.GL_FRAGMENT_SHADER)
    prog_obj[n] = GL.glCreateProgram()
    GL.glAttachShader(prog_obj[n], f_shader[n])
    GL.glLinkProgram(prog_obj[n])
    if not GL.glGetProgramiv(prog_obj[n], GL.GL_LINK_STATUS):
        info = GL.glGetProgramInfoLog(prog_obj[n])
        sys.stderr.write(f"Program {n} link error: {info}\n")
        sys.exit(1)


def setup_textures() -> None:
    global wall_texture_id, render_texture_id
    files = ["WRHS.tga", "MAMS.tga", "WPI.tga", "Babson.tga"]
    wall_texture_id = list(GL.glGenTextures(4))
    for i, name in enumerate(files):
        img = iio.imread(os.path.join(PWD, name))
        img = np.flipud(img)
        if img.ndim == 3 and img.shape[2] == 4:
            img = img[:, :, :3]
        img = np.ascontiguousarray(img, dtype=np.uint8)
        h, w = img.shape[:2]
        GL.glBindTexture(GL.GL_TEXTURE_2D, wall_texture_id[i])
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_GENERATE_MIPMAP, 1)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGB8,
            w,
            h,
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

    render_texture_id = list(GL.glGenTextures(5))
    for i in range(max_draw_buffers + 1):
        if i > 0:
            GL.glActiveTexture(GL.GL_TEXTURE0 + i - 1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, render_texture_id[i])
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR
        )
        if i == 0:
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D,
                GL.GL_TEXTURE_MIN_FILTER,
                GL.GL_LINEAR_MIPMAP_NEAREST,
            )
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGBA8,
            fbo_width,
            fbo_height,
            0,
            GL.GL_RGBA,
            GL.GL_UNSIGNED_BYTE,
            None,
        )
    GL.glActiveTexture(GL.GL_TEXTURE0)


def render_scene() -> None:
    global animation_angle
    animation_angle = (animation_angle + 1.0) % 360.0

    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    if window_width > window_height:
        ar = float(window_width) / float(window_height)
        GL.glFrustum(
            -ar * camera_zoom,
            ar * camera_zoom,
            -camera_zoom,
            camera_zoom,
            2.0,
            1000.0,
        )
    else:
        ar = float(window_height) / float(window_width)
        GL.glFrustum(
            -camera_zoom,
            camera_zoom,
            -ar * camera_zoom,
            ar * camera_zoom,
            2.0,
            1000.0,
        )
    camera_pos[0] = max(-99.0, min(99.0, camera_pos[0]))
    camera_pos[1] = max(-20.0, min(120.0, camera_pos[1]))
    camera_pos[2] = max(-99.0, min(99.0, camera_pos[2]))
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GLU.gluLookAt(
        camera_pos[0],
        camera_pos[1],
        camera_pos[2],
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
    )

    if do_processing:
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, framebuffer_id[0])
        GL.glViewport(0, 0, fbo_width, fbo_height)
    else:
        GL.glViewport(0, 0, window_width, window_height)

    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    draw_models(True)

    if not do_processing:
        return

    # Pass 2: post-process the rendered scene into 4 textures
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, framebuffer_id[1])
    GL.glBindTexture(GL.GL_TEXTURE_2D, render_texture_id[0])
    GL.glGenerateMipmap(GL.GL_TEXTURE_2D)

    if use_draw_buffers:
        GL.glDrawBuffers(
            max_draw_buffers,
            [GL.GL_COLOR_ATTACHMENT0 + i for i in range(max_draw_buffers)],
        )
        loops = [0]
    else:
        loops = list(range(max_draw_buffers))

    for loop in loops:
        if use_draw_buffers:
            shader_num = 0
        else:
            shader_num = loop + 2
            GL.glDrawBuffer(GL.GL_COLOR_ATTACHMENT0 + loop)

        GL.glUseProgram(prog_obj[shader_num])
        loc = GL.glGetUniformLocation(prog_obj[shader_num], "sampler0")
        if loc != -1:
            GL.glUniform1i(loc, 0)
        loc = GL.glGetUniformLocation(prog_obj[shader_num], "tc_offset")
        if loc != -1:
            GL.glUniform2fv(loc, 9, tex_coord_offsets)

        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GL.glBegin(GL.GL_QUADS)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 0.0, 0.0)
        GL.glVertex2f(-1.0, -1.0)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 0.0, 1.0)
        GL.glVertex2f(-1.0, 1.0)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 1.0, 1.0)
        GL.glVertex2f(1.0, 1.0)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 1.0, 0.0)
        GL.glVertex2f(1.0, -1.0)
        GL.glEnd()

    # Pass 3: combine 4 textures back into a tiled image on screen
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
    GL.glViewport(0, 0, window_width, window_height)
    GL.glUseProgram(prog_obj[1])
    for i in range(4):
        loc = GL.glGetUniformLocation(prog_obj[1], f"sampler{i}")
        if loc != -1:
            GL.glUniform1i(loc, i)
    GL.glBindTexture(GL.GL_TEXTURE_2D, render_texture_id[1])
    GL.glBegin(GL.GL_QUADS)
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 0.0, 0.0)
    GL.glVertex2f(-1.0, -1.0)
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 0.0, 1.0)
    GL.glVertex2f(-1.0, 1.0)
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 1.0, 1.0)
    GL.glVertex2f(1.0, 1.0)
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 1.0, 0.0)
    GL.glVertex2f(1.0, -1.0)
    GL.glEnd()
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glUseProgram(0)


def setup_rc() -> None:
    global max_tex_size, max_draw_buffers, renderbuffer_id
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

    max_draw_buffers = min(
        GL.glGetIntegerv(GL.GL_MAX_DRAW_BUFFERS),
        GL.glGetIntegerv(GL.GL_MAX_COLOR_ATTACHMENTS),
        GL.glGetIntegerv(GL.GL_MAX_TEXTURE_IMAGE_UNITS) - 1,
        4,
    )
    max_tex_size = min(
        GL.glGetIntegerv(GL.GL_MAX_TEXTURE_SIZE),
        GL.glGetIntegerv(GL.GL_MAX_RENDERBUFFER_SIZE),
    )
    setup_textures()
    for i in range(TOTAL_SHADERS):
        prepare_shader(i)
    renderbuffer_id = GL.glGenRenderbuffers(1)
    GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, renderbuffer_id)
    GL.glRenderbufferStorage(
        GL.GL_RENDERBUFFER, GL.GL_DEPTH_COMPONENT32, fbo_width, fbo_height
    )
    fbs = list(GL.glGenFramebuffers(2))
    framebuffer_id[0], framebuffer_id[1] = fbs
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, framebuffer_id[0])
    GL.glFramebufferRenderbuffer(
        GL.GL_FRAMEBUFFER,
        GL.GL_DEPTH_ATTACHMENT,
        GL.GL_RENDERBUFFER,
        renderbuffer_id,
    )
    GL.glFramebufferTexture2D(
        GL.GL_FRAMEBUFFER,
        GL.GL_COLOR_ATTACHMENT0,
        GL.GL_TEXTURE_2D,
        render_texture_id[0],
        0,
    )
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, framebuffer_id[1])
    for i in range(max_draw_buffers):
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_COLOR_ATTACHMENT0 + i,
            GL.GL_TEXTURE_2D,
            render_texture_id[i + 1],
            0,
        )
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)


def change_size(w: int, h: int) -> None:
    global window_width, window_height, fbo_width, fbo_height
    orig = (fbo_width, fbo_height)
    window_width = fbo_width = w
    window_height = fbo_height = h
    if fbo_width > max_tex_size:
        fbo_width = max_tex_size
    if fbo_height > max_tex_size:
        fbo_height = max_tex_size
    if (fbo_width, fbo_height) != orig and renderbuffer_id != 0:
        GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, renderbuffer_id)
        GL.glRenderbufferStorage(
            GL.GL_RENDERBUFFER, GL.GL_DEPTH_COMPONENT32, fbo_width, fbo_height
        )
        for i in range(max_draw_buffers + 1):
            GL.glBindTexture(GL.GL_TEXTURE_2D, render_texture_id[i])
            GL.glTexImage2D(
                GL.GL_TEXTURE_2D,
                0,
                GL.GL_RGBA8,
                fbo_width,
                fbo_height,
                0,
                GL.GL_RGBA,
                GL.GL_UNSIGNED_BYTE,
                None,
            )
        x_inc = 1.0 / fbo_width
        y_inc = 1.0 / fbo_height
        for i in range(3):
            for j in range(3):
                tex_coord_offsets[(((i * 3) + j) * 2) + 0] = -x_inc + i * x_inc
                tex_coord_offsets[(((i * 3) + j) * 2) + 1] = -y_inc + j * y_inc


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def _nudge_cam(axis: int, d: float) -> None:
    camera_pos[axis] += d


def _set_use_draw_buffers(v: bool) -> None:
    global use_draw_buffers
    use_draw_buffers = v


def _set_do_processing(v: bool) -> None:
    global do_processing
    do_processing = v


def imgui_menubar() -> None:
    # All controls live in the top menubar. Movement items run once per click
    # and show their key in the shortcut column; hold the key for continuous
    # motion.
    if not imgui.begin_main_menu_bar():
        return
    if imgui.begin_menu("File", True):
        _common.menu_action(
            "Quit", "Esc", lambda: glfw.set_window_should_close(_window, True)
        )
        imgui.end_menu()
    if imgui.begin_menu("Options", True):
        clicked, v = imgui.menu_item(
            "Use draw buffers (MRT)", "", use_draw_buffers, True
        )
        if clicked:
            _set_use_draw_buffers(v)
        clicked, v = imgui.menu_item("Post-processing", "", do_processing, True)
        if clicked:
            _set_do_processing(v)
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


def on_key(window, key: int, _scancode: int, action: int, mods: int) -> None:
    # Render-option toggles moved to the imgui panel; keys are navigation only.
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)
        return
    delta = -1.0 if (mods & glfw.MOD_SHIFT) else 1.0
    if key == glfw.KEY_X:
        camera_pos[0] += delta
    elif key == glfw.KEY_Y:
        camera_pos[1] += delta
    elif key == glfw.KEY_Z:
        camera_pos[2] += delta
    elif key == glfw.KEY_LEFT:
        camera_pos[0] -= 1.0
    elif key == glfw.KEY_RIGHT:
        camera_pos[0] += 1.0
    elif key == glfw.KEY_UP:
        camera_pos[2] -= 1.0
    elif key == glfw.KEY_DOWN:
        camera_pos[2] += 1.0


def main() -> None:
    global _window
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    window = glfw.create_window(
        window_width, window_height, "FBO Draw Buffers Demo", None, None
    )
    if not window:
        glfw.terminate()
        sys.exit(1)
    _window = window
    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    imgui.create_context()
    impl = GlfwRenderer(window)
    # Set our key callback AFTER GlfwRenderer -- it installs its own glfw key
    # callback that doesn't chain, so navigation/Esc must be registered last.
    glfw.set_key_callback(window, on_key)

    print("FBO Draw Buffers Demo")
    print("  X/Y/Z + shift, arrows: move camera   Esc: quit")

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)
    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        render_scene()
        # render_scene's no-processing path returns early (still on the
        # default framebuffer); the processing path ends with Pass 3
        # bound to framebuffer 0. Rebind defensively so imgui always
        # draws to the window.
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        imgui.new_frame()
        imgui_menubar()
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)
    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
