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
  static float paddle_1_offset_Y = 0.0;
  static float paddle_2_offset_Y = 0.0;
  const Uint8 *state = SDL_GetKeyboardState(NULL);
  std::function<void()> from_keyboard_update_paddle_positions =
    [&]()
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
    };
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

    from_keyboard_update_paddle_positions();

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
  class Vertex {
  public:
    Vertex(float the_x, float the_y):
      x(the_x),
      y(the_y)
    {}
    float x;
    float y;
  };
  std::function<void(Vertex)> draw_paddle_relative_to =
    [&](Vertex center)
    {
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

    from_keyboard_update_paddle_positions();

    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      draw_paddle_relative_to(Vertex(-0.9f,
                                     0.0f + paddle_1_offset_Y));
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      draw_paddle_relative_to(Vertex(0.9f,
                                     0.0f + paddle_2_offset_Y));
    }
    return SDL_FALSE;
  }
  typedef std::function<Vertex (Vertex)> vertex_transformer;
  vertex_transformer model_space_to_device_space =
    [&](Vertex modelspace)
    {
      return Vertex(modelspace.x/100.0f,
                    modelspace.y/100.0f);
    };
  from_keyboard_update_paddle_positions = [&]()
    {
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

    from_keyboard_update_paddle_positions();

    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      Vertex center(-90.0f, 0.0f + paddle_1_offset_Y);
      draw_paddle_relative_to(model_space_to_device_space(center));
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      Vertex center(90.0f, 0.0f + paddle_2_offset_Y);
      draw_paddle_relative_to(model_space_to_device_space(center));
    }
    return SDL_FALSE;
  }


  std::function<void (vertex_transformer)> draw_paddle_programmable =
    [&](vertex_transformer f)
    {
      glBegin(GL_QUADS);
      {
        Vertex local_v_1(-10.0,-30.0);
        Vertex global_v_1 = f(local_v_1);
        glVertex2f(global_v_1.x,global_v_1.y);
        Vertex local_v_2 (10.0, -30.0);
        Vertex global_v_2 = f(local_v_2);
        glVertex2f(global_v_2.x,global_v_2.y);
        Vertex local_v_3(10.0,30.0);
        Vertex global_v_3 = f(local_v_3);
        glVertex2f(global_v_3.x,global_v_3.y);
        Vertex local_v_4(-10.0, 30.0);
        Vertex global_v_4 = f(local_v_4);
        glVertex2f(global_v_4.x,global_v_4.y);
        glEnd();
      }
    };
  std::function<Vertex(float, float,Vertex)>translate
    = [&](float x,
          float y,
          Vertex modelspace)
    {
      return Vertex(modelspace.x + x,
                    modelspace.y + y);
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

    from_keyboard_update_paddle_positions();

    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_vertex){
	  Vertex vertex_translated = translate(-90.0f,
					       0.0f + paddle_1_offset_Y,
					       modelspace_vertex);
	  return model_space_to_device_space(vertex_translated);
	});

    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_vertex){
	  Vertex vertex_translated = translate(90.0f,
					       0.0f + paddle_2_offset_Y,
					       modelspace_vertex);
	  return model_space_to_device_space(vertex_translated);
	});

    }
    return SDL_FALSE;
  }
  std::function<Vertex(float,Vertex)> rotate =
    [&](float angle_in_radians,
        Vertex modelspace)
    {
      return Vertex(((float) modelspace.x*cos(angle_in_radians)
                     - modelspace.y*sin(angle_in_radians)),
                    ((float) modelspace.x*sin(angle_in_radians)
                     + modelspace.y*cos(angle_in_radians)));
    };
  static float paddle_1_rotation = 0.0;
  static float paddle_2_rotation = 0.0;
  std::function<void()> from_keyboard_update_rotation_of_paddles = [&](){
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

    from_keyboard_update_paddle_positions();
    from_keyboard_update_rotation_of_paddles();

    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_vertex){
	  Vertex vertex_rotated = rotate(paddle_1_rotation,
					 modelspace_vertex);
	  Vertex vertex_translated = translate(-90.0f,
					       0.0f + paddle_1_offset_Y,
					       vertex_rotated);
	  return model_space_to_device_space(vertex_translated);
	});

    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_vertex){
	  Vertex vertex_rotated = rotate(paddle_2_rotation,
					 modelspace_vertex);
	  Vertex vertex_translated = translate(90.0f,
					       0.0f + paddle_2_offset_Y,
					       vertex_rotated);
	  return model_space_to_device_space(vertex_translated);
	});

    }
    return SDL_FALSE;
  }
  static float camera_x = 0.0;
  static float camera_y = 0.0;
  std::function<void()> from_keyboard_update_camera_position = [&]()
    {
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
    };
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

    from_keyboard_update_paddle_positions();
    from_keyboard_update_rotation_of_paddles();
    from_keyboard_update_camera_position();

    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_vertex){
	  Vertex vertex_rotated = rotate(paddle_1_rotation,
					 modelspace_vertex);
	  Vertex vertex_translated = translate(-90.0f,
					       0.0f + paddle_1_offset_Y,
					       vertex_rotated);
	  Vertex camera_coordinates(vertex_translated.x - camera_x,
                                    vertex_translated.y - camera_y);
	  return model_space_to_device_space(camera_coordinates);
	});

    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_vertex){
	  Vertex vertex_rotated = rotate(paddle_2_rotation,
					 modelspace_vertex);
	  Vertex vertex_translated = translate(90.0f,
					       0.0f + paddle_2_offset_Y,
					       vertex_rotated);
	  Vertex camera_coordinates(vertex_translated.x - camera_x,
                                    vertex_translated.y - camera_y);
	  return model_space_to_device_space(camera_coordinates);
	});

    }
    return SDL_FALSE;
  }
  std::function<void (vertex_transformer)> draw_square_programmable =
    [&](vertex_transformer f)
    {
      glBegin(GL_QUADS);
      {
        Vertex local_v_1(-5.0, -5.0);
        Vertex global_v_1 = f(local_v_1);
        glVertex2f(global_v_1.x,global_v_1.y);
        Vertex local_v_2 (5.0, -5.0);
        Vertex global_v_2 = f(local_v_2);
        glVertex2f(global_v_2.x,global_v_2.y);
        Vertex local_v_3(5.0, 5.0);
        Vertex global_v_3 = f(local_v_3);
        glVertex2f(global_v_3.x,global_v_3.y);
        Vertex local_v_4(-5.0,5.0);
        Vertex global_v_4 = f(local_v_4);
        glVertex2f(global_v_4.x,global_v_4.y);
        glEnd();
      }
    };

  if(8 == demo_number){
    /*
     *  Demo 8 - Translate Relative location
     */
    // handle events
    glClear(GL_COLOR_BUFFER_BIT);
    while (SDL_PollEvent(&event))
      {
        if (event.type == SDL_QUIT){
          return SDL_TRUE;
        }
      }

    from_keyboard_update_paddle_positions();
    from_keyboard_update_rotation_of_paddles();
    from_keyboard_update_camera_position();

    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_vertex){
	  Vertex vertex_rotated = rotate(paddle_1_rotation,
					 modelspace_vertex);
	  Vertex vertex_translated = translate(-90.0f,
					       0.0f + paddle_1_offset_Y,
					       vertex_rotated);
	  Vertex camera_coordinates(vertex_translated.x - camera_x,
                                    vertex_translated.y - camera_y);
	  return model_space_to_device_space(camera_coordinates);
	});

    }
    // draw square, relative to paddle 1
    glColor3f(0.0,0.0,1.0);
    {
      draw_square_programmable([&](Vertex modelspace_vertex){
          Vertex square_translated = translate(20.0f,
                                               0.0f,
                                               modelspace_vertex);
          Vertex vertex_rotated = rotate(paddle_1_rotation,
                                         square_translated);
          Vertex vertex_translated = translate(-90.0f,
                                               0.0f + paddle_1_offset_Y,
                                               vertex_rotated);
          Vertex camera_coordinates(vertex_translated.x - camera_x,
                                    vertex_translated.y - camera_y);
          return model_space_to_device_space(camera_coordinates);
        }
        );
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_Vertex){
	  Vertex Vertex_rotated = rotate(paddle_2_rotation,
					 modelspace_Vertex);
	  Vertex Vertex_translated = translate(90.0f,
					       0.0f + paddle_2_offset_Y,
					       Vertex_rotated);
	  Vertex camera_coordinates(Vertex_translated.x - camera_x,
                                    Vertex_translated.y - camera_y);
	  return model_space_to_device_space(camera_coordinates);
	});

    }
    return SDL_FALSE;
  }
  static float square_rotation = 0.0;
  std::function<void()> from_keyboard_update_square_rotation = [&]()
    {
      if (state[SDL_SCANCODE_Q]) {
        square_rotation += 0.1;
      }
    };
  if(9 == demo_number){
    /*
     *  Demo 9 - Rotation of square
     */
    // handle events
    glClear(GL_COLOR_BUFFER_BIT);
    while (SDL_PollEvent(&event))
      {
        if (event.type == SDL_QUIT){
          return SDL_TRUE;
        }
      }

    from_keyboard_update_paddle_positions();
    from_keyboard_update_rotation_of_paddles();
    from_keyboard_update_camera_position();
    from_keyboard_update_square_rotation();

    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_Vertex){
	  Vertex Vertex_rotated = rotate(paddle_1_rotation,
					 modelspace_Vertex);
	  Vertex Vertex_translated = translate(-90.0f,
					       0.0f + paddle_1_offset_Y,
					       Vertex_rotated);
	  Vertex camera_coordinates(Vertex_translated.x - camera_x,
                                    Vertex_translated.y - camera_y);
	  return model_space_to_device_space(camera_coordinates);
	});

    }
    // draw square, relative to paddle 1
    glColor3f(0.0,0.0,1.0);
    {
      draw_square_programmable([&](Vertex modelspace_Vertex){
          Vertex square_rotated = rotate(square_rotation,
                                         modelspace_Vertex);
          Vertex square_translated = translate(20.0f,
                                               0.0f,
                                               square_rotated);
          Vertex Vertex_rotated = rotate(paddle_1_rotation,
                                         square_translated);
          Vertex Vertex_translated = translate(-90.0f,
                                               0.0f + paddle_1_offset_Y,
                                               Vertex_rotated);
          Vertex camera_coordinates(Vertex_translated.x - camera_x,
                                    Vertex_translated.y - camera_y);
          return model_space_to_device_space(camera_coordinates);
        });
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_Vertex){
	  Vertex Vertex_rotated = rotate(paddle_2_rotation,
					 modelspace_Vertex);
	  Vertex Vertex_translated = translate(90.0f,
					       0.0f + paddle_2_offset_Y,
					       Vertex_rotated);
	  Vertex camera_coordinates(Vertex_translated.x - camera_x,
                                    Vertex_translated.y - camera_y);
	  return model_space_to_device_space(camera_coordinates);
	});

    }
    return SDL_FALSE;
  }
  std::function<Vertex(float, float,Vertex)> scale =
    [&](float scale_x,
        float scale_y,
        Vertex modelspace)
    {
      return Vertex(modelspace.x * scale_x,
                    modelspace.y * scale_y);
    };
  // change the definition of square to positive and negative 1.0
  draw_square_programmable =
    [&](vertex_transformer f)
    {
      glBegin(GL_QUADS);
      {
        Vertex local_v_1(-1.0, -1.0);
        Vertex global_v_1 = f(local_v_1);
        printf("2d %f %f\n",global_v_1.x,global_v_1.y);
        glVertex2f(global_v_1.x,global_v_1.y);
        Vertex local_v_2(1.0, -1.0);
        Vertex global_v_2 = f(local_v_2);
        glVertex2f(global_v_2.x,global_v_2.y);
        Vertex local_v_3(1.0, 1.0);
        Vertex global_v_3 = f(local_v_3);
        glVertex2f(global_v_3.x,global_v_3.y);
        Vertex local_v_4(-1.0,1.0);
        Vertex global_v_4 = f(local_v_4);
        glVertex2f(global_v_4.x,global_v_4.y);
        glEnd();
      }
    };
  static float rotation_around_paddle_1 = 0.0;
  if(10 == demo_number){
    /*
     *  Demo 10 - Scaling
     */
    // handle events
    glClear(GL_COLOR_BUFFER_BIT);
    while (SDL_PollEvent(&event))
      {
        if (event.type == SDL_QUIT){
          return SDL_TRUE;
        }
      }


    from_keyboard_update_paddle_positions();
    from_keyboard_update_rotation_of_paddles();
    from_keyboard_update_camera_position();
    from_keyboard_update_square_rotation();
    // handle keyboard input
    {
      if (state[SDL_SCANCODE_E]) {
        rotation_around_paddle_1 += 0.1;
      }
    }

    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      draw_square_programmable([&](Vertex modelspace_Vertex){
          Vertex Vertex_scaled = scale(10.0f,
                                       30.0f,
                                       modelspace_Vertex);
          Vertex Vertex_rotated = rotate(paddle_1_rotation,
                                         Vertex_scaled);
          Vertex Vertex_translated = translate(-90.0f,
                                               0.0f + paddle_1_offset_Y,
                                               Vertex_rotated);
          Vertex camera_coordinates(Vertex_translated.x - camera_x,
                                    Vertex_translated.y - camera_y);
          return model_space_to_device_space(camera_coordinates);
        });
    }
    // draw square, relative to paddle 1
    glColor3f(0.0,0.0,1.0);
    {
      draw_square_programmable([&](Vertex modelspace_Vertex){
          Vertex Vertex_scaled = scale(5.0f,
                                       5.0f,
                                       modelspace_Vertex);
          Vertex square_rotated = rotate(square_rotation,
                                         Vertex_scaled);
          Vertex square_translated = translate(20.0f,
                                               0.0f,
                                               square_rotated);
          Vertex around_paddle_1 = rotate(rotation_around_paddle_1,
                                          square_translated);
          Vertex Vertex_rotated = rotate(paddle_1_rotation,
                                         around_paddle_1);
          Vertex Vertex_translated = translate(-90.0f,
                                               0.0f + paddle_1_offset_Y,
                                               Vertex_rotated);
          Vertex camera_coordinates(Vertex_translated.x - camera_x,
                                    Vertex_translated.y - camera_y);
          return model_space_to_device_space(camera_coordinates);
        });
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      draw_square_programmable([&](Vertex modelspace_Vertex){
          Vertex Vertex_scaled = scale(10.0f,
                                       30.0f,
                                       modelspace_Vertex);
          Vertex Vertex_rotated = rotate(paddle_2_rotation,
                                         Vertex_scaled);
          Vertex Vertex_translated = translate(90.0f,
                                               0.0f + paddle_2_offset_Y,
                                               Vertex_rotated);
          Vertex camera_coordinates(Vertex_translated.x - camera_x,
                                    Vertex_translated.y - camera_y);
          return model_space_to_device_space(camera_coordinates);
        });
    }
    return SDL_FALSE;
  }

  class Vertex3 {
  public:
    Vertex3(float the_x, float the_y, float the_z):
      x(the_x),
      y(the_y),
      z(the_z)
    {}
    float x;
    float y;
    float z;
  };
  typedef std::function<Vertex3 (Vertex3)> Vertex3_transformer;
  std::function<Vertex3(float, float,float,Vertex3)> translate3 =
    [&](float x,
        float y,
        float z,
        Vertex3 modelspace)
    {
      return Vertex3(modelspace.x + x,
                     modelspace.y + y,
                     modelspace.z + z);
    };
  std::function<Vertex3(float,Vertex3)> rotate3Z =
    [&](float angle_in_radians,
        Vertex3 modelspace)
    {
      return Vertex3(((float) modelspace.x*cos(angle_in_radians)
                      - modelspace.y*sin(angle_in_radians)),
                     ((float) modelspace.x*sin(angle_in_radians)
                      + modelspace.y*cos(angle_in_radians)),
                     modelspace.z);
    };
  std::function<Vertex3(float, float, float, Vertex3)> scale3 =
    [&](float scale_x,
        float scale_y,
        float scale_z,
        Vertex3 modelspace)
    {
      return Vertex3(modelspace.x * scale_x,
                     modelspace.y * scale_y,
                     modelspace.y * scale_z);
      
    };
  std::function<void (Vertex3_transformer)>
    draw_square3_programmable =
    [&](Vertex3_transformer f)
    {
      glBegin(GL_QUADS);
      {
        Vertex3 local_v_1(-1.0,
                          -1.0,
                          0.0);
        Vertex3 global_v_1 = f(local_v_1);
        glVertex3f(global_v_1.x,
                   global_v_1.y,
                   global_v_1.z);
        Vertex3 local_v_2 ( 1.0, -1.0, 0.0);
        Vertex3 global_v_2 = f(local_v_2);
        glVertex3f(global_v_2.x,
                   global_v_2.y,
                   global_v_2.z);
        Vertex3 local_v_3( 1.0, 1.0, 0.0);
        Vertex3 global_v_3 = f(local_v_3);
        glVertex3f(global_v_3.x,
                   global_v_3.y,
                   global_v_3.z);
        Vertex3 local_v_4( -1.0, 1.0, 0.0);
        Vertex3 global_v_4 = f(local_v_4);
        glVertex3f(global_v_4.x,
                   global_v_4.y,
                   global_v_4.z);
        glEnd();
      }
    };

  std::function<Vertex3(float,float,float,
                        float,float,float,
                        Vertex3)> Vertex3_ortho =
    [&](float xmin,
        float xmax,
        float ymin,
        float ymax,
        float zmin,
        float zmax,
        Vertex3 pos){
    float x_length = xmax-xmin;
    float y_length = ymax-ymin;
    float z_length = zmax-zmin;
    Vertex3 translated = translate3(xmax-x_length/2.0,
                                    ymax-y_length/2.0,
                                    zmax-z_length/2.0,
                                    pos);
    Vertex3 scaled = scale3(1/(x_length/2.0),
                            1/(y_length/2.0),
                            1/(z_length/2.0),
                            translated);
    return scaled;
  };

  if(11 == demo_number){
    /*
     *  Demo 11 - Ortho projection in 3d
     */
    // handle events
    glClear(GL_COLOR_BUFFER_BIT);
    while (SDL_PollEvent(&event))
      {
        if (event.type == SDL_QUIT){
          return SDL_TRUE;
        }
      }

    from_keyboard_update_paddle_positions();
    from_keyboard_update_rotation_of_paddles();
    from_keyboard_update_camera_position();
    from_keyboard_update_square_rotation();
    // handle keyboard input
    {
      if (state[SDL_SCANCODE_E]) {
        rotation_around_paddle_1 += 0.1;
      }
    }

    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      draw_square3_programmable([&](Vertex3 Vertex3_local_coordinates){
          Vertex3 Vertex3_scaled = scale3(10.0f,
                                          30.0f,
                                          1.0f,
                                          Vertex3_local_coordinates);
          Vertex3 Vertex3_rotated = rotate3Z(paddle_1_rotation,
                                             Vertex3_scaled);
          Vertex3 Vertex3_translated = translate3(-90.0f,
                                                  0.0f + paddle_1_offset_Y,
                                                  0.0f,
                                                  Vertex3_rotated);
          Vertex3 camera_coordinates(Vertex3_translated.x - camera_x,
                                     Vertex3_translated.y - camera_y,
                                     Vertex3_translated.z);
          return Vertex3_ortho(-100.0f,100.0f,
                               -100.0f,100.0f,
                               -100.0f,100.0f,
                               camera_coordinates);
        });
    }
    // draw square, relative to paddle 1
    glColor3f(0.0,0.0,1.0);
    {
      draw_square3_programmable([&](Vertex3 Vertex3_local_coordinates){
          Vertex3 Vertex3_scaled = scale3(5.0f,
                                          5.0f,
                                          0.0f,
                                          Vertex3_local_coordinates);
          Vertex3 square_rotated = rotate3Z(square_rotation,
                                            Vertex3_scaled);
          Vertex3 square_translated = translate3(20.0f,
                                                 0.0f,
                                                 0.0f,
                                                 square_rotated);
          Vertex3 around_paddle_1 = rotate3Z(rotation_around_paddle_1,
                                             square_translated);
          Vertex3 Vertex3_rotated = rotate3Z(paddle_1_rotation,
                                             around_paddle_1);
          Vertex3 Vertex3_translated = translate3(-90.0f,
                                                  0.0f + paddle_1_offset_Y,
                                                  0.0f,
                                                  Vertex3_rotated);
          Vertex3 camera_coordinates(Vertex3_translated.x - camera_x,
                                     Vertex3_translated.y - camera_y,
                                     Vertex3_translated.z);
          return Vertex3_ortho(-100.0f,100.0f,
                               -100.0f,100.0f,
                               -100.0f,100.0f,
                               camera_coordinates);
        });
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      draw_square3_programmable([&](Vertex3 Vertex3_local_coordinates){
          Vertex3 Vertex3_scaled = scale3(10.0f,
                                          30.0f,
                                          1.0f,
                                          Vertex3_local_coordinates);
          Vertex3 Vertex3_rotated = rotate3Z(paddle_2_rotation,
                                             Vertex3_scaled);
          Vertex3 Vertex3_translated = translate3(90.0f,
                                                  0.0f + paddle_2_offset_Y,
                                                  0.0f,
                                                  Vertex3_rotated);
          Vertex3 camera_coordinates(Vertex3_translated.x - camera_x,
                                     Vertex3_translated.y - camera_y,
                                     Vertex3_translated.z);
          return Vertex3_ortho(-100.0f,100.0f,
                               -100.0f,100.0f,
                               -100.0f,100.0f,
                               camera_coordinates);
        });
    }
    return SDL_FALSE;
  }
  std::function<void()> draw_square_opengl2point1 = [&](){
    glBegin(GL_QUADS);
    {
      glVertex2f(-1.0, -1.0);
      glVertex2f(1.0, -1.0);
      glVertex2f(1.0, 1.0);
      glVertex2f(-1.0, 1.0);
      glEnd();
    }
  };

  std::function<double(double)> RAD_TO_DEG = [&](double rad){
    return 57.296 * rad;
  };
  if(40 == demo_number){
    /*
     *  Demo 11 - OpenGL Matricies
     */
    // handle events
    glClear(GL_COLOR_BUFFER_BIT);
    while (SDL_PollEvent(&event))
      {
        if (event.type == SDL_QUIT){
          return SDL_TRUE;
        }
        if (event.type == SDL_WINDOWEVENT){
          if(event.window.event == SDL_WINDOWEVENT_RESIZED){
            int w = event.window.data1, h = event.window.data2;
            glViewport(0,0,w,h);
          }
        }
      }


    from_keyboard_update_paddle_positions();
    from_keyboard_update_rotation_of_paddles();
    from_keyboard_update_camera_position();
    from_keyboard_update_square_rotation();
    // handle keyboard input
    {
      if (state[SDL_SCANCODE_E]) {
        rotation_around_paddle_1 += 0.1;
      }
    }

    // set up Camera
    {
      // define the projection
      glMatrixMode(GL_PROJECTION);
      glLoadIdentity();
      glOrtho(-100,100,-100,100,-100,100);
      // move the "camera"
      glMatrixMode(GL_MODELVIEW);
      glLoadIdentity();
      glTranslatef(-camera_x,
                   -camera_y,
                   0.0);
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
                   0.0f);
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
