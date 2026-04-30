
# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
import ctypes
import dataclasses
import math


from numpy import ndarray


# When using a pure python backend, prefer to import glfw before
# imgui_bundle (so that you end up using the standard glfw, not the
# one provided by imgui_bundle)
import glfw
import numpy as np
import OpenGL.GL as GL  # pip install PyOpenGL

# new - SHADERS
import OpenGL.GL.shaders as shaders
from imgui_bundle import imgui, imgui_md
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer
from numpy.typing import NDArray

import modelviewprojection.colorutils as colorutils
import modelviewprojection.pyMatrixStack as ms

if not glfw.init():
    sys.exit()

# NEW - for shader location
pwd = os.path.dirname(os.path.abspath(__file__))

# NEW - for shaders
glfloat_size = 4
floatsPerVector = 3
floatsPerColor = 4


glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
# CORE profile means no fixed functions.
# compatibility profile would mean access to legacy fixed functions
# compatibility mode isn't supported by every graphics driver,
# particulary on laptops which switch between integrated graphics
# and a discrete card over time based off of usage.
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
# for osx
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)


def init_fonts_and_markdown() -> None:
    # uncomment to keep using the default hardcoded font, or load your default font here
    # imgui.get_io().fonts.add_font_default()

    # Load markdown fonts
    imgui_md.initialize_markdown()
    font_loader: imgui_md.VoidFunction = imgui_md.get_font_loader_function()
    font_loader()


def impl_glfw_init():

    width, height = 500, 500
    window_name = "ModelViewProjection Demo 21 "

    if not glfw.init():
        print("Could not initialize OpenGL context")
        sys.exit(1)

    # OS X supports only forward-compatible core profiles from 3.2
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)

    # Create a windowed mode window and its OpenGL context
    window = glfw.create_window(
        int(width), int(height), window_name, None, None
    )
    glfw.make_context_current(window)

    if not window:
        glfw.terminate()
        print("Could not initialize Window")
        sys.exit(1)

    return window


imgui.create_context()
window = impl_glfw_init()
impl = GlfwRenderer(window)
init_fonts_and_markdown()

if not impl:
    glfw.terminate()
    sys.exit()

# Make the window's context current
glfw.make_context_current(window)


# Install a key handler
def on_key(win, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(win, 1)


glfw.set_key_callback(window, on_key)

GL.glClearColor(0.0289, 0.071875, 0.0972, 1.0)


GL.glClearDepth(1.0)
GL.glDepthFunc(GL.GL_LEQUAL)
GL.glEnable(GL.GL_DEPTH_TEST)

__enable_blend__: bool = True
if __enable_blend__:
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)


# ---------------------------------------------------------------------------
# Pipeline -- compile each shader program once, cache uniform locations.
# ---------------------------------------------------------------------------


def compile_program(vert_filename: str, frag_filename: str) -> int:
    with open(os.path.join(pwd, vert_filename), "r") as f:
        vs = shaders.compileShader(f.read(), GL.GL_VERTEX_SHADER)
    with open(os.path.join(pwd, frag_filename), "r") as f:
        fs = shaders.compileShader(f.read(), GL.GL_FRAGMENT_SHADER)
    return shaders.compileProgram(vs, fs)


triangle_program: int = compile_program("triangle.vert", "triangle.frag")
u_triangle_mvp: int = GL.glGetUniformLocation(triangle_program, "mvpMatrix")
triangle_attr_position: int = GL.glGetAttribLocation(
    triangle_program, "position"
)
triangle_attr_color: int = GL.glGetAttribLocation(triangle_program, "color_in")

ground_program: int = compile_program("ground.vert", "ground.frag")
u_ground_mvp: int = GL.glGetUniformLocation(ground_program, "mvpMatrix")
ground_attr_position: int = GL.glGetAttribLocation(ground_program, "position")


# ---------------------------------------------------------------------------
# Geometry -- build VAOs + VBOs once, at module scope.
# ---------------------------------------------------------------------------


all_vaos: list[int] = []
all_vbos: list[int] = []


def make_colored_vao(
    vertices: NDArray, color: colorutils.Color4
) -> tuple[int, int]:
    """Build a VAO for the triangle pipeline:  positions + per-vertex
    color, with the color repeated once per vertex.  Returns
    (vao, vertex_count)."""
    vertices = np.ascontiguousarray(vertices, dtype=np.float32)
    n_verts = vertices.size // floatsPerVector
    color_arr = np.tile(
        np.array([color.r, color.g, color.b, color.a], dtype=np.float32),
        n_verts,
    )

    vao = GL.glGenVertexArrays(1)
    all_vaos.append(vao)
    GL.glBindVertexArray(vao)

    pos_vbo = GL.glGenBuffers(1)
    all_vbos.append(pos_vbo)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, pos_vbo)
    GL.glBufferData(
        GL.GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL.GL_STATIC_DRAW
    )
    GL.glEnableVertexAttribArray(triangle_attr_position)
    GL.glVertexAttribPointer(
        triangle_attr_position,
        floatsPerVector,
        GL.GL_FLOAT,
        False,
        0,
        ctypes.c_void_p(0),
    )

    color_vbo = GL.glGenBuffers(1)
    all_vbos.append(color_vbo)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, color_vbo)
    GL.glBufferData(
        GL.GL_ARRAY_BUFFER, color_arr.nbytes, color_arr, GL.GL_STATIC_DRAW
    )
    GL.glEnableVertexAttribArray(triangle_attr_color)
    GL.glVertexAttribPointer(
        triangle_attr_color,
        floatsPerColor,
        GL.GL_FLOAT,
        False,
        0,
        ctypes.c_void_p(0),
    )

    GL.glBindVertexArray(0)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    return vao, n_verts


def make_ground_vao() -> tuple[int, int]:
    verts: list[float] = []
    for x in range(-600, 601, 20):
        for z in range(-600, 601, 20):
            verts += [-float(x), -5.0, float(z)]
            verts += [ float(x), -5.0, float(z)]
            verts += [ float(x), -5.0, -float(z)]
            verts += [ float(x), -5.0,  float(z)]
    vertices = np.array(verts, dtype=np.float32)
    n_verts = vertices.size // floatsPerVector

    vao = GL.glGenVertexArrays(1)
    all_vaos.append(vao)
    GL.glBindVertexArray(vao)

    vbo = GL.glGenBuffers(1)
    all_vbos.append(vbo)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
    GL.glBufferData(
        GL.GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL.GL_STATIC_DRAW
    )
    GL.glEnableVertexAttribArray(ground_attr_position)
    GL.glVertexAttribPointer(
        ground_attr_position,
        floatsPerVector,
        GL.GL_FLOAT,
        False,
        0,
        ctypes.c_void_p(0),
    )

    GL.glBindVertexArray(0)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    return vao, n_verts


paddle_vertices: NDArray = np.array(
    [
        [-1.0, -3.0, 0.0],
        [ 1.0, -3.0, 0.0],
        [ 1.0,  3.0, 0.0],
        [ 1.0,  3.0, 0.0],
        [-1.0,  3.0, 0.0],
        [-1.0, -3.0, 0.0],
    ],
    dtype=np.float32,
)
square_vertices: NDArray = np.array(
    [
        [-0.5, -0.5, 0.0],
        [ 0.5, -0.5, 0.0],
        [ 0.5,  0.5, 0.0],
        [ 0.5,  0.5, 0.0],
        [-0.5,  0.5, 0.0],
        [-0.5, -0.5, 0.0],
    ],
    dtype=np.float32,
)

paddle1_color: colorutils.Color4 = colorutils.Color4(
    r=0.578123, g=0.0, b=1.0, a=0.75
)
paddle2_color: colorutils.Color4 = colorutils.Color4(
    r=1.0, g=1.0, b=0.0, a=0.75
)
square_color: colorutils.Color4 = colorutils.Color4(
    r=0.0, g=0.0, b=1.0, a=0.75
)

paddle1_vao, paddle1_vertex_count = make_colored_vao(
    paddle_vertices, paddle1_color
)
paddle2_vao, paddle2_vertex_count = make_colored_vao(
    paddle_vertices, paddle2_color
)
square_vao, square_vertex_count = make_colored_vao(
    square_vertices, square_color
)
ground_vao, ground_vertex_count = make_ground_vao()


# ---------------------------------------------------------------------------
# Scene state -- plain module-level data.
# ---------------------------------------------------------------------------


paddle1_position: NDArray = np.array([-9.0, 0.0, 0.0])
paddle1_rotation: float = 0.0

paddle2_position: NDArray = np.array([9.0, 0.0, 0.0])
paddle2_rotation: float = 0.0

# the square has no world-space position of its own -- it lives in
# paddle1's local space, so only its rotations matter.
square_rotation: float = 0.0
square_rotation_around_paddle1: float = 0.0


number_of_controllers = glfw.joystick_present(glfw.JOYSTICK_1)


@dataclasses.dataclass
class Camera:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rot_y: float = 0.0
    rot_x: float = 0.0


camera = Camera(x=0.0, y=0.0, z=40.0, rot_y=0.0, rot_x=0.0)


# ---------------------------------------------------------------------------
# Rendering helpers -- one draw function per pipeline.
# ---------------------------------------------------------------------------


def _current_mvp_bytes() -> NDArray:
    return np.ascontiguousarray(
        ms.get_current_matrix(ms.MatrixStack.modelviewprojection),
        dtype=np.float32,
    )


def draw_triangles(vao: int, vertex_count: int) -> None:
    GL.glUseProgram(triangle_program)
    GL.glUniformMatrix4fv(u_triangle_mvp, 1, GL.GL_TRUE, _current_mvp_bytes())
    GL.glBindVertexArray(vao)
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, vertex_count)
    GL.glBindVertexArray(0)


def draw_lines(vao: int, vertex_count: int) -> None:
    GL.glUseProgram(ground_program)
    GL.glUniformMatrix4fv(u_ground_mvp, 1, GL.GL_TRUE, _current_mvp_bytes())
    GL.glBindVertexArray(vao)
    GL.glDrawArrays(GL.GL_LINES, 0, vertex_count)
    GL.glBindVertexArray(0)


def handle_inputs() -> None:
    global square_rotation_around_paddle1, square_rotation
    global paddle1_rotation, paddle2_rotation

    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        square_rotation_around_paddle1 += 0.1

    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square_rotation += 0.1

    move_multiple = 1.0
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.rot_y -= 0.03
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.rot_y += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_UP) == glfw.PRESS:
        camera.rot_x += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_DOWN) == glfw.PRESS:
        camera.rot_x -= 0.03
    # //TODO -  explain movement on XZ-plane
    # //TODO -  show camera movement in graphviz
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera.x -= move_multiple * math.sin(camera.rot_y)
        camera.z -= move_multiple * math.cos(camera.rot_y)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.x += move_multiple * math.sin(camera.rot_y)
        camera.z += move_multiple * math.cos(camera.rot_y)

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1_position[1] -= 1.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1_position[1] += 1.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2_position[1] -= 1.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2_position[1] += 1.0

    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        paddle1_rotation += 0.1
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        paddle1_rotation -= 0.1
    if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
        paddle2_rotation += 0.1
    if glfw.get_key(window, glfw.KEY_L) == glfw.PRESS:
        paddle2_rotation -= 0.1


# fmt: off
# square_vertices = np.array(
#     [[-5.0, -5.0, 0.0],
#      [5.0, -5.0, 0.0],
#      [5.0, 5.0, 0.0],
#      [-5.0, 5.0, 0.0]],
#     dtype=np.float32,
# )
# fmt: on


TARGET_FRAMERATE = 60  # fps

# to try to standardize on 60 fps, compare times between frames
time_at_beginning_of_previous_frame = glfw.get_time()

# Loop until the user closes the window
while not glfw.window_should_close(window):
    # poll the time to try to get a constant framerate
    while (
        glfw.get_time()
        < time_at_beginning_of_previous_frame + 1.0 / TARGET_FRAMERATE
    ):
        pass

    # set for comparison on the next frame
    time_at_beginning_of_previous_frame = glfw.get_time()

    # Poll for and process events
    glfw.poll_events()
    impl.process_inputs()

    imgui.new_frame()

    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("File", True):
            clicked_quit, selected_quit = imgui.menu_item(
                "Quit", "Cmd+Q", False, True
            )

            if clicked_quit:
                exit(1)

            imgui.end_menu()
        imgui.end_main_menu_bar()

    imgui.begin("Custom window", True)

    changed, __enable_blend__ = imgui.checkbox(
        label="Blend", v=__enable_blend__
    )

    if changed:
        if __enable_blend__:
            GL.glEnable(GL.GL_BLEND)
        else:
            GL.glDisable(GL.GL_BLEND)

    imgui.end()

    width, height = glfw.get_framebuffer_size(window)
    GL.glViewport(0, 0, width, height)
    GL.glClear(sum([GL.GL_COLOR_BUFFER_BIT, GL.GL_DEPTH_BUFFER_BIT]))

    ms.set_to_identity_matrix(ms.MatrixStack.model)
    ms.set_to_identity_matrix(ms.MatrixStack.view)
    ms.set_to_identity_matrix(ms.MatrixStack.projection)

    # set the projection matrix to be perspective
    ms.perspective(
        field_of_view=45.0,
        aspect_ratio=float(width) / float(height),
        near_z=0.1,
        far_z=1000.0,
    )

    # render scene
    width, height = glfw.get_framebuffer_size(window)
    GL.glViewport(0, 0, width, height)
    GL.glClearColor(0.0289, 0.071875, 0.0972, 1.0)  # r  # g  # b  # a
    GL.glClear(sum([GL.GL_COLOR_BUFFER_BIT, GL.GL_DEPTH_BUFFER_BIT]))

    handle_inputs()

    axes_list = glfw.get_joystick_axes(glfw.JOYSTICK_1)
    if len(axes_list) >= 1 and axes_list[0]:
        if math.fabs(float(axes_list[0][0])) > 0.1:
            camera.x += 1.0 * axes_list[0][0] * math.cos(camera.rot_y)
            camera.z -= 1.0 * axes_list[0][0] * math.sin(camera.rot_y)
        if math.fabs(float(axes_list[0][1])) > 0.1:
            camera.x += 1.0 * axes_list[0][1] * math.sin(camera.rot_y)
            camera.z += 1.0 * axes_list[0][1] * math.cos(camera.rot_y)

        # print(axes_list[0][4])
        if math.fabs(axes_list[0][3]) > 0.10:
            camera.rot_x -= 3.0 * axes_list[0][3] * 0.01
        if math.fabs(axes_list[0][2]) > 0.10:
            camera.rot_y -= 3.0 * axes_list[0][2] * 0.01

    # note - opengl matrices use degrees
    ms.rotate_x(ms.MatrixStack.view, -camera.rot_x)
    ms.rotate_y(ms.MatrixStack.view, -camera.rot_y)
    ms.translate(ms.MatrixStack.view, -camera.x, -camera.y, -camera.z)

    draw_lines(ground_vao, ground_vertex_count)

    with ms.push_matrix(ms.MatrixStack.model):
        # draw paddle 1
        # Unlike in previous demos, because the transformations
        # are on a stack, the fns on the model stack can
        # be read forwards, where each operation translates/rotates/scales
        # the current space
        ms.translate(
            ms.MatrixStack.model,
            paddle1_position[0],
            paddle1_position[1],
            0.0,
        )
        ms.rotate_z(ms.MatrixStack.model, paddle1_rotation)
        draw_triangles(paddle1_vao, paddle1_vertex_count)

        with ms.push_matrix(ms.MatrixStack.model):
            # # draw the square

            # since the modelstack is already in paddle1's space
            # just add the transformations relative to it
            # before paddle 2 is drawn, we need to remove
            # the square's 3 ms transformations

            ms.translate(ms.MatrixStack.model, 0.0, 0.0, -1.0)
            ms.rotate_z(ms.MatrixStack.model, square_rotation_around_paddle1)

            ms.translate(ms.MatrixStack.model, 2.0, 0.0, 0.0)
            ms.rotate_z(ms.MatrixStack.model, square_rotation)

            draw_triangles(square_vao, square_vertex_count)
        # back to padde 1 space
    # get back to center of global space

    with ms.push_matrix(ms.MatrixStack.model):
        # draw paddle 2

        ms.translate(
            ms.MatrixStack.model,
            paddle2_position[0],
            paddle2_position[1],
            0.0,
        )
        ms.rotate_z(ms.MatrixStack.model, paddle2_rotation)
        draw_triangles(paddle2_vao, paddle2_vertex_count)

    imgui.render()
    impl.render(imgui.get_draw_data())
    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)


# Clean up GL resources before tearing down the context.
GL.glBindVertexArray(0)
GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
GL.glUseProgram(0)

for vao in all_vaos:
    GL.glDeleteVertexArrays(1, [vao])
for vbo in all_vbos:
    GL.glDeleteBuffers(1, [vbo])
GL.glDeleteProgram(triangle_program)
GL.glDeleteProgram(ground_program)

glfw.terminate()
