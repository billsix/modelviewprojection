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

#version 330 core

layout (location = 0) in vec3 position;

uniform mat4 mMatrix;
uniform mat4 vMatrix;
uniform mat4 pMatrix;
uniform float field_of_view;
uniform float aspect_ratio;
uniform float near_z;
uniform float far_z;
uniform vec3 color;
uniform float time;

out VS_OUT {
  vec4 color;
} vs_out;

vec4 project(vec4 cameraSpace){

    float translateRatio = min((time - 90.0)/5.0, 1.0);
    mat4 translate_to_origin = transpose(mat4(
         1.0, 0.0, 0.0, 0.0,
         0.0, 1.0, 0.0, 0.0,
         0.0, 0.0, 1.0, 16.0/2 * translateRatio,
         0.0, 0.0, 0.0, 1.0));
    float scaleRatio = min((time - 95.0)/5.0, 1.0);
    float xVal = 1.0 + (1.0/5.0 - 1.0) * scaleRatio;
    float yVal = 1.0 + (1.0/5.0 - 1.0) * scaleRatio;
    float zVal = 1.0 + (2.0/15.0 - 1) * scaleRatio;
    mat4 scale_to_ndc = transpose(mat4(
         xVal,     0.0,     0.0,    0.0,
         0.0,      yVal,    0.0,    0.0,
         0.0,      0.0,     zVal,   0.0,
         0.0,      0.0,     0.0,    1.0));

    //use transpose to put the matrix in column major order
    if (time < 90){
      translate_to_origin = mat4(1.0);
    }
    if (time < 95){
      scale_to_ndc =  mat4(1.0);
    }

//ortho


     return scale_to_ndc * translate_to_origin * cameraSpace;
}


void main()
{
  gl_Position = pMatrix * vMatrix * project(mMatrix * vec4(position,1.0));
   vs_out.color = vec4(color,1.0);
}
