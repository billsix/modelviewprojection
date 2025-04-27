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
layout (location = 1) in vec3 color_in;

uniform mat4 mMatrix;
uniform mat4 vMatrix;
uniform mat4 pMatrix;
uniform float field_of_view;
uniform float aspect_ratio;
uniform float near_z;
uniform float far_z;
uniform float time;

out VS_OUT {
  vec4 color;
} vs_out;

vec4 project(vec4 cameraSpace){

    float top = (-near_z) * tan(field_of_view * 3.14159265358979323846 / 360.0);
    float right = top * aspect_ratio;

    float scaleXRatio = min((time - 90.0)/5.0, 1.0);
    float xVal = 1 + (near_z/cameraSpace.z - 1) * scaleXRatio;

    mat4 scale_x = transpose(mat4(
                                  xVal, 0.0, 0.0, 0.0,
                                  0.0,                 1.0, 0.0, 0.0,
                                  0.0,                 0.0, 1.0, 0.0,
                                  0.0,                 0.0, 0.0, 1.0));
    float scaleYRatio = min((time - 95.0)/5.0, 1.0);
    float yVal = 1 + (near_z/cameraSpace.z - 1) * scaleYRatio;
    mat4 scale_y = transpose(mat4(
                                  1.0, 0.0,                 0.0, 0.0,
                                  0.0, yVal, 0.0, 0.0,
                                  0.0, 0.0,                 1.0, 0.0,
                                  0.0, 0.0,                 0.0, 1.0));
    float translateRatio = min((time - 100.0)/5.0, 1.0);
    float zVal = (-((far_z + near_z) / 2.0)) * translateRatio;
    mat4 translate_to_origin = transpose(mat4(
         1.0, 0.0, 0.0, 0.0,
         0.0, 1.0, 0.0, 0.0,
         0.0, 0.0, 1.0, zVal,
         0.0, 0.0, 0.0, 1.0));
    float scaleRatio = min((time - 105.0)/5.0, 1.0);
    xVal = 1.0 + (1.0/right - 1.0) * scaleRatio;
    yVal = 1.0 + (1.0/top - 1.0) * scaleRatio;
    zVal = 1.0 + (2.0/(near_z - far_z) - 1) * scaleRatio;
    mat4 scale_to_ndc = transpose(mat4(
         xVal,     0.0,     0.0,    0.0,
         0.0,      yVal,    0.0,    0.0,
         0.0,      0.0,     zVal,   0.0,
         0.0,      0.0,     0.0,    1.0));

    //use transpose to put the matrix in column major order
    if (time < 90){
      scale_x = mat4(1.0);
    }
    if (time < 95){
      scale_y =  mat4(1.0);
    }
    if (time < 100){
      translate_to_origin = mat4(1.0);
    }
    if (time < 105){
      scale_to_ndc =  mat4(1.0);
    }

//ortho


     return scale_to_ndc * translate_to_origin * scale_y * scale_x * cameraSpace;
}


void main()
{
  // mMatrix has the "virtual camera's" view transformations in it.
  // so, from right to left, model, view (virtual, moving camera), project, view (our view), project (our view)
  gl_Position = pMatrix * vMatrix * project(mMatrix * vec4(position,1.0));
   vs_out.color = vec4(color_in,1.0);
}
