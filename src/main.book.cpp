//Model View Projection
//====================
//Bill Six
//v1.0, 2003-12
//:doctype: book
//
//
//[dedication]
//Example Dedication
//------------------
//Optional dedication.
//
//This document is an AsciiDoc book skeleton containing briefly
//annotated example elements plus a couple of example index entries and
//footnotes.
//
//Books are normally used to generate DocBook markup and the titles of
//the preface, appendix, bibliography, glossary and index sections are
//significant ('specialsections').
//
//
//[preface]
//Example Preface
//---------------
//Optional preface.
//
//Preface Sub-section
//~~~~~~~~~~~~~~~~~~~
//Preface sub-section body.
//
//
//The First Chapter
//-----------------
//Chapters can contain sub-sections nested up to three deep.
//footnote:[An example footnote.]
//indexterm:[Example index entry]
//
//Chapters can have their own bibliography, glossary and index.
//
//[source,C,linenums]
//----
/*  src/main.cpp
 *
 * Copyright 2016 - William Emerison Six
 * All rights reserved
 * main.cpp is Distributed under LGPL 2.1 or Apache 2.0
 */
#include <stdio.h>
#include <math.h>
#include <functional>
#include <cmath>
#include <vector>
#include "main.h"
SDL_Window *window;
SDL_GLContext glcontext;
//----
//[source,C,linenums]
//----
#define RAD_TO_DEG(rad) (57.296 * rad)
#define DEG_TO_RAD(degree) (degree / 57.296)
void print_usage(){
  puts("Usage -- modelviewprojection demonumber");
}


// Use C linkage because of SDL_main
#ifdef __cplusplus
extern "C"
#endif
int main(int argc, char *argv[])
{
  int demo_number;
  if(argc == 1){
    print_usage();
    demo_number = 15;
  }
  else{
    // get demo number from the command line
    demo_number = atoi(argv[1]);
  }
//----
//[source,C,linenums]
//----
  if (SDL_Init(SDL_INIT_EVERYTHING) != 0){
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
  if(NULL == (window = SDL_CreateWindow("modelviewprojection",
                                        SDL_WINDOWPOS_CENTERED,
                                        SDL_WINDOWPOS_CENTERED,
                                        500,
                                        500,
                                        (SDL_WINDOW_OPENGL |
                                         SDL_WINDOW_RESIZABLE)))){
    SDL_LogMessage(SDL_LOG_CATEGORY_APPLICATION,
                   SDL_LOG_PRIORITY_ERROR,
                   "Could not create window: %s\n",
                   SDL_GetError());
    return 1;
  }
  glcontext = SDL_GL_CreateContext(window);
  // init GLEW
#ifdef linux
  glewExperimental = GL_TRUE;
#elif _WIN32
#endif
  glewInit();
  SDL_GL_MakeCurrent(window,glcontext);
  // log opengl version
  SDL_LogMessage(SDL_LOG_CATEGORY_APPLICATION,
                 SDL_LOG_PRIORITY_INFO,
                 "OpenGL version loaded: %s\n",
                 glGetString(GL_VERSION));
  // initialize OpenGL
  glClearColor(0,0,0,1);
//----
//[source,C,linenums]
//----
  SDL_bool quit = SDL_FALSE;
  do{
    quit = render_scene(&demo_number);
    SDL_GL_SwapWindow(window);
  } while (quit != SDL_TRUE);
  // Cleanup
  SDL_GL_DeleteContext(glcontext);
  SDL_DestroyWindow(window);
  SDL_Quit();
  return 0;
}
//----
//[source,C,linenums]
//----
SDL_bool render_scene(int *demo_number){
  SDL_Event event;
  glClear(GL_COLOR_BUFFER_BIT);
  glClear(GL_DEPTH_BUFFER_BIT);
  glClearDepth(-1.1f );
  glDepthFunc(GL_GREATER);
  glMatrixMode(GL_PROJECTION);
  glLoadIdentity();
  glMatrixMode(GL_MODELVIEW);
  glLoadIdentity();
  // set viewport
  {
    int w, h;
    SDL_GetWindowSize(window,&w,&h);
    glViewport(0, 0,
               w, h);
  }
  // handle events
  while (SDL_PollEvent(&event)){
    if (event.type == SDL_QUIT){
      return SDL_TRUE;
    }
  }
//----
//[source,C,linenums]
//----
  if(0 == *demo_number){
    return SDL_FALSE;
  }
//----
//[source,C,linenums]
//----
  if(1 == *demo_number){
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
//----
//[source,C,linenums]
//----
  static float paddle_1_offset_Y = 0.0;
  static float paddle_2_offset_Y = 0.0;
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
//[source,C,linenums]
//----
  if(2 == *demo_number){
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
//----
//[source,C,linenums]
//----
  class Vertex {
  public:
    Vertex(float the_x, float the_y):
      x(the_x),
      y(the_y)
    {}
    Vertex translate(float x,
                     float y)
    {
      return Vertex(this->x + x,
                    this->y + y);
    };
    Vertex rotate(float angle_in_radians)
    {
      return Vertex(((float) this->x*cos(angle_in_radians)
                     - this->y*sin(angle_in_radians)),
                    ((float) this->x*sin(angle_in_radians)
                     + this->y*cos(angle_in_radians)));
    };
    Vertex scale(float scale_x,
                 float scale_y)
    {
      return Vertex(this->x * scale_x,
                    this->y * scale_y);
    };

    float x;
    float y;
  };
  std::function<void(Vertex)> draw_paddle_relative_to =
    [&](Vertex center)
    {
      glBegin(GL_QUADS);
      glVertex2f(center.x-0.1,center.y-0.3);
      glVertex2f(center.x+0.1,center.y-0.3);
      glVertex2f(center.x+0.1,center.y+0.3);
      glVertex2f(center.x-0.1,center.y+0.3);
      glEnd();
    };
//----
//[source,C,linenums]
//----
  if(3 == *demo_number){
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
//----
//[source,C,linenums]
//----
  if (state[SDL_SCANCODE_S]) {
    // add 0.1 to correct for the previous calculation
    paddle_1_offset_Y += 0.1;
    paddle_1_offset_Y -= 10.0f;
  }
  if (state[SDL_SCANCODE_W]) {
    paddle_1_offset_Y -= 0.1;
    paddle_1_offset_Y += 10.0f;
  }
  if (state[SDL_SCANCODE_K]) {
    paddle_2_offset_Y += 0.1;
    paddle_2_offset_Y -= 10.0f;
  }
  if (state[SDL_SCANCODE_I]) {
    paddle_2_offset_Y -= 0.1;
    paddle_2_offset_Y += 10.0f;
  }
//----
//[source,C,linenums]
//----
  if(4 == *demo_number){
    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      Vertex center(-90.0f, 0.0f + paddle_1_offset_Y);
      draw_paddle_relative_to(center.scale(1.0/100.0, 1.0/100.0));
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      Vertex center(90.0f, 0.0f + paddle_2_offset_Y);
      draw_paddle_relative_to(center.scale(1.0/100.0, 1.0/100.0));
    }
    return SDL_FALSE;
  }
//----
//[source,C,linenums]
//----
  typedef std::function<Vertex (Vertex)> Vertex_transformer;
  std::function<void (Vertex_transformer)> draw_paddle_programmable =
    [&](Vertex_transformer f)
    {
      glBegin(GL_QUADS);
      Vertex ndc_v_1 = f(Vertex(-10.0,-30.0));
      glVertex2f(ndc_v_1.x,ndc_v_1.y);
      Vertex ndc_v_2 = f(Vertex(10.0, -30.0));
      glVertex2f(ndc_v_2.x,ndc_v_2.y);
      Vertex ndc_v_3 = f(Vertex(10.0,30.0));
      glVertex2f(ndc_v_3.x,ndc_v_3.y);
      Vertex ndc_v_4 = f(Vertex(-10.0, 30.0));
      glVertex2f(ndc_v_4.x,ndc_v_4.y);
      glEnd();
    };
//----
//[source,C,linenums]
//----
  if(5 == *demo_number){
    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_vertex){
	  return modelspace_vertex
            .translate(-90.0f,
                       0.0f + paddle_1_offset_Y)
            .scale(1.0/100.0, 1.0/100.0);
	});
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_vertex){
	  return modelspace_vertex
            .translate(90.0f,
                       0.0f + paddle_2_offset_Y)
            .scale(1.0/100.0, 1.0/100.0);
	});
    }
    return SDL_FALSE;
  }
//----
//[source,C,linenums]
//----
  static float paddle_1_rotation = 0.0;
  static float paddle_2_rotation = 0.0;
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
    glColor3f(1.0,1.0,1.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_vertex){
	  return modelspace_vertex
            .rotate(paddle_1_rotation)
            .translate(-90.0f,
                       0.0f + paddle_1_offset_Y)
            .scale(1.0/100.0, 1.0/100.0);
	});
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_vertex){
	  return modelspace_vertex
            .rotate(paddle_2_rotation)
            .translate(90.0f,
                       0.0f + paddle_2_offset_Y)
            .scale(1.0/100.0, 1.0/100.0);
	});
    }
    return SDL_FALSE;
  }
//----
//[source,C,linenums]
//----
  static float camera_x = 0.0;
  static float camera_y = 0.0;
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
    glColor3f(1.0,1.0,1.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_vertex){
	  return modelspace_vertex
            .rotate(paddle_1_rotation)
            .translate(-90.0f,
                       0.0f + paddle_1_offset_Y)
            .translate(- camera_x,
                       - camera_y)
            .scale(1.0/100.0, 1.0/100.0);
	});
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_vertex){
	  return modelspace_vertex
            .rotate(paddle_2_rotation)
            .translate(90.0f,
                       0.0f + paddle_2_offset_Y)
            .translate(- camera_x,
                       - camera_y)
            .scale(1.0/100.0, 1.0/100.0);
	});
    }
    return SDL_FALSE;
  }
//----
//[source,C,linenums]
//----
  std::function<void (Vertex_transformer)> draw_square_programmable =
    [&](Vertex_transformer f)
    {
      glBegin(GL_QUADS);
      {
        Vertex ndc_v_1 = f(Vertex(-5.0, -5.0));
        glVertex2f(ndc_v_1.x,ndc_v_1.y);
        Vertex ndc_v_2 = f(Vertex(5.0, -5.0));
        glVertex2f(ndc_v_2.x,ndc_v_2.y);
        Vertex ndc_v_3 = f(Vertex(5.0, 5.0));
        glVertex2f(ndc_v_3.x,ndc_v_3.y);
        Vertex ndc_v_4 = f(Vertex(-5.0,5.0));
        glVertex2f(ndc_v_4.x,ndc_v_4.y);
        glEnd();
      }
    };
//----
//[source,C,linenums]
//----
  if(8 == *demo_number){
    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_vertex){
          return modelspace_vertex
            .rotate(paddle_1_rotation)
            .translate(-90.0f,
                       0.0f + paddle_1_offset_Y)
            .translate(- camera_x,
                       - camera_y)
            .scale(1.0/100.0, 1.0/100.0);
	});
    }
    // draw square, relative to paddle 1
    glColor3f(0.0,0.0,1.0);
    {
      draw_square_programmable([&](Vertex modelspace_vertex){
          return modelspace_vertex
            .translate(20.0f,
                       0.0f)
            .rotate(paddle_1_rotation)
            .translate(-90.0f,
                       0.0f + paddle_1_offset_Y)
            .translate(- camera_x,
                       - camera_y)
            .scale(1.0/100.0, 1.0/100.0);
        }
        );
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_vertex){
	  return modelspace_vertex
            .rotate(paddle_2_rotation)
            .translate(90.0f,
                       0.0f + paddle_2_offset_Y)
            .translate(- camera_x,
                       - camera_y)
            .scale(1.0/100.0, 1.0/100.0);
	});
    }
    return SDL_FALSE;
  }
//----
//[source,C,linenums]
//----
  static float square_rotation = 0.0;
  // update_square_rotation
  if (state[SDL_SCANCODE_Q]) {
    square_rotation += 0.1;
  }
  if(9 == *demo_number){
    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_vertex){
	  return modelspace_vertex
            .rotate(paddle_1_rotation)
            .translate(-90.0f,
                       0.0f + paddle_1_offset_Y)
            .translate(- camera_x,
                       - camera_y)
            .scale(1.0/100.0, 1.0/100.0);
	});
    }
    // draw square, relative to paddle 1
    glColor3f(0.0,0.0,1.0);
    {
      draw_square_programmable([&](Vertex modelspace_vertex){
          return modelspace_vertex
            .rotate(square_rotation)
            .translate(20.0f,
                       0.0f)
            .rotate(paddle_1_rotation)
            .translate(-90.0f,
                       0.0f + paddle_1_offset_Y)
            .translate(- camera_x,
                       - camera_y)
            .scale(1.0/100.0, 1.0/100.0);
        });
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      draw_paddle_programmable([&](Vertex modelspace_vertex){
	  return modelspace_vertex
            .rotate(paddle_2_rotation)
            .translate(90.0f,
                       0.0f + paddle_2_offset_Y)
            .translate(- camera_x,
                       - camera_y)
            .scale(1.0/100.0, 1.0/100.0);
	});
    }
    return SDL_FALSE;
  }
//----
//[source,C,linenums]
//----
  // change the definition of square to positive and negative 1.0
  draw_square_programmable =
    [&](Vertex_transformer f)
    {
      glBegin(GL_QUADS);
      {
        Vertex ndc_v_1 = f(Vertex(-1.0, -1.0));
        glVertex2f(ndc_v_1.x,ndc_v_1.y);
        Vertex ndc_v_2 = f(Vertex(1.0, -1.0));
        glVertex2f(ndc_v_2.x,ndc_v_2.y);
        Vertex ndc_v_3 = f(Vertex(1.0, 1.0));
        glVertex2f(ndc_v_3.x,ndc_v_3.y);
        Vertex ndc_v_4 = f(Vertex(-1.0,1.0));
        glVertex2f(ndc_v_4.x,ndc_v_4.y);
        glEnd();
      }
    };
  static float rotation_around_paddle_1 = 0.0;
  if (state[SDL_SCANCODE_E]) {
    rotation_around_paddle_1 += 0.1;
  }
//----
//[source,C,linenums]
//----
  if(10 == *demo_number){
    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      draw_square_programmable([&](Vertex modelspace_vertex){
          return modelspace_vertex
            .scale(10.0f,
                   30.0f)
            .rotate(paddle_1_rotation)
            .translate(-90.0f,
                       0.0f + paddle_1_offset_Y)
            .translate(- camera_x,
                       - camera_y)
            .scale(1.0/100.0, 1.0/100.0);
        });
    }
    // draw square, relative to paddle 1
    glColor3f(0.0,0.0,1.0);
    {
      draw_square_programmable([&](Vertex modelspace_vertex){
          return modelspace_vertex
            .scale(5.0f,
                   5.0f)
            .rotate(square_rotation)
            .translate(20.0f,
                       0.0f)
            .rotate(rotation_around_paddle_1)
            .rotate(paddle_1_rotation)
            .translate(-90.0f,
                       0.0f + paddle_1_offset_Y)
            .translate(- camera_x,
                       - camera_y)
            .scale(1.0/100.0, 1.0/100.0);
        });
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      draw_square_programmable([&](Vertex modelspace_vertex){
          return modelspace_vertex
            .scale(10.0f,
                   30.0f)
            .rotate(paddle_2_rotation)
            .translate(90.0f,
                       0.0f + paddle_2_offset_Y)
            .translate(- camera_x,
                       - camera_y)
            .scale(1.0/100.0, 1.0/100.0);
        });
    }
    return SDL_FALSE;
  }
//----
//[source,C,linenums]
//----
  class Vertex3 {
  public:
    Vertex3(float the_x, float the_y, float the_z):
      x(the_x),
      y(the_y),
      z(the_z)
    {}
    Vertex3 translate(float x,
                      float y,
                      float z)
    {
      return Vertex3(this->x + x,
                     this->y + y,
                     this->z + z);
    };
    Vertex3 rotateX(float angle_in_radians)
    {
      return Vertex3(this->x,
                     ((float) this->y*cos(angle_in_radians)
                      - this->z*sin(angle_in_radians)),
                     ((float) this->y*sin(angle_in_radians)
                      + this->z*cos(angle_in_radians)));
    };
    Vertex3 rotateY(float angle_in_radians)
    {
      return Vertex3(((float) this->z*sin(angle_in_radians)
                      + this->x*cos(angle_in_radians)),
                     this->y,
                     ((float) this->z*cos(angle_in_radians)
                      - this->x*sin(angle_in_radians)));
    };
    Vertex3 rotateZ(float angle_in_radians)
    {
      return Vertex3(((float) this->x*cos(angle_in_radians)
                      - this->y*sin(angle_in_radians)),
                     ((float) this->x*sin(angle_in_radians)
                      + this->y*cos(angle_in_radians)),
                     this->z);
    };
    Vertex3 scale(float scale_x,
                  float scale_y,
                  float scale_z)
    {
      return Vertex3(this->x * scale_x,
                     this->y * scale_y,
                     this->z * scale_z);
    };
    Vertex3 ortho(float left,
                  float right,
                  float bottom,
                  float top,
                  float nearVal,
                  float farVal)
    {
      float x_length = right-left;
      float y_length = top-bottom;
      float z_length = farVal-nearVal;
      return this->
        translate(-(right-x_length/2.0),
                  -(top-y_length/2.0),
                  -(farVal-z_length/2.0))
        .scale(1/(x_length/2.0),
               1/(y_length/2.0),
               1/(-z_length/2.0));
        // negate z length because it is already negative, and don't want
        // to flip the data
    }
    Vertex3 perspective(float nearZ,
                        float farZ){
      const float field_of_view =  DEG_TO_RAD(45.0/2.0);
      int w, h;
      SDL_GetWindowSize(window,&w,&h);
      float y_angle =  ((float)h / (float)w) * field_of_view;

      float sheared_x = this->x / fabs(this->z) * fabs(nearZ);
      float sheared_y = this->y / fabs(this->z) * fabs(nearZ);
      Vertex3 projected =  Vertex3(sheared_x, sheared_y, this->z);
      float x_min_of_box = fabs(nearZ) * tan(field_of_view);
      float y_min_of_box = fabs(nearZ) * tan(y_angle);
      return projected.ortho(-x_min_of_box, x_min_of_box,
                             -y_min_of_box, y_min_of_box,
                             nearZ, farZ);
    };
    float x;
    float y;
    float z;
  };

  typedef std::function<Vertex3 (Vertex3)> Vertex3_transformer;
  std::function<void (Vertex3_transformer)>
    draw_square3_programmable =
    [&](Vertex3_transformer f)
    {
      glBegin(GL_QUADS);
      Vertex3 ndc_v_1 = f(Vertex3(-1.0,-1.0,0.0));
      glVertex3f(ndc_v_1.x,ndc_v_1.y,ndc_v_1.z);
      Vertex3 ndc_v_2 = f(Vertex3(1.0,-1.0,0.0));
      glVertex3f(ndc_v_2.x,ndc_v_2.y,ndc_v_2.z);
      Vertex3 ndc_v_3 = f(Vertex3(1.0,1.0,0.0));
      glVertex3f(ndc_v_3.x,ndc_v_3.y,ndc_v_3.z);
      Vertex3 ndc_v_4 = f(Vertex3(-1.0,1.0,0.0));
      glVertex3f(ndc_v_4.x,ndc_v_4.y,ndc_v_4.z);
      glEnd();
    };
//----
//[source,C,linenums]
//----
  if(11 == *demo_number){
    // draw paddle 1, relative to the offset
    glColor3f(1.0,1.0,1.0);
    {
      draw_square3_programmable([&](Vertex3 Vertex3_local_coordinate){
          return Vertex3_local_coordinate
            .scale(10.0f,
                    30.0f,
                    1.0f)
            .rotateZ(paddle_1_rotation)
            .translate(-90.0f,
                       0.0f + paddle_1_offset_Y,
                       0.0f)
            .translate(- camera_x,
                       - camera_y,
                       0)
            .ortho(-100.0f,100.0f,
                   -100.0f,100.0f,
                   100.0f,-100.0f);
        });
    }
    // draw square, relative to paddle 1
    glColor3f(0.0,0.0,1.0);
    {
      draw_square3_programmable([&](Vertex3 Vertex3_local_coordinate){
          return Vertex3_local_coordinate
            .scale(5.0f,
                   5.0f,
                   0.0f)
            .rotateZ(square_rotation)
            .translate(20.0f,
                       0.0f,
                       0.0f)
            .rotateZ(rotation_around_paddle_1)
            .rotateZ(paddle_1_rotation)
            .translate(-90.0f,
                       0.0f + paddle_1_offset_Y,
                       0.0f)
            .translate(- camera_x,
                       - camera_y,
                       0)
            .ortho(-100.0f,100.0f,
                   -100.0f,100.0f,
                   100.0f,-100.0f);
        });
    }
    // draw paddle 2, relative to the offset
    glColor3f(1.0,1.0,0.0);
    {
      draw_square3_programmable([&](Vertex3 Vertex3_local_coordinate){
          return Vertex3_local_coordinate
            .scale(10.0f,
                   30.0f,
                   1.0f)
            .rotateZ(paddle_2_rotation)
            .translate(90.0f,
                       0.0f + paddle_2_offset_Y,
                       0.0f)
            .translate(- camera_x,
                       - camera_y,
                       0)
            .ortho(-100.0f,100.0f,
                   -100.0f,100.0f,
                   100.0f,-100.0f);
        });
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
  if(12 == *demo_number){
    // every shape is projected the same way
    transformationStack.push_back([&](Vertex3 v){
        return v.ortho(-100.0f,100.0f,
                       -100.0f,100.0f,
                       100.0f,-100.0f);
      });
    // every shape is relative to the camera
    transformationStack.push_back([&](Vertex3 v){
        return v.translate(- camera_x,
                           - camera_y,
                           0.0);
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
    return SDL_FALSE;
  }
//----
//[source,C,linenums]
//----
  static float moving_camera_x = 0.0;
  static float moving_camera_y = 0.0;
  static float moving_camera_z = 0.0;
  static float moving_camera_rot_y = 0.0;
  static float moving_camera_rot_x = 0.0;
  // update camera from the keyboard
  {
    const float move_multiple = 15.0;
    if (state[SDL_SCANCODE_RIGHT]) {
      moving_camera_rot_y -= (GLfloat)0.03;
    }
    if (state[SDL_SCANCODE_LEFT]) {
      moving_camera_rot_y += (GLfloat)0.03;
    }
    if (state[SDL_SCANCODE_UP]) {
      moving_camera_x -= move_multiple * (GLfloat)sin(moving_camera_rot_y);
      moving_camera_z -= move_multiple * (GLfloat)cos(moving_camera_rot_y);
    }
    if (state[SDL_SCANCODE_DOWN]) {
      moving_camera_x += move_multiple * (GLfloat)sin(moving_camera_rot_y);
      moving_camera_z += move_multiple * (GLfloat)cos(moving_camera_rot_y);
    }
  }
//----
//[source,C,linenums]
//----
  if(13 == *demo_number){
    // every shape is projected the same way
    transformationStack.push_back([&](Vertex3 v){
        return v.ortho(-100.0f,100.0f,
                       -100.0f,100.0f,
                       100.0f,-100.0f);
      });
    // every shape is relative to the camera
    // camera transformation #3 - tilt your head down
    transformationStack.push_back([&](Vertex3 v){
        return v.rotateX(moving_camera_rot_x);
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
        return v.rotateX(moving_camera_rot_x);
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
    glVertex2f(-1.0, -1.0);
    glVertex2f(1.0, -1.0);
    glVertex2f(1.0, 1.0);
    glVertex2f(-1.0, 1.0);
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
      glRotatef(RAD_TO_DEG(moving_camera_rot_x),
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
//And now for something completely different: ((monkeys)), lions and
//tigers (Bengal and Siberian) using the alternative syntax index
//entries.
//(((Big cats,Lions)))
//(((Big cats,Tigers,Bengal Tiger)))
//(((Big cats,Tigers,Siberian Tiger)))
//Note that multi-entry terms generate separate index entries.
//
//Here are a couple of image examples: an image:images/smallnew.png[]
//example inline image followed by an example block image:
//
//.Tiger block image
//image::images/tiger.png[Tiger image]
//
//Followed by an example table:
//
//.An example table
//[width="60%",options="header"]
//|==============================================
//| Option          | Description
//| -a 'USER GROUP' | Add 'USER' to 'GROUP'.
//| -R 'GROUP'      | Disables access to 'GROUP'.
//|==============================================
//
//.An example example
//===============================================
//Lorum ipum...
//===============================================
//
//[[X1]]
//Sub-section with Anchor
//~~~~~~~~~~~~~~~~~~~~~~~
//Sub-section at level 2.
//
//Chapter Sub-section
//^^^^^^^^^^^^^^^^^^^
//Sub-section at level 3.
//
//Chapter Sub-section
//+++++++++++++++++++
//Sub-section at level 4.
//
//This is the maximum sub-section depth supported by the distributed
//AsciiDoc configuration.
//footnote:[A second example footnote.]
//
//
//The Second Chapter
//------------------
//An example link to anchor at start of the <<X1,first sub-section>>.
//indexterm:[Second example index entry]
//
//An example link to a bibliography entry <<taoup>>.
//
//
//The Third Chapter
//-----------------
//Book chapters are at level 1 and can contain sub-sections.
//
//
//:numbered!:
//
//[appendix]
//Example Appendix
//----------------
//One or more optional appendixes go here at section level 1.
//
//Appendix Sub-section
//~~~~~~~~~~~~~~~~~~~
//Sub-section body.
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
