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

# TODO -- this demo needs to be redone, as I'm mixing two different concepts,
# 1) poor depth management fixed in demo 15, 2) camera position/orientation in 3D space, and controls.
# Really, I should focus on 1), fix it in demo 15, and then make the subsequent demo
# on 2).  Apologies to the class, will do the best that I can in class, and will fix later.


# PURPOSE
#
# Do the same stuff as the previous demo, but use 3D coordinates,
# where the negative z axis goes into the screen (because
# of the right hand rule).  Use Ortho to put a rectangular prism
# into NDC.

# Things that this demo purposefully does poorly.  Show the demo and
# it's failures.
#
# 1) The blue square is always drawn, even
# when it's behind the purple paddle.  The solution will be
# zbuffering https://en.wikipedia.org/wiki/Z-buffering#Mathematics,
# and it is implemented in the next demo.
#
# 2) When moving front to back, parts of the geometry disappears.
#   This is because it gets "clipped out", as the geometry is outside
#   of NDC, (-1 to 1 on all three axis).  We could fix this by making
#   a bigger ortho rectangular prism, but because of problem 3, we'll
#   ignore that for now.
#
# 3) This doesn't look like a 3D application should, where further away
#  objects are smaller.  This will be fixed in 2 demos, demo16.
#
# FIRST - DISCUSS Z POSITION DATA, show that the square is always visible,
# and show the how the next demo fixes it.  Then move on to the next
# paragraph.
#
# PAUSE -- now that we have returned from demo 15, let's talk about
# 3d movement and camera controls!

# NEW CAMERA CONTROLS for up, left, down, right, page up, page down
# Camera now moves through the 3D world, as you would expect to see
# in any first person game, but very poorly as perspective is not
# taken into account.  (Perspective meaning that objects that are
# further away down the negative z axis appear smaller in terms
# of their x and y coordinate)
#
# The camera has an x,y,z position, and two rotations (one around
# the x axis, and one around the y axis).
#
# NOTE - the camera space transformtions are the most unintuitive aspects
# of graphics programming.  If you read the transformations
# here from top down, you are envisioning moving all of the objects
# in the scene, and that your camera is fixed, the diagram
# on the left side of the following image.
#
# eog ../images/demo10.png
#
# That is the equivalent of when driving, that your car is fixed,
# and that you are rotating the earth.  This way of thinking,
# may suffice to you, and if you can keep it straight, great.
# The camera isn't moving, everything else has a velocity
# that's in the opposite direction.
#
# If instead, you view that the camera is defined in terms of world
# space, and it's movement is relative to that world space, (the right
# diagram in demo10.png), then the intepretation is a bit harder.
# First, think of the transformations that put your camera in the
# correct position and orientation.  Write them down.
# 1) translate to the camera's position, using the actual position values
#  of camera position (not their negatives)
# 2) rotate around the y axis
# 3) rotate around the x axis
# The ordering of 1) before 2) and 3) should be clear, as
# we are imagining a coordinate system that moves, just
# like we do for the modelspace to world space transformations.
# The ordering of 2) and 3) is very important, and 2 rotations
# across different axises are not commutative.
# https://en.wikipedia.org/wiki/Commutative_property.
#
#
#     (Remember, read bottom up, just like the previous demos
#      for modelspace to worldspace data)
#
#        world_space = camera_space.rotate_x(moving_camera_rot_x)
#                                  .rotate_y(moving_camera_rot_y)
#                                  .translate(tx=moving_camera_x,
#                                             ty=moving_camera_y,
#                                             tz=moving_camera_z)


# We rotate on the y axis first, then the x axis. (described later)
#
# Try this.  Rotate your head to the right a little more that
# 45 degrees.  Now rotate your head back a little more than 45 degrees.
#
# Now, reset your head (glPopMatrix). Try rotating your head back 45 degrees.  Once it's there,
# rotate your head (not your neck), 45 degrees.  It's different, and uncomfortable!
#
# We rotate the camera by the y axis first, then by the relative x axis,
# for the same reason.
#
#
# Back to the point, we are envisioning the camera relative to the world
# space by making a moving coordinate system (composed of an origin, 1 unit
# in the "x" axis, 1 unit in the "y" axis, and 1 unit in the axis), where
# each subsequent transformation is relative to the previous coordinate system.
# (This system is beneficial btw because it allows us to think of one coordinate
# system at a time, and forget how we got there, (similar to a Markov process,
# https://en.wikipedia.org/wiki/Markov_chain))
#
# But that system of thinking works only when we are placing the camera into
# it's position/orientation.  Looking at the right hand picture of
# eog ../images/demo10.png
# thinking in this way would allow us to transform vertices defined in camera space
# to world space, just like the paddles/square.
#
# But we don't want that.  Instead, we want to take the modelspace geometry from,
# say Paddle1 space, to world space,
# and then to camera space (which is going in the opposite direction, therefore requires
# an inverse operation, just like in the univariate currency example from Bitcoin to Euro.
#
# eog ../images/currency.png
#
# Given that the inverse of a sequence of transformations is the sequence backwards,
# with each transformations inverted, we must do that to get from world space
# to camera space.
#
# If I tell you to take two steps to the left, rotate 90 degrees, and then reverse it,
# you'd rotate 90 degress in the opposite direction, and then take two steps to the right.
#
# (See https://en.wikipedia.org/wiki/Matrix_multiplication, under
#  the section on square matricies, which say that (A*B)^-1 = (B^-1) * (A^-1) )
#

# The inverted form is
#        camera_space = world_space.translate(tx=-moving_camera_x,
#                                             ty=-moving_camera_y,
#                                             tz=-moving_camera_z) \
#                                  .rotate_y( -moving_camera_rot_y) \
#                                  .rotate_x( -moving_camera_rot_x)

# Trying to reason about the camera's position and orientation is difficult.
# As such, in this demo, I have added the non-inverted transformations
# in the comments, but will not do so in subsequent demos.
#
#
#
# Before we start, take a look at ../mvpVisualization/demo.py
# to see the 3D geometry drawn both in world space and in their modelspace.
#
# To count in the modelspace, look at a given axis (which I've drawn in units
# of 10 for ease of viewing, although it should normally be in units of 1)
# On the red axis, it's 2*10 units wide, and 6*10 units tall, which matches
# the modelspace data in the constructor for the Paddles.
#
# Take a look at ../mvpVisualization/demoAnimation.py to see an animated
# version of the axis being moved from into their world space positions,
# relative to which the modelspace data is drawn.
#
# The gray axis in the middle happens when we hold onto the original
# axises, as we first draw paddle 1 relative to it, the square relative
# to paddle1, but we need to later get back to world space so that we
# can draw paddle2.  In later code, we will use glPushMatrix to
# save onto a copy of the current axises, and glPopMatrix to discard
# our "current at the time" axis, returning back to the saved axis.  Like a quicksave
# in a video game.
#
# To follow along with the code, read the transformations from modelspace
# to worldspace backwards, and you will see how the axises are moving and
# why.
#
# Take a look at ../mvpVisualization/demoViewWorldTopLevel.py to see an
# animated version that shows the objects being placed in world space,
# the camera being put into it's space using the normal way of thinking
# of a coordinate system being moved, but then the transformations
# are inverted, brining the objects in world space with it,
# in backwards order, to put the NDC cube defined in camera
# space to the NDC defined in world space.  One way to think of it,
# is that NDC is defined at the top level of the tree of transformations,
# so in world space.  We need to get the -1 to 1 space in x,y,z relative
# to camera space to match the -1 to 1 space in world space.
#
# eog ../images/demo10.png
#
# Why do we do this?  Because it doesn't matter how we think about
# the coordinate transformations, the computer will always execute
# the code from top down, take the resulting coordinates, and clip
# out anything outside of -1 to 1. So, world space. The computer has no notion
# of camera space, it's our own invention, so we need to get the coordinates
# that we care about into that space.

# After looking at the demos and explaining the code, now cover the camera movement code.

# Other things added
# Added rotations around the x axis, y axis, and z axis.
# https://en.wikipedia.org/wiki/Rotation_matrix
#
# Added translate in 3D.  Added scale in 3D.  These are just like
# the 2D versions, just with the same process applied to the z axis.
#
# They direction of the rotation is defined by the right hand rule.
#
# https://en.wikipedia.org/wiki/Right-hand_rule
#

#

# |=======================================
# |Keyboard Input |Action
# |w              |Move Left Paddle Up
# |s              |Move Left Paddle Down
# |i              |Move Right Paddle Up
# |k              |Move Right Paddle Down
# |               |
# |d              |Increase Left Paddle's Rotation
# |a              |Decrease Left Paddle's Rotation
# |l              |Increase Right Paddle's Rotation
# |j              |Decrease Right Paddle's Rotation
# |               |
# |q              |Rotate the square around it's center
# |e              |Rotate the square around paddle 1's center
# |               |
# TODO - fix this
# |UP             |Move the camera up, moving the objects down
# |DOWN           |Move the camera down, moving the objects up
# |LEFT           |Move the camera left, moving the objects right
# |RIGHT          |Move the camera right, moving the objects left
# |               |
# |PAGEUP         |
# |PAGEDOWN       |Move the camera down, moving the objects up

# |=======================================



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
                            "ModelViewProjection Demo 14",
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


glMatrixMode(GL_PROJECTION);
glLoadIdentity();
glMatrixMode(GL_MODELVIEW);
glLoadIdentity();


def draw_in_square_viewport():
    # clear to gray.
    glClearColor(0.2, #r
                 0.2, #g
                 0.2, #b
                 1.0) #a
    glClear(GL_COLOR_BUFFER_BIT)

    width, height = glfw.get_framebuffer_size(window)
    # figure out the minimum dimension of the window
    min = width if width < height else height

    # per pixel than just it's current color.
    glEnable(GL_SCISSOR_TEST)
    glScissor(int((width - min)/2.0),  #min x
              int((height - min)/2.0), #min y
              min,                     #width x
              min)                     #width y

    glClearColor(0.0, #r
                 0.0, #g
                 0.0, #b
                 1.0) #a
    # gl clear will only update the square to black values.
    glClear(GL_COLOR_BUFFER_BIT)
    # disable the scissor test, so now any opengl calls will
    # happen as usual.
    glDisable(GL_SCISSOR_TEST)

    # But, we only want to draw within the black square.
    # We set the viewport, so that the NDC coordinates
    # will be mapped the the region of screen coordinates
    # that we care about, which is the black square.
    glViewport(int(0.0 + (width - min)/2.0),  #min x
               int(0.0 + (height - min)/2.0), #min y
               min,                           #width x
               min)                           #width y


# NEW - 3 dimensions of data
class Vertex:
    def __init__(self,x,y,z):
        self.x = x
        self.y = y
        self.z = z

    def translate(self, tx, ty, tz):
        return Vertex(x=self.x + tx,
                      y=self.y + ty,
                      z=self.z + tz)

    # NEW - Rotations around an angle in 3D space follow the right hand rule
    #   With open palm, fingers on the x axis, rotating the fingers to y axis,
    # means that the positive z axis is in the direction of the thumb.  Positive Theta
    # moves in the direction that your fingers did.

    # starting on the y axis, rotating to z axis, thumb is on the positive x axis.

    # starting on the z axis, rotating to x axis, thumb is on the positive y axis.

    def rotate_x(self, angle_in_radians):
        return Vertex(x=self.x,
                      y=self.y*math.cos(angle_in_radians) - self.z*math.sin(angle_in_radians),
                      z=self.y*math.sin(angle_in_radians) + self.z*math.cos(angle_in_radians))

    def rotate_y(self, angle_in_radians):
        return Vertex(x=self.z*math.sin(angle_in_radians) + self.x*math.cos(angle_in_radians),
                      y=self.y,
                      z=self.z*math.cos(angle_in_radians) - self.x*math.sin(angle_in_radians))

    # NEW - this is the rotate that we used in the previous demo, but generarlized to 3D space.
    def rotate_z(self, angle_in_radians):
        return Vertex(x=self.x*math.cos(angle_in_radians) - self.y*math.sin(angle_in_radians),
                      y=self.x*math.sin(angle_in_radians) + self.y*math.cos(angle_in_radians),
                      z=self.z)

    def scale(self, scale_x, scale_y, scale_z):
        return Vertex(x=self.x * scale_x,
                      y=self.y * scale_y,
                      z=self.z * scale_z)

    # NEW - ortho takes an arbitrary rectangular prism, moves the center of it to NDC,
    # and scales the dimensions down to NDC, so that any objects within the rectangular
    # prism are visible within NDC.  Since this is a transformation that happens
    # from camera space to NDC, we can read them from top down.
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
                   # .scale(1.0/(x_length/2.0),
                   #        1.0/(y_length/2.0),
                   #        1.0/(-z_length/2.0))

    def camera_space_to_ndc_space_fn(self):
        return self.ortho(left= -100.0,
                          right= 100.0,
                          bottom= -100.0,
                          top= 100.0,
                          near= 100.0,
                          far= -100.0)


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
moving_camera_z = 40.0
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

    # NEW
    # The input for the camera is completely different
    move_multiple = 15.0
    # pressing right or left changs the rotation of the y axis,
    # making you look left or right
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        moving_camera_rot_y -= 0.03
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        moving_camera_rot_y += 0.03
    # pressing page up or page down changes how you'll rotate
    # on the relative x axis to look up or down, after
    # you've rotated left or right
    if glfw.get_key(window, glfw.KEY_PAGE_UP) == glfw.PRESS:
        moving_camera_rot_x += 0.03
    if glfw.get_key(window, glfw.KEY_PAGE_DOWN) == glfw.PRESS:
        moving_camera_rot_x -= 0.03;
    # up should make us move forward in the world
    # since our movement is constrained to the xz plane, for the purposes
    # of movement, we can ignore the moving_camera_rot_x, as that looks
    # up or down.
    # TODO - explain this better, with diagrams.
    # the gist is, you can imagine your camera in a local coordinate system,
    # like showed in the ../mvpVisualization/demoViewWorldTopLevel.py.
    # in that frame of reference (before rotating on the x axis),
    # moving forward means moving down
    # the local negative z axis.  Moving right means moving in the
    # local x axis.  These calculations convert our local x and z coordinates
    # from camera space into world space, so that the movements happen in world
    # space.
    # TODO - perhaps do that calculation of translating spaces by inverse operations,
    # as it will still work because we have not scaled nonuniformly.
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


    # draw paddle 1
    glColor3f(paddle1.r,
              paddle1.g,
              paddle1.b)
    glBegin(GL_QUADS)
    for model_space in paddle1.vertices:
        world_space = model_space.rotate_z(paddle1.rotation) \
                                 .translate(tx=paddle1.initial_position.x,
                                            ty=paddle1.initial_position.y,
                                            tz=0.0) \
                                 .translate(tx=paddle1.input_offset_x,
                                            ty=paddle1.input_offset_y,
                                            tz=0.0)

#   The camera's position would be placed here, but we need
#   to do the inverse transformation to get from worldspace
#   to camera space, from which NDC will be defined.
#                       world_space.rotate_x(moving_camera_rot_x)
#                                  .rotate_y(moving_camera_rot_y)
#                                  .translate(tx=moving_camera_x,
#                                             ty=moving_camera_y,
#                                             tz=moving_camera_z)
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

    # draw square
    glColor3f(0.0, #r
              0.0, #g
              1.0) #b
    glBegin(GL_QUADS)
    for model_space in square:
        paddle_1_space = model_space.rotate_z(square_rotation) \
                                    .translate(tx=20.0, ty=0.0, tz=0.0) \
                                    .rotate_z(rotation_around_paddle1) \
                                    .translate(tx=0.0,
                                               ty=0.0,
                                               tz=-10.0)
        # the square should not be visible when hidden behind the paddle1,
        # as we did a translate by -10.
        # this is because without depth buffering, the object drawn last
        # clobbers the color of any previously drawn object at the pixel.
        # Try moving the square drawing code to the beginning, and you will
        # see that the square can be hidden behind the paddle.
        world_space = paddle_1_space.rotate_z(paddle1.rotation) \
                                    .translate(tx=paddle1.initial_position.x,
                                               ty=paddle1.initial_position.y,
                                               tz=0.0) \
                                    .translate(tx=paddle1.input_offset_x,
                                               ty=paddle1.input_offset_y,
                                               tz=0.0)

#   The camera's position would be placed here, but we need
#   to do the inverse transformation to get from worldspace
#   to camera space, from which NDC will be defined.
#                       world_space.rotate_x(moving_camera_rot_x)
#                                  .rotate_y(moving_camera_rot_y)
#                                  .translate(tx=moving_camera_x,
#                                             ty=moving_camera_y,
#                                             tz=moving_camera_z)
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



    # draw paddle 2
    glColor3f(paddle2.r,
              paddle2.g,
              paddle2.b)
    glBegin(GL_QUADS)
    for model_space in paddle2.vertices:
        world_space = model_space.rotate_z(paddle2.rotation) \
                                 .translate(tx=paddle2.initial_position.x,
                                            ty=paddle2.initial_position.y,
                                            tz=0.0) \
                                 .translate(tx=paddle2.input_offset_x,
                                            ty=paddle2.input_offset_y,
                                            tz=0.0)

#   The camera's position would be placed here, but we need
#   to do the inverse transformation to get from worldspace
#   to camera space, from which NDC will be defined.
#                       world_space.rotate_x(moving_camera_rot_x)
#                                  .rotate_y(moving_camera_rot_y)
#                                  .translate(tx=moving_camera_x,
#                                             ty=moving_camera_y,
#                                             tz=moving_camera_z)
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

    # done with frame, flush and swap buffers
    # Swap front and back buffers
    glfw.swap_buffers(window)

glfw.terminate()
