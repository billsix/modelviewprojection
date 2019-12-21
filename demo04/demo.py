import sys
import os
import numpy as np
import math
from OpenGL.GL import *
import glfw

if not glfw.init():
    sys.exit()

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR,1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR,4)

window = glfw.create_window(500,
                            500,
                            "ModelViewProjection Demo 4",
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
        glfw.set_window_should_close(window,1)
glfw.set_key_callback(window, on_key)

glClearColor(0.0,
             0.0,
             0.0,
             1.0)

glEnable(GL_BLEND)

glBlendFunc(GL_SRC_ALPHA,
            GL_ONE_MINUS_SRC_ALPHA)

glMatrixMode(GL_PROJECTION);
glLoadIdentity();
glMatrixMode(GL_MODELVIEW);
glLoadIdentity();


def draw_in_square_viewport():

    glClearColor(0.2, #r
                 0.2, #g
                 0.2, #b
                 1.0) #a
    glClear(GL_COLOR_BUFFER_BIT)

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    min = width if width < height else height

    glViewport(int(0.0 + (width - min)/2.0),  #min x
               int(0.0 + (height - min)/2.0), #min y
               min,                           #width x
               min)                           #width y

    glEnable(GL_SCISSOR_TEST)
    glScissor(int(0.0 + (width - min)/2.0),  #min x
              int(0.0 + (height - min)/2.0), #min y
              min,                           #width x
              min)                           #width y

    glClearColor(0.0, #r
                 0.0, #g
                 0.0, #b
                 1.0) #a
    glClear(GL_COLOR_BUFFER_BIT)
    glDisable(GL_SCISSOR_TEST)



class Vertex:
    def __init__(self,x,y):
        self.x = x
        self.y = y

class Paddle:
    def __init__(self,vertices, r, g, b, offset_x=0.0, offset_y=0.0):
        self.vertices = vertices
        self.r = r
        self.g = g
        self.b = b
        self.offset_x = offset_x
        self.offset_y = offset_y


paddle1 = Paddle(vertices=[Vertex(-1.0,-0.3),
                           Vertex(-0.8,-0.3),
                           Vertex(-0.8,0.3),
                           Vertex(-1.0,0.3)],
                 r=0.578123,
                 g=0.0,
                 b=1.0)

paddle2 = Paddle(vertices=[Vertex(0.8,-0.3),
                           Vertex(1.0,-0.3),
                           Vertex(1.0,0.3),
                           Vertex(0.8,0.3)],
                 r=1.0,
                 g=0.0,
                 b=0.0)


def handle_movement_of_paddles():
    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.offset_y -= 0.1
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.offset_y += 0.1
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.offset_y -= 0.1
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.offset_y += 0.1


# Loop until the user closes the window
while not glfw.window_should_close(window):
    # Poll for and process events
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # render scene
    draw_in_square_viewport()
    handle_movement_of_paddles()

    # draw paddle 1
    glColor3f(paddle1.r,
              paddle1.g,
              paddle1.b)

    glBegin(GL_QUADS)
    for vertex in paddle1.vertices:
        glVertex2f(vertex.x,
                   vertex.y + paddle1.offset_y)
    glEnd()

    # draw paddle 2
    glColor3f(paddle2.r,
              paddle2.g,
              paddle2.b)

    glBegin(GL_QUADS)
    for vertex in paddle2.vertices:
        glVertex2f(vertex.x,
                   vertex.y + paddle2.offset_y)
    glEnd()




    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)

glfw.terminate()