/*
 * William Emerison Six
 *
 * Copyright 2016 - William Emerison Six
 * All rights reserved
 * Distributed under LGPL 2.1 or Apache 2.0
 */

#include <stdio.h>
#include "main.h"

SDL_Window *window;
SDL_Renderer *renderer;
SDL_GLContext glcontext;
SDL_PixelFormat RGBAFormat;

void
print_usage(){
  puts("Usage -- math4graphics demonumber");
}


int
main(int argc, char** argv)
{
  int demo_number = 0;
  // get demo number from the command line
  {
    if(argc == 1){
      print_usage();
      return 0;
    }
    demo_number = atoi(argv[1]);
  }

  // initial SDL, OpenGL, GLEW
  {
    if (SDL_Init(SDL_INIT_EVERYTHING) != 0)
      {
        SDL_LogMessage(SDL_LOG_CATEGORY_APPLICATION,
                       SDL_LOG_PRIORITY_ERROR,
                       "Error: %s\n",
                       SDL_GetError());
        return 1;
      }
    
    // Initialize SDL Attributes
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
    
    if(NULL == (window = SDL_CreateWindow("math4graphics",
                                          SDL_WINDOWPOS_CENTERED,
                                          SDL_WINDOWPOS_CENTERED,
                                          500,
                                          500,
                                          SDL_WINDOW_OPENGL|SDL_WINDOW_RESIZABLE))){
      SDL_LogMessage(SDL_LOG_CATEGORY_APPLICATION,
                     SDL_LOG_PRIORITY_ERROR,
                     "Could not create window: %s\n",
                     SDL_GetError());
      return 1;
    }
    
    glcontext = SDL_GL_CreateContext(window);
    // init GLEW
    glewExperimental = GL_TRUE;
    glewInit();
    // TODO - figure out why this isn't working on Windows
#ifndef _WINDOWS
    SDL_GL_MakeCurrent(glcontext, window);
#endif
    // log opengl version
    SDL_LogMessage(SDL_LOG_CATEGORY_APPLICATION,
                   SDL_LOG_PRIORITY_INFO,
                   "OpenGL version loaded: %s\n",
                   glGetString(GL_VERSION));
    // initialize OpenGL
    glClearColor(0,0,0,1);
  }
  
  SDL_bool quit = SDL_FALSE;
  do{
    quit = render_scene(demo_number);
    SDL_GL_SwapWindow(window);
  } while (quit != SDL_TRUE);
  // Cleanup
  SDL_GL_DeleteContext(glcontext);
  SDL_DestroyWindow(window);
  SDL_Quit();
  return 0;
}

SDL_bool
render_scene(int demo_number){
  SDL_Event event;
  if(0 == demo_number){
    /*
     *  Demo 0 -- black screen
     */
    glClear(GL_COLOR_BUFFER_BIT);
    // handle events
    while (SDL_PollEvent(&event))
      {
        if (event.type == SDL_QUIT){
          return SDL_TRUE;        
        }
      }
    return SDL_FALSE;
  }
  if(1 == demo_number){
    /*
     *  Demo 1 -- two rectangles
     */
    // handle events
    glClear(GL_COLOR_BUFFER_BIT);
    while (SDL_PollEvent(&event))
      {
        if (event.type == SDL_QUIT){
          return SDL_TRUE;        
        }
      }
    
    // draw paddle 1
    glColor3f(1.0,1.0,1.0);
    glBegin(GL_QUADS);
    {
      glVertex2f(-1.0,-0.3);
      glVertex2f(-0.8,-0.3);
      glVertex2f(-0.8,0.3);
      glVertex2f(-1.0,0.3);
      glEnd();
    }
    // draw paddle 2
    glColor3f(1.0,1.0,0.0);
    glBegin(GL_QUADS);
    {
      glVertex2f(0.8,-0.3);
      glVertex2f(1.0,-0.3);
      glVertex2f(1.0,0.3);
      glVertex2f(0.8,0.3);
      glEnd();
    }
    
    return SDL_FALSE;
  }
  if(2 == demo_number){
    /*
     *  Demo 2 -- two paddles and handle events
     */
    // handle events
    glClear(GL_COLOR_BUFFER_BIT);
    while (SDL_PollEvent(&event))
      {
        if (event.type == SDL_QUIT){
          return SDL_TRUE;        
        }
      }
    
    static float paddle_1_offset_Y = 0.0;
    static float paddle_2_offset_Y = 0.0;
    
    const Uint8 *state = SDL_GetKeyboardState(NULL);
    
    // handle keyboard input
    {
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
    }
    
    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    glBegin(GL_QUADS);
    {
      glVertex2f(-1.0,-0.3+paddle_1_offset_Y);
      glVertex2f(-0.8,-0.3+paddle_1_offset_Y);
      glVertex2f(-0.8,0.3+paddle_1_offset_Y);
      glVertex2f(-1.0,0.3+paddle_1_offset_Y);
      glEnd();
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    glBegin(GL_QUADS);
    {
      glVertex2f(0.8,-0.3+paddle_2_offset_Y);
      glVertex2f(1.0,-0.3+paddle_2_offset_Y);
      glVertex2f(1.0,0.3+paddle_2_offset_Y);
      glVertex2f(0.8,0.3+paddle_2_offset_Y);
      glEnd();
    }
    
    return SDL_FALSE;
  }
  
  // in later demos,
  //glClearDepth( 1.0f );
  //glEnable( GL_DEPTH_TEST );
  //glDepthFunc( GL_LEQUAL );
  
}
