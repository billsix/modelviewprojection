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

# PURPOSE
#
# Remove repetition in the coordinate transformations,
# as previous demos had very similar transformtions,
# especially from camera space to NDC space.
# Each node in the tree of the graph of objects (../images/demo11.png)
# should only be specified once.
#
# Noticing in the previous demos that the lower parts of the transformations
# have a common pattern, we can create a stack of functions for later application.
# Before drawing geometry, we add any functions to the top of the stack,
# apply all of our functions in the stack to our modelspace data to
# get NDC data,
# and before we return to the parent
# node, we pop the functions we added off of the stack, to ensure that
# we return the stack to the state that the parent node gave us.


# To explain in more detail ---
#
# What's the difference between drawing paddle 1 and the square?
#
# Here is paddle 1 code
# for model_space in paddle1.vertices:
#     world_space = model_space.rotate_z(paddle1.rotation) \
#                              .translate(tx=paddle1.initial_position.x,
#                                         ty=paddle1.initial_position.y,
#                                         tz=0.0) \
#                              .translate(tx=paddle1.input_offset_x,
#                                         ty=paddle1.input_offset_y,
#                                         tz=0.0)
#      camera_space = world_space.translate(tx=-moving_camera_x,
#                                          ty=-moving_camera_y,
#                                          tz=-moving_camera_z) \
#                               .rotate_y( -moving_camera_rot_y) \
#                               .rotate_x( -moving_camera_rot_x)
#     ndc_space = camera_space.camera_space_to_ndc_space_fn()

# Here is the square's code:
# for model_space in square:
#     paddle_1_space = model_space.rotate_z(square_rotation) \                 added
#                                 .translate(tx=20.0, ty=0.0, tz=0.0) \        added
#                                 .rotate_z(rotation_around_paddle1) \         added
#                                 .translate(tx=0.0,                           added
#                                            ty=0.0,                           added
#                                            tz=-10.0)                         added
#     world_space = paddle_1_space.rotate_z(paddle1.rotation) \                same
#                                 .translate(tx=paddle1.initial_position.x,    same
#                                            ty=paddle1.initial_position.y,    same
#                                            tz=0.0) \                         same
#                                 .translate(tx=paddle1.input_offset_x,        same
#                                            ty=paddle1.input_offset_y,        same
#                                            tz=-0.0)                          same
#      camera_space = world_space.translate(tx=-moving_camera_x,               same
#                                          ty=-moving_camera_y,                same
#                                          tz=-moving_camera_z) \              same
#                               .rotate_y( -moving_camera_rot_y) \             same
#                               .rotate_x( -moving_camera_rot_x)               same
#     ndc_space = camera_space.camera_space_to_ndc_space_fn()                  same


# The only difference is the square's model-space to paddle1 space.
# In a graphics program, because the scene is a hierarchy of relative
# objects, it's unwise to put this much repetition in the transformation
# sequence.  Especially if we might change how the camera operates,
# or from perspective to ortho.  It would required a lot of code changes.
# And I don't like reading from the bottom of the code up.  Code doesn't
# execute that way.  I want to read from top to bottom.

# When reading the transformation sequences from top down
# the transformation at the top is applied first, the transformation
# at the bottom is applied last, with the intermediate results method-chained together.
# (look up above for a reminder)

#
#  With a function stack, the function at the top of the stack (f5) is applied first,
#  the result of this is then given as input to f4 (second on the stack), all
#  the way down to f1, which was the first fn to be placed on the stack,
#  and as such, the last to be applied. (Last In First Applied - LIFA)
#
###### TOP OF STACK
#              |-------------------|
# (MODELSPACE) |                   |
#   (x,y,z)->  |       f5          |--
#              |-------------------| |
#                                    |
#           -------------------------
#           |
#           |  |-------------------|
#           |  |                   |
#            ->|       f4          |--
#              |-------------------| |
#                                    |
#           -------------------------
#           |
#           |  |-------------------|
#           |  |                   |
#            ->|       f3          |--
#              |-------------------| |
#                                    |
#           -------------------------
#           |
#           |  |-------------------|
#           |  |                   |
#            ->|       f2          |--
#              |-------------------| |
#                                    |
#           -------------------------
#           |
#           |  |-------------------|
#           |  |                   |
#            ->|       f1          |-->  (x,y,z) NDC
#              |-------------------|
###### BOTTOM OF STACK


# So, in order to ensure that the functions in a stack will execute
# in the same order as all of the previous demos, they need to
# push as listed below:

# Here is paddle 1 code
# for model_space in paddle1.vertices:
#     world_space = model_space.rotate_z(paddle1.rotation) \                push this seventh (because last in, first applied)
#                              .translate(tx=paddle1.initial_position.x,    push this sixth
#                                         ty=paddle1.initial_position.y,
#                                         tz=0.0) \
#                              .translate(tx=paddle1.input_offset_x,        push this fifth
#                                         ty=paddle1.input_offset_y,
#                                         tz=0.0)
#      camera_space = world_space.translate(tx=-moving_camera_x,            push this fourth
#                                          ty=-moving_camera_y,
#                                          tz=-moving_camera_z) \
#                               .rotate_y( -moving_camera_rot_y) \          push this third
#                               .rotate_x( -moving_camera_rot_x)            push this second
#     ndc_space = camera_space.camera_space_to_ndc_space_fn()               push this first  (because first in, last applied)





# Notice that we will now be pushing everything in reverse order,
# at least relative to how the previous demos have worked.
#
# This means that from modelspace to world space, we can now
# read the transformations FROM TOP TO BOTTOM (lexigraphically).  YEAH!!!!
#
# FUNCTION STACKS FTW!!!!!!!!!!  (I use function stacks to attempt to
#                                 transition to matricies, without having
#                                 to cover linear algebra material.  Matrix
#                                 stacks will be used in the same way
#                                 as this function stack is)
#



# Then, to draw the square relative to paddle one, those six
# transformations will already be on the stack, therefore
# only push the differences, and then apply the stack to
# the paddle's modelspace data

# Here is the square's code:
# for model_space in square:
#     paddle_1_space = model_space.rotate_z(square_rotation) \             push this eleventh
#                                 .translate(tx=20.0, ty=0.0, tz=0.0) \    push this tenth
#                                 .rotate_z(rotation_around_paddle1) \     push this ninth
#                                 .translate(tx=0.0,                       push this eigth
#                                            ty=0.0,
#                                            tz=-10.0)
#     world_space = paddle_1_space.rotate_z(paddle1.rotation) \             (nothing to push here or below,
#                                 .translate(tx=paddle1.initial_position.x, as they are already on the stack
#                                            ty=paddle1.initial_position.y,
#                                            tz=0.0) \
#                                 .translate(tx=paddle1.input_offset_x,
#                                            ty=paddle1.input_offset_y,
#                                            tz=-0.0)
#      camera_space = world_space.translate(tx=-moving_camera_x,
#                                          ty=-moving_camera_y,
#                                          tz=-moving_camera_z) \
#                               .rotate_y( -moving_camera_rot_y) \
#                               .rotate_x( -moving_camera_rot_x)
#     ndc_space = camera_space.camera_space_to_ndc_space_fn()
#     glVertex3f(ndc_space.x,
#                ndc_space.y,
#                ndc_space.z)

# when we have drawn the blue square, we are done drawing from
# this part of the tree, and need to go back up to world space
# eog ../images/demo11.png

# Therefore, we just need to pop off the correct number of
# functions, to just leave worldspace->cameraspace->ndc.
# Effectively, the following computation is all that
# will remain on the matrix stack.

#      camera_space = world_space.translate(tx=-moving_camera_x,
#                                          ty=-moving_camera_y,
#                                          tz=-moving_camera_z) \
#                               .rotate_y( -moving_camera_rot_y) \
#                               .rotate_x( -moving_camera_rot_x)
#     ndc_space = camera_space.camera_space_to_ndc_space_fn()

# We can then push the transformations from world space to
# paddle2 space, shown below.  Search for NEW to find the NEW CODE

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
    min = width if width < height else height

    glEnable(GL_SCISSOR_TEST)
    glScissor(int((width - min)/2.0),  #min x
              int((height - min)/2.0), #min y
              min,                     #width x
              min)                     #width y

    glClearColor(0.0, #r
                 0.0, #g
                 0.0, #b
                 1.0) #a
    glClear(GL_COLOR_BUFFER_BIT)
    glDisable(GL_SCISSOR_TEST)

    glViewport(int(0.0 + (width - min)/2.0),  #min x
               int(0.0 + (height - min)/2.0), #min y
               min,                           #width x
               min)                           #width y


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
              left,
              right,
              bottom,
              top,
              near,
              far):
        midpoint_x, midpoint_y, midpoint_z = (left+right)/2.0, (bottom + top)/2.0, (near+far)/2.0
        length_x, length_y, length_z = right - left, top - bottom, far - near
        return self.translate(tx=-midpoint_x,
                              ty=-midpoint_y,
                              tz=-midpoint_z) \
                   .scale(2.0/length_x,
                          2.0/length_y,
                          2.0/(-length_z))

    def perspective(self, fov, aspectRatio, nearZ, farZ):
        top = -nearZ * math.tan(math.radians(fov)/ 2.0)
        right = top * aspectRatio

        scaled_x = self.x * nearZ / self.z
        scaled_y = self.y * nearZ / self.z
        projected =  Vertex(scaled_x,
                            scaled_y,
                            self.z)
        return projected.ortho(left = -right,
                               right = right,
                               bottom = -top,
                               top = top,
                               near = nearZ,
                               far = farZ)


    def camera_space_to_ndc_space_fn(self):
        return self.perspective(fov=45.0,
                                aspectRatio=1.0,  #since the viewport is always square
                                nearZ=-0.1,
                                farZ=-10000.0)


class Paddle:
    def __init__(self,vertices, r, g, b, initial_position, rotation=0.0, input_offset_x=0.0, input_offset_y=0.0):
        self.vertices = vertices
        self.r = r
        self.g = g
        self.b = b
        self.rotation = rotation
        self.input_offset_x = input_offset_x
        self.input_offset_y = input_offset_y
        self.initial_position = initial_position


paddle1 = Paddle(vertices=[Vertex(x=-10.0, y=-30.0, z=0.0),
                           Vertex(x= 10.0, y=-30.0, z=0.0),
                           Vertex(x= 10.0, y= 30.0, z=0.0),
                           Vertex(x=-10.0, y=30.0,  z=0.0)],
                 r=0.578123,
                 g=0.0,
                 b=1.0,
                 initial_position=Vertex(x=-90.0,y=0.0,z=0.0))

paddle2 = Paddle(vertices=[Vertex(x=-10.0, y=-30.0, z=0.0),
                           Vertex(x= 10.0, y=-30.0, z=0.0),
                           Vertex(x= 10.0, y= 30.0, z=0.0),
                           Vertex(x=-10.0, y=30.0,  z=0.0)],
                 r=1.0,
                 g=0.0,
                 b=0.0,
                 initial_position=Vertex(x=90.0,y=0.0,z=0.0))

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
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        moving_camera_x -= move_multiple * math.sin(moving_camera_rot_y)
        moving_camera_z -= move_multiple * math.cos(moving_camera_rot_y)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        moving_camera_x += move_multiple * math.sin(moving_camera_rot_y);
        moving_camera_z += move_multiple * math.cos(moving_camera_rot_y);

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


# NEW - function stack.  The bottom of the stack has
# the low index, the top of the stack has the highest
# index
fn_stack = []

# NEW -
# Given an input vertex, apply the function at the top
# of the stack to the vertex, capture the output vertex,
# to be used as input to the next lower function on the
# stack.  Continue doing this until we get the value
# returned from the function at the bottom of the stack.
def apply_stack(vertex):
    v = vertex
    for fn in reversed(fn_stack):
        v = fn(v)
    return v


TARGET_FRAMERATE = 60 # fps

# to try to standardize on 60 fps, compare times between frames
time_at_beginning_of_previous_frame = glfw.get_time()

# Loop until the user closes the window
while not glfw.window_should_close(window):
    # poll the time to try to get a constant framerate
    while glfw.get_time() < time_at_beginning_of_previous_frame +  1.0/TARGET_FRAMERATE:
        pass
    # set for comparison on the next frame
    time_at_beginning_of_previous_frame = glfw.get_time()

    # Poll for and process events
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # render scene
    draw_in_square_viewport()
    handle_inputs()

    # NEW
    # In previous demos, camera_space_to_ndc_space_fn was always
    # the last function called by the computer.  put it on the bottom of the stack,
    # so that "apply_stack" calls this function last

    # "append" adds the function to the end of a list, where
    # we conisder the front of the list to be the bottom of the stack,
    # and the end of the list to be the top of the stack.

    # every object uses the same projection
    fn_stack.append(lambda v: v.camera_space_to_ndc_space_fn()) # (1)

    # NEW
    # Unlike in previous demos in which we read the transformations
    # from model space to world space backwards; because the transformations
    # are on a stack, the fns on the model stack can
    # be read forwards, where each operation translates/rotates/scales
    # the current space

    # The camera's position and orientation are defined relative
    # to world space like so, read top to bottom:

    # fn_stack.append(lambda v: v.translate(tx=moving_camera_x,
    #                                       ty=moving_camera_y,
    #                                       tz=moving_camera_z))
    # fn_stack.append(lambda v: v.rotate_y( moving_camera_rot_y))
    # fn_stack.append(lambda v: v.rotate_x( moving_camera_rot_x))

    # But, since we are dealing with world-space to camera space,
    # they must be inverted by reversing the order, and negating
    # the arguments

    # Therefore the transformations to put the world space into
    # camera space are.
    fn_stack.append(lambda v: v.rotate_x( -moving_camera_rot_x)) # (2)
    fn_stack.append(lambda v: v.rotate_y( -moving_camera_rot_y)) # (3)
    fn_stack.append(lambda v: v.translate(tx=-moving_camera_x,   # (4)
                                          ty=-moving_camera_y,
                                          tz=-moving_camera_z))


    # NEW
    # draw paddle 1
    # Unlike in previous demos in which we read the transformations
    # from model space to world space backwards; because the transformations
    # are on a stack, the fns on the model stack can
    # be read forwards, where each operation translates/rotates/scales
    # the current space
    fn_stack.append(lambda v: v.translate(tx=paddle1.input_offset_x, # (5) translate the local origin
                                          ty=paddle1.input_offset_y,
                                          tz=0.0))
    fn_stack.append(lambda v: v.translate(tx=paddle1.initial_position.x,  # (6) translate the local origin
                                          ty=paddle1.initial_position.y,
                                          tz=0.0))
    fn_stack.append(lambda v: v.rotate_z(paddle1.rotation)) # (7) (rotate around the local z axis

    # draw paddle 1
    # set the color
    glColor3f(paddle1.r,
              paddle1.g,
              paddle1.b)

    # NEW
    # specify that we are drawing a quadrilateral
    glBegin(GL_QUADS)
    for model_space in paddle1.vertices:
        # for each of the modelspace coordinates, apply all
        # of the procedures on the stack from top to bottom
        ndc_space = apply_stack(model_space)
        # this results in coordinate data in NDC space,
        # which we can pass to glVertex3f
        glVertex3f(ndc_space.x,
                   ndc_space.y,
                   ndc_space.z)
    glEnd()



    # NEW
    # draw the square
    glColor3f(0.0, #r
              0.0, #g
              1.0) #b

    # since the modelstack is already in paddle1's space,
    # and since the blue square is defined relative to paddle1,
    # just add the transformations relative to it
    # before the blue square is drawn.  Draw the square, and then
    # remove these 4 transformations from the stack (done below)
    fn_stack.append(lambda v: v.translate(tx=0.0, ty=0.0, tz=-10.0)) # (8)
    fn_stack.append(lambda v: v.rotate_z(rotation_around_paddle1)) # (9)
    fn_stack.append(lambda v: v.translate(tx=20.0, ty=0.0, tz=0.0)) # (10)
    fn_stack.append(lambda v: v.rotate_z(square_rotation)) # (11)

    # same as for paddle 1, apply the stack to get modelspace->ndc, call
    # glvertex on the result
    glBegin(GL_QUADS)
    for model_space in square:
        ndc_space = apply_stack(model_space)
        glVertex3f(ndc_space.x,
                   ndc_space.y,
                   ndc_space.z)
    glEnd()

    # NEW
    # Now we need to remove fns from the stack so that the
    # matrix stack would convert from world space to NDC.
    # This will allow us to just add the transformaions from
    # world space to paddle2 space on the stack.
    fn_stack.pop() # pop off (11)
    fn_stack.pop() # pop off (10)
    fn_stack.pop() # pop off (9)
    fn_stack.pop() # pop off (8)
    fn_stack.pop() # pop off (7)
    fn_stack.pop() # pop off (6)
    fn_stack.pop() # pop off (5)


    # NEW
    # since paddle2's model_space is independent of paddle 1's space, only
    # leave the view and projection fns (1) - (4)

    # draw paddle 2
    fn_stack.append(lambda v: v.translate(tx=paddle2.input_offset_x, # (12)
                                          ty=paddle2.input_offset_y,
                                          tz=0.0))
    fn_stack.append(lambda v: v.translate(tx=paddle2.initial_position.x,  # (13)
                                          ty=paddle2.initial_position.y,
                                          tz=0.0))
    fn_stack.append(lambda v: v.rotate_z(paddle2.rotation)) # (14)

    # NEW
    # draw paddle 2
    glColor3f(paddle2.r,
              paddle2.g,
              paddle2.b)

    glBegin(GL_QUADS)
    for model_space in paddle2.vertices:
        ndc_space = apply_stack(model_space)
        glVertex3f(ndc_space.x,
                   ndc_space.y,
                   ndc_space.z)
    glEnd()

    # remove all fns from the function stack, as the next frame will set them
    # clear makes the list empty, as the list (stack) will be repopulated
    # the next iteration of the event loop.
    fn_stack.clear()

    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)




glfw.terminate()
