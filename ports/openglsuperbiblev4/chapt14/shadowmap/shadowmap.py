# shadowmap.py
# Two-pass depth-texture shadow mapping. First the scene is rendered
# from the light's POV into a depth texture; then the scene is
# rendered normally with the depth texture used as a shadow lookup
# via GL_COMPARE_R_TO_TEXTURE.
#
# C++ used a right-click GLUT menu for shadow toggle / control mode;
# replaced here with key bindings (S = toggle shadows, M = show
# shadow map, C = toggle camera/light control).
#
# Note: the C++ original drew glutSolidTorus and glutSolidOctahedron;
# this port substitutes a generic torus and a simple octahedron.
#
# OpenGL SuperBible, Chapter 14
# Python port of shadowmap.cpp by Benjamin Lipchak

import math
import os
import sys

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU

if os.getenv("XDG_SESSION_TYPE") == "wayland" and not os.getenv(
    "PYOPENGL_PLATFORM"
):
    os.environ["PYOPENGL_PLATFORM"] = "x11"


control_camera: bool = True
no_shadows: bool = False
show_shadow_map: bool = False
factor: float = 4.0

window_width: int = 1024
window_height: int = 512
shadow_width: int = 1024
shadow_height: int = 512
shadow_texture_id: int = 0

ambient_light = (0.2, 0.2, 0.2, 1.0)
diffuse_light = (0.7, 0.7, 0.7, 1.0)

light_pos = [100.0, 300.0, 100.0, 1.0]
camera_pos = [100.0, 150.0, 200.0, 1.0]
camera_zoom: float = 0.3
texture_matrix: np.ndarray = np.eye(4, dtype=np.float32).flatten()


def draw_solid_cube(size: float) -> None:
    s = size / 2.0
    GL.glBegin(GL.GL_QUADS)
    for nx, ny, nz, vs in [
        (0, 0, 1, [(-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s)]),
        (0, 0, -1, [(s, -s, -s), (-s, -s, -s), (-s, s, -s), (s, s, -s)]),
        (1, 0, 0, [(s, -s, s), (s, -s, -s), (s, s, -s), (s, s, s)]),
        (-1, 0, 0, [(-s, -s, -s), (-s, -s, s), (-s, s, s), (-s, s, -s)]),
        (0, 1, 0, [(-s, s, s), (s, s, s), (s, s, -s), (-s, s, -s)]),
        (0, -1, 0, [(-s, -s, -s), (s, -s, -s), (s, -s, s), (-s, -s, s)]),
    ]:
        GL.glNormal3f(nx, ny, nz)
        for v in vs:
            GL.glVertex3f(*v)
    GL.glEnd()


def draw_solid_sphere(radius: float, slices: int, stacks: int) -> None:
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        s0, c0 = math.sin(lat0), math.cos(lat0)
        s1, c1 = math.sin(lat1), math.cos(lat1)
        GL.glBegin(GL.GL_QUAD_STRIP)
        for j in range(slices + 1):
            lng = 2.0 * math.pi * float(j) / slices
            cl, sl = math.cos(lng), math.sin(lng)
            GL.glNormal3f(cl * c0, sl * c0, s0)
            GL.glVertex3f(radius * cl * c0, radius * sl * c0, radius * s0)
            GL.glNormal3f(cl * c1, sl * c1, s1)
            GL.glVertex3f(radius * cl * c1, radius * sl * c1, radius * s1)
        GL.glEnd()


def draw_solid_cone(base: float, height: float, slices: int) -> None:
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glNormal3f(0.0, 0.0, 1.0)
    GL.glVertex3f(0.0, 0.0, height)
    for i in range(slices + 1):
        a = 2.0 * math.pi * float(i) / slices
        GL.glVertex3f(math.cos(a) * base, math.sin(a) * base, 0.0)
    GL.glEnd()


def draw_torus(major: float, minor: float, n_major: int, n_minor: int) -> None:
    major_step = 2.0 * math.pi / n_major
    minor_step = 2.0 * math.pi / n_minor
    for i in range(n_major):
        a0, a1 = i * major_step, (i + 1) * major_step
        x0, y0 = math.cos(a0), math.sin(a0)
        x1, y1 = math.cos(a1), math.sin(a1)
        GL.glBegin(GL.GL_TRIANGLE_STRIP)
        for j in range(n_minor + 1):
            b = j * minor_step
            cb, sb = math.cos(b), math.sin(b)
            r = minor * cb + major
            z = minor * sb
            GL.glNormal3f(x0 * cb, y0 * cb, sb)
            GL.glVertex3f(x0 * r, y0 * r, z)
            GL.glNormal3f(x1 * cb, y1 * cb, sb)
            GL.glVertex3f(x1 * r, y1 * r, z)
        GL.glEnd()


def draw_solid_octahedron() -> None:
    """A unit octahedron -- 8 triangle faces, vertices at ±1 on each axis."""
    verts = [
        (1.0, 0.0, 0.0), (-1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0), (0.0, -1.0, 0.0),
        (0.0, 0.0, 1.0), (0.0, 0.0, -1.0),
    ]
    faces = [
        (0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
        (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5),
    ]
    GL.glBegin(GL.GL_TRIANGLES)
    for f in faces:
        for i in f:
            v = verts[i]
            GL.glNormal3f(*v)
            GL.glVertex3f(*v)
    GL.glEnd()


def draw_models(draw_base_plane: bool) -> None:
    if draw_base_plane:
        GL.glColor3f(0.0, 0.0, 0.90)
        GL.glNormal3f(0.0, 1.0, 0.0)
        GL.glBegin(GL.GL_QUADS)
        GL.glVertex3f(-100.0, -25.0, -100.0)
        GL.glVertex3f(-100.0, -25.0, 100.0)
        GL.glVertex3f(100.0, -25.0, 100.0)
        GL.glVertex3f(100.0, -25.0, -100.0)
        GL.glEnd()

    GL.glColor3f(1.0, 0.0, 0.0)
    draw_solid_cube(48.0)

    GL.glColor3f(0.0, 1.0, 0.0)
    GL.glPushMatrix()
    GL.glTranslatef(-60.0, 0.0, 0.0)
    draw_solid_sphere(25.0, 50, 50)
    GL.glPopMatrix()

    GL.glColor3f(1.0, 1.0, 0.0)
    GL.glPushMatrix()
    GL.glRotatef(-90.0, 1.0, 0.0, 0.0)
    GL.glTranslatef(60.0, 0.0, -24.0)
    draw_solid_cone(25.0, 50.0, 50)
    GL.glPopMatrix()

    GL.glColor3f(1.0, 0.0, 1.0)
    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, 60.0)
    draw_torus(16.0, 8.0, 50, 50)
    GL.glPopMatrix()

    GL.glColor3f(0.0, 1.0, 1.0)
    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, -60.0)
    GL.glScalef(25.0, 25.0, 25.0)
    draw_solid_octahedron()
    GL.glPopMatrix()


def regenerate_shadow_map() -> None:
    global texture_matrix

    scene_bounding_radius = 95.0
    light_to_scene = math.sqrt(
        light_pos[0] ** 2 + light_pos[1] ** 2 + light_pos[2] ** 2
    )
    near = light_to_scene - scene_bounding_radius
    fov = math.degrees(2.0 * math.atan(scene_bounding_radius / light_to_scene))

    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(fov, 1.0, near, near + 2.0 * scene_bounding_radius)
    light_projection = np.array(
        GL.glGetFloatv(GL.GL_PROJECTION_MATRIX), dtype=np.float32
    )

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GLU.gluLookAt(light_pos[0], light_pos[1], light_pos[2],
                  0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    light_modelview = np.array(
        GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX), dtype=np.float32
    )
    GL.glViewport(0, 0, shadow_width, shadow_height)
    GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

    GL.glShadeModel(GL.GL_FLAT)
    GL.glDisable(GL.GL_LIGHTING)
    GL.glDisable(GL.GL_COLOR_MATERIAL)
    GL.glDisable(GL.GL_NORMALIZE)
    GL.glColorMask(False, False, False, False)
    GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)

    draw_models(False)

    GL.glCopyTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_DEPTH_COMPONENT,
                        0, 0, shadow_width, shadow_height, 0)

    GL.glShadeModel(GL.GL_SMOOTH)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glEnable(GL.GL_NORMALIZE)
    GL.glColorMask(True, True, True, True)
    GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)

    bias_matrix = np.array([
        0.5, 0.0, 0.0, 0.0,
        0.0, 0.5, 0.0, 0.0,
        0.0, 0.0, 0.5, 0.0,
        0.5, 0.5, 0.5, 1.0,
    ], dtype=np.float32).reshape(4, 4)
    proj = light_projection.reshape(4, 4)
    mv = light_modelview.reshape(4, 4)
    # Column-major matmul: (bias * proj * mv) -- transposed for GL plane eqs
    m = (bias_matrix @ proj @ mv).T
    texture_matrix = m.flatten().astype(np.float32)


def render_scene() -> None:
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    if window_width > window_height:
        ar = float(window_width) / float(window_height)
        GL.glFrustum(-ar * camera_zoom, ar * camera_zoom,
                     -camera_zoom, camera_zoom, 1.0, 1000.0)
    else:
        ar = float(window_height) / float(window_width)
        GL.glFrustum(-camera_zoom, camera_zoom,
                     -ar * camera_zoom, ar * camera_zoom, 1.0, 1000.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GLU.gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
                  0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    GL.glViewport(0, 0, window_width, window_height)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    if show_shadow_map:
        GL.glMatrixMode(GL.GL_PROJECTION); GL.glLoadIdentity()
        GL.glMatrixMode(GL.GL_MODELVIEW);  GL.glLoadIdentity()
        GL.glMatrixMode(GL.GL_TEXTURE)
        GL.glPushMatrix(); GL.glLoadIdentity()
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glDisable(GL.GL_LIGHTING)
        GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_REPLACE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_COMPARE_MODE,
                           GL.GL_NONE)
        sw = (float(shadow_width) / window_width) * 2.0 - 1.0
        sh = (float(shadow_height) / window_height) * 2.0 - 1.0
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 0.0); GL.glVertex2f(-1.0, -1.0)
        GL.glTexCoord2f(1.0, 0.0); GL.glVertex2f(sw, -1.0)
        GL.glTexCoord2f(1.0, 1.0); GL.glVertex2f(sw, sh)
        GL.glTexCoord2f(0.0, 1.0); GL.glVertex2f(-1.0, sh)
        GL.glEnd()
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_MODELVIEW)
    elif no_shadows:
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, ambient_light)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, diffuse_light)
        draw_models(True)
    else:
        # Ambient pass
        low_amb = (0.1, 0.1, 0.1, 1.0)
        low_diff = (0.35, 0.35, 0.35, 1.0)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, low_amb)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, low_diff)
        draw_models(True)
        GL.glAlphaFunc(GL.GL_GREATER, 0.9)
        GL.glEnable(GL.GL_ALPHA_TEST)

        # Lit pass with shadow comparison
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, ambient_light)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, diffuse_light)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_COMPARE_MODE,
                           GL.GL_COMPARE_R_TO_TEXTURE)
        GL.glEnable(GL.GL_TEXTURE_GEN_S)
        GL.glEnable(GL.GL_TEXTURE_GEN_T)
        GL.glEnable(GL.GL_TEXTURE_GEN_R)
        GL.glEnable(GL.GL_TEXTURE_GEN_Q)
        GL.glTexGenfv(GL.GL_S, GL.GL_EYE_PLANE, texture_matrix[0:4])
        GL.glTexGenfv(GL.GL_T, GL.GL_EYE_PLANE, texture_matrix[4:8])
        GL.glTexGenfv(GL.GL_R, GL.GL_EYE_PLANE, texture_matrix[8:12])
        GL.glTexGenfv(GL.GL_Q, GL.GL_EYE_PLANE, texture_matrix[12:16])

        draw_models(True)

        GL.glDisable(GL.GL_ALPHA_TEST)
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glDisable(GL.GL_TEXTURE_GEN_S)
        GL.glDisable(GL.GL_TEXTURE_GEN_T)
        GL.glDisable(GL.GL_TEXTURE_GEN_R)
        GL.glDisable(GL.GL_TEXTURE_GEN_Q)


def setup_rc() -> None:
    global shadow_texture_id
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glDepthFunc(GL.GL_LEQUAL)
    GL.glPolygonOffset(factor, 0.0)
    GL.glShadeModel(GL.GL_SMOOTH)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_COLOR_MATERIAL)
    GL.glEnable(GL.GL_NORMALIZE)
    GL.glEnable(GL.GL_LIGHT0)

    shadow_texture_id = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, shadow_texture_id)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S,
                       GL.GL_CLAMP_TO_EDGE)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T,
                       GL.GL_CLAMP_TO_EDGE)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_DEPTH_TEXTURE_MODE,
                       GL.GL_INTENSITY)
    GL.glTexGeni(GL.GL_S, GL.GL_TEXTURE_GEN_MODE, GL.GL_EYE_LINEAR)
    GL.glTexGeni(GL.GL_T, GL.GL_TEXTURE_GEN_MODE, GL.GL_EYE_LINEAR)
    GL.glTexGeni(GL.GL_R, GL.GL_TEXTURE_GEN_MODE, GL.GL_EYE_LINEAR)
    GL.glTexGeni(GL.GL_Q, GL.GL_TEXTURE_GEN_MODE, GL.GL_EYE_LINEAR)

    regenerate_shadow_map()


def change_size(w: int, h: int) -> None:
    global window_width, window_height
    window_width, window_height = w, h


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def on_key(window, key: int, _scancode: int, action: int, mods: int) -> None:
    global no_shadows, show_shadow_map, control_camera, factor
    if action != glfw.PRESS:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)
        return

    pos = camera_pos if control_camera else light_pos
    delta = -5.0 if (mods & glfw.MOD_SHIFT) else 5.0

    if key == glfw.KEY_X:
        pos[0] += delta
    elif key == glfw.KEY_Y:
        pos[1] += delta
    elif key == glfw.KEY_Z:
        pos[2] += delta
    elif key == glfw.KEY_F:
        factor += -1.0 if (mods & glfw.MOD_SHIFT) else 1.0
        GL.glPolygonOffset(factor, 0.0)
        regenerate_shadow_map()
    elif key == glfw.KEY_S:
        no_shadows = not no_shadows
        show_shadow_map = False
    elif key == glfw.KEY_M:
        show_shadow_map = not show_shadow_map
        no_shadows = False
    elif key == glfw.KEY_C:
        control_camera = not control_camera

    if not control_camera:
        regenerate_shadow_map()


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window = glfw.create_window(window_width, window_height,
                                "Shadow Mapping Demo", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    setup_rc()
    w, h = glfw.get_framebuffer_size(window)
    change_size(w, h)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        render_scene()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
