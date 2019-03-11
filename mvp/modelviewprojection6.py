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
                            "ModelViewProjection",
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

    def translate(self, tx, ty):
        return Vertex(x=self.x + tx, y=self.y + ty)

    def scale(self, x, y):
        return Vertex(x=self.x * x, y=self.y * y)


class Paddle:
    def __init__(self,vertices, r, g, b, globalPosition, offsetX=0.0, offsetY=0.0):
        self.vertices = vertices
        self.r = r
        self.g = g
        self.b = b
        self.offsetX = offsetX
        self.offsetY = offsetY
        self.globalPosition = globalPosition

    def draw(self):
        glColor3f(self.r,
                  self.g,
                  self.b)

        glBegin(GL_QUADS)
        for modelspace in self.vertices:
            worldSpace = modelspace.translate(tx=self.globalPosition.x,
                                              ty=self.globalPosition.y) \
                                   .translate(tx=self.offsetX,
                                              ty=self.offsetY)

            ndcSpace = worldSpace.scale(x=1.0/100.0,
                                        y=1.0/100.0)
            glVertex2f(ndcSpace.x,
                       ndcSpace.y)
        glEnd()


paddle1 = Paddle(vertices=[Vertex(x=-10.0, y=-30.0),
                           Vertex(x= 10.0, y=-30.0),
                           Vertex(x= 10.0, y=30.0),
                           Vertex(x=-10.0, y=30.0)],
                 r=0.578123,
                 g=0.0,
                 b=1.0,
                 globalPosition=Vertex(-90.0,0.0))

paddle2 = Paddle(vertices=[Vertex(x=-10.0, y=-30.0),
                           Vertex(x= 10.0, y=-30.0),
                           Vertex(x= 10.0, y=30.0),
                           Vertex(x=-10.0, y=30.0)],
                 r=1.0,
                 g=0.0,
                 b=0.0,
                 globalPosition=Vertex(90.0,0.0))


def handle_movement_of_paddles():
    global paddle1, paddle2

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        paddle1.offsetY -= 10.0
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        paddle1.offsetY += 10.0
    if glfw.get_key(window, glfw.KEY_K) == glfw.PRESS:
        paddle2.offsetY -= 10.0
    if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
        paddle2.offsetY += 10.0



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

    paddle1.draw()
    paddle2.draw()


    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)

glfw.terminate()
