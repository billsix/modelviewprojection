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
                            "ModelViewProjection Demo 17",
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

glClearDepth(-1.0)
glDepthFunc(GL_GREATER)
glEnable(GL_DEPTH_TEST)

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
    def __init__(self,x,y,z):
        self.x = x
        self.y = y
        self.z = z

    def translate(self, tx, ty, tz):
        return Vertex(x=self.x + tx,
                      y=self.y + ty,
                      z=self.z + tz)

    def rotate_x(self, angle_in_radians):
        return Vertex(x=self.x,
                      y=self.y*math.cos(angle_in_radians) - self.z*math.sin(angle_in_radians),
                      z=self.y*math.sin(angle_in_radians) + self.z*math.cos(angle_in_radians))

    def rotate_y(self, angle_in_radians):
        return Vertex(x=self.z*math.sin(angle_in_radians) + self.x*math.cos(angle_in_radians),
                      y=self.y,
                      z=self.z*math.cos(angle_in_radians) - self.x*math.sin(angle_in_radians))

    def rotate_z(self, angle_in_radians):
        return Vertex(x=self.x*math.cos(angle_in_radians) - self.y*math.sin(angle_in_radians),
                      y=self.x*math.sin(angle_in_radians) + self.y*math.cos(angle_in_radians),
                      z=self.z)

    def scale(self, scale_x, scale_y, scale_z):
        return Vertex(x=self.x * scale_x,
                      y=self.y * scale_y,
                      z=self.z * scale_z)

    def ortho(self,
              min_x,
              max_x,
              min_y,
              max_y,
              min_z,
              max_z):
        x_length = max_x-min_x
        y_length = max_y-min_y
        z_length = max_z-min_z
        return self.translate(tx=-(max_x-x_length/2.0),
                              ty=-(max_y-y_length/2.0),
                              tz=-(max_z-z_length/2.0)) \
                   .scale(1/(x_length/2.0),
                          1/(y_length/2.0),
                          1/(-z_length/2.0))

    def perspective(self, fov, aspectRatio, nearZ, farZ):
        top = math.fabs(nearZ) * math.tan(math.radians(fov)/ 2.0)
        right = top * aspectRatio

        sheared_x = self.x / math.fabs(self.z) * math.fabs(nearZ)
        sheared_y = self.y / math.fabs(self.z) * math.fabs(nearZ)
        projected =  Vertex(sheared_x,
                            sheared_y,
                            self.z)
        return projected.ortho(min_x= -right,
                               max_x= right,
                               min_y= -top,
                               max_y= top,
                               min_z= nearZ,
                               max_z= farZ)


    def camera_space_to_ndc_space_fn(self):
        return self.perspective(fov=45.0,
                                aspectRatio=width / height,
                                nearZ=-0.1,
                                farZ=-10000.0)


class Paddle:
    def __init__(self,vertices, r, g, b, global_position, rotation=0.0, offset_x=0.0, offset_y=0.0):
        self.vertices = vertices
        self.r = r
        self.g = g
        self.b = b
        self.rotation = rotation
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.global_position = global_position

    def draw(self):
        glColor3f(self.r,
                  self.g,
                  self.b)

        glBegin(GL_QUADS)
        for model_space in self.vertices:
            world_space = apply_stack(model_space, model_stack)
            camera_space = apply_stack(world_space, view_stack)
            ndc_space = apply_stack(camera_space, projection_stack)
            glVertex3f(ndc_space.x,
                       ndc_space.y,
                       ndc_space.z)
        glEnd()


paddle1 = Paddle(vertices=[Vertex(x=-10.0, y=-30.0, z=0.0),
                           Vertex(x= 10.0, y=-30.0, z=0.0),
                           Vertex(x= 10.0, y= 30.0, z=0.0),
                           Vertex(x=-10.0, y=30.0,  z=0.0)],
                 r=0.578123,
                 g=0.0,
                 b=1.0,
                 global_position=Vertex(x=-90.0,y=0.0,z=0.0))

paddle2 = Paddle(vertices=[Vertex(x=-10.0, y=-30.0, z=0.0),
                           Vertex(x= 10.0, y=-30.0, z=0.0),
                           Vertex(x= 10.0, y= 30.0, z=0.0),
                           Vertex(x=-10.0, y=30.0,  z=0.0)],
                 r=1.0,
                 g=0.0,
                 b=0.0,
                 global_position=Vertex(x=90.0,y=0.0,z=0.0))

moving_camera_x = 0.0
moving_camera_y = 0.0
moving_camera_z = 400.0
moving_camera_rot_y = 0.0
moving_camera_rot_x = 0.0


square = [Vertex(x=-5.0, y=-5.0, z=0.0),
          Vertex(x= 5.0, y=-5.0, z=0.0),
          Vertex(x= 5.0, y= 5.0, z=0.0),
          Vertex(x=-5.0, y=5.0,  z=0.0)]
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
        moving_camera_rot_x -= 0.03;
##//TODO -  explaing movement on XZ-plane
##//TODO -  show camera movement in graphviz
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        moving_camera_x -= move_multiple * math.sin(moving_camera_rot_y)
        moving_camera_z -= move_multiple * math.cos(moving_camera_rot_y)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        moving_camera_x += move_multiple * math.sin(moving_camera_rot_y);
        moving_camera_z += move_multiple * math.cos(moving_camera_rot_y);

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



projection_stack = []
view_stack = []
model_stack = []

def apply_stack(vertex, stack):
    v = vertex
    for fn in reversed(stack):
        v = fn(v)
    return v

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


    # every object uses the same projection
    projection_stack.append(lambda v: v.camera_space_to_ndc_space_fn())

    # every object is from the same view
    # Unlike in previous demos, because the transformations
    # are on a stack, the fns on the view stack need to
    # be read in reverse
    view_stack.append(lambda v: v.rotate_x( -moving_camera_rot_x))
    view_stack.append(lambda v: v.rotate_y( -moving_camera_rot_y))
    view_stack.append(lambda v: v.translate(tx=-moving_camera_x,
                                            ty=-moving_camera_y,
                                            tz=-moving_camera_z))

    # draw paddle 1
    # Unlike in previous demos, because the transformations
    # are on a stack, the fns on the model stack can
    # be read forwards, where each operation translates/rotates/scales
    # the current space
    model_stack.append(lambda v: v.translate(tx=paddle1.offset_x,
                                             ty=paddle1.offset_y,
                                             tz=0.0))
    model_stack.append(lambda v: v.translate(tx=paddle1.global_position.x,
                                             ty=paddle1.global_position.y,
                                             tz=0.0))
    model_stack.append(lambda v: v.rotate_z(paddle1.rotation))

    paddle1.draw()


    # draw the square
    glColor3f(0.0, #r
              0.0, #g
              1.0) #b

    # since the modelstack is already in paddle1's space
    # just add the transformations relative to it
    # before paddle 2 is drawn, we need to remove
    # the square's 3 model_space transformations
    model_stack.append(lambda v: v.translate(tx=0.0, ty=0.0, tz=-10.0))
    model_stack.append(lambda v: v.rotate_z(rotation_around_paddle1))
    model_stack.append(lambda v: v.translate(tx=20.0, ty=0.0, tz=0.0))
    model_stack.append(lambda v: v.rotate_z(square_rotation))

    glBegin(GL_QUADS)
    for model_space in square:
        world_space = apply_stack(model_space, model_stack)
        camera_space = apply_stack(world_space, view_stack)
        ndc_space = apply_stack(camera_space, projection_stack)

        glVertex3f(ndc_space.x,
                   ndc_space.y,
                   ndc_space.z)
    glEnd()
    model_stack.pop()
    model_stack.pop()
    model_stack.pop()


    # since paddle2's model_space is independent of paddle 1's space
    # just clear the stack
    model_stack.clear()

    # draw paddle 2
    model_stack.append(lambda v: v.translate(tx=paddle2.offset_x,
                                             ty=paddle2.offset_y,
                                             tz=0.0))
    model_stack.append(lambda v: v.translate(tx=paddle2.global_position.x,
                                             ty=paddle2.global_position.y,
                                             tz=0.0))
    model_stack.append(lambda v: v.rotate_z(paddle2.rotation))
    paddle2.draw()


    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)

    projection_stack.clear()
    view_stack.clear()
    model_stack.clear()



glfw.terminate()
