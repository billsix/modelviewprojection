// Copyright (c) 2018-2025 William Emerison Six
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 59 Temple Place - Suite 330,
// Boston, MA 02111-1307, USA.

#version 120

void main(void)
{
    // gl_Vector is modelspace data

    vec4 camera_space = gl_ModelViewMatrix * gl_Vector;
    // in camera space, the frustum is on the negative z axis
    vec4 clip_space = gl_ProjectionMatrix * camera_space;
    vec3 ndc_space = clip_space.xyz / clip_space.w;
    // in ndc space, x y and z need to be divided by w

    // normal MVP transform
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vector;

    // Copy the primary color
    gl_FrontColor = gl_Color;
}
