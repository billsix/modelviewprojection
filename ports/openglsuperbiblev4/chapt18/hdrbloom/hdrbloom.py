# hdrbloom.py
# HDR + bloom: render an HDR ball into a 16F texture (and a "bright
# pass" companion); generate mips of the bright pass; gaussian-blur
# four of those mip levels into separate small RGBA8 textures; in the
# final pass the COMBINE shader sums the original HDR scene, the four
# blurred levels, and a one-frame-old afterglow PBO.
#
# Keys: 1..8 cycle stop points (orig/bright/pre-blur/post-blur/just-
# bloom/no-afterglow/just-afterglow/full); arrows rotate light /
# change tess; L/Shift+L change bloom limit; P pause spin; X/Y/Z +
# shift to pan; Esc quits.
#
# OpenGL SuperBible, Chapter 18
# Python port of hdrbloom.cpp by Benjamin Lipchak

import math
import os
import sys

import glfw
import numpy as np
import OpenGL.GL as GL
import OpenGL.GL.shaders as shaders_mod
import OpenGL.GLU as GLU



PWD = os.path.dirname(os.path.abspath(__file__))
window_width: int = 512
window_height: int = 512
fbo_width: int = 512
fbo_height: int = 512

HDRBALL, GAUSSIAN, COMBINE, SHOW2D = 0, 1, 2, 3
TOTAL_SHADER_SETS = 4
shader_names = ["hdrball", "gaussian", "combine", "show2d"]
v_shader = [0] * TOTAL_SHADER_SETS
f_shader = [0] * TOTAL_SHADER_SETS
prog_obj = [0] * TOTAL_SHADER_SETS

ORIG_SCENE = 0
BRIGHT_PASS = 1
PRE_BLUR = 2
POST_BLUR = 3
JUST_BLOOM = 4
NO_AFTER_GLOW = 5
JUST_AFTER_GLOW = 6
FULL_SCENE = 7
which_stop_point: int = FULL_SCENE
after_glow_valid: bool = False

texture_id: list = [0] * 7
framebuffer_id: list = [0] * 5
renderbuffer_id: int = 0
pbo_id: int = 0
max_tex_size: int = 0
tex_coord_offsets = np.zeros((4, 5 * 5 * 2), dtype=np.float32)

light_pos_loc: int = -1
bloom_limit_loc: int = -1
offsets_loc: int = -1
star_intensity_loc: int = -1
after_glow_loc: int = -1

camera_pos = [50.0, 50.0, 150.0, 1.0]
camera_zoom: float = 0.4
light_pos = np.array([140.0, 250.0, 140.0, 1.0], dtype=np.float32)
light_rotation: float = 30.0
bloom_limit: float = 1.0
tess: int = 75
animation_angle: float = 0.0
angle_increment: float = 4.0
paused: bool = False


def transform_vec3(v: np.ndarray, m: np.ndarray) -> np.ndarray:
    out = np.zeros(3, dtype=np.float32)
    for r in range(3):
        out[r] = m[r] * v[0] + m[r + 4] * v[1] + m[r + 8] * v[2] + m[r + 12] * v[3]
    return out


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


def prepare_shader(n: int) -> None:
    name = shader_names[n]
    with open(os.path.join(PWD, "shaders", f"{name}.vs")) as f:
        vs_src = f.read()
    with open(os.path.join(PWD, "shaders", f"{name}.fs")) as f:
        fs_src = f.read()
    v_shader[n] = shaders_mod.compileShader(vs_src, GL.GL_VERTEX_SHADER)
    f_shader[n] = shaders_mod.compileShader(fs_src, GL.GL_FRAGMENT_SHADER)
    prog_obj[n] = GL.glCreateProgram()
    GL.glAttachShader(prog_obj[n], v_shader[n])
    GL.glAttachShader(prog_obj[n], f_shader[n])
    GL.glLinkProgram(prog_obj[n])
    if not GL.glGetProgramiv(prog_obj[n], GL.GL_LINK_STATUS):
        info = GL.glGetProgramInfoLog(prog_obj[n])
        sys.stderr.write(f"Program {n} link error: {info}\n")
        sys.exit(1)


def draw_models() -> None:
    GL.glPushMatrix()
    GL.glRotatef(light_rotation, 0.0, 1.0, 0.0)
    mv = np.array(GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX),
                  dtype=np.float32).flatten()
    light_pos_eye = transform_vec3(light_pos, mv)
    GL.glPopMatrix()
    GL.glUniform3fv(light_pos_loc, 1, light_pos_eye)
    GL.glPushMatrix()
    GL.glRotatef(animation_angle / 5.0, 0.0, 1.0, 0.0)
    draw_solid_sphere(50.0, tess, tess)
    GL.glPopMatrix()


def first_pass() -> None:
    GL.glUseProgram(prog_obj[HDRBALL])
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, framebuffer_id[0])
    GL.glViewport(0, 0, fbo_width, fbo_height)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glUniform1f(star_intensity_loc, abs(angle_increment))
    draw_models()
    GL.glDisable(GL.GL_DEPTH_TEST)


def second_pass() -> None:
    GL.glUseProgram(prog_obj[GAUSSIAN])
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id[1])
    for i in range(4):
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, framebuffer_id[1 + i])
        GL.glViewport(0, 0, fbo_width >> i, fbo_height >> i)
        GL.glUniform2fv(offsets_loc, 25, tex_coord_offsets[i])
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_BASE_LEVEL, i)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAX_LEVEL, i)
        GL.glBegin(GL.GL_QUADS)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 0.0, 0.0); GL.glVertex2f(-1.0, -1.0)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 0.0, 1.0); GL.glVertex2f(-1.0, 1.0)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 1.0, 1.0); GL.glVertex2f(1.0, 1.0)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 1.0, 0.0); GL.glVertex2f(1.0, -1.0)
        GL.glEnd()
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_BASE_LEVEL, 0)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAX_LEVEL, 1000)


def final_pass() -> None:
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
    GL.glViewport(0, 0, window_width, window_height)
    GL.glActiveTexture(GL.GL_TEXTURE5)
    GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, pbo_id)
    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB8, fbo_width, fbo_height,
                    0, GL.GL_RGB, GL.GL_UNSIGNED_BYTE, None)
    GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)
    GL.glActiveTexture(GL.GL_TEXTURE0)

    if which_stop_point == ORIG_SCENE:
        GL.glUseProgram(prog_obj[SHOW2D])
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id[0])
    elif which_stop_point in (BRIGHT_PASS, PRE_BLUR):
        GL.glUseProgram(prog_obj[SHOW2D])
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id[1])
    elif which_stop_point == POST_BLUR:
        GL.glUseProgram(prog_obj[SHOW2D])
    else:
        GL.glUseProgram(prog_obj[COMBINE])
        if which_stop_point in (JUST_BLOOM, JUST_AFTER_GLOW):
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        else:
            GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id[0])
        GL.glUniform1i(after_glow_loc,
                       1 if (which_stop_point >= JUST_AFTER_GLOW
                             and after_glow_valid) else 0)

    GL.glBegin(GL.GL_QUADS)
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 0.0, 0.0); GL.glVertex2f(-1.0, -1.0)
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 0.0, 1.0); GL.glVertex2f(-1.0, 1.0)
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 1.0, 1.0); GL.glVertex2f(1.0, 1.0)
    GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 1.0, 0.0); GL.glVertex2f(1.0, -1.0)
    GL.glEnd()


def render_scene() -> None:
    global animation_angle, angle_increment, after_glow_valid
    if not paused:
        animation_angle = (animation_angle + angle_increment) % 360.0
        angle_increment *= 0.99
        if abs(angle_increment) < 0.01:
            angle_increment = 0.0

    GL.glMatrixMode(GL.GL_PROJECTION); GL.glLoadIdentity()
    if window_width > window_height:
        ar = float(window_width) / float(window_height)
        GL.glFrustum(-ar * camera_zoom, ar * camera_zoom,
                     -camera_zoom, camera_zoom, 1.0, 1000.0)
    else:
        ar = float(window_height) / float(window_width)
        GL.glFrustum(-camera_zoom, camera_zoom,
                     -ar * camera_zoom, ar * camera_zoom, 1.0, 1000.0)
    GL.glMatrixMode(GL.GL_MODELVIEW); GL.glLoadIdentity()
    GLU.gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
                  0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

    first_pass()
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id[1])
    GL.glGenerateMipmap(GL.GL_TEXTURE_2D)
    second_pass()
    final_pass()

    GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, pbo_id)
    GL.glReadPixels(0, 0, fbo_width, fbo_height,
                    GL.GL_RGB, GL.GL_UNSIGNED_BYTE, None)
    GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, 0)
    after_glow_valid = True
    GL.glUseProgram(0)


def setup_textures() -> None:
    global texture_id
    texture_id = list(GL.glGenTextures(7))
    for i in range(2):
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id[i])
        for p in (GL.GL_TEXTURE_WRAP_S, GL.GL_TEXTURE_WRAP_T):
            GL.glTexParameteri(GL.GL_TEXTURE_2D, p, GL.GL_CLAMP_TO_EDGE)
        for p in (GL.GL_TEXTURE_MIN_FILTER, GL.GL_TEXTURE_MAG_FILTER):
            GL.glTexParameteri(GL.GL_TEXTURE_2D, p, GL.GL_LINEAR)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB16F,
                        fbo_width, fbo_height, 0, GL.GL_RGB, GL.GL_FLOAT, None)
    for i in range(2, 7):
        GL.glActiveTexture(GL.GL_TEXTURE1 + i - 2)
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id[i])
        for p in (GL.GL_TEXTURE_WRAP_S, GL.GL_TEXTURE_WRAP_T):
            GL.glTexParameteri(GL.GL_TEXTURE_2D, p, GL.GL_CLAMP_TO_EDGE)
        for p in (GL.GL_TEXTURE_MIN_FILTER, GL.GL_TEXTURE_MAG_FILTER):
            GL.glTexParameteri(GL.GL_TEXTURE_2D, p, GL.GL_LINEAR)
        if i < 6:
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA8,
                            fbo_width >> (i - 2), fbo_height >> (i - 2),
                            0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, None)
        else:
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB8,
                            fbo_width, fbo_height,
                            0, GL.GL_RGB, GL.GL_UNSIGNED_BYTE, None)
    GL.glActiveTexture(GL.GL_TEXTURE0)


def setup_rc() -> None:
    global max_tex_size, framebuffer_id, renderbuffer_id, pbo_id
    global light_pos_loc, bloom_limit_loc, offsets_loc, star_intensity_loc
    global after_glow_loc

    max_tex_size = min(GL.glGetIntegerv(GL.GL_MAX_TEXTURE_SIZE),
                       GL.glGetIntegerv(GL.GL_MAX_RENDERBUFFER_SIZE))
    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
    GL.glDepthFunc(GL.GL_LEQUAL)
    GL.glShadeModel(GL.GL_SMOOTH)
    GL.glHint(GL.GL_GENERATE_MIPMAP_HINT, GL.GL_NICEST)

    for i in range(TOTAL_SHADER_SETS):
        prepare_shader(i)

    GL.glUseProgram(prog_obj[HDRBALL])
    light_pos_loc = GL.glGetUniformLocation(prog_obj[HDRBALL], "lightPos")
    star_intensity_loc = GL.glGetUniformLocation(prog_obj[HDRBALL], "starIntensity")
    bloom_limit_loc = GL.glGetUniformLocation(prog_obj[HDRBALL], "bloomLimit")
    GL.glUniform1f(bloom_limit_loc, bloom_limit)
    GL.glUseProgram(prog_obj[GAUSSIAN])
    offsets_loc = GL.glGetUniformLocation(prog_obj[GAUSSIAN], "tc_offset")
    s = GL.glGetUniformLocation(prog_obj[GAUSSIAN], "sampler0")
    if s != -1:
        GL.glUniform1i(s, 0)
    GL.glUseProgram(prog_obj[COMBINE])
    for i in range(6):
        s = GL.glGetUniformLocation(prog_obj[COMBINE], f"sampler{i}")
        if s != -1:
            GL.glUniform1i(s, i)
    after_glow_loc = GL.glGetUniformLocation(prog_obj[COMBINE], "afterGlow")
    GL.glUseProgram(prog_obj[SHOW2D])
    s = GL.glGetUniformLocation(prog_obj[SHOW2D], "sampler0")
    if s != -1:
        GL.glUniform1i(s, 0)
    GL.glUseProgram(0)

    setup_textures()

    pbo_id = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, pbo_id)
    GL.glBufferData(GL.GL_PIXEL_PACK_BUFFER, 1, None, GL.GL_STREAM_COPY)
    GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, 0)

    renderbuffer_id = GL.glGenRenderbuffers(1)
    GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, renderbuffer_id)
    GL.glRenderbufferStorage(GL.GL_RENDERBUFFER, GL.GL_DEPTH_COMPONENT32,
                             fbo_width, fbo_height)
    framebuffer_id[:] = list(GL.glGenFramebuffers(5))
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, framebuffer_id[0])
    GL.glDrawBuffers(2, [GL.GL_COLOR_ATTACHMENT0, GL.GL_COLOR_ATTACHMENT1])
    GL.glFramebufferRenderbuffer(GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT,
                                 GL.GL_RENDERBUFFER, renderbuffer_id)
    GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0,
                              GL.GL_TEXTURE_2D, texture_id[0], 0)
    GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT1,
                              GL.GL_TEXTURE_2D, texture_id[1], 0)
    for i in range(4):
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, framebuffer_id[1 + i])
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0,
                                  GL.GL_TEXTURE_2D, texture_id[2 + i], 0)
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)


def change_size(w: int, h: int) -> None:
    global window_width, window_height, fbo_width, fbo_height, after_glow_valid
    orig = (fbo_width, fbo_height)
    window_width = fbo_width = w
    window_height = fbo_height = h
    if fbo_width > max_tex_size: fbo_width = max_tex_size
    if fbo_height > max_tex_size: fbo_height = max_tex_size
    if (fbo_width, fbo_height) != orig and pbo_id != 0:
        GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, pbo_id)
        pitch = ((fbo_width * 3) + 3) & ~0x3
        GL.glBufferData(GL.GL_PIXEL_PACK_BUFFER, fbo_height * pitch,
                        None, GL.GL_STREAM_COPY)
        GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, 0)
        after_glow_valid = False
        GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, renderbuffer_id)
        GL.glRenderbufferStorage(GL.GL_RENDERBUFFER, GL.GL_DEPTH_COMPONENT32,
                                 fbo_width, fbo_height)
        for i in range(2):
            GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id[i])
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB16F,
                            fbo_width, fbo_height, 0,
                            GL.GL_RGB, GL.GL_FLOAT, None)
        for i in range(2, 7):
            GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id[i])
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA8,
                            fbo_width >> (i - 2), fbo_height >> (i - 2),
                            0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, None)
        for k in range(4):
            xi = 1.0 / float(fbo_width >> k)
            yi = 1.0 / float(fbo_height >> k)
            for i in range(5):
                for j in range(5):
                    tex_coord_offsets[k][((i * 5) + j) * 2 + 0] = -2.0 * xi + i * xi
                    tex_coord_offsets[k][((i * 5) + j) * 2 + 1] = -2.0 * yi + j * yi


def on_framebuffer_size(_window, w: int, h: int) -> None:
    change_size(w, h)


def select_stop_point(p: int) -> None:
    global which_stop_point
    which_stop_point = p
    names = ["orig", "bright", "pre-blur", "post-blur",
             "just-bloom", "no-afterglow", "just-afterglow", "full"]
    print(f"stop point: {names[p]}")
    if p == JUST_AFTER_GLOW:
        for i, t in enumerate((1, 2, 3, 4)):
            GL.glActiveTexture(GL.GL_TEXTURE0 + t); GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
    else:
        for i, t in enumerate((1, 2, 3, 4)):
            GL.glActiveTexture(GL.GL_TEXTURE0 + t)
            GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id[2 + i])
    GL.glActiveTexture(GL.GL_TEXTURE0)


def on_key(window, key: int, _scancode: int, action: int, mods: int) -> None:
    global light_rotation, tess, bloom_limit, paused
    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True); return
    if glfw.KEY_1 <= key <= glfw.KEY_8:
        select_stop_point(key - glfw.KEY_1); return
    if key == glfw.KEY_LEFT:
        light_rotation -= 5.0
    elif key == glfw.KEY_RIGHT:
        light_rotation += 5.0
    elif key == glfw.KEY_UP:
        tess += 5
    elif key == glfw.KEY_DOWN:
        tess = max(5, tess - 5)
    elif key == glfw.KEY_L:
        bloom_limit += 0.05 if (mods & glfw.MOD_SHIFT) else -0.05
        GL.glUseProgram(prog_obj[HDRBALL])
        GL.glUniform1f(bloom_limit_loc, bloom_limit)
        GL.glUseProgram(0)
    elif key == glfw.KEY_P:
        paused = not paused
    elif key == glfw.KEY_X:
        camera_pos[0] += -5.0 if (mods & glfw.MOD_SHIFT) else 5.0
    elif key == glfw.KEY_Y:
        camera_pos[1] += -5.0 if (mods & glfw.MOD_SHIFT) else 5.0
    elif key == glfw.KEY_Z:
        camera_pos[2] += -5.0 if (mods & glfw.MOD_SHIFT) else 5.0


def main() -> None:
    if not glfw.init():
        sys.exit(1)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    window = glfw.create_window(window_width, window_height,
                                "High Dynamic Range Bloom Demo", None, None)
    if not window:
        glfw.terminate(); sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glfw.set_framebuffer_size_callback(window, on_framebuffer_size)

    print("HDR Bloom Demo")
    print("  1..8: stop point   L / shift+L: bloom limit   P: pause")
    print("  arrows: rotate light / change tess   X/Y/Z + shift: pan")

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
