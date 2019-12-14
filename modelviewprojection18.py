import sys
import os
import numpy as np
import math
from OpenGL.GL import *
from OpenGL.GLU import *
import glfw
import pyMatrixStack as ms

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)

window = glfw.create_window(500,
                            500,
                            "ModelViewProjection Demo 18",
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

glEnable(GL_BLEND)

glBlendFunc(GL_SRC_ALPHA,
            GL_ONE_MINUS_SRC_ALPHA)

# NEW - TODO - talk about opengl matricies and z pos/neg
glEnable(GL_DEPTH_TEST)
glClearDepth(1.0)
glDepthFunc(GL_LEQUAL)



def draw_in_square_viewport():

    glClearColor(0.2,  # r
                 0.2,  # g
                 0.2,  # b
                 1.0)  # a
    glClear(GL_COLOR_BUFFER_BIT)

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    min = width if width < height else height

    glViewport(int(0.0 + (width - min)/2.0),  # min x
               int(0.0 + (height - min)/2.0),  # min y
               min,  # width x
               min)  # width y

    glEnable(GL_SCISSOR_TEST)
    glScissor(int(0.0 + (width - min)/2.0),  # min x
              int(0.0 + (height - min)/2.0),  # min y
              min,  # width x
              min)  # width y

    glClearColor(0.0,  # r
                 0.0,  # g
                 0.0,  # b
                 1.0)  # a
    glClear(GL_COLOR_BUFFER_BIT)
    glDisable(GL_SCISSOR_TEST)




class Paddle:
    def __init__(self, r, g, b, global_position, rotation=0.0, offset_x=0.0, offset_y=0.0):
        self.r = r
        self.g = g
        self.b = b
        self.rotation = rotation
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.global_position = global_position
        self.vertices = np.array([[-10.0, -30.0,  0.0],
                                  [10.0,  -30.0,  0.0],
                                  [10.0,   30.0,  0.0],
                                  [-10.0,  30.0,  0.0]],
                                 dtype=np.float32)


paddle1 = Paddle(r=0.578123,
                 g=0.0,
                 b=1.0,
                 global_position=np.array([-90.0, 0.0, 0.0]))

paddle2 = Paddle(r=1.0,
                 g=0.0,
                 b=0.0,
                 global_position=np.array([90.0, 0.0, 0.0]))

moving_camera_x = 0.0
moving_camera_y = 0.0
moving_camera_z = 400.0
moving_camera_rot_y = 0.0
moving_camera_rot_x = 0.0


square_rotation = 0.0
rotation_around_paddle1 = 0.0


def handle_inputs():
    global rotation_around_paddle1
    if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
        rotation_around_paddle1 += 0.1

    global square_rotation
    if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
        square_rotation += 0.1

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

    # render scene
    draw_in_square_viewport()
    handle_inputs()

    ms.setToIdentityMatrix(ms.MatrixStack.model)
    ms.setToIdentityMatrix(ms.MatrixStack.view)
    ms.setToIdentityMatrix(ms.MatrixStack.projection)

    # set the projection matrix to be perspective
    ms.perspective(fov=45.0,
                   aspectRatio=width / height,
                   nearZ=0.1,
                   farZ=10000.0)
    glMatrixMode(GL_PROJECTION)
    # ascontiguousarray puts the array in column major order
    glLoadMatrixf(np.ascontiguousarray(ms.getCurrentMatrix(ms.MatrixStack.projection).T))

    # note - opengl matricies use degrees
    ms.rotate_x(ms.MatrixStack.view,-moving_camera_rot_x)
    ms.rotate_y(ms.MatrixStack.view,-moving_camera_rot_y)
    ms.translate(ms.MatrixStack.view,
                 -moving_camera_x,
                 -moving_camera_y,
                 -moving_camera_z)

    with ms.PushMatrix(ms.MatrixStack.model):

        # draw paddle 1
        # Unlike in previous demos, because the transformations
        # are on a stack, the fns on the model stack can
        # be read forwards, where each operation translates/rotates/scales
        # the current space
        glColor3f(paddle1.r,
                  paddle1.g,
                  paddle1.b)

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

        glMatrixMode(GL_MODELVIEW)
        # ascontiguousarray puts the array in column major order
        glLoadMatrixf(np.ascontiguousarray(ms.getCurrentMatrix(ms.MatrixStack.modelview).T))
        glBegin(GL_QUADS)
        for model_space in paddle1.vertices:
            glVertex3f(model_space[0],
                       model_space[1],
                       model_space[2])
        glEnd()

        # # draw the square
        glColor3f(0.0,  # r
                  0.0,  # g
                  1.0)  # b

        # since the modelstack is already in paddle1's space
        # just add the transformations relative to it
        # before paddle 2 is drawn, we need to remove
        # the square's 3 model_space transformations
        ms.translate(ms.MatrixStack.model,
                     0.0,
                     0.0,
                     -10.0)
        ms.rotate_z(ms.MatrixStack.model,
                    rotation_around_paddle1)
        ms.translate(ms.MatrixStack.model,
                     20.0,
                     0.0,
                     0.0)
        ms.rotate_z(ms.MatrixStack.model,
                    square_rotation)


        glMatrixMode(GL_MODELVIEW)
        # ascontiguousarray puts the array in column major order
        glLoadMatrixf(np.ascontiguousarray(ms.getCurrentMatrix(ms.MatrixStack.modelview).T))
        glBegin(GL_QUADS)
        for model_space in square_vertices:
            glVertex3f(model_space[0],
                       model_space[1],
                       model_space[2])
        glEnd()

    #get back to center of global space


    # draw paddle 2
    glColor3f(paddle2.r,
              paddle2.g,
              paddle2.b)

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

    glMatrixMode(GL_MODELVIEW)
    # ascontiguousarray puts the array in column major order
    glLoadMatrixf(np.ascontiguousarray(ms.getCurrentMatrix(ms.MatrixStack.modelview).T))
    glBegin(GL_QUADS)
    for model_space in paddle2.vertices:
        glVertex3f(model_space[0],
                   model_space[1],
                   model_space[2])
    glEnd()


    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)


glfw.terminate()
