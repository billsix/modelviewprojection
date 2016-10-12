/*
 * William Emerison Six
 *
 * Copyright 2016 - William Emerison Six
 * All rights reserved
 * Distributed under LGPL 2.1 or Apache 2.0
 */

#include <stdio.h>
#include <math.h>
#include <functional>
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
    SDL_GL_MakeCurrent(window,glcontext);
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
  struct vertex { float x; float y;};
  std::function<void(struct vertex)> draw_paddle_relative_to =
    [&](struct vertex center){
       glBegin(GL_QUADS);
       {
         glVertex2f(center.x-0.1,center.y-0.3);
         glVertex2f(center.x+0.1,center.y-0.3);
         glVertex2f(center.x+0.1,center.y+0.3);
         glVertex2f(center.x-0.1,center.y+0.3);
         glEnd();
       }
  };
  if(3 == demo_number){
    /*
     *  Demo 3
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
    {
      struct vertex center;
      center.x = -0.9f;
      center.y= 0.0f + paddle_1_offset_Y;
      draw_paddle_relative_to(center);
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      struct vertex center;
      center.x = 0.9f;
      center.y= 0.0f + paddle_2_offset_Y;
      draw_paddle_relative_to(center);
    }
    return SDL_FALSE;
  }
  typedef std::function<struct vertex (struct vertex)> vertex_transformer;
  vertex_transformer model_space_to_device_space =
    [&](struct vertex modelspace){
      struct vertex device_coordinate ;
      device_coordinate.x=modelspace.x/100.0f;
      device_coordinate.y=modelspace.y/100.0f;
      return device_coordinate;
  };
  if(4 == demo_number){
    /*
     *  Demo 3
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
        paddle_1_offset_Y -= 10.0;
      }
      if (state[SDL_SCANCODE_W]) {
        paddle_1_offset_Y += 10.0;
      }
      if (state[SDL_SCANCODE_K]) {
        paddle_2_offset_Y -= 10.0;
      }
      if (state[SDL_SCANCODE_I]) {
        paddle_2_offset_Y += 10.0;
      }
    }

    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      struct vertex center;
      center.x = -90.0f;
      center.y= 0.0f + paddle_1_offset_Y;
      draw_paddle_relative_to(model_space_to_device_space(center));
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      struct vertex center;
      center.x = 90.0f;
      center.y= 0.0f + paddle_2_offset_Y;
      draw_paddle_relative_to(model_space_to_device_space(center));
    }
    return SDL_FALSE;
  }


  std::function<void (vertex_transformer)> draw_paddle_programmable =
    [&](vertex_transformer f){
      glBegin(GL_QUADS);
      {
        struct vertex local_v_1;
        local_v_1.x = -10.0; local_v_1.y = -30.0;
        struct vertex global_v_1 = f(local_v_1);
        glVertex2f(global_v_1.x,global_v_1.y);
        struct vertex local_v_2 ;
        local_v_2.x = 10.0, local_v_2.y = -30.0;
        struct vertex global_v_2 = f(local_v_2);
        glVertex2f(global_v_2.x,global_v_2.y);
        struct vertex local_v_3;
        local_v_3.x = 10.0;local_v_3.y = 30.0;
        struct vertex global_v_3 = f(local_v_3);
        glVertex2f(global_v_3.x,global_v_3.y);
        struct vertex local_v_4;
        local_v_4.x = -10.0; local_v_4.y = 30.0;
        struct vertex global_v_4 = f(local_v_4);
        glVertex2f(global_v_4.x,global_v_4.y);
        glEnd();
      }
  };
  auto translate = [&](float x,
                       float y,
                       struct vertex modelspace){
    struct vertex translated_vertex;
    translated_vertex.x = modelspace.x + x;
    translated_vertex.y = modelspace.y + y;
    return translated_vertex;
  };
  if(5 == demo_number){
    /*
     *  Demo 3
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
        paddle_1_offset_Y -= 10.0;
      }
      if (state[SDL_SCANCODE_W]) {
        paddle_1_offset_Y += 10.0;
      }
      if (state[SDL_SCANCODE_K]) {
        paddle_2_offset_Y -= 10.0;
      }
      if (state[SDL_SCANCODE_I]) {
        paddle_2_offset_Y += 10.0;
      }
    }

    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      vertex_transformer local_coordinates_to_device_coordinates =
        [&](struct vertex vertex_local_coordinates){
           struct vertex vertex_translated = translate(-90.0f,
                                                       0.0f + paddle_1_offset_Y,
                                                       vertex_local_coordinates);
           return model_space_to_device_space(vertex_translated);
      };

      draw_paddle_programmable(local_coordinates_to_device_coordinates);
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      vertex_transformer local_coordinates_to_device_coordinates =
        [&](struct vertex vertex_local_coordinates){
           struct vertex vertex_translated = translate(90.0f,
                                                       0.0f + paddle_2_offset_Y,
                                                       vertex_local_coordinates);
           return model_space_to_device_space(vertex_translated);
      };
      draw_paddle_programmable(local_coordinates_to_device_coordinates);
    }
    return SDL_FALSE;
  }
  auto rotate = [&](float angle_in_radians,
                   struct vertex modelspace){
    struct vertex rotated_vertex;
    rotated_vertex.x = ((float) modelspace.x*cos(angle_in_radians)
                        - modelspace.y*sin(angle_in_radians));
    rotated_vertex.y = ((float) modelspace.x*sin(angle_in_radians)
                        + modelspace.y*cos(angle_in_radians));
    return rotated_vertex;
  };
  if(6 == demo_number){
    /*
     *  Demo 3
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
    static float paddle_1_rotation = 0.0;
    static float paddle_2_rotation = 0.0;

    const Uint8 *state = SDL_GetKeyboardState(NULL);

    // handle keyboard input
    {
      if (state[SDL_SCANCODE_S]) {
        paddle_1_offset_Y -= 10.0;
      }
      if (state[SDL_SCANCODE_W]) {
        paddle_1_offset_Y += 10.0;
      }
      if (state[SDL_SCANCODE_K]) {
        paddle_2_offset_Y -= 10.0;
      }
      if (state[SDL_SCANCODE_I]) {
        paddle_2_offset_Y += 10.0;
      }
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
    }

    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      vertex_transformer local_coordinates_to_device_coordinates =
        [&](struct vertex vertex_local_coordinates){
           struct vertex vertex_rotated = rotate(paddle_1_rotation,
                                                 vertex_local_coordinates);
           struct vertex vertex_translated = translate(-90.0f,
                                                       0.0f + paddle_1_offset_Y,
                                                       vertex_rotated);
           return model_space_to_device_space(vertex_translated);
      };

      draw_paddle_programmable(local_coordinates_to_device_coordinates);
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      vertex_transformer local_coordinates_to_device_coordinates =
        [&](struct vertex vertex_local_coordinates){
           struct vertex vertex_rotated = rotate(paddle_2_rotation,
                                                 vertex_local_coordinates);
           struct vertex vertex_translated = translate(90.0f,
                                                       0.0f + paddle_2_offset_Y,
                                                       vertex_rotated);
           return model_space_to_device_space(vertex_translated);
      };
      draw_paddle_programmable(local_coordinates_to_device_coordinates);
    }
    return SDL_FALSE;
  }
  if(7 == demo_number){
    /*
     *  Demo 7 - moving camera
     */
    // handle events
    glClear(GL_COLOR_BUFFER_BIT);
    while (SDL_PollEvent(&event))
      {
        if (event.type == SDL_QUIT){
          return SDL_TRUE;
        }
      }

    static float camera_x = 0.0;
    static float camera_y = 0.0;

    static float paddle_1_offset_Y = 0.0;
    static float paddle_2_offset_Y = 0.0;
    static float paddle_1_rotation = 0.0;
    static float paddle_2_rotation = 0.0;

    const Uint8 *state = SDL_GetKeyboardState(NULL);

    // handle keyboard input
    {
      if (state[SDL_SCANCODE_S]) {
        paddle_1_offset_Y -= 10.0;
      }
      if (state[SDL_SCANCODE_W]) {
        paddle_1_offset_Y += 10.0;
      }
      if (state[SDL_SCANCODE_K]) {
        paddle_2_offset_Y -= 10.0;
      }
      if (state[SDL_SCANCODE_I]) {
        paddle_2_offset_Y += 10.0;
      }
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
    }

    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      vertex_transformer local_coordinates_to_device_coordinates =
        [&](struct vertex vertex_local_coordinates){
           struct vertex vertex_rotated = rotate(paddle_1_rotation,
                                                 vertex_local_coordinates);
           struct vertex vertex_translated = translate(-90.0f,
                                                       0.0f + paddle_1_offset_Y,
                                                       vertex_rotated);
           struct vertex camera_coordinates;
           camera_coordinates.x = vertex_translated.x - camera_x;
           camera_coordinates.y = vertex_translated.y - camera_y;
           return model_space_to_device_space(camera_coordinates);
      };

      draw_paddle_programmable(local_coordinates_to_device_coordinates);
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      vertex_transformer local_coordinates_to_device_coordinates =
        [&](struct vertex vertex_local_coordinates){
           struct vertex vertex_rotated = rotate(paddle_2_rotation,
                                                 vertex_local_coordinates);
           struct vertex vertex_translated = translate(90.0f,
                                                       0.0f + paddle_2_offset_Y,
                                                       vertex_rotated);
           struct vertex camera_coordinates;
           camera_coordinates.x = vertex_translated.x - camera_x;
           camera_coordinates.y = vertex_translated.y - camera_y;
           return model_space_to_device_space(camera_coordinates);
      };
      draw_paddle_programmable(local_coordinates_to_device_coordinates);
    }
    return SDL_FALSE;
  }
  std::function<void (vertex_transformer)> draw_square_programmable =
    [&](vertex_transformer f){
      glBegin(GL_QUADS);
      {
        struct vertex local_v_1;
        local_v_1.x = -5.0; local_v_1.y = -5.0;
        struct vertex global_v_1 = f(local_v_1);
        glVertex2f(global_v_1.x,global_v_1.y);
        struct vertex local_v_2 ;
        local_v_2.x = 5.0, local_v_2.y = -5.0;
        struct vertex global_v_2 = f(local_v_2);
        glVertex2f(global_v_2.x,global_v_2.y);
        struct vertex local_v_3;
        local_v_3.x = 5.0;local_v_3.y = 5.0;
        struct vertex global_v_3 = f(local_v_3);
        glVertex2f(global_v_3.x,global_v_3.y);
        struct vertex local_v_4;
        local_v_4.x = -5.0; local_v_4.y = 5.0;
        struct vertex global_v_4 = f(local_v_4);
        glVertex2f(global_v_4.x,global_v_4.y);
        glEnd();
      }
  };

  if(8 == demo_number){
    /*
     *  Demo 8 - Relative location
     */
    // handle events
    glClear(GL_COLOR_BUFFER_BIT);
    while (SDL_PollEvent(&event))
      {
        if (event.type == SDL_QUIT){
          return SDL_TRUE;
        }
      }

    static float camera_x = 0.0;
    static float camera_y = 0.0;

    static float paddle_1_offset_Y = 0.0;
    static float paddle_2_offset_Y = 0.0;
    static float paddle_1_rotation = 0.0;
    static float paddle_2_rotation = 0.0;

    const Uint8 *state = SDL_GetKeyboardState(NULL);

    // handle keyboard input
    {
      if (state[SDL_SCANCODE_S]) {
        paddle_1_offset_Y -= 10.0;
      }
      if (state[SDL_SCANCODE_W]) {
        paddle_1_offset_Y += 10.0;
      }
      if (state[SDL_SCANCODE_K]) {
        paddle_2_offset_Y -= 10.0;
      }
      if (state[SDL_SCANCODE_I]) {
        paddle_2_offset_Y += 10.0;
      }
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
    }

    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      vertex_transformer local_coordinates_to_device_coordinates =
        [&](struct vertex vertex_local_coordinates){
           struct vertex vertex_rotated = rotate(paddle_1_rotation,
                                                 vertex_local_coordinates);
           struct vertex vertex_translated = translate(-90.0f,
                                                       0.0f + paddle_1_offset_Y,
                                                       vertex_rotated);
           struct vertex camera_coordinates;
           camera_coordinates.x = vertex_translated.x - camera_x;
           camera_coordinates.y = vertex_translated.y - camera_y;
           return model_space_to_device_space(camera_coordinates);
      };

      draw_paddle_programmable(local_coordinates_to_device_coordinates);
    }
    // draw square, relative to paddle 1
    glColor3f(0.0,0.0,1.0);
    {
      vertex_transformer local_coordinates_to_device_coordinates =
        [&](struct vertex vertex_local_coordinates){
           struct vertex square_translated = translate(20.0f,
                                                       0.0f,
                                                       vertex_local_coordinates);
           struct vertex vertex_rotated = rotate(paddle_1_rotation,
                                                 square_translated);
           struct vertex vertex_translated = translate(-90.0f,
                                                       0.0f + paddle_1_offset_Y,
                                                       vertex_rotated);
           struct vertex camera_coordinates;
           camera_coordinates.x = vertex_translated.x - camera_x;
           camera_coordinates.y = vertex_translated.y - camera_y;
           return model_space_to_device_space(camera_coordinates);
      };

      draw_square_programmable(local_coordinates_to_device_coordinates);
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      vertex_transformer local_coordinates_to_device_coordinates =
        [&](struct vertex vertex_local_coordinates){
           struct vertex vertex_rotated = rotate(paddle_2_rotation,
                                                 vertex_local_coordinates);
           struct vertex vertex_translated = translate(90.0f,
                                                       0.0f + paddle_2_offset_Y,
                                                       vertex_rotated);
           struct vertex camera_coordinates;
           camera_coordinates.x = vertex_translated.x - camera_x;
           camera_coordinates.y = vertex_translated.y - camera_y;
           return model_space_to_device_space(camera_coordinates);
      };
      draw_paddle_programmable(local_coordinates_to_device_coordinates);
    }
    return SDL_FALSE;
  }
  // std::function<void()> draw_paddle_opengl2point1 = [&](){
  //   glBegin(GL_QUADS);
  //   {
  //     glVertex2f(-10.0, -30.0);
  //     glVertex2f(10.0, -30.0);
  //     glVertex2f(10.0, 30.0);
  //     glVertex2f(-10.0, 30.0);
  //     glEnd();
  //   }
  // };

  // std::function<double(double)> RAD_TO_DEG = [&](double rad){
  //   return 57.296 * rad;
  // };
  // if(8 == demo_number){
  //   /*
  //    *  Demo 7 - OpenGL Matricies
  //    */
  //   // handle events
  //   glClear(GL_COLOR_BUFFER_BIT);
  //   while (SDL_PollEvent(&event))
  //     {
  //       if (event.type == SDL_QUIT){
  //         return SDL_TRUE;
  //       }
  //       if (event.type == SDL_WINDOWEVENT){
  //         if(event.window.event == SDL_WINDOWEVENT_RESIZED){
  //           int w = event.window.data1, h = event.window.data2;
  //           glViewport(0,0,w,h);
  //         }
  //       }
  //     }

  //   static float camera_x = 0.0;
  //   static float camera_y = 0.0;

  //   static float paddle_1_offset_Y = 0.0;
  //   static float paddle_2_offset_Y = 0.0;
  //   static float paddle_1_rotation = 0.0;
  //   static float paddle_2_rotation = 0.0;

  //   const Uint8 *state = SDL_GetKeyboardState(NULL);

  //   // handle keyboard input
  //   {
  //     if (state[SDL_SCANCODE_S]) {
  //       paddle_1_offset_Y -= 10.0;
  //     }
  //     if (state[SDL_SCANCODE_W]) {
  //       paddle_1_offset_Y += 10.0;
  //     }
  //     if (state[SDL_SCANCODE_K]) {
  //       paddle_2_offset_Y -= 10.0;
  //     }
  //     if (state[SDL_SCANCODE_I]) {
  //       paddle_2_offset_Y += 10.0;
  //     }
  //     if (state[SDL_SCANCODE_A]) {
  //       paddle_1_rotation -= 0.1;
  //     }
  //     if (state[SDL_SCANCODE_D]) {
  //       paddle_1_rotation += 0.1;
  //     }
  //     if (state[SDL_SCANCODE_J]) {
  //       paddle_2_rotation -= 0.1;
  //     }
  //     if (state[SDL_SCANCODE_L]) {
  //       paddle_2_rotation += 0.1;
  //     }
  //     if (state[SDL_SCANCODE_UP]) {
  //       camera_y += 10.0;
  //     }
  //     if (state[SDL_SCANCODE_DOWN]) {
  //       camera_y -= 10.0;
  //     }
  //     if (state[SDL_SCANCODE_LEFT]) {
  //       camera_x -= 10.0;
  //     }
  //     if (state[SDL_SCANCODE_RIGHT]) {
  //       camera_x += 10.0;
  //     }
  //   }

  //   // set up Camera
  //   {
  //     // define the projection
  //     glMatrixMode(GL_PROJECTION);
  //     glLoadIdentity();
  //     glOrtho(-100,100,-100,100,-100,100);
  //     // move the "camera"
  //     glMatrixMode(GL_MODELVIEW);
  //     glLoadIdentity();
  //     glTranslatef(-camera_x,
  //                  -camera_y,
  //                  0.0);
  //   }

  //   // draw paddle 1, relative to the offset
  //   glPushMatrix();
  //   glColor3f(1.0,1.0,1.0);
  //   glTranslatef(-90.0f,
  //                0.0f + paddle_1_offset_Y,
  //                0.0);
  //   glRotatef(RAD_TO_DEG(paddle_1_rotation),
  //             0.0,
  //             0.0,
  //             1.0);
  //   draw_paddle_opengl2point1();
  //   glPopMatrix();


  //   // draw paddle 2, relative to the offset
  //   glPushMatrix();
  //   glColor3f(1.0,1.0,0.0);
  //   glTranslatef(90.0f,
  //                0.0f + paddle_2_offset_Y,
  //                0.0);
  //   glRotatef(RAD_TO_DEG(paddle_2_rotation),
  //              0.0,
  //              0.0,
  //              1.0);
  //   draw_paddle_opengl2point1();
  //   glPopMatrix();

  //   return SDL_FALSE;
  // }

  // in later demos,
  //glClearDepth( 1.0f );
  //glEnable( GL_DEPTH_TEST );
  //glDepthFunc( GL_LEQUAL );

}
