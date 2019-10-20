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
                            "ModelViewProjection Demo 16",
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

    def perspective(self, nearZ, farZ):
        field_of_view =  math.radians(45.0/2.0)
        width, height = glfw.get_framebuffer_size(window)
        y_angle =  (width / height) * field_of_view


        sheared_x = self.x / math.fabs(self.z) * math.fabs(nearZ)
        sheared_y = self.y / math.fabs(self.z) * math.fabs(nearZ)
        projected =  Vertex(sheared_x,
                            sheared_y,
                            self.z)

        x_min_of_box = math.fabs(nearZ) * math.tan(field_of_view)
        y_min_of_box = math.fabs(nearZ) * math.tan(y_angle)
        return projected.ortho(min_x= -x_min_of_box,
                               max_x= x_min_of_box,
                               min_y= -y_min_of_box,
                               max_y= y_min_of_box,
                               min_z= nearZ,
                               max_z= farZ)


    def camera_space_to_ndc_space_fn(self):
        return self.perspective(-0.1, -10000.0)


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
            world_space = model_space.rotate_z(self.rotation) \
                                     .translate(tx=self.global_position.x,
                                                ty=self.global_position.y,
                                                tz=0.0) \
                                     .translate(tx=self.offset_x,
                                                ty=self.offset_y,
                                                tz=0.0)

            camera_space = world_space.translate(tx=-moving_camera_x,
                                                 ty=-moving_camera_y,
                                                 tz=-moving_camera_z) \
                                      .rotate_y( -moving_camera_rot_y) \
                                      .rotate_x( -moving_camera_rot_x)
            ndc_space = camera_space.camera_space_to_ndc_space_fn()
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

    paddle1.draw()

    glColor3f(0.0, #r
              0.0, #g
              1.0) #b
    glBegin(GL_QUADS)
    for model_space in square:
        paddle_1_space = model_space.rotate_z(square_rotation) \
                                    .translate(tx=20.0, ty=0.0, tz=0.0) \
                                    .rotate_z(rotation_around_paddle1)
        world_space = paddle_1_space.rotate_z(paddle1.rotation) \
                                    .translate(tx=paddle1.global_position.x,
                                               ty=paddle1.global_position.y,
                                               tz=0.0) \
                                    .translate(tx=paddle1.offset_x,
                                               ty=paddle1.offset_y,
                                               tz=-10.0) # TODO - explain why this should be visible

        camera_space = world_space.translate(tx=-moving_camera_x,
                                             ty=-moving_camera_y,
                                             tz=-moving_camera_z) \
                                  .rotate_y( -moving_camera_rot_y) \
                                  .rotate_x( -moving_camera_rot_x)
        ndc_space = camera_space.camera_space_to_ndc_space_fn()
        glVertex3f(ndc_space.x,
                   ndc_space.y,
                   ndc_space.z)
    glEnd()

    paddle2.draw()

    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)

glfw.terminate()
