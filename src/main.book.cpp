//Model View Projection
//====================
//Bill Six
//v1.0, 2017-
//:doctype: book
//
//[dedication]
//= Dedication
//
//To Teresa, Liam, Adam, and Kate.
//
//
//[preface]
//= Preface
//
//"I had no idea how much math was involved in computer graphics."
//
//Unfortunately many students of computer graphics come away with
//that impression, which this book attempts to remedy.  Creating basic
//2D and 3D
//graphics really only requires knowledge of high-school level
//geometry.  Based on that knowledge, this book builds both 2D and 3D
//applications from the ground up. 
//
//Thoughout the book, I show how to place objects in 3D,
//how to draw 3D objects relative to other objects, how to add a 
//camera which moves over time to the scene, and how to transform all
//that 3D data into the 2D coordinates
//of the computer screen.  By the end, you will understand the basics of
//how to create first-person
//and third-person games.  I made this book to show how to make the kind
//of graphics programs which programmers want to make, shown using
//math they aleady know.
//
//With that said, this books is purposely limited in scope, and
//the applications produced are not particurly pretty nor realistic-looking.
//For advanced graphics topics, you'll need to consult another reference.
//Although this book fills a huge gap that other books don't address,
//those other books are excellent reference books for advanced topics.
//
//
//
//:toc:
//
//[[intro]]
//= Introduction
//[[openWindow]]
//== Opening a Window
//
//
//The code for the entire book is contained within "main.cpp", licenced
//under the Apache 2.0 license.
//
//Include the necessary headers.
//
//[source,C,linenums]
//----
/*  src/main.cpp
 *
 * Copyright 2016-2017 - William Emerison Six
 * All rights reserved
 * main.cpp is Distributed under Apache 2.0
 */
#include <iostream>
#include <vector>
#include <functional>
#include <cmath>
#include "main.h"
//----
//
//In order to create graphics, first we need to be able to create a window.
//As OpenGL provides no window management,
//we will use Simple Direct-Media Layer, as it provides this functionality in a cross platform manner.
//
//
//Create a pointer for the window.  If you are new to C++, don't fret
//over what a pointer is.  The majority of the book doesn't use them.
//
//The author does not know what "glcontext" provides, other than it is necessary,
//so don't worry about it.
//
//[source,C,linenums]
//----
SDL_Window *window;
SDL_GLContext glcontext;
//----
//
//
//Use C linkage for main.  Knowing why isn't terribly important,
//but for the interested reader,
//<<linkageAppendix,the appendix>>  provides a description of
//C-linkage vs. C++ linkage.
//
//[source,C,linenums]
//----
#ifdef __cplusplus
extern "C"
#endif
int main(int argc, char *argv[])
{
//----
//== Let the User Pick the Demo to Run.
//[source,C,linenums]
//----
  std::cout << "Input demo number to run: (1-15): " << std::endl;
  int demo_number;
  std::cin >> demo_number ;
//----
//== SDL/OpenGL Initialization
//
//You don't really need to know what this code does yet.
//Later sections will explain pertinent parts.
//
//
//
//[source,C,linenums]
//----
  //initialize video support, joystick support, etc.
  if (SDL_Init(SDL_INIT_TIMER
               | SDL_INIT_AUDIO
               | SDL_INIT_VIDEO
               | SDL_INIT_EVENTS) != 0){
    SDL_LogMessage(SDL_LOG_CATEGORY_APPLICATION,
                   SDL_LOG_PRIORITY_ERROR,
                   "Error: %s\n",
                   SDL_GetError());
    return 1;
  }
  // Definetely need two buffers.  Who in their right mind
  // would use only one?
  SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1);
  // used later for depth testing, don't worry about it for now
  SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 24);
  // Stecils will not be covered in this book.
  SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE, 8);
  // OpenGL has had multiple versions, which vary in what the
  // provide.  Specify the version of OpenGL which we will
  // use

  // put the next few lines in only when running opengl 3.2+
  /* SDL_GL_SetAttribute(SDL_GL_CONTEXT_FLAGS, */
  /*                     SDL_GL_CONTEXT_FORWARD_COMPATIBLE_FLAG); */
  SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK,
                      SDL_GL_CONTEXT_PROFILE_COMPATIBILITY);
  SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 2);
  SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 1);
  // the following two lines are not important to discuss
  SDL_DisplayMode current;
  SDL_GetCurrentDisplayMode(0, &current);
//----
//Create a 500 pixel by 500 pixel window, which the user can resize.
//[source,C,linenums]
//----
  if(NULL == (window = SDL_CreateWindow("modelviewprojection",
                                        SDL_WINDOWPOS_CENTERED,
                                        SDL_WINDOWPOS_CENTERED,
                                        500,
                                        500,
                                        (SDL_WINDOW_OPENGL |
                                         SDL_WINDOW_RESIZABLE)))){
    // if a window can't be created, inform the user
    // and quit.
    SDL_LogMessage(SDL_LOG_CATEGORY_APPLICATION,
                   SDL_LOG_PRIORITY_ERROR,
                   "Could not create window: %s\n",
                   SDL_GetError());
    return 1;
  }
  glcontext = SDL_GL_CreateContext(window);
//----
//When distributing a native application which uses shared libraries,
//the procedure calls provided by the library are known at compile-time.
//Unlike typical shared libraries, OpenGL's shared library is providid
//to the user by the vendor of the graphics card, as
//different cards offer different functionality.
//"GLEW" is a project which allows us to use OpenGL nicely.  See
//<<sharedLibAppendix,the appendix>> for a more full explanantion.
//[source,C,linenums]
//----
  glewInit(); // make OpenGL calls possible
  SDL_GL_MakeCurrent(window,glcontext);
  // log opengl version
  SDL_LogMessage(SDL_LOG_CATEGORY_APPLICATION,
                 SDL_LOG_PRIORITY_INFO,
                 "OpenGL version loaded: %s\n",
                 glGetString(GL_VERSION));
//----
//For every frame drawn, each pixel has a default color, set by
//calling "glClearColor". "0,0,0,1", means black "0,0,0", without
//transparency (the "1").
//[source,C,linenums]
//----
  glClearColor(0,0,0,1);
//----
//== The Event Loop
//
//When you pause a movie, motion stops and you see one picture.
//The video for movies is a sequence of pictures, which when
//rendered in quick succession, provide the illusion of motion.
//
//Interactive computer graphics are rendered the same way,
//one "frame" at a time.
//
//Render a frame for the selected demo, swap the buffers
//footnote:[Because one "frame" is created incrementally, yet the
//user doesn't want half-drawn pictures on his monitor, the programmer
//must inform the graphics card when to "flush" the framebuffer
//(the array of pixels).  Flushing the framebuffer takes time,
//and should that call to flush the buffer "block", meaning
//it would not return until the flush is complete, we would
//have wasted CPU time.  To avoid wasting the CPU time,
//OpenGL has two "framebuffers".  "SDL_GL_SwapWindow" initializes the flushing
//the current buffer, switches the current writable framebuffer to the
//other one, thus allowing a non-blocking call.],
//and unless the user closed the window, repeat.
//
//[source,C,linenums]
//----
  SDL_bool quit = SDL_FALSE;
  do{
    quit = render_scene(&demo_number);
    SDL_GL_SwapWindow(window);
  } while (quit != SDL_TRUE);
//----
//== The User Closed the App, Cleanup After Yourself
//[source,C,linenums]
//----
  SDL_GL_DeleteContext(glcontext);
  SDL_DestroyWindow(window);
  SDL_Quit();
  return 0;
} // end main
//----
//== Render the Current Demo
//
//Regardless of which demo will be run, certain things need
//to happen every frame.  The default color of each pixel withith
//the current framebuffer needs
//to be reset to the current clear color.  If the window was
//resized, it should act correctly
//
//[source,C,linenums]
//----
SDL_bool render_scene(int *demo_number){
  glClear(GL_COLOR_BUFFER_BIT);
  glClear(GL_DEPTH_BUFFER_BIT); // don't worry for now
  glClearDepth(-1.1f ); // don't worry for now
  glDepthFunc(GL_GREATER); // don't worry for now
  glMatrixMode(GL_PROJECTION); // don't worry for now
  glLoadIdentity(); // don't worry for now
  glMatrixMode(GL_MODELVIEW); // don't worry for now
  glLoadIdentity(); // don't worry for now
  // map the normalized device-coordinates to screen coordinates,
  // explained  later.
  {
    int w, h;
    SDL_GetWindowSize(window,&w,&h);
    glViewport(0, 0,
               w, h);
  }
//----
//
//When a graphics application is executing, it is creating new
//frames (pictures) at some rate (e.g. 60 frames per second).  At any given
//frame, the user of the application might do something, (e.g.
//move the mouse, click, type on the keyboard, close the application).
//
//At the beginning of every frame, ask OpenGL if it received one
//of these events since we last asked (i.e., the previous frame).
//
//
//
//[source,C,linenums]
//----
  // if the user hits the "X" button to close the window,
  // then quit
  SDL_Event event;
  while (SDL_PollEvent(&event)){
    if (event.type == SDL_QUIT){
      return SDL_TRUE;
    }
  }
//----
//== Black Screen
//
//Since the color of each pixel in the current framebuffer
//has already been set to black, demo 0 will only show a
//black window.
//
//[source,C,linenums]
//----
  if(0 == *demo_number){
    return SDL_FALSE;
  }
//----
//== Draw "Pong" Paddles
//
//A black screen is not particularly interesting.  So instead
//let's draw something slightly more interesting.  Let's make
//something that looks like "Pong", a game from Atari in which
//two players each control a paddle on their side of the screen.
//
//"glColor3f" sets the color for the upcoming graphical "primitive".
//"paddle1" is white, "paddle2" is yellow.
//
//"glBegin(GL_QUADS)" tells OpenGL that we are about to draw a
//quadrilateral, whose vertices are specified by calls to "glVertex2f".
//
//"glEnd()" tells OpenGL that we have finished providing vertices for
//the primitive.
//
//[source,C,linenums]
//----
  if(1 == *demo_number){
    // draw paddle 1
    {
      glColor3f(1.0,1.0,1.0);
      glBegin(GL_QUADS);
      glVertex2f(-1.0,
		 -0.3);
      glVertex2f(-0.8,
		 -0.3);
      glVertex2f(-0.8,
		 0.3);
      glVertex2f(-1.0,
		 0.3);
      glEnd();
    }
    // draw paddle 2
    {
      glColor3f(1.0,1.0,0.0);
      glBegin(GL_QUADS);
      glVertex2f(0.8,
		 -0.3);
      glVertex2f(1.0,
		 -0.3);
      glVertex2f(1.0,
		 0.3);
      glVertex2f(0.8,
		 0.3);
      glEnd();
    }
    return SDL_FALSE;
  }
//----
//=== Screen-space vs normalized device coordinates-space
//My monitor has 1920x1200 pixels.  Not every monitor in existence
//has that exact number of pixels.  To ensure that graphical programs
//may run on computers with varying numbers of pixels, OpenGL
//makes the "domain" of drawable pixels from -1.0 to 1.0, for both the
//x and y coordinates.
//(-1.0,-1.0) is the lower left pixel on your screen, (1.0,1.0) is the
//upper right pixel.
//
//== Move the Paddles using the Keyboard
//
//Paddles which don't move are boring.  Use keyboard input from SDL
//to move the paddles up or down.
//
//(static variables are initialized only the first time the code is executed,
//in subsequent calls to "render_scene", they retain the value they had the last time
//"render-scene" was called.)
//[source,C,linenums]
//----
  static GLfloat paddle_1_offset_Y = 0.0;
  static GLfloat paddle_2_offset_Y = 0.0;
  const Uint8 *state = SDL_GetKeyboardState(NULL);
  // update_paddle_positions
  if (state[SDL_SCANCODE_S]) {
    paddle_1_offset_Y -= 0.1;
  }
  if (state[SDL_SCANCODE_W]) {
    paddle_1_offset_Y += 0.1;
  }
  if (state[SDL_SCANCODE_K]) {
    paddle_2_offset_Y -= 0.1;
  }
  if (state[SDL_SCANCODE_I]) {
    paddle_2_offset_Y += 0.1;
  }
//----
//
//Change the y coordinate of the paddle's vertices based on
//the keyboard input of the user.
//
//
//[source,C,linenums]
//----
  if(2 == *demo_number){
    // draw paddle 1, relative to the offset
    {
      glColor3f(1.0,1.0,1.0);
      glBegin(GL_QUADS);
      glVertex2f(-1.0,
		 -0.3+paddle_1_offset_Y);
      glVertex2f(-0.8,
		 -0.3+paddle_1_offset_Y);
      glVertex2f(-0.8,
		 0.3+paddle_1_offset_Y);
      glVertex2f(-1.0,
		 0.3+paddle_1_offset_Y);
      glEnd();
    }
    // draw paddle 2, relative to the offset
    {
      glColor3f(1.0,1.0,0.0);
      glBegin(GL_QUADS);
      glVertex2f(0.8,
		 -0.3+paddle_2_offset_Y);
      glVertex2f(1.0,
		 -0.3+paddle_2_offset_Y);
      glVertex2f(1.0,
		 0.3+paddle_2_offset_Y);
      glVertex2f(0.8,
		 0.3+paddle_2_offset_Y);
      glEnd();
    }
    return SDL_FALSE;
  }
//----
//== Model Vertices with a Data-Structure
//
//
//Modeling vertices, along with transformations of them,
//is important.  So let's make a class to encapsulate
//modifications to verticies.
//[source,C,linenums]
//----
  class Vertex {
  public:
    // members
    GLfloat x;
    GLfloat y;
    // construtor
    Vertex(GLfloat the_x, GLfloat the_y):
      x(the_x),
      y(the_y)
    {}
    // transformations
//----
//
//Rather than incrementing y values before calling "glVertex",
//instead call "translate" on the vertex.
//[source,C,linenums]
//----
    Vertex translate(GLfloat translate_x,
                     GLfloat translate_y)
    {
      return Vertex(x + translate_x,
                    y + translate_y);
    };
//----
//
//Similarly, we can expand or shink the size of an object
//by "scale"ing each of the vertices of the object, assuming
//the object's center is at (0,0).
//[source,C,linenums]
//----
    Vertex scale(GLfloat scale_x,
                 GLfloat scale_y)
    {
      return Vertex(x * scale_x,
                    y * scale_y);
    };
//----
//
//We can also rotate an object around (0,0).  This won't
//be used until later.
//[source,C,linenums]
//----
    Vertex rotate(GLfloat angle_in_radians)
    {
      return Vertex(x*cos(angle_in_radians) - y*sin(angle_in_radians),
                    x*sin(angle_in_radians) + y*cos(angle_in_radians));
    };
  };
//----
//[source,C,linenums]
//----
  if(3 == *demo_number){
    std::vector<Vertex> paddle = {
      Vertex(-0.1, -0.3),
      Vertex(0.1, -0.3),
      Vertex(0.1, 0.3),
      Vertex(-0.1, 0.3)
    };
    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    glBegin(GL_QUADS);
    for(Vertex v : paddle){
      Vertex newPosition = v
	.translate(-0.9,
		   paddle_1_offset_Y);
      glVertex2f(newPosition.x,
		 newPosition.y);
    }
    glEnd();

    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    glBegin(GL_QUADS);
    for(Vertex v : paddle){
      Vertex newPosition = v
	.translate(0.9,
		   paddle_2_offset_Y);
      glVertex2f(newPosition.x,
		 newPosition.y);
    }
    glEnd();
    return SDL_FALSE;
  }
//----
//[source,C,linenums]
//----
  if (state[SDL_SCANCODE_S]) {
    paddle_1_offset_Y -= 10.0f;
  }
  if (state[SDL_SCANCODE_W]) {
    paddle_1_offset_Y += 10.0f;
  }
  if (state[SDL_SCANCODE_K]) {
    paddle_2_offset_Y -= 10.0f;
  }
  if (state[SDL_SCANCODE_I]) {
    paddle_2_offset_Y += 10.0f;
  }
//----
//[source,C,linenums]
//----
  const std::vector<Vertex> paddle = {
    Vertex(-10.0, -30.0),
    Vertex(10.0, -30.0),
    Vertex(10.0, 30.0),
    Vertex(-10.0, 30.0)
  };
  if(4 == *demo_number){
    // draw paddle 1, relative to the offset
    {
      glColor3f(1.0,1.0,1.0);
      glBegin(GL_QUADS);
      for(Vertex modelspace : paddle){
        Vertex newPosition = modelspace
	  .translate(-90.0,
		     paddle_1_offset_Y)
	  .scale(1.0/100.0,
		 1.0/100.0);
        glVertex2f(newPosition.x,
		   newPosition.y);
      }
      glEnd();
    }
    // draw paddle 2, relative to the offset
    {
      glBegin(GL_QUADS);
      glColor3f(1.0,1.0,0.0);
      for(Vertex modelspace : paddle){
        Vertex worldSpace = modelspace
	  .translate(90.0,
		     paddle_2_offset_Y);
        Vertex ndcSpace = worldSpace.scale(1.0/100.0,
                                           1.0/100.0);
        glVertex2f(ndcSpace.x,
		   ndcSpace.y);
      }
      glEnd();
    }
    return SDL_FALSE;
  }
//----
//== Rotate the Paddles About their Center
//
//[source,C,linenums]
//----
  static GLfloat paddle_1_rotation = 0.0;
  static GLfloat paddle_2_rotation = 0.0;
  // update_rotation_of_paddles
  if (state[SDL_SCANCODE_A]) {
    paddle_1_rotation -= 0.1;
  }
  if (state[SDL_SCANCODE_D]) {
    paddle_1_rotation += 0.1;
  }
  if (state[SDL_SCANCODE_J]) {
    paddle_2_rotation -= 0.1;
  }
  if (state[SDL_SCANCODE_L]) {
    paddle_2_rotation += 0.1;
  }
//----
//[source,C,linenums]
//----
  if(6 == *demo_number){
    // draw paddle 1, relative to the offset
    {
      glColor3f(1.0,1.0,1.0);
      glBegin(GL_QUADS);
      for(Vertex modelspace : paddle){
        Vertex worldSpace = modelspace
	  .rotate(paddle_1_rotation)
	  .translate(-90.0,
		     paddle_1_offset_Y);
        Vertex ndcSpace = worldSpace.scale(1.0/100.0,
                                           1.0/100.0);
        glVertex2f(ndcSpace.x,
		   ndcSpace.y);
      }
      glEnd();
    }
    // draw paddle 2, relative to the offset
    {
      glBegin(GL_QUADS);
      glColor3f(1.0,1.0,0.0);
      for(Vertex modelspace : paddle){
        Vertex worldSpace = modelspace
	  .rotate(paddle_2_rotation)
	  .translate(90.0,
		     paddle_2_offset_Y);
        Vertex ndcSpace = worldSpace.scale(1.0/100.0,
                                           1.0/100.0);
        glVertex2f(ndcSpace.x,
		   ndcSpace.y);
      }
      glEnd();
    }
    return SDL_FALSE;
  }
//----
//== Make a Movable Camera
//
//[source,C,linenums]
//----
  static GLfloat camera_x = 0.0;
  static GLfloat camera_y = 0.0;
  // update_camera_position
  if (state[SDL_SCANCODE_UP]) {
    camera_y += 10.0;
  }
  if (state[SDL_SCANCODE_DOWN]) {
    camera_y -= 10.0;
  }
  if (state[SDL_SCANCODE_LEFT]) {
    camera_x -= 10.0;
  }
  if (state[SDL_SCANCODE_RIGHT]) {
    camera_x += 10.0;
  }
//----
//[source,C,linenums]
//----
  if(7 == *demo_number){
    // draw paddle 1, relative to the offset
    {
      glColor3f(1.0,1.0,1.0);
      glBegin(GL_QUADS);
      for(Vertex modelspace : paddle){
        Vertex worldSpace = modelspace
	  .rotate(paddle_1_rotation)
	  .translate(-90.0,
		     paddle_1_offset_Y);
        Vertex cameraSpace = worldSpace.translate(-camera_x,
                                                  -camera_y);
        Vertex ndcSpace = cameraSpace.scale(1.0/100.0,
                                            1.0/100.0);
        glVertex2f(ndcSpace.x,
		   ndcSpace.y);
      }
      glEnd();
    }
    // draw paddle 2, relative to the offset
    {
      glBegin(GL_QUADS);
      glColor3f(1.0,1.0,0.0);
      for(Vertex modelspace : paddle){
        Vertex worldSpace = modelspace
	  .rotate(paddle_2_rotation)
	  .translate(90.0,
		     paddle_2_offset_Y);
        Vertex cameraSpace = worldSpace.translate(-camera_x,
                                                  -camera_y);
        Vertex ndcSpace = cameraSpace.scale(1.0/100.0,
                                             1.0/100.0);
        glVertex2f(ndcSpace.x,
		   ndcSpace.y);
      }
      glEnd();
    }
    return SDL_FALSE;
  }
//----
//[source,C,linenums]
//----
  const std::vector<Vertex> square = {
    Vertex(-5.0, -5.0),
    Vertex(5.0, -5.0),
    Vertex(5.0, 5.0),
    Vertex(-5.0, 5.0)
  };
//----
//== Draw a Small Square Relative to the Left Paddle
//
//[source,C,linenums]
//----
  if(8 == *demo_number){
    // draw paddle 1, relative to the offset
    {
      glColor3f(1.0,1.0,1.0);
      glBegin(GL_QUADS);
      for(Vertex modelspace : paddle){
        Vertex worldSpace = modelspace
	  .rotate(paddle_1_rotation)
	  .translate(-90.0,
		     paddle_1_offset_Y);
        Vertex cameraSpace = worldSpace.translate(-camera_x,
                                                  -camera_y);
        Vertex ndcSpace = cameraSpace.scale(1.0/100.0,
                                            1.0/100.0);
        glVertex2f(ndcSpace.x,
		   ndcSpace.y);
      }
      glEnd();
    }
    // draw square, relative to paddle 1
    {
      glColor3f(0.0,0.0,1.0);
      glBegin(GL_QUADS);
      for(Vertex modelspace : square){
        Vertex worldSpace = modelspace
	  .translate(20.0f,
		     0.0f)
	  .rotate(paddle_1_rotation)
	  .translate(-90.0,
		     paddle_1_offset_Y);
        Vertex cameraSpace = worldSpace.translate(-camera_x,
                                                  -camera_y);
        Vertex ndcSpace = cameraSpace.scale(1.0/100.0,
                                            1.0/100.0);
        glVertex2f(ndcSpace.x,
		   ndcSpace.y);
      }
      glEnd();
    }
    // draw paddle 2, relative to the offset
    {
      glBegin(GL_QUADS);
      glColor3f(1.0,1.0,0.0);
      for(Vertex modelspace : paddle){
        Vertex worldSpace = modelspace
	  .rotate(paddle_2_rotation)
	  .translate(90.0,
		     paddle_2_offset_Y);
        Vertex cameraSpace = worldSpace.translate(-camera_x,
                                                  -camera_y);
        Vertex ndcSpace = cameraSpace.scale(1.0/100.0,
                                            1.0/100.0);
        glVertex2f(ndcSpace.x,
		   ndcSpace.y);
      }
      glEnd();
    }
    return SDL_FALSE;
  }
//----
//== Rotate the Square About Its Origin
//
//[source,C,linenums]
//----
  static GLfloat square_rotation = 0.0;
  // update_square_rotation
  if (state[SDL_SCANCODE_Q]) {
    square_rotation += 0.1;
  }
  if(9 == *demo_number){
    // draw paddle 1, relative to the offset
    {
      glColor3f(1.0,1.0,1.0);
      glBegin(GL_QUADS);
      for(Vertex modelspace : paddle){
        Vertex worldSpace = modelspace
	  .rotate(paddle_1_rotation)
	  .translate(-90.0,
		     paddle_1_offset_Y);
        Vertex cameraSpace = worldSpace.translate(-camera_x,
                                                  -camera_y);
        Vertex ndcSpace = cameraSpace.scale(1.0/100.0,
                                            1.0/100.0);
        glVertex2f(ndcSpace.x,
		   ndcSpace.y);
      }
      glEnd();
    }
    // draw square, relative to paddle 1
    {
      glColor3f(0.0,0.0,1.0);
      glBegin(GL_QUADS);
      for(Vertex modelspace : square){
        Vertex worldSpace  = modelspace
	  .rotate(square_rotation)
	  .translate(20.0f,
		     0.0f)
	  .rotate(paddle_1_rotation)
	  .translate(-90.0,
		     paddle_1_offset_Y);
        Vertex cameraSpace = worldSpace.translate(-camera_x,
                                                  -camera_y);
        Vertex ndcSpace = cameraSpace.scale(1.0/100.0,
                                            1.0/100.0);
        glVertex2f(ndcSpace.x,
		   ndcSpace.y);
      }
      glEnd();
    }
    // draw paddle 2, relative to the offset
    {
      glBegin(GL_QUADS);
      glColor3f(1.0,1.0,0.0);
      for(Vertex modelspace : paddle){
        Vertex worldSpace  = modelspace
	  .rotate(paddle_2_rotation)
	  .translate(90.0,
		     paddle_2_offset_Y);
        Vertex cameraSpace = worldSpace.translate(-camera_x,
                                                  -camera_y);
        Vertex ndcSpace = cameraSpace.scale(1.0/100.0,
                                            1.0/100.0);
        glVertex2f(ndcSpace.x,
		   ndcSpace.y);
      }
      glEnd();
    }
    return SDL_FALSE;
  }
//----
//[source,C,linenums]
//----
  static GLfloat rotation_around_paddle_1 = 0.0;
  if (state[SDL_SCANCODE_E]) {
    rotation_around_paddle_1 += 0.1;
  }
//----
//== Rotate the Square About the Paddle
//
//[source,C,linenums]
//----
  if(10 == *demo_number){
    // draw paddle 1, relative to the offset
    {
      glColor3f(1.0,1.0,1.0);
      glBegin(GL_QUADS);
      for(Vertex modelspace : paddle){
        Vertex worldSpace  = modelspace
	  .rotate(paddle_1_rotation)
	  .translate(-90.0,
		     paddle_1_offset_Y);
        Vertex cameraSpace = worldSpace.translate(-camera_x,
                                                  -camera_y);
        Vertex ndcSpace = cameraSpace.scale(1.0/100.0,
                                            1.0/100.0);
        glVertex2f(ndcSpace.x,
		   ndcSpace.y);
      }
      glEnd();
    }
    // draw square, relative to paddle 1
    {
      glColor3f(0.0,0.0,1.0);
      glBegin(GL_QUADS);
      for(Vertex modelspace : square){
        Vertex worldSpace  = modelspace
	  .rotate(square_rotation)
	  .translate(20.0f,
		     0.0f)
	  .rotate(rotation_around_paddle_1)
	  .rotate(paddle_1_rotation)
	  .translate(-90.0,
		     paddle_1_offset_Y);
        Vertex cameraSpace = worldSpace.translate(-camera_x,
                                                  -camera_y);
        Vertex ndcSpace = cameraSpace.scale(1.0/100.0,
                                            1.0/100.0);
        glVertex2f(ndcSpace.x,
		   ndcSpace.y);
      }
      glEnd();
    }
    // draw paddle 2, relative to the offset
    {
      glBegin(GL_QUADS);
      glColor3f(1.0,1.0,0.0);
      for(Vertex modelspace : paddle){
        Vertex worldSpace  = modelspace
	  .rotate(paddle_2_rotation)
	  .translate(90.0,
		     paddle_2_offset_Y);
        Vertex cameraSpace = worldSpace.translate(-camera_x,
                                                  -camera_y);
        Vertex ndcSpace = cameraSpace.scale(1.0/100.0,
                                            1.0/100.0);
        glVertex2f(ndcSpace.x,
		   ndcSpace.y);
      }
      glEnd();
    }
    return SDL_FALSE;
  }
//----
//[source,C,linenums]
//----
  class Vertex3 {
  public:
    Vertex3(GLfloat the_x, GLfloat the_y, GLfloat the_z):
      x(the_x),
      y(the_y),
      z(the_z)
    {}
    Vertex3 translate(GLfloat translate_x,
                      GLfloat translate_y,
                      GLfloat translate_z)
    {
      return Vertex3(x + translate_x,
                     y + translate_y,
		     z + translate_z);
    };
    Vertex3 rotateX(GLfloat angle_in_radians)
    {
      return Vertex3(x,
                     y*cos(angle_in_radians) - z*sin(angle_in_radians),
		     y*sin(angle_in_radians) + z*cos(angle_in_radians));
    };
    Vertex3 rotateY(GLfloat angle_in_radians)
    {
      return Vertex3(z*sin(angle_in_radians) + x*cos(angle_in_radians),
                     y,
		     z*cos(angle_in_radians) - x*sin(angle_in_radians));
    };
    Vertex3 rotateZ(GLfloat angle_in_radians)
    {
      return Vertex3(x*cos(angle_in_radians) - y*sin(angle_in_radians),
                     x*sin(angle_in_radians) + y*cos(angle_in_radians),
                     z);
    };
    Vertex3 scale(GLfloat scale_x,
                  GLfloat scale_y,
                  GLfloat scale_z)
    {
      return Vertex3(x * scale_x,
                     y * scale_y,
                     z * scale_z);
    };
    Vertex3 ortho(GLfloat left,
                  GLfloat right,
                  GLfloat bottom,
                  GLfloat top,
                  GLfloat nearVal,
                  GLfloat farVal)
    {
      GLfloat x_length = right-left;
      GLfloat y_length = top-bottom;
      GLfloat z_length = farVal-nearVal;
      return
	translate(-(right-x_length/2.0),
		  -(top-y_length/2.0),
		  -(farVal-z_length/2.0))
        .scale(1/(x_length/2.0),
               1/(y_length/2.0),
               1/(-z_length/2.0));
      // negate z length because it is already negative, and don't want
      // to flip the data
    }

#define RAD_TO_DEG(rad) (57.296 * rad)
#define DEG_TO_RAD(degree) (degree / 57.296)
    Vertex3 perspective(GLfloat nearZ,
                        GLfloat farZ){
      const GLfloat field_of_view =  DEG_TO_RAD(45.0/2.0);
      int w, h;
      SDL_GetWindowSize(window,&w,&h);
      GLfloat y_angle =  (h / w) * field_of_view;

      GLfloat sheared_x = x / fabs(z) * fabs(nearZ);
      GLfloat sheared_y = y / fabs(z) * fabs(nearZ);
      Vertex3 projected =  Vertex3(sheared_x,
				   sheared_y,
				   z);
      GLfloat x_min_of_box = fabs(nearZ) * tan(field_of_view);
      GLfloat y_min_of_box = fabs(nearZ) * tan(y_angle);
      return projected.ortho(-x_min_of_box,
			     x_min_of_box,
                             -y_min_of_box,
			     y_min_of_box,
                             nearZ,
			     farZ);
    };
    GLfloat x;
    GLfloat y;
    GLfloat z;
  };

  typedef std::function<Vertex3 (Vertex3)> Vertex3_transformer;
  std::function<void (Vertex3_transformer)>
    draw_square3_programmable =
    [&](Vertex3_transformer f)
    {
      glBegin(GL_QUADS);
      Vertex3 ndc_v_1 = f(Vertex3(-1.0,-1.0,0.0));
      glVertex3f(ndc_v_1.x,
		 ndc_v_1.y,
		 ndc_v_1.z);
      Vertex3 ndc_v_2 = f(Vertex3(1.0,-1.0,0.0));
      glVertex3f(ndc_v_2.x,
		 ndc_v_2.y,
		 ndc_v_2.z);
      Vertex3 ndc_v_3 = f(Vertex3(1.0,1.0,0.0));
      glVertex3f(ndc_v_3.x,
		 ndc_v_3.y,
		 ndc_v_3.z);
      Vertex3 ndc_v_4 = f(Vertex3(-1.0,1.0,0.0));
      glVertex3f(ndc_v_4.x,
		 ndc_v_4.y,
		 ndc_v_4.z);
      glEnd();
    };
//----
//[source,C,linenums]
//----
  const std::vector<Vertex3> paddle3D = {
    Vertex3(-10.0, -30.0, 0.0),
    Vertex3(10.0, -30.0, 0.0),
    Vertex3(10.0, 30.0, 0.0),
    Vertex3(-10.0, 30.0, 0.0)
  };
  const std::vector<Vertex3> square3D = {
    Vertex3(-5.0, -5.0, 0.0),
    Vertex3(5.0, -5.0, 0.0),
    Vertex3(5.0, 5.0, 0.0),
    Vertex3(-5.0, 5.0, 0.0)
  };


//// TODO -- update newposition to have better names for 3d
  if(11 == *demo_number){
    // draw paddle 1, relative to the offset
    {
      glColor3f(1.0,1.0,1.0);
      glBegin(GL_QUADS);
      for(Vertex3 modelspace : paddle3D){
        Vertex3 worldSpace = modelspace
	  .rotateZ(paddle_1_rotation)
	  .translate(-90.0,
		     paddle_1_offset_Y,
		     0.0);
	Vertex3 cameraSpace = worldSpace
	  .translate(-camera_x,
		     -camera_y,
		     0.0);
	Vertex3 ndcSpace = cameraSpace
	  .ortho(-100.0f,100.0f,
		 -100.0f,100.0f,
		 100.0f,-100.0f);
        glVertex3f(ndcSpace.x,
		   ndcSpace.y,
		   ndcSpace.z);
      }
      glEnd();
    }
    // draw square, relative to paddle 1
    {
      glColor3f(0.0,0.0,1.0);
      glBegin(GL_QUADS);
      for(Vertex3 modelspace : square3D){
        Vertex3 worldSpace = modelspace
	  .rotateZ(square_rotation)
	  .translate(20.0f,
		     0.0f,
		     -10.0f)  // NEW, using a different Z value
	  .rotateZ(rotation_around_paddle_1)
	  .rotateZ(paddle_1_rotation)
	  .translate(-90.0,
		     paddle_1_offset_Y,
		     0.0);
	Vertex3 cameraSpace = worldSpace
	  .translate(-camera_x,
		     -camera_y,
		     0.0);
	Vertex3 ndcSpace = cameraSpace
	  .ortho(-100.0f,100.0f,
		 -100.0f,100.0f,
		 100.0f,-100.0f);
        glVertex3f(ndcSpace.x,
		   ndcSpace.y,
		   ndcSpace.y);
      }
      glEnd();
    }
    // draw paddle 2, relative to the offset
    {
      glBegin(GL_QUADS);
      glColor3f(1.0,1.0,0.0);
      for(Vertex3 modelspace : paddle3D){
        Vertex3 worldSpace = modelspace
	  .rotateZ(paddle_2_rotation)
	  .translate(90.0,
		     paddle_2_offset_Y,
		     0.0);
	Vertex3 cameraSpace = worldSpace
	  .translate(-camera_x,
		     -camera_y,
		     0.0);
	Vertex3 ndcSpace = cameraSpace
	  .ortho(-100.0f,100.0f,
		 -100.0f,100.0f,
		 100.0f,-100.0f);
        glVertex3f(ndcSpace.x,
		   ndcSpace.y,
		   ndcSpace.z);
      }
      glEnd();
    }
    return SDL_FALSE;
  }
//----
//[source,C,linenums]
//----
  // use stacks for transformations
  std::vector<Vertex3_transformer> transformationStack;
  Vertex3_transformer applyTransformationStack = [&](Vertex3 v){
    Vertex3 result = v;
    for(std::vector<Vertex3_transformer>::reverse_iterator
          rit = transformationStack.rbegin();
        rit!=transformationStack.rend();
        rit++)
      {
        result = (*rit)(result);
      }
    return result;
  };
//----
//[source,C,linenums]
//----
  static GLfloat moving_camera_x = 0.0;
  static GLfloat moving_camera_y = 0.0;
  static GLfloat moving_camera_z = 0.0;
  static GLfloat moving_camera_rot_y = 0.0;
  static GLfloat moving_camera_rot_x = 0.0;
  // update camera from the keyboard
  {
    const GLfloat move_multiple = 15.0;
    if (state[SDL_SCANCODE_RIGHT]) {
      moving_camera_rot_y -= 0.03;
    }
    if (state[SDL_SCANCODE_LEFT]) {
      moving_camera_rot_y += 0.03;
    }
    if (state[SDL_SCANCODE_PAGEUP]) {
      moving_camera_rot_x += 0.03;
    }
    if (state[SDL_SCANCODE_PAGEDOWN]) {
      moving_camera_rot_x -= 0.03;
    }
    if (state[SDL_SCANCODE_UP]) {
      moving_camera_x -= move_multiple * sin(moving_camera_rot_y);
      moving_camera_z -= move_multiple * cos(moving_camera_rot_y);
    }
    if (state[SDL_SCANCODE_DOWN]) {
      moving_camera_x += move_multiple * sin(moving_camera_rot_y);
      moving_camera_z += move_multiple * cos(moving_camera_rot_y);
    }
  }
//----
//[source,C,linenums]
//----


  if(13 == *demo_number){
    // draw paddle 1, relative to the offset
    {
      glColor3f(1.0,1.0,1.0);
      glBegin(GL_QUADS);
      for(Vertex3 modelspace : paddle3D){
        Vertex3 worldSpace = modelspace
	  .rotateZ(paddle_1_rotation)
	  .translate(-90.0,
		     paddle_1_offset_Y,
		     0.0);
          // new camera transformations
	Vertex3 cameraSpace = worldSpace
	  .translate(-moving_camera_x,
		     -moving_camera_y,
		     -moving_camera_z)
	  .rotateY(-moving_camera_rot_y)
	  .rotateX(-moving_camera_rot_x);
          // end new camera transformations
	Vertex3 ndcSpace = cameraSpace
	  .ortho(-100.0f,100.0f,
		 -100.0f,100.0f,
		 100.0f,-100.0f);
        glVertex3f(ndcSpace.x,
		   ndcSpace.y,
		   ndcSpace.z);
      }
      glEnd();
    }
    // draw square, relative to paddle 1
    {
      glColor3f(0.0,0.0,1.0);
      glBegin(GL_QUADS);
      for(Vertex3 modelspace : square3D){
        Vertex3 worldSpace = modelspace
	  .rotateZ(square_rotation)
	  .translate(20.0f,
		     0.0f,
		     -10.0f)  // NEW, using a different Z value
	  .rotateZ(rotation_around_paddle_1)
	  .rotateZ(paddle_1_rotation)
	  .translate(-90.0,
		     paddle_1_offset_Y,
		     0.0);
          // new camera transformations
	Vertex3 cameraSpace = worldSpace
	  .translate(-moving_camera_x,
		     -moving_camera_y,
		     -moving_camera_z)
	  .rotateY(-moving_camera_rot_y)
	  .rotateX(-moving_camera_rot_x);
          // end new camera transformations
	Vertex3 ndcSpace = cameraSpace
	  .ortho(-100.0f,100.0f,
		 -100.0f,100.0f,
		 100.0f,-100.0f);
        glVertex3f(ndcSpace.x,
		   ndcSpace.y,
		   ndcSpace.z);
      }
      glEnd();
    }

    // draw paddle 2, relative to the offset
    {
      glBegin(GL_QUADS);
      glColor3f(1.0,1.0,0.0);
      for(Vertex3 modelspace : paddle3D){
        Vertex3 worldSpace = modelspace
	  .rotateZ(paddle_2_rotation)
	  .translate(90.0,
		     paddle_2_offset_Y,
		     0.0);
          // new camera transformations
	Vertex3 cameraSpace = worldSpace
	  .translate(-moving_camera_x,
		     -moving_camera_y,
		     -moving_camera_z)
	  .rotateY(-moving_camera_rot_y)
	  .rotateX(-moving_camera_rot_x);
          // end new camera transformations
	Vertex3 ndcSpace = cameraSpace
	  .ortho(-100.0f,100.0f,
		 -100.0f,100.0f,
		 100.0f,-100.0f);
        glVertex3f(ndcSpace.x,
		   ndcSpace.y,
		   ndcSpace.z);
      }
      glEnd();
    }
    return SDL_FALSE;
  }



  if(*demo_number >= 14){
    glEnable(GL_DEPTH_TEST);
  }
  if(14 == *demo_number){
    *demo_number = 13;
    return SDL_FALSE;
  }
//----
//[source,C,linenums]
//----
  if(*demo_number >= 14){
    static bool first_frame = true;
    if(first_frame){
      moving_camera_z = 400.0; // for the perspective to look right
      first_frame = false;
    }
  }
//----
//[source,C,linenums]
//----
  if(15 == *demo_number){
    // every shape is projected the same way
    transformationStack.push_back([&](Vertex3 v){
        return v.perspective(-0.1f,
                             -1000.0f);
      });
    // THE REST IS THE SAME AS THE PREVIOUS
    // every shape is relative to the camera
    // camera transformation #3 - tilt your head down
    transformationStack.push_back([&](Vertex3 v){
        return v.rotateX(-moving_camera_rot_x);
      });
    // camera transformation #2 - turn your head to the side
    transformationStack.push_back([&](Vertex3 v){
        return v.rotateY(-moving_camera_rot_y);
      });
    // camera transformation #1 - move to the origin
    transformationStack.push_back([&](Vertex3 v){
        return v.translate(- moving_camera_x,
                           - moving_camera_y,
                           - moving_camera_z);
      });
    transformationStack.push_back([&](Vertex3 v){
        return v.translate(-90.0f,
                           0.0f + paddle_1_offset_Y,
                           0.0f);
      });
    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      transformationStack.push_back([&](Vertex3 v){
          return v.rotateZ(paddle_1_rotation);
        });
      transformationStack.push_back([&](Vertex3 v){
          return v.scale(10.0f,
                         30.0f,
                         1.0f);
        });
      draw_square3_programmable(applyTransformationStack);
      transformationStack.pop_back();
      transformationStack.pop_back();
    }
    // draw square, relative to paddle 1
    glColor3f(0.0,0.0,1.0);
    {
      transformationStack.push_back([&](Vertex3 v){
          return v.rotateZ(paddle_1_rotation);
        });
      transformationStack.push_back([&](Vertex3 v){
          return v.rotateZ(rotation_around_paddle_1);
        });
      transformationStack.push_back([&](Vertex3 v){
          return v.translate(20.0f,
                             0.0f,
                             -10.0f); // NEW, using a non zero
        });
      transformationStack.push_back([&](Vertex3 v){
          return v.rotateZ(square_rotation);
        });
      transformationStack.push_back([&](Vertex3 v){
          return v.scale(5.0f,
                         5.0f,
                         0.0f);
        });
      draw_square3_programmable(applyTransformationStack);
      transformationStack.pop_back();
      transformationStack.pop_back();
      transformationStack.pop_back();
      transformationStack.pop_back();
      transformationStack.pop_back();
    }
    // get back to the global origin
    transformationStack.pop_back();
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      transformationStack.push_back([&](Vertex3 v){
          return v.translate(90.0f,
                             0.0f + paddle_2_offset_Y,
                             0.0f);
        });
      transformationStack.push_back([&](Vertex3 v){
          return v.rotateZ(paddle_2_rotation);
        });
      transformationStack.push_back([&](Vertex3 v){
          return v.scale(10.0f,
                         30.0f,
                         1.0f);
        });
      draw_square3_programmable(applyTransformationStack);
      transformationStack.pop_back();
      transformationStack.pop_back();
      transformationStack.pop_back();
    }
    transformationStack.pop_back();
    transformationStack.pop_back();
    transformationStack.pop_back();
    transformationStack.pop_back();
    return SDL_FALSE;
  }
//----
//[source,C,linenums]
//----
  if(*demo_number >= 16){
    // for whatever reason, gluPerspective flips the z values
    glClearDepth(1.1f );
    glDepthFunc(GL_LEQUAL);
  }
//----
//[source,C,linenums]
//----
  std::function<void()> draw_square_opengl2point1 = [&](){
    glBegin(GL_QUADS);
    glVertex2f(-1.0,
	       -1.0);
    glVertex2f(1.0,
	       -1.0);
    glVertex2f(1.0,
	       1.0);
    glVertex2f(-1.0,
	       1.0);
    glEnd();
  };
//----
//[source,C,linenums]
//----
  if(40 == *demo_number){
    /*
     *  Demo 40 - OpenGL Matricies
     */
    // set up Camera
    {
      // define the projection
      glMatrixMode(GL_PROJECTION);
      glLoadIdentity();
      glHint( GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST );
      {
        int w, h;
        SDL_GetWindowSize(window,&w,&h);
        gluPerspective(45.0f,
                       (GLdouble)w / (GLdouble)h,
                       0.1f,
                       1000.0f);
      }
      // move the "camera"
      glMatrixMode(GL_MODELVIEW);
      glLoadIdentity();
      glRotatef(RAD_TO_DEG(-moving_camera_rot_x),
                1.0,
                0.0,
                0.0);
      glRotatef(RAD_TO_DEG(-moving_camera_rot_y),
                0.0,
                1.0,
                0.0);
      glTranslatef(-moving_camera_x,
                   -moving_camera_y,
                   -moving_camera_z);
    }
    // draw paddle 1, relative to the offset
    glPushMatrix();
    {
      glColor3f(1.0,1.0,1.0);
      glTranslatef(-90.0f,
                   0.0f + paddle_1_offset_Y,
                   0.0);
      glRotatef(RAD_TO_DEG(paddle_1_rotation),
                0.0,
                0.0,
                1.0);
      // scaling of this object should not affect the relative square
      glPushMatrix();
      {
        glScalef(10.0f,
                 30.0f,
                 0.0f);
        draw_square_opengl2point1();
        glPopMatrix();
      }
      // draw square, relative to paddle 1
      glColor3f(0.0,0.0,1.0);
      glRotatef(RAD_TO_DEG(rotation_around_paddle_1),
                0.0f,
                0.0f,
                1.0f);
      glTranslatef(20.0f,
                   0.0f,
                   -10.0f);
      glRotatef(RAD_TO_DEG(square_rotation),
                0.0f,
                0.0f,
                1.0f);
      glScalef(5.0f,
               5.0f,
               5.0f);
      draw_square_opengl2point1();
      glPopMatrix();
    }
    // draw paddle 2, relative to the offset
    glPushMatrix();
    glColor3f(1.0,1.0,0.0);
    glTranslatef(90.0f,
                 0.0f + paddle_2_offset_Y,
                 0.0);
    glRotatef(RAD_TO_DEG(paddle_2_rotation),
              0.0,
              0.0,
              1.0);
    glScalef(10.0f,
             30.0f,
             0.0f);
    draw_square_opengl2point1();
    glPopMatrix();
    return SDL_FALSE;
  }
  // in later demos,
  //glClearDepth(1.0f );
  //glEnable(GL_DEPTH_TEST );
  //glDepthFunc(GL_LEQUAL );
  return SDL_FALSE;
}
//----
//
//[[linkageAppendix]]
//[appendix]
//== Linkage
//
//Foo bar baz
//
//[[sharedLibAppendix]]
//[appendix]
//== Shared Libraries
//
//Foo bar baz2
//
//
//[bibliography]
//Example Bibliography
//--------------------
//The bibliography list is a style of AsciiDoc bulleted list.
//
//[bibliography]
//.Books
//- [[[taoup]]] Eric Steven Raymond. 'The Art of Unix
//  Programming'. Addison-Wesley. ISBN 0-13-142901-9.
//  - [[[walsh-muellner]]] Norman Walsh & Leonard Muellner.
//    'DocBook - The Definitive Guide'. O'Reilly & Associates. 1999.
//      ISBN 1-56592-580-7.
//
//[bibliography]
//.Articles
//- [[[abc2003]]] Gall Anonim. 'An article', Whatever. 2003.
//
//
//[glossary]
//Example Glossary
//----------------
//Glossaries are optional. Glossaries entries are an example of a style
//of AsciiDoc labeled lists.
//
//[glossary]
//A glossary term::
//  The corresponding (indented) definition.
//
//A second glossary term::
//  The corresponding (indented) definition.
//
//
//[colophon]
//Example Colophon
//----------------
//Text at the end of a book describing facts about its production.
//
//
//[index]
//Example Index
//-------------
//////////////////////////////////////////////////////////////////
//The index is normally left completely empty, it's contents being
//generated automatically by the DocBook toolchain.
//////////////////////////////////////////////////////////////////
