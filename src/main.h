#ifndef MAIN_H
#define MAIN_H 1
/*
 * William Emerison Six
 *
 * Copyright 2016-2017 - William Emerison Six
 * All rights reserved
 * Distributed under Apache 2.0
 */


#define GLEW_STATIC 1

#if HAVE_CONFIG_H
#include <config.h>
#endif
#ifdef _WINDOWS
#include <windows.h>
#include <stdlib.h>
#include <string.h>
#include <tchar.h>
#endif
#include "SDL.h"
#include <GL/glew.h>
#include <assert.h>
#include <GL/glu.h>


extern SDL_Window *window;
extern SDL_Renderer *renderer;
extern SDL_GLContext glcontext;

void
render_scene(int *demo_number);


#endif
