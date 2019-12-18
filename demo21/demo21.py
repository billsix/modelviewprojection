import sys
import os
import numpy as np
import math
from OpenGL.GL import *
# new - SHADERS
import OpenGL.GL.shaders as shaders
import glfw
import pyMatrixStack as ms

if not glfw.init():
    sys.exit()

# NEW - for shader location
pwd = os.path.dirname(os.path.abspath(__file__))

# NEW - for shaders
glfloat_size = 4
floatsPerVertex = 3
floatsPerColor = 3


glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
# CORE profile means no fixed functions.
# compatibility profile would mean access to legacy fixed functions
# compatibility mode isn't supported by every graphics driver,
# particulary on laptops which switch between integrated graphics
# and a discrete card over time based off of usage.
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
# for osx
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)

window = glfw.create_window(500,
                            500,
                            "ModelViewProjection Demo 21",
                            None,
                            None)
if not window:
    glfw.terminate()
    sys.exit()

# Make the window's context current
glfw.make_context_current(window)

# Install a key handler


def on_key(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, 1)


glfw.set_key_callback(window, on_key)

glClearColor(0.0,
             0.0,
             0.0,
             1.0)


# NEW - TODO - talk about opengl matricies and z pos/neg
glClearDepth(-1.0)
glDepthFunc(GL_GREATER)
glEnable(GL_DEPTH_TEST)


class Paddle:
    def __init__(self, r, g, b, global_position, rotation=0.0, offset_x=0.0, offset_y=0.0):
        self.r = r
        self.g = g
        self.b = b
        self.rotation = rotation
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.global_position = global_position


    def vertices(self):
        return np.array([-10.0, -30.0,  0.0,
                         10.0,  -30.0,  0.0,
                         10.0,   30.0,  0.0,
                         10.0,   30.0,  0.0,
                         -10.0,  30.0,  0.0,
                         -10.0, -30.0,  0.0],
                        dtype=np.float32)

    def prepare_to_render(self):
        # GL_QUADS aren't available anymore, only triangles
        # need 6 vertices instead of 4
        vertices = self.vertices()
        self.numberOfVertices = np.size(vertices) // floatsPerVertex
        color = np.array([self.r, self.g, self.b,
                          self.r, self.g, self.b,
                          self.r, self.g, self.b,
                          self.r, self.g, self.b,
                          self.r, self.g, self.b,
                          self.r, self.g, self.b],
                         dtype=np.float32)
        self.numberOfColors = np.size(color) // floatsPerColor

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # initialize shaders

        with open(os.path.join(pwd, 'triangle21.vert'), 'r') as f:
            vs = shaders.compileShader(f.read(), GL_VERTEX_SHADER)

        with open(os.path.join(pwd, 'triangle21.frag'), 'r') as f:
            fs = shaders.compileShader(f.read(), GL_FRAGMENT_SHADER)

        self.shader = shaders.compileProgram(vs, fs)

        self.mvMatrixLoc = glGetUniformLocation(self.shader, "mvMatrix")


        # send the modelspace data to the GPU
        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)

        position = glGetAttribLocation(self.shader, 'position')
        glEnableVertexAttribArray(position)

        glVertexAttribPointer(position,
                              floatsPerVertex,
                              GL_FLOAT,
                              False,
                              0,
                              ctypes.c_void_p(0))

        glBufferData(GL_ARRAY_BUFFER,
                     glfloat_size * np.size(vertices),
                     vertices,
                     GL_STATIC_DRAW)


        # send the modelspace data to the GPU
        vboColor = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vboColor)

        colorAttribLoc = glGetAttribLocation(self.shader, 'color_in')
        glEnableVertexAttribArray(colorAttribLoc)
        glVertexAttribPointer(colorAttribLoc,
                              floatsPerColor,
                              GL_FLOAT,
                              False,
                              0,
                              ctypes.c_void_p(0))

        glBufferData(GL_ARRAY_BUFFER,
                     glfloat_size * np.size(color),
                     color,
                     GL_STATIC_DRAW)


        # reset VAO/VBO to default
        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def render(self):
        glUseProgram(self.shader)
        glBindVertexArray(self.vao)

        # pass projection parameters to the shader
        fov_loc = glGetUniformLocation(self.shader, "fov");
        glUniform1f(fov_loc, 45.0);
        aspect_loc = glGetUniformLocation(self.shader, "aspectRatio");
        glUniform1f(aspect_loc, width/height);
        nearZ_loc = glGetUniformLocation(self.shader, "nearZ");
        glUniform1f(nearZ_loc, -0.1);
        farZ_loc = glGetUniformLocation(self.shader, "farZ");
        glUniform1f(farZ_loc, -10000.0);

        # ascontiguousarray puts the array in column major order
        glUniformMatrix4fv(self.mvMatrixLoc,
                           1,
                           GL_TRUE,
                           np.ascontiguousarray(
                               ms.getCurrentMatrix(
                                   ms.MatrixStack.modelview),
                               dtype=np.float32))
        glDrawArrays(GL_TRIANGLES,
                     0,
                     self.numberOfVertices)
        glBindVertexArray(0)


paddle1 = Paddle(r=0.578123,
                 g=0.0,
                 b=1.0,
                 global_position=np.array([-90.0, 0.0, 0.0]))
paddle1.prepare_to_render()
paddle2 = Paddle(r=1.0,
                 g=0.0,
                 b=0.0,
                 global_position=np.array([90.0, 0.0, 0.0]))
paddle2.prepare_to_render()


class Square (Paddle):
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b
        self.rotation = 0.0
        self.rotation_around_paddle1 = 0.0


    def vertices(self):
        return np.array([[-5.0, -5.0,  0.0],
                         [5.0, -5.0,  0.0],
                         [5.0,  5.0,  0.0],
                         [5.0,  5.0,  0.0],
                         [-5.0, 5.0,  0.0],
                         [-5.0, -5.0,  0.0]],
                        dtype=np.float32)

square = Square(r=0.0,
                g=0.0,
                b=1.0)

square.prepare_to_render()


moving_camera_x = 0.0
moving_camera_y = 0.0
moving_camera_z = 400.0
moving_camera_rot_y = 0.0
moving_camera_rot_x = 0.0



def handle_inputs():
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        square.rotation_around_paddle1 += 0.1

    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square.rotation += 0.1

    global moving_camera_x
    global moving_camera_y
    global moving_camera_z
    global moving_camera_rot_x
    global moving_camera_rot_y

    move_multiple = 15.0
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        moving_camera_rot_y -= 0.03
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        moving_camera_rot_y += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_UP) == glfw.PRESS:
        moving_camera_rot_x += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_DOWN) == glfw.PRESS:
        moving_camera_rot_x -= 0.03
# //TODO -  explaing movement on XZ-plane
# //TODO -  show camera movement in graphviz
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        moving_camera_x -= move_multiple * math.sin(moving_camera_rot_y)
        moving_camera_z -= move_multiple * math.cos(moving_camera_rot_y)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        moving_camera_x += move_multiple * math.sin(moving_camera_rot_y)
        moving_camera_z += move_multiple * math.cos(moving_camera_rot_y)

    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.offset_y -= 10.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.offset_y += 10.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.offset_y -= 10.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.offset_y += 10.0

    global paddle_1_rotation, paddle_2_rotation

    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        paddle1.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        paddle1.rotation -= 0.1
    if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
        paddle2.rotation += 0.1
    if glfw.get_key(window, glfw.KEY_L) == glfw.PRESS:
        paddle2.rotation -= 0.1



square_vertices = np.array([[-5.0, -5.0,  0.0],
                            [5.0, -5.0,  0.0],
                            [5.0,  5.0,  0.0],
                            [-5.0, 5.0,  0.0]],
                           dtype=np.float32)



# Loop until the user closes the window
while not glfw.window_should_close(window):
    # Poll for and process events
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


    ms.setToIdentityMatrix(ms.MatrixStack.model)
    ms.setToIdentityMatrix(ms.MatrixStack.view)
    ms.setToIdentityMatrix(ms.MatrixStack.projection)

    # render scene
    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClearColor(0.0,  # r
                 0.0,  # g
                 0.0,  # b
                 1.0)  # a
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    handle_inputs()

    # note - opengl matricies use degrees
    ms.rotate_x(ms.MatrixStack.view,
               -moving_camera_rot_x)
    ms.rotate_y(ms.MatrixStack.view,
               -moving_camera_rot_y)
    ms.translate(ms.MatrixStack.view,
                 -moving_camera_x,
                 -moving_camera_y,
                 -moving_camera_z)

    with ms.push_matrix(ms.MatrixStack.model):
        # draw paddle 1
        # Unlike in previous demos, because the transformations
        # are on a stack, the fns on the model stack can
        # be read forwards, where each operation translates/rotates/scales
        # the current space
        ms.translate(ms.MatrixStack.model,
                     paddle1.offset_x,
                     paddle1.offset_y,
                     0.0)
        ms.translate(ms.MatrixStack.model,
                     paddle1.global_position[0],
                     paddle1.global_position[1],
                     0.0)
        ms.rotate_z(ms.MatrixStack.model,
                   paddle1.rotation)
        paddle1.render()

        with ms.push_matrix(ms.MatrixStack.model):
            # # draw the square

            # since the modelstack is already in paddle1's space
            # just add the transformations relative to it
            # before paddle 2 is drawn, we need to remove
            # the square's 3 model_space transformations

            ms.translate(ms.MatrixStack.model,
                         0.0,
                         0.0,
                         -10.0)
            ms.rotate_z(ms.MatrixStack.model,
                       square.rotation_around_paddle1)

            ms.translate(ms.MatrixStack.model,
                         20.0,
                         0.0,
                         0.0)
            ms.rotate_z(ms.MatrixStack.model,
                       square.rotation)

            square.render()
        # back to padde 1 space
    # get back to center of global space


    with ms.push_matrix(ms.MatrixStack.model):
        # draw paddle 2

        ms.translate(ms.MatrixStack.model,
                     paddle2.offset_x,
                     paddle2.offset_y,
                     0.0)
        ms.translate(ms.MatrixStack.model,
                     paddle2.global_position[0],
                     paddle2.global_position[1],
                     0.0)
        ms.rotate_z(ms.MatrixStack.model,
                   paddle2.rotation)
        paddle2.render()


    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)


glfw.terminate()
