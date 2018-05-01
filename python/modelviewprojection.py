#Book licensed under Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)
#https://creativecommons.org/licenses/by-nc-sa/4.0/

#Generated graphics Python code licensed under Apache 2.0 license

#Copyright (c) 2017-2018 William Emerison Six


import sys
import os
import OpenGL.GL as gl
import numpy as np
import math
import glfw.glfw as glfw
import ctypes


if __name__ != '__main__':
    sys.exit(1)

# Initialize the library
if not glfw.glfwInit():
    sys.exit()

glfw.glfwWindowHint(glfw.GLFW_CONTEXT_VERSION_MAJOR,1)
glfw.glfwWindowHint(glfw.GLFW_CONTEXT_VERSION_MINOR,4)

# Create a windowed mode window and its OpenGL context
window = glfw.glfwCreateWindow(500,
                               500,
                               str.encode("pyNuklear demo - GLFW OpenGL2"),
                               None,
                               None)
if not window:
    glfw.glfwTerminate()
    sys.exit()

# Make the window's context current
glfw.glfwMakeContextCurrent(window)

# Install a key handler
def on_key(window, key, scancode, action, mods):
    if key == glfw.GLFW_KEY_ESCAPE and action == glfw.GLFW_PRESS:
        glfw.glfwSetWindowShouldClose(window,1)
glfw.glfwSetKeyCallback(window, on_key)

gl.glClearColor(0.0,
                0.0,
                0.0,
                1.0)
gl.glClearDepth(-1.0)
gl.glDepthFunc(gl.GL_GREATER)
gl.glEnable(gl.GL_BLEND)
gl.glBlendFunc(gl.GL_SRC_ALPHA,
               gl.GL_ONE_MINUS_SRC_ALPHA)
gl.glEnable(gl.GL_DEPTH_TEST)

gl.glMatrixMode(gl.GL_PROJECTION);
gl.glLoadIdentity();
gl.glMatrixMode(gl.GL_MODELVIEW);
gl.glLoadIdentity();


def main_loop():
    # Loop until the user closes the window
    while not glfw.glfwWindowShouldClose(window):
        # Poll for and process events
        glfw.glfwPollEvents()

        width, height = glfw.glfwGetFramebufferSize(window)
        gl.glViewport(0, 0, width, height)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # currently undefined, but will be before the event loop is called
        render_scene()

        # done with frame, flush and swap buffers
        # Swap front and back buffers
        glfw.glfwSwapBuffers(window)

    glfw.glfwTerminate()

def demo1():
    # The baseline behavior.  A black screen.
    pass

def demo2():
    gl.glColor3f(1.0, #r
                 1.0, #g
                 1.0) #b
    gl.glBegin(gl.GL_QUADS)
    gl.glVertex2f(-1.0, #x
                  -0.3) #y
    gl.glVertex2f(-0.8, #x
                  -0.3) #y
    gl.glVertex2f(-0.8, #x
                  0.3)  #y
    gl.glVertex2f(-1.0, #x
                  0.3)  #y
    gl.glEnd();

    gl.glColor3f(1.0,
                 1.0,
                 0.0)
    gl.glBegin(gl.GL_QUADS)

    gl.glVertex2f(0.8,
                  -0.3)
    gl.glVertex2f(1.0,
                  -0.3)
    gl.glVertex2f(1.0,
                  0.3)
    gl.glVertex2f(0.8,
                  0.3)
    gl.glEnd()


def draw_in_square_viewport():

    gl.glClearColor(0.2, #r
                    0.2, #g
                    0.2, #b
                    1.0) #a
    gl.glClear(gl.GL_COLOR_BUFFER_BIT);

    width, height = glfw.glfwGetFramebufferSize(window)
    gl.glViewport(0, 0, width, height)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    min = width if width < height else height

    gl.glViewport(int(0.0 + (width - min)/2.0),  #min x
                  int(0.0 + (height - min)/2.0), #min y
                  min,                           #width x
                  min)                           #width y

    gl.glEnable(gl.GL_SCISSOR_TEST);
    gl.glScissor(int(0.0 + (width - min)/2.0),  #min x
                 int(0.0 + (height - min)/2.0), #min y
                 min,                           #width x
                 min)                           #width y

    gl.glClearColor(0.0, #r
                    0.0, #g
                    0.0, #b
                    1.0) #a
    gl.glClear(gl.GL_COLOR_BUFFER_BIT);
    gl.glDisable(gl.GL_SCISSOR_TEST);


def demo3():
    draw_in_square_viewport()
    demo2()


paddle_1_offset_Y = 0.0;
paddle_2_offset_Y = 0.0;

# will be overridden per demo
def handle_inputs():
    global paddle_1_offset_Y, paddle_2_offset_Y

    if glfw.glfwGetKey(window, glfw.GLFW_KEY_S) == glfw.GLFW_PRESS:
        paddle_1_offset_Y -= 0.1
    if glfw.glfwGetKey(window, glfw.GLFW_KEY_W) == glfw.GLFW_PRESS:
        paddle_1_offset_Y += 0.1
    if glfw.glfwGetKey(window, glfw.GLFW_KEY_K) == glfw.GLFW_PRESS:
        paddle_2_offset_Y -= 0.1
    if glfw.glfwGetKey(window, glfw.GLFW_KEY_I) == glfw.GLFW_PRESS:
        paddle_2_offset_Y += 0.1


def demo4():
    draw_in_square_viewport()
    handle_inputs()

    gl.glColor3f(1.0, #r
                 1.0, #g
                 1.0) #b
    gl.glBegin(gl.GL_QUADS)
    gl.glVertex2f(-1.0, #x
                  -0.3+paddle_1_offset_Y) #y
    gl.glVertex2f(-0.8, #x
                  -0.3+paddle_1_offset_Y) #y
    gl.glVertex2f(-0.8, #x
                  0.3+paddle_1_offset_Y)  #y
    gl.glVertex2f(-1.0, #x
                  0.3+paddle_1_offset_Y)  #y
    gl.glEnd();



    gl.glColor3f(1.0,
                 1.0,
                 0.0)
    gl.glBegin(gl.GL_QUADS)

    gl.glVertex2f(0.8,
                  -0.3+paddle_2_offset_Y)
    gl.glVertex2f(1.0,
                  -0.3+paddle_2_offset_Y)
    gl.glVertex2f(1.0,
                  0.3+paddle_2_offset_Y)
    gl.glVertex2f(0.8,
                  0.3+paddle_2_offset_Y)
    gl.glEnd()

class Vertex:
    def __init__(self,x,y):
        self.x = x
        self.y = y

# add translate method to Vertex
def translate(self, x, y):
    return Vertex(x=self.x + x, y=self.y + y)
Vertex.translate = translate

# add scale method to Vertex
def scale(self, x, y):
    return Vertex(x=self.x * x, y=self.y * y)

Vertex.scale = scale

# add rotate method to Vertex
def rotate(self,angle_in_radians):
    return Vertex(x= self.x * math.cos(angle_in_radians) - self.y * math.sin(angle_in_radians),
                  y= self.x * math.sin(angle_in_radians) + self.y * math.cos(angle_in_radians))

Vertex.rotate = rotate

# add rotate around method to Vertex
def rotate_around(angle_in_radians, center):
    translateToCenter = translate(-center.x,
                                  -center.y)
    rotatedAroundOrigin = translateToCenter.rotate(angle_in_radians)
    backToCenter = rotatedAroundOrigin.translate(center.x,
                                                 center.y)
    return backToCenter

Vertex.rotate_around = rotate_around

paddle = [Vertex(x=-0.1, y=-0.3),
          Vertex(x= 0.1, y=-0.3),
          Vertex(x= 0.1, y=0.3),
          Vertex(x=-0.1, y=0.3)]

def demo5():
    draw_in_square_viewport()
    handle_inputs()

    gl.glColor3f(1.0, #r
                 1.0, #g
                 1.0) #b
    gl.glBegin(gl.GL_QUADS)
    for v in paddle:
        newPosition = v.translate(x=-0.9,
                                  y=paddle_1_offset_Y);
        gl.glVertex2f(newPosition.x,
                      newPosition.y)
    gl.glEnd()


    gl.glColor3f(1.0, #r
                 1.0, #g
                 0.0) #b
    gl.glBegin(gl.GL_QUADS)
    for v in paddle:
        newPosition = v.translate(x=0.9,
                                  y=paddle_2_offset_Y);
        gl.glVertex2f(newPosition.x,
                      newPosition.y)
    gl.glEnd()



render_scene = demo5
main_loop()
