# cubemap.py
# Cube map applied to a sphere via texgen reflection mapping, with the
# same six images textured manually onto a skybox.
# OpenGL SuperBible, Chapter 9
# Python port of CubeMap.cpp by Richard S. Wright Jr.

import math
import os
import sys

import glfw
import imageio.v3 as iio
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU



PWD = os.path.dirname(os.path.abspath(__file__))
camera_x: float = 0.0
camera_y: float = 0.0
camera_z: float = 0.0
camera_yaw: float = 0.0

cube_faces = ["pos_x.tga", "neg_x.tga", "pos_y.tga", "neg_y.tga",
              "pos_z.tga", "neg_z.tga"]
cube_targets = [
    GL.GL_TEXTURE_CUBE_MAP_POSITIVE_X, GL.GL_TEXTURE_CUBE_MAP_NEGATIVE_X,
    GL.GL_TEXTURE_CUBE_MAP_POSITIVE_Y, GL.GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
    GL.GL_TEXTURE_CUBE_MAP_POSITIVE_Z, GL.GL_TEXTURE_CUBE_MAP_NEGATIVE_Z,
]


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


def draw_skybox() -> None:
    e = 15.0
    GL.glBegin(GL.GL_QUADS)
    # -X
    GL.glTexCoord3f(-1.0, -1.0, 1.0); GL.glVertex3f(-e, -e, e)
    GL.glTexCoord3f(-1.0, -1.0, -1.0); GL.glVertex3f(-e, -e, -e)
    GL.glTexCoord3f(-1.0, 1.0, -1.0); GL.glVertex3f(-e, e, -e)
    GL.glTexCoord3f(-1.0, 1.0, 1.0); GL.glVertex3f(-e, e, e)
    # +X
    GL.glTexCoord3f(1.0, -1.0, -1.0); GL.glVertex3f(e, -e, -e)
    GL.glTexCoord3f(1.0, -1.0, 1.0); GL.glVertex3f(e, -e, e)
    GL.glTexCoord3f(1.0, 1.0, 1.0); GL.glVertex3f(e, e, e)
    GL.glTexCoord3f(1.0, 1.0, -1.0); GL.glVertex3f(e, e, -e)
    # -Z
    GL.glTexCoord3f(-1.0, -1.0, -1.0); GL.glVertex3f(-e, -e, -e)
    GL.glTexCoord3f(1.0, -1.0, -1.0); GL.glVertex3f(e, -e, -e)
    GL.glTexCoord3f(1.0, 1.0, -1.0); GL.glVertex3f(e, e, -e)
    GL.glTexCoord3f(-1.0, 1.0, -1.0); GL.glVertex3f(-e, e, -e)
    # +Z
    GL.glTexCoord3f(1.0, -1.0, 1.0); GL.glVertex3f(e, -e, e)
    GL.glTexCoord3f(-1.0, -1.0, 1.0); GL.glVertex3f(-e, -e, e)
    GL.glTexCoord3f(-1.0, 1.0, 1.0); GL.glVertex3f(-e, e, e)
    GL.glTexCoord3f(1.0, 1.0, 1.0); GL.glVertex3f(e, e, e)
    # +Y
    GL.glTexCoord3f(-1.0, 1.0, 1.0); GL.glVertex3f(-e, e, e)
    GL.glTexCoord3f(-1.0, 1.0, -1.0); GL.glVertex3f(-e, e, -e)
    GL.glTexCoord3f(1.0, 1.0, -1.0); GL.glVertex3f(e, e, -e)
    GL.glTexCoord3f(1.0, 1.0, 1.0); GL.glVertex3f(e, e, e)
    # -Y
    GL.glTexCoord3f(-1.0, -1.0, -1.0); GL.glVertex3f(-e, -e, -e)
    GL.glTexCoord3f(-1.0, -1.0, 1.0); GL.glVertex3f(-e, -e, e)
    GL.glTexCoord3f(1.0, -1.0, 1.0); GL.glVertex3f(e, -e, e)
    GL.glTexCoord3f(1.0, -1.0, -1.0); GL.glVertex3f(e, -e, -e)
    GL.glEnd()


def setup_rc() -> None:
    GL.glCullFace(GL.GL_BACK)
    GL.glFrontFace(GL.GL_CCW)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_DEPTH_TEST)

    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_MAG_FILTER,
                       GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_MIN_FILTER,
                       GL.GL_LINEAR_MIPMAP_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_S,
                       GL.GL_CLAMP_TO_EDGE)
    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_T,
                       GL.GL_CLAMP_TO_EDGE)
    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_R,
                       GL.GL_CLAMP_TO_EDGE)

    for i, fname in enumerate(cube_faces):
        img = np.flipud(iio.imread(os.path.join(PWD, fname)))
        h, w = img.shape[:2]
        fmt = (GL.GL_RGBA if img.ndim == 3 and img.shape[2] == 4
               else GL.GL_RGB)
        img = np.ascontiguousarray(img, dtype=np.uint8)
        GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_GENERATE_MIPMAP,
                           GL.GL_TRUE)
        GL.glTexImage2D(cube_targets[i], 0, fmt, w, h, 0, fmt,
                        GL.GL_UNSIGNED_BYTE, img)

    GL.glTexGeni(GL.GL_S, GL.GL_TEXTURE_GEN_MODE, GL.GL_REFLECTION_MAP)
    GL.glTexGeni(GL.GL_T, GL.GL_TEXTURE_GEN_MODE, GL.GL_REFLECTION_MAP)
    GL.glTexGeni(GL.GL_R, GL.GL_TEXTURE_GEN_MODE, GL.GL_REFLECTION_MAP)

    GL.glEnable(GL.GL_TEXTURE_CUBE_MAP)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_DECAL)


def apply_camera_transform() -> None:
    GL.glRotatef(-math.degrees(camera_yaw), 0.0, 1.0, 0.0)
    GL.glTranslatef(-camera_x, -camera_y, -camera_z)


def render_scene() -> None:
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    GL.glPushMatrix()
    apply_camera_transform()

    # Skybox -- manual texture coordinates, no texgen
    GL.glDisable(GL.GL_TEXTURE_GEN_S)
    GL.glDisable(GL.GL_TEXTURE_GEN_T)
    GL.glDisable(GL.GL_TEXTURE_GEN_R)
    draw_skybox()

    # Sphere -- texgen reflects the cube map onto it
    GL.glEnable(GL.GL_TEXTURE_GEN_S)
    GL.glEnable(GL.GL_TEXTURE_GEN_T)
    GL.glEnable(GL.GL_TEXTURE_GEN_R)

    GL.glPushMatrix()
    GL.glTranslatef(0.0, 0.0, -3.0)

    GL.glMatrixMode(GL.GL_TEXTURE)
    GL.glPushMatrix()
    # Inverse-rotate the texture matrix so reflections track the camera
    GL.glRotatef(math.degrees(camera_yaw), 0.0, 1.0, 0.0)

    draw_solid_sphere(0.75, 41, 41)

    GL.glPopMatrix()
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glPopMatrix()
    GL.glPopMatrix()


def change_size(w: int, h: int) -> None:
    if h == 0:
        h = 1
    GL.glViewport(0, 0, w, h)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(35.0, float(w) / float(h), 1.0, 2000.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def handle_camera_keys(window) -> None:
    global camera_x, camera_z, camera_yaw
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera_x += 0.1 * math.sin(camera_yaw)
        camera_z -= 0.1 * math.cos(camera_yaw)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera_x -= 0.1 * math.sin(camera_yaw)
        camera_z += 0.1 * math.cos(camera_yaw)
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera_yaw += 0.1
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera_yaw -= 0.1


def on_key(window, key: int, _scancode: int, action: int, _mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
    window = glfw.create_window(800, 600, "OpenGL Cube Maps", None, None)
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
        handle_camera_keys(window)
        render_scene()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
