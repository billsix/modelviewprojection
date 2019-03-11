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

# Loop until the user closes the window
while not glfw.window_should_close(window):
    # Poll for and process events
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # render scene
    # draw paddle 1
    glColor3f(0.578123, #r
              0.0,      #g
              1.0)      #b
    glBegin(GL_QUADS)
    glVertex2f(-1.0, #x
               -0.3) #y
    glVertex2f(-0.8, #x
               -0.3) #y
    glVertex2f(-0.8, #x
               0.3)  #y
    glVertex2f(-1.0, #x
               0.3)  #y
    glEnd()
    # draw paddle 2
    glColor3f(1.0,
              0.0,
              0.0)
    glBegin(GL_QUADS)

    glVertex2f(0.8,
               -0.3)
    glVertex2f(1.0,
               -0.3)
    glVertex2f(1.0,
               0.3)
    glVertex2f(0.8,
               0.3)
    glEnd()


    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)

glfw.terminate()
