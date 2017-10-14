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
#include <GL/glew.h>
#include <GLFW/glfw3.h>
#include <assert.h>
#include <GL/glu.h>


extern GLFWwindow* window;

void
render_scene(int *demo_number);

/* void */
/* ndc_space_to_pixel_space(SDL_Window *window, */
/*                            GLfloat ndcspace_x, */
/*                            GLfloat ndcspace_y, */
/*                            int * screenspace_x, */
/*                            int * screenspace_y){ */
/*   int w, h; */
/*   SDL_GetWindowSize(window, */
/*                     /\*width*\/  &w, */
/*                     /\*height*\/ &h); */

/*   /\* */

/*     screen-space */

/*           (0,0) ------------------------- (width,0) */
/*                 ------------------------- */
/*                 ------------------------- */
/*                 ------------------------- */
/*                 ------------------------- */
/*                 ------------------------- */
/*                 ------------------------- */
/*                 ------------------------- */
/*      (0,height) ------------------------- (width,height) */


/*     ndc */

/*         (-1,1)  ------------------------- (1,1) */
/*                 ------------------------- */
/*                 ------------------------- */
/*                 ------------------------- */
/*                 ------------------------- */
/*                 ------------------------- */
/*                 ------------------------- */
/*                 ------------------------- */
/*         (-1,-1) ------------------------- (1,-1) */


/*     width */
/*     -1 -> 0 */
/*     0  -> w/2 */
/*     1  -> w */

/*     y = mx +b */
/*     f = w/2 * x + w/2 */

/*     height */
/*     1  -> 0 */
/*     0  -> h/2 */
/*     -1 -> h */

/*     y = mx +b */
/*     f = -h/2 * y + h/2 */

/*   *\/ */

/*   *screenspace_x = w/2 * ndcspace_x + w/2; */
/*   *screenspace_y = -h/2 * ndcspace_y + h/2; */
/* } */


#endif
