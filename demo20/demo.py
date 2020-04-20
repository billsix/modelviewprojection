#Copyright (c) 2018-2020 William Emerison Six
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.


# Purpose.
#
# Use OpenGL 3.3, Core profile.  No more glBegin/glVertex/glEnd.
# We need to use vertex array objects and vertexbuffer objects.


import sys
import os
import numpy as np
import math
from OpenGL.GL import *
import OpenGL.GL.shaders as shaders
import glfw
import pyMatrixStack as ms
import atexit

if not glfw.init():
    sys.exit()

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
                            "ModelViewProjection Demo 20",
                            None,
                            None)
if not window:
    glfw.terminate()
    sys.exit()

# Make the window's context current
glfw.make_context_current(window)

# Install a key handler


def on_exit():
    # delete the objects
    paddle1.__del__()
    paddle2.__del__()
    square.__del__()

    # normally in Python, you should call "del paddle1",
    # but that would not guarantee that the object would
    # actually be garbage collected at that moment, and
    # the OpenGL context could be destroyed before the garbage
    # collection happens, therefore, force the destruction
    # of the VAO and VBO by immediately calling __del__
    #
    # This is not normal Python practice to call
    # this type of method directly, but oh well.
atexit.register(on_exit)



def on_key(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, 1)


glfw.set_key_callback(window, on_key)

glClearColor(0.0,
             0.0,
             0.0,
             1.0)


glClearDepth(-1.0)
glDepthFunc(GL_GREATER)
glEnable(GL_DEPTH_TEST)



class Paddle:
    def __init__(self, r, g, b, initial_position, rotation=0.0, input_offset_x=0.0, input_offset_y=0.0):
        self.r = r
        self.g = g
        self.b = b
        self.rotation = rotation
        self.input_offset_x = input_offset_x
        self.input_offset_y = input_offset_y
        self.initial_position = initial_position


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
        # get the number of vertices, for a later call to glDrawArrays
        self.numberOfVertices = np.size(vertices) // floatsPerVertex
        # Make a color array of the same length as the number of verticies.
        # it would have been more efficient to use indices, but I don't
        # want to put too much in this demo.
        color = np.array([self.r, self.g, self.b,
                          self.r, self.g, self.b,
                          self.r, self.g, self.b,
                          self.r, self.g, self.b,
                          self.r, self.g, self.b,
                          self.r, self.g, self.b],
                         dtype=np.float32)
        self.numberOfColors = np.size(color) // floatsPerColor

        # Create a vertex array object.
        # Before I talk about vertex array objects, I want to talk about
        # vertex buffer objects.
        # This topic is discussed in the OpenGL Blue book, but the gist is that
        # we push our modelspace data onto the graphics card's GPU memory,
        # either every frame (for data that changes per frame), or less frequently.
        # This is because function calls are expensive; every time you call
        # glBegin, glVertex, glEnd, there is subroutine linkage overhead.
        #
        # And worse, if you modelspace data rarely changes, what's the point of
        # sending that from RAM to the GPU every frame?
        #
        # So what are Vertex Array Objects then?  Well, in OpenGL Superbible
        # v4, there were a lot of predefined variables in the shaders.  You didn't
        # have to do anything to populate the modelviewprojection matrix, the vertices,
        # the color etc.
        #
        # Vertex array objects are a collection of vbos, and they can be configured
        # to pass data into the shader.
        #
        # create the vao
        self.vao = glGenVertexArrays(1)
        # make it the current VAO
        glBindVertexArray(self.vao)

        # initialize shaders
        with open(os.path.join(pwd, 'triangle.vert'), 'r') as f:
            vs = shaders.compileShader(f.read(), GL_VERTEX_SHADER)

        with open(os.path.join(pwd, 'triangle.frag'), 'r') as f:
            fs = shaders.compileShader(f.read(), GL_FRAGMENT_SHADER)

        self.shader = shaders.compileProgram(vs, fs)

        # create a vbo for the vertices, to send the modelspace data to the GPU
        self.vbo = glGenBuffers(1)
        # make the vbo current
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

        # get the handle for the position variable within the shader
        position = glGetAttribLocation(self.shader, 'position')
        # enable the position in the VAO, so that data will be fed from the
        # VBO
        glEnableVertexAttribArray(position)

        # specify how the vertex data should be fed from the VBO into the VAO
        glVertexAttribPointer(position, #index
                              floatsPerVertex, #size
                              GL_FLOAT, #type
                              False, #normalized (should be called normalize - a verb)
                              0, #stride (this is for interleaved arrays, meaning
                                 # [V1x, V1y, V1z, C1r, C1g, C1b, V2x .....]
                              ctypes.c_void_p(0)) #pointer (offset pointer, 0 because we start
                                                  # with the first vertex position
                                                  # if we used interleaved arrays,
                                                  # we would have this number be greater than 0
                                                  # to specify the offset of the first color

        # From the OpenGL docs
        #Parameters

        #index
        #
        #    Specifies the index of the generic vertex attribute to be modified.
        #
        #size
        #
        #    Specifies the number of components per generic vertex attribute. Must be 1, 2, 3, 4. Additionally,
        #    the symbolic constant GL_BGRA is accepted by glVertexAttribPointer. The initial value is 4.
        #
        #type
        #
        #    Specifies the data type of each component in the array. The symbolic constants GL_BYTE, GL_UNSIGNED_BYTE,
        #    GL_SHORT, GL_UNSIGNED_SHORT, GL_INT, and GL_UNSIGNED_INT are accepted by glVertexAttribPointer and
        #    glVertexAttribIPointer. Additionally GL_HALF_FLOAT, GL_FLOAT, GL_DOUBLE, GL_FIXED, GL_INT_2_10_10_10_REV,
        #    GL_UNSIGNED_INT_2_10_10_10_REV and GL_UNSIGNED_INT_10F_11F_11F_REV
        #    are accepted by glVertexAttribPointer. GL_DOUBLE is also accepted by glVertexAttribLPointer and is the only token
        #    accepted by the type parameter for that function. The initial value is GL_FLOAT.
        #
        #normalized
        #
        #    For glVertexAttribPointer, specifies whether fixed-point data values should be normalized (GL_TRUE) or converted directly
        #    as fixed-point values (GL_FALSE) when they are accessed.
        #
        #stride
        #
        #    Specifies the byte offset between consecutive generic vertex attributes. If stride is 0, the generic vertex
        #    attributes are understood to be tightly packed in the array. The initial value is 0.
        #
        #pointer
        #
        #    Specifies a offset of the first component of the first generic vertex attribute in the array
        #    in the data store of the buffer currently bound to the GL_ARRAY_BUFFER target. The initial value is 0.
        #

        # Send the data over.  GL_STATIC_DRAW means that we don't expect to change the contents of the
        # vertex buffer frequently.  There are other options, take a look at the opengl docs.
        # These options are basically hints to the opengl driver, so that it can put the data
        # on the graphic card's GPU memory in an efficient place.  I don't know the implementation
        # details of how drivers utilize this information.
        glBufferData(GL_ARRAY_BUFFER,
                     glfloat_size * np.size(vertices),
                     vertices,
                     GL_STATIC_DRAW)


        # Do the same thing for the colors
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

    # destructor
    def __del__(self):
        # when the object is deleted, delete the VAO and VBO
        glDeleteVertexArrays(1, [self.vao])
        glDeleteBuffers(1, [self.vbo])
        # It would be more efficient to have muliple paddles use
        # just one program.  For the ease of implementation and
        # understanding, each object gets its own copy of the program
        glDeleteProgram(self.shader)

    def render(self):
        # active the program
        glUseProgram(self.shader)
        # bind the VAO, so that all of the linkages to the shader
        # are active
        glBindVertexArray(self.vao)

        # uniform variables within the shader are how we pass
        # in data that doesn't vary vertex to vertex.

        # pass projection parameters to the shader
        # (it would be more efficient to get these locs
        #  when we set up the VAO.  I put the code here for
        #  clarity)
        fov_loc = glGetUniformLocation(self.shader, "fov");
        # send 1 float into the shader, into the uniform fov
        glUniform1f(fov_loc, 45.0);
        aspect_loc = glGetUniformLocation(self.shader, "aspectRatio");
        glUniform1f(aspect_loc, width/height);
        # Here, I'm still using negative z values for nearZ and
        # farZ, because that's consistent both with the math that I've
        # taught you so far and with the right hand rule.
        # By the end of lesson 25, we will use positive nearZ
        # and farZ values, as is consistent with the "standard"
        # perspective projection matrix.
        nearZ_loc = glGetUniformLocation(self.shader, "nearZ");
        glUniform1f(nearZ_loc, -0.1);
        farZ_loc = glGetUniformLocation(self.shader, "farZ");
        glUniform1f(farZ_loc, -10000.0);

        # Here we have to send the modelview matrix over ourselves.
        # Unlike what you have learned in the OPenGL Superbible,
        # In Core Profile, there are very few predefined variables in shaders.
        mvMatrixLoc = glGetUniformLocation(self.shader, "mvMatrix")
        # ascontiguousarray puts the array in column major order
        glUniformMatrix4fv(mvMatrixLoc,
                           1,
                           GL_TRUE,
                           np.ascontiguousarray(
                               ms.getCurrentMatrix(
                                   ms.MatrixStack.modelview),
                               dtype=np.float32))
        # Invoke the shaders.  Linkages are already set up from the VBOs (via
        # the VAO), and from the
        # uniforms.
        # Vertex Data will come from the VBO
        # into the shader's "position" variable, which is defined
        # within the shader, and will need to output "gl_Position",
        # one of the few special variables in OpenGL 3.3 Core Profile
        # mode.

        glDrawArrays(GL_TRIANGLES,
                     0,
                     self.numberOfVertices)
        # unset the current VAO
        glBindVertexArray(0)


paddle1 = Paddle(r=0.578123,
                 g=0.0,
                 b=1.0,
                 initial_position=np.array([-90.0, 0.0, 0.0]))
paddle1.prepare_to_render()
paddle2 = Paddle(r=1.0,
                 g=0.0,
                 b=0.0,
                 initial_position=np.array([90.0, 0.0, 0.0]))
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
        paddle1.input_offset_y -= 10.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.input_offset_y += 10.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.input_offset_y -= 10.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.input_offset_y += 10.0

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


TARGET_FRAMERATE = 60 # fps


time_at_beginning_of_previous_frame = glfw.get_time()


while not glfw.window_should_close(window):
    while glfw.get_time() < time_at_beginning_of_previous_frame +  1.0/TARGET_FRAMERATE:
        pass

    time_at_beginning_of_previous_frame = glfw.get_time()

    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


    ms.setToIdentityMatrix(ms.MatrixStack.model)
    ms.setToIdentityMatrix(ms.MatrixStack.view)
    ms.setToIdentityMatrix(ms.MatrixStack.projection)

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClearColor(0.0,  # r
                 0.0,  # g
                 0.0,  # b
                 1.0)  # a
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    handle_inputs()

    ms.rotate_x(ms.MatrixStack.view,
               -moving_camera_rot_x)
    ms.rotate_y(ms.MatrixStack.view,
               -moving_camera_rot_y)
    ms.translate(ms.MatrixStack.view,
                 -moving_camera_x,
                 -moving_camera_y,
                 -moving_camera_z)

    with ms.push_matrix(ms.MatrixStack.model):
        ms.translate(ms.MatrixStack.model,
                     paddle1.input_offset_x,
                     paddle1.input_offset_y,
                     0.0)
        ms.translate(ms.MatrixStack.model,
                     paddle1.initial_position[0],
                     paddle1.initial_position[1],
                     0.0)
        ms.rotate_z(ms.MatrixStack.model,
                   paddle1.rotation)
        # NEW
        paddle1.render()

        with ms.push_matrix(ms.MatrixStack.model):
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

            # NEW
            square.render()

    with ms.push_matrix(ms.MatrixStack.model):
        ms.translate(ms.MatrixStack.model,
                     paddle2.input_offset_x,
                     paddle2.input_offset_y,
                     0.0)
        ms.translate(ms.MatrixStack.model,
                     paddle2.initial_position[0],
                     paddle2.initial_position[1],
                     0.0)
        ms.rotate_z(ms.MatrixStack.model,
                   paddle2.rotation)
        # NEW
        paddle2.render()

    glfw.swap_buffers(window)


glfw.terminate()
