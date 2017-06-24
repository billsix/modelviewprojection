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
//ifdef::pdf[]
//:max-width: 450
//:half-width: 275
//:quarter-width: 137
//endif::[]
//ifndef::pdf[]
//:max-width: 300
//:half-width: 150
//:quarter-width: 75
//endif::[]
//
//[preface]
//= Preface
//
//"I had no idea how much math was involved in computer graphics."
//
//Unfortunately many students of computer graphics have the impression
//that the writing of computer graphics programs requires knowledge of
//advanced math; which is patently untrue.
//Only the understanding of high-school level geometry is required.
//Using math you already know, this book builds both 2D and 3D
//applications from the ground up using OpenGL, a standard for graphics
//programming.
//
//Thoughout the book, I show how to place objects in space,
//how to draw objects relative to other objects, how to add a
//camera which moves over time based on user input, and how to transform all
//the objects into the 2D pixel coordinates
//of the computer screen.  By the end of this book, you will understand the basics of
//how to create first-person
//and third-person applications/games.  I made this book to show programmers
//how to make the kind
//of graphics programs which they want to make, using
//math they aleady know.
//
//This book is purposely limited in scope, and
//the applications produced are not particurly pretty nor realistic-looking.
//For advanced graphics topics, you'll need to consult other references,
//such as the OpenGL "red book" and "blue book".
//Although this book fills a huge gap that other books do not address,
//those other books are excellent reference books for advanced topics.
//
//
//
//:toc:
//
//[intro]
//= Introduction
//
//[[basics]]
//== Basics
//
//
//The device attached to a computer which displays information to the user is called a *monitor*.
//The monitor is composed of a two-dimensional array of light-emitting elements called *pixel*.
//At a given time, each individual pixel is instructed to display
//one specific color, represented within the computer as a number.
//The aggregate of the colors at each pixel at one moment in time, called a *frame*,
//provides a picture that has some meaning to the human user.
//
//
//
//In OpenGL, the top left pixel of a window is coordinate (0,0).  The bottom right is (window_width,window_height)
//
//
//image:monitor.png[title="Foo",width={max-width}]
//
//image:monitor2.png[title="Foo",width={max-width}]
//
//
//Frames are created within the computer and sent to the monitor
//at a rate over time, called the *framerate*,
//measured in *Hertz*.  By updating frames quickly and at a constant rate, the computer
//provides the end-user with the illusion of motion.
//
//TODO - insert 3 20x20 frames which show motion
//
//
//
//[[openWindow]]
//=== Opening a Window
//
//Desktop operating systems allow the user to run more than one
//program at a time, where each program draws into a subsect of
//the monitor called a window.
//
//TODO - insert picture.

//
//To create and to open a window in a cross-platform manner, this
//book will call procedures provided by the widely-ported SDL2 library (supporting Windows, macOS, Linux).
//SDL2 also provides procedures for receiving
//keyboard input, controller inputfootnote:[tested with a wired XBox 360 controller], and
//to load images from the filesystem.
//
//Much of the code listed from here until section<<the-event-loop>> will be of little interest upon first reading.
//As such, the reader may choose to skip ahead to section<<the-event-loop>> now.
//
//The code for the entire book is available at https://github.com/billsix/modelviewprojection,
//contained within "src/main.cpp". The code, but not the contents of the book, is licenced
//using the open-source Apache 2.0 license.
//
//==== Include Headers
//
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
//
//
//==== Create Data Structure to Represent the Window
//Create a pointer for the window.  If you are new to C or C++, don't fret
//over what a pointer is, as
//the majority of this book does not require knowledge of pointers.
//Programmers of any mainstream language (Java, Python, C#, etc)
//should be able to understand the content of this book.
//
//[source,C,linenums]
//----
SDL_Window *window;
SDL_GLContext glcontext;
//----
//
//
//==== Define main
//Use C linkage for main.  Knowing why isn't terribly important,
//but for the interested reader, <<linkageAppendix>>  provides a description of
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
//==== Let the User Pick the Demo to Run.
//[source,C,linenums]
//----
  std::cout << "Input demo number to run: (1-15): " << std::endl;
  int demo_number;
  std::cin >> demo_number ;
//----
//==== SDL/OpenGL Initialization
//
//-Initialize SDL, including the video, audio, timer, and event subsystems.
//Log any errors.
//[source,C,linenums]
//----
  //initialize video support, joystick support, etc.
  if (0 != SDL_Init(SDL_INIT_TIMER
                    | SDL_INIT_AUDIO
                    | SDL_INIT_VIDEO
                    | SDL_INIT_EVENTS)){
    SDL_LogMessage(SDL_LOG_CATEGORY_APPLICATION,
                   SDL_LOG_PRIORITY_ERROR,
                   "Error: %s\n",
                   SDL_GetError());
    return 1;
  }
//----
//-Set OpenGL to be double-buffered.
//
//One frame is created incrementally over time on the CPU, but the frame
//is sent to the monitor
//only when frame is completely drawn, and each pixel has a color.
//The act of sending the frame to the monitor is called *flushing*
//the frame.
//Flushing takes time,
//and if the call to flush were to blockfootnote:[meaning it would not return control back to the call-ing procedure until the flush is complete], we would
//have wasted CPU time.  To avoid this,
//OpenGL has two *framebuffers*footnote:[regions of memory which will eventually contain the full data for a frame],
//only one of which is "active", or writable, at a given time.
//"SDL_GL_SwapWindow" is a non-blocking call which initiates the flushing
//the current buffer, and which switches the current writable framebuffer to the
//other one, thus allowing the CPU to resume.
//[source,C,linenums]
//----
  SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1);
  SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 24);
  SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE, 8);

  // put the next few lines in only when running opengl 3.2+
  /* SDL_GL_SetAttribute(SDL_GL_CONTEXT_FLAGS, */
  /*                     SDL_GL_CONTEXT_FORWARD_COMPATIBLE_FLAG); */
  SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK,
                      SDL_GL_CONTEXT_PROFILE_COMPATIBILITY);
  SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 2);
  SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 1);

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
                                        (SDL_WINDOW_OPENGL
                                         | SDL_WINDOW_RESIZABLE)))){
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
//A native application which links against shared libraries typically knows at compile-time
//exactly which procedures are provided by the shared libraries.
//But unlike typical shared libraries, a system's OpenGL shared library is supplied
//to the user by the graphics card vendor, who may not provide every OpenGL procedure from
//every version of OpenGL (of which there are many).
//To make programming in OpenGL easier, all calls to OpenGL are actually calls to "GLEW" procedures,
//which effectively are function pointers.  To ensure that those function pointers are initialized,
//call "glewInit".
//See <<sharedLibAppendix>> for a more full explanantion.
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
  glClearColor(/*red*/   0.0,
               /*green*/ 0.0,
               /*blue*/  0.0,
               /*alpha*/ 1.0);
//----
//Set the default depth for all fragments
//[source,C,linenums]
//----
  glClearDepth(-1.1f);
//----
//Set the depth test for all fragments.
//[source,C,linenums]
//----
  glDepthFunc(GL_GREATER);
//----
//Enable blending of new values in a fragment with the old value.
//[source,C,linenums]
//----
  glEnable(GL_BLEND);
//----
//Specify how a given fragment's color value within the framebuffer combines with a second color.  This new
//blended value is then set for the fragment.
//[source,C,linenums]
//----
  glBlendEquation(GL_FUNC_ADD);
  glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

  glMatrixMode(GL_PROJECTION);
  glLoadIdentity();
  glMatrixMode(GL_MODELVIEW);
  glLoadIdentity();
//----
//Map the normalized device-coordinates to screen coordinates, explained later.
//[source,C,linenums]
//----
  {
    int w, h;
    SDL_GetWindowSize(window,
                      /*width*/  &w,
                      /*height*/ &h);
    glViewport(/*min_x*/ 0,
               /*min_y*/ 0,
               /*max_x*/ w,
               /*max_y*/ h);
  }
//----
//[[the-event-loop]]
//==== The Event Loop
//
//When you pause a movie, motion stops and you see one picture.
//Movies are composed of sequence of pictures, when
//rendered in quick succession, provide the illusion of motion.
//
//Interactive computer graphics are rendered the same way,
//one "frame" at a time.
//
//Render a frame for the user-selected demo, flush the complete frame to the monitor.
//Unless the user closed the window, repeat indefinitely.
//
//[source,C,linenums]
//----
  while (true){
    render_scene(&demo_number);
    // if the user hits the "X" button to close the window,
    // then quit
    SDL_Event event;
    while (SDL_PollEvent(&event)){
      if (SDL_QUIT == event.type){
        goto endOfEventLoop;
      }
      if (SDL_WINDOWEVENT == event.type){
        int w, h;
        SDL_GetWindowSize(window,&w,&h);
        glViewport(/*min_x*/ 0,
                   /*min_y*/ 0,
                   /*max_x*/ w,
                   /*max_y*/ h);
      }
    }
    // flush the frame
    SDL_GL_SwapWindow(window);
  }
//----
//==== The User Closed the App, Delete the Window.
//[source,C,linenums]
//----
 endOfEventLoop:
  SDL_GL_DeleteContext(glcontext);
  SDL_DestroyWindow(window);
  SDL_Quit();
  return 0;
} // end main
//----
//=== Render the Selected Demo
//
//Regardless of which demo will be run, certain things need
//to happen every frame.  The color of each pixel withith
//the current framebuffer
//is reset to a default color.
//
//[source,C,linenums]
//----
void render_scene(int *demo_number){
  // clear the framebuffer
  glClear(GL_COLOR_BUFFER_BIT);
  glClear(GL_DEPTH_BUFFER_BIT);

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
//== Demo 0 - Black Screen
//
//To understand the material of this book well, the reader is advised to
//run the compile the program and run the demos.  To do so, the source
//code for this book may be obtained at https://github.com/billsix/modelviewprojection.
//It has been tested on Windows 10 (Visual Studio Community 2017),
//Linux, and OS X.
//
//Once built, execute "modelviewprojection". When prompted, type "0" and then press the "Enter" key.
//
//The first demo is the least interesting graphical program possible.
//
//The event loop, defined in section <<the-event-loop>>, executes a few procedures
//before calling the current procedure.

//-Sets the color at every pixel black.  (A constant color is better than whatever
//color happened to be the previous time it was drawn.)
//
//-If the user resized the window, reset OpenGL's mappings from *normalized-device-coordinates*
//to *screen-coordinates*.
//
//-Cleared the depth buffer (don't worry about this for now).
//
//
//
//
//
//[source,C,linenums]
//----
  if(0 == *demo_number){
    return;
  }
//----

//When this code returns, the event loop flushes the frame to the monitor.  Since
//no geometry was drawn, the color value for each pixel is still black.
//
//The event loop then calls this code over and over again, and since we retain no state and
//we draw nothing, a black screen will be diplayed every frame until the user
//closes the window, and says to himself, "why did I buy Doom 3"?

//=== Normalized-Device-Coordinates
//
//The author owns two monitors, one which has 1024x768 pixels, and one which has
//1920x1200 pixels.  When he purchases a game from Steam, he expects that his game
//will run correctly on either monitor, in full-screen mode.  If a graphics programmer
//had to explictly set each indiviual pixel's color, the the programmer would have to
//program using "screen-space"footnote:[Any "space" means a system of numbers which you're using.
//Screen-space means you're specifically using pixel coordinates, i.e, set pixel (5,10) to be red].

//What looks alright is screen-space on a large monitor...

//image:screenspace2.png[title="Programming using Screen Space on Large Monitor",width={max-width}]

//isn't even the same picture on a smaller monitor.

//image:screenspace.png[title="Programming using Screen Space on Small Monitor",width={max-width}]



//Like any good program or library, OpenGL abstracts over screen-space, thus freeing the
//programmer from caring about screen size.  If a programmer does not want to program
//in discretefootnote:[discrete means integer values, not continuous] screen-space,
//what type of numbers should he use?  Firstly, it should be a continuous space, meaning
//that it should be in decimal numbers.  Because if a real-world object is 10.3 meters long, a programmer
//should be able to enter "float foo = 10.3".  Secondly, it should be a fixed range vertically
//and an fixed range horizontally.  OpenGL will have to convert points from some space to screen-space,
//and since OpenGL does this in hardware (i.e. you can't programmatically change how the conversion
//happens), it should be a fixed size.

//OpenGL uses *normalized-device-coordinates*footnote:[normalized- meaning a distance value of
//1; device- the monitor; coordinates- the system of numbers (i.e. space) in which you are working],
//which is a continous space from -1.0 to 1.0 horizontally,
//and -1.0 to 1.0 vertically.


//By specifying geometry using normalized-device-coordinates,
//OpenGL will automatically convert from a continuous, -1.0 to 1.0 space,
//to discrete pixel-space.

//image:ndcSpace.png[title="Programming using Screen Space on Large Monitor",width={max-width}]

//Whether we own a small monitor

//image:ndcSpace1.png[title="Programming using Screen Space on Small Monitor",width={max-width}]

//or a large monitor.

//image:ndcSpace2.png[title="Programming using Screen Space on Large Monitor",width={max-width}]

//-Exercise 1.  How would you convert from ndc-space to screen-space, given
//a monitor width _w_ and height _h_?

//== Demo 1 - Draw "Pong" Paddles
//
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
//----
//Draw paddle 1.
//[source,C,linenums]
//----
    glColor3f(/*red*/   1.0,
              /*green*/ 1.0,
              /*blue*/  1.0);
    glBegin(GL_QUADS);
    {
      glVertex2f(/*x*/ -1.0,
                 /*y*/ -0.3);
      glVertex2f(/*x*/ -0.8,
                 /*y*/ -0.3);
      glVertex2f(/*x*/ -0.8,
                 /*y*/ 0.3);
      glVertex2f(/*x*/ -1.0,
                 /*y*/ 0.3);
    }
    glEnd();
//----

//The framebuffer, which has not yet been flushed to the monitor, has geometry which looks like this:

//image:plot1.png[title="Foo",width={max-width}]


//Draw paddle 2.
//[source,C,linenums]
//----
    glColor3f(/*red*/   1.0,
              /*green*/ 1.0,
              /*blue*/  0.0);
    glBegin(GL_QUADS);
    {
      glVertex2f(/*x*/ 0.8,
                 /*y*/ -0.3);
      glVertex2f(/*x*/ 1.0,
                 /*y*/ -0.3);
      glVertex2f(/*x*/ 1.0,
                 /*y*/ 0.3);
      glVertex2f(/*x*/ 0.8,
                 /*y*/ 0.3);
    }
    glEnd();
//----

//The framebuffer, which has not yet been flushed to the monitor, has geometry which looks like this:

//image:plot2.png[title="Foo",width={max-width}]

//[source,C,linenums]
//----
    return;
  }
//----

//
//== Demo 2 - Move the Paddles using the Keyboard
//
//[width="75%",frame="topbot",options="header,footer"]
//|=======================================
//|Keyboard Input |Action
//|w              |Move Left Paddle Up
//|s              |Move Left Paddle Down
//|k              |Move Right Paddle Up
//|i              |Move Right Paddle Down
//|=======================================
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
//----
//Draw paddle 1, relative to the offset.
//[source,C,linenums]
//----
    glColor3f(/*red*/   1.0,
              /*green*/ 1.0,
              /*blue*/  1.0);
    glBegin(GL_QUADS);
    {
      glVertex2f(/*x*/ -1.0,
                 /*y*/ -0.3+paddle_1_offset_Y);
      glVertex2f(/*x*/ -0.8,
                 /*y*/ -0.3+paddle_1_offset_Y);
      glVertex2f(/*x*/ -0.8,
                 /*y*/ 0.3+paddle_1_offset_Y);
      glVertex2f(/*x*/ -1.0,
                 /*y*/ 0.3+paddle_1_offset_Y);
    }
    glEnd();
//----
//Draw paddle 2, relative to the offset.
//[source,C,linenums]
//----
    glColor3f(/*red*/   1.0,
              /*green*/ 1.0,
              /*blue*/  0.0);
    glBegin(GL_QUADS);
    {
      glVertex2f(/*x*/ 0.8,
                 /*y*/ -0.3+paddle_2_offset_Y);
      glVertex2f(/*x*/ 1.0,
                 /*y*/ -0.3+paddle_2_offset_Y);
      glVertex2f(/*x*/ 1.0,
                 /*y*/ 0.3+paddle_2_offset_Y);
      glVertex2f(/*x*/ 0.8,
                 /*y*/ 0.3+paddle_2_offset_Y);
    }
    glEnd();
    return;
  }
//----

//== Demo 3 - Model Vertices with a Data-Structure
//
//[width="75%",frame="topbot",options="header,footer"]
//|=======================================
//|Keyboard Input |Action
//|w              |Move Left Paddle Up
//|s              |Move Left Paddle Down
//|k              |Move Right Paddle Up
//|i              |Move Right Paddle Down
//|=======================================
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
//----
//Draw paddle 1, relative to the offset.
//[source,C,linenums]
//----
    glColor3f(/*red*/   1.0,
              /*green*/ 1.0,
              /*blue*/  1.0);
    glBegin(GL_QUADS);
    {
      for(Vertex v : paddle){
        Vertex newPosition = v.translate(/*x*/ -0.9,
                                         /*y*/ paddle_1_offset_Y);
        glVertex2f(/*x*/ newPosition.x,
                   /*y*/ newPosition.y);
      }
    }
    glEnd();
//----
//Draw paddle 2, relative to the offset.
//[source,C,linenums]
//----
    glColor3f(/*red*/   1.0,
              /*green*/ 1.0,
              /*blue*/  0.0);
    glBegin(GL_QUADS);
    {
      for(Vertex v : paddle){
        Vertex newPosition = v.translate(/*x*/ 0.9,
                                         /*y*/ paddle_2_offset_Y);
        glVertex2f(/*x*/ newPosition.x,
                   /*y*/ newPosition.y);
      }
    }
    glEnd();
    return;
  }
//----
//== Demo 4 - Use More Desirable Coordinate System
//
//[width="75%",frame="topbot",options="header,footer"]
//|=======================================
//|Keyboard Input |Action
//|w              |Move Left Paddle Up
//|s              |Move Left Paddle Down
//|k              |Move Right Paddle Up
//|i              |Move Right Paddle Down
//|=======================================

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
//----
//Draw paddle 1, relative to the offset.
//[source,C,linenums]
//----
    glColor3f(/*red*/   1.0,
              /*green*/ 1.0,
              /*blue*/  1.0);
    glBegin(GL_QUADS);
    {
      for(Vertex modelspace : paddle){
        Vertex newPosition = modelspace
          .translate(/*x*/ -90.0,
                     /*y*/ paddle_1_offset_Y)
          .scale(/*x*/ 1.0/100.0,
                 /*y*/ 1.0/100.0);
        glVertex2f(/*x*/ newPosition.x,
                   /*y*/ newPosition.y);
      }
    }
    glEnd();
//----
//Draw paddle 2, relative to the offset
//[source,C,linenums]
//----
    glBegin(GL_QUADS);
    {
      glColor3f(/*red*/   1.0,
                /*green*/ 1.0,
                /*blue*/  0.0);
      for(Vertex modelspace : paddle){
        Vertex worldSpace = modelspace.translate(/*x*/ 90.0,
                                                 /*y*/ paddle_2_offset_Y);
        Vertex ndcSpace = worldSpace.scale(/*x*/ 1.0/100.0,
                                           /*y*/ 1.0/100.0);
        glVertex2f(/*x*/ ndcSpace.x,
                   /*y*/ ndcSpace.y);
      }
    }
    glEnd();
    return;
  }
//----
//== Demo 5 - Rotate the Paddles About their Center
//
//[width="75%",frame="topbot",options="header,footer"]
//|=======================================
//|Keyboard Input |Action
//|w              |Move Left Paddle Up
//|s              |Move Left Paddle Down
//|k              |Move Right Paddle Up
//|i              |Move Right Paddle Down
//|               |
//|d              |Increase Left Paddle's Rotation
//|a              |Decrease Left Paddle's Rotation
//|l              |Increase Right Paddle's Rotation
//|j              |Decrease Right Paddle's Rotation
//|=======================================

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
  if(5 == *demo_number){
//----
//Draw paddle 1, relative to the offset.
//[source,C,linenums]
//----
    glColor3f(/*red*/   1.0,
              /*green*/ 1.0,
              /*blue*/  1.0);
    glBegin(GL_QUADS);
    {
      for(Vertex modelspace : paddle){
        Vertex worldSpace = modelspace
          .rotate(/*radians*/ paddle_1_rotation)
          .translate(/*x*/ -90.0,
                     /*y*/ paddle_1_offset_Y);
        Vertex ndcSpace = worldSpace.scale(/*x*/ 1.0/100.0,
                                           /*y*/ 1.0/100.0);
        glVertex2f(/*x*/ ndcSpace.x,
                   /*y*/ ndcSpace.y);
      }
    }
    glEnd();
//----
//Draw paddle 2, relative to the offset
//[source,C,linenums]
//----
    glBegin(GL_QUADS);
    {
      glColor3f(/*red*/   1.0,
                /*green*/ 1.0,
                /*blue*/  0.0);
      for(Vertex modelspace : paddle){
        Vertex worldSpace = modelspace
          .rotate(/*radians*/ paddle_2_rotation)
          .translate(/*x*/ 90.0,
                     /*y*/ paddle_2_offset_Y);
        Vertex ndcSpace = worldSpace.scale(/*x*/ 1.0/100.0,
                                           /*y*/ 1.0/100.0);
        glVertex2f(/*x*/ ndcSpace.x,
                   /*y*/ ndcSpace.y);
      }
    }
    glEnd();
    return;
  }
//----

//== Demo 6 - Make a Movable Camera
//
//[width="75%",frame="topbot",options="header,footer"]
//|=======================================
//|Keyboard Input |Action
//|w              |Move Left Paddle Up
//|s              |Move Left Paddle Down
//|k              |Move Right Paddle Up
//|i              |Move Right Paddle Down
//|               |
//|d              |Increase Left Paddle's Rotation
//|a              |Decrease Left Paddle's Rotation
//|l              |Increase Right Paddle's Rotation
//|j              |Decrease Right Paddle's Rotation
//|               |
//|UP             |Move the Camera Up
//|DOWN           |Move the Camera Down
//|LEFT           |Move the Camera Left
//|RIGHT          |Move the Camera Right
//|=======================================
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
  if(6 == *demo_number){
//----
//Draw paddle 1, relative to the offset.
//[source,C,linenums]
//----
    glColor3f(/*red*/   1.0,
              /*green*/ 1.0,
              /*blue*/  1.0);
    glBegin(GL_QUADS);
    {
      for(Vertex modelspace : paddle){
        Vertex worldSpace = modelspace
          .rotate(/*radians*/ paddle_1_rotation)
          .translate(/*x*/ -90.0,
                     /*y*/ paddle_1_offset_Y);
        Vertex cameraSpace = worldSpace.translate(/*x*/ -camera_x,
                                                  /*y*/ -camera_y);
        Vertex ndcSpace = cameraSpace.scale(/*x*/ 1.0/100.0,
                                            /*y*/ 1.0/100.0);
        glVertex2f(/*x*/ ndcSpace.x,
                   /*y*/ ndcSpace.y);
      }
    }
    glEnd();
//----
//Draw paddle 2, relative to the offset
//[source,C,linenums]
//----
    glBegin(GL_QUADS);
    {
      glColor3f(/*red*/   1.0,
                /*green*/ 1.0,
                /*blue*/  0.0);
      for(Vertex modelspace : paddle){
        Vertex worldSpace = modelspace
          .rotate(/*radians*/ paddle_2_rotation)
          .translate(/*x*/ 90.0,
                     /*y*/ paddle_2_offset_Y);
        Vertex cameraSpace = worldSpace.translate(/*x*/ -camera_x,
                                                  /*y*/ -camera_y);
        Vertex ndcSpace = cameraSpace.scale(/*x*/ 1.0/100.0,
                                            /*y*/ 1.0/100.0);
        glVertex2f(/*x*/ ndcSpace.x,
                   /*y*/ ndcSpace.y);
      }
    }
    glEnd();
    return;
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
//== Demo 7 - Draw a Small Square Relative to the Left Paddle
//
//[width="75%",frame="topbot",options="header,footer"]
//|=======================================
//|Keyboard Input |Action
//|w              |Move Left Paddle Up
//|s              |Move Left Paddle Down
//|k              |Move Right Paddle Up
//|i              |Move Right Paddle Down
//|               |
//|d              |Increase Left Paddle's Rotation
//|a              |Decrease Left Paddle's Rotation
//|l              |Increase Right Paddle's Rotation
//|j              |Decrease Right Paddle's Rotation
//|               |
//|UP             |Move the Camera Up
//|DOWN           |Move the Camera Down
//|LEFT           |Move the Camera Left
//|RIGHT          |Move the Camera Right
//|=======================================
//
//[source,C,linenums]
//----
  std::function<void()> draw_paddle_1 = [&](){
    glColor3f(/*red*/   1.0,
              /*green*/ 1.0,
              /*blue*/  1.0);
    glBegin(GL_QUADS);
    {
      for(Vertex modelspace : paddle){
        Vertex worldSpace = modelspace
          .rotate(/*radians*/ paddle_1_rotation)
          .translate(/*x*/ -90.0,
                     /*y*/ paddle_1_offset_Y);
        Vertex cameraSpace = worldSpace.translate(/*x*/ -camera_x,
                                                  /*y*/ -camera_y);
        Vertex ndcSpace = cameraSpace.scale(/*x*/ 1.0/100.0,
                                            /*y*/ 1.0/100.0);
        glVertex2f(/*x*/ ndcSpace.x,
                   /*y*/ ndcSpace.y);
      }
    }
    glEnd();
  };
  std::function<void()> draw_paddle_2 = [&](){
    glBegin(GL_QUADS);
    {
      glColor3f(/*red*/   1.0,
                /*green*/ 1.0,
                /*blue*/  0.0);
      for(Vertex modelspace : paddle){
        Vertex worldSpace = modelspace
          .rotate(/*radians*/ paddle_2_rotation)
          .translate(/*x*/ 90.0,
                     /*y*/ paddle_2_offset_Y);
        Vertex cameraSpace = worldSpace.translate(/*x*/ -camera_x,
                                                  /*y*/ -camera_y);
        Vertex ndcSpace = cameraSpace.scale(/*x*/ 1.0/100.0,
                                            /*y*/ 1.0/100.0);
        glVertex2f(/*x*/ ndcSpace.x,
                   /*y*/ ndcSpace.y);
      }
    }
    glEnd();
  };
//----
//
//[source,C,linenums]
//----
  if(7 == *demo_number){
//----
//Draw paddle 1.
//[source,C,linenums]
//----
    draw_paddle_1();
//----
//Draw square, relative to paddle 1.
//[source,C,linenums]
//----
    glColor3f(/*red*/   0.0,
              /*green*/ 0.0,
              /*blue*/  1.0);
    glBegin(GL_QUADS);
    {
      for(Vertex modelspace : square){
        Vertex worldSpace = modelspace
          .translate(/*x*/ 20.0f,
                     /*y*/ 0.0f)
          .rotate(/*radians*/ paddle_1_rotation)
          .translate(/*x*/ -90.0,
                     /*y*/ paddle_1_offset_Y);
        Vertex cameraSpace = worldSpace.translate(/*x*/ -camera_x,
                                                  /*y*/ -camera_y);
        Vertex ndcSpace = cameraSpace.scale(/*x*/ 1.0/100.0,
                                            /*y*/ 1.0/100.0);
        glVertex2f(/*x*/ ndcSpace.x,
                   /*y*/ ndcSpace.y);
      }
    }
    glEnd();
//----
//Draw paddle 2.
//[source,C,linenums]
//----
    draw_paddle_2();
    return;
  }
//----
//== Demo 8 - Rotate the Square About Its Origin
//
//[width="75%",frame="topbot",options="header,footer"]
//|=======================================
//|Keyboard Input |Action
//|w              |Move Left Paddle Up
//|s              |Move Left Paddle Down
//|k              |Move Right Paddle Up
//|i              |Move Right Paddle Down
//|               |
//|d              |Increase Left Paddle's Rotation
//|a              |Decrease Left Paddle's Rotation
//|l              |Increase Right Paddle's Rotation
//|j              |Decrease Right Paddle's Rotation
//|               |
//|UP             |Move the Camera Up
//|DOWN           |Move the Camera Down
//|LEFT           |Move the Camera Left
//|RIGHT          |Move the Camera Right
//|               |
//|q              |Rotate the square around its center.
//|=======================================
//[source,C,linenums]
//----
  static GLfloat square_rotation = 0.0;
  // update_square_rotation
  if (state[SDL_SCANCODE_Q]) {
    square_rotation += 0.1;
  }
  if(8 == *demo_number){
//----
//Draw paddle 1.
//[source,C,linenums]
//----
    draw_paddle_1();
//----
//Draw square, relative to paddle 1.
//[source,C,linenums]
//----
    glColor3f(/*red*/   0.0,
              /*green*/ 0.0,
              /*blue*/  1.0);
    glBegin(GL_QUADS);
    {
      for(Vertex modelspace : square){
        Vertex worldSpace  = modelspace
          .rotate(/*radians*/ square_rotation)
          .translate(/*x*/ 20.0f,
                     /*y*/ 0.0f)
          .rotate(/*radians*/ paddle_1_rotation)
          .translate(/*x*/ -90.0,
                     /*y*/ paddle_1_offset_Y);
        Vertex cameraSpace = worldSpace.translate(/*x*/ -camera_x,
                                                  /*y*/ -camera_y);
        Vertex ndcSpace = cameraSpace.scale(/*x*/ 1.0/100.0,
                                            /*y*/ 1.0/100.0);
        glVertex2f(/*x*/ ndcSpace.x,
                   /*y*/ ndcSpace.y);
      }
      glEnd();
    }
//----
//Draw paddle 2.
//[source,C,linenums]
//----
    draw_paddle_2();
    return;
  }
//----
//== Demo 9 - Rotate the Square About the Paddle
//[width="75%",frame="topbot",options="header,footer"]
//|=======================================
//|Keyboard Input |Action
//|w              |Move Left Paddle Up
//|s              |Move Left Paddle Down
//|k              |Move Right Paddle Up
//|i              |Move Right Paddle Down
//|               |
//|d              |Increase Left Paddle's Rotation
//|a              |Decrease Left Paddle's Rotation
//|l              |Increase Right Paddle's Rotation
//|j              |Decrease Right Paddle's Rotation
//|               |
//|UP             |Move the Camera Up
//|DOWN           |Move the Camera Down
//|LEFT           |Move the Camera Left
//|RIGHT          |Move the Camera Right
//|               |
//|q              |Rotate the square around its center.
//|e              |Rotate the square around the left paddle
//|=======================================
//
//[source,C,linenums]
//----
  static GLfloat rotation_around_paddle_1 = 0.0;
  if (state[SDL_SCANCODE_E]) {
    rotation_around_paddle_1 += 0.1;
  }
//----
//[source,C,linenums]
//----
  if(9 == *demo_number){
//----
//Draw paddle 1.
//[source,C,linenums]
//----
    draw_paddle_1();
//----
//Draw square, relative to paddle 1.
//[source,C,linenums]
//----
    glColor3f(/*red*/   0.0,
              /*green*/ 0.0,
              /*blue*/  1.0);
    glBegin(GL_QUADS);
    {
      for(Vertex modelspace : square){
        Vertex worldSpace  = modelspace
          .rotate(/*radians*/ square_rotation)
          .translate(/*x*/ 20.0f,
                     /*y*/ 0.0f)
          .rotate(/*radians*/ rotation_around_paddle_1)
          .rotate(/*radians*/ paddle_1_rotation)
          .translate(/*x*/ -90.0,
                     /*y*/ paddle_1_offset_Y);
        Vertex cameraSpace = worldSpace.translate(/*x*/ -camera_x,
                                                  /*y*/ -camera_y);
        Vertex ndcSpace = cameraSpace.scale(/*x*/ 1.0/100.0,
                                            /*y*/ 1.0/100.0);
        glVertex2f(/*x*/ ndcSpace.x,
                   /*y*/ ndcSpace.y);
      }
      glEnd();
    }
//----
//Draw paddle 2.
//[source,C,linenums]
//----
    draw_paddle_2();
    return;
  }
//----
//== Demo 10

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
    Vertex3 ortho(GLfloat min_x,
                  GLfloat max_x,
                  GLfloat min_y,
                  GLfloat max_y,
                  GLfloat min_z,
                  GLfloat max_z)
    {
      GLfloat x_length = max_x-min_x;
      GLfloat y_length = max_y-min_y;
      GLfloat z_length = max_z-min_z;
      return
	translate(-(max_x-x_length/2.0),
		  -(max_y-y_length/2.0),
		  -(max_z-z_length/2.0))
        .scale(/*x*/ 1/(x_length/2.0),
               /*y*/ 1/(y_length/2.0),
               /*z*/ 1/(-z_length/2.0));
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
      GLfloat y_angle =  (w / h) * field_of_view;

      GLfloat sheared_x = x / fabs(z) * fabs(nearZ);
      GLfloat sheared_y = y / fabs(z) * fabs(nearZ);
      Vertex3 projected =  Vertex3(/*x*/ sheared_x,
				   /*y*/ sheared_y,
				   /*z*/ z);
      GLfloat x_min_of_box = fabs(nearZ) * tan(field_of_view);
      GLfloat y_min_of_box = fabs(nearZ) * tan(y_angle);
      return projected.ortho(/*min_x*/ -x_min_of_box,
			     /*max_x*/ x_min_of_box,
                             /*min_y*/ -y_min_of_box,
			     /*max_y*/ y_min_of_box,
                             /*min_z*/ nearZ,
			     /*max_z*/ farZ);
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
      {
        Vertex3 ndc_v_1 = f(Vertex3(/*x*/ -1.0,
                                    /*y*/ -1.0,
                                    /*z*/ 0.0));
        glVertex3f(/*x*/ ndc_v_1.x,
                   /*y*/ ndc_v_1.y,
                   /*z*/ ndc_v_1.z);
        Vertex3 ndc_v_2 = f(Vertex3(/*x*/ 1.0,
                                    /*y*/ -1.0,
                                    /*z*/ 0.0));
        glVertex3f(/*x*/ ndc_v_2.x,
                   /*y*/ ndc_v_2.y,
                   /*z*/ ndc_v_2.z);
        Vertex3 ndc_v_3 = f(Vertex3(/*x*/ 1.0,
                                    /*y*/ 1.0,
                                    /*z*/ 0.0));
        glVertex3f(/*x*/ ndc_v_3.x,
                   /*y*/ ndc_v_3.y,
                   /*z*/ ndc_v_3.z);
        Vertex3 ndc_v_4 = f(Vertex3(/*x*/ -1.0,
                                    /*y*/ 1.0,
                                    /*z*/ 0.0));
        glVertex3f(/*x*/ ndc_v_4.x,
                   /*y*/ ndc_v_4.y,
                   /*z*/ ndc_v_4.z);
      }
      glEnd();
    };
//----
//[source,C,linenums]
//----
  const std::vector<Vertex3> paddle3D = {
    Vertex3(/*x*/ -10.0,
            /*y*/ -30.0,
            /*z*/ 0.0),
    Vertex3(/*x*/ 10.0,
            /*y*/ -30.0,
            /*z*/ 0.0),
    Vertex3(/*x*/ 10.0,
            /*y*/ 30.0,
            /*z*/ 0.0),
    Vertex3(/*x*/ -10.0,
            /*y*/ 30.0,
            /*z*/ 0.0)
  };
  const std::vector<Vertex3> square3D = {
    Vertex3(/*x*/ -5.0,
            /*y*/ -5.0,
            /*z*/ 0.0),
    Vertex3(/*x*/ 5.0,
            /*y*/ -5.0,
            /*z*/ 0.0),
    Vertex3(/*x*/ 5.0,
            /*y*/ 5.0,
            /*z*/ 0.0),
    Vertex3(/*x*/ -5.0,
            /*y*/ 5.0,
            /*z*/ 0.0)
  };


//// TODO -- update newposition to have better names for 3d
  if(10 == *demo_number){
//----
//Draw paddle 1.
//[source,C,linenums]
//----
    draw_paddle_1();
//----
//Draw square, relative to paddle 1.
//[source,C,linenums]
//----
    glColor3f(/*red*/   0.0,
              /*green*/ 0.0,
              /*blue*/  1.0);
    glBegin(GL_QUADS);
    {
      for(Vertex3 modelspace : square3D){
        Vertex3 worldSpace = modelspace
          .rotateZ(/*radians*/ square_rotation)
          .translate(/*x*/ 20.0f,
                     /*y*/ 0.0f,
                     /*z*/ -10.0f)  // NEW, using a different Z value
          .rotateZ(/*radians*/ rotation_around_paddle_1)
          .rotateZ(/*radians*/ paddle_1_rotation)
          .translate(/*x*/ -90.0,
                     /*y*/ paddle_1_offset_Y,
                     /*z*/ 0.0);
        Vertex3 cameraSpace = worldSpace
          .translate(/*x*/ -camera_x,
                     /*y*/ -camera_y,
                     /*z*/ 0.0);
        Vertex3 ndcSpace = cameraSpace
          .ortho(/*min_x*/ -100.0f,
                 /*max_x*/ 100.0f,
                 /*min_y*/ -100.0f,
                 /*max_y*/ 100.0f,
                 /*min_z*/ 100.0f,
                 /*max_z*/ -100.0f);
        glVertex3f(/*x*/ ndcSpace.x,
                   /*y*/ ndcSpace.y,
                   /*z*/ ndcSpace.y);
      }
      glEnd();
    }
//----
//Draw paddle 2.
//[source,C,linenums]
//----
    draw_paddle_2();
    return;
  }
//----
//
//== Demo 11
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


  if(11 == *demo_number){
//----
//Draw paddle 1, relative to the offset.
//[source,C,linenums]
//----
    glColor3f(/*red*/   1.0,
              /*green*/ 1.0,
              /*blue*/  1.0);
    glBegin(GL_QUADS);
    {
      for(Vertex3 modelspace : paddle3D){
        Vertex3 worldSpace = modelspace
          .rotateZ(/*radians*/ paddle_1_rotation)
          .translate(/*x*/ -90.0,
                     /*y*/ paddle_1_offset_Y,
                     /*z*/ 0.0);
        // new camera transformations
        Vertex3 cameraSpace = worldSpace
          .translate(/*x*/ -moving_camera_x,      // NEW
                     /*y*/ -moving_camera_y,      // NEW
                     /*z*/ -moving_camera_z)      // NEW
          .rotateY(/*radians*/ -moving_camera_rot_y)    // NEW
          .rotateX(/*radians*/ -moving_camera_rot_x);   // NEW
        // end new camera transformations
        Vertex3 ndcSpace = cameraSpace
          .ortho(/*min_x*/ -100.0f,
                 /*max_x*/ 100.0f,
                 /*min_y*/ -100.0f,
                 /*max_y*/ 100.0f,
                 /*min_z*/ 100.0f,
                 /*max_z*/ -100.0f);
        glVertex3f(/*x*/ ndcSpace.x,
                   /*y*/ ndcSpace.y,
                   /*z*/ ndcSpace.z);
      }
    }
    glEnd();
//----
//Draw square, relative to paddle 1.
//[source,C,linenums]
//----
    glColor3f(/*red*/   0.0,
              /*green*/ 0.0,
              /*blue*/  1.0);
    glBegin(GL_QUADS);
    {
      for(Vertex3 modelspace : square3D){
        Vertex3 worldSpace = modelspace
          .rotateZ(/*radians*/ square_rotation)
          .translate(/*x*/ 20.0f,
                     /*y*/ 0.0f,
                     /*z*/ -10.0f)  // NEW, using a different Z value
          .rotateZ(/*radians*/ rotation_around_paddle_1)
          .rotateZ(/*radians*/ paddle_1_rotation)
          .translate(/*x*/ -90.0,
                     /*y*/ paddle_1_offset_Y,
                     /*z*/ 0.0);
        // new camera transformations
        Vertex3 cameraSpace = worldSpace
          .translate(/*x*/ -moving_camera_x,      // NEW
                     /*y*/ -moving_camera_y,      // NEW
                     /*z*/ -moving_camera_z)      // NEW
          .rotateY(/*radians*/ -moving_camera_rot_y)    // NEW
          .rotateX(/*radians*/ -moving_camera_rot_x);   // NEW
        // end new camera transformations
        Vertex3 ndcSpace = cameraSpace
          .ortho(/*min_x*/ -100.0f,
                 /*max_x*/ 100.0f,
                 /*min_y*/ -100.0f,
                 /*max_y*/ 100.0f,
                 /*min_z*/ 100.0f,
                 /*max_z*/ -100.0f);
        glVertex3f(/*x*/ ndcSpace.x,
                   /*y*/ ndcSpace.y,
                   /*z*/ ndcSpace.z);
      }
      glEnd();
    }
//----
//Draw paddle 2, relative to the offset.
//[source,C,linenums]
//----
    glBegin(GL_QUADS);
    {
      glColor3f(/*red*/   1.0,
                /*green*/ 1.0,
                /*blue*/  0.0);
      for(Vertex3 modelspace : paddle3D){
        Vertex3 worldSpace = modelspace
          .rotateZ(/*radians*/ paddle_2_rotation)
          .translate(/*x*/ 90.0,
                     /*y*/ paddle_2_offset_Y,
                     /*z*/ 0.0);
        // new camera transformations
        Vertex3 cameraSpace = worldSpace
          .translate(/*x*/ -moving_camera_x,      // NEW
                     /*y*/ -moving_camera_y,      // NEW
                     /*z*/ -moving_camera_z)      // NEW
          .rotateY(/*radians*/ -moving_camera_rot_y)    // NEW
          .rotateX(/*radians*/ -moving_camera_rot_x);   // NEW
        // end new camera transformations
        Vertex3 ndcSpace = cameraSpace
          .ortho(/*min_x*/ -100.0f,
                 /*max_x*/ 100.0f,
                 /*min_y*/ -100.0f,
                 /*max_y*/ 100.0f,
                 /*min_z*/ 100.0f,
                 /*max_z*/ -100.0f);
        glVertex3f(/*x*/ ndcSpace.x,
                   /*y*/ ndcSpace.y,
                   /*z*/ ndcSpace.z);
      }
    }
    glEnd();
    return;
  }



//== Demo 12
  if(*demo_number >= 12){
    glEnable(GL_DEPTH_TEST);
  }
  if(12 == *demo_number){
    *demo_number = 11;
    return;
  }
//----
//== Demo 13
//[source,C,linenums]
//----
  if(*demo_number >= 13){
    static bool first_frame = true;
    if(first_frame){
      moving_camera_z = 400.0; // for the perspective to look right
      first_frame = false;
    }
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
  if(13 == *demo_number){
    // every shape is projected the same way
    transformationStack.push_back([&](Vertex3 v){
        return v.perspective(-0.1f,
                             -1000.0f);
      });
    // THE REST IS THE SAME AS THE PREVIOUS
    // every shape is relative to the camera
    // camera transformation #3 - tilt your head down
    transformationStack.push_back([&](Vertex3 v){
        return v.rotateX(/*radians*/ -moving_camera_rot_x);
      });
    // camera transformation #2 - turn your head to the side
    transformationStack.push_back([&](Vertex3 v){
        return v.rotateY(/*radians*/ -moving_camera_rot_y);
      });
    // camera transformation #1 - move to the origin
    transformationStack.push_back([&](Vertex3 v){
        return v.translate(/*x*/ - moving_camera_x,
                           /*y*/ - moving_camera_y,
                           /*z*/ - moving_camera_z);
      });
    transformationStack.push_back([&](Vertex3 v){
        return v.translate(/*x*/ -90.0f,
                           /*y*/ 0.0f + paddle_1_offset_Y,
                           /*z*/ 0.0f);
      });
//----
//Draw paddle 1, relative to the offset.
//[source,C,linenums]
//----
    glColor3f(/*red*/   1.0,
              /*green*/ 1.0,
              /*blue*/  1.0);
    transformationStack.push_back([&](Vertex3 v){
        return v.rotateZ(/*radians*/ paddle_1_rotation);
      });
    transformationStack.push_back([&](Vertex3 v){
        return v.scale(/*x*/ 10.0f,
                       /*y*/ 30.0f,
                       /*z*/ 1.0f);
      });
    draw_square3_programmable(applyTransformationStack);
    transformationStack.pop_back();
    transformationStack.pop_back();
//----
//Draw square, relative to paddle 1.
//[source,C,linenums]
//----
    glColor3f(/*red*/   0.0,
              /*green*/ 0.0,
              /*blue*/  1.0);
    {
      transformationStack.push_back([&](Vertex3 v){
          return v.rotateZ(/*radians*/ paddle_1_rotation);
        });
      transformationStack.push_back([&](Vertex3 v){
          return v.rotateZ(/*radians*/ rotation_around_paddle_1);
        });
      transformationStack.push_back([&](Vertex3 v){
          return v.translate(/*x*/ 20.0f,
                             /*y*/ 0.0f,
                             /*z*/ -10.0f); // NEW, using a non zero
        });
      transformationStack.push_back([&](Vertex3 v){
          return v.rotateZ(/*radians*/ square_rotation);
        });
      transformationStack.push_back([&](Vertex3 v){
          return v.scale(/*x*/ 5.0f,
                         /*y*/ 5.0f,
                         /*z*/ 0.0f);
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
//----
//Draw paddle 2, relative to the offset.
//[source,C,linenums]
//----
    glColor3f(/*red*/   1.0,
              /*green*/ 1.0,
              /*blue*/  0.0);
    transformationStack.push_back([&](Vertex3 v){
        return v.translate(/*x*/ 90.0f,
                           /*y*/ 0.0f + paddle_2_offset_Y,
                           /*z*/ 0.0f);
      });
    transformationStack.push_back([&](Vertex3 v){
        return v.rotateZ(/*radians*/ paddle_2_rotation);
      });
    transformationStack.push_back([&](Vertex3 v){
        return v.scale(/*x*/ 10.0f,
                       /*y*/ 30.0f,
                       /*z*/ 1.0f);
      });
    draw_square3_programmable(applyTransformationStack);
    transformationStack.pop_back();
    transformationStack.pop_back();
    transformationStack.pop_back();
    transformationStack.pop_back();
    transformationStack.pop_back();
    transformationStack.pop_back();
    transformationStack.pop_back();
    return;
  }
//----
//== Demo 14
//[source,C,linenums]
//----
  if(*demo_number >= 14){
    // for whatever reason, gluPerspective flips the z values
    glClearDepth(1.1f );
    glDepthFunc(GL_LEQUAL);
  }
//----
//[source,C,linenums]
//----
  std::function<void()> draw_square_opengl2point1 = [&](){
    glBegin(GL_QUADS);
    {
      glVertex2f(/*x*/ -1.0,
                 /*y*/ -1.0);
      glVertex2f(/*x*/ 1.0,
                 /*y*/ -1.0);
      glVertex2f(/*x*/ 1.0,
                 /*y*/ 1.0);
      glVertex2f(/*x*/ -1.0,
                 /*y*/ 1.0);
    }
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
      glRotatef(/*degrees*/ RAD_TO_DEG(-moving_camera_rot_x),
                /*x*/ 1.0,
                /*y*/ 0.0,
                /*z*/ 0.0);
      glRotatef(/*degrees*/ RAD_TO_DEG(-moving_camera_rot_y),
                /*x*/ 0.0,
                /*y*/ 1.0,
                /*z*/ 0.0);
      glTranslatef(/*x*/ -moving_camera_x,
                   /*y*/ -moving_camera_y,
                   /*z*/ -moving_camera_z);
    }
//----
//Draw paddle 1, relative to the offset.
//[source,C,linenums]
//----
    glPushMatrix();
    glColor3f(/*red*/   1.0,
              /*green*/ 1.0,
              /*blue*/  1.0);
    glTranslatef(/*x*/ -90.0f,
                 /*y*/ 0.0f + paddle_1_offset_Y,
                 /*z*/ 0.0);
    glRotatef(/*degrees*/ RAD_TO_DEG(paddle_1_rotation),
              /*x*/ 0.0,
              /*y*/ 0.0,
              /*z*/ 1.0);
    // scaling of this object should not affect the relative square
    glPushMatrix();
    {
      glScalef(/*x*/ 10.0f,
               /*y*/ 30.0f,
               /*z*/ 0.0f);
      draw_square_opengl2point1();
      glPopMatrix();
    }
//----
//Draw square, relative to paddle 1.
//[source,C,linenums]
//----
    glColor3f(/*red*/   0.0,
              /*green*/ 0.0,
              /*blue*/  1.0);
    glRotatef(/*degrees*/ RAD_TO_DEG(rotation_around_paddle_1),
              /*x*/ 0.0f,
              /*y*/ 0.0f,
              /*z*/ 1.0f);
    glTranslatef(/*x*/ 20.0f,
                 /*y*/ 0.0f,
                 /*z*/ -10.0f);
    glRotatef(/*degrees*/ RAD_TO_DEG(square_rotation),
              /*x*/ 0.0f,
              /*y*/ 0.0f,
              /*z*/ 1.0f);
    glScalef(/*x*/ 5.0f,
             /*y*/ 5.0f,
             /*z*/ 5.0f);
    draw_square_opengl2point1();
    glPopMatrix();
//----
//Draw paddle 2, relative to the offset.
//[source,C,linenums]
//----
    glPushMatrix();
    glColor3f(/*red*/   1.0,
              /*green*/ 1.0,
              /*blue*/  0.0);
    glTranslatef(/*x*/ 90.0f,
                 /*y*/ 0.0f + paddle_2_offset_Y,
                 /*z*/ 0.0);
    glRotatef(/*degrees*/ RAD_TO_DEG(paddle_2_rotation),
              /*x*/ 0.0,
              /*y*/ 0.0,
              /*z*/ 1.0);
    glScalef(/*x*/ 10.0f,
             /*y*/ 30.0f,
             /*z*/ 0.0f);
    draw_square_opengl2point1();
    glPopMatrix();
    return;
  }
  // in later demos,
  //glClearDepth(1.0f );
  //glEnable(GL_DEPTH_TEST );
  //glDepthFunc(GL_LEQUAL );
  return;
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
